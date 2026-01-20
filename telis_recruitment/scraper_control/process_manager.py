"""
Scraper Process Manager - Manages scraper subprocess lifecycle.
Singleton class to start, stop, and monitor the scraper subprocess.

Enhanced with automatic retry logic and circuit breaker for reliable error handling.
"""

import os
import subprocess
import psutil
import threading
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from collections import deque
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class CircuitBreakerState(Enum):
    """Circuit breaker states for error handling."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Too many errors, blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class ProcessManager:
    """
    Singleton class to manage the scraper process lifecycle.
    Handles starting, stopping, and monitoring the scraper subprocess.
    
    Enhanced with automatic retry logic and circuit breaker for reliable error handling.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.process: Optional[subprocess.Popen] = None
        self.pid: Optional[int] = None
        self.status: str = 'stopped'
        self.start_time: Optional[datetime] = None
        self.params: Dict[str, Any] = {}
        self.logs: list = []
        self.max_logs: int = 1000
        self.output_thread: Optional[threading.Thread] = None
        self.current_run_id: Optional[int] = None
        self.early_exit_threshold: int = 5  # Seconds threshold for detecting early process exits
        
        # Error tracking for retry logic
        self.error_counts: Dict[str, int] = {
            'missing_module': 0,
            'rate_limit': 0,
            'config_error': 0,
            'crash': 0,
            'connection_error': 0,
            'timeout': 0,
            'parsing_error': 0,
            'other': 0
        }
        self.error_timestamps: deque = deque(maxlen=100)  # Track last 100 errors for rate calculation
        self.consecutive_failures: int = 0
        self.retry_count: int = 0
        self.last_failure_time: Optional[datetime] = None
        
        # Circuit breaker state
        self.circuit_breaker_state: CircuitBreakerState = CircuitBreakerState.CLOSED
        self.circuit_breaker_opened_at: Optional[datetime] = None
        self.circuit_breaker_failures: int = 0
        
        # Load configuration from database (will be set dynamically)
        self._load_config()
        
        self._initialized = True
    
    def _load_config(self):
        """Load configuration from database."""
        try:
            from .models import ScraperConfig
            config = ScraperConfig.get_config()
            
            self.max_retry_attempts = config.process_max_retry_attempts
            self.qpi_reduction_factor = config.process_qpi_reduction_factor
            self.error_rate_threshold = config.process_error_rate_threshold
            self.circuit_breaker_failure_threshold = config.process_circuit_breaker_failures
            self.retry_backoff_base = config.process_retry_backoff_base
            self.error_rate_window_seconds = 300  # 5 minutes window for error rate calculation
            
            logger.info(f"Loaded config: max_retry={self.max_retry_attempts}, "
                       f"qpi_factor={self.qpi_reduction_factor}, "
                       f"error_threshold={self.error_rate_threshold}, "
                       f"cb_threshold={self.circuit_breaker_failure_threshold}, "
                       f"backoff={self.retry_backoff_base}, "
                       f"error_window={self.error_rate_window_seconds}s")
        except Exception as e:
            logger.warning(f"Failed to load config from database, using defaults: {e}")
            # Set default values
            self.max_retry_attempts = 3
            self.qpi_reduction_factor = 0.7
            self.error_rate_threshold = 0.5
            self.circuit_breaker_failure_threshold = 5
            self.retry_backoff_base = 30.0
            self.error_rate_window_seconds = 300  # 5 minutes
    
    def _read_output(self):
        """Background thread to read and store process output."""
        try:
            while True:
                line = self.process.stdout.readline()
                if not line:  # EOF
                    # Log that process ended
                    exit_code = self.process.poll()
                    logger.warning(f"Scraper process ended with exit code: {exit_code}")
                    
                    # Check if it ended too quickly (configurable threshold)
                    if self.start_time:
                        runtime = (timezone.now() - self.start_time).total_seconds()
                        if runtime < self.early_exit_threshold:
                            error_msg = f"⚠️ Scraper exited after only {runtime:.1f}s - likely a startup error!"
                            logger.error(error_msg)
                            self._log_error(error_msg)
                            self._log_error("This usually means the scraper script has no executable entry point or crashed immediately.")
                            
                            # Track as crash and potentially retry
                            self._track_error('crash')
                            self.consecutive_failures += 1
                            self.last_failure_time = timezone.now()
                            
                            # Mark run as failed
                            if self.current_run_id:
                                try:
                                    from .models import ScraperRun
                                    run = ScraperRun.objects.get(id=self.current_run_id)
                                    run.status = 'failed'
                                    run.finished_at = timezone.now()
                                    run.save(update_fields=['status', 'finished_at'])
                                except Exception as e:
                                    logger.error(f"Failed to update ScraperRun: {e}")
                            
                            # Schedule retry if appropriate
                            if self._should_retry():
                                # Get the user from the current run
                                user = None
                                if self.current_run_id:
                                    try:
                                        from .models import ScraperRun
                                        run = ScraperRun.objects.get(id=self.current_run_id)
                                        user = run.started_by
                                    except Exception:
                                        pass
                                
                                self._schedule_retry(self.params, user=user)
                        else:
                            # Normal completion - reset error counters
                            self.consecutive_failures = 0
                            self.retry_count = 0
                            
                            # If circuit breaker is half-open, close it on success
                            if self.circuit_breaker_state == CircuitBreakerState.HALF_OPEN:
                                self._close_circuit_breaker()
                    break
                if line.strip():
                    timestamp = timezone.now()
                    log_entry = {
                        'timestamp': timestamp.isoformat(),
                        'message': line.strip()
                    }
                    self.logs.append(log_entry)
                    
                    # Keep only last max_logs entries
                    if len(self.logs) > self.max_logs:
                        self.logs = self.logs[-self.max_logs:]
                    
                    # Update ScraperRun logs and create ScraperLog entry
                    if self.current_run_id:
                        try:
                            from .models import ScraperRun, ScraperLog
                            
                            run = ScraperRun.objects.get(id=self.current_run_id)
                            
                            # Append to run logs
                            if run.logs:
                                run.logs += f"\n{line.strip()}"
                            else:
                                run.logs = line.strip()
                            
                            # Keep logs reasonable size
                            if len(run.logs) > 50000:  # ~50KB
                                run.logs = run.logs[-50000:]
                            run.save(update_fields=['logs'])
                            
                            # Create ScraperLog entry for SSE streaming
                            # Determine log level from message
                            level = 'INFO'
                            message_lower = line.lower()
                            if 'error' in message_lower or 'exception' in message_lower:
                                level = 'ERROR'
                            elif 'warn' in message_lower or 'warning' in message_lower:
                                level = 'WARN'
                            
                            ScraperLog.objects.create(
                                run=run,
                                level=level,
                                message=line.strip()
                            )
                            
                            # Detect common errors and track them
                            if 'ModuleNotFoundError' in line:
                                self._log_error("Missing module - check dependencies")
                                self._track_error('missing_module')
                            elif 'KeyError' in line or 'AttributeError' in line:
                                self._log_error(f"Configuration error: {line.strip()}")
                                self._track_error('config_error')
                            elif 'rate limit' in message_lower:
                                self._log_error("Rate limit hit - consider reducing QPI")
                                self._track_error('rate_limit')
                            elif 'ConnectionError' in line or 'connection' in message_lower and 'error' in message_lower:
                                self._log_error("Connection error detected")
                                self._track_error('connection_error')
                            elif 'TimeoutError' in line or 'timeout' in message_lower:
                                self._log_error("Timeout error detected")
                                self._track_error('timeout')
                            elif 'ParseError' in line or 'parsing' in message_lower and 'error' in message_lower:
                                self._log_error("Parsing error detected")
                                self._track_error('parsing_error')
                            
                        except Exception as e:
                            logger.error(f"Failed to update ScraperRun logs: {e}")
        except Exception as e:
            logger.error(f"Error reading scraper output: {e}")
    
    def _log_error(self, message: str):
        """Log an error message to the current run."""
        if self.current_run_id:
            try:
                from .models import ScraperLog, ScraperRun
                run = ScraperRun.objects.get(id=self.current_run_id)
                ScraperLog.objects.create(
                    run=run,
                    level='ERROR',
                    message=message
                )
            except Exception as e:
                logger.error(f"Failed to log error: {e}")
    
    def _track_error(self, error_type: str):
        """
        Track an error for retry and circuit breaker logic.
        
        Args:
            error_type: Type of error ('missing_module', 'rate_limit', 'config_error', 'crash', 'other')
        """
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        self.error_timestamps.append(timezone.now())
        self.circuit_breaker_failures += 1
        
        logger.info(f"Error tracked: {error_type}, total: {self.error_counts[error_type]}, "
                   f"circuit breaker failures: {self.circuit_breaker_failures}")
        
        # Check if circuit breaker should open
        if (self.circuit_breaker_state == CircuitBreakerState.CLOSED and 
            self.circuit_breaker_failures >= self.circuit_breaker_failure_threshold):
            self._open_circuit_breaker()
        
        # Check error rate
        error_rate = self._calculate_error_rate()
        if error_rate > self.error_rate_threshold:
            logger.warning(f"High error rate detected: {error_rate:.2%}")
            if self.circuit_breaker_state == CircuitBreakerState.CLOSED:
                self._open_circuit_breaker()
    
    def _calculate_error_rate(self) -> float:
        """
        Calculate error rate over the configured time window.
        
        Returns:
            Error rate as a float between 0 and 1
        """
        if not self.error_timestamps:
            return 0.0
        
        now = timezone.now()
        window_start = now - timedelta(seconds=self.error_rate_window_seconds)
        
        # Count errors in the time window
        recent_errors = sum(1 for ts in self.error_timestamps if ts >= window_start)
        
        # Calculate rate (errors per second)
        if recent_errors == 0:
            return 0.0
        
        # Estimate total operations (assuming at least 1 operation per second)
        total_operations = max(self.error_rate_window_seconds, 1)
        return min(recent_errors / total_operations, 1.0)
    
    def _open_circuit_breaker(self):
        """Open the circuit breaker to prevent further operations."""
        self.circuit_breaker_state = CircuitBreakerState.OPEN
        self.circuit_breaker_opened_at = timezone.now()
        
        logger.error(f"Circuit breaker OPENED after {self.circuit_breaker_failures} failures")
        self._log_error(f"🔴 Circuit breaker OPENED - too many errors detected. "
                       f"Pausing operations for safety.")
        
        # Stop the running process if any
        if self.is_running():
            logger.info("Stopping scraper due to circuit breaker opening")
            self.stop()
    
    def _check_circuit_breaker(self) -> bool:
        """
        Check if circuit breaker allows operation.
        
        Returns:
            True if operation is allowed, False if blocked
        """
        if self.circuit_breaker_state == CircuitBreakerState.CLOSED:
            return True
        
        if self.circuit_breaker_state == CircuitBreakerState.HALF_OPEN:
            # Allow one test operation
            return True
        
        # Check if enough time has passed to try again
        if self.circuit_breaker_opened_at:
            from .models import ScraperConfig
            config = ScraperConfig.get_config()
            penalty_seconds = config.circuit_breaker_penalty
            
            elapsed = (timezone.now() - self.circuit_breaker_opened_at).total_seconds()
            if elapsed >= penalty_seconds:
                # Transition to half-open state
                self.circuit_breaker_state = CircuitBreakerState.HALF_OPEN
                logger.info(f"Circuit breaker transitioning to HALF_OPEN after {elapsed:.1f}s penalty")
                self._log_error(f"⚠️ Circuit breaker HALF_OPEN - attempting test operation")
                return True
        
        logger.warning("Circuit breaker is OPEN - operation blocked")
        return False
    
    def _close_circuit_breaker(self):
        """Close the circuit breaker after successful operation."""
        self.circuit_breaker_state = CircuitBreakerState.CLOSED
        self.circuit_breaker_failures = 0
        self.circuit_breaker_opened_at = None
        logger.info("Circuit breaker CLOSED - normal operation resumed")
        self._log_error("✅ Circuit breaker CLOSED - operations resumed successfully")
    
    def _should_retry(self) -> bool:
        """
        Determine if a retry should be attempted.
        
        Returns:
            True if retry should be attempted, False otherwise
        """
        # Don't retry if max attempts reached
        if self.retry_count >= self.max_retry_attempts:
            logger.info(f"Max retry attempts ({self.max_retry_attempts}) reached")
            return False
        
        # Don't retry if circuit breaker is open and penalty hasn't passed
        if not self._check_circuit_breaker():
            logger.info("Circuit breaker is blocking retry")
            return False
        
        return True
    
    def _calculate_retry_backoff(self) -> float:
        """
        Calculate exponential backoff for retry with maximum cap.
        
        Returns:
            Backoff time in seconds (capped at 300s = 5 minutes)
        """
        backoff = self.retry_backoff_base * (2 ** self.retry_count)
        return min(backoff, 300.0)  # Max 5 minutes
    
    def _adjust_qpi_for_rate_limit(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adjust QPI downward if rate limit errors detected.
        
        Args:
            params: Original scraper parameters
            
        Returns:
            Updated parameters with adjusted QPI
        """
        if self.error_counts.get('rate_limit', 0) > 0:
            original_qpi = params.get('qpi', 15)
            new_qpi = max(1, int(original_qpi * self.qpi_reduction_factor))
            
            if new_qpi != original_qpi:
                logger.info(f"Reducing QPI from {original_qpi} to {new_qpi} due to rate limit errors")
                self._log_error(f"⚙️ Automatically reducing QPI: {original_qpi} → {new_qpi} "
                               f"to avoid rate limits")
                params = params.copy()
                params['qpi'] = new_qpi
        
        return params
    
    def _schedule_retry(self, params: Dict[str, Any], user=None):
        """
        Schedule an automatic retry with adjusted parameters.
        
        Args:
            params: Scraper parameters
            user: User who started the scraper
        """
        if not self._should_retry():
            logger.info("Retry not scheduled - conditions not met")
            return
        
        self.retry_count += 1
        backoff_time = self._calculate_retry_backoff()
        
        logger.info(f"Scheduling retry {self.retry_count}/{self.max_retry_attempts} "
                   f"after {backoff_time:.1f}s backoff")
        self._log_error(f"🔄 Scheduling automatic retry {self.retry_count}/{self.max_retry_attempts} "
                       f"in {backoff_time:.1f}s")
        
        # Adjust parameters if needed
        adjusted_params = self._adjust_qpi_for_rate_limit(params)
        
        # Schedule retry in a separate thread
        def retry_after_backoff():
            import time
            time.sleep(backoff_time)
            
            logger.info(f"Executing scheduled retry {self.retry_count}")
            self._log_error(f"🔄 Executing automatic retry {self.retry_count}")
            self.start(adjusted_params, user=user)
        
        retry_thread = threading.Thread(target=retry_after_backoff, daemon=True)
        retry_thread.start()
    
    def _find_scraper_script(self):
        """Find the scraper script to execute."""
        # Get project root (parent of telis_recruitment)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        
        # Priority 1: scriptname.py (the actual scraper with proper entry point)
        script_path = os.path.join(project_root, 'scriptname.py')
        if os.path.exists(script_path):
            logger.info(f"Found scraper script: {script_path}")
            return ('script', script_path)
        
        # Priority 2: luca_scraper module (if __main__.py exists)
        main_path = os.path.join(project_root, 'luca_scraper', '__main__.py')
        if os.path.exists(main_path):
            logger.info(f"Found luca_scraper module with __main__.py")
            return ('module', 'luca_scraper')
        
        # Priority 3: scriptname_backup.py (backup)
        backup_path = os.path.join(project_root, 'scriptname_backup.py')
        if os.path.exists(backup_path):
            logger.info(f"Found backup script: {backup_path}")
            return ('script', backup_path)
        
        logger.error("No scraper script found (tried scriptname.py, luca_scraper/__main__.py, scriptname_backup.py)")
        return (None, None)
    
    def _build_command(self, params: Dict[str, Any], script_type: str, script_path: str) -> list:
        """
        Build command line arguments with validation and fallbacks.
        
        Args:
            params: Dictionary of scraper parameters
            script_type: 'module' or 'script'
            script_path: Path to script or module name
            
        Returns:
            List of command arguments
        """
        # Build base command
        if script_type == 'module':
            # script_path contains the module name (e.g., 'luca_scraper'), not a file path
            cmd = ['python', '-m', script_path]
        else:
            cmd = ['python', script_path]
        
        # Industry - always set
        industry = params.get('industry', 'recruiter')
        cmd.extend(['--industry', str(industry)])
        
        # QPI - always set
        qpi = params.get('qpi', 15)
        cmd.extend(['--qpi', str(int(qpi))])
        
        # Mode - only if not standard
        mode = params.get('mode', 'standard')
        if mode and mode != 'standard':
            # Validate against CLI choices
            valid_modes = ['learning', 'aggressive', 'snippet_only']
            if mode in valid_modes:
                cmd.extend(['--mode', mode])
            else:
                logger.warning(f"Skipping invalid mode: {mode}")
        
        # Date restrict - only if set
        daterestrict = params.get('daterestrict', '')
        if daterestrict and daterestrict.strip():
            cmd.extend(['--daterestrict', daterestrict.strip()])
        
        # Boolean flags
        if params.get('smart', False):
            cmd.append('--smart')
        
        if params.get('force', False):
            cmd.append('--force')
        
        if params.get('once', True):  # Default True for single-run execution
            cmd.append('--once')
        
        if params.get('dry_run', False):
            cmd.append('--dry-run')
        
        logger.info(f"Built scraper command: {' '.join(cmd)}")
        return cmd
    
    def start(self, params: Dict[str, Any], user=None) -> Dict[str, Any]:
        """
        Start the scraper with given parameters.
        
        Args:
            params: Dictionary of scraper parameters
                - industry: str (recruiter, candidates, talent_hunt, all)
                - qpi: int (queries per industry)
                - mode: str (standard, learning, aggressive, snippet_only)
                - smart: bool
                - force: bool
                - once: bool
                - dry_run: bool
            user: Django User who started the scraper
                
        Returns:
            Dictionary with status and process info
        """
        if self.is_running():
            return {
                'success': False,
                'error': 'Scraper läuft bereits',
                'status': self.status
            }
        
        # Check circuit breaker
        if not self._check_circuit_breaker():
            from .models import ScraperConfig
            config = ScraperConfig.get_config()
            penalty_seconds = config.circuit_breaker_penalty
            
            if self.circuit_breaker_opened_at:
                elapsed = (timezone.now() - self.circuit_breaker_opened_at).total_seconds()
                remaining = max(0, penalty_seconds - elapsed)
                
                return {
                    'success': False,
                    'error': f'Circuit breaker is OPEN - please wait {remaining:.0f}s before retrying',
                    'status': 'circuit_breaker_open',
                    'circuit_breaker_state': self.circuit_breaker_state.value,
                    'remaining_penalty_seconds': remaining
                }
        
        try:
            # Create ScraperRun record
            from .models import ScraperRun, ScraperConfig
            
            config = ScraperConfig.get_config()
            run = ScraperRun.objects.create(
                status='running',
                params_snapshot=params,
                started_by=user
            )
            self.current_run_id = run.id
            
            # Find scraper script
            script_type, script_path = self._find_scraper_script()
            
            if script_type is None:
                run.status = 'failed'
                run.finished_at = timezone.now()
                run.logs = "Scraper script not found (luca_scraper/cli.py or scriptname.py)"
                run.save()
                return {
                    'success': False,
                    'error': 'Scraper script nicht gefunden',
                    'status': 'error'
                }
            
            # Build command with robust validation
            cmd = self._build_command(params, script_type, script_path)
            
            # Prepare environment
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            env = os.environ.copy()
            env_file = os.path.join(project_root, '.env')
            if os.path.exists(env_file):
                try:
                    from dotenv import dotenv_values
                    env_vars = dotenv_values(env_file)
                    env.update(env_vars)
                except ImportError:
                    pass
            
            # Start process
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                cwd=project_root,
                env=env
            )
            
            self.pid = self.process.pid
            self.status = 'running'
            self.start_time = timezone.now()
            self.params = params
            self.logs = []
            
            # Update run record with PID
            run.pid = self.pid
            run.save(update_fields=['pid'])
            
            # Start output reader thread
            self.output_thread = threading.Thread(target=self._read_output, daemon=True)
            self.output_thread.start()
            
            logger.info(f"Scraper started with PID {self.pid}")
            
            return {
                'success': True,
                'status': self.status,
                'pid': self.pid,
                'run_id': run.id,
                'params': self.params
            }
            
        except Exception as e:
            logger.error(f"Failed to start scraper: {e}", exc_info=True)
            self.status = 'error'
            if self.current_run_id:
                try:
                    from .models import ScraperRun
                    run = ScraperRun.objects.get(id=self.current_run_id)
                    run.status = 'failed'
                    run.logs = f"Failed to start: {str(e)}"
                    run.finished_at = timezone.now()
                    run.save()
                except Exception:
                    pass
            return {
                'success': False,
                'error': str(e),
                'status': self.status
            }
    
    def stop(self) -> Dict[str, Any]:
        """
        Stop the running scraper process.
        
        Returns:
            Dictionary with status
        """
        if not self.is_running():
            return {
                'success': False,
                'error': 'Kein Scraper-Prozess läuft',
                'status': self.status
            }
        
        try:
            if self.process:
                # Try graceful termination first
                self.process.terminate()
                
                try:
                    self.process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    # Force kill if still running
                    self.process.kill()
                    self.process.wait()
                
                self.process = None
            
            # Also try to kill via PID if it exists
            if self.pid:
                try:
                    proc = psutil.Process(self.pid)
                    proc.terminate()
                    proc.wait(timeout=5)
                except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                    pass
            
            # Update ScraperRun record
            if self.current_run_id:
                try:
                    from .models import ScraperRun
                    run = ScraperRun.objects.get(id=self.current_run_id)
                    run.status = 'stopped'
                    run.finished_at = timezone.now()
                    run.save()
                except Exception as e:
                    logger.error(f"Failed to update ScraperRun: {e}")
            
            self.status = 'stopped'
            self.pid = None
            self.start_time = None
            self.current_run_id = None
            
            # Reset retry counter on manual stop (user intervention)
            self.retry_count = 0
            self.consecutive_failures = 0
            
            logger.info("Scraper stopped successfully")
            
            return {
                'success': True,
                'status': self.status
            }
            
        except Exception as e:
            logger.error(f"Failed to stop scraper: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'status': self.status
            }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current scraper status.
        
        Returns:
            Dictionary with detailed status information including error tracking and circuit breaker state
        """
        # Check if process is actually running
        if self.process and self.process.poll() is not None:
            # Process has ended
            if self.current_run_id:
                try:
                    from .models import ScraperRun
                    run = ScraperRun.objects.get(id=self.current_run_id)
                    if run.status == 'running':
                        run.status = 'completed'
                        run.finished_at = timezone.now()
                        run.save()
                except Exception as e:
                    logger.error(f"Failed to update ScraperRun: {e}")
            
            self.status = 'stopped'
            self.pid = None
            self.start_time = None
            self.current_run_id = None
        
        status_info = {
            'status': self.status,
            'pid': self.pid,
            'run_id': self.current_run_id,
            'params': self.params if self.status != 'stopped' else {},
            # Error tracking information
            'error_counts': self.error_counts.copy(),
            'consecutive_failures': self.consecutive_failures,
            'retry_count': self.retry_count,
            'max_retry_attempts': self.max_retry_attempts,
            'error_rate': self._calculate_error_rate(),
            # Circuit breaker information
            'circuit_breaker_state': self.circuit_breaker_state.value,
            'circuit_breaker_failures': self.circuit_breaker_failures,
        }
        
        # Add circuit breaker penalty info if open
        if self.circuit_breaker_state != CircuitBreakerState.CLOSED and self.circuit_breaker_opened_at:
            from .models import ScraperConfig
            config = ScraperConfig.get_config()
            penalty_seconds = config.circuit_breaker_penalty
            elapsed = (timezone.now() - self.circuit_breaker_opened_at).total_seconds()
            remaining = max(0, penalty_seconds - elapsed)
            
            status_info['circuit_breaker_penalty_seconds'] = penalty_seconds
            status_info['circuit_breaker_elapsed_seconds'] = elapsed
            status_info['circuit_breaker_remaining_seconds'] = remaining
        
        if self.start_time:
            uptime = (timezone.now() - self.start_time).total_seconds()
            status_info['uptime_seconds'] = int(uptime)
            status_info['start_time'] = self.start_time.isoformat()
        
        # Get process info if running
        if self.pid and self.is_running():
            try:
                proc = psutil.Process(self.pid)
                status_info['cpu_percent'] = proc.cpu_percent(interval=0)
                status_info['memory_mb'] = round(proc.memory_info().rss / 1024 / 1024, 2)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Get run statistics if available (enhanced with new metrics)
        if self.current_run_id:
            try:
                from .models import ScraperRun
                run = ScraperRun.objects.get(id=self.current_run_id)
                status_info['leads_found'] = run.leads_found
                status_info['leads_accepted'] = run.leads_accepted
                status_info['leads_rejected'] = run.leads_rejected
                status_info['api_cost'] = float(run.api_cost)
                status_info['links_checked'] = run.links_checked
                status_info['links_successful'] = run.links_successful
                status_info['links_failed'] = run.links_failed
                status_info['block_rate'] = run.block_rate
                status_info['timeout_rate'] = run.timeout_rate
                status_info['error_rate'] = run.error_rate
                status_info['avg_request_time_ms'] = run.avg_request_time_ms
                status_info['lead_acceptance_rate'] = run.lead_acceptance_rate
                status_info['success_rate'] = run.success_rate
                status_info['circuit_breaker_triggered'] = run.circuit_breaker_triggered
            except Exception:
                pass
        
        return status_info
    
    def is_running(self) -> bool:
        """
        Check if scraper process is currently running.
        
        Returns:
            True if running, False otherwise
        """
        if self.process and self.process.poll() is None:
            return True
        
        if self.pid:
            try:
                proc = psutil.Process(self.pid)
                return proc.is_running()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        return False
    
    def get_logs(self, lines: int = 100) -> list:
        """
        Get recent logs from the scraper process.
        
        Args:
            lines: Maximum number of log entries to return
            
        Returns:
            List of log entries (most recent first)
        """
        return self.logs[-lines:] if self.logs else []
    
    def reset_error_tracking(self):
        """
        Manually reset error tracking and circuit breaker.
        Useful for admin operations or after fixing issues.
        """
        logger.info("Manually resetting error tracking and circuit breaker")
        
        self.error_counts = {
            'missing_module': 0,
            'rate_limit': 0,
            'config_error': 0,
            'crash': 0,
            'connection_error': 0,
            'timeout': 0,
            'parsing_error': 0,
            'other': 0
        }
        self.error_timestamps.clear()
        self.consecutive_failures = 0
        self.retry_count = 0
        self.last_failure_time = None
        
        # Reset circuit breaker
        if self.circuit_breaker_state != CircuitBreakerState.CLOSED:
            self._log_error("🔧 Manual reset: Circuit breaker closed, error counters reset")
        
        self.circuit_breaker_state = CircuitBreakerState.CLOSED
        self.circuit_breaker_opened_at = None
        self.circuit_breaker_failures = 0
        
        logger.info("Error tracking and circuit breaker reset complete")


# Global manager instance
_manager = None
_manager_lock = threading.Lock()


def get_manager() -> ProcessManager:
    """Get the global process manager instance."""
    global _manager
    if _manager is None:
        with _manager_lock:
            if _manager is None:
                _manager = ProcessManager()
    return _manager
