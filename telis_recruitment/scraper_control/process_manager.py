"""
Scraper Process Manager - Manages scraper subprocess lifecycle.
Singleton class to start, stop, and monitor the scraper subprocess.

Enhanced with automatic retry logic and circuit breaker for reliable error handling.
Refactored to use composition with specialized components.
"""

import os
import subprocess
import psutil
import threading
from typing import Optional, Dict, Any, List
from datetime import datetime
from django.utils import timezone
import logging

from .process_launcher import ProcessLauncher
from .output_monitor import OutputMonitor
from .retry_controller import RetryController
from .circuit_breaker import CircuitBreaker, CircuitBreakerState
from .error_types import ScraperErrorType, create_error_response

logger = logging.getLogger(__name__)


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
        
        # Core process state
        self.status: str = 'stopped'
        self.start_time: Optional[datetime] = None
        self.params: Dict[str, Any] = {}
        self.early_exit_threshold: int = 5  # Seconds threshold for detecting early process exits
        
        # Error context information
        self.last_error_type: Optional[ScraperErrorType] = None
        self.last_error_message: Optional[str] = None
        self.last_error_details: Optional[str] = None
        self.last_error_component: Optional[str] = None
        
        # Auto-recovery state
        self.consecutive_failures: int = 0
        self.max_consecutive_failures: int = 5
        self.auto_restart_timer: Optional[threading.Timer] = None
        self.auto_restart_delays = [30, 60, 120, 240, 480]  # Exponential backoff in seconds
        self.max_auto_restart_delay: int = 600  # 10 minutes max
        
        # Composition: specialized components
        self.launcher = ProcessLauncher()
        self.output_monitor = OutputMonitor(max_logs=1000)
        self.retry_controller = RetryController()
        self.circuit_breaker = CircuitBreaker()
        
        # Config version tracking for automatic restart on config changes
        self.current_config_version: int = 0
        self.config_watcher_thread: Optional[threading.Thread] = None
        self.config_check_interval: int = 10  # Check every 10 seconds
        self.restart_lock = threading.Lock()  # Prevent concurrent restarts
        self.last_restart_user = None  # Track user who last started the process
        
        # Load configuration from database (will be set dynamically)
        self._load_config()
        
        # Start config version watcher thread
        self._start_config_watcher()
        
        self._initialized = True
    
    def _load_config(self):
        """Load configuration from database and propagate to components."""
        try:
            from .models import ScraperConfig
            config = ScraperConfig.get_config()
            
            # Load config into components
            self.retry_controller.load_config(config)
            self.circuit_breaker.load_config(config)
            
            # Track current config version
            self.current_config_version = config.config_version
            
            logger.info(f"Configuration loaded into all components (version {self.current_config_version})")
        except Exception as e:
            logger.warning(f"Failed to load config from database, using defaults: {e}")
    
    def _set_error_context(
        self,
        error_type: ScraperErrorType,
        error_message: str,
        details: Optional[str] = None,
        component: Optional[str] = None
    ):
        """
        Store error context information for later retrieval.
        
        Args:
            error_type: The type of error
            error_message: Human-readable error message
            details: Additional details about the error
            component: The component that failed
        """
        self.last_error_type = error_type
        self.last_error_message = error_message
        self.last_error_details = details
        self.last_error_component = component
        logger.error(
            f"Error set: {error_type.value} - {error_message} "
            f"(component: {component}, details: {details})"
        )
    
    def _clear_error_context(self):
        """Clear stored error context."""
        self.last_error_type = None
        self.last_error_message = None
        self.last_error_details = None
        self.last_error_component = None
    
    def _update_run_as_failed(self, error_message: str):
        """
        Helper method to mark a scraper run as failed.
        
        Args:
            error_message: Error message to log in the run record
        """
        if self.output_monitor.current_run_id:
            try:
                from .models import ScraperRun
                run = ScraperRun.objects.get(id=self.output_monitor.current_run_id)
                run.status = 'failed'
                run.logs = error_message
                run.finished_at = timezone.now()
                run.save()
            except Exception as e:
                logger.error(f"Failed to update ScraperRun as failed: {e}")
    
    def _handle_process_completion(self, exit_code: int, runtime: float):
        """
        Handle process completion from OutputMonitor.
        
        Args:
            exit_code: Process exit code
            runtime: Runtime in seconds
        """
        # Check if it ended too quickly (configurable threshold)
        if runtime < self.early_exit_threshold:
            error_msg = f"⚠️ Scraper exited after only {runtime:.1f}s - likely a startup error!"
            logger.error(error_msg)
            self.output_monitor.log_error(error_msg)
            self.output_monitor.log_error("This usually means the scraper script has no executable entry point or crashed immediately.")
            
            # Set error context for early exit
            self._set_error_context(
                ScraperErrorType.PROCESS_EARLY_EXIT,
                error_msg,
                details=f"Runtime: {runtime:.1f}s",
                component="process_monitor"
            )
            
            # Track as crash and record failure
            self._handle_error('crash')
            self.retry_controller.record_failure()
            
            # Increment consecutive failures for auto-recovery
            self.consecutive_failures += 1
            logger.warning(f"Consecutive failures: {self.consecutive_failures}/{self.max_consecutive_failures}")
            
            # Mark run as failed
            if self.output_monitor.current_run_id:
                try:
                    from .models import ScraperRun
                    run = ScraperRun.objects.get(id=self.output_monitor.current_run_id)
                    run.status = 'failed'
                    run.finished_at = timezone.now()
                    run.save(update_fields=['status', 'finished_at'])
                except Exception as e:
                    logger.error(f"Failed to update ScraperRun: {e}")
            
            # Schedule retry if appropriate
            if self.retry_controller.should_retry(self.circuit_breaker.check_and_update()):
                # Get the user from the current run
                user = None
                if self.output_monitor.current_run_id:
                    try:
                        from .models import ScraperRun
                        run = ScraperRun.objects.get(id=self.output_monitor.current_run_id)
                        user = run.started_by
                    except Exception:
                        pass
                
                self.retry_controller.schedule_retry(
                    self.params,
                    self.start,
                    self.output_monitor.log_error,
                    self.circuit_breaker.check_and_update(),
                    user=user
                )
            
            # Trigger auto-restart if threshold reached
            if self._should_auto_restart():
                logger.info("Triggering auto-restart due to consecutive failures")
                self._auto_restart()
                
        else:
            # Normal completion - reset error counters
            self.retry_controller.record_success()
            self.circuit_breaker.record_success()
            
            # Reset consecutive failures counter on successful run
            if exit_code == 0:
                self.reset_failure_counter()
    
    def _handle_error(self, error_type: str):
        """
        Handle error detection from OutputMonitor or other sources.
        
        Args:
            error_type: Type of error detected
        """
        # Track error in retry controller
        error_rate = self.retry_controller.track_error(error_type)
        
        # Record failure in circuit breaker
        self.circuit_breaker.record_failure(self.output_monitor.log_error)
        
        # Log the error with specific message
        if error_type == 'missing_module':
            self.output_monitor.log_error("Missing module - check dependencies")
        elif error_type == 'config_error':
            self.output_monitor.log_error("Configuration error detected")
        elif error_type == 'rate_limit':
            self.output_monitor.log_error("Rate limit hit - consider reducing QPI")
        elif error_type == 'connection_error':
            self.output_monitor.log_error("Connection error detected")
        elif error_type == 'timeout':
            self.output_monitor.log_error("Timeout error detected")
        elif error_type == 'parsing_error':
            self.output_monitor.log_error("Parsing error detected")
        
        # Check error rate threshold
        if error_rate > self.retry_controller.error_rate_threshold:
            logger.warning(f"High error rate detected: {error_rate:.2%}")
            if self.circuit_breaker.state == CircuitBreakerState.CLOSED:
                self.circuit_breaker.open(self.output_monitor.log_error)
    
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
            self._set_error_context(
                ScraperErrorType.ALREADY_RUNNING,
                "Scraper läuft bereits",
                component="process_manager"
            )
            return create_error_response(
                ScraperErrorType.ALREADY_RUNNING,
                status=self.status,
                pid=self.launcher.pid,
                run_id=self.output_monitor.current_run_id,
                params=self.params
            )
        
        # Check circuit breaker
        if not self.circuit_breaker.check_and_update(self.output_monitor.log_error):
            remaining = self.circuit_breaker.get_remaining_penalty()
            
            self._set_error_context(
                ScraperErrorType.CIRCUIT_BREAKER_OPEN,
                f'Circuit breaker is OPEN - please wait {remaining:.0f}s before retrying',
                details=f"Remaining: {remaining:.0f}s",
                component="circuit_breaker"
            )
            
            return create_error_response(
                ScraperErrorType.CIRCUIT_BREAKER_OPEN,
                details=f"Remaining: {remaining:.0f}s",
                component="circuit_breaker",
                status='circuit_breaker_open',
                circuit_breaker_state=self.circuit_breaker.state.value,
                remaining_penalty_seconds=remaining,
                pid=None,
                run_id=None,
                params={}
            )
        
        try:
            # Create ScraperRun record
            from .models import ScraperRun, ScraperConfig
            
            config = ScraperConfig.get_config()
            run = ScraperRun.objects.create(
                status='running',
                params_snapshot=params,
                started_by=user
            )
            self.output_monitor.current_run_id = run.id
            
            # Find scraper script using launcher
            script_type, script_path = self.launcher.find_scraper_script()
            
            if script_type is None:
                self._update_run_as_failed("Scraper script not found (luca_scraper/cli.py or scriptname.py)")
                
                self._set_error_context(
                    ScraperErrorType.SCRIPT_NOT_FOUND,
                    "Scraper script nicht gefunden",
                    details="luca_scraper/cli.py or scriptname.py not found",
                    component="script_loader"
                )
                
                return create_error_response(
                    ScraperErrorType.SCRIPT_NOT_FOUND,
                    details="luca_scraper/cli.py or scriptname.py not found",
                    component="script_loader",
                    pid=None,
                    run_id=run.id,
                    params=params
                )
            
            # Build command using launcher
            cmd = self.launcher.build_command(params, script_type, script_path)
            
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
            
            overrides = config.env_overrides()
            self.launcher.apply_env_overrides(env, overrides)
            
            # Start process using launcher
            process = self.launcher.start_process(cmd, env, project_root)
            
            self.status = 'running'
            self.start_time = timezone.now()
            self.params = params
            self.last_restart_user = user  # Track user for automatic restarts
            
            # Reset consecutive failures on successful start
            self.reset_failure_counter()
            
            # Clear any previous error context on successful start
            self._clear_error_context()
            
            # Update run record with PID
            run.pid = self.launcher.pid
            run.save(update_fields=['pid'])
            
            # Start output monitoring
            self.output_monitor.start_monitoring(
                process,
                run.id,
                error_callback=self._handle_error,
                completion_callback=self._handle_process_completion
            )
            
            logger.info(f"Scraper started with PID {self.launcher.pid}")
            
            return {
                'success': True,
                'status': self.status,
                'pid': self.launcher.pid,
                'run_id': run.id,
                'params': self.params
            }
            
        except PermissionError as e:
            logger.error(f"Permission denied starting scraper: {e}", exc_info=True)
            self.status = 'error'
            
            self._set_error_context(
                ScraperErrorType.PERMISSION_DENIED,
                "Permission denied",
                details=str(e),
                component="process_launcher"
            )
            
            self._update_run_as_failed(f"Permission denied: {str(e)}")
            
            return create_error_response(
                ScraperErrorType.PERMISSION_DENIED,
                details=str(e),
                component="process_launcher",
                pid=self.launcher.pid if self.launcher else None,
                run_id=self.output_monitor.current_run_id,
                params=params
            )
            
        except FileNotFoundError as e:
            logger.error(f"File not found: {e}", exc_info=True)
            self.status = 'error'
            
            self._set_error_context(
                ScraperErrorType.FILE_ACCESS_ERROR,
                "File not found",
                details=str(e),
                component="process_launcher"
            )
            
            self._update_run_as_failed(f"File not found: {str(e)}")
            
            return create_error_response(
                ScraperErrorType.FILE_ACCESS_ERROR,
                details=str(e),
                component="process_launcher",
                pid=self.launcher.pid if self.launcher else None,
                run_id=self.output_monitor.current_run_id,
                params=params
            )
            
        except Exception as e:
            logger.error(f"Failed to start scraper: {e}", exc_info=True)
            self.status = 'error'
            
            # Try to detect error type from exception message
            error_type = ScraperErrorType.UNKNOWN_ERROR
            component = "process_manager"
            
            error_str = str(e).lower()
            if 'config' in error_str or 'settings' in error_str:
                error_type = ScraperErrorType.CONFIG_ERROR
                component = "config_loader"
            elif 'module' in error_str or 'import' in error_str:
                error_type = ScraperErrorType.MISSING_DEPENDENCY
                component = "dependency_loader"
            elif 'permission' in error_str or 'access' in error_str:
                error_type = ScraperErrorType.PERMISSION_DENIED
                component = "process_launcher"
            
            self._set_error_context(
                error_type,
                str(e),
                details=str(e),
                component=component
            )
            
            self._update_run_as_failed(f"Failed to start: {str(e)}")
            
            return create_error_response(
                error_type,
                details=str(e),
                component=component,
                pid=self.launcher.pid if self.launcher else None,
                run_id=self.output_monitor.current_run_id,
                params=params
            )
    
    def stop(self) -> Dict[str, Any]:
        """
        Stop the running scraper process.
        
        Returns:
            Dictionary with status
        """
        if not self.is_running():
            self._set_error_context(
                ScraperErrorType.NOT_RUNNING,
                "Kein Scraper-Prozess läuft",
                component="process_manager"
            )
            return create_error_response(
                ScraperErrorType.NOT_RUNNING,
                status=self.status
            )
        
        try:
            # Stop the process using launcher
            self.launcher.stop_process()
            
            # Update ScraperRun record
            if self.output_monitor.current_run_id:
                try:
                    from .models import ScraperRun
                    run = ScraperRun.objects.get(id=self.output_monitor.current_run_id)
                    run.status = 'stopped'
                    run.finished_at = timezone.now()
                    run.save()
                except Exception as e:
                    logger.error(f"Failed to update ScraperRun: {e}")
            
            self.status = 'stopped'
            self.start_time = None
            self.output_monitor.current_run_id = None
            
            # Reset retry counter on manual stop (user intervention)
            self.retry_controller.retry_count = 0
            self.retry_controller.consecutive_failures = 0
            
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
    
    def restart_process(self) -> Dict[str, Any]:
        """
        Restart the running scraper process with the same parameters.
        
        This method stops the current process and starts a new one with the same
        configuration. It uses a lock to prevent concurrent restarts.
        
        Returns:
            Dictionary with status and process info
        """
        # Use lock to prevent concurrent restarts
        if not self.restart_lock.acquire(blocking=False):
            logger.warning("Restart already in progress, ignoring concurrent restart request")
            return {
                'success': False,
                'error': 'Restart already in progress',
                'status': self.status
            }
        
        try:
            if not self.is_running():
                logger.warning("Cannot restart: no scraper process is running")
                return {
                    'success': False,
                    'error': 'Kein Scraper-Prozess läuft',
                    'status': self.status
                }
            
            logger.info("Restarting scraper process due to configuration change")
            
            # Save current parameters and user
            restart_params = self.params.copy()
            restart_user = self.last_restart_user
            
            # Log the restart event
            self.output_monitor.log_error("🔄 Konfigurationsänderung erkannt – automatischer Neustart wird durchgeführt...")
            
            # Stop the current process
            stop_result = self.stop()
            if not stop_result.get('success'):
                logger.error(f"Failed to stop process during restart: {stop_result.get('error')}")
                return {
                    'success': False,
                    'error': f"Fehler beim Stoppen: {stop_result.get('error')}",
                    'status': self.status
                }
            
            # Brief pause to ensure clean shutdown
            import time
            time.sleep(2)
            
            # Reload configuration
            self._load_config()
            
            # Start the process again with the same parameters
            start_result = self.start(restart_params, user=restart_user)
            
            if start_result.get('success'):
                logger.info("Scraper restarted successfully")
                self.output_monitor.log_error("✅ Scraper erfolgreich mit neuer Konfiguration neu gestartet")
            else:
                logger.error(f"Failed to start process during restart: {start_result.get('error')}")
            
            return start_result
            
        finally:
            self.restart_lock.release()
    
    def _start_config_watcher(self):
        """
        Start background thread that watches for configuration changes.
        
        Polls the ScraperConfig.config_version every few seconds and triggers
        an automatic restart when the version changes.
        """
        if self.config_watcher_thread is not None:
            logger.debug("Config watcher thread already running")
            return
        
        def config_watcher_loop():
            """Background loop that checks for config version changes."""
            logger.info("Config watcher thread started")
            
            while True:
                try:
                    import time
                    time.sleep(self.config_check_interval)
                    
                    # Only check if a scraper is running
                    if not self.is_running():
                        continue
                    
                    # Check current config version from database
                    try:
                        from .models import ScraperConfig
                        config = ScraperConfig.get_config()
                        new_version = config.config_version
                        
                        if new_version != self.current_config_version:
                            logger.info(
                                f"Configuration version changed: {self.current_config_version} -> {new_version}"
                            )
                            
                            # Update tracked version
                            old_version = self.current_config_version
                            self.current_config_version = new_version
                            
                            # Trigger automatic restart
                            logger.info("Triggering automatic restart due to config change")
                            restart_result = self.restart_process()
                            
                            if restart_result.get('success'):
                                logger.info(f"Config change restart successful (v{old_version} -> v{new_version})")
                            else:
                                logger.error(f"Config change restart failed: {restart_result.get('error')}")
                    
                    except Exception as e:
                        logger.debug(f"Error checking config version: {e}")
                        # Don't fail the watcher thread on transient errors
                        continue
                        
                except Exception as e:
                    logger.error(f"Error in config watcher loop: {e}", exc_info=True)
                    # Continue running even if there's an error
                    continue
        
        # Start daemon thread
        self.config_watcher_thread = threading.Thread(
            target=config_watcher_loop,
            name="ConfigWatcher",
            daemon=True
        )
        self.config_watcher_thread.start()
        logger.info("Config watcher thread initialized")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current scraper status.
        
        Returns:
            Dictionary with detailed status information including error tracking and circuit breaker state
        """
        # Check if process is actually running
        if self.launcher.process and self.launcher.process.poll() is not None:
            # Process has ended
            if self.output_monitor.current_run_id:
                try:
                    from .models import ScraperRun
                    run = ScraperRun.objects.get(id=self.output_monitor.current_run_id)
                    if run.status == 'running':
                        run.status = 'completed'
                        run.finished_at = timezone.now()
                        run.save()
                except Exception as e:
                    logger.error(f"Failed to update ScraperRun: {e}")
            
            self.status = 'stopped'
            self.start_time = None
            self.output_monitor.current_run_id = None
        
        status_info = {
            'status': self.status,
            'pid': self.launcher.pid,
            'run_id': self.output_monitor.current_run_id,
            'params': self.params if self.status != 'stopped' else {},
            # Error tracking information from retry controller
            'error_counts': self.retry_controller.error_counts.copy(),
            'consecutive_failures': self.retry_controller.consecutive_failures,
            'retry_count': self.retry_controller.retry_count,
            'max_retry_attempts': self.retry_controller.max_retry_attempts,
            'error_rate': self.retry_controller.calculate_error_rate(),
            # Circuit breaker information
            'circuit_breaker_state': self.circuit_breaker.state.value,
            'circuit_breaker_failures': self.circuit_breaker.failures,
        }
        
        # Add error context information if available
        if self.last_error_type is not None:
            from .error_types import ErrorContext
            error_info = ErrorContext.get_error_info(
                self.last_error_type,
                self.last_error_details,
                self.last_error_component
            )
            status_info.update(error_info)
        
        # Add circuit breaker penalty info if open
        if self.circuit_breaker.state != CircuitBreakerState.CLOSED and self.circuit_breaker.opened_at:
            remaining = self.circuit_breaker.get_remaining_penalty()
            
            status_info['circuit_breaker_remaining_seconds'] = remaining
        
        if self.start_time:
            uptime = (timezone.now() - self.start_time).total_seconds()
            status_info['uptime_seconds'] = int(uptime)
            status_info['start_time'] = self.start_time.isoformat()
        
        # Get process info if running
        if self.launcher.pid and self.is_running():
            try:
                proc = psutil.Process(self.launcher.pid)
                status_info['cpu_percent'] = proc.cpu_percent(interval=0)
                status_info['memory_mb'] = round(proc.memory_info().rss / 1024 / 1024, 2)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Get run statistics if available (enhanced with new metrics)
        if self.output_monitor.current_run_id:
            try:
                from .models import ScraperRun
                run = ScraperRun.objects.get(id=self.output_monitor.current_run_id)
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
        return self.launcher.is_running()
    
    def get_logs(self, lines: int = 100) -> list:
        """
        Get recent logs from the scraper process.
        
        Args:
            lines: Maximum number of log entries to return
            
        Returns:
            List of log entries (most recent first)
        """
        return self.output_monitor.get_logs(lines)
    
    def reset_error_tracking(self):
        """
        Manually reset error tracking and circuit breaker.
        Useful for admin operations or after fixing issues.
        """
        logger.info("Manually resetting error tracking and circuit breaker")
        
        # Reset retry controller
        self.retry_controller.reset()
        
        # Reset circuit breaker
        if self.circuit_breaker.state != CircuitBreakerState.CLOSED:
            self.output_monitor.log_error("🔧 Manual reset: Circuit breaker closed, error counters reset")
        
        self.circuit_breaker.reset(self.output_monitor.log_error)
        
        logger.info("Error tracking and circuit breaker reset complete")
    
    def preview_command(self, params: Dict[str, Any]) -> str:
        """
        Preview the command that would be executed without starting the process.
        
        Args:
            params: Dictionary of scraper parameters
            
        Returns:
            Command string preview
        """
        return self.launcher.preview_command(params)
    
    # Backward compatibility: proxy properties and methods for tests
    @property
    def error_counts(self):
        """Backward compatibility: access retry_controller.error_counts"""
        return self.retry_controller.error_counts
    
    @error_counts.setter
    def error_counts(self, value):
        """Backward compatibility: set retry_controller.error_counts"""
        self.retry_controller.error_counts = value
    
    @property
    def error_timestamps(self):
        """Backward compatibility: access retry_controller.error_timestamps"""
        return self.retry_controller.error_timestamps
    
    @property
    def consecutive_failures(self):
        """Backward compatibility: access retry_controller.consecutive_failures"""
        return self.retry_controller.consecutive_failures
    
    @consecutive_failures.setter
    def consecutive_failures(self, value):
        """Backward compatibility: set retry_controller.consecutive_failures"""
        self.retry_controller.consecutive_failures = value
    
    @property
    def retry_count(self):
        """Backward compatibility: access retry_controller.retry_count"""
        return self.retry_controller.retry_count
    
    @retry_count.setter
    def retry_count(self, value):
        """Backward compatibility: set retry_controller.retry_count"""
        self.retry_controller.retry_count = value
    
    @property
    def circuit_breaker_state(self):
        """Backward compatibility: access circuit_breaker.state"""
        return self.circuit_breaker.state
    
    @circuit_breaker_state.setter
    def circuit_breaker_state(self, value):
        """Backward compatibility: set circuit_breaker.state"""
        self.circuit_breaker.state = value
    
    @property
    def circuit_breaker_failures(self):
        """Backward compatibility: access circuit_breaker.failures"""
        return self.circuit_breaker.failures
    
    @circuit_breaker_failures.setter
    def circuit_breaker_failures(self, value):
        """Backward compatibility: set circuit_breaker.failures"""
        self.circuit_breaker.failures = value
    
    @property
    def circuit_breaker_opened_at(self):
        """Backward compatibility: access circuit_breaker.opened_at"""
        return self.circuit_breaker.opened_at
    
    @circuit_breaker_opened_at.setter
    def circuit_breaker_opened_at(self, value):
        """Backward compatibility: set circuit_breaker.opened_at"""
        self.circuit_breaker.opened_at = value
    
    def _track_error(self, error_type: str):
        """Backward compatibility: delegate to _handle_error"""
        self._handle_error(error_type)
    
    def _calculate_error_rate(self) -> float:
        """Backward compatibility: delegate to retry_controller"""
        return self.retry_controller.calculate_error_rate()
    
    def _open_circuit_breaker(self):
        """Backward compatibility: delegate to circuit_breaker"""
        self.circuit_breaker.open(self.output_monitor.log_error)
        # Stop the running process if any
        if self.is_running():
            logger.info("Stopping scraper due to circuit breaker opening")
            self.stop()
    
    def _close_circuit_breaker(self):
        """Backward compatibility: delegate to circuit_breaker"""
        self.circuit_breaker.close(self.output_monitor.log_error)
    
    def _check_circuit_breaker(self) -> bool:
        """Backward compatibility: delegate to circuit_breaker"""
        return self.circuit_breaker.check_and_update(self.output_monitor.log_error)
    
    # Auto-recovery methods
    def _should_auto_restart(self) -> bool:
        """
        Check if automatic restart should be triggered.
        
        Returns:
            True if auto-restart should happen
        """
        if self.consecutive_failures >= self.max_consecutive_failures:
            logger.warning(
                f"Consecutive failures ({self.consecutive_failures}) reached max threshold "
                f"({self.max_consecutive_failures}), auto-restart enabled"
            )
            return True
        return False
    
    def _calculate_restart_delay(self) -> int:
        """
        Calculate exponential backoff delay for auto-restart.
        
        Uses exponential backoff: 30s, 60s, 120s, 240s, 480s, max 600s
        
        Returns:
            Delay in seconds
        """
        failure_index = min(self.consecutive_failures - 1, len(self.auto_restart_delays) - 1)
        if failure_index >= 0 and failure_index < len(self.auto_restart_delays):
            delay = self.auto_restart_delays[failure_index]
        else:
            delay = self.max_auto_restart_delay
        
        return min(delay, self.max_auto_restart_delay)
    
    def _auto_restart(self):
        """
        Automatically restart the scraper after a delay.
        
        Uses exponential backoff to avoid rapid restart loops.
        Triggered when consecutive failures exceed threshold.
        """
        if self.is_running():
            logger.info("Scraper already running, skipping auto-restart")
            return
        
        if not self._should_auto_restart():
            logger.debug("Auto-restart conditions not met")
            return
        
        delay = self._calculate_restart_delay()
        
        logger.info(
            f"Scheduling auto-restart in {delay}s "
            f"(failure #{self.consecutive_failures})"
        )
        
        # Cancel any existing restart timer
        if self.auto_restart_timer:
            self.auto_restart_timer.cancel()
        
        # Schedule restart with timer
        def restart_callback():
            logger.info("Executing auto-restart")
            try:
                # Attempt to restart with the same parameters
                user = None
                if self.output_monitor.current_run_id:
                    try:
                        from .models import ScraperRun
                        run = ScraperRun.objects.get(id=self.output_monitor.current_run_id)
                        user = run.started_by
                    except Exception:
                        pass
                
                result = self.start(self.params, user=user)
                
                if result.get('success'):
                    logger.info("Auto-restart successful")
                    # Reset counter on successful start
                    self.consecutive_failures = 0
                else:
                    logger.error(f"Auto-restart failed: {result.get('error')}")
                    self.consecutive_failures += 1
                    
                    # Trigger another restart if still below threshold
                    if self._should_auto_restart():
                        self._auto_restart()
                        
            except Exception as e:
                logger.error(f"Auto-restart exception: {e}", exc_info=True)
                self.consecutive_failures += 1
        
        self.auto_restart_timer = threading.Timer(delay, restart_callback)
        self.auto_restart_timer.daemon = True
        self.auto_restart_timer.start()
    
    def reset_failure_counter(self):
        """
        Reset the consecutive failures counter.
        
        Call this after a successful manual restart or when
        the scraper runs successfully for a sufficient duration.
        """
        if self.consecutive_failures > 0:
            logger.info(
                f"Resetting consecutive failures counter from {self.consecutive_failures} to 0"
            )
            self.consecutive_failures = 0
        
        # Cancel any pending auto-restart
        if self.auto_restart_timer:
            logger.debug("Cancelling pending auto-restart timer")
            self.auto_restart_timer.cancel()
            self.auto_restart_timer = None


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
