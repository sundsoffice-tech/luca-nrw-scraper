# -*- coding: utf-8 -*-
"""
Scraper Control Module - Manages scraper subprocess lifecycle
"""

import os
import subprocess
import psutil
import time
import threading
import queue
from typing import Optional, Dict, Any
from datetime import datetime


class ScraperController:
    """
    Manages the scraper process lifecycle.
    Handles starting, stopping, pausing, and status monitoring.
    """
    
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.pid: Optional[int] = None
        self.status: str = 'stopped'
        self.start_time: Optional[datetime] = None
        self.paused: bool = False
        self.params: Dict[str, Any] = {}
        self.output_queue: queue.Queue = queue.Queue(maxsize=1000)
        self.output_thread: Optional[threading.Thread] = None
    
    def _read_output(self):
        """Background thread to read process output."""
        try:
            while True:
                line = self.process.stdout.readline()
                if not line:  # Empty string means EOF
                    break
                if line.strip():  # Only add non-empty lines
                    self.output_queue.put(line.strip())
                    # Also send to dashboard log queue if available
                    try:
                        from dashboard.app import add_log_entry
                        add_log_entry('INFO', line.strip())
                    except Exception:
                        pass  # Silently ignore if dashboard is not available
        except Exception:
            pass  # Process may have terminated
        
    def start(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Start the scraper with given parameters.
        
        Args:
            params: Dictionary of scraper parameters
                - industry: str (recruiter, candidates, all)
                - qpi: int (queries per industry)
                - mode: str (standard, headhunter, aggressive, snippet_only, learning)
                - smart: bool
                - force: bool
                - once: bool
                - dry_run: bool
                
        Returns:
            Dictionary with status and process info
        """
        if self.is_running():
            return {
                'success': False,
                'error': 'Scraper is already running',
                'status': self.status
            }
        
        try:
            # Build command
            # Allow configuration via environment variable or default to scriptname.py
            script_name = os.getenv('LUCA_SCRAPER_SCRIPT', 'scriptname.py')
            script_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                script_name
            )
            
            cmd = ['python', script_path]
            
            # Add parameters
            industry = params.get('industry', 'recruiter')
            cmd.extend(['--industry', industry])
            
            qpi = params.get('qpi', 15)
            cmd.extend(['--qpi', str(qpi)])
            
            mode = params.get('mode', 'standard')
            if mode and mode != 'standard':
                cmd.extend(['--mode', mode])
            
            if params.get('smart', True):
                cmd.append('--smart')
            
            if params.get('force', False):
                cmd.append('--force')
            
            if params.get('once', True):
                cmd.append('--once')
            
            if params.get('dry_run', False):
                cmd.append('--dry-run')
            
            # Get the project root directory (where .env and scriptname.py are)
            project_root = os.path.dirname(os.path.dirname(__file__))
            
            # Load .env file if python-dotenv is available
            env = os.environ.copy()
            env_file = os.path.join(project_root, '.env')
            if os.path.exists(env_file):
                try:
                    from dotenv import dotenv_values
                    env_vars = dotenv_values(env_file)
                    env.update(env_vars)
                except ImportError:
                    # python-dotenv not available, continue without loading
                    pass
            
            # Start process with correct working directory and environment
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                cwd=project_root,  # IMPORTANT: Set working directory
                env=env  # IMPORTANT: Pass environment variables
            )
            
            self.pid = self.process.pid
            self.status = 'running'
            self.start_time = datetime.now()
            self.params = params
            self.paused = False
            
            # Start output reader thread
            self.output_thread = threading.Thread(target=self._read_output, daemon=True)
            self.output_thread.start()
            
            # Wait briefly to check if process started successfully
            time.sleep(0.5)
            if self.process.poll() is not None:
                # Process already terminated - get error output
                remaining_output = []
                try:
                    while True:
                        line = self.process.stdout.readline()
                        if not line:
                            break
                        remaining_output.append(line.strip())
                except Exception:
                    pass  # Continue even if reading fails
                
                error_msg = '\n'.join(remaining_output) if remaining_output else 'Process terminated without output'
                self.status = 'error'
                return {
                    'success': False,
                    'error': f'Scraper terminated immediately: {error_msg[:500]}',
                    'status': 'error'
                }
            
            return {
                'success': True,
                'status': self.status,
                'pid': self.pid,
                'params': self.params
            }
            
        except Exception as e:
            self.status = 'error'
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
                'error': 'No scraper process running',
                'status': self.status
            }
        
        try:
            if self.process:
                # Try graceful termination first
                self.process.terminate()
                
                # Wait up to 10 seconds for process to terminate
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
            
            self.status = 'stopped'
            self.pid = None
            self.start_time = None
            self.paused = False
            
            return {
                'success': True,
                'status': self.status
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'status': self.status
            }
    
    def pause(self) -> Dict[str, Any]:
        """
        Pause the running scraper process (SIGSTOP).
        
        Returns:
            Dictionary with status
        """
        if not self.is_running():
            return {
                'success': False,
                'error': 'No scraper process running',
                'status': self.status
            }
        
        if self.paused:
            return {
                'success': False,
                'error': 'Scraper is already paused',
                'status': 'paused'
            }
        
        try:
            if self.pid:
                proc = psutil.Process(self.pid)
                proc.suspend()
                self.paused = True
                self.status = 'paused'
                
            return {
                'success': True,
                'status': self.status
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'status': self.status
            }
    
    def resume(self) -> Dict[str, Any]:
        """
        Resume the paused scraper process (SIGCONT).
        
        Returns:
            Dictionary with status
        """
        if not self.paused:
            return {
                'success': False,
                'error': 'Scraper is not paused',
                'status': self.status
            }
        
        try:
            if self.pid:
                proc = psutil.Process(self.pid)
                proc.resume()
                self.paused = False
                self.status = 'running'
                
            return {
                'success': True,
                'status': self.status
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'status': self.status
            }
    
    def reset(self, db_path: str) -> Dict[str, Any]:
        """
        Reset URL cache and queries.
        
        Args:
            db_path: Path to SQLite database
            
        Returns:
            Dictionary with status
        """
        try:
            import sqlite3
            
            con = sqlite3.connect(db_path)
            cur = con.cursor()
            
            # Reset queries_done and urls_seen
            cur.execute("DELETE FROM queries_done")
            cur.execute("DELETE FROM urls_seen")
            
            con.commit()
            con.close()
            
            return {
                'success': True,
                'message': 'Cache and queries reset successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
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
            self.status = 'stopped'
            self.pid = None
            self.start_time = None
            self.paused = False
        
        status_info = {
            'status': self.status,
            'pid': self.pid,
            'paused': self.paused,
            'params': self.params if self.status != 'stopped' else {}
        }
        
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()
            status_info['uptime_seconds'] = int(uptime)
            status_info['start_time'] = self.start_time.isoformat()
        
        # Get process info if running
        if self.pid and self.is_running():
            try:
                proc = psutil.Process(self.pid)
                # Use interval=0 for non-blocking call (returns 0.0 on first call)
                status_info['cpu_percent'] = proc.cpu_percent(interval=0)
                status_info['memory_mb'] = proc.memory_info().rss / 1024 / 1024
            except (psutil.NoSuchProcess, psutil.AccessDenied):
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
    
    def get_output(self, lines: int = 50) -> list:
        """
        Get recent output from the scraper process.
        
        Args:
            lines: Maximum number of lines to return from the queue
            
        Returns:
            List of output lines (up to 'lines' count)
        """
        output = []
        # Retrieve up to 'lines' items from the queue
        while not self.output_queue.empty() and len(output) < lines:
            try:
                output.append(self.output_queue.get_nowait())
            except queue.Empty:
                break
        return output


# Global controller instance
_controller = ScraperController()


def get_controller() -> ScraperController:
    """Get the global scraper controller instance."""
    return _controller
