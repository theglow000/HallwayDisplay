#!/bin/bash
# Monitor troubleshooting script for Hallway Display
# This script helps diagnose and fix monitor control issues

# Function to log messages
log() {
  echo "$1"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "monitor-diagnostic.log"
}

log "=== Hallway Display Monitor Diagnostics ==="
log "Date: $(date)"
log "User: $(whoami)"
log "Groups: $(groups)"

# Check X server display
log "=== X Server Display Check ==="
if [ -z "$DISPLAY" ]; then
  log "DISPLAY environment variable not set. Setting to :0"
  export DISPLAY=:0
else
  log "DISPLAY=$DISPLAY"
fi

if [ -z "$XAUTHORITY" ]; then
  log "XAUTHORITY environment variable not set. Setting default."
  export XAUTHORITY=/home/theglow000/.Xauthority
else
  log "XAUTHORITY=$XAUTHORITY"
fi

# Test X server access
log "Testing X server access..."
if xset q &>/dev/null; then
  log "✅ X server is accessible"
else
  log "❌ X server is NOT accessible"
  
  # Try alternative DISPLAY values
  for disp in ":1" ":0.0" ":2"; do
    log "Trying DISPLAY=$disp"
    export DISPLAY=$disp
    if xset q &>/dev/null; then
      log "✅ X server is accessible with DISPLAY=$disp"
      break
    fi
  done
  
  # If still not working try xhost
  if ! xset q &>/dev/null; then
    log "Trying xhost to allow access..."
    DISPLAY=:0 xhost +local: || true
    
    if xset q &>/dev/null; then
      log "✅ X server access granted with xhost"
    else
      log "❌ Still cannot access X server"
      log "You may need to run this from a graphical session or use: sudo -E ./monitor-diagnostic.sh"
    fi
  fi
fi

# Check I2C access for DDC/CI
log "=== I2C/DDC Access Check ==="
I2C_BUS_NUM=${1:-1}  # Default to bus 1, can be overridden from command line
I2C_BUS="/dev/i2c-$I2C_BUS_NUM"

log "Checking I2C bus access..."
if [ -e "$I2C_BUS" ]; then
  log "I2C bus exists: $I2C_BUS"
  
  if [ -r "$I2C_BUS" ] && [ -w "$I2C_BUS" ]; then
    log "✅ I2C bus is readable and writable"
  else
    log "❌ I2C bus permission issue"
    log "Current permissions: $(ls -la $I2C_BUS)"
    log "Consider running: sudo chmod 666 $I2C_BUS"
  fi
else
  log "❌ I2C bus $I2C_BUS does not exist"
  log "Available I2C buses:"
  ls -la /dev/i2c* 2>/dev/null || log "No I2C buses found"
fi

# Check ddcutil
log "=== DDC/CI Control Check ==="
if command -v ddcutil &>/dev/null; then
  log "✅ ddcutil is installed"
  
  # Try to detect monitors
  log "Detecting monitors..."
  ddcutil detect > monitor-detection.log 2>&1
  log "Monitor detection results saved to monitor-detection.log"
  
  # Check if ddcutil can communicate with the monitor
  log "Testing monitor communication..."
  if ddcutil --bus=$I2C_BUS_NUM getvcp 10 &>/dev/null; then
    log "✅ ddcutil can communicate with the monitor"
    
    # Test brightness control
    log "Testing brightness control..."
    CURRENT_BRIGHTNESS=$(ddcutil --bus=$I2C_BUS_NUM getvcp 10 | grep -oP 'current value = \K\d+' || echo "unknown")
    log "Current brightness: $CURRENT_BRIGHTNESS"
    
    # Only test setting brightness if we could read it
    if [ "$CURRENT_BRIGHTNESS" != "unknown" ]; then
      TEST_BRIGHTNESS=$((CURRENT_BRIGHTNESS + 10))
      if [ $TEST_BRIGHTNESS -gt 100 ]; then
        TEST_BRIGHTNESS=$((CURRENT_BRIGHTNESS - 10))
      fi
      
      log "Setting test brightness to $TEST_BRIGHTNESS..."
      if ddcutil --bus=$I2C_BUS_NUM setvcp 10 $TEST_BRIGHTNESS &>/dev/null; then
        log "✅ Brightness control works"
        # Restore original brightness
        ddcutil --bus=$I2C_BUS_NUM setvcp 10 $CURRENT_BRIGHTNESS &>/dev/null
      else
        log "❌ Failed to set brightness"
      fi
    fi
    
    # Test power control
    log "Testing power state control..."
    if ddcutil --bus=$I2C_BUS_NUM getvcp D6 &>/dev/null; then
      log "✅ Can read power state"
      
      # We don't actually change power state in diagnostic to avoid disruption
      log "Monitor supports power control via DDC/CI"
    else
      log "❌ Cannot read power state"
    fi
  else
    log "❌ ddcutil cannot communicate with the monitor"
    log "Trying with --noverify option..."
    
    if ddcutil --noverify --bus=$I2C_BUS_NUM getvcp 10 &>/dev/null; then
      log "✅ ddcutil works with --noverify option"
      log "Add '--noverify' to ddcutil commands in monitor.py"
    else
      log "❌ Communication failed even with --noverify"
    fi
  fi
