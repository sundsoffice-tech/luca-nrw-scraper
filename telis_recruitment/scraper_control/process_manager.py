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
        
        # Composition: specialized components
        self.launcher = ProcessLauncher()
        self.output_monitor = OutputMonitor(max_logs=1000)
        self.retry_controller = RetryController()
        self.circuit_breaker = CircuitBreaker()
        
        # Load configuration from database (will be set dynamically)
        self._load_config()
        
        self._initialized = True
    
    def _load_config(self):
        """Load configuration from database and propagate to components."""
        try:
            from .models import ScraperConfig
            config = ScraperConfig.get_config()
            
            # Load config into components
            self.retry_controller.load_config(config)
            self.circuit_breaker.load_config(config)
            
            logger.info("Configuration loaded into all components")
        except Exception as e:
            logger.warning(f"Failed to load config from database, using defaults: {e}")
    
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
            
            # Track as crash and record failure
            self._handle_error('crash')
            self.retry_controller.record_failure()
            
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
        else:
            # Normal completion - reset error counters
            self.retry_controller.record_success()
            self.circuit_breaker.record_success(self.output_monitor.log_error)
    
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
            return {
                'success': False,
                'error': 'Scraper läuft bereits',
                'status': self.status
            }
        
        # Check circuit breaker
        if not self.circuit_breaker.check_and_update(self.output_monitor.log_error):
            remaining = self.circuit_breaker.get_remaining_penalty()
            
            return {
                'success': False,
                'error': f'Circuit breaker is OPEN - please wait {remaining:.0f}s before retrying',
                'status': 'circuit_breaker_open',
                'circuit_breaker_state': self.circuit_breaker.state.value,
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
            self.output_monitor.current_run_id = run.id
            
            # Find scraper script using launcher
            script_type, script_path = self.launcher.find_scraper_script()
            
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
            
        except Exception as e:
            logger.error(f"Failed to start scraper: {e}", exc_info=True)
            self.status = 'error'
            if self.output_monitor.current_run_id:
                try:
                    from .models import ScraperRun
                    run = ScraperRun.objects.get(id=self.output_monitor.current_run_id)
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
    
    def preview_command(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preview the command that would be executed without starting the process.
        
        Args:
            params: Dictionary of scraper parameters
            
        Returns:
            Dictionary with command preview information
        """
        return self.launcher.preview_command(params)


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
