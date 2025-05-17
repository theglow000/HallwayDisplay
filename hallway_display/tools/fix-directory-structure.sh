#!/bin/bash
# Directory structure fix script for Hallway Display
# This script helps organize the correct directory structure

# Function to log
log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "=== Hallway Display Directory Structure Fix ==="

# Determine the current directory
CURRENT_DIR=$(pwd)
log "Current directory: $CURRENT_DIR"

# Based on your terminal output, it looks like you have:
# /home/theglow000/HallwayDisplay/   <- This directory
# But possibly also:
# /home/theglow000/HallwayDisplay/HallwayDisplay/
# /home/theglow000/HallwayDisplay/hallway_display/

# Check for nested directories
if [ -d "HallwayDisplay" ]; then
  log "Found nested HallwayDisplay directory."
  if [ -d "hallway_display" ]; then
    log "Found hallway_display directory at the same level."
    log "This indicates a potentially incorrect structure."
    
    # Check what's in each directory
    log "Checking HallwayDisplay contents..."
    ls -la HallwayDisplay/ | tail -n +4 | head -n 5
    
    log "Checking hallway_display contents..."
    ls -la hallway_display/ | tail -n +4 | head -n 5
    
    read -p "Would you like to fix the directory structure? (y/n): " fix_structure
    
    if [[ "$fix_structure" == "y" ]]; then
      log "Creating backup directory..."
      mkdir -p backup_$(date +%Y%m%d)
      
      # Ask which directory has the actual code
      log "Which directory contains the actual Hallway Display code?"
      echo "1) $CURRENT_DIR/hallway_display"
      echo "2) $CURRENT_DIR/HallwayDisplay"
      read -p "Enter 1 or 2: " directory_choice
      
      if [ "$directory_choice" == "1" ]; then
        # hallway_display is the correct one
        log "Backing up HallwayDisplay..."
        cp -r HallwayDisplay backup_$(date +%Y%m%d)/
        
        log "Removing nested HallwayDisplay directory..."
        rm -rf HallwayDisplay
        
        log "hallway_display directory will be used as the main code directory"
      elif [ "$directory_choice" == "2" ]; then
        # HallwayDisplay is the correct one
        log "Backing up hallway_display..."
        cp -r hallway_display backup_$(date +%Y%m%d)/
        
        log "Removing duplicate hallway_display directory..."
        rm -rf hallway_display
        
        log "Moving contents from nested HallwayDisplay to current directory..."
        cp -r HallwayDisplay/* .
        rm -rf HallwayDisplay
        
        log "Directory structure has been fixed"
      else
        log "Invalid choice. No changes made."
      fi
    else
      log "No changes made to directory structure."
    fi
  else
    log "Only found nested HallwayDisplay directory."
    read -p "Move contents up one level? (y/n): " move_contents
    
    if [[ "$move_contents" == "y" ]]; then
      log "Backing up before changes..."
      mkdir -p backup_$(date +%Y%m%d)
      cp -r HallwayDisplay backup_$(date +%Y%m%d)/
      
      log "Moving contents from nested HallwayDisplay to current directory..."
      cp -r HallwayDisplay/* .
      rm -rf HallwayDisplay
      
      log "Directory structure has been fixed"
    else
      log "No changes made to directory structure."
    fi
  fi
elif [ -d "hallway_display" ]; then
  log "Found hallway_display directory at the expected location."
  log "Directory structure appears correct."
else
  log "Neither HallwayDisplay nor hallway_display directory found."
  log "Are you in the correct directory?"
fi

# Check for git repository
if [ -d ".git" ]; then
  log "Git repository found in current directory."
else
  log "No Git repository in current directory."
  if [ -d "hallway_display/.git" ]; then
    log "Git repository found in hallway_display subdirectory."
    read -p "Move Git repository to current directory? (y/n): " move_git
    
    if [[ "$move_git" == "y" ]]; then
      log "Moving Git repository..."
      mv hallway_display/.git .
      log "Git repository moved to current directory."
    fi
  else
    log "No Git repository found in subdirectories."
    log "You may need to initialize a Git repository using the git-setup.sh script."
  fi
fi

log "Directory structure check complete."
