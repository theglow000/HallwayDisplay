#!/bin/bash
# Enhanced monitor control fix script
# This script improves monitor control by focusing on alternative control methods

echo "=== Enhanced Monitor Control Fix ==="
date
echo "User: $(whoami)"

# Function to log messages with timestamps
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Set display environment variables
if [ -z "$DISPLAY" ]; then
    export DISPLAY=:0
    log_message "Setting DISPLAY=$DISPLAY"
fi

if [ -z "$XAUTHORITY" ]; then
    export XAUTHORITY=~/.Xauthority
    log_message "Setting XAUTHORITY=$XAUTHORITY"
fi

# Verify X server access
log_message "Verifying X server access..."
if ! xset q &>/dev/null; then
    log_message "❌ X server not accessible. Trying to fix..."
    xhost +local: &>/dev/null
    if ! xset q &>/dev/null; then
        log_message "❌ X server still not accessible. Please fix your X server configuration."
        exit 1
    fi
fi
log_message "✅ X server is accessible"

# Create enhanced monitor control module
log_message "Creating enhanced monitor control script..."
cd "$(dirname "$0")/.."
PROJECT_DIR="$(pwd)"

cat > "$PROJECT_DIR/modules/enhanced_monitor.py" << 'EOF'
"""
Enhanced monitor control module for the Hallway Display system.

This module provides a more robust interface for controlling the monitor's
power state and brightness with multiple fallback mechanisms.
"""

import subprocess
import time
import os
import sys
import threading

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import setup_logger
from config import settings
from modules.monitor import MonitorController

# Setup logger
logger = setup_logger('enhanced_monitor')

