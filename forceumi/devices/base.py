"""
Base Device Class Definition

All device classes should inherit from this base class and implement the standard interface.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
import logging


class BaseDevice(ABC):
    """Base device class defining standard interface for all devices"""
    
    def __init__(self, name: str = "Device"):
        """
        Initialize device
        
        Args:
            name: Device name
        """
        self.name = name
        self.logger = logging.getLogger(f"forceumi.devices.{name}")
        self._connected = False
        
    @abstractmethod
    def connect(self) -> bool:
        """
        Connect to device
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """
        Disconnect from device
        
        Returns:
            bool: True if disconnection successful, False otherwise
        """
        pass
    
    @abstractmethod
    def read(self) -> Optional[Any]:
        """
        Read data from device
        
        Returns:
            Device data, or None if read failed
        """
        pass
    
    def is_connected(self) -> bool:
        """
        Check if device is connected
        
        Returns:
            bool: True if connected, False otherwise
        """
        return self._connected
    
    def __enter__(self):
        """Context manager support"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager support"""
        self.disconnect()
        return False
    
    def __repr__(self) -> str:
        status = "connected" if self._connected else "disconnected"
        return f"<{self.__class__.__name__}(name={self.name}, status={status})>"

