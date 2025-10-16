"""
Launch GUI Example

Simple script to launch the GUI with optional config file.
"""

import sys
from pathlib import Path
from forceumi.gui.main_window import main as gui_main


def main():
    """Launch GUI"""
    print("Launching ForceUMI Data Collection GUI...")
    
    # Check for config file
    config_files = ["config.yaml", "config.yml", "config.json"]
    config_found = None
    
    for config_file in config_files:
        if Path(config_file).exists():
            config_found = config_file
            print(f"Using configuration: {config_file}")
            break
    
    if not config_found:
        print("No configuration file found, using defaults")
    
    # Launch GUI
    gui_main()


if __name__ == "__main__":
    main()

