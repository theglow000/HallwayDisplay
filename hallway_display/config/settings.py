"""
Configuration settings for the Hallway Display system.
"""
import os
from pathlib import Path

# Load sensitive settings from .env file if it exists
env_file = Path(__file__).parent / '.env'
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

# Display URLs - Use environment variables or defaults
DAKBOARD_URL = os.environ.get("DAKBOARD_URL", "https://dakboard.com/app/screenurl")  # Default is generic
HOME_ASSISTANT_URL = os.environ.get("HOME_ASSISTANT_URL", "http://homeassistant.local:8123")  # Default is discoverable name

# GPIO Pin Configuration
# BH1750 Light Sensor
BH1750_SDA_PIN = 2  # GPIO pin for SDA
BH1750_SCL_PIN = 11  # GPIO pin for SCL
BH1750_ADDR_PIN = 14  # GPIO pin for ADDR (if used)

# PIR Motion Sensor
PIR_VCC_PIN = 2  # GPIO pin for VCC (physical pin 2)
PIR_OUT_PIN = 17  # GPIO pin for OUT (signal) (physical pin 11)
PIR_GND_PIN = 14  # GPIO pin for GND (physical pin 14)
PIR_ENABLE_PIN = 9  # GPIO pin for enabling the sensor (if used)

# Monitor Control
MONITOR_I2C_BUS = 1  # I2C bus for ddcutil (from previous setup)
DDCUTIL_COMMAND = "sudo"  # Use 'sudo' if needed, or empty string if not
VCP_BRIGHTNESS = "10"  # VCP code for Brightness
VCP_POWER = "D6"  # VCP code for Power State
POWER_STATE_ON = "1"  # Value for power on
POWER_STATE_OFF = "4"  # Value for standby/off

# Schedule Settings
# Weekday schedule (Monday-Friday)
WEEKDAY_MORNING_ON_START = "06:00"  # 6 AM
WEEKDAY_MORNING_ON_END = "08:00"    # 8 AM
WEEKDAY_EVENING_ON_START = "17:00"  # 5 PM
WEEKDAY_EVENING_ON_END = "23:00"    # 11 PM

# Weekend schedule (Saturday-Sunday)
WEEKEND_ON_START = "08:00"  # 8 AM
WEEKEND_ON_END = "23:00"    # 11 PM

# Brightness settings
MIN_BRIGHTNESS = 10  # Minimum brightness level (0-100)
MAX_BRIGHTNESS = 90  # Maximum brightness level (0-100)
NIGHT_BRIGHTNESS = 15  # Brightness level for night mode

# Timeout settings
INACTIVITY_TIMEOUT = 30  # Seconds of inactivity before switching back to DakBoard
MOTION_TIMEOUT = 180  # Seconds of no motion before turning off display during motion-active periods

# Browser settings
BROWSER_COMMAND = "chromium-browser"  # Command to launch the browser
BROWSER_KIOSK_ARGS = ["--kiosk", "--incognito", "--noerrdialogs", "--disable-translate", 
                      "--disable-infobars", "--disable-features=TranslateUI"]
