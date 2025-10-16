"""
Tests for configuration management
"""

import pytest
import tempfile
from pathlib import Path

from forceumi.config import Config


class TestConfig:
    """Test Config manager"""
    
    def test_init(self):
        """Test configuration initialization"""
        config = Config()
        assert config.config is not None
        assert "devices" in config.config
        assert "data" in config.config
        assert "collector" in config.config
        assert "gui" in config.config
    
    def test_get(self):
        """Test getting configuration values"""
        config = Config()
        
        # Get nested value
        camera_width = config.get("devices.camera.width")
        assert camera_width == 640
        
        # Get with default
        nonexistent = config.get("nonexistent.key", "default")
        assert nonexistent == "default"
    
    def test_set(self):
        """Test setting configuration values"""
        config = Config()
        
        # Set nested value
        config.set("devices.camera.width", 1280)
        assert config.get("devices.camera.width") == 1280
        
        # Set new value
        config.set("new.nested.value", 42)
        assert config.get("new.nested.value") == 42
    
    def test_save_and_load_yaml(self):
        """Test saving and loading YAML configuration"""
        config = Config()
        config.set("devices.camera.width", 1280)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "config.yaml"
            
            # Save
            success = config.save(str(filepath))
            assert success
            assert filepath.exists()
            
            # Load
            new_config = Config()
            success = new_config.load(str(filepath))
            assert success
            assert new_config.get("devices.camera.width") == 1280
    
    def test_save_and_load_json(self):
        """Test saving and loading JSON configuration"""
        config = Config()
        config.set("devices.camera.fps", 60)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "config.json"
            
            # Save
            success = config.save(str(filepath))
            assert success
            assert filepath.exists()
            
            # Load
            new_config = Config()
            success = new_config.load(str(filepath))
            assert success
            assert new_config.get("devices.camera.fps") == 60
    
    def test_to_dict(self):
        """Test converting configuration to dictionary"""
        config = Config()
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert "devices" in config_dict
        assert "data" in config_dict

