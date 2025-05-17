#!/bin/bash
# Fix monitor control issues by ensuring the correct Python path for imports
# and testing alternative monitor control methods

echo "=== Fixing Python Module Imports ==="
cd "$(dirname "$0")/.."
HALLWAY_DIR="$(pwd)"
echo "Project directory: $HALLWAY_DIR"

# Create a wrapper script to run Python with the correct path
cat > run_hallway_display.sh << 'EOF'
#!/bin/bash
# Wrapper script to run Hallway Display with correct Python path
cd "$(dirname "$0")"
PROJECT_DIR="$(pwd)"
export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"
echo "Running with PYTHONPATH=$PYTHONPATH"
python3 "$PROJECT_DIR/main.py" "$@"
EOF

chmod +x run_hallway_display.sh
echo "✅ Created wrapper script run_hallway_display.sh"

# Test the monitor control directly
echo "=== Testing Monitor Control Module ==="
cat > test_monitor_control.py << 'EOF'
#!/usr/bin/env python3
"""
Test script for the monitor control module.

This script tests the monitor control module directly by importing it
and performing basic operations.
"""

import os
import sys
import time

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.monitor import MonitorController
from utils.logger import setup_logger

# Setup logger
logger = setup_logger('test_monitor')

def test_monitor():
    """Test basic monitor control operations."""
    print("Initializing monitor controller...")
    monitor = MonitorController()
    
    print("Testing power state...")
    state = monitor.get_power_state()
    print(f"Current power state: {state}")
    
    print("Testing brightness...")
    brightness = monitor.get_brightness()
    print(f"Current brightness: {brightness}")
    
    # Try alternative control methods
    print("Testing alternative power control methods...")
    if state == "ON":
        print("Testing power off...")
        result = monitor._try_alternative_power_control(False)
        print(f"Power off result: {result}")
        time.sleep(3)
        
        print("Testing power on...")
        result = monitor._try_alternative_power_control(True)
        print(f"Power on result: {result}")
    else:
        print("Testing power on...")
        result = monitor._try_alternative_power_control(True)
        print(f"Power on result: {result}")
        time.sleep(3)
        
        print("Testing power off...")
        result = monitor._try_alternative_power_control(False)
        print(f"Power off result: {result}")
    
    print("Testing brightness setting...")
    # Try a moderate brightness value (50%)
    result = monitor.set_brightness(50)
    print(f"Set brightness 50% result: {result}")
    
    print("Monitor control test complete.")

if __name__ == "__main__":
    print("=== Monitor Control Test ===")
    try:
        test_monitor()
    except Exception as e:
        print(f"Error testing monitor control: {e}")
        import traceback
        traceback.print_exc()
    print("=== Test Complete ===")
EOF

chmod +x test_monitor_control.py
echo "✅ Created monitor control test script"

# Update start.sh to use the new wrapper script
cat > start_fixed.sh << 'EOF'
#!/bin/bash
# Start script for Hallway Display with improved error handling and diagnostics

echo "=== Starting Hallway Display System ==="
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
    echo "❌ X server not accessible. Trying alternative methods..."
    # Try fixing X server access
    xhost +local: &>/dev/null
    if xset q &>/dev/null; then
        echo "✅ X server is now accessible"
    else
        echo "❌ X server still not accessible. Check your X server configuration."
        exit 1
    fi
fi

# Execute the Hallway Display using the wrapper script
cd "$(dirname "$0")"
PROJECT_DIR="$(pwd)"
echo "Starting Hallway Display from $PROJECT_DIR"

if [ -f "$PROJECT_DIR/run_hallway_display.sh" ]; then
    echo "Using Python wrapper script"
    exec "$PROJECT_DIR/run_hallway_display.sh" "$@"
else
    echo "Wrapper script not found, using direct execution"
    export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"
    exec python3 "$PROJECT_DIR/main.py" "$@"
fi
EOF

chmod +x start_fixed.sh
echo "✅ Created fixed start script"

echo "=== Setup Complete ==="
echo "To start the Hallway Display, use: ./start_fixed.sh"
echo "To test monitor control directly, use: ./test_monitor_control.py"
