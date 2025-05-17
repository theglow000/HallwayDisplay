#!/bin/bash
# Simple GitHub repository setup script for Raspberry Pi
# This script properly sets up the Git repository on your Raspberry Pi

# Function to log
log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "=== Hallway Display GitHub Setup ==="

# Get current user
CURRENT_USER=$(whoami)
log "Current user: $CURRENT_USER"

# Check if running with sudo
if [ "$EUID" -eq 0 ]; then
  log "Warning: Running as root. Will ensure proper ownership for user."
  # Get the SUDO_USER if available, otherwise use a default
  ACTUAL_USER=${SUDO_USER:-theglow000}
  log "Will set ownership to: $ACTUAL_USER"
else
  ACTUAL_USER=$CURRENT_USER
fi

# Check current directory
CURRENT_DIR="$(pwd)"
log "Current directory: $CURRENT_DIR"

# Look for hallway_display directory
if [[ "$CURRENT_DIR" == *"/HallwayDisplay/tools"* ]]; then
  # We're in the tools directory, move up one level
  cd ..
  log "Changed to: $(pwd)"
elif [[ "$CURRENT_DIR" != *"/HallwayDisplay"* ]]; then
  log "Warning: Not in a HallwayDisplay directory."
  log "Please run this script from the HallwayDisplay directory."
  exit 1
fi

# Remove any existing .git directory to start fresh
if [ -d ".git" ]; then
  log "Removing existing Git repository..."
  rm -rf .git
fi

# Initialize a new Git repository
log "Initializing new Git repository..."
git init

# Configure Git
log "Configuring Git..."
git config user.name "theglow000"
git config user.email "theglow000@example.com"

# Add GitHub remote
log "Adding GitHub remote..."
git remote add origin https://github.com/theglow000/HallwayDisplay.git

# Create main branch
log "Creating main branch..."
git checkout -b main

# Fetch from GitHub
log "Fetching from GitHub..."
git fetch origin

# Reset local repository to match GitHub exactly
log "Resetting local repository to match GitHub..."
git reset --hard origin/main

# Set upstream branch
log "Setting upstream branch..."
git branch --set-upstream-to=origin/main main

# Set permissions
log "Setting file permissions..."
find . -name "*.sh" -exec chmod +x {} \;
find . -name "*.py" -exec chmod +x {} \;

# Fix ownership if running as root
if [ "$EUID" -eq 0 ]; then
  log "Setting correct ownership of repository files..."
  chown -R $ACTUAL_USER:$ACTUAL_USER .
  log "Ownership set to $ACTUAL_USER"
fi

log "Git repository setup complete!"
log "You can now use 'git pull' to get updates."
