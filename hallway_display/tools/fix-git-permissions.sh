#!/bin/bash
# Fix Git repository ownership
# This script changes the ownership of Git repository files
# from root to the current user

# Function to log
log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "=== Fixing Git Repository Ownership ==="

# Check if we're in the HallwayDisplay directory
CURRENT_DIR="$(pwd)"
if [[ "$CURRENT_DIR" != *"/HallwayDisplay"* ]]; then
  log "Warning: Not in a HallwayDisplay directory."
  log "Please run this script from the HallwayDisplay directory."
  exit 1
fi

# Get the current username
USERNAME=$(whoami)
log "Current user: $USERNAME"

# We need sudo to change ownership
log "This script needs sudo permissions to change file ownership"
log "You'll be prompted for your password"

# Change ownership of all files in the Git directory
sudo chown -R $USERNAME:$USERNAME .git/
log "Changed ownership of .git directory to $USERNAME"

# Try a Git command to verify access
if git status &>/dev/null; then
  log "Git repository accessible! Ownership fixed successfully."
else
  log "Still having issues with Git access. Additional debugging may be needed."
fi

log "Ownership fix complete!"
