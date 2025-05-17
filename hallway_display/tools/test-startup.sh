#!/bin/bash
# Test script for Hallway Display startup with proper permissions
# This script helps verify that the startup process works correctly

# Function to log messages
log() {
  echo "$1"
}

log "=== Hallway Display Start Test ==="

# Check if X server is accessible
log "Testing X server access..."
if ! xset q &>/dev/null; then
  log "X server not accessible. Trying to fix..."
  export DISPLAY=:0
  export XAUTHORITY=/home/theglow000/.Xauthority
  
  if ! xset q &>/dev/null; then
    log "X server still not accessible. Trying with xhost..."
    xhost +local: || true
    
    if ! xset q &>/dev/null; then
      log "ERROR: Cannot access X server. Make sure you're running from a desktop session."
      exit 1
    fi
  fi
fi

log "X server is accessible!"

# Ensure permissions are correct for the start script
log "Setting permissions for start_enhanced.sh..."
chmod +x ../start_enhanced.sh

# Run the enhanced start script with proper environment variables
log "Starting Hallway Display with enhanced script..."
cd ..
DISPLAY=:0 XAUTHORITY=/home/theglow000/.Xauthority ./start_enhanced.sh