else
  log "❌ ddcutil is not installed"
  log "Install with: sudo apt install ddcutil"
fi

# Test alternative power control methods
log "=== Alternative Power Control Methods ==="

# 1. DPMS via xset
log "Testing DPMS via xset..."
if command -v xset &>/dev/null && xset q &>/dev/null; then
  log "✅ xset DPMS status:"
  xset q | grep -A 2 "DPMS" > dpms-status.log
  cat dpms-status.log | while read line; do
    log "  $line" 
  done
  
  # We don't actually change power state in diagnostic
  log "DPMS control should be available via xset"
else
  log "❌ Cannot access DPMS control via xset"
fi

# 2. CEC control
log "Testing CEC control..."
if command -v cec-client &>/dev/null; then
  log "✅ cec-client is installed"
  log "CEC adapter info:"
  echo "pow 0" | cec-client -s -d 1 > cec-status.log 2>&1
  log "CEC status saved to cec-status.log"
else
  log "❌ cec-client is not installed"
  log "Install with: sudo apt install cec-utils"
fi

# 3. tvservice (Raspberry Pi specific)
log "Testing tvservice control..."
if command -v tvservice &>/dev/null; then
  log "✅ tvservice is available"
  log "TV service status:"
  tvservice -s > tvservice-status.log 2>&1
  cat tvservice-status.log | while read line; do
    log "  $line" 
  done
else
  log "❌ tvservice is not available"
  log "This is normal if you're not on a Raspberry Pi"
fi

# Check Python dependencies
log "=== Python Monitor Control Check ==="
if command -v python3 &>/dev/null; then
  log "Testing monitor control module..."
  cat > test_monitor.py << EOF
import sys
import os
sys.path.insert(0, '.')
try:
    from modules.monitor import MonitorController
    monitor = MonitorController()
    print("Monitor module initialized successfully")
    
    # Try to get power state
    power_state = monitor.get_power_state()
    print(f"Current power state: {power_state}")
    
    # Try to get brightness
    brightness = monitor.get_brightness()
    print(f"Current brightness: {brightness}")
    
    # Report available methods
    methods = []
    if hasattr(monitor, '_try_xset_dpms') and callable(monitor._try_xset_dpms):
        methods.append("DPMS (xset)")
    if hasattr(monitor, '_try_cec_control') and callable(monitor._try_cec_control):
        methods.append("CEC")
    if hasattr(monitor, '_try_tvservice') and callable(monitor._try_tvservice):
        methods.append("tvservice")
    print(f"Alternative control methods: {', '.join(methods)}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
EOF

  log "Running monitor test..."
  python3 test_monitor.py > monitor-module-test.log 2>&1
  log "Monitor module test results saved to monitor-module-test.log"
  cat monitor-module-test.log | while read line; do
    log "  $line" 
  done
else
  log "❌ Python 3 not found"
fi

# Summary
log "=== Summary ==="
log "Monitor diagnostics complete. Check the log files for detailed results."
log "Main diagnostic log: monitor-diagnostic.log"
log "Additional logs:"
log "- monitor-detection.log: ddcutil monitor detection"
log "- dpms-status.log: DPMS status"
log "- cec-status.log: CEC adapter information"
log "- tvservice-status.log: Raspberry Pi TV service status"
log "- monitor-module-test.log: Python monitor module test"

log "Recommendations:"
log "1. Verify X server is accessible (DISPLAY is set correctly)"
log "2. Make sure user has access to I2C bus (add to i2c group)"
log "3. Confirm monitor supports DDC/CI (enable in monitor's OSD menu)"
log "4. Try alternative control methods if DDC/CI fails"
log "5. Consider using sudo for testing, but fix permissions for operation"

log "See README.md troubleshooting section for additional help."
