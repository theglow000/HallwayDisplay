#!/bin/bash
# Monitor control fix script for Hallway Display
# This script applies fixes for common monitor control issues

# Function to log messages
log() {
  echo "$1"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "monitor-fix.log"
}

log "=== Hallway Display Monitor Control Fix ==="
log "Date: $(date)"
log "User: $(whoami)"

# Get options
FIX_PERMISSIONS=0
FIX_XSERVER=0
INSTALL_DEPS=0
TEST_MONITOR=0

# Parse command line options
while [ $# -gt 0 ]; do
  case "$1" in
    --permissions)
      FIX_PERMISSIONS=1
      shift
      ;;
    --xserver)
      FIX_XSERVER=1
      shift
      ;;
    --dependencies)
      INSTALL_DEPS=1
      shift
      ;;
    --test)
      TEST_MONITOR=1
      shift
      ;;
    --all)
      FIX_PERMISSIONS=1
      FIX_XSERVER=1
      INSTALL_DEPS=1
      TEST_MONITOR=1
      shift
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--permissions] [--xserver] [--dependencies] [--test] [--all]"
      exit 1
      ;;
  esac
done

# If no options specified, show usage
if [ $FIX_PERMISSIONS -eq 0 ] && [ $FIX_XSERVER -eq 0 ] && [ $INSTALL_DEPS -eq 0 ] && [ $TEST_MONITOR -eq 0 ]; then
  echo "Usage: $0 [--permissions] [--xserver] [--dependencies] [--test] [--all]"
  echo "  --permissions  Fix I2C and device permissions"
  echo "  --xserver      Fix X server display access"
  echo "  --dependencies Install required dependencies"
  echo "  --test         Test monitor control"
  echo "  --all          Apply all fixes"
  exit 0
fi

# Fix I2C and device permissions
if [ $FIX_PERMISSIONS -eq 1 ]; then
  log "=== Fixing I2C and Device Permissions ==="
  
  # Check if user is in i2c group
  if ! groups | grep -q "i2c"; then
    log "Adding user to i2c group..."
    sudo usermod -a -G i2c $USER
    log "Added user to i2c group. You will need to log out and back in for this to take effect."
  else
    log "User already in i2c group."
  fi
  
  # Check i2c device permissions
  for i in {0..10}; do
    if [ -e "/dev/i2c-$i" ]; then
      log "Setting permissions for /dev/i2c-$i..."
      sudo chmod 666 /dev/i2c-$i
    fi
  done
  
  # Add udev rule for persistent i2c permissions
  if [ ! -f "/etc/udev/rules.d/99-i2c-permissions.rules" ]; then
    log "Creating udev rule for persistent i2c permissions..."
    echo 'SUBSYSTEM=="i2c-dev", GROUP="i2c", MODE="0666"' | sudo tee /etc/udev/rules.d/99-i2c-permissions.rules > /dev/null
    sudo udevadm control --reload-rules
    sudo udevadm trigger
    log "Created udev rule for i2c permissions."
  else
    log "Udev rule for i2c permissions already exists."
  fi
  
  log "Permission fixes applied."
fi

# Fix X server display access
if [ $FIX_XSERVER -eq 1 ]; then
  log "=== Fixing X Server Display Access ==="
  
  # Set DISPLAY and XAUTHORITY if not set
  if [ -z "$DISPLAY" ]; then
    log "Setting DISPLAY=:0"
    export DISPLAY=:0
  fi
  
  if [ -z "$XAUTHORITY" ]; then
    log "Setting XAUTHORITY=/home/theglow000/.Xauthority"
    export XAUTHORITY=/home/theglow000/.Xauthority
  fi
  
  # Allow X server access
  log "Allowing X server access..."
  xhost +local: || true
  
  # Create X server wrapper script
  log "Creating X server wrapper script..."
  cat > $HOME/.xsessionrc << EOF
# Allow X server access for the current user
xhost +local:
EOF
  chmod +x $HOME/.xsessionrc
  log "Created X server wrapper script."
  
  # Update service file if exists
  if [ -f "/etc/systemd/system/hallway-display.service" ]; then
    log "Updating systemd service file..."
    sudo sed -i 's/^Environment=/Environment="DISPLAY=:0" "XAUTHORITY=\/home\/theglow000\/.Xauthority" /' /etc/systemd/system/hallway-display.service
    sudo systemctl daemon-reload
    log "Updated systemd service file."
  fi
  
  log "X server access fixes applied."
fi

# Install required dependencies
if [ $INSTALL_DEPS -eq 1 ]; then
  log "=== Installing Required Dependencies ==="
  
  log "Updating package lists..."
  sudo apt update
  
  log "Installing ddcutil and related packages..."
  sudo apt install -y ddcutil i2c-tools cec-utils
  
  log "Installing Python packages..."
  pip3 install --upgrade smbus2 psutil
  
  log "Dependencies installed."
fi

# Test monitor control
if [ $TEST_MONITOR -eq 1 ]; then
  log "=== Testing Monitor Control ==="
  
  # Test ddcutil
  log "Testing ddcutil..."
  if command -v ddcutil &>/dev/null; then
    log "Detecting monitors..."
    ddcutil detect > monitor-detection.log 2>&1
    log "Monitor detection saved to monitor-detection.log"
    
    # Test brightness control
    log "Testing brightness control..."
    if ddcutil getvcp 10 &>/dev/null; then
      log "✅ Can read brightness"
    else
      log "❌ Cannot read brightness"
      log "Trying with --noverify option..."
      if ddcutil --noverify getvcp 10 &>/dev/null; then
        log "✅ Can read brightness with --noverify"
        
        # Update monitor.py to use --noverify
        if [ -f "../modules/monitor.py" ]; then
          log "Updating monitor.py to use --noverify by default..."
          sed -i 's/verify=True/verify=False/g' ../modules/monitor.py
          log "Updated monitor.py"
        fi
      else
        log "❌ Cannot read brightness even with --noverify"
      fi
    fi
    
    # Test power control
    log "Testing power state control..."
    if ddcutil getvcp D6 &>/dev/null; then
      log "✅ Can read power state"
    else
      log "❌ Cannot read power state"
      log "Trying alternative methods..."
      
      # Test DPMS
      if command -v xset &>/dev/null && xset q &>/dev/null; then
        log "✅ DPMS via xset is available"
      else
        log "❌ DPMS via xset is not available"
      fi
      
      # Test tvservice
      if command -v tvservice &>/dev/null; then
        log "✅ tvservice is available"
      else
        log "❌ tvservice is not available"
      fi
    fi
  else
    log "❌ ddcutil is not installed"
  fi
  
  # Test Python module
  log "Testing monitor.py module..."
  if [ -f "../modules/monitor.py" ]; then
    cat > test_monitor.py << EOF
import sys
import os
sys.path.insert(0, '..')
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
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
EOF

    python3 test_monitor.py > monitor-module-test.log 2>&1
    log "Monitor module test saved to monitor-module-test.log"
    cat monitor-module-test.log
  else
    log "❌ monitor.py not found"
  fi
  
  log "Monitor control tests complete."
fi

log "=== Summary ==="
log "Monitor control fixes and tests complete."
log "Refer to monitor-fix.log for details."
log "If you still have issues, try running the full diagnostic script:"
log "  ./monitor-diagnostic.sh"
