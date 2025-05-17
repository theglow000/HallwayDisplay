#!/usr/bin/env python3
"""
Configuration GUI for the Hallway Display system.

This utility provides a graphical interface to update the configuration 
settings for the Hallway Display system, including URLs, schedule times,
and GPIO pin assignments.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import importlib.util
import re
from pathlib import Path

class ConfigEditor:
    """GUI for editing the Hallway Display configuration."""
    
    def __init__(self, root):
        """Initialize the configuration editor.
        
        Args:
            root: The Tkinter root window.
        """
        self.root = root
        self.root.title("Hallway Display Configuration")
        self.root.geometry("800x600")
        self.root.minsize(600, 500)
        
        # Set up the main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create tabs
        self.create_general_tab()
        self.create_schedule_tab()
        self.create_gpio_tab()
        self.create_brightness_tab()
        
        # Add buttons at the bottom
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=10)
        
        ttk.Button(button_frame, text="Save Configuration", command=self.save_configuration).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Reload", command=self.load_configuration).pack(side=tk.RIGHT, padx=5)
        
        # Load current configuration
        self.load_configuration()
    
    def create_general_tab(self):
        """Create the General tab with URL settings."""
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="General")
        
        # URL settings
        ttk.Label(tab, text="URLs", font=("", 12, "bold")).grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(tab, text="DakBoard URL:").grid(row=1, column=0, sticky=tk.W)
        self.dakboard_url = ttk.Entry(tab, width=50)
        self.dakboard_url.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(tab, text="Home Assistant URL:").grid(row=2, column=0, sticky=tk.W)
        self.homeassistant_url = ttk.Entry(tab, width=50)
        self.homeassistant_url.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Timeout settings
        ttk.Label(tab, text="Timeouts", font=("", 12, "bold")).grid(row=3, column=0, sticky=tk.W, pady=(20, 10))
        
        ttk.Label(tab, text="Inactivity Timeout (seconds):").grid(row=4, column=0, sticky=tk.W)
        self.inactivity_timeout = ttk.Spinbox(tab, from_=5, to=300, increment=5, width=10)
        self.inactivity_timeout.grid(row=4, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(tab, text="Motion Timeout (seconds):").grid(row=5, column=0, sticky=tk.W)
        self.motion_timeout = ttk.Spinbox(tab, from_=10, to=600, increment=10, width=10)
        self.motion_timeout.grid(row=5, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Browser settings
        ttk.Label(tab, text="Browser", font=("", 12, "bold")).grid(row=6, column=0, sticky=tk.W, pady=(20, 10))
        
        ttk.Label(tab, text="Browser Command:").grid(row=7, column=0, sticky=tk.W)
        self.browser_command = ttk.Entry(tab, width=30)
        self.browser_command.grid(row=7, column=1, sticky=tk.W, padx=5, pady=5)
    
    def create_schedule_tab(self):
        """Create the Schedule tab with time settings."""
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="Schedule")
        
        # Weekday schedule
        ttk.Label(tab, text="Weekday Schedule (Monday-Friday)", font=("", 12, "bold")).grid(row=0, column=0, columnspan=4, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(tab, text="Morning ON:").grid(row=1, column=0, sticky=tk.W)
        self.weekday_morning_on_start = ttk.Entry(tab, width=10)
        self.weekday_morning_on_start.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(tab, text="to").grid(row=1, column=2, sticky=tk.W)
        self.weekday_morning_on_end = ttk.Entry(tab, width=10)
        self.weekday_morning_on_end.grid(row=1, column=3, sticky=tk.W, padx=5, pady=5)
        ttk.Label(tab, text="Format: HH:MM (24-hour)").grid(row=1, column=4, sticky=tk.W, padx=5)
        
        ttk.Label(tab, text="Evening ON:").grid(row=2, column=0, sticky=tk.W)
        self.weekday_evening_on_start = ttk.Entry(tab, width=10)
        self.weekday_evening_on_start.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(tab, text="to").grid(row=2, column=2, sticky=tk.W)
        self.weekday_evening_on_end = ttk.Entry(tab, width=10)
        self.weekday_evening_on_end.grid(row=2, column=3, sticky=tk.W, padx=5, pady=5)
        ttk.Label(tab, text="Format: HH:MM (24-hour)").grid(row=2, column=4, sticky=tk.W, padx=5)
        
        # Weekend schedule
        ttk.Label(tab, text="Weekend Schedule (Saturday-Sunday)", font=("", 12, "bold")).grid(row=3, column=0, columnspan=4, sticky=tk.W, pady=(20, 10))
        
        ttk.Label(tab, text="ON:").grid(row=4, column=0, sticky=tk.W)
        self.weekend_on_start = ttk.Entry(tab, width=10)
        self.weekend_on_start.grid(row=4, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(tab, text="to").grid(row=4, column=2, sticky=tk.W)
        self.weekend_on_end = ttk.Entry(tab, width=10)
        self.weekend_on_end.grid(row=4, column=3, sticky=tk.W, padx=5, pady=5)
        ttk.Label(tab, text="Format: HH:MM (24-hour)").grid(row=4, column=4, sticky=tk.W, padx=5)
    
    def create_gpio_tab(self):
        """Create the GPIO tab with pin assignments."""
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="GPIO Pins")
        
        # BH1750 Light Sensor
        ttk.Label(tab, text="BH1750 Light Sensor", font=("", 12, "bold")).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(tab, text="SDA Pin:").grid(row=1, column=0, sticky=tk.W)
        self.bh1750_sda_pin = ttk.Spinbox(tab, from_=0, to=40, width=5)
        self.bh1750_sda_pin.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(tab, text="SCL Pin:").grid(row=2, column=0, sticky=tk.W)
        self.bh1750_scl_pin = ttk.Spinbox(tab, from_=0, to=40, width=5)
        self.bh1750_scl_pin.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(tab, text="ADDR Pin:").grid(row=3, column=0, sticky=tk.W)
        self.bh1750_addr_pin = ttk.Spinbox(tab, from_=0, to=40, width=5)
        self.bh1750_addr_pin.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
        
        # PIR Motion Sensor
        ttk.Label(tab, text="PIR Motion Sensor", font=("", 12, "bold")).grid(row=0, column=2, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(tab, text="VCC Pin:").grid(row=1, column=2, sticky=tk.W)
        self.pir_vcc_pin = ttk.Spinbox(tab, from_=0, to=40, width=5)
        self.pir_vcc_pin.grid(row=1, column=3, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(tab, text="OUT Pin:").grid(row=2, column=2, sticky=tk.W)
        self.pir_out_pin = ttk.Spinbox(tab, from_=0, to=40, width=5)
        self.pir_out_pin.grid(row=2, column=3, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(tab, text="GND Pin:").grid(row=3, column=2, sticky=tk.W)
        self.pir_gnd_pin = ttk.Spinbox(tab, from_=0, to=40, width=5)
        self.pir_gnd_pin.grid(row=3, column=3, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(tab, text="Enable Pin:").grid(row=4, column=2, sticky=tk.W)
        self.pir_enable_pin = ttk.Spinbox(tab, from_=0, to=40, width=5)
        self.pir_enable_pin.grid(row=4, column=3, sticky=tk.W, padx=5, pady=5)
        
        # Monitor Control
        ttk.Label(tab, text="Monitor Control", font=("", 12, "bold")).grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=(20, 10))
        
        ttk.Label(tab, text="I2C Bus:").grid(row=6, column=0, sticky=tk.W)
        self.monitor_i2c_bus = ttk.Spinbox(tab, from_=0, to=40, width=5)
        self.monitor_i2c_bus.grid(row=6, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(tab, text="Power VCP Code:").grid(row=7, column=0, sticky=tk.W)
        self.vcp_power = ttk.Entry(tab, width=5)
        self.vcp_power.grid(row=7, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(tab, text="Brightness VCP Code:").grid(row=8, column=0, sticky=tk.W)
        self.vcp_brightness = ttk.Entry(tab, width=5)
        self.vcp_brightness.grid(row=8, column=1, sticky=tk.W, padx=5, pady=5)
    
    def create_brightness_tab(self):
        """Create the Brightness tab with brightness settings."""
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="Brightness")
        
        # Brightness settings
        ttk.Label(tab, text="Brightness Levels", font=("", 12, "bold")).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(tab, text="Minimum Brightness (0-100):").grid(row=1, column=0, sticky=tk.W)
        self.min_brightness = ttk.Scale(tab, from_=0, to=100, orient=tk.HORIZONTAL, length=200)
        self.min_brightness.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        self.min_brightness_value = ttk.Label(tab, text="0")
        self.min_brightness_value.grid(row=1, column=2, sticky=tk.W)
        self.min_brightness.bind("<Motion>", lambda e: self.min_brightness_value.configure(text=str(int(self.min_brightness.get()))))
        
        ttk.Label(tab, text="Maximum Brightness (0-100):").grid(row=2, column=0, sticky=tk.W)
        self.max_brightness = ttk.Scale(tab, from_=0, to=100, orient=tk.HORIZONTAL, length=200)
        self.max_brightness.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        self.max_brightness_value = ttk.Label(tab, text="0")
        self.max_brightness_value.grid(row=2, column=2, sticky=tk.W)
        self.max_brightness.bind("<Motion>", lambda e: self.max_brightness_value.configure(text=str(int(self.max_brightness.get()))))
        
        ttk.Label(tab, text="Night Brightness (0-100):").grid(row=3, column=0, sticky=tk.W)
        self.night_brightness = ttk.Scale(tab, from_=0, to=100, orient=tk.HORIZONTAL, length=200)
        self.night_brightness.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
        self.night_brightness_value = ttk.Label(tab, text="0")
        self.night_brightness_value.grid(row=3, column=2, sticky=tk.W)
        self.night_brightness.bind("<Motion>", lambda e: self.night_brightness_value.configure(text=str(int(self.night_brightness.get()))))
    
    def load_configuration(self):
        """Load the current configuration from settings.py."""
        try:
            # Get the absolute path to the settings.py file
            script_dir = os.path.dirname(os.path.abspath(__file__))
            settings_path = os.path.join(script_dir, "config", "settings.py")
            
            # Import the settings module
            spec = importlib.util.spec_from_file_location("settings", settings_path)
            settings = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(settings)
            
            # General settings
            self.dakboard_url.delete(0, tk.END)
            self.dakboard_url.insert(0, getattr(settings, "DAKBOARD_URL", "https://dakboard.com/app/screenurl"))
            
            self.homeassistant_url.delete(0, tk.END)
            self.homeassistant_url.insert(0, getattr(settings, "HOME_ASSISTANT_URL", "http://homeassistant.local:8123"))
            
            self.inactivity_timeout.delete(0, tk.END)
            self.inactivity_timeout.insert(0, str(getattr(settings, "INACTIVITY_TIMEOUT", 30)))
            
            self.motion_timeout.delete(0, tk.END)
            self.motion_timeout.insert(0, str(getattr(settings, "MOTION_TIMEOUT", 180)))
            
            self.browser_command.delete(0, tk.END)
            self.browser_command.insert(0, getattr(settings, "BROWSER_COMMAND", "chromium-browser"))
            
            # Schedule settings
            self.weekday_morning_on_start.delete(0, tk.END)
            self.weekday_morning_on_start.insert(0, getattr(settings, "WEEKDAY_MORNING_ON_START", "06:00"))
            
            self.weekday_morning_on_end.delete(0, tk.END)
            self.weekday_morning_on_end.insert(0, getattr(settings, "WEEKDAY_MORNING_ON_END", "08:00"))
            
            self.weekday_evening_on_start.delete(0, tk.END)
            self.weekday_evening_on_start.insert(0, getattr(settings, "WEEKDAY_EVENING_ON_START", "17:00"))
            
            self.weekday_evening_on_end.delete(0, tk.END)
            self.weekday_evening_on_end.insert(0, getattr(settings, "WEEKDAY_EVENING_ON_END", "23:00"))
            
            self.weekend_on_start.delete(0, tk.END)
            self.weekend_on_start.insert(0, getattr(settings, "WEEKEND_ON_START", "08:00"))
            
            self.weekend_on_end.delete(0, tk.END)
            self.weekend_on_end.insert(0, getattr(settings, "WEEKEND_ON_END", "23:00"))
            
            # GPIO settings
            self.bh1750_sda_pin.delete(0, tk.END)
            self.bh1750_sda_pin.insert(0, str(getattr(settings, "BH1750_SDA_PIN", 2)))
            
            self.bh1750_scl_pin.delete(0, tk.END)
            self.bh1750_scl_pin.insert(0, str(getattr(settings, "BH1750_SCL_PIN", 11)))
            
            self.bh1750_addr_pin.delete(0, tk.END)
            self.bh1750_addr_pin.insert(0, str(getattr(settings, "BH1750_ADDR_PIN", 14)))
            
            self.pir_vcc_pin.delete(0, tk.END)
            self.pir_vcc_pin.insert(0, str(getattr(settings, "PIR_VCC_PIN", 1)))
            
            self.pir_out_pin.delete(0, tk.END)
            self.pir_out_pin.insert(0, str(getattr(settings, "PIR_OUT_PIN", 3)))
            
            self.pir_gnd_pin.delete(0, tk.END)
            self.pir_gnd_pin.insert(0, str(getattr(settings, "PIR_GND_PIN", 5)))
            
            self.pir_enable_pin.delete(0, tk.END)
            self.pir_enable_pin.insert(0, str(getattr(settings, "PIR_ENABLE_PIN", 9)))
            
            self.monitor_i2c_bus.delete(0, tk.END)
            self.monitor_i2c_bus.insert(0, str(getattr(settings, "MONITOR_I2C_BUS", 20)))
            
            self.vcp_power.delete(0, tk.END)
            self.vcp_power.insert(0, getattr(settings, "VCP_POWER", "D6"))
            
            self.vcp_brightness.delete(0, tk.END)
            self.vcp_brightness.insert(0, getattr(settings, "VCP_BRIGHTNESS", "10"))
            
            # Brightness settings
            self.min_brightness.set(getattr(settings, "MIN_BRIGHTNESS", 10))
            self.min_brightness_value.configure(text=str(int(self.min_brightness.get())))
            
            self.max_brightness.set(getattr(settings, "MAX_BRIGHTNESS", 90))
            self.max_brightness_value.configure(text=str(int(self.max_brightness.get())))
            
            self.night_brightness.set(getattr(settings, "NIGHT_BRIGHTNESS", 15))
            self.night_brightness_value.configure(text=str(int(self.night_brightness.get())))
            
            messagebox.showinfo("Configuration Loaded", "Current configuration loaded successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load configuration: {e}")
    
    def save_configuration(self):
        """Save the configuration to settings.py."""
        try:
            # Validate the input before saving
            self.validate_input()
            
            # Get the absolute path to the settings.py file
            script_dir = os.path.dirname(os.path.abspath(__file__))
            settings_path = os.path.join(script_dir, "config", "settings.py")
            
            # Read the current settings file
            with open(settings_path, "r") as f:
                settings_content = f.read()
            
            # Update the settings
            settings_content = self.update_setting(settings_content, "DAKBOARD_URL", f'"{self.dakboard_url.get()}"')
            settings_content = self.update_setting(settings_content, "HOME_ASSISTANT_URL", f'"{self.homeassistant_url.get()}"')
            settings_content = self.update_setting(settings_content, "INACTIVITY_TIMEOUT", self.inactivity_timeout.get())
            settings_content = self.update_setting(settings_content, "MOTION_TIMEOUT", self.motion_timeout.get())
            settings_content = self.update_setting(settings_content, "BROWSER_COMMAND", f'"{self.browser_command.get()}"')
            
            settings_content = self.update_setting(settings_content, "WEEKDAY_MORNING_ON_START", f'"{self.weekday_morning_on_start.get()}"')
            settings_content = self.update_setting(settings_content, "WEEKDAY_MORNING_ON_END", f'"{self.weekday_morning_on_end.get()}"')
            settings_content = self.update_setting(settings_content, "WEEKDAY_EVENING_ON_START", f'"{self.weekday_evening_on_start.get()}"')
            settings_content = self.update_setting(settings_content, "WEEKDAY_EVENING_ON_END", f'"{self.weekday_evening_on_end.get()}"')
            settings_content = self.update_setting(settings_content, "WEEKEND_ON_START", f'"{self.weekend_on_start.get()}"')
            settings_content = self.update_setting(settings_content, "WEEKEND_ON_END", f'"{self.weekend_on_end.get()}"')
            
            settings_content = self.update_setting(settings_content, "BH1750_SDA_PIN", self.bh1750_sda_pin.get())
            settings_content = self.update_setting(settings_content, "BH1750_SCL_PIN", self.bh1750_scl_pin.get())
            settings_content = self.update_setting(settings_content, "BH1750_ADDR_PIN", self.bh1750_addr_pin.get())
            settings_content = self.update_setting(settings_content, "PIR_VCC_PIN", self.pir_vcc_pin.get())
            settings_content = self.update_setting(settings_content, "PIR_OUT_PIN", self.pir_out_pin.get())
            settings_content = self.update_setting(settings_content, "PIR_GND_PIN", self.pir_gnd_pin.get())
            settings_content = self.update_setting(settings_content, "PIR_ENABLE_PIN", self.pir_enable_pin.get())
            settings_content = self.update_setting(settings_content, "MONITOR_I2C_BUS", self.monitor_i2c_bus.get())
            settings_content = self.update_setting(settings_content, "VCP_POWER", f'"{self.vcp_power.get()}"')
            settings_content = self.update_setting(settings_content, "VCP_BRIGHTNESS", f'"{self.vcp_brightness.get()}"')
            
            settings_content = self.update_setting(settings_content, "MIN_BRIGHTNESS", int(self.min_brightness.get()))
            settings_content = self.update_setting(settings_content, "MAX_BRIGHTNESS", int(self.max_brightness.get()))
            settings_content = self.update_setting(settings_content, "NIGHT_BRIGHTNESS", int(self.night_brightness.get()))
            
            # Write the updated settings back to the file
            with open(settings_path, "w") as f:
                f.write(settings_content)
            
            messagebox.showinfo("Configuration Saved", "Configuration saved successfully.")
        except ValueError as e:
            messagebox.showerror("Validation Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {e}")
    
    def update_setting(self, content, name, value):
        """Update a setting in the settings file.
        
        Args:
            content: The current content of the settings file.
            name: The name of the setting to update.
            value: The new value for the setting.
            
        Returns:
            str: The updated content of the settings file.
        """
        # Look for the setting pattern
        pattern = rf"^{name}\s*=.*$"
        new_line = f"{name} = {value}"
        
        # Replace the first matching line
        result = re.sub(pattern, new_line, content, flags=re.MULTILINE, count=1)
        
        # If no replacement was made, append the setting to the end of the file
        if result == content and name not in content:
            result += f"\n{new_line}"
        
        return result
    
    def validate_input(self):
        """Validate the input fields.
        
        Raises:
            ValueError: If any input is invalid.
        """
        # Validate time formats
        for field_name, field in [
            ("Weekday Morning Start", self.weekday_morning_on_start),
            ("Weekday Morning End", self.weekday_morning_on_end),
            ("Weekday Evening Start", self.weekday_evening_on_start),
            ("Weekday Evening End", self.weekday_evening_on_end),
            ("Weekend Start", self.weekend_on_start),
            ("Weekend End", self.weekend_on_end)
        ]:
            time_str = field.get()
            if not re.match(r"^([01]?[0-9]|2[0-3]):([0-5][0-9])$", time_str):
                raise ValueError(f"Invalid time format for {field_name}: {time_str}\nUse HH:MM format (24-hour).")
        
        # Validate numeric values
        for field_name, field in [
            ("Inactivity Timeout", self.inactivity_timeout),
            ("Motion Timeout", self.motion_timeout),
            ("BH1750 SDA Pin", self.bh1750_sda_pin),
            ("BH1750 SCL Pin", self.bh1750_scl_pin),
            ("BH1750 ADDR Pin", self.bh1750_addr_pin),
            ("PIR VCC Pin", self.pir_vcc_pin),
            ("PIR OUT Pin", self.pir_out_pin),
            ("PIR GND Pin", self.pir_gnd_pin),
            ("PIR Enable Pin", self.pir_enable_pin),
            ("Monitor I2C Bus", self.monitor_i2c_bus)
        ]:
            try:
                int(field.get())
            except ValueError:
                raise ValueError(f"Invalid numeric value for {field_name}: {field.get()}")
        
        # Validate URLs
        if not self.dakboard_url.get().startswith(("http://", "https://")):
            raise ValueError(f"Invalid DakBoard URL: {self.dakboard_url.get()}\nURL must start with http:// or https://.")
        
        if not self.homeassistant_url.get().startswith(("http://", "https://")):
            raise ValueError(f"Invalid Home Assistant URL: {self.homeassistant_url.get()}\nURL must start with http:// or https://.")


def main():
    """Run the configuration editor."""
    root = tk.Tk()
    app = ConfigEditor(root)
    root.mainloop()


if __name__ == "__main__":
    main()
