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
BASE_DIR=$(pwd)

# Check if this is a proper Git repository
if [ ! -d ".git" ]; then
  log "Error: Not a Git repository. Please run git-setup.sh first."
  log "You can run: ./tools/git-setup.sh"
  exit 1
fi

# Display current status
log "Current repository status:"
git status

# Check if we have a remote named origin
if ! git remote | grep -q "^origin$"; then
  log "Error: No remote named 'origin' found."
  log "Setting up remote origin..."
  git remote add origin https://github.com/theglow000/HallwayDisplay.git
fi

# Fetch latest changes
log "Fetching latest changes from GitHub..."
git fetch origin

# Check current branch
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null)
if [ -z "$CURRENT_BRANCH" ]; then
  log "No current branch. Creating 'main' branch..."
  git checkout -b main
  CURRENT_BRANCH="main"
elif [ "$CURRENT_BRANCH" = "master" ]; then
  log "Currently on 'master' branch. Renaming to 'main'..."
  git branch -m master main
  CURRENT_BRANCH="main"
fi

# Check if branch has upstream
if ! git rev-parse --abbrev-ref --symbolic-full-name @{u} &>/dev/null; then
  log "Setting upstream branch to origin/main..."
  git branch --set-upstream-to=origin/main "$CURRENT_BRANCH"
fi

# Check if there are changes to pull
if git rev-parse @{u} &>/dev/null; then
  LOCAL=$(git rev-parse @)
  REMOTE=$(git rev-parse @{u})

  if [ "$LOCAL" = "$REMOTE" ]; then
    log "Already up-to-date. No changes to pull."
  else
    # Check for local modifications
    if git diff-index --quiet HEAD -- 2>/dev/null; then
      # No local changes, safe to pull
      log "Pulling latest changes..."
      git pull origin main
      
      # Make scripts executable
      log "Setting permissions..."
      chmod +x *.sh tools/*.sh main.py configure.py 2>/dev/null
      
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
else
  log "No upstream branch found. Unable to check for updates."
  log "Try running: git push -u origin main"
fi

log "Update process completed."
