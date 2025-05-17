"""
Display control module for the Hallway Display system.

This module manages the display of DakBoard and Home Assistant
by controlling Chromium browser instances.
"""

import subprocess
import time
import threading
import os
import signal
import psutil
import sys

# Add the project root to the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import setup_logger
from config import settings

# Setup logger
logger = setup_logger('display')

class DisplayError(Exception):
    """Exception raised for display-related errors."""
    pass

class DisplayController:
    """Controller for displaying DakBoard and Home Assistant.
    
    This class manages separate browser instances for DakBoard and Home Assistant,
    and provides methods to switch between them.
    """
    
    def __init__(self):
        """Initialize the display controller."""
        self.dakboard_process = None
        self.homeassistant_process = None
        self.current_display = None  # 'dakboard' or 'homeassistant'
        self.last_interaction_time = 0
        self.inactivity_timer = None
        self.keep_running = False
        logger.info("Display controller initialized")
    
    def start(self):
        """Start the display controller and launch browser instances."""
        try:
            # Launch DakBoard browser
            self._launch_dakboard()
            
            # Wait for DakBoard to initialize
            time.sleep(3)
            
            # Launch Home Assistant browser (hidden initially)
            self._launch_homeassistant()
            
            # Set DakBoard as the active display
            self._activate_dakboard()
            
            # Start inactivity timer
            self.keep_running = True
            self.inactivity_timer = threading.Thread(target=self._check_inactivity, daemon=True)
            self.inactivity_timer.start()
            
            logger.info("Display controller started")
            return True
        except Exception as e:
            logger.error(f"Failed to start display controller: {e}")
            self.stop()  # Clean up if there's an error
            return False
    
    def stop(self):
        """Stop the display controller and close browser instances."""
        self.keep_running = False
        
        # Stop inactivity timer
        if self.inactivity_timer:
            self.inactivity_timer.join(timeout=2.0)
        
        # Close browser instances
        self._close_browsers()
        
        logger.info("Display controller stopped")
    
    def switch_to_dakboard(self):
        """Switch to the DakBoard display."""
        if self.current_display == 'dakboard':
            logger.debug("Already on DakBoard display")
            return True
        
        logger.info("Switching to DakBoard display")
        return self._activate_dakboard()
    
    def switch_to_homeassistant(self):
        """Switch to the Home Assistant display."""
        if self.current_display == 'homeassistant':
            logger.debug("Already on Home Assistant display")
            return True
        
        logger.info("Switching to Home Assistant display")
        self.last_interaction_time = time.time()  # Reset interaction time
        return self._activate_homeassistant()
    
    def handle_touch(self):
        """Handle a touch event.
        
        This method should be called when a touch event is detected.
        It will switch to Home Assistant if we're on DakBoard,
        or reset the inactivity timer if we're already on Home Assistant.
        """
        logger.debug("Touch event detected")
        self.last_interaction_time = time.time()
        
        if self.current_display == 'dakboard':
            logger.info("Touch on DakBoard, switching to Home Assistant")
            return self.switch_to_homeassistant()
        else:
            logger.debug("Touch on Home Assistant, resetting inactivity timer")
            return True
    
    def _launch_dakboard(self):
        """Launch the DakBoard browser instance."""
        try:
            logger.info("Launching DakBoard browser")
            command = [
                settings.BROWSER_COMMAND,
                settings.DAKBOARD_URL,
                "--window-position=0,0",
                "--window-size=1920,1080",
                "--user-data-dir=/tmp/dakboard_profile"
            ]
            command.extend(settings.BROWSER_KIOSK_ARGS)
            
            # Launch browser with DISPLAY environment variable set
            env = os.environ.copy()
            env['DISPLAY'] = ':0'
            
            self.dakboard_process = subprocess.Popen(
                command,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            logger.debug(f"DakBoard browser launched with PID {self.dakboard_process.pid}")
            return True
        except Exception as e:
            logger.error(f"Failed to launch DakBoard browser: {e}")
            return False
    
    def _launch_homeassistant(self):
        """Launch the Home Assistant browser instance."""
        try:
            logger.info("Launching Home Assistant browser")
            command = [
                settings.BROWSER_COMMAND,
                settings.HOME_ASSISTANT_URL,
                "--window-position=0,0",
                "--window-size=1920,1080",
                "--user-data-dir=/tmp/homeassistant_profile"
            ]
            command.extend(settings.BROWSER_KIOSK_ARGS)
            
            # Launch browser with DISPLAY environment variable set
            env = os.environ.copy()
            env['DISPLAY'] = ':0'
            
            self.homeassistant_process = subprocess.Popen(
                command,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            logger.debug(f"Home Assistant browser launched with PID {self.homeassistant_process.pid}")
            
            # Initially hide the Home Assistant window
            self._hide_homeassistant()
            
            return True
        except Exception as e:
            logger.error(f"Failed to launch Home Assistant browser: {e}")
            return False
    
    def _activate_dakboard(self):
        """Activate the DakBoard window and hide Home Assistant."""
        try:
            # Check if DakBoard process is running
            if not self.dakboard_process or self.dakboard_process.poll() is not None:
                logger.warning("DakBoard browser not running, relaunching")
                self._launch_dakboard()
            
            # Show DakBoard window
            self._show_dakboard()
            
            # Hide Home Assistant window
            self._hide_homeassistant()
            
            self.current_display = 'dakboard'
            logger.debug("DakBoard display activated")
            return True
        except Exception as e:
            logger.error(f"Failed to activate DakBoard display: {e}")
            return False
    
    def _activate_homeassistant(self):
        """Activate the Home Assistant window and hide DakBoard."""
        try:
            # Check if Home Assistant process is running
            if not self.homeassistant_process or self.homeassistant_process.poll() is not None:
                logger.warning("Home Assistant browser not running, relaunching")
                self._launch_homeassistant()
            
            # Show Home Assistant window
            self._show_homeassistant()
            
            # Hide DakBoard window
            self._hide_dakboard()
            
            self.current_display = 'homeassistant'
            logger.debug("Home Assistant display activated")
            return True
        except Exception as e:
            logger.error(f"Failed to activate Home Assistant display: {e}")
            return False
    
    def _show_dakboard(self):
        """Show the DakBoard window."""
        try:
            if self.dakboard_process and self.dakboard_process.poll() is None:
                pid = self.dakboard_process.pid
                subprocess.run(["xdotool", "search", "--pid", str(pid), "windowmap"], check=False)
                subprocess.run(["xdotool", "search", "--pid", str(pid), "windowraise"], check=False)
                logger.debug("DakBoard window shown and raised")
            else:
                logger.warning("Cannot show DakBoard window - process not running")
        except Exception as e:
            logger.error(f"Failed to show DakBoard window: {e}")
    
    def _hide_dakboard(self):
        """Hide the DakBoard window."""
        try:
            if self.dakboard_process and self.dakboard_process.poll() is None:
                pid = self.dakboard_process.pid
                subprocess.run(["xdotool", "search", "--pid", str(pid), "windowunmap"], check=False)
                logger.debug("DakBoard window hidden")
            else:
                logger.warning("Cannot hide DakBoard window - process not running")
        except Exception as e:
            logger.error(f"Failed to hide DakBoard window: {e}")
    
    def _show_homeassistant(self):
        """Show the Home Assistant window."""
        try:
            if self.homeassistant_process and self.homeassistant_process.poll() is None:
                pid = self.homeassistant_process.pid
                subprocess.run(["xdotool", "search", "--pid", str(pid), "windowmap"], check=False)
                subprocess.run(["xdotool", "search", "--pid", str(pid), "windowraise"], check=False)
                logger.debug("Home Assistant window shown and raised")
            else:
                logger.warning("Cannot show Home Assistant window - process not running")
        except Exception as e:
            logger.error(f"Failed to show Home Assistant window: {e}")
    
    def _hide_homeassistant(self):
        """Hide the Home Assistant window."""
        try:
            if self.homeassistant_process and self.homeassistant_process.poll() is None:
                pid = self.homeassistant_process.pid
                subprocess.run(["xdotool", "search", "--pid", str(pid), "windowunmap"], check=False)
                logger.debug("Home Assistant window hidden")
            else:
                logger.warning("Cannot hide Home Assistant window - process not running")
        except Exception as e:
            logger.error(f"Failed to hide Home Assistant window: {e}")
    
    def _close_browsers(self):
        """Close all browser instances."""
        try:
            # Close DakBoard browser
            if self.dakboard_process and self.dakboard_process.poll() is None:
                logger.debug(f"Closing DakBoard browser (PID {self.dakboard_process.pid})")
                try:
                    # Try to terminate gracefully first
                    self.dakboard_process.terminate()
                    self.dakboard_process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    # If it doesn't terminate, force kill
                    logger.warning("DakBoard browser didn't terminate, force killing")
                    self.dakboard_process.kill()
                    
            # Close Home Assistant browser
            if self.homeassistant_process and self.homeassistant_process.poll() is None:
                logger.debug(f"Closing Home Assistant browser (PID {self.homeassistant_process.pid})")
                try:
                    # Try to terminate gracefully first
                    self.homeassistant_process.terminate()
                    self.homeassistant_process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    # If it doesn't terminate, force kill
                    logger.warning("Home Assistant browser didn't terminate, force killing")
                    self.homeassistant_process.kill()
                    
            # Kill any orphaned browser processes
            self._kill_orphaned_browsers()
                    
            logger.info("All browser instances closed")
        except Exception as e:
            logger.error(f"Error closing browser instances: {e}")
    
    def _kill_orphaned_browsers(self):
        """Find and kill any orphaned browser processes."""
        try:
            browser_name = os.path.basename(settings.BROWSER_COMMAND)
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    # Check if this is a browser process we launched
                    if proc.info['name'] and browser_name in proc.info['name'].lower():
                        if proc.info['cmdline'] and any(arg in ' '.join(proc.info['cmdline']) for arg in [
                            '/tmp/dakboard_profile', 
                            '/tmp/homeassistant_profile',
                            settings.DAKBOARD_URL,
                            settings.HOME_ASSISTANT_URL
                        ]):
                            logger.warning(f"Killing orphaned browser process: PID {proc.info['pid']}")
                            proc.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
        except Exception as e:
            logger.error(f"Error killing orphaned browsers: {e}")
    
    def _check_inactivity(self):
        """Check for inactivity and switch back to DakBoard if needed."""
        while self.keep_running:
            try:
                # Check if we're on Home Assistant and need to switch back to DakBoard
                if self.current_display == 'homeassistant':
                    current_time = time.time()
                    time_since_interaction = current_time - self.last_interaction_time
                    
                    if time_since_interaction > settings.INACTIVITY_TIMEOUT:
                        logger.info(f"Inactivity timeout reached ({settings.INACTIVITY_TIMEOUT}s). Switching back to DakBoard.")
                        self.switch_to_dakboard()
                
                # Sleep for a short period before checking again
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error in inactivity checker: {e}")
                time.sleep(5)  # Wait longer after an error