class EnhancedMonitorController(MonitorController):
    """Enhanced controller for monitor power and brightness with multiple fallback mechanisms.
    
    This class extends the standard MonitorController with additional
    fallback methods and better error handling.
    """
    
    def __init__(self):
        """Initialize the enhanced monitor controller."""
        super().__init__()
        self.alternative_methods_only = False
        self.preferred_method = None
        self._detect_best_method()
        logger.info("Enhanced monitor controller initialized")
    
    def _detect_best_method(self):
        """Detect the best control method available on this system."""
        # Test DDC/CI
        if self._test_ddcutil():
            self.preferred_method = "ddcutil"
            logger.info("Using DDC/CI (ddcutil) as preferred control method")
            return
            
        # Test DPMS via xset
        if self._test_xset_dpms():
            self.preferred_method = "xset"
            self.alternative_methods_only = True
            logger.info("Using DPMS (xset) as preferred control method")
            return
            
        # Test CEC
        if self._test_cec():
            self.preferred_method = "cec"
            self.alternative_methods_only = True
            logger.info("Using CEC as preferred control method")
            return
            
        # Test tvservice
        if self._test_tvservice():
            self.preferred_method = "tvservice"
            self.alternative_methods_only = True
            logger.info("Using tvservice as preferred control method")
            return
            
        # No good methods available, use ddcutil anyway but log a warning
        self.preferred_method = "ddcutil"
        logger.warning("No working control methods detected. Defaulting to ddcutil, but monitor control might not work.")
    
    def _test_ddcutil(self):
        """Test if ddcutil can communicate with the monitor."""
        try:
            # Construct the command
            command = []
            if settings.DDCUTIL_COMMAND:
                command.append(settings.DDCUTIL_COMMAND)
                
            command.extend([
                "ddcutil",
                "--sleep-multiplier", ".1",
                "--bus", str(settings.MONITOR_I2C_BUS),
                "detect"
            ])
            
            # Run the command with a short timeout
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                check=False, 
                timeout=3
            )
            
            return result.returncode == 0 and "Display" in result.stdout
            
        except Exception as e:
            logger.debug(f"ddcutil test failed: {e}")
            return False
    
    def _test_xset_dpms(self):
        """Test if xset DPMS is available."""
        try:
            result = subprocess.run(
                ["xset", "q"],
                env={"DISPLAY": os.environ.get("DISPLAY", ":0"), 
                     "XAUTHORITY": os.environ.get("XAUTHORITY", os.path.expanduser("~/.Xauthority"))},
                capture_output=True,
                text=True,
                check=False,
                timeout=2
            )
            
            return result.returncode == 0
            
        except Exception as e:
            logger.debug(f"xset test failed: {e}")
            return False
    
    def _test_cec(self):
        """Test if CEC control is available."""
        try:
            # Check if cec-client is installed
            which_result = subprocess.run(
                ["which", "cec-client"],
                capture_output=True,
                text=True,
                check=False,
                timeout=2
            )
            
            if which_result.returncode != 0:
                return False
                
            # Try a simple CEC command
            result = subprocess.run(
                ["echo", "scan", "|", "cec-client", "-s", "-d", "1"],
                shell=True,
                capture_output=True,
                text=True,
                check=False,
                timeout=3
            )
            
            return result.returncode == 0 and not "No devices found" in result.stdout
            
        except Exception as e:
            logger.debug(f"CEC test failed: {e}")
            return False
    
    def _test_tvservice(self):
        """Test if tvservice is available."""
        try:
            result = subprocess.run(
                ["tvservice", "-s"],
                capture_output=True,
                text=True,
                check=False,
                timeout=2
            )
            
            return result.returncode == 0
            
        except Exception as e:
            logger.debug(f"tvservice test failed: {e}")
            return False
    
    def set_power(self, state, retry_count=2):
        """Set the monitor power state with improved fallback.
        
        Args:
            state: True to turn on, False to turn off.
            retry_count: Number of times to retry if the command fails.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        state_desc = "ON" if state else "OFF (Standby)"
        logger.info(f"Setting monitor power state to {state_desc} using {self.preferred_method}")
        
        # Skip DDC/CI if we know it doesn't work
        if self.alternative_methods_only:
            return self._set_power_alternative(state)
            
        # Try DDC/CI first if it's not known to be broken
        result = super().set_power(state, retry_count)
        if result:
            return True
            
        # If DDC/CI failed, try alternative methods
        logger.warning(f"Primary method failed to set power {state_desc}, trying alternatives")
        return self._set_power_alternative(state)
    
    def _set_power_alternative(self, state):
        """Set power using the preferred alternative method."""
        if self.preferred_method == "xset":
            return self._set_power_xset(state)
        elif self.preferred_method == "cec":
            return self._set_power_cec(state)
        elif self.preferred_method == "tvservice":
            return self._set_power_tvservice(state)
        else:
            # Try all methods in sequence
            return self._try_alternative_power_control(state)
    
    def _set_power_xset(self, state):
        """Set power using xset DPMS."""
        try:
            command = ["xset", "dpms", "force", "on" if state else "off"]
            
            result = subprocess.run(
                command,
                env={"DISPLAY": os.environ.get("DISPLAY", ":0"), 
                     "XAUTHORITY": os.environ.get("XAUTHORITY", os.path.expanduser("~/.Xauthority"))},
                capture_output=True,
                text=True,
                check=False,
                timeout=3
            )
            
            if result.returncode == 0:
                self.monitor_is_off = not state
                logger.info(f"Successfully set power to {state} using xset")
                return True
            else:
                logger.warning(f"Failed to set power using xset: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error using xset for power control: {e}")
            return False
    
    def _set_power_cec(self, state):
        """Set power using CEC."""
        try:
            # CEC command: 0x04 for ON, 0x36 for Standby
            cec_command = "tx 10:04" if state else "tx 10:36"
            
            result = subprocess.run(
                ["echo", cec_command, "|", "cec-client", "-s", "-d", "1"],
                shell=True,
                capture_output=True,
                text=True,
                check=False,
                timeout=5
            )
            
            if result.returncode == 0:
                self.monitor_is_off = not state
                logger.info(f"Successfully set power to {state} using CEC")
                return True
            else:
                logger.warning(f"Failed to set power using CEC: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error using CEC for power control: {e}")
            return False
    
    def _set_power_tvservice(self, state):
        """Set power using tvservice."""
        try:
            command = ["tvservice", "--preferred" if state else "--off"]
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                timeout=5
            )
            
            if result.returncode == 0:
                self.monitor_is_off = not state
                logger.info(f"Successfully set power to {state} using tvservice")
                return True
            else:
                logger.warning(f"Failed to set power using tvservice: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error using tvservice for power control: {e}")
            return False
    
    def set_brightness(self, value):
        """Set the monitor brightness with alternative method fallback.
        
        Args:
            value: Brightness value (0-100).
            
        Returns:
            bool: True if successful, False otherwise.
        """
        # Try standard method first
        result = super().set_brightness(value)
        if result:
            return True
            
        # If that fails, we don't have many alternatives for brightness
        # Some TVs/monitors might support brightness control via CEC
        logger.warning(f"Failed to set brightness to {value}. No good alternative methods available.")
        return False
EOF

log_message "✅ Created enhanced monitor control module"

# Create test script for the enhanced monitor control
cat > "$PROJECT_DIR/test_enhanced_monitor.py" << 'EOF'
#!/usr/bin/env python3
"""
Test script for the enhanced monitor control.

