"""
Scheduler module for the Hallway Display system.

This module manages the time-based scheduling for when the monitor
should be on/off based on the configured rules.
"""

import time
import datetime
import threading
from ..utils.logger import setup_logger
from ..config import settings

# Setup logger
logger = setup_logger('scheduler')

class SchedulerError(Exception):
    """Exception raised for scheduler-related errors."""
    pass

class MonitorScheduler:
    """Scheduler for monitor on/off times.
    
    This class manages the time-based scheduling for when the monitor
    should be on or off, supporting different schedules for weekdays
    and weekends.
    """
    
    def __init__(self, state_change_callback=None):
        """Initialize the monitor scheduler.
        
        Args:
            state_change_callback: Function to call when the scheduled state changes.
                The callback will be called with a boolean argument indicating
                whether the monitor should be on (True) or off (False).
        """
        self.state_change_callback = state_change_callback
        self.keep_running = False
        self.scheduler_thread = None
        self.current_state = None  # Current scheduled state (True = on, False = off)
        
        # Parse time settings
        self._parse_time_settings()
        
        logger.info("Monitor scheduler initialized")
    
    def _parse_time_settings(self):
        """Parse time settings from the configuration."""
        try:
            # Parse weekday settings
            self.weekday_morning_on_start = self._parse_time(settings.WEEKDAY_MORNING_ON_START)
            self.weekday_morning_on_end = self._parse_time(settings.WEEKDAY_MORNING_ON_END)
            self.weekday_evening_on_start = self._parse_time(settings.WEEKDAY_EVENING_ON_START)
            self.weekday_evening_on_end = self._parse_time(settings.WEEKDAY_EVENING_ON_END)
            
            # Parse weekend settings
            self.weekend_on_start = self._parse_time(settings.WEEKEND_ON_START)
            self.weekend_on_end = self._parse_time(settings.WEEKEND_ON_END)
            
            logger.debug(f"Weekday morning: {self.weekday_morning_on_start.strftime('%H:%M')} - "
                         f"{self.weekday_morning_on_end.strftime('%H:%M')}")
            logger.debug(f"Weekday evening: {self.weekday_evening_on_start.strftime('%H:%M')} - "
                         f"{self.weekday_evening_on_end.strftime('%H:%M')}")
            logger.debug(f"Weekend: {self.weekend_on_start.strftime('%H:%M')} - "
                         f"{self.weekend_on_end.strftime('%H:%M')}")
        except Exception as e:
            logger.error(f"Failed to parse time settings: {e}")
            raise SchedulerError(f"Failed to parse time settings: {e}")
    
    def _parse_time(self, time_str):
        """Parse a time string in format HH:MM.
        
        Args:
            time_str: Time string in format HH:MM.
            
        Returns:
            datetime.time: Parsed time object.
            
        Raises:
            ValueError: If the time string is invalid.
        """
        try:
            hours, minutes = map(int, time_str.split(':'))
            return datetime.time(hours, minutes)
        except Exception as e:
            raise ValueError(f"Invalid time format '{time_str}'. Expected HH:MM: {e}")
    
    def is_scheduled_on(self):
        """Check if the monitor is scheduled to be on at the current time.
        
        Returns:
            bool: True if the monitor should be on, False otherwise.
        """
        now = datetime.datetime.now()
        current_time = now.time()
        weekday = now.weekday()  # 0-6 (Monday-Sunday)
        
        # Check if it's a weekend (Saturday = 5, Sunday = 6)
        is_weekend = weekday >= 5
        
        if is_weekend:
            # Weekend schedule
            is_on = self._is_time_between(current_time, self.weekend_on_start, self.weekend_on_end)
            logger.debug(f"Weekend schedule: {'ON' if is_on else 'OFF'} at {current_time.strftime('%H:%M')}")
            return is_on
        else:
            # Weekday schedule
            morning_on = self._is_time_between(current_time, self.weekday_morning_on_start, self.weekday_morning_on_end)
            evening_on = self._is_time_between(current_time, self.weekday_evening_on_start, self.weekday_evening_on_end)
            is_on = morning_on or evening_on
            logger.debug(f"Weekday schedule: {'ON' if is_on else 'OFF'} at {current_time.strftime('%H:%M')}")
            return is_on
    
    def _is_time_between(self, current_time, start_time, end_time):
        """Check if the current time is between start and end times.
        
        Args:
            current_time: Current time to check.
            start_time: Start time of the range.
            end_time: End time of the range.
            
        Returns:
            bool: True if the current time is within the range, False otherwise.
        """
        # Handle overnight ranges (e.g., 22:00 - 06:00)
        if start_time < end_time:
            return start_time <= current_time < end_time
        else:
            return start_time <= current_time or current_time < end_time
    
    def start(self):
        """Start the scheduler thread."""
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            logger.warning("Scheduler thread already running")
            return
        
        try:
            self.keep_running = True
            self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
            self.scheduler_thread.start()
            logger.info("Monitor scheduler started")
        except Exception as e:
            logger.error(f"Failed to start scheduler thread: {e}")
            self.keep_running = False
            raise SchedulerError(f"Failed to start scheduler thread: {e}")
    
    def stop(self):
        """Stop the scheduler thread."""
        self.keep_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=2.0)
            if self.scheduler_thread.is_alive():
                logger.warning("Scheduler thread did not stop cleanly")
            else:
                logger.info("Monitor scheduler stopped")
    
    def _scheduler_loop(self):
        """Main scheduler loop."""
        while self.keep_running:
            try:
                # Check if the monitor should be on
                should_be_on = self.is_scheduled_on()
                
                # If the state has changed, notify the callback
                if should_be_on != self.current_state:
                    logger.info(f"Scheduled state changed to {'ON' if should_be_on else 'OFF'}")
                    self.current_state = should_be_on
                    if self.state_change_callback:
                        self.state_change_callback(should_be_on)
                
                # Sleep for a short period before checking again
                time.sleep(10)  # Check every 10 seconds
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(30)  # Wait longer after an error
