"""
ProcessLauncher - Handles finding and launching the scraper subprocess.
Responsible for script discovery, command building, and subprocess lifecycle.
"""

import os
import subprocess
import shlex
from typing import Optional, Dict, Any, Tuple, List
import logging

logger = logging.getLogger(__name__)


class ProcessLauncher:
    """
    Manages the lifecycle of the scraper subprocess.
    Handles script discovery, command building, and process start/stop operations.
    """

    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.pid: Optional[int] = None

    def find_scraper_script(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Find the scraper script to execute.

        Returns:
            Tuple of (script_type, script_path) where script_type is 'module' or 'script'
        """
        # Get project root (parent of telis_recruitment)
        # This file is in telis_recruitment/scraper_control/process_launcher.py
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

    def build_command(self, params: Dict[str, Any], script_type: str, script_path: str) -> List[str]:
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

    def preview_command(self, params: Dict[str, Any]) -> str:
        """
        Return the scraper command string for the current params without starting the process.

        Args:
            params: Scraper parameters

        Returns:
            Command string for preview

        Raises:
            ValueError: If scraper script not found
        """
        script_type, script_path = self.find_scraper_script()
        if script_type is None:
            raise ValueError("Scraper script not found (scriptname.py, luca_scraper/__main__.py, scriptname_backup.py)")

        cmd = self.build_command(params, script_type, script_path)
        preview = ' '.join(shlex.quote(part) for part in cmd)
        logger.debug(f"Preview command: {preview}")
        return preview

    def apply_env_overrides(self, env: Dict[str, str], overrides: Dict[str, str]):
        """
        Apply ScraperConfig-provided environment overrides.

        Args:
            env: Base environment dictionary
            overrides: Environment variable overrides to apply
        """
        for key, value in overrides.items():
            if value:
                env[key] = value

    def start_process(self, cmd: List[str], env: Dict[str, str], cwd: str) -> subprocess.Popen:
        """
        Start the scraper subprocess.

        Args:
            cmd: Command and arguments
            env: Environment variables
            cwd: Working directory

        Returns:
            The started subprocess.Popen object
        """
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
            cwd=cwd,
            env=env
        )
        self.pid = self.process.pid
        logger.info(f"Scraper started with PID {self.pid}")
        return self.process

    def stop_process(self) -> bool:
        """
        Stop the running scraper process.

        Returns:
            True if process was stopped successfully, False otherwise
        """
        if not self.process:
            return False

        try:
            # Try graceful termination first
            self.process.terminate()

            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                # Force kill if still running
                self.process.kill()
                self.process.wait()

            self.process = None
            logger.info("Scraper process stopped successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to stop scraper process: {e}", exc_info=True)
            return False

    def is_running(self) -> bool:
        """
        Check if the subprocess is currently running.

        Returns:
            True if running, False otherwise
        """
        if self.process and self.process.poll() is None:
            return True
        return False

    def get_exit_code(self) -> Optional[int]:
        """
        Get the exit code of the process if it has exited.

        Returns:
            Exit code or None if process is still running
        """
        if self.process:
            return self.process.poll()
        return None
