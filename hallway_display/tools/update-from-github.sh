#!/bin/bash
# GitHub update script for Hallway Display
# This script helps pull the latest changes from GitHub
# and updates the installation on your Raspberry Pi

# Function to log
log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Navigate to the project directory
cd "$(dirname "$0")"
cd .. # Move up one level to the repository root

# Check if git is initialized
if [ ! -d ".git" ]; then
  log "Git repository not initialized. Setting up initial repository..."
  
  # Initialize git
  log "Initializing git repository..."
  git init
  
  # Add GitHub remote
  log "Adding GitHub remote..."
  git remote add origin https://github.com/theglow000/HallwayDisplay.git
  
  # Create an initial commit if needed
  if [ -z "$(git status --porcelain)" ]; then
    log "Creating initial commit..."
    git add .
    git commit -m "Initial commit from Raspberry Pi"
  fi
  
  # Set up branch and tracking
  log "Setting up main branch..."
  git branch -M main
  
  # Pull from GitHub
  log "Pulling code from GitHub..."
  git pull origin main --allow-unrelated-histories
  
  # Make scripts executable
  log "Setting permissions..."
  find . -name "*.sh" -type f -exec chmod +x {} \;
  find . -name "*.py" -type f -exec chmod +x {} \;
  
  log "Initial repository setup complete!"
  exit 0
fi

# Display current status
log "Current repository status:"
git status

# Fetch latest changes
log "Fetching latest changes from GitHub..."
git fetch origin

# Check if there are changes to pull
LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse @{u})

if [ "$LOCAL" = "$REMOTE" ]; then
  log "Already up-to-date. No changes to pull."
else
  # Check for local modifications
  if git diff-index --quiet HEAD --; then
    # No local changes, safe to pull
    log "Pulling latest changes..."
    git pull origin main
    
    # Make scripts executable
    log "Setting permissions..."
    chmod +x hallway_display/*.sh
    chmod +x hallway_display/main.py
    chmod +x hallway_display/configure.py
    
    # Restart the service if running
    log "Checking if service is running..."
    if systemctl is-active --quiet hallway-display.service; then
      log "Restarting service..."
      sudo systemctl restart hallway-display.service
      log "Service restarted."
    else
      log "Service not running. No need to restart."
    fi
  else
    # There are local modifications
    log "Warning: You have local modifications that would be overwritten by pull."
    log "Options:"
    log "1. Stash your changes: git stash"
    log "2. Discard your changes: git reset --hard origin/main"
    log "3. Merge manually: git pull (resolve conflicts)"
    
    # Ask what to do
    read -p "What would you like to do? (stash/reset/merge/cancel): " choice
    
    case "$choice" in
      stash)
        log "Stashing local changes..."
        git stash
        log "Pulling latest changes..."
        git pull origin main
        log "Your changes are saved in the stash. Use 'git stash apply' to restore them."
        ;;
      reset)
        log "Discarding local changes and pulling latest version..."
        git reset --hard origin/main
        log "Local changes have been discarded."
        ;;
      merge)
        log "Attempting to merge changes..."
        git pull origin main
        log "If there were conflicts, please resolve them manually."
        ;;
      *)
        log "Update canceled. No changes were made."
        exit 0
        ;;
    esac
  fi
fi

log "Update process completed."
