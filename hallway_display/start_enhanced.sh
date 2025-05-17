#!/bin/bash
# Enhanced startup script for the Hallway Display system
# This version includes improved handling of X server permissions and
# better error recovery for Raspberry Pi environments

LOG_FILE="logs/startup-$(date +'%Y-%m-%d').log"

# Function to log messages
log() {
  echo "$1"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Create logs directory if it doesn't exist
mkdir -p logs

log "=== Starting Hallway Display System ==="
log "User: $(whoami)"
log "Groups: $(groups)"

# Handle X server display environment
setup_display_environment() {
  log "Setting up display environment..."
  
  # Try to auto-detect display if not set
  if [ -z "$DISPLAY" ]; then
    log "DISPLAY not set, auto-detecting..."
    for disp in ":0" ":0.0" ":1" ":2"; do
      export DISPLAY=$disp
      if XAUTHORITY="$HOME/.Xauthority" xset q &>/dev/null; then
        log "Found working display: $DISPLAY with home Xauthority"
        export XAUTHORITY="$HOME/.Xauthority"
        return 0
      fi
      
      # Try specific theglow000 user if we're running as root
      if [ "$EUID" -eq 0 ]; then
        if XAUTHORITY="/home/theglow000/.Xauthority" xset q &>/dev/null; then
          log "Found working display: $DISPLAY with theglow000 Xauthority"
          export XAUTHORITY="/home/theglow000/.Xauthority"
          return 0
        fi
      fi
    done
    
    # If we get here, auto-detection failed
    log "Auto-detection failed, using fallback display settings"
    export DISPLAY=":0"
    export XAUTHORITY="$HOME/.Xauthority"
    
    # If running as root, try to allow X server access
    if [ "$EUID" -eq 0 ]; then
      log "Running as root, attempting to grant X server access..."
      sudo -u theglow000 DISPLAY=:0 XAUTHORITY=/home/theglow000/.Xauthority xhost +si:localuser:root || true
      xhost +local:root || true
    fi
  else
    log "Using existing display settings: DISPLAY=$DISPLAY, XAUTHORITY=$XAUTHORITY"
  fi
}

# Verify X server accessibility
verify_x_server() {
  log "Verifying X server access..."
  if xset q &>/dev/null; then
    log "✅ X server is accessible"
    return 0
  else
    log "❌ X server is NOT accessible"
    return 1
  fi
}

# Check and install missing dependencies
check_dependencies() {
  log "Checking dependencies..."
  missing_deps=0

  # Check for Python
  if ! command -v python3 &> /dev/null; then
    log "Error: Python 3 is not installed or not in PATH"
    missing_deps=1
  fi

  # Check for ddcutil
  if ! command -v ddcutil &> /dev/null; then
    log "Error: ddcutil is not installed or not in PATH"
    missing_deps=1
  fi

  # Check for xdotool
  if ! command -v xdotool &> /dev/null; then
    log "Error: xdotool is not installed or not in PATH"
    missing_deps=1
  fi

  # Check for chromium-browser
  if ! command -v chromium-browser &> /dev/null; then
    log "Error: chromium-browser is not installed or not in PATH"
    missing_deps=1
  fi

  # Check if virtual environment exists and use it if it does
  if [ -d "hallway_venv" ]; then
    log "Virtual environment found, activating..."
    source hallway_venv/bin/activate
    PYTHON_CMD="hallway_venv/bin/python3"
  else
    PYTHON_CMD="python3"
  fi

  # Check for critical Python modules
  $PYTHON_CMD -c "import evdev" 2>/dev/null || { log "Error: evdev Python module not installed"; missing_deps=1; }
  $PYTHON_CMD -c "import RPi.GPIO as GPIO" 2>/dev/null || { log "Error: RPi.GPIO Python module not installed"; missing_deps=1; }
  $PYTHON_CMD -c "import psutil" 2>/dev/null || { log "Error: psutil Python module not installed"; missing_deps=1; }

  if [ $missing_deps -eq 1 ]; then
    log "Please install missing dependencies. See README.md for installation instructions."
    return 1
  fi

  log "All dependencies found."
  return 0
}

# Setup proper permissions for hardware access
setup_permissions() {
  log "Setting up permissions for hardware access..."
  
  # Check if running as root
  if [ "$EUID" -ne 0 ]; then
    log "Not running as root - checking group permissions..."
    
    # Check for gpio group membership
    if ! groups | grep -q "gpio"; then
      log "Warning: Current user is not part of 'gpio' group"
    fi
    
    # Check for i2c group membership
    if ! groups | grep -q "i2c"; then
      log "Warning: Current user is not part of 'i2c' group"
    fi
    
    # Check for video group membership
    if ! groups | grep -q "video"; then
      log "Warning: Current user is not part of 'video' group"
    fi
  else
    log "Running as root, device permissions should be available"
  fi
  
  # Try to fix common permission issues
  if [ -e "/dev/gpiomem" ] && [ "$EUID" -eq 0 ]; then
    chmod a+rw /dev/gpiomem || true
    log "Set permissions on /dev/gpiomem"
  fi
  
  if [ -e "/dev/i2c-1" ] && [ "$EUID" -eq 0 ]; then
    chmod a+rw /dev/i2c-1 || true
    log "Set permissions on /dev/i2c-1"
  fi
}

# Main execution flow
main() {
  # Navigate to the script directory
  cd "$(dirname "$0")"
  
  # Make sure scripts are executable
  chmod +x main.py configure.py
  
  # Setup display environment
  setup_display_environment
  
  # Verify X server access
  if ! verify_x_server; then
    log "X server access issue - attempting recovery"
    # If using default DISPLAY, try alternatives
    if [ "$DISPLAY" = ":0" ]; then
      for alt_display in ":1" ":0.0"; do
        log "Trying alternative display: $alt_display"
        export DISPLAY=$alt_display
        if verify_x_server; then
          break
        fi
      done
    fi
    
    # If still not working and not root, suggest running with sudo
    if ! verify_x_server && [ "$EUID" -ne 0 ]; then
      log "Still unable to access X server. You may need to run with sudo."
      log "Try: sudo -E ./start.sh"
      echo "X server not accessible. Try running with sudo: sudo -E ./start.sh"
      exit 1
    fi
  fi
  
  # Check dependencies
  if ! check_dependencies; then
    log "Dependency check failed"
    exit 1
  fi
  
  # Setup hardware permissions
  setup_permissions
  
  # Check if the DAkBoard and Home Assistant URLs are set
  $PYTHON_CMD -c "from config import settings; exit(0 if settings.DAKBOARD_URL != 'https://dakboard.com/app/screenurl' and settings.HOME_ASSISTANT_URL != 'http://homeassistant.local:8123' else 1)" 2>/dev/null
  if [ $? -ne 0 ]; then
    log "Warning: Default URLs detected in config/settings.py"
    log "Please update the DAKBOARD_URL and HOME_ASSISTANT_URL settings before running."
  fi
  
  # Start the system
  log "Starting Hallway Display system..."
  log "Using Python command: $PYTHON_CMD"
  
  # Use tee to capture output while also displaying it
  $PYTHON_CMD main.py 2>&1 | tee -a "$LOG_FILE"
  
  # Deactivate virtual environment if it was activated
  if [ -d "hallway_venv" ]; then
    deactivate
  fi
  
  log "Hallway Display system has exited with code $?"
}

# Run the main function
main
