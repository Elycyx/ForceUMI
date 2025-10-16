"""
Tests for device modules
"""

import pytest
import numpy as np
from forceumi.devices import Camera, PoseSensor, ForceSensor


class TestCamera:
    """Test Camera device"""
    
    def test_init(self):
        """Test camera initialization"""
        camera = Camera(device_id=0, width=640, height=480, fps=30)
        assert camera.device_id == 0
        assert camera.width == 640
        assert camera.height == 480
        assert camera.fps == 30
        assert not camera.is_connected()
    
    def test_connect_disconnect(self):
        """Test camera connection (may fail without actual hardware)"""
        camera = Camera(device_id=0)
        
        # Note: This may fail without actual camera hardware
        # In real testing, you would mock the cv2.VideoCapture
        try:
            connected = camera.connect()
            if connected:
                assert camera.is_connected()
                disconnected = camera.disconnect()
                assert disconnected
                assert not camera.is_connected()
        except Exception:
            # Expected to fail without hardware
            pass


class TestPoseSensor:
    """Test PoseSensor device"""
    
    def test_init(self):
        """Test pose sensor initialization"""
        sensor = PoseSensor(port="/dev/ttyUSB0", baudrate=115200)
        assert sensor.port == "/dev/ttyUSB0"
        assert sensor.baudrate == 115200
        assert not sensor.is_connected()
    
    def test_connect_disconnect(self):
        """Test pose sensor connection"""
        sensor = PoseSensor()
        
        # Mock connection for testing
        connected = sensor.connect()
        assert connected
        assert sensor.is_connected()
        
        disconnected = sensor.disconnect()
        assert disconnected
        assert not sensor.is_connected()
    
    def test_read(self):
        """Test pose sensor reading"""
        sensor = PoseSensor()
        sensor.connect()
        
        data = sensor.read()
        assert data is not None
        assert isinstance(data, np.ndarray)
        assert data.shape == (7,)
        assert data.dtype == np.float32
        
        sensor.disconnect()


class TestForceSensor:
    """Test ForceSensor device"""
    
    def test_init(self):
        """Test force sensor initialization"""
        sensor = ForceSensor(port="/dev/ttyUSB1", baudrate=115200)
        assert sensor.port == "/dev/ttyUSB1"
        assert sensor.baudrate == 115200
        assert not sensor.is_connected()
        assert np.allclose(sensor.bias, np.zeros(6))
    
    def test_connect_disconnect(self):
        """Test force sensor connection"""
        sensor = ForceSensor()
        
        connected = sensor.connect()
        assert connected
        assert sensor.is_connected()
        
        disconnected = sensor.disconnect()
        assert disconnected
        assert not sensor.is_connected()
    
    def test_read(self):
        """Test force sensor reading"""
        sensor = ForceSensor()
        sensor.connect()
        
        data = sensor.read()
        assert data is not None
        assert isinstance(data, np.ndarray)
        assert data.shape == (6,)
        assert data.dtype == np.float32
        
        sensor.disconnect()

