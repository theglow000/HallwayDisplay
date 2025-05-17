#!/bin/bash
# Monitor Recovery Script
# This script attempts to recover a monitor that is powered on but showing a black screen

echo "=== Monitor Recovery Script ==="
date
echo "User: $(whoami)"

# Function to log messages with timestamps
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Set display environment variables
if [ -z "$DISPLAY" ]; then
    export DISPLAY=:0
    log_message "Setting DISPLAY=$DISPLAY"
fi

if [ -z "$XAUTHORITY" ]; then
    export XAUTHORITY=~/.Xauthority
    log_message "Setting XAUTHORITY=$XAUTHORITY"
fi

# Verify X server access
log_message "Verifying X server access..."
if ! xset q &>/dev/null; then
    log_message "❌ X server not accessible. Trying to fix..."
    xhost +local: &>/dev/null
    if ! xset q &>/dev/null; then
        log_message "❌ X server still not accessible. Please fix your X server configuration."
        exit 1
    fi
fi
log_message "✅ X server is accessible"

# Function to attempt monitor recovery
recover_monitor() {
    log_message "Starting monitor recovery sequence..."
    
    # 1. Try DPMS cycling (force monitor off then on)
    log_message "Step 1: Cycling DPMS power states..."
    log_message "  Forcing monitor off..."
    xset dpms force off
    sleep 3
    log_message "  Forcing monitor on..."
    xset dpms force on
    sleep 2
    
    # 2. Check HDMI status on Raspberry Pi
    log_message "Step 2: Checking HDMI status..."
    if command -v tvservice &> /dev/null; then
        log_message "  Current HDMI status:"
        tvservice -s
        
        log_message "  Detailed display information:"
        tvservice -d edid.dat
        edidparser edid.dat
        rm -f edid.dat
        
        # Try power cycling the HDMI
        log_message "  Power cycling HDMI output..."
        tvservice -o
        sleep 2
        tvservice -p
        sleep 1
        
        # Force a specific resolution
        log_message "  Forcing HDMI to 1080p60 mode..."
        tvservice -e "CEA 16"
        sleep 1
        
        # Reset the framebuffer
        log_message "  Resetting framebuffer..."
        fbset -depth 8
        fbset -depth 16
        sleep 1
    else
        log_message "  tvservice command not found (not a Raspberry Pi?)"
    fi
    
    # 3. Try X11 display reconfiguration
    log_message "Step 3: Reconfiguring X11 displays..."
    log_message "  Current display configuration:"
    xrandr
    
    log_message "  Attempting to reset all displays..."
    xrandr --auto
    sleep 2
    
    # 4. Try CEC commands if available
    log_message "Step 4: Trying CEC control if available..."
    if command -v cec-client &> /dev/null; then
        log_message "  CEC control available, trying to wake display..."
        echo "on 0" | cec-client -s -d 1
        sleep 3
    else
        log_message "  cec-client not found, skipping CEC control"
    fi
    
    # 5. Check GPU/video driver status
    log_message "Step 5: Checking video driver status..."
    if command -v vcgencmd &> /dev/null; then
        log_message "  GPU memory allocation:"
        vcgencmd get_mem gpu
        log_message "  Video core status:"
        vcgencmd measure_temp
        vcgencmd measure_volts
    else
        log_message "  vcgencmd not found (not a Raspberry Pi?)"
    fi
    
    log_message "Monitor recovery sequence completed"
    log_message "If your monitor is still black, try the following:"
    log_message "1. Check physical connections (power, HDMI)"
    log_message "2. Try a different HDMI cable or port"
    log_message "3. Check if monitor works with another device"
    log_message "4. Edit /boot/config.txt to add specific HDMI settings:"
    log_message "   hdmi_force_hotplug=1"
    log_message "   hdmi_drive=2"
    log_message "   hdmi_group=1"
    log_message "   hdmi_mode=16 # (for 1080p60)"
}

# Run recovery procedure
recover_monitor

# Create a Python script to test monitor state detection
log_message "Creating monitor test utility..."
cd "$(dirname "$0")/.."
PROJECT_DIR="$(pwd)"

cat > "$PROJECT_DIR/tools/detect_monitor_state.py" << 'EOF'
#!/usr/bin/env python3
"""
Monitor State Detection Tool.

This script attempts to detect the actual state of the monitor 
and provides detailed diagnostics.
"""

import os
import sys
import subprocess
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from modules.enhanced_monitor import EnhancedMonitorController
except ImportError:
    print("Enhanced monitor controller not found, using standard controller")
    from modules.monitor import MonitorController as EnhancedMonitorController

