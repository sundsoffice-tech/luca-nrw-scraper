"""
OutputMonitor - Handles process output reading and log management.
Responsible for reading subprocess output, storing logs, and persisting to database.
"""

import threading
import logging
from typing import Optional, List, Dict, Any
from collections import deque
from datetime import datetime
from django.utils import timezone

logger = logging.getLogger(__name__)


class OutputMonitor:
    """
    Monitors and manages subprocess output and logging.
    Reads process stdout, maintains in-memory log buffer, and persists to database.
    """

    def __init__(self, max_logs: int = 1000):
        self.logs: List[Dict[str, Any]] = []
        self.max_logs = max_logs
        self.output_thread: Optional[threading.Thread] = None
        self.current_run_id: Optional[int] = None
        self._stop_monitoring = False
        self._lock = threading.Lock()  # Thread-safe access to logs

    def start_monitoring(self, process, current_run_id: int, error_callback=None, completion_callback=None):
        """
        Start monitoring process output in a background thread.

        Args:
            process: subprocess.Popen object to monitor
            current_run_id: ID of the current ScraperRun
            error_callback: Callback function for error detection, signature: (error_type: str) -> None
            completion_callback: Callback function for process completion, signature: (exit_code: int, runtime: float) -> None
        """
        self.current_run_id = current_run_id
        self._stop_monitoring = False
        self.output_thread = threading.Thread(
            target=self._read_output,
            args=(process, error_callback, completion_callback),
            daemon=True
        )
        self.output_thread.start()

    def stop_monitoring(self):
        """Stop the output monitoring thread."""
        self._stop_monitoring = True
        if self.output_thread and self.output_thread.is_alive():
            self.output_thread.join(timeout=2)

    def _read_output(self, process, error_callback=None, completion_callback=None):
        """
        Background thread to read and store process output.

        Args:
            process: subprocess.Popen object
            error_callback: Callback for error detection
            completion_callback: Callback for process completion
        """
        start_time = timezone.now()

        try:
            while not self._stop_monitoring:
                line = process.stdout.readline()
                if not line:  # EOF
                    # Log that process ended
                    exit_code = process.poll()
                    runtime = (timezone.now() - start_time).total_seconds()
                    logger.warning(f"Scraper process ended with exit code: {exit_code}")

                    # Call completion callback if provided
                    if completion_callback:
                        completion_callback(exit_code, runtime)

                    break

                if line.strip():
                    self._process_log_line(line.strip(), error_callback)

        except Exception as e:
            logger.error(f"Error reading scraper output: {e}")

    def _process_log_line(self, line: str, error_callback=None):
        """
        Process a single log line: store in memory and persist to database.

        Args:
            line: Log line to process
            error_callback: Callback for error detection
        """
        timestamp = timezone.now()
        log_entry = {
            'timestamp': timestamp.isoformat(),
            'message': line
        }
        with self._lock:
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
                    run.logs += f"\n{line}"
                else:
                    run.logs = line

                # Keep logs reasonable size
                if len(run.logs) > 50000:  # ~50KB
                    run.logs = run.logs[-50000:]
                run.save(update_fields=['logs'])

                # Determine log level from message
                level = self._detect_log_level(line)

                # Create ScraperLog entry for SSE streaming
                ScraperLog.objects.create(
                    run=run,
                    level=level,
                    message=line
                )

                # Detect common errors and notify callback
                if error_callback:
                    error_type = self._detect_error_type(line)
                    if error_type:
                        error_callback(error_type)

            except Exception as e:
                logger.error(f"Failed to update ScraperRun logs: {e}")

    def _detect_log_level(self, message: str) -> str:
        """
        Detect log level from message content.

        Args:
            message: Log message

        Returns:
            Log level string (INFO, WARN, ERROR)
        """
        message_lower = message.lower()
        if 'error' in message_lower or 'exception' in message_lower:
            return 'ERROR'
        elif 'warn' in message_lower or 'warning' in message_lower:
            return 'WARN'
        return 'INFO'

    def _detect_error_type(self, line: str) -> Optional[str]:
        """
        Detect error type from log line.

        Args:
            line: Log line to analyze

        Returns:
            Error type string or None if no error detected
        """
        message_lower = line.lower()

        if 'ModuleNotFoundError' in line:
            return 'missing_module'
        elif 'KeyError' in line or 'AttributeError' in line:
            return 'config_error'
        elif 'rate limit' in message_lower:
            return 'rate_limit'
        elif 'ConnectionError' in line or ('connection' in message_lower and 'error' in message_lower):
            return 'connection_error'
        elif 'TimeoutError' in line or 'timeout' in message_lower:
            return 'timeout'
        elif 'ParseError' in line or ('parsing' in message_lower and 'error' in message_lower):
            return 'parsing_error'

        return None

    def log_error(self, message: str):
        """
        Log an error message to the current run.

        Args:
            message: Error message to log
        """
        if self.current_run_id:
            try:
                from .models import ScraperLog, ScraperRun
                run = ScraperRun.objects.get(id=self.current_run_id)
                
                # Create ScraperLog entry for SSE streaming
                ScraperLog.objects.create(
                    run=run,
                    level='ERROR',
                    message=message
                )
                
                # CRITICAL FIX: Also append to run.logs for persistence
                if run.logs:
                    run.logs += f"\n{message}"
                else:
                    run.logs = message
                
                # Keep logs reasonable size
                if len(run.logs) > 50000:  # ~50KB
                    run.logs = run.logs[-50000:]
                run.save(update_fields=['logs'])
                
            except Exception as e:
                logger.error(f"Failed to log error: {e}")

    def get_logs(self, lines: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent logs from the scraper process.

        Args:
            lines: Maximum number of log entries to return

        Returns:
            List of log entries (most recent first)
        """
        with self._lock:
            return self.logs[-lines:] if self.logs else []

    def get_final_output(self, max_chars: int = 5000) -> str:
        """
        Get the last N characters of output for error diagnosis.
        
        This is useful when the process exits early and we need to capture
        the actual error message that caused the exit.
        
        Args:
            max_chars: Maximum number of characters to return (default: 5000)
            
        Returns:
            String containing the last N characters of all log output
        """
        with self._lock:
            if not self.logs:
                return ""
            
            # Get last 50 log entries (or all if fewer)
            recent_logs = self.logs[-50:]
            all_logs = "\n".join(entry.get('message', '') for entry in recent_logs)
            
            # Return last max_chars characters
            return all_logs[-max_chars:] if len(all_logs) > max_chars else all_logs

    def clear_logs(self):
        """Clear the in-memory log buffer."""
        self.logs = []