This script tests the enhanced monitor control functionality.
"""

import os
import sys
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.enhanced_monitor import EnhancedMonitorController
from utils.logger import setup_logger

# Setup logger
logger = setup_logger('test_enhanced')

def test_enhanced_monitor():
    """Test enhanced monitor control operations."""
    print("Initializing enhanced monitor controller...")
    monitor = EnhancedMonitorController()
    
    print(f"Preferred control method: {monitor.preferred_method}")
    print(f"Alternative methods only: {monitor.alternative_methods_only}")
    
    print("Testing power state...")
    state = monitor.get_power_state()
    print(f"Current power state: {state}")
    
    print("Testing brightness...")
    brightness = monitor.get_brightness()
    print(f"Current brightness: {brightness}")
    
    print("Testing power control...")
    if state == "ON" or state is None:
        print("Testing power off...")
        result = monitor.set_power(False)
        print(f"Power off result: {result}")
        time.sleep(3)
        
        print("Testing power on...")
        result = monitor.set_power(True)
        print(f"Power on result: {result}")
    else:
        print("Testing power on...")
        result = monitor.set_power(True)
        print(f"Power on result: {result}")
        time.sleep(3)
        
        print("Testing power off...")
        result = monitor.set_power(False)
        print(f"Power off result: {result}")
    
    # Leave the monitor on after tests
    monitor.set_power(True)
    
    print("Enhanced monitor control test complete.")

if __name__ == "__main__":
    print("=== Enhanced Monitor Control Test ===")
    try:
        test_enhanced_monitor()
    except Exception as e:
        print(f"Error testing enhanced monitor control: {e}")
        import traceback
        traceback.print_exc()
    print("=== Test Complete ===")
EOF

chmod +x "$PROJECT_DIR/test_enhanced_monitor.py"
log_message "✅ Created enhanced monitor test script"

# Update main.py to use the enhanced monitor controller
# First, check if it's been modified already
if ! grep -q "EnhancedMonitorController" "$PROJECT_DIR/main.py"; then
    log_message "Updating main.py to use the enhanced monitor controller..."
    
    # Create a backup of main.py
    cp "$PROJECT_DIR/main.py" "$PROJECT_DIR/main.py.bak"
    
    # Replace the import
    sed -i 's/from modules.monitor import MonitorController/from modules.monitor import MonitorController\nfrom modules.enhanced_monitor import EnhancedMonitorController/' "$PROJECT_DIR/main.py"
    
    # Replace the controller initialization
    sed -i 's/self.monitor = MonitorController()/self.monitor = EnhancedMonitorController()/' "$PROJECT_DIR/main.py"
    
    log_message "✅ Updated main.py to use enhanced monitor controller"
else
    log_message "✅ main.py already uses enhanced monitor controller"
fi

# Create a new enhanced start script
cat > "$PROJECT_DIR/start_enhanced_monitor.sh" << 'EOF'
#!/bin/bash
# Enhanced start script for Hallway Display with improved monitor control

echo "=== Starting Hallway Display with Enhanced Monitor Control ==="
echo "User: $(whoami)"
echo "Groups: $(groups)"

# Set display environment variables
if [ -z "$DISPLAY" ]; then
    export DISPLAY=:0
    echo "Setting DISPLAY=$DISPLAY"
fi

if [ -z "$XAUTHORITY" ]; then
    export XAUTHORITY=~/.Xauthority
    echo "Setting XAUTHORITY=$XAUTHORITY"
fi

# Verify X server access
echo "Verifying X server access..."
if xset q &>/dev/null; then
    echo "✅ X server is accessible"
else
    echo "❌ X server not accessible. Trying to fix..."
    xhost +local: &>/dev/null
    if xset q &>/dev/null; then
        echo "✅ X server is now accessible"
    else
        echo "❌ X server still not accessible. Check your X server configuration."
        exit 1
    fi
fi

# Set PYTHONPATH
cd "$(dirname "$0")"
PROJECT_DIR="$(pwd)"
export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"
echo "PYTHONPATH set to: $PYTHONPATH"

# Run the application
echo "Starting Hallway Display with enhanced monitor control..."
exec python3 "$PROJECT_DIR/main.py" "$@"
EOF

chmod +x "$PROJECT_DIR/start_enhanced_monitor.sh"
log_message "✅ Created enhanced start script"

log_message "=== Enhanced Monitor Control Fix Complete ==="
log_message "To test the enhanced monitor control, run:"
log_message "  $PROJECT_DIR/test_enhanced_monitor.py"
log_message "To start the Hallway Display with enhanced monitor control, run:"
log_message "  $PROJECT_DIR/start_enhanced_monitor.sh"
log_message "Recommended: Add these scripts to your autostart configuration."
