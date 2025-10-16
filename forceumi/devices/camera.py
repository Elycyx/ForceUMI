"""
RGB Camera Device Interface

Handles RGB fisheye camera for image acquisition.
"""

import cv2
import numpy as np
from typing import Optional, Dict, Any
from forceumi.devices.base import BaseDevice


class Camera(BaseDevice):
    """RGB fisheye camera device"""
    
    def __init__(
        self,
        device_id: int = 0,
        width: int = 640,
        height: int = 480,
        fps: int = 30,
        name: str = "Camera"
    ):
        """
        Initialize camera
        
        Args:
            device_id: Camera device ID (default: 0)
            width: Image width in pixels
            height: Image height in pixels
            fps: Frames per second
            name: Device name
        """
        super().__init__(name)
        self.device_id = device_id
        self.width = width
        self.height = height
        self.fps = fps
        self.cap = None
        
    def connect(self) -> bool:
        """
        Connect to camera
        
        Returns:
            bool: True if connection successful
        """
        try:
            self.cap = cv2.VideoCapture(self.device_id)
            
            if not self.cap.isOpened():
                self.logger.error(f"Failed to open camera {self.device_id}")
                return False
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)
            
            self._connected = True
            self.logger.info(f"Camera {self.device_id} connected successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to camera: {e}")
            return False
    
    def disconnect(self) -> bool:
        """
        Disconnect from camera
        
        Returns:
            bool: True if disconnection successful
        """
        try:
            if self.cap is not None:
                self.cap.release()
                self.cap = None
            
            self._connected = False
            self.logger.info("Camera disconnected")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to disconnect camera: {e}")
            return False
    
    def read(self) -> Optional[np.ndarray]:
        """
        Read frame from camera
        
        Returns:
            np.ndarray: RGB image (H, W, 3) or None if read failed
        """
        if not self.is_connected():
            self.logger.warning("Camera not connected")
            return None
        
        try:
            ret, frame = self.cap.read()
            
            if not ret:
                self.logger.warning("Failed to read frame from camera")
                return None
            
            # Convert BGR to RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            return frame
            
        except Exception as e:
            self.logger.error(f"Error reading from camera: {e}")
            return None
    
    def get_properties(self) -> Dict[str, Any]:
        """
        Get camera properties
        
        Returns:
            dict: Camera properties
        """
        if not self.is_connected():
            return {}
        
        return {
            "width": int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "fps": int(self.cap.get(cv2.CAP_PROP_FPS)),
            "backend": self.cap.getBackendName(),
        }

