"""
Configuration Management

Handles loading and saving configuration files.
"""

import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging


class Config:
    """Configuration manager for ForceUMI system"""
    
    DEFAULT_CONFIG = {
        "devices": {
            "camera": {
                "device_id": 3,
                "width": 480,
                "height": 480,
                "fps": 20,
            },
            "pose_sensor": {
                # PyTracker (VR tracking) configuration
                "device_name": "tracker_1",  # VR tracker name in PyTracker
                "config_file": None,  # Optional: path to PyTracker config.json
                "gripper_port": None,  # Optional: serial port for gripper sensor
            },
            "force_sensor": {
                # PyForce (Sunrise sensor) configuration
                "ip_addr": "192.168.0.108",  # Force sensor IP address
                "port": 4008,  # Force sensor TCP port
                "sample_rate": 100,  # Optional: sampling rate in Hz (10-1000)
            },
        },
        "data": {
            "save_dir": "./data",
            "compression": "gzip",
            "compression_level": 4,
            "auto_save": True,
        },
        "collector": {
            "max_fps": 20.0,
        },
        "gui": {
            "window_title": "ForceUMI Data Collection",
            "image_display_size": [480, 480],
            "force_plot_length": 500,
            "update_interval": 50,  # milliseconds (~30 fps)
        },
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration
        
        Args:
            config_path: Path to configuration file (YAML or JSON)
        """
        self.logger = logging.getLogger("forceumi.Config")
        self.config = self.DEFAULT_CONFIG.copy()
        
        if config_path:
            self.load(config_path)
    
    def load(self, filepath: str) -> bool:
        """
        Load configuration from file
        
        Args:
            filepath: Path to configuration file
            
        Returns:
            bool: True if load successful
        """
        try:
            filepath = Path(filepath)
            
            if not filepath.exists():
                self.logger.warning(f"Config file not found: {filepath}")
                return False
            
            with open(filepath, "r") as f:
                if filepath.suffix in [".yaml", ".yml"]:
                    loaded_config = yaml.safe_load(f)
                elif filepath.suffix == ".json":
                    loaded_config = json.load(f)
                else:
                    self.logger.error(f"Unsupported config format: {filepath.suffix}")
                    return False
            
            # Deep merge with default config
            self._deep_update(self.config, loaded_config)
            
            self.logger.info(f"Configuration loaded from {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return False
    
    def save(self, filepath: str) -> bool:
        """
        Save configuration to file
        
        Args:
            filepath: Path to save configuration file
            
        Returns:
            bool: True if save successful
        """
        try:
            filepath = Path(filepath)
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, "w") as f:
                if filepath.suffix in [".yaml", ".yml"]:
                    yaml.dump(self.config, f, default_flow_style=False)
                elif filepath.suffix == ".json":
                    json.dump(self.config, f, indent=2)
                else:
                    self.logger.error(f"Unsupported config format: {filepath.suffix}")
                    return False
            
            self.logger.info(f"Configuration saved to {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation
        
        Args:
            key: Configuration key (e.g., "devices.camera.width")
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split(".")
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """
        Set configuration value using dot notation
        
        Args:
            key: Configuration key (e.g., "devices.camera.width")
            value: Value to set
        """
        keys = key.split(".")
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def _deep_update(self, base: Dict, update: Dict):
        """
        Deep update dictionary
        
        Args:
            base: Base dictionary to update
            update: Dictionary with updates
        """
        for key, value in update.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Get configuration as dictionary
        
        Returns:
            dict: Configuration dictionary
        """
        return self.config.copy()
    
    def __repr__(self) -> str:
        return f"<Config({len(self.config)} sections)>"

