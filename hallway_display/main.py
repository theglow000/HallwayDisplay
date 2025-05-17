#!/usr/bin/env python3
"""
Main controller for the Hallway Display system.

This is the main entry point for the Hallway Display system, which
coordinates between all modules to implement the business logic.
"""

import os
import time
import signal
import sys
import threading
import evdev
from modules.sensor import SensorManager
from modules.monitor import MonitorController
from modules.display import DisplayController
from modules.scheduler import MonitorScheduler
from modules.config_launcher import ConfigLauncher
from utils.logger import setup_logger
from config import settings

# Setup logger
logger = setup_logger('main')

class HallwayDisplay:
    """Main controller for the Hallway Display system.
    
    This class coordinates between all modules to implement the business
    logic for the Hallway Display system.
    """
    
    def __init__(self):
        """Initialize the Hallway Display controller."""
        self.sensor_manager = None
        self.monitor_controller = None
        self.display_controller = None
        self.scheduler = None
        self.touch_device = None
        self.touch_thread = None
        self.keep_running = False
        self.motion_detected = False
        self.last_motion_time = 0
        self.config_launcher = None
        
        logger.info("Hallway Display controller initialized")
    
    def initialize(self):
        """Initialize all modules."""
        try:
            # Initialize monitor controller
            logger.info("Initializing monitor controller...")
            self.monitor_controller = MonitorController()
            
            # Initialize scheduler with callback
            logger.info("Initializing scheduler...")
            self.scheduler = MonitorScheduler(state_change_callback=self._handle_schedule_change)
            
            # Initialize display controller
            logger.info("Initializing display controller...")
            self.display_controller = DisplayController()
            
            # Initialize sensor manager with callbacks
            logger.info("Initializing sensor manager...")
            self.sensor_manager = SensorManager(
                motion_callback=self._handle_motion_event,
                light_change_callback=self._handle_light_change
            )
            
            logger.info("All modules initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize modules: {e}")
            return False
    
    def start(self):
        """Start the Hallway Display system."""
        if not self.initialize():
            logger.error("Failed to initialize. Exiting.")
            return False
        
        try:
            # Register signal handlers for graceful shutdown
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            # Start scheduler
            logger.info("Starting scheduler...")
            self.scheduler.start()
            
            # Start sensor manager
            logger.info("Starting sensor manager...")
            self.sensor_manager.start()
            
            # Start display controller
            logger.info("Starting display controller...")
            self.display_controller.start()
            
            # Start touch monitoring
            logger.info("Starting touch monitoring...")
            self._start_touch_monitoring()
            
            # Start configuration launcher
            logger.info("Starting configuration launcher...")
            self.config_launcher = ConfigLauncher(position="bottom-right", size=50, opacity=0.6)
            self.config_launcher.start()
            
            # Set keep_running flag
            self.keep_running = True
            
            # Check initial schedule state
            scheduled_on = self.scheduler.is_scheduled_on()
            logger.info(f"Initial scheduled state: {'ON' if scheduled_on else 'OFF'}")
            self._set_monitor_state(scheduled_on)
            
            logger.info("Hallway Display system started successfully")
            logger.info(f"DakBoard URL: {settings.DAKBOARD_URL}")
            logger.info(f"Home Assistant URL: {settings.HOME_ASSISTANT_URL}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to start Hallway Display system: {e}")
            self.stop()
            return False
    
    def run(self):
        """Run the main loop."""
        if not self.keep_running:
            if not self.start():
                return False
        
        logger.info("Starting main loop...")
        
        try:
            # Main loop
            while self.keep_running:
                try:
                    # Check if monitor should be off due to motion inactivity
                    if self.monitor_controller.is_on() and not self.scheduler.is_scheduled_on():
                        current_time = time.time()
                        if current_time - self.last_motion_time > settings.MOTION_TIMEOUT:
                            logger.info(f"Motion inactivity timeout reached ({settings.MOTION_TIMEOUT}s). Turning monitor off.")
                            self._set_monitor_state(False)
                    
                    # Main loop sleep - using a loop to ensure quick exit on signal
                    for _ in range(5):  # Check every 5 seconds
                        if not self.keep_running:
                            break
                        time.sleep(1)
                        
                except Exception as e:
                    logger.error(f"Error in main loop: {e}")
                    time.sleep(30)  # Wait longer after an error
            
            logger.info("Main loop stopped")
            return True
        except Exception as e:
            logger.error(f"Unhandled exception in main loop: {e}")
            return False
        finally:
            self.stop()
    
    def stop(self):
        """Stop the Hallway Display system."""
        logger.info("Stopping Hallway Display system...")
        
        # Set flag to stop threads
        self.keep_running = False
        
        try:
            # Stop touch monitoring
            self._stop_touch_monitoring()
            
            # Stop configuration launcher
            if self.config_launcher:
                logger.info("Stopping configuration launcher...")
                self.config_launcher.stop()
            
            # Stop display controller
            if self.display_controller:
                logger.info("Stopping display controller...")
                self.display_controller.stop()
            
            # Stop sensor manager
            if self.sensor_manager:
                logger.info("Stopping sensor manager...")
                self.sensor_manager.stop()
            
            # Stop scheduler
            if self.scheduler:
                logger.info("Stopping scheduler...")
                self.scheduler.stop()
            
            logger.info("Hallway Display system stopped")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    def _handle_schedule_change(self, should_be_on):
        """Handle a schedule state change.
        
        Args:
            should_be_on: Whether the monitor should be on according to the schedule.
        """
        logger.info(f"Schedule changed to {'ON' if should_be_on else 'OFF'}")
        self._set_monitor_state(should_be_on)
    
    def _handle_motion_event(self):
        """Handle a motion event."""
        logger.debug("Motion event detected")
        self.motion_detected = True
        self.last_motion_time = time.time()
        
        # If the monitor is off and not in a scheduled off period, turn it on
        if not self.monitor_controller.is_on() and not self.scheduler.is_scheduled_on():
            logger.info("Motion detected while monitor is off. Turning monitor on.")
            self._set_monitor_state(True)
    
    def _handle_light_change(self, light_level):
        """Handle a light level change.
        
        Args:
            light_level: Current light level in lux.
        """
        logger.debug(f"Light level changed to {light_level:.2f} lux")
        
        # Only adjust brightness if the monitor is on
        if self.monitor_controller.is_on():
            self._adjust_brightness(light_level)
    
    def _adjust_brightness(self, light_level):
        """Adjust monitor brightness based on ambient light level.
        
        Args:
            light_level: Current light level in lux.
        """
        # Simple mapping of light level to brightness
        # This can be adjusted based on your specific needs
        
        # Map light level (lux) to brightness (0-100)
        # These thresholds are just examples and should be adjusted
        if light_level < 10:  # Very dark
            brightness = settings.MIN_BRIGHTNESS
        elif light_level > 1000:  # Very bright
            brightness = settings.MAX_BRIGHTNESS
        else:
            # Linear interpolation between MIN and MAX brightness
            brightness_range = settings.MAX_BRIGHTNESS - settings.MIN_BRIGHTNESS
            light_factor = (light_level - 10) / (1000 - 10)  # 0.0 to 1.0
            brightness = settings.MIN_BRIGHTNESS + int(light_factor * brightness_range)
        
        logger.debug(f"Setting brightness to {brightness}% based on light level {light_level:.2f} lux")
        self.monitor_controller.set_brightness(brightness)
    
    def _set_monitor_state(self, should_be_on):
        """Set the monitor state.
        
        Args:
            should_be_on: Whether the monitor should be on.
        """
        if should_be_on:
            # Turn on monitor if it's off
            if not self.monitor_controller.is_on():
                logger.info("Turning monitor ON")
                self.monitor_controller.turn_on()
                
                # Wait for monitor to turn on
                time.sleep(2)
                
                # Adjust brightness based on current light level
                light_level = self.sensor_manager.get_light_level()
                self._adjust_brightness(light_level)
                
                # Make sure DakBoard is displayed
                self.display_controller.switch_to_dakboard()
        else:
            # Turn off monitor if it's on
            if self.monitor_controller.is_on():
                logger.info("Turning monitor OFF")
                # Make sure we're on DakBoard before turning off
                self.display_controller.switch_to_dakboard()
                self.monitor_controller.turn_off()
    
    def _start_touch_monitoring(self):
        """Start monitoring for touch events."""
        try:
            # Find the touch device
            touch_path = self._find_touch_device()
            if not touch_path:
                logger.error("Touch device not found. Touch functionality will be disabled.")
                return False
            
            # Start the touch monitoring thread
            self.keep_running = True
            self.touch_thread = threading.Thread(target=self._touch_monitor_loop, args=(touch_path,), daemon=True)
            self.touch_thread.start()
            logger.info(f"Touch monitoring started on device: {touch_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to start touch monitoring: {e}")
            return False
    
    def _stop_touch_monitoring(self):
        """Stop the touch monitoring thread."""
        if self.touch_thread and self.touch_thread.is_alive():
            logger.info("Stopping touch monitoring...")
            # Thread will stop when keep_running is set to False
            self.touch_thread.join(timeout=2.0)
            if self.touch_thread.is_alive():
                logger.warning("Touch monitoring thread did not stop cleanly")
            else:
                logger.info("Touch monitoring stopped")
    
    def _find_touch_device(self):
        """Find the touch input device.
        
        Returns:
            str: Path to the touch device, or None if not found.
        """
        try:
            # Try to use the configured device path first
            touch_device_path = "/dev/input/by-id/usb-ILITEK_ILITEK-TP-event-if00"
            if os.path.exists(touch_device_path):
                return touch_device_path
            
            # Fall back to searching by name
            logger.info("Searching for touch input device...")
            devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
            for device in devices:
                logger.debug(f"Found input device: {device.path} - {device.name}")
                # Look for common touchscreen identifiers in device name
                if any(keyword in device.name.lower() for keyword in ["touch", "ilitek", "hid", "screen"]):
                    logger.info(f"Touch device found: {device.path} - {device.name}")
                    return device.path
            
            logger.warning("No touch device found by name")
            
            # If no touchscreen found, try to use the first device that supports touch events
            for device in devices:
                capabilities = device.capabilities(verbose=True)
                if evdev.ecodes.EV_KEY in capabilities and evdev.ecodes.BTN_TOUCH in capabilities[evdev.ecodes.EV_KEY]:
                    logger.info(f"Touch-capable device found: {device.path} - {device.name}")
                    return device.path
            
            logger.error("No touch-capable device found")
            return None
        except Exception as e:
            logger.error(f"Error finding touch device: {e}")
            return None
    
    def _touch_monitor_loop(self, device_path):
        """Monitor the touch device for events.
        
        Args:
            device_path: Path to the touch input device.
        """
        while self.keep_running:
            try:
                # Open the touch device
                touch_device = evdev.InputDevice(device_path)
                logger.info(f"Touch device opened: {touch_device.name}")
                
                # Monitor for touch events
                for event in touch_device.read_loop():
                    if not self.keep_running:
                        break
                    
                    # Check for touch events
                    if event.type == evdev.ecodes.EV_KEY and event.code == evdev.ecodes.BTN_TOUCH and event.value == 1:
                        logger.debug("Touch event detected")
                        self._handle_touch_event()
                    
                    # Check for multitouch events (some devices use ABS_MT_TRACKING_ID)
                    if event.type == evdev.ecodes.EV_ABS and event.code == evdev.ecodes.ABS_MT_TRACKING_ID and event.value != -1:
                        logger.debug("Multitouch event detected")
                        self._handle_touch_event()
            
            except (OSError, IOError) as e:
                logger.error(f"Touch device error: {e}")
                logger.info(f"Will attempt to reconnect in 5 seconds...")
                time.sleep(5)
            except Exception as e:
                logger.error(f"Unexpected error in touch monitoring: {e}")
                time.sleep(5)
    
    def _handle_touch_event(self):
        """Handle a touch event."""
        # Update motion/interaction time
        self.last_motion_time = time.time()
        
        # If the monitor is off, turn it on
        if not self.monitor_controller.is_on():
            logger.info("Touch detected while monitor is off. Turning monitor on.")
            self._set_monitor_state(True)
            time.sleep(1)  # Wait for the monitor to turn on
        
        # Handle the touch in the display controller
        self.display_controller.handle_touch()
    
    def _signal_handler(self, sig, frame):
        """Handle SIGINT and SIGTERM signals for graceful shutdown."""
        logger.info(f"Signal {sig} received. Shutting down...")
        self.keep_running = False


if __name__ == "__main__":
    try:
        # Create and start the Hallway Display controller
        display = HallwayDisplay()
        
        # Start the system
        if display.start():
            # Run the main loop
            display.run()
        else:
            logger.error("Failed to start Hallway Display system")
            sys.exit(1)
            
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}", exc_info=True)
        sys.exit(1)
