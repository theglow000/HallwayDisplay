"""
Configuration Launcher module for the Hallway Display system.

This module adds a floating button overlay to the screen that launches
the configuration GUI when clicked.
"""

import os
import subprocess
import threading
import signal
import sys
import tkinter as tk

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import setup_logger

# Setup logger
logger = setup_logger('config_launcher')

class ConfigLauncher:
    """A floating button overlay to launch the configuration GUI.
    
    This class creates a small, semi-transparent button in the corner of the
    screen that launches the configuration GUI when clicked.
    """
    
    def __init__(self, position="bottom-right", size=50, opacity=0.6):
        """Initialize the configuration launcher.
        
        Args:
            position: The position of the button: "bottom-right", "bottom-left",
                      "top-right", or "top-left".
            size: The size of the button in pixels.
            opacity: The opacity of the button (0.0 to 1.0).
        """
        self.position = position
        self.size = size
        self.opacity = opacity
        self.root = None
        self.button = None
        self.is_running = False
        self.thread = None
        
        logger.info("Configuration launcher initialized")
    
    def start(self):
        """Start the configuration launcher in a separate thread."""
        if self.is_running:
            logger.warning("Configuration launcher already running")
            return
        
        logger.info("Starting configuration launcher")
        self.is_running = True
        self.thread = threading.Thread(target=self._run_launcher, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop the configuration launcher."""
        if not self.is_running:
            return
        
        logger.info("Stopping configuration launcher")
        self.is_running = False
        if self.root:
            self.root.quit()
            self.root.destroy()
        
        # Wait for the thread to finish
        if self.thread:
            self.thread.join(timeout=2.0)
    
    def _run_launcher(self):
        """Run the configuration launcher in a Tkinter window."""
        try:
            # Create a transparent window
            self.root = tk.Tk()
            self.root.overrideredirect(True)  # Remove window decorations
            self.root.attributes('-topmost', True)  # Keep on top
            
            # Configure transparency
            if sys.platform == "linux":
                self.root.attributes('-type', 'utility')  # Small utility window
                try:
                    self.root.attributes('-alpha', self.opacity)  # Set transparency
                except:
                    logger.warning("Transparency not supported on this platform")
            elif sys.platform == "win32":
                self.root.attributes('-alpha', self.opacity)  # Set transparency
            elif sys.platform == "darwin":
                self.root.attributes('-alpha', self.opacity)  # Set transparency
            
            # Create the button with a settings gear icon (Unicode character)
            self.button = tk.Button(
                self.root,
                text="⚙️",
                font=("Arial", int(self.size/2)),
                bg='#555555',
                fg='white',
                activebackground='#777777',
                activeforeground='white',
                bd=0,
                highlightthickness=0,
                command=self._launch_config,
                width=2,
                height=1
            )
            self.button.pack(fill=tk.BOTH, expand=True)
            
            # Position the window in the corner
            self._position_window()
            
            # Add a tooltip
            self._create_tooltip(self.button, "Open Settings")
            
            # Monitor for the stop signal
            self.root.after(500, self._check_stop_signal)
            
            # Start the Tkinter main loop
            self.root.mainloop()
            
            logger.info("Configuration launcher stopped")
        except Exception as e:
            logger.error(f"Error in configuration launcher: {e}")
        finally:
            self.is_running = False
    
    def _position_window(self):
        """Position the window in the specified corner."""
        # Get screen width and height
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Set window size
        self.root.geometry(f"{self.size}x{self.size}")
        
        # Position window in the specified corner
        x = 0
        y = 0
        
        if self.position == "bottom-right":
            x = screen_width - self.size
            y = screen_height - self.size
        elif self.position == "bottom-left":
            x = 0
            y = screen_height - self.size
        elif self.position == "top-right":
            x = screen_width - self.size
            y = 0
        elif self.position == "top-left":
            x = 0
            y = 0
        
        self.root.geometry(f"+{x}+{y}")
    
    def _create_tooltip(self, widget, text):
        """Create a tooltip for the widget.
        
        Args:
            widget: The widget to add the tooltip to.
            text: The tooltip text.
        """
        # Create a tooltip label
        tooltip = tk.Label(
            widget,
            text=text,
            bg="#333333",
            fg="white",
            padx=5,
            pady=5,
            wraplength=200,
            relief=tk.SOLID,
            borderwidth=1
        )
        
        # Function to show the tooltip
        def show_tooltip(event):
            tooltip.place(x=self.size, y=0)
            
        # Function to hide the tooltip
        def hide_tooltip(event):
            tooltip.place_forget()
        
        # Bind the events
        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", hide_tooltip)
    
    def _check_stop_signal(self):
        """Check if the stop signal has been set."""
        if not self.is_running:
            self.root.quit()
            return
        
        self.root.after(500, self._check_stop_signal)
    
    def _launch_config(self):
        """Launch the configuration GUI."""
        try:
            logger.info("Launching configuration GUI")
            
            # Get the path to the configuration script
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_script = os.path.join(script_dir, "configure.py")
            
            # Launch the configuration GUI in a separate process
            env = os.environ.copy()
            env['DISPLAY'] = ':0'
            subprocess.Popen(
                ["python3", config_script],
                env=env,
                cwd=script_dir,
                start_new_session=True
            )
            
            logger.info("Configuration GUI launched")
        except Exception as e:
            logger.error(f"Error launching configuration GUI: {e}")
