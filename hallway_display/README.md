# Hallway Display System

A modular system for managing a Raspberry Pi-based hallway display that shows DakBoard and Home Assistant interfaces.

## Features

- **Time-based Scheduling**: Automatically turns the monitor on/off based on configured times.
- **Motion Detection**: Wakes the monitor when motion is detected during off periods.
- **Ambient Light Sensing**: Adjusts monitor brightness based on room light levels.
- **Touch Interface**: Switches between DakBoard and Home Assistant on touch.
- **Modular Design**: Each component is separate for easier debugging and maintenance.

## Requirements

### Hardware
- Raspberry Pi 4
- 21.5" Touchscreen Monitor
- HC-SR501 PIR Motion Sensor
- BH1750 Light Sensor

### Software
- Raspberry Pi OS
- Python 3.7+
- ddcutil (for monitor control)
- Chromium browser
- evdev (for touch detection)
- xdotool (for window management)

## Installation

1. **Install required system packages**:
   ```bash
   sudo apt update
   sudo apt install -y python3-pip python3-venv python3-evdev python3-rpi.gpio python3-smbus python3-psutil ddcutil xdotool chromium-browser
   ```

2. **Create a virtual environment (if any packages are missing from apt)**:
   ```bash
   python3 -m venv hallway_venv
   source hallway_venv/bin/activate
   pip install evdev RPi.GPIO smbus psutil
   deactivate
   ```

2. **Setup ddcutil permissions**:
   ```bash
   sudo usermod -a -G i2c $USER
   ```
   (Logout and login again for this to take effect)

3. **Configure the system**:
   Edit `config/settings.py` to set your preferences, including:
   - DakBoard URL
   - Home Assistant URL
   - Schedule times
   - Brightness settings

## Usage

1. **Configure the system**:
   There are two ways to configure the system:
   
   a. **GUI Configuration Tool** (Recommended):
   ```bash
   python3 configure.py
   ```
   This will open a graphical interface where you can easily adjust settings such as:
   - DakBoard and Home Assistant URLs
   - Schedule times
   - GPIO pin assignments
   - Brightness levels
   - Timeout durations
   
   b. **Manual Configuration**:
   Edit `config/settings.py` directly with a text editor.

2. **Start the system**:
   ```bash
   ./start.sh
   ```

3. **Run at startup (using systemd)**:
   The system is configured to run automatically at startup using a systemd service unit.

   Create the service file: Create a file named hallway-display.service in /etc/systemd/system/ with the following content (adjust paths if necessary):
   Ini, TOML

   [Unit]
   Description=Hallway Display System
   After=graphical.target network-online.target
   Requires=network-online.target

   [Service]
   User=theglow000  # Replace with your actual username
   WorkingDirectory=/home/theglow000/HallwayDisplay/hallway_display
   ExecStart=/home/theglow000/HallwayDisplay/hallway_display/start.sh
   Restart=on-failure
   StandardOutput=append:/var/log/hallway-display.log
   StandardError=append:/var/log/hallway-display.log

   [Install]
   WantedBy=graphical.target
   
   Enable the service:
   ```bash
   sudo systemctl enable hallway-display.service
   ```

   Start the service:
   ```bash
   sudo systemctl start hallway-display.service
   ```

   Reboot to run at startup:
   ```bash
   sudo reboot
   ```

## Project Structure

- `config/` - Configuration settings
- `modules/` - System components
  - `sensor.py` - Handles motion and light sensors
  - `monitor.py` - Controls monitor power and brightness
  - `display.py` - Manages DakBoard and Home Assistant display
  - `scheduler.py` - Handles time-based scheduling
- `utils/` - Utility functions
- `main.py` - Main controller
- `start.sh` - Startup script

## Customization

### Configuration GUI

The system includes a convenient GUI for changing settings without editing files directly. 
There are two ways to access it:

1. **From the touchscreen display**: A small gear icon (⚙️) appears in the bottom-right corner of the screen. 
   Click this icon to open the configuration interface.

2. **Manually from the command line**:
   ```bash
   ./configure.sh
   ```

The configuration GUI provides tabs for:
- **General**: URLs, timeout settings
- **Schedule**: Weekday and weekend on/off times
- **GPIO Pins**: Sensor pin assignments
- **Brightness**: Minimum, maximum, and night brightness levels

### Manual Configuration

If you prefer to edit files directly:

- **Schedule Times**: Edit `config/settings.py` to adjust the times when the monitor should be on/off.
- **Brightness Levels**: Modify `MIN_BRIGHTNESS`, `MAX_BRIGHTNESS`, and `NIGHT_BRIGHTNESS` settings.
- **URLs**: Update `DAKBOARD_URL` and `HOME_ASSISTANT_URL` settings.

## GitHub Integration

Using GitHub for version control makes it easy to develop on one machine and deploy to your Raspberry Pi.

### Initial Setup

