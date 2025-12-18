# -*- coding: utf-8 -*-
"""
Scheduler Module - Manages automatic scraper runs based on schedule
"""

import sqlite3
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable


class ScraperScheduler:
    """
    Manages automatic scraper runs based on configurable schedule.
    """
    
    def __init__(self, db_path: str, start_callback: Callable):
        """
        Initialize scheduler.
        
        Args:
            db_path: Path to SQLite database
            start_callback: Function to call to start scraper
        """
        self.db_path = db_path
        self.start_callback = start_callback
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
    def get_config(self) -> Dict[str, Any]:
        """
        Get scheduler configuration from database.
        
        Returns:
            Dictionary with scheduler configuration
        """
        try:
            con = sqlite3.connect(self.db_path)
            cur = con.cursor()
            
            cur.execute("SELECT * FROM scheduler_config WHERE id = 1")
            row = cur.fetchone()
            
            if row:
                config = {
                    'id': row[0],
                    'enabled': bool(row[1]),
                    'interval_hours': row[2],
                    'pause_start_hour': row[3],
                    'pause_end_hour': row[4],
                    'pause_weekends': bool(row[5]),
                    'last_run': row[6],
                    'next_run': row[7],
                    'created_at': row[8],
                    'updated_at': row[9]
                }
            else:
                # Create default config
                cur.execute("""
                    INSERT INTO scheduler_config 
                    (id, enabled, interval_hours, pause_start_hour, pause_end_hour, pause_weekends)
                    VALUES (1, 0, 2.0, 23, 6, 0)
                """)
                con.commit()
                config = {
                    'id': 1,
                    'enabled': False,
                    'interval_hours': 2.0,
                    'pause_start_hour': 23,
                    'pause_end_hour': 6,
                    'pause_weekends': False,
                    'last_run': None,
                    'next_run': None,
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
            
            con.close()
            return config
            
        except Exception as e:
            return {
                'error': str(e),
                'enabled': False,
                'interval_hours': 2.0
            }
    
    def update_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update scheduler configuration.
        
        Args:
            config: Dictionary with configuration values
            
        Returns:
            Updated configuration with next_run calculated
        """
        try:
            con = sqlite3.connect(self.db_path)
            cur = con.cursor()
            
            # Ensure config row exists
            cur.execute("SELECT id FROM scheduler_config WHERE id = 1")
            if not cur.fetchone():
                cur.execute("""
                    INSERT INTO scheduler_config (id) VALUES (1)
                """)
            
            # Update fields
            update_fields = []
            update_values = []
            
            if 'enabled' in config:
                update_fields.append('enabled = ?')
                update_values.append(int(config['enabled']))
            
            if 'interval_hours' in config:
                update_fields.append('interval_hours = ?')
                update_values.append(float(config['interval_hours']))
            
            if 'pause_start_hour' in config:
                update_fields.append('pause_start_hour = ?')
                update_values.append(int(config['pause_start_hour']))
            
            if 'pause_end_hour' in config:
                update_fields.append('pause_end_hour = ?')
                update_values.append(int(config['pause_end_hour']))
            
            if 'pause_weekends' in config:
                update_fields.append('pause_weekends = ?')
                update_values.append(int(config['pause_weekends']))
            
            # Always update timestamp
            update_fields.append('updated_at = ?')
            update_values.append(datetime.now().isoformat())
            
            # Calculate next run
            next_run = self.calculate_next_run(config)
            if next_run:
                update_fields.append('next_run = ?')
                update_values.append(next_run.isoformat())
            
            update_values.append(1)  # WHERE id = 1
            
            query = f"UPDATE scheduler_config SET {', '.join(update_fields)} WHERE id = ?"
            cur.execute(query, update_values)
            
            con.commit()
            con.close()
            
            # Restart scheduler if it was running
            if self.running:
                self.stop()
                if config.get('enabled', False):
                    self.start()
            elif config.get('enabled', False):
                self.start()
            
            result = self.get_config()
            result['next_run_datetime'] = next_run.isoformat() if next_run else None
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def calculate_next_run(self, config: Optional[Dict[str, Any]] = None) -> Optional[datetime]:
        """
        Calculate next scheduled run time.
        
        Args:
            config: Optional config dictionary, otherwise fetches from DB
            
        Returns:
            datetime of next run or None if disabled
        """
        if config is None:
            config = self.get_config()
        
        if not config.get('enabled', False):
            return None
        
        interval_hours = config.get('interval_hours', 2.0)
        pause_start = config.get('pause_start_hour', 23)
        pause_end = config.get('pause_end_hour', 6)
        pause_weekends = config.get('pause_weekends', False)
        
        # Start from now
        next_run = datetime.now()
        
        # If there was a last run, add interval
        last_run_str = config.get('last_run')
        if last_run_str:
            try:
                last_run = datetime.fromisoformat(last_run_str)
                next_run = last_run + timedelta(hours=interval_hours)
            except:
                pass
        
        # Ensure next run is in the future
        if next_run <= datetime.now():
            next_run = datetime.now() + timedelta(hours=interval_hours)
        
        # Skip if in night pause
        while self._is_in_pause(next_run, pause_start, pause_end, pause_weekends):
            next_run += timedelta(hours=1)
        
        return next_run
    
    def _is_in_pause(self, dt: datetime, pause_start: int, pause_end: int, pause_weekends: bool) -> bool:
        """
        Check if given datetime is within pause period.
        
        Args:
            dt: DateTime to check
            pause_start: Start hour of night pause (23)
            pause_end: End hour of night pause (6)
            pause_weekends: Whether weekends are paused
            
        Returns:
            True if in pause period
        """
        # Check weekend
        if pause_weekends and dt.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return True
        
        # Check night pause
        hour = dt.hour
        if pause_start > pause_end:
            # Pause spans midnight (e.g., 23:00 to 06:00)
            if hour >= pause_start or hour < pause_end:
                return True
        else:
            # Pause within same day (e.g., 01:00 to 05:00)
            if pause_start <= hour < pause_end:
                return True
        
        return False
    
    def start(self):
        """Start the scheduler thread."""
        if self.running:
            return
        
        config = self.get_config()
        if not config.get('enabled', False):
            return
        
        self.running = True
        self._stop_event.clear()
        self.thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop the scheduler thread."""
        self.running = False
        self._stop_event.set()
        if self.thread:
            self.thread.join(timeout=2)
            self.thread = None
    
    def _scheduler_loop(self):
        """Main scheduler loop."""
        while self.running and not self._stop_event.is_set():
            try:
                config = self.get_config()
                
                if not config.get('enabled', False):
                    # Disabled, stop the thread
                    break
                
                # Check if it's time to run
                next_run_str = config.get('next_run')
                if next_run_str:
                    next_run = datetime.fromisoformat(next_run_str)
                    
                    if datetime.now() >= next_run:
                        # Time to run!
                        pause_start = config.get('pause_start_hour', 23)
                        pause_end = config.get('pause_end_hour', 6)
                        pause_weekends = config.get('pause_weekends', False)
                        
                        # Double-check we're not in pause period
                        if not self._is_in_pause(datetime.now(), pause_start, pause_end, pause_weekends):
                            # Start the scraper
                            self._execute_scheduled_run(config)
                        
                        # Update last_run and calculate next_run
                        self._update_run_times(config)
                
            except Exception as e:
                print(f"Scheduler error: {e}")
            
            # Sleep for 60 seconds before checking again
            self._stop_event.wait(60)
    
    def _execute_scheduled_run(self, config: Dict[str, Any]):
        """
        Execute a scheduled scraper run.
        
        Args:
            config: Scheduler configuration
        """
        try:
            # Default parameters for scheduled runs
            params = {
                'industry': 'recruiter',
                'qpi': 15,
                'mode': 'standard',
                'smart': True,
                'force': False,
                'once': True,
                'dry_run': False
            }
            
            # Call the start callback
            self.start_callback(params)
            
        except Exception as e:
            print(f"Error executing scheduled run: {e}")
    
    def _update_run_times(self, config: Dict[str, Any]):
        """
        Update last_run and next_run in database.
        
        Args:
            config: Current configuration
        """
        try:
            con = sqlite3.connect(self.db_path)
            cur = con.cursor()
            
            now = datetime.now()
            next_run = self.calculate_next_run(config)
            
            cur.execute("""
                UPDATE scheduler_config 
                SET last_run = ?, next_run = ?, updated_at = ?
                WHERE id = 1
            """, (now.isoformat(), next_run.isoformat() if next_run else None, now.isoformat()))
            
            con.commit()
            con.close()
            
        except Exception as e:
            print(f"Error updating run times: {e}")


# Global scheduler instance
_scheduler: Optional[ScraperScheduler] = None


def get_scheduler(db_path: str, start_callback: Callable) -> ScraperScheduler:
    """
    Get the global scheduler instance.
    
    Args:
        db_path: Path to SQLite database
        start_callback: Function to call to start scraper
        
    Returns:
        ScraperScheduler instance
    """
    global _scheduler
    if _scheduler is None:
        _scheduler = ScraperScheduler(db_path, start_callback)
    return _scheduler
