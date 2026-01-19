"""
Scraper Process Manager - Manages scraper subprocess lifecycle.
Singleton class to start, stop, and monitor the scraper subprocess.

Enhanced features:
- Command preview before execution
- CRM-based environment variable loading
- Live configuration updates via database flag
"""

import os
import subprocess
import psutil
import threading
import json
from typing import Optional, Dict, Any, List, Tuple
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
        self.early_exit_threshold: int = 5  # Seconds threshold for detecting early process exits
        self._config_check_interval: int = 5  # Seconds between config reload checks
        self._last_config_hash: Optional[str] = None  # Track config changes
        self._initialized = True
    
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
    
    def _build_environment_from_crm(self) -> Dict[str, str]:
        """
        Build environment variables from CRM/ScraperConfig instead of .env files.
        
        Reads configuration from the ScraperConfig model and converts to environment
        variables that the scraper subprocess can use.
        
        Returns:
            Dictionary of environment variables
        """
        env = os.environ.copy()
        
        try:
            from .models import ScraperConfig
            config = ScraperConfig.get_config()
            
            # Map ScraperConfig fields to environment variables
            crm_env_mapping = {
                # HTTP & Networking
                'SCRAPER_HTTP_TIMEOUT': str(config.http_timeout),
                'SCRAPER_ASYNC_LIMIT': str(config.async_limit),
                'SCRAPER_POOL_SIZE': str(config.pool_size),
                'SCRAPER_HTTP2_ENABLED': '1' if config.http2_enabled else '0',
                
                # Rate Limiting
                'SCRAPER_SLEEP_BETWEEN_QUERIES': str(config.sleep_between_queries),
                'SCRAPER_MAX_GOOGLE_PAGES': str(config.max_google_pages),
                'SCRAPER_CIRCUIT_BREAKER_PENALTY': str(config.circuit_breaker_penalty),
                'SCRAPER_RETRY_MAX_PER_URL': str(config.retry_max_per_url),
                
                # Scoring
                'SCRAPER_MIN_SCORE': str(config.min_score),
                'SCRAPER_MAX_PER_DOMAIN': str(config.max_per_domain),
                'SCRAPER_DEFAULT_QUALITY_SCORE': str(config.default_quality_score),
                'SCRAPER_CONFIDENCE_THRESHOLD': str(config.confidence_threshold),
                
                # Feature Flags
                'SCRAPER_ENABLE_KLEINANZEIGEN': '1' if config.enable_kleinanzeigen else '0',
                'SCRAPER_ENABLE_TELEFONBUCH': '1' if config.enable_telefonbuch else '0',
                'SCRAPER_ENABLE_PERPLEXITY': '1' if config.enable_perplexity else '0',
                'SCRAPER_ENABLE_BING': '1' if config.enable_bing else '0',
                'SCRAPER_PARALLEL_PORTAL_CRAWL': '1' if config.parallel_portal_crawl else '0',
                'SCRAPER_MAX_CONCURRENT_PORTALS': str(config.max_concurrent_portals),
                
                # Content
                'SCRAPER_ALLOW_PDF': '1' if config.allow_pdf else '0',
                'SCRAPER_MAX_CONTENT_LENGTH': str(config.max_content_length),
                
                # Security
                'SCRAPER_ALLOW_INSECURE_SSL': '1' if config.allow_insecure_ssl else '0',
            }
            
            # Update environment with CRM settings
            env.update(crm_env_mapping)
            
            logger.info(f"Loaded {len(crm_env_mapping)} environment variables from CRM config")
            
        except Exception as e:
            logger.warning(f"Could not load CRM config for environment: {e}")
        
        # Fallback: Also load from .env file if it exists (for API keys, etc.)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        env_file = os.path.join(project_root, '.env')
        if os.path.exists(env_file):
            try:
                from dotenv import dotenv_values
                env_vars = dotenv_values(env_file)
                # Only add .env values that are not already set by CRM config
                for key, value in env_vars.items():
                    if key not in env:
                        env[key] = value
                logger.info(f"Supplemented with {len(env_vars)} .env variables (API keys, etc.)")
            except ImportError:
                logger.debug("python-dotenv not installed, skipping .env file")
        
        return env
    
    def get_command_preview(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a preview of the command that would be executed.
        
        This allows administrators to verify the configuration before starting.
        
        Args:
            params: Dictionary of scraper parameters
            
        Returns:
            Dictionary with command preview information
        """
        script_type, script_path = self._find_scraper_script()
        
        if script_type is None:
            return {
                'success': False,
                'error': 'Scraper script nicht gefunden',
                'command': None,
                'environment': {}
            }
        
        # Build command
        cmd = self._build_command(params, script_type, script_path)
        
        # Get environment variables (only show scraper-related ones)
        env = self._build_environment_from_crm()
        scraper_env = {k: v for k, v in env.items() if k.startswith('SCRAPER_')}
        
        # Get project root for context
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        
        return {
            'success': True,
            'command': ' '.join(cmd),
            'command_args': cmd,
            'script_type': script_type,
            'script_path': script_path,
            'working_directory': project_root,
            'environment': scraper_env,
            'params': params
        }
    
    def check_live_config_updates(self) -> Optional[Dict[str, Any]]:
        """
        Check if configuration has been updated and return changed parameters.
        
        This enables runtime configuration changes by checking the database
        for updates to pool_size, sleep_between_queries, etc.
        
        Returns:
            Dictionary of changed config values, or None if no changes
        """
        try:
            from .models import ScraperConfig
            config = ScraperConfig.get_config()
            
            # Create a hash of live-updateable config values
            live_config = {
                'pool_size': config.pool_size,
                'sleep_between_queries': config.sleep_between_queries,
                'async_limit': config.async_limit,
                'min_score': config.min_score,
                'max_per_domain': config.max_per_domain,
            }
            
            config_hash = json.dumps(live_config, sort_keys=True)
            
            if self._last_config_hash is None:
                # First check - just store the hash
                self._last_config_hash = config_hash
                return None
            
            if config_hash != self._last_config_hash:
                # Config changed!
                old_hash = self._last_config_hash
                self._last_config_hash = config_hash
                
                logger.info(f"Live config update detected: {live_config}")
                return live_config
            
            return None
            
        except Exception as e:
            logger.warning(f"Could not check live config updates: {e}")
            return None
    
    def write_config_update_signal(self, config_values: Dict[str, Any]) -> bool:
        """
        Write a config update signal file that the running scraper can read.
        
        The scraper can poll this file to pick up runtime configuration changes.
        
        Args:
            config_values: Dictionary of configuration values to update
            
        Returns:
            True if signal was written successfully
        """
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            signal_file = os.path.join(project_root, '.scraper_config_update.json')
            
            signal_data = {
                'timestamp': timezone.now().isoformat(),
                'config': config_values,
                'run_id': self.current_run_id
            }
            
            with open(signal_file, 'w') as f:
                json.dump(signal_data, f)
            
            logger.info(f"Wrote config update signal to {signal_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write config update signal: {e}")
            return False
    
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
            
            # Prepare environment from CRM config (enhanced approach)
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            env = self._build_environment_from_crm()
            
            # Initialize config hash for live updates
            self._last_config_hash = None
            self.check_live_config_updates()  # Initialize tracking
            
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
            Dictionary with detailed status information including metrics
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
