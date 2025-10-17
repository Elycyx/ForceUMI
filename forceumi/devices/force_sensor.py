"""
Force Sensor Device Interface

Handles 6-axis force/torque sensor for force data acquisition using PyForce.
"""

import time
import numpy as np
from typing import Optional, Dict, Any
from forceumi.devices.base import BaseDevice

try:
    from pyforce import ForceSensor as PyForceSensor
    PYFORCE_AVAILABLE = True
except ImportError:
    PYFORCE_AVAILABLE = False


class ForceSensor(BaseDevice):
    """6-axis force/torque sensor device (Sunrise/宇立)"""
    
    def __init__(
        self,
        ip_addr: str = "192.168.0.108",
        port: int = 4008,
        sample_rate: Optional[int] = None,
        name: str = "ForceSensor"
    ):
        """
        Initialize force sensor using PyForce
        
        Args:
            ip_addr: Force sensor IP address (default: 192.168.0.108)
            port: Force sensor port (default: 4008)
            sample_rate: Optional sampling rate in Hz
            name: Device name
        """
        super().__init__(name)
        self.ip_addr = ip_addr
        self.port = port
        self.sample_rate = sample_rate
        
        self.sensor = None
        self.bias = np.zeros(6, dtype=np.float32)
        
    def connect(self) -> bool:
        """
        Connect to force sensor via PyForce
        
        Returns:
            bool: True if connection successful
        """
        if not PYFORCE_AVAILABLE:
            self.logger.error("PyForce is not installed. Install with: pip install git+https://github.com/Elycyx/PyForce.git")
            return False
        
        try:
            # Create PyForce sensor instance
            self.sensor = PyForceSensor(ip_addr=self.ip_addr, port=self.port)
            
            # Connect to sensor
            if not self.sensor.connect():
                self.logger.error(f"Failed to connect to force sensor at {self.ip_addr}:{self.port}")
                return False
            
            # Start data stream (required for real-time reading)
            if not self.sensor.start_stream():
                self.logger.error("Failed to start data stream")
                self.sensor.disconnect()
                return False
            
            # Wait for stream to stabilize
            time.sleep(0.5)
            self.logger.info("Data stream started and stabilized")
            
            # Configure sample rate if specified
            if self.sample_rate is not None:
                self.sensor.set_sample_rate(self.sample_rate)
                self.logger.info(f"Sample rate set to {self.sample_rate} Hz")
            
            # Query sensor info
            info = self.sensor.query_info()
            if info:
                self.logger.info(f"Force sensor info: {info}")
            
            self._connected = True
            self.logger.info(f"Force sensor connected at {self.ip_addr}:{self.port}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to force sensor: {e}")
            if self.sensor:
                self.sensor.disconnect()
            return False
    
    def disconnect(self) -> bool:
        """
        Disconnect from force sensor
        
        Returns:
            bool: True if disconnection successful
        """
        try:
            if self.sensor is not None:
                # Stop data stream
                self.sensor.stop_stream()
                # Disconnect
                self.sensor.disconnect()
                self.sensor = None
            
            self._connected = False
            self.logger.info("Force sensor disconnected")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to disconnect force sensor: {e}")
            return False
    
    def read(self) -> Optional[np.ndarray]:
        """
        Read force/torque data from sensor
        
        Returns:
            np.ndarray: 6-axis force/torque [fx, fy, fz, mx, my, mz] or None if read failed
        """
        if not self.is_connected():
            self.logger.warning("Force sensor not connected")
            return None
        
        try:
            # Read from PyForce (returns np.ndarray [fx, fy, fz, mx, my, mz])
            force_data = self.sensor.read()
            
            if force_data is None:
                self.logger.warning("Failed to read force data")
                return None
            
            # Apply bias correction
            corrected_data = force_data - self.bias
            
            return corrected_data.astype(np.float32)
            
        except Exception as e:
            self.logger.error(f"Error reading from force sensor: {e}")
            return None
    
    def get_with_timestamp(self) -> Optional[Dict[str, Any]]:
        """
        Get force data with timestamp
        
        Returns:
            dict: {'ft': np.ndarray, 'timestamp': float} or None if read failed
        """
        if not self.is_connected():
            self.logger.warning("Force sensor not connected")
            return None
        
        try:
            # Use PyForce's get() method which returns data with timestamp
            data = self.sensor.get()
            
            if data is None:
                return None
            
            # Apply bias correction to force/torque data
            data['ft'] = data['ft'] - self.bias
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error reading timestamped force data: {e}")
            return None
    
    def zero(self, num_samples: int = 100) -> bool:
        """
        Zero/bias the force sensor by averaging multiple samples
        
        Args:
            num_samples: Number of samples to average for bias calculation
            
        Returns:
            bool: True if zeroing successful
        """
        if not self.is_connected():
            self.logger.warning("Force sensor not connected")
            return False
        
        try:
            # Use PyForce's built-in zero calibration
            if self.sensor.zero(num_samples=num_samples):
                # Get the bias from PyForce
                self.bias = self.sensor.bias.astype(np.float32)
                self.logger.info(f"Force sensor zeroed with bias: {self.bias}")
                return True
            else:
                self.logger.error("Failed to zero force sensor")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to zero force sensor: {e}")
            return False
    
    def set_sample_rate(self, rate: int) -> bool:
        """
        Set sensor sampling rate
        
        Args:
            rate: Sampling rate in Hz
            
        Returns:
            bool: True if successful
        """
        if not self.is_connected():
            self.logger.warning("Force sensor not connected")
            return False
        
        try:
            if self.sensor.set_sample_rate(rate):
                self.sample_rate = rate
                self.logger.info(f"Sample rate set to {rate} Hz")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to set sample rate: {e}")
            return False
    
    def get_sensor_info(self) -> Optional[Dict[str, Any]]:
        """
        Query sensor information
        
        Returns:
            dict: Sensor information or None if failed
        """
        if not self.is_connected():
            return None
        
        try:
            info = self.sensor.query_info()
            return info
        except Exception as e:
            self.logger.error(f"Failed to query sensor info: {e}")
            return None
    
    def set_compute_unit(self, unit: str) -> bool:
        """
        Set computation unit
        
        Args:
            unit: Computation unit string (e.g., "MVPV")
            
        Returns:
            bool: True if successful
        """
        if not self.is_connected():
            self.logger.warning("Force sensor not connected")
            return False
        
        try:
            return self.sensor.set_compute_unit(unit)
        except Exception as e:
            self.logger.error(f"Failed to set compute unit: {e}")
            return False
    
    def set_decouple_matrix(self, matrix: str) -> bool:
        """
        Set decouple matrix
        
        Args:
            matrix: Decouple matrix string
            
        Returns:
            bool: True if successful
        """
        if not self.is_connected():
            self.logger.warning("Force sensor not connected")
            return False
        
        try:
            return self.sensor.set_decouple_matrix(matrix)
        except Exception as e:
            self.logger.error(f"Failed to set decouple matrix: {e}")
            return False

