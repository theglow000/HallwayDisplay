#!/bin/bash
# Display environment test script for Hallway Display
# This script helps diagnose common display environment issues
# on Raspberry Pi systems

# Log file
LOG_FILE="display_env_test_$(date +%Y%m%d_%H%M%S).log"

# Function to log messages
log() {
  echo "$1"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Header
log "=== Hallway Display Environment Test ==="
log "Date: $(date)"
log "User: $(whoami)"
log "Groups: $(groups)"
log ""

# Check environment variables
log "=== Environment Variables ==="
log "DISPLAY=$DISPLAY"
log "XAUTHORITY=$XAUTHORITY"
log ""

# Check X server
log "=== X Server Test ==="
if xset q &>/dev/null; then
  log "✅ X server is accessible"
else
  log "❌ X server is NOT accessible"
  log "Trying to set DISPLAY=:0..."
  export DISPLAY=:0
  if xset q &>/dev/null; then
    log "✅ X server is now accessible with DISPLAY=:0"
  else
    log "❌ X server is still NOT accessible"
    log "Trying other common DISPLAY values..."
    for disp in ":1" ":2" ":0.0"; do
      export DISPLAY=$disp
      if xset q &>/dev/null; then
        log "✅ X server is accessible with DISPLAY=$disp"
        log "You should set this value in start.sh"
        break
      fi
    done
  fi
fi
log ""

# Check Xauthority file
log "=== Xauthority Check ==="
if [ -f "$XAUTHORITY" ]; then
  log "✅ Xauthority file exists: $XAUTHORITY"
  log "File permissions: $(ls -la "$XAUTHORITY")"
else
  log "❌ Xauthority file does NOT exist: $XAUTHORITY"
  log "Trying to find valid Xauthority file..."
  
  # Try to find common Xauthority locations
  potential_auth=( 
    "/home/$(whoami)/.Xauthority"
    "/home/theglow000/.Xauthority"
    "/run/user/$(id -u)/gdm/Xauthority"
    "$(find /tmp -name 'xauth_*' 2>/dev/null | head -n1)"
  )
  
  for auth_file in "${potential_auth[@]}"; do
    if [ -f "$auth_file" ]; then
      log "Found potential Xauthority file: $auth_file"
      log "Trying this file..."
      export XAUTHORITY="$auth_file"
      if xset q &>/dev/null; then
        log "✅ X server accessible with XAUTHORITY=$auth_file"
        log "You should set this value in start.sh"
        break
      fi
    fi
  done
fi
log ""

# Check GPIO access
log "=== GPIO Access Test ==="
if [ -e "/dev/gpiomem" ]; then
  log "GPIO memory device exists: /dev/gpiomem"
  log "Permissions: $(ls -la /dev/gpiomem)"
  
  if [ -w "/dev/gpiomem" ]; then
    log "✅ Current user can write to /dev/gpiomem"
  else
    log "❌ Current user CANNOT write to /dev/gpiomem"
    log "You may need to add user to gpio group or run with sudo"
  fi
else
  log "❌ GPIO memory device does NOT exist: /dev/gpiomem"
  log "This may indicate GPIO access is not available on this system"
fi
log ""

# Check I2C access
log "=== I2C Access Test ==="
I2C_BUS="/dev/i2c-1"
if [ -e "$I2C_BUS" ]; then
  log "I2C bus exists: $I2C_BUS"
  log "Permissions: $(ls -la $I2C_BUS)"
  
  if [ -w "$I2C_BUS" ]; then
    log "✅ Current user can write to $I2C_BUS"
  else
    log "❌ Current user CANNOT write to $I2C_BUS"
    log "You may need to add user to i2c group or run with sudo"
  fi
  
  # Try detecting I2C devices
  log "Scanning for I2C devices..."
  if command -v i2cdetect &>/dev/null; then
    i2cdetect -y 1 >> "$LOG_FILE" 2>&1
    log "Verify if I2C devices are detected in the log file"
  else
    log "i2cdetect not available, install i2c-tools package"
  fi
else
  log "❌ I2C bus does NOT exist: $I2C_BUS"
  log "You may need to enable I2C in raspi-config"
fi
log ""

# Test ddcutil
log "=== ddcutil Test ==="
if command -v ddcutil &>/dev/null; then
  log "✅ ddcutil is installed"
  log "Testing monitor detection..."
  ddcutil detect >> "$LOG_FILE" 2>&1
  log "Verify if monitor is detected in the log file"
else
  log "❌ ddcutil is NOT installed"
  log "You can install it with: sudo apt install ddcutil"
fi
log ""

# Test browser launch
log "=== Browser Launch Test ==="
if command -v chromium-browser &>/dev/null; then
  log "✅ Chromium browser is installed"
  
  # Try quick launch test with timeout (don't actually open browser)
  log "Testing if browser can connect to display..."
  timeout 2s chromium-browser --no-sandbox --headless about:blank &>/dev/null
  if [ $? -eq 124 ]; then
    # Timeout is actually a success here (browser launched)
    log "✅ Browser appears to connect to display"
  else
    log "❌ Browser may have issues connecting to display"
  fi
else
  log "❌ Chromium browser is NOT installed"
fi
log ""

# Final notes
log "=== Summary ==="
log "Test completed. Common issues:"
log "1. DISPLAY environment variable not set correctly"
log "2. XAUTHORITY not pointing to valid file"
log "3. Current user not in required groups (gpio, i2c, video)"
log "4. I2C or GPIO not enabled in raspi-config"
log ""

log "If you need to run with sudo, use:"
log "xhost +local:root # Allow root X11 access temporarily"
log "sudo -E ./start.sh # Preserve environment variables"
log ""

log "Test log saved to: $LOG_FILE"
