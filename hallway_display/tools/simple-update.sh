#!/bin/bash
# Simple update script to pull changes from GitHub
# and update permissions correctly

# Function to log
log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "=== Hallway Display Update ==="

# Navigate to the project directory
cd "$(dirname "$0")"
cd .. # Move up one level to the repository root

# Display current status
log "Current repository status:"
git status

# Pull latest changes
log "Pulling latest changes from GitHub..."
git pull

# Check if pull was successful
if [ $? -eq 0 ]; then
  log "Pull successful!"
  
  # Set permissions
  log "Setting file permissions..."
  find . -name "*.sh" -exec chmod +x {} \;
  find . -name "*.py" -exec chmod +x {} \;
  
  # Check if service is running and offer to restart
  if systemctl is-active --quiet hallway-display.service; then
    log "Hallway Display service is running."
    read -p "Do you want to restart the service to apply changes? (y/n): " restart_service
    
    if [[ "$restart_service" == "y" ]]; then
      log "Restarting service..."
      sudo systemctl restart hallway-display.service
      log "Service restarted."
    else
      log "Service not restarted. Changes will apply on next restart."
    fi
  else
    log "Hallway Display service is not running."
    read -p "Do you want to start the service now? (y/n): " start_service
    
    if [[ "$start_service" == "y" ]]; then
      log "Starting service..."
      sudo systemctl start hallway-display.service
      log "Service started."
    fi
  fi
else
  log "Error pulling changes. Please check your network connection or repository status."
fi

log "Update process completed."
