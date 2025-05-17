"""
Sensor module for the Hallway Display system.

This module handles the PIR motion sensor and BH1750 light sensor,
providing a common interface for sensor readings and event notifications.
"""

import time
import threading
import RPi.GPIO as GPIO
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import setup_logger
from config import settings

# Setup logger
logger = setup_logger('sensor')

class SensorError(Exception):
    """Exception raised for sensor-related errors."""
    pass

class BH1750Sensor:
    """Interface for the BH1750 light sensor.
    
    This class handles communication with the BH1750 light sensor over I2C.
    """
    
    # BH1750 constants
    POSSIBLE_ADDRESSES = [0x23, 0x5C]  # Possible I2C addresses of the BH1750
    ONE_TIME_HIGH_RES_MODE = 0x20  # 1 lux resolution
    
    def __init__(self):
        """Initialize the BH1750 light sensor."""
        self.bus = None
        self.address = None
        
        try:
            # Enable pull-ups on I2C pins to improve reliability
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(2, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # SDA
            GPIO.setup(3, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # SCL
            
            import smbus
            # Initialize I2C bus
            self.bus = smbus.SMBus(1)  # Raspberry Pi I2C bus
            
            # Try each possible address
            device_found = False
            for addr in self.POSSIBLE_ADDRESSES:
                try:
                    self.bus.write_byte(addr, self.ONE_TIME_HIGH_RES_MODE)
                    time.sleep(0.2)
                    self.bus.read_byte(addr)
                    self.address = addr
                    device_found = True
                    logger.info(f"BH1750 light sensor found at address 0x{addr:02X}")
                    break
                except Exception as e:
                    logger.debug(f"BH1750 not found at address 0x{addr:02X}: {e}")
            
            if not device_found:
                raise SensorError("BH1750 sensor not found at any known address")
                
            logger.info("BH1750 light sensor initialized")
        except ImportError:
            logger.error("smbus library not found. Install with: pip install smbus")
            raise SensorError("smbus library not found")
        except Exception as e:
            logger.error(f"Failed to initialize BH1750 sensor: {e}")
            raise SensorError(f"Failed to initialize BH1750 sensor: {e}")
      def read_light(self):
        """Read light level from the BH1750 sensor.
        
        Returns:
            float: Light level in lux, or None if reading failed.
        
        Raises:
            SensorError: If reading from the sensor fails repeatedly.
        """
        # Retry pattern with timeout
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Send measurement command
                self.bus.write_byte(self.address, self.ONE_TIME_HIGH_RES_MODE)
                
                # Wait for measurement to be taken
                time.sleep(0.3)  # Increased from 0.2 to 0.3 for more reliable readings
                
                # Read data from sensor
                data = self.bus.read_i2c_block_data(self.address, 0, 2)
                
                # Convert the data to lux
                light_level = (data[0] << 8 | data[1]) / 1.2
                logger.debug(f"Light level: {light_level:.2f} lux")
                return light_level
                
            except IOError as e:
                # I2C communication might fail temporarily due to bus contention
                logger.warning(f"I2C communication error (attempt {attempt+1}/{max_retries}): {e}")
                time.sleep(0.5)  # Wait a bit longer before retry
                
            except Exception as e:
                logger.error(f"Failed to read from BH1750 sensor: {e}")
                # Return a default value instead of raising an exception
                return None
                
        # If we've exhausted retries, return None instead of raising an exception
        # This allows the system to continue functioning without light sensor data
        logger.error("Failed to read from BH1750 sensor after multiple attempts")
        return None


class PIRMotionSensor:
    """Interface for the HC-SR501 PIR motion sensor.
    
    This class handles communication with the PIR motion sensor using GPIO.
    """
    
    def __init__(self, callback=None):
        """Initialize the PIR motion sensor.
        
        Args:
            callback: Function to call when motion is detected.
        """
        self.callback = callback
        self.last_motion_time = 0
        self.polling_thread = None
        self.keep_polling = False
        
        # Initialize GPIO
        try:
            GPIO.setmode(GPIO.BCM)
            # Setup the PIR sensor pin as input with pull-down resistor
            # This ensures stable readings even with longer cable runs
            GPIO.setup(settings.PIR_OUT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            logger.info("PIR motion sensor initialized")
        except Exception as e:
            logger.error(f"Failed to initialize PIR sensor: {e}")
            raise SensorError(f"Failed to initialize PIR sensor: {e}")
    
    def start_monitoring(self):
        """Start monitoring for motion events.
        
        Uses either edge detection (preferred) or polling as a fallback.
        """
        try:
            # Try to use edge detection first (most efficient)
            GPIO.add_event_detect(settings.PIR_OUT_PIN, GPIO.RISING, 
                                 callback=self._motion_detected, bouncetime=300)
            logger.info("PIR motion monitoring started using event detection")
        except Exception as e:
            # Fall back to polling if edge detection fails (often due to permissions)
            logger.warning(f"Edge detection failed: {e}. Falling back to polling.")
            self._start_polling()
    
    def _start_polling(self):
        """Start polling for PIR state changes as a fallback method."""
        if self.polling_thread is not None and self.polling_thread.is_alive():
            return  # Already polling
            
        self.keep_polling = True
        self.polling_thread = threading.Thread(target=self._polling_loop, daemon=True)
        self.polling_thread.start()
        logger.info("PIR motion monitoring started using polling")
        
    def _polling_loop(self):
        """Background thread that polls the PIR sensor state."""
        last_state = GPIO.input(settings.PIR_OUT_PIN)
        
        while self.keep_polling:
            try:
                current_state = GPIO.input(settings.PIR_OUT_PIN)
                # Detect rising edge (motion detection)
                if current_state == 1 and last_state == 0:
                    self._motion_detected(settings.PIR_OUT_PIN)
                last_state = current_state
                time.sleep(0.1)  # 100ms polling interval
            except Exception as e:
                logger.error(f"Error in PIR polling loop: {e}")
                time.sleep(1)  # Longer delay on error
    
    def stop_monitoring(self):
        """Stop monitoring for motion events."""
        try:
            GPIO.remove_event_detect(settings.PIR_OUT_PIN)
            logger.info("PIR motion monitoring stopped")
        except Exception as e:
            logger.error(f"Failed to stop PIR monitoring: {e}")
    
    def _motion_detected(self, channel):
        """Callback function when motion is detected.
        
        Args:
            channel: GPIO channel that triggered the event.
        """
        self.last_motion_time = time.time()
        logger.debug("Motion detected")
        if self.callback:
            self.callback()
    
    def read_motion(self):
        """Read the current state of the PIR sensor.
        
        Returns:
            bool: True if motion is detected, False otherwise.
        """
        try:
            state = GPIO.input(settings.PIR_OUT_PIN)
            return state == GPIO.HIGH
        except Exception as e:
            logger.error(f"Failed to read from PIR sensor: {e}")
            raise SensorError(f"Failed to read from PIR sensor: {e}")


class SensorManager:
    """Manager for sensor readings and events.
    
    This class provides a unified interface for all sensors and handles
    periodic readings and event notifications.
    """
    
    def __init__(self, motion_callback=None, light_change_callback=None):
        """Initialize the sensor manager.
        
        Args:
            motion_callback: Function to call when motion is detected.
            light_change_callback: Function to call when light level changes significantly.
        """
        self.motion_callback = motion_callback
        self.light_change_callback = light_change_callback
        self.light_sensor = None
        self.motion_sensor = None
        self.last_light_level = 0
        self.light_threshold = 10  # Lux change threshold to trigger callback
        self.keep_running = False
        self.light_polling_thread = None
        
        logger.info("Sensor manager initialized")
    
    def initialize_sensors(self):
        """Initialize all sensors."""
        try:
            # Initialize light sensor
            self.light_sensor = BH1750Sensor()
            
            # Initialize motion sensor with callback
            self.motion_sensor = PIRMotionSensor(callback=self._handle_motion_event)
            
            logger.info("All sensors initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize sensors: {e}")
            return False
    
    def start(self):
        """Start sensor monitoring."""
        if not self.light_sensor or not self.motion_sensor:
            if not self.initialize_sensors():
                logger.error("Failed to start sensor monitoring due to initialization error")
                return False
        
        try:
            # Start motion sensor monitoring
            self.motion_sensor.start_monitoring()
            
            # Start light polling thread
            self.keep_running = True
            self.light_polling_thread = threading.Thread(target=self._poll_light_sensor, daemon=True)
            self.light_polling_thread.start()
            
            logger.info("Sensor monitoring started")
            return True
        except Exception as e:
            logger.error(f"Failed to start sensor monitoring: {e}")
            return False
    
    def stop(self):
        """Stop sensor monitoring."""
        try:
            # Stop light polling thread
            self.keep_running = False
            if self.light_polling_thread:
                self.light_polling_thread.join(timeout=2.0)
            
            # Stop motion sensor monitoring
            if self.motion_sensor:
                self.motion_sensor.stop_monitoring()
                
            logger.info("Sensor monitoring stopped")
        except Exception as e:
            logger.error(f"Error stopping sensor monitoring: {e}")
    
    def _handle_motion_event(self):
        """Internal callback for motion events."""
        if self.motion_callback:
            self.motion_callback()
    
    def _poll_light_sensor(self):
        """Poll the light sensor periodically."""
        while self.keep_running:
            try:
                # Read light level
                light_level = self.light_sensor.read_light()
                
                # Check if light level changed significantly
                if abs(light_level - self.last_light_level) > self.light_threshold:
                    logger.debug(f"Light level changed from {self.last_light_level:.2f} to {light_level:.2f} lux")
                    self.last_light_level = light_level
                    if self.light_change_callback:
                        self.light_change_callback(light_level)
                
                # Sleep before next reading
                time.sleep(5)  # Poll every 5 seconds
            except Exception as e:
                logger.error(f"Error in light sensor polling: {e}")
                time.sleep(10)  # Wait longer after an error
    
    def get_light_level(self):
        """Get the current light level.
        
        Returns:
            float: Current light level in lux.
        """
        if not self.light_sensor:
            logger.error("Light sensor not initialized")
            return 0
        
        try:
            return self.light_sensor.read_light()
        except Exception as e:
            logger.error(f"Error reading light level: {e}")
            return 0
    
    def is_motion_detected(self):
        """Check if motion is currently detected.
        
        Returns:
            bool: True if motion is detected, False otherwise.
        """
        if not self.motion_sensor:
            logger.error("Motion sensor not initialized")
            return False
        
        try:
            return self.motion_sensor.read_motion()
        except Exception as e:
            logger.error(f"Error reading motion state: {e}")
            return False