1. **Create a GitHub repository**:
   - Go to [GitHub](https://github.com) and create a new repository
   - Name it "HallwayDisplay" and set visibility to "Public"

2. **Push your local code to GitHub** (from development machine):
   ```bash
   cd c:\Users\thegl\Desktop\HallwayDisplay
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/theglow000/HallwayDisplay.git
   git push -u origin main
   ```

### Deploying to Raspberry Pi

1. **First-time setup**:
   ```bash
   # Install Git if needed
   sudo apt update
   sudo apt install git
   
   # Clone your repository
   cd /home/theglow000
   git clone https://github.com/theglow000/HallwayDisplay.git
   
   # Set proper permissions
   chmod +x /home/theglow000/HallwayDisplay/hallway_display/start.sh
   chmod +x /home/theglow000/HallwayDisplay/hallway_display/main.py
   ```

2. **Updating existing installation**:
   ```bash
   # Pull latest changes
   cd /home/theglow000/HallwayDisplay
   git pull
   
   # Ensure scripts are executable
   chmod +x hallway_display/start.sh hallway_display/main.py
   
   # Restart the service if running
   sudo systemctl restart hallway-display.service
   ```

### Development Workflow

1. **Make changes** on your development machine
2. **Commit and push** to GitHub:
   ```bash
   git add .
   git commit -m "Description of changes"
   git push
   ```
3. **Pull changes** on your Raspberry Pi:
   ```bash
   cd /home/theglow000/HallwayDisplay
   git pull
   ```

### Troubleshooting Git Issues

- **Local changes conflict**: If you've made changes directly on the Pi that conflict:
  ```bash
  # Discard local changes and force-sync with GitHub
  git fetch
  git reset --hard origin/main
  ```

- **Permission issues after update**: Reset permissions if needed:
  ```bash
  chmod -R +x /home/theglow000/HallwayDisplay/hallway_display/*.sh
  chmod +x /home/theglow000/HallwayDisplay/hallway_display/main.py
  ```

## Troubleshooting

### Logs
Logs are stored in the `logs/` directory with a filename based on the current date.

### Diagnostic Tools
The system includes diagnostic tools to help identify and resolve common issues:

1. **Display Environment Diagnostics**:
   ```bash
   chmod +x display_diagnostics.sh
   ./display_diagnostics.sh
   ```
   This script checks for common display, X server, and permission issues and provides guidance on how to fix them.

2. **Enhanced Startup Script**:
   If you're experiencing issues with the regular start script, try the enhanced version:
   ```bash
   chmod +x start_enhanced.sh
   ./start_enhanced.sh
   ```
   This script includes improved error handling and permission management.

### Common Issues

#### X Server Display Issues
- **Error**: "Can't open display: (null)" or "No display name and no DISPLAY environment variable"
  - **Solution 1**: Make sure you're running from a desktop session (not SSH without X forwarding)
  - **Solution 2**: Try running with proper display environment variables:
    ```bash
    DISPLAY=:0 XAUTHORITY=/home/theglow000/.Xauthority ./start.sh
    ```
  - **Solution 3**: For root/sudo access to X server:
    ```bash
    # First, from the regular user session:
    xhost +local:root
    # Then run with sudo:
    sudo -E ./start.sh
    ```

#### GPIO and Sensor Issues
- **Error**: "Failed to add edge detection" or other GPIO permission issues
  - **Solution 1**: Add your user to the required groups:
    ```bash
    sudo usermod -a -G gpio,i2c,video $USER
    # Log out and back in for changes to take effect
    ```
  - **Solution 2**: Use the polling fallback (implemented in the latest code)
  - **Solution 3**: Run with sudo:
    ```bash
    sudo -E ./start_enhanced.sh
    ```

#### Monitor Control Issues
- **Error**: "Monitor not responding to power commands" or "Monitor brightness control not working"
  - **Solution 1**: Verify I2C bus and ddcutil accessibility:
    ```bash
    # Check if monitor is detectable
    ddcutil detect
    # Check specific I2C bus
    ddcutil --bus=1 detect
    ```
  - **Solution 2**: Try different display control methods:
    ```bash
    # DPMS method
    xset dpms force on  # Turn on
    xset dpms force off  # Turn off
    
    # For Raspberry Pi specific
    tvservice --preferred  # Turn on
    tvservice --off  # Turn off
    ```
  - **Solution 3**: Verify monitor supports DDC/CI (many monitors have this disabled by default in their OSD menu)

#### Light Sensor Issues
- **Error**: "Failed to read from BH1750 sensor" or timeouts
  - **Solution 1**: Check I2C connections and pull-up resistors:
    ```bash
    # Scan I2C bus for devices
    i2cdetect -y 1
    ```
  - **Solution 2**: Try both common BH1750 addresses (0x23 and 0x5C) - implemented in latest code
  - **Solution 3**: Verify your user has access to I2C devices:
    ```bash
    sudo usermod -a -G i2c $USER
    # Log out and back in for changes to take effect
    ```

#### Getting Updates from GitHub
- **Error**: "Authentication failed" when pulling from GitHub
  - **Solution 1**: Use HTTPS URL with a personal access token:
    ```bash
    git remote set-url origin https://your-username:your-token@github.com/theglow000/HallwayDisplay.git
    ```
  - **Solution 2**: For public repositories, use the public HTTPS URL:
    ```bash
    git remote set-url origin https://github.com/theglow000/HallwayDisplay.git
    git pull
    ```

## License

[MIT License](LICENSE)
