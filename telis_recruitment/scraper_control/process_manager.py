"""
Scraper Process Manager - Manages scraper subprocess lifecycle.
Singleton class to start, stop, and monitor the scraper subprocess.
"""

import os
import subprocess
import psutil
import threading
from typing import Optional, Dict, Any
from datetime import datetime
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class ProcessManager:
    """
    Singleton class to manage the scraper process lifecycle.
    Handles starting, stopping, and monitoring the scraper subprocess.
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
        self._initialized = True
    
    def _read_output(self):
        """Background thread to read and store process output."""
        try:
            while True:
                line = self.process.stdout.readline()
                if not line:  # EOF
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
                            
                            # Detect common errors
                            if 'ModuleNotFoundError' in line:
                                self._log_error("Missing module - check dependencies")
                            if 'KeyError' in line or 'AttributeError' in line:
                                self._log_error(f"Configuration error: {line.strip()}")
                            if 'rate limit' in message_lower:
                                self._log_error("Rate limit hit - consider reducing QPI")
                            
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
    
    def _find_scraper_script(self):
        """Find the scraper script to execute."""
        # Get project root (parent of telis_recruitment)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        
        # Priority 1: luca_scraper/cli.py (preferred)
        cli_path = os.path.join(project_root, 'luca_scraper', 'cli.py')
        if os.path.exists(cli_path):
            # Check if we can run it as a module
            luca_scraper_init = os.path.join(project_root, 'luca_scraper', '__init__.py')
            if os.path.exists(luca_scraper_init):
                return ('module', 'luca_scraper.cli')
        
        # Priority 2: scriptname.py (fallback)
        script_path = os.path.join(project_root, 'scriptname.py')
        if os.path.exists(script_path):
            return ('script', script_path)
        
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
            cmd = ['python', '-m', 'luca_scraper.cli']
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
        
        if params.get('once', True):  # Default True!
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
            Dictionary with detailed status information
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
            'params': self.params if self.status != 'stopped' else {}
        }
        
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
        
        # Get run statistics if available
        if self.current_run_id:
            try:
                from .models import ScraperRun
                run = ScraperRun.objects.get(id=self.current_run_id)
                status_info['leads_found'] = run.leads_found
                status_info['api_cost'] = float(run.api_cost)
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
