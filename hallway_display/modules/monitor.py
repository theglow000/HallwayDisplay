"""
Monitor control module for the Hallway Display system.

This module provides a clean interface for controlling the monitor's
power state and brightness using ddcutil.
"""

import subprocess
import time
import os
import sys

# Add parent directory to path for relative imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import setup_logger
from config import settings

# Setup logger
logger = setup_logger('monitor')

class MonitorError(Exception):
    """Exception raised for monitor-related errors."""
    pass

class MonitorController:
    """Controller for monitor power and brightness using ddcutil.
    
    This class provides methods to control the monitor's power state and
    brightness level using the ddcutil command-line tool.
    """
    
    def __init__(self):
        """Initialize the monitor controller."""
        self.last_brightness_set = -1
        self.last_power_state_set = -1
        self.monitor_is_off = None  # We don't know the initial state
        logger.info("Monitor controller initialized")
    
    def run_ddcutil(self, args, timeout=5, verify=True):
        """Run a ddcutil command and handle potential errors.
        
        Args:
            args: List of arguments to pass to ddcutil.
            timeout: Command timeout in seconds.
            verify: Whether to verify the command (some power commands need --noverify).
            
        Returns:
            bool: True if the command succeeded, False otherwise.
            
        Raises:
            MonitorError: If the command fails critically.
        """
        # Construct the command
        if settings.DDCUTIL_COMMAND:
            command = [settings.DDCUTIL_COMMAND]
        else:
            command = []
            
        # Add base arguments
        command.extend([
            "ddcutil",
            "--sleep-multiplier", ".1",
            "--bus", str(settings.MONITOR_I2C_BUS)
        ])
        
        # Add command-specific arguments
        command.extend(args)
        
        # Add noverify if needed
        if not verify and "setvcp" in args:
            command.insert(command.index("setvcp") + 1, "--noverify")
        
        try:
            logger.debug(f"Running ddcutil command: {' '.join(command)}")
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                check=False, 
                timeout=timeout
            )
            
            if result.returncode != 0:
                logger.warning(
                    f"ddcutil command failed (Code: {result.returncode}): {' '.join(command)}\n"
                    f"Stderr: {result.stderr.strip()}\n"
                    f"Stdout: {result.stdout.strip()}"
                )
                return False
                
            logger.debug(f"ddcutil command succeeded: {result.stdout.strip()}")
            return True
            
        except subprocess.TimeoutExpired:
            logger.warning(f"ddcutil command timed out: {' '.join(command)}")
            return False
        except FileNotFoundError:
            error_msg = f"Command '{command[0]}' not found. Is ddcutil installed and in PATH?"
            logger.error(error_msg)
            raise MonitorError(error_msg)
        except Exception as e:
            logger.error(f"Error running ddcutil: {e}")
            return False
            
    def set_power(self, state, retry_count=2):
        """Set the monitor power state.
        
        Args:
            state: True to turn on, False to turn off.
            retry_count: Number of times to retry if the command fails.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        state_code = settings.POWER_STATE_ON if state else settings.POWER_STATE_OFF
        state_desc = "ON" if state else "OFF (Standby)"
        
        # Avoid redundant calls
        if state_code == self.last_power_state_set:
            if (state_code == settings.POWER_STATE_OFF and self.monitor_is_off) or \
               (state_code == settings.POWER_STATE_ON and not self.monitor_is_off):
                logger.debug(f"Power state already {state_desc}, skipping")
                return True
        
        logger.info(f"Setting monitor power state to {state_desc}")
        
        # Try primary method: DDC/CI using ddcutil
        for attempt in range(retry_count + 1):
            if attempt > 0:
                logger.info(f"Retrying monitor power {state_desc} (attempt {attempt}/{retry_count})")
                time.sleep(1)  # Wait before retry
                
            # Use --noverify for power commands
            if self.run_ddcutil(["setvcp", settings.VCP_POWER, state_code], verify=False):
                self.monitor_is_off = not state
                self.last_power_state_set = state_code
                # Reset brightness tracking if turning off
                if not state:
                    self.last_brightness_set = -1
                return True
                
        # If DDC/CI failed, try alternative methods
        logger.warning(f"DDC/CI failed to set power {state_desc}, trying alternatives")
        
        if self._try_alternative_power_control(state):
            self.monitor_is_off = not state
            self.last_power_state_set = state_code
            # Reset brightness tracking if turning off
            if not state:
                self.last_brightness_set = -1
            return True
        
        logger.error(f"All methods failed to set monitor power to {state_desc}")
        return False
    
    def set_brightness(self, value):
        """Set the monitor brightness.
        
        Args:
            value: Brightness value (0-100).
            
        Returns:
            bool: True if successful, False otherwise.
        """
        # Clamp value between 0 and 100
        brightness = max(0, min(100, int(value)))
        
        # Avoid redundant calls
        if brightness == self.last_brightness_set:
            logger.debug(f"Brightness already {brightness}%, skipping")
            return True
        
        logger.debug(f"Setting brightness to {brightness}%")
        if self.run_ddcutil(["setvcp", settings.VCP_BRIGHTNESS, str(brightness)]):
            self.last_brightness_set = brightness
            return True
        else:
            logger.error(f"Failed to set brightness to {brightness}%")
            return False
      def get_power_state(self):
        """Get the current monitor power state.
        
        Returns:
            str: "ON" if the monitor is on, "OFF" if off.
            None: If the power state cannot be determined.
        """
        # Try DDC/CI method first
        ddc_state = self._get_power_state_ddcutil()
        if ddc_state is not None:
            return ddc_state
            
        # Fall back to alternative methods if DDC/CI fails
        logger.warning("DDC/CI failed to get power state, trying alternatives")
        
        # Try xset method
        xset_state = self._get_power_state_xset()
        if xset_state is not None:
            return xset_state
            
        # Try tvservice method
        tvservice_state = self._get_power_state_tvservice()
        if tvservice_state is not None:
            return tvservice_state
            
        # If all methods fail, use the last known state
        logger.warning("All methods failed to get power state, using last known state")
        return "OFF" if self.monitor_is_off else "ON" if self.monitor_is_off is not None else None
        
    def _get_power_state_ddcutil(self):
        """Get the current monitor power state using ddcutil.
        
        Returns:
            str: "ON" if the monitor is on, "OFF" if off.
            None: If the power state cannot be determined.
        """
        try:
            command = []
            if settings.DDCUTIL_COMMAND:
                command.append(settings.DDCUTIL_COMMAND)
                
            command.extend([
                "ddcutil",
                "--sleep-multiplier", ".1",
                "--bus", str(settings.MONITOR_I2C_BUS),
                "getvcp", settings.VCP_POWER
            ])
            
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                check=False, 
                timeout=5
            )
            
            if result.returncode != 0:
                logger.warning(f"Failed to get monitor power state: {result.stderr.strip()}")
                return None
                
            # Parse the output
            output = result.stdout.strip()
            
            # Handle different output formats
            if "DPMS: Standby" in output:
                self.monitor_is_off = True
                return "OFF"
            elif "DPM: On" in output:
                self.monitor_is_off = False
                return "ON"
            elif "current value" in output:
                state_part = output.split("current value =")[1].split(",")[0].strip()
                power_state = state_part.split("x")[1].strip() if "x" in state_part else state_part
                
                is_on = power_state == settings.POWER_STATE_ON
                self.monitor_is_off = not is_on
                return "ON" if is_on else "OFF"
            else:
                logger.warning(f"Unexpected output format from ddcutil: {output}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.warning("ddcutil command timed out while getting power state")
            return None
        except FileNotFoundError as exc:
            logger.error("ddcutil command not found. Is it installed?")
            return None
        except Exception as e:
            logger.error(f"Error getting monitor power state: {e}")
            return None
            
    def _get_power_state_xset(self):
        """Get the current monitor power state using xset.
        
        Returns:
            str: "ON" if the monitor is on, "OFF" if off.
            None: If the power state cannot be determined.
        """
        try:
            result = subprocess.run(
                ["xset", "q"],
                env={"DISPLAY": ":0", "XAUTHORITY": os.environ.get("XAUTHORITY", "/home/theglow000/.Xauthority")},
                capture_output=True,
                text=True,
                check=False,
                timeout=3
            )
            
            if result.returncode != 0:
                return None
                
            output = result.stdout.strip()
            
            # Check DPMS status
            if "Monitor is On" in output:
                self.monitor_is_off = False
                return "ON"
            elif "Monitor is in Standby" in output or "Monitor is in Suspend" in output or "Monitor is Off" in output:
                self.monitor_is_off = True
                return "OFF"
                
            return None
            
        except subprocess.TimeoutExpired:
            return None
        except FileNotFoundError:
            return None
        except Exception as e:
            logger.debug(f"xset power state check failed: {e}")
            return None
            
    def _get_power_state_tvservice(self):
        """Get the current monitor power state using tvservice.
        
        Returns:
            str: "ON" if the monitor is on, "OFF" if off.
            None: If the power state cannot be determined.
        """
        try:
            result = subprocess.run(
                ["tvservice", "-s"],
                capture_output=True,
                text=True,
                check=False,
                timeout=3
            )
            
            if result.returncode != 0:
                return None
                
            output = result.stdout.strip()
            
            # Check tvservice status
            if "state 0x" in output and ("0xa" in output or "0x12" in output):
                self.monitor_is_off = False
                return "ON"
            elif "state 0x" in output and "0x40" in output:
                self.monitor_is_off = True
                return "OFF"
                
            return None
            
        except subprocess.TimeoutExpired:
            return None
        except FileNotFoundError:
            return None
        except Exception as e:
            logger.debug(f"tvservice power state check failed: {e}")
            return None
    
    def get_brightness(self):
        """Get the current brightness of the monitor.
        
        Returns:
            int: Current brightness value (0-100).
            None: If the brightness cannot be determined.
        """
        try:
            logger.debug("Getting monitor brightness")
            command = []
            if settings.DDCUTIL_COMMAND:
                command.append(settings.DDCUTIL_COMMAND)
                
            command.extend([
                "ddcutil",
                "--sleep-multiplier", ".1",
                "--bus", str(settings.MONITOR_I2C_BUS),
                "getvcp", settings.VCP_BRIGHTNESS
            ])
            
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                check=False, 
                timeout=5
            )
            
            if result.returncode != 0:
                logger.warning(f"Failed to get monitor brightness: {result.stderr.strip()}")
                return None
            
            # Parse the output to extract the brightness
            # Example output: "VCP code 0x10 (Brightness): current value = 50, max value = 100"
            output = result.stdout.strip()
            if "current value" in output:
                brightness_part = output.split("current value =")[1].split(",")[0].strip()
                brightness = int(brightness_part)
                logger.debug(f"Current brightness: {brightness}%")
                self.last_brightness_set = brightness
                return brightness
            else:
                logger.warning(f"Unexpected output format from ddcutil: {output}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting monitor brightness: {e}")
            return None
    
    def turn_on(self):
        """Turn the monitor on.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        return self.set_power(True)
    
    def turn_off(self):
        """Turn the monitor off (standby).
        
        Returns:
            bool: True if successful, False otherwise.
        """
        return self.set_power(False)
    
    def is_on(self):
        """Check if the monitor is currently on.
        
        Returns:
            bool: True if monitor is on, False if off/standby.
        """
        # If we don't know the state, query it
        if self.monitor_is_off is None:
            state = self.get_power_state()
            return state if state is not None else False
        
        return not self.monitor_is_off
          def _try_alternative_power_control(self, state):
        """Try alternative methods to control monitor power when DDC/CI fails.
        
        Args:
            state: True to turn on, False to turn off.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        # Method 1: CEC-client for HDMI-CEC compatible displays
        if self._try_cec_control(state):
            logger.info("Successfully set power using CEC-client")
            return True
            
        # Method 2: VESA DPMS for local X11 displays
        if self._try_xset_dpms(state):
            logger.info("Successfully set power using xset DPMS")
            return True
            
        # Method 3: tvservice for Raspberry Pi's own HDMI control
        if self._try_tvservice(state):
            logger.info("Successfully set power using tvservice")
            return True
            
        return False
        
    def _try_cec_control(self, state):
        """Try using CEC-client to control monitor power.
        
        Args:
            state: True to turn on, False to turn off.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Check if cec-client is available
            result = subprocess.run(
                ["which", "cec-client"], 
                capture_output=True, 
                text=True, 
                check=False
            )
            
            if result.returncode != 0:
                logger.debug("cec-client not found, skipping CEC control")
                return False
                
            # CEC command: 0x0 for ON, 0x36 for Standby
            cec_command = "tx 10:04" if state else "tx 10:36"
            
            # Run cec-client
            logger.debug(f"Trying CEC command: {cec_command}")
            result = subprocess.run(
                ["echo", cec_command, "|", "cec-client", "-s", "-d", "1"],
                shell=True,  # Need shell to use pipe
                capture_output=True,
                text=True,
                check=False,
                timeout=5
            )
            
            return result.returncode == 0
            
        except Exception as e:
            logger.debug(f"CEC control failed: {e}")
            return False
            
    def _try_xset_dpms(self, state):
        """Try using xset to control DPMS power state.
        
        Args:
            state: True to turn on, False to turn off.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Check if xset is available
            result = subprocess.run(
                ["which", "xset"], 
                capture_output=True, 
                text=True, 
                check=False
            )
            
            if result.returncode != 0:
                logger.debug("xset not found, skipping DPMS control")
                return False
                
            # DPMS command: force on or off
            dpms_command = ["xset", "dpms", "force", "on" if state else "off"]
            
            # Run xset
            logger.debug(f"Trying DPMS command: {' '.join(dpms_command)}")
            result = subprocess.run(
                dpms_command,
                env={"DISPLAY": ":0", "XAUTHORITY": os.environ.get("XAUTHORITY", "/home/theglow000/.Xauthority")},
                capture_output=True,
                text=True,
                check=False,
                timeout=5
            )
            
            return result.returncode == 0
            
        except Exception as e:
            logger.debug(f"DPMS control failed: {e}")
            return False
            
    def _try_tvservice(self, state):
        """Try using tvservice (Raspberry Pi specific) to control HDMI power.
        
        Args:
            state: True to turn on, False to turn off.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Check if tvservice is available
            result = subprocess.run(
                ["which", "tvservice"], 
                capture_output=True, 
                text=True, 
                check=False
            )
            
            if result.returncode != 0:
                logger.debug("tvservice not found, skipping tvservice control")
                return False
                
            # tvservice command: --preferred for ON, --off for OFF
            tvservice_command = ["tvservice", "--preferred" if state else "--off"]
            
            # Run tvservice
            logger.debug(f"Trying tvservice command: {' '.join(tvservice_command)}")
            result = subprocess.run(
                tvservice_command,
                capture_output=True,
                text=True,
                check=False,
                timeout=5
            )
            
            return result.returncode == 0
            
        except Exception as e:
            logger.debug(f"tvservice control failed: {e}")
            return False
