#!/bin/bash
# Startup script for the Hallway Display system

# Set display environment variables
export DISPLAY=:0
export XAUTHORITY=/home/theglow000/.Xauthority

# Navigate to the script directory
cd "$(dirname "$0")"

# Create the logs directory if it doesn't exist
mkdir -p logs

# Make sure main.py is executable
chmod +x main.py

# Check if we're running as root - some features may require root
if [ "$EUID" -ne 0 ]; then
  echo "Note: Running without root privileges. Some features like GPIO access and monitor control may not work."
  echo "If you encounter permission issues, try running with sudo."
  
  # Check for GPIO group membership
  if ! groups | grep -q "gpio"; then
    echo "Warning: Current user is not part of 'gpio' group which may cause permission issues."
    echo "Consider running: sudo usermod -a -G gpio,i2c,video $USER"
    echo "Then log out and back in for changes to take effect."
  fi
  echo ""
fi

# Check for X server
if ! xset q &>/dev/null; then
  echo "Warning: X server not available or not accessible."
  echo "Make sure you're running this from a desktop session or the DISPLAY variable is set correctly."
  echo ""
fi

# Check for required dependencies
echo "Checking dependencies..."
missing_deps=0

# Check for Python
if ! command -v python3 &> /dev/null; then
  echo "Error: Python 3 is not installed or not in PATH"
  missing_deps=1
fi

# Check for ddcutil
if ! command -v ddcutil &> /dev/null; then
  echo "Error: ddcutil is not installed or not in PATH"
  missing_deps=1
fi

# Check for xdotool
if ! command -v xdotool &> /dev/null; then
  echo "Error: xdotool is not installed or not in PATH"
  missing_deps=1
fi

# Check for chromium-browser
if ! command -v chromium-browser &> /dev/null; then
  echo "Error: chromium-browser is not installed or not in PATH"
  missing_deps=1
fi

# Check if virtual environment exists and use it if it does
if [ -d "hallway_venv" ]; then
  echo "Virtual environment found, activating..."
  source hallway_venv/bin/activate
  PYTHON_CMD="hallway_venv/bin/python3"
else
  PYTHON_CMD="python3"
fi

# Check for critical Python modules
$PYTHON_CMD -c "import evdev" 2>/dev/null || { echo "Error: evdev Python module not installed"; missing_deps=1; }
$PYTHON_CMD -c "import RPi.GPIO" 2>/dev/null || { echo "Error: RPi.GPIO Python module not installed"; missing_deps=1; }
$PYTHON_CMD -c "import psutil" 2>/dev/null || { echo "Error: psutil Python module not installed"; missing_deps=1; }

if [ $missing_deps -eq 1 ]; then
  echo ""
  echo "Please install missing dependencies. See README.md for installation instructions."
  exit 1
fi

echo "All dependencies found."
echo ""

# Check if the DAkBoard and Home Assistant URLs are set
python3 -c "from config import settings; exit(0 if settings.DAKBOARD_URL != 'https://dakboard.com/app/screenurl' and settings.HOME_ASSISTANT_URL != 'http://homeassistant.local:8123' else 1)" 2>/dev/null
if [ $? -ne 0 ]; then
  echo "Warning: Default URLs detected in config/settings.py"
  echo "Please update the DAKBOARD_URL and HOME_ASSISTANT_URL settings before running."
  echo ""
fi

# Start the Hallway Display system
echo "Starting Hallway Display system..."
echo "Press Ctrl+C to stop."
echo ""

# Run the main script - append output to log file
echo "Using Python command: $PYTHON_CMD"
$PYTHON_CMD main.py 2>&1 | tee -a "logs/console-$(date +'%Y-%m-%d').log"

# Deactivate virtual environment if it was activated
if [ -d "hallway_venv" ]; then
  deactivate
fi

exit $?