def log(message):
    """Log a message with timestamp."""
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}")

def run_command(command, shell=False):
    """Run a shell command and return the output."""
    try:
        result = subprocess.run(
            command,
            shell=shell,
            capture_output=True,
            text=True,
            check=False,
            timeout=10
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except Exception as e:
        return "", str(e), -1

def detect_monitor_state():
    """Detect the actual state of the monitor and provide diagnostics."""
    log("Starting monitor state detection")
    
    # Check X11 display information
    log("Checking X11 display information...")
    stdout, stderr, _ = run_command(["xrandr"])
    if stdout:
        connected_displays = [line for line in stdout.split('\n') if " connected " in line]
        log(f"Connected displays: {len(connected_displays)}")
        for display in connected_displays:
            log(f"  {display}")
    else:
        log("❌ Could not get X11 display information")
        if stderr:
            log(f"Error: {stderr}")
    
    # Check if we have a Raspberry Pi
    is_raspberry_pi = os.path.exists("/usr/bin/tvservice")
    log(f"Running on Raspberry Pi: {is_raspberry_pi}")
    
    # Get HDMI status on Raspberry Pi
    if is_raspberry_pi:
        log("Checking HDMI status...")
        stdout, stderr, _ = run_command(["tvservice", "-s"])
        if stdout:
            log(f"HDMI status: {stdout}")
        else:
            log("❌ Could not get HDMI status")
            if stderr:
                log(f"Error: {stderr}")
    
    # Try to use EnhancedMonitorController
    log("Checking monitor controller...")
    try:
        monitor = EnhancedMonitorController()
        
        log(f"Preferred control method: {monitor.preferred_method}")
        log(f"Using alternative methods only: {monitor.alternative_methods_only}")
        
        # Get current power state
        power_state = monitor.get_power_state()
        log(f"Reported power state: {power_state}")
        
        # Get current brightness
        brightness = monitor.get_brightness()
        log(f"Reported brightness: {brightness}")
        
    except Exception as e:
        log(f"❌ Error initializing monitor controller: {e}")
        import traceback
        traceback.print_exc()
    
    # Check EDID information
    if is_raspberry_pi:
        log("Checking EDID information...")
        run_command(["tvservice", "-d", "/tmp/edid.dat"])
        stdout, stderr, _ = run_command(["edidparser", "/tmp/edid.dat"])
        if stdout:
            # Extract the most important parts
            edid_summary = []
            for line in stdout.split('\n'):
                if any(key in line for key in ["Manufacturer", "Product", "Monitor name", "Native details"]):
                    edid_summary.append(line.strip())
            
            log("EDID information:")
            for line in edid_summary:
                log(f"  {line}")
        else:
            log("❌ Could not read EDID information")
            if stderr:
                log(f"Error: {stderr}")
    
    # Check DPMS status
    log("Checking DPMS status...")
    stdout, stderr, _ = run_command(["xset", "-q"])
    if stdout:
        dpms_lines = []
        capture = False
        for line in stdout.split('\n'):
            if "DPMS" in line:
                capture = True
            if capture and line.strip():
                dpms_lines.append(line.strip())
            if capture and not line.strip():
                capture = False
        
        log("DPMS information:")
        for line in dpms_lines:
            log(f"  {line}")
    else:
        log("❌ Could not get DPMS status")
        if stderr:
            log(f"Error: {stderr}")
    
    # Try to detect display driver issues
    log("Checking display drivers...")
    stdout, stderr, _ = run_command(["lsmod | grep -E 'drm|gpu|nvidia|fglrx|radeon|nouveau'"], shell=True)
    if stdout:
        log("Display-related kernel modules:")
        for line in stdout.split('\n')[:5]:  # Show only first 5 lines
            log(f"  {line}")
    else:
        log("❌ Could not detect display kernel modules")
    
    log("Monitor state detection complete")

if __name__ == "__main__":
    print("=== Monitor State Detection ===")
    try:
        detect_monitor_state()
    except Exception as e:
        print(f"Error during monitor state detection: {e}")
        import traceback
        traceback.print_exc()
    print("=== Detection Complete ===")
EOF

chmod +x "$PROJECT_DIR/tools/detect_monitor_state.py"
log_message "✅ Created monitor state detection tool"

# Create config.txt backup and recommendations
log_message "Creating Raspberry Pi config.txt recommendations..."

cat > "$PROJECT_DIR/tools/fix-hdmi-config.sh" << 'EOF'
#!/bin/bash
# HDMI configuration fix for Raspberry Pi
# This script modifies the config.txt file to fix HDMI issues

echo "=== HDMI Configuration Fix ==="
date
echo "User: $(whoami)"

# Check if we're running on a Raspberry Pi
if [ ! -f /boot/config.txt ] && [ ! -f /boot/firmware/config.txt ]; then
    echo "❌ This doesn't appear to be a Raspberry Pi, or config.txt is not in the expected location."
    exit 1
fi

# Determine config.txt location
CONFIG_PATH="/boot/config.txt"
if [ ! -f "$CONFIG_PATH" ]; then
    CONFIG_PATH="/boot/firmware/config.txt"
fi

echo "Using config file: $CONFIG_PATH"

# Backup the original config
BACKUP_PATH="${CONFIG_PATH}.bak"
echo "Creating backup at $BACKUP_PATH"
sudo cp "$CONFIG_PATH" "$BACKUP_PATH"

# Check for existing HDMI settings
echo "Checking for existing HDMI settings..."
NEEDS_FORCE_HOTPLUG=$(grep -q "hdmi_force_hotplug=1" "$CONFIG_PATH" || echo "true")
NEEDS_DRIVE=$(grep -q "hdmi_drive=2" "$CONFIG_PATH" || echo "true")
NEEDS_GROUP=$(grep -q "hdmi_group=" "$CONFIG_PATH" || echo "true")
NEEDS_MODE=$(grep -q "hdmi_mode=" "$CONFIG_PATH" || echo "true")

# Add missing HDMI settings
echo "Adding missing HDMI settings..."

TEMP_CONFIG=$(mktemp)
cat "$CONFIG_PATH" > "$TEMP_CONFIG"

# Add a section separator if needed
echo "" >> "$TEMP_CONFIG"
echo "# HDMI Fix for Black Screen Issues" >> "$TEMP_CONFIG"

if [ "$NEEDS_FORCE_HOTPLUG" = "true" ]; then
    echo "hdmi_force_hotplug=1" >> "$TEMP_CONFIG"
    echo "Added hdmi_force_hotplug=1"
fi

if [ "$NEEDS_DRIVE" = "true" ]; then
    echo "hdmi_drive=2" >> "$TEMP_CONFIG"
    echo "Added hdmi_drive=2"
fi

if [ "$NEEDS_GROUP" = "true" ]; then
    echo "hdmi_group=1" >> "$TEMP_CONFIG"
    echo "Added hdmi_group=1 (CEA)"
fi

if [ "$NEEDS_MODE" = "true" ]; then
    echo "hdmi_mode=16" >> "$TEMP_CONFIG"
    echo "Added hdmi_mode=16 (1080p60)"
fi

# Uncomment and add overscan settings
if ! grep -q "^disable_overscan=" "$CONFIG_PATH"; then
    echo "disable_overscan=1" >> "$TEMP_CONFIG"
    echo "Added disable_overscan=1"
fi

# Write back to config.txt
sudo cp "$TEMP_CONFIG" "$CONFIG_PATH"
rm "$TEMP_CONFIG"

echo "✅ HDMI settings updated successfully"
echo "A backup was created at $BACKUP_PATH"
echo "You need to REBOOT for these changes to take effect"
echo ""
echo "If your monitor still shows a black screen after reboot, try:"
echo "1. Connect a different monitor or TV to verify the output"
echo "2. Try using a different HDMI cable"
echo "3. Try different hdmi_mode values by editing $CONFIG_PATH"
echo "   - For TVs: hdmi_group=1, hdmi_mode=4 (720p) or hdmi_mode=16 (1080p)"
echo "   - For Monitors: hdmi_group=2, hdmi_mode=16 (1024x768) or hdmi_mode=35 (1280x1024)"
EOF

chmod +x "$PROJECT_DIR/tools/fix-hdmi-config.sh"
log_message "✅ Created HDMI configuration fix script"

log_message "=== Monitor Recovery Process Complete ==="
log_message "To recover from a black screen, run:"
log_message "  $PROJECT_DIR/tools/monitor-recovery.sh"
log_message "To diagnose monitor state, run:"
log_message "  $PROJECT_DIR/tools/detect_monitor_state.py"
log_message "To fix HDMI configuration (Raspberry Pi only), run:"
log_message "  $PROJECT_DIR/tools/fix-hdmi-config.sh"
log_message ""
log_message "If your monitor is physically powered on but showing a black screen:"
log_message "1. First run the recovery script to try automatic fixes"
log_message "2. Then run the detection tool to diagnose the problem"
log_message "3. Finally, if running on a Raspberry Pi, try the HDMI config fix"
log_message "4. After making changes, REBOOT your system"
