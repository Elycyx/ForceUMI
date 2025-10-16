"""
Pose Sensor Device Interface

Handles UMI pose sensor for 6DOF position and orientation data using PyTracker.
"""

import numpy as np
from typing import Optional, Dict, Any
from forceumi.devices.base import BaseDevice

try:
    import pytracker
    PYTRACKER_AVAILABLE = True
except ImportError:
    PYTRACKER_AVAILABLE = False


class PoseSensor(BaseDevice):
    """UMI 7D state sensor device (position + orientation + gripper)"""
    
    def __init__(
        self,
        device_name: str = "tracker_1",
        config_file: Optional[str] = None,
        gripper_port: Optional[str] = None,
        name: str = "PoseSensor"
    ):
        """
        Initialize pose sensor using PyTracker
        
        Args:
            device_name: Name of the tracker device in PyTracker (e.g., "tracker_1")
            config_file: Optional path to PyTracker config.json file
            gripper_port: Optional serial port for gripper sensor
            name: Device name
        """
        super().__init__(name)
        self.device_name = device_name
        self.config_file = config_file
        self.gripper_port = gripper_port
        
        self.tracker = None
        self.device = None
        self.gripper_value = 0.0  # Current gripper state
        
    def connect(self) -> bool:
        """
        Connect to pose sensor via PyTracker
        
        Returns:
            bool: True if connection successful
        """
        if not PYTRACKER_AVAILABLE:
            self.logger.error("PyTracker is not installed. Install with: pip install git+https://github.com/Elycyx/PyTracker.git")
            return False
        
        try:
            # Initialize PyTracker
            if self.config_file:
                self.tracker = pytracker.Tracker(self.config_file)
            else:
                self.tracker = pytracker.Tracker()
            
            # Get the specific device
            if self.device_name not in self.tracker.devices:
                available_devices = list(self.tracker.devices.keys())
                self.logger.error(f"Device '{self.device_name}' not found. Available devices: {available_devices}")
                return False
            
            self.device = self.tracker.devices[self.device_name]
            
            # TODO: Initialize gripper sensor if port provided
            # if self.gripper_port:
            #     import serial
            #     self.gripper_conn = serial.Serial(self.gripper_port, 115200, timeout=1)
            
            self._connected = True
            self.logger.info(f"Pose sensor '{self.device_name}' connected successfully")
            
            # Print discovered devices for debugging
            self.tracker.print_discovered_objects()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to pose sensor: {e}")
            return False
    
    def disconnect(self) -> bool:
        """
        Disconnect from pose sensor
        
        Returns:
            bool: True if disconnection successful
        """
        try:
            # PyTracker handles cleanup automatically
            self.device = None
            self.tracker = None
            
            # TODO: Close gripper connection if exists
            # if hasattr(self, 'gripper_conn') and self.gripper_conn:
            #     self.gripper_conn.close()
            
            self._connected = False
            self.logger.info("Pose sensor disconnected")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to disconnect pose sensor: {e}")
            return False
    
    def read(self) -> Optional[np.ndarray]:
        """
        Read pose data from sensor
        
        Returns:
            np.ndarray: 7D state [x, y, z, rx, ry, rz, gripper] or None if read failed
                       gripper is always absolute value
        """
        if not self.is_connected():
            self.logger.warning("Pose sensor not connected")
            return None
        
        try:
            # Get pose from PyTracker (returns [x, y, z, yaw, pitch, roll])
            pose_data = self.device.get_pose_euler()
            
            if pose_data is None or len(pose_data) != 6:
                self.logger.warning("Failed to read valid pose data")
                return None
            
            # Convert to [x, y, z, rx, ry, rz, gripper] format
            x, y, z, yaw, pitch, roll = pose_data
            
            # TODO: Read gripper value from serial port
            # For now, use the stored gripper value
            gripper = self._read_gripper()
            
            # Create 7D state array
            state = np.array([x, y, z, roll, pitch, yaw, gripper], dtype=np.float32)
            
            return state
            
        except Exception as e:
            self.logger.error(f"Error reading from pose sensor: {e}")
            return None
    
    def _read_gripper(self) -> float:
        """
        Read gripper state
        
        Returns:
            float: Gripper value (0.0 = closed, 1.0 = open)
        """
        try:
            # TODO: Implement actual gripper reading from serial port
            # if hasattr(self, 'gripper_conn') and self.gripper_conn:
            #     data = self.gripper_conn.readline().decode().strip()
            #     return float(data)
            
            # For now, return the stored value
            return self.gripper_value
            
        except Exception as e:
            self.logger.error(f"Error reading gripper: {e}")
            return self.gripper_value
    
    def get_pose_quaternion(self) -> Optional[np.ndarray]:
        """
        Get pose in quaternion format
        
        Returns:
            np.ndarray: 8D array [x, y, z, qw, qx, qy, qz, gripper] or None if read failed
        """
        if not self.is_connected():
            self.logger.warning("Pose sensor not connected")
            return None
        
        try:
            pose_data = self.device.get_pose_quaternion()
            
            if pose_data is None or len(pose_data) != 7:
                return None
            
            # pose_data is [x, y, z, r_w, r_x, r_y, r_z]
            gripper = self._read_gripper()
            
            # Return [x, y, z, qw, qx, qy, qz, gripper]
            state = np.array([*pose_data, gripper], dtype=np.float32)
            return state
            
        except Exception as e:
            self.logger.error(f"Error reading quaternion pose: {e}")
            return None
    
    def get_velocity(self) -> Optional[np.ndarray]:
        """
        Get linear velocity
        
        Returns:
            np.ndarray: 3D velocity [vx, vy, vz] or None if read failed
        """
        if not self.is_connected():
            return None
        
        try:
            return self.device.get_velocity()
        except Exception as e:
            self.logger.error(f"Error reading velocity: {e}")
            return None
    
    def get_angular_velocity(self) -> Optional[np.ndarray]:
        """
        Get angular velocity
        
        Returns:
            np.ndarray: 3D angular velocity [wx, wy, wz] or None if read failed
        """
        if not self.is_connected():
            return None
        
        try:
            return self.device.get_angular_velocity()
        except Exception as e:
            self.logger.error(f"Error reading angular velocity: {e}")
            return None
    
    def set_gripper(self, value: float):
        """
        Set gripper target value
        
        Args:
            value: Gripper value (0.0 = closed, 1.0 = open)
        """
        self.gripper_value = np.clip(value, 0.0, 1.0)
        
        # TODO: Send command to gripper actuator
        # if hasattr(self, 'gripper_conn') and self.gripper_conn:
        #     self.gripper_conn.write(f"{self.gripper_value}\n".encode())
    
    def sample(self, num_samples: int, sample_rate: float) -> Optional[np.ndarray]:
        """
        Collect multiple pose samples at specified rate
        
        Args:
            num_samples: Number of samples to collect
            sample_rate: Sampling rate in Hz
            
        Returns:
            np.ndarray: Array of shape (num_samples, 7) or None if failed
        """
        if not self.is_connected():
            self.logger.warning("Pose sensor not connected")
            return None
        
        try:
            # Use PyTracker's built-in sampling
            data_buffer = self.device.sample(num_samples, sample_rate)
            
            # Convert to our 7D format
            samples = []
            for i in range(len(data_buffer.time)):
                x = data_buffer.x[i]
                y = data_buffer.y[i]
                z = data_buffer.z[i]
                roll = data_buffer.roll[i]
                pitch = data_buffer.pitch[i]
                yaw = data_buffer.yaw[i]
                gripper = self._read_gripper()  # Same gripper for all samples
                
                samples.append([x, y, z, roll, pitch, yaw, gripper])
            
            return np.array(samples, dtype=np.float32)
            
        except Exception as e:
            self.logger.error(f"Error sampling data: {e}")
            return None
    
    def get_device_info(self) -> Dict[str, Any]:
        """
        Get device information
        
        Returns:
            dict: Device information
        """
        if not self.is_connected():
            return {}
        
        try:
            return {
                "device_name": self.device_name,
                "device_type": "Tracker",
                "serial": self.device.get_serial() if hasattr(self.device, 'get_serial') else "Unknown",
                "connected": self._connected,
            }
        except Exception as e:
            self.logger.error(f"Error getting device info: {e}")
            return {}

