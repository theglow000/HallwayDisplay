#!/bin/bash
# GitHub repository setup script for Hallway Display
# This script fixes repository structure issues and properly sets up Git

# Function to log
log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "=== Hallway Display Git Repository Setup ==="

# Determine current directory
CURRENT_DIR="$(pwd)"
BASE_DIR="$(dirname "$CURRENT_DIR")"
log "Current directory: $CURRENT_DIR"
log "Base directory: $BASE_DIR"

# Check if we're in the tools directory within HallwayDisplay
if [[ "$CURRENT_DIR" != *"/HallwayDisplay/tools" ]]; then
  log "Warning: This script should be run from the HallwayDisplay/tools directory."
  read -p "Continue anyway? (y/n): " continue_anyway
  if [[ "$continue_anyway" != "y" ]]; then
    log "Exiting..."
    exit 1
  fi
fi

# Move up to the parent directory
cd "$BASE_DIR"
log "Changed to: $(pwd)"

# Check the directory structure
log "Checking directory structure..."
if [ -d "hallway_display" ] && [ -d "HallwayDisplay" ]; then
  log "Found both hallway_display and HallwayDisplay directories."
  log "This appears to be a duplicate directory structure."
  
  # Check if HallwayDisplay/hallway_display exists
  if [ -d "HallwayDisplay/hallway_display" ]; then
    log "Found HallwayDisplay/hallway_display - this is likely the correct structure."
    
    # Ask if we should fix the structure
    read -p "Would you like to fix the directory structure? This will reorganize files. (y/n): " fix_structure
    if [[ "$fix_structure" == "y" ]]; then
      log "Backing up current structure..."
      mkdir -p backup
      cp -r hallway_display backup/
      
      log "Removing duplicate directory..."
      rm -rf hallway_display
      
      log "Moving HallwayDisplay to be the main Git repository..."
      cd HallwayDisplay
      
      # Initialize Git repository here if not already
      if [ ! -d ".git" ]; then
        log "Initializing Git repository..."
        git init
        git config --local user.email "theglow000@example.com"
        git config --local user.name "theglow000"
        git remote add origin https://github.com/theglow000/HallwayDisplay.git
        
        # Create main branch and set it as default
        git checkout -b main
        
        log "Fetching from GitHub..."
        git fetch origin
        
        # Check if there's content on GitHub
        if git ls-remote --exit-code origin main &>/dev/null; then
          log "Setting up tracking branch for main..."
          git branch --set-upstream-to=origin/main main
        fi
      else
        log "Git repository already initialized in HallwayDisplay."
      fi
    fi
  else
    log "Unexpected directory structure. Proceeding with caution."
  fi
else
  # Single directory case
  log "Checking Git repository status..."
  
  # Check if we're already in a Git repository
  if [ -d ".git" ]; then
    log "Git repository already exists. Verifying remote..."
    GIT_REMOTE=$(git remote -v | grep origin | grep fetch | awk '{print $2}')
    if [[ "$GIT_REMOTE" == *"github.com/theglow000/HallwayDisplay"* ]]; then
      log "Remote correctly points to GitHub repository."
    else
      log "Updating remote to point to GitHub repository..."
      git remote remove origin
      git remote add origin https://github.com/theglow000/HallwayDisplay.git
    fi
    
    # Check current branch
    CURRENT_BRANCH=$(git branch --show-current)
    if [ "$CURRENT_BRANCH" == "main" ]; then
      log "Already on main branch."
    elif [ "$CURRENT_BRANCH" == "master" ]; then
      log "Creating main branch from master..."
      git branch -m master main
    else
      log "Creating main branch..."
      git checkout -b main
    fi
    
    log "Fetching from GitHub..."
    git fetch origin
    
    # Check if there's content on GitHub
    if git ls-remote --exit-code origin main &>/dev/null; then
      log "Setting up tracking branch for main..."
      git branch --set-upstream-to=origin/main main
    fi
  else
    # No Git repository yet, check if we should initialize
    if [ -d "hallway_display" ]; then
      log "Found hallway_display directory but no Git repository."
      read -p "Initialize Git repository here? (y/n): " init_git
      
      if [[ "$init_git" == "y" ]]; then
        log "Initializing Git repository..."
        git init
        git config --local user.email "theglow000@example.com"
        git config --local user.name "theglow000"
        git remote add origin https://github.com/theglow000/HallwayDisplay.git
        
        # Create main branch
        git checkout -b main
        
        log "Fetching from GitHub..."
        git fetch origin
        
        # Check if we should add files
        read -p "Add existing files to repository? (y/n): " add_files
        if [[ "$add_files" == "y" ]]; then
          log "Adding files to repository..."
          git add .
          git commit -m "Initial commit of Hallway Display system"
          
          # Ask about pushing
          read -p "Push to GitHub? (y/n): " push_files
          if [[ "$push_files" == "y" ]]; then
            log "Pushing to GitHub..."
            git push -u origin main
          else
            log "Skipping push to GitHub."
          fi
        else
          log "Skipping addition of files."
          
          # Check if there's content on GitHub
          if git ls-remote --exit-code origin main &>/dev/null; then
            log "Pulling from GitHub..."
            git pull origin main
            
            # Set upstream
            git branch --set-upstream-to=origin/main main
          fi
        fi
      fi
    else
      log "No hallway_display directory found."
      log "This doesn't appear to be a Hallway Display installation."
    fi
  fi
fi

# Now perform a clean check to see if we can pull
if [ -d ".git" ]; then
  log "Checking for updates from GitHub..."
  
  # Try to get the current branch
  CURRENT_BRANCH=$(git branch --show-current)
  if [ -z "$CURRENT_BRANCH" ]; then
    # If we can't get the current branch, try to create/checkout main
    log "No current branch found. Attempting to create main branch..."
    git checkout -b main
    CURRENT_BRANCH="main"
  fi
  
  # Make sure we have an upstream
  if ! git rev-parse --abbrev-ref --symbolic-full-name @{u} &>/dev/null; then
    log "Setting upstream branch..."
    git branch --set-upstream-to=origin/main "$CURRENT_BRANCH"
  fi
  
  # Now try to pull
  log "Pulling latest changes..."
  git pull origin main
  
  # Fix permissions
  log "Setting permissions..."
  if [ -d "hallway_display" ]; then
    chmod +x hallway_display/*.sh hallway_display/tools/*.sh hallway_display/main.py hallway_display/configure.py 2>/dev/null
  else
    chmod +x *.sh tools/*.sh main.py configure.py 2>/dev/null
  fi
  
  log "Repository setup complete!"
else
  log "No Git repository found. Please run this script again from the correct directory."
fi
