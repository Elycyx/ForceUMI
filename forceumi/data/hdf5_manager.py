"""
HDF5 File Manager

Handles reading and writing episode data to HDF5 files.
"""

import h5py
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import logging


class HDF5Manager:
    """Manager for HDF5 file operations"""
    
    def __init__(
        self,
        compression: str = "gzip",
        compression_level: int = 4
    ):
        """
        Initialize HDF5 manager
        
        Args:
            compression: Compression algorithm (gzip, lzf, None)
            compression_level: Compression level (0-9 for gzip)
        """
        self.compression = compression
        self.compression_level = compression_level
        self.logger = logging.getLogger("forceumi.data.HDF5Manager")
    
    def save_episode(
        self,
        filepath: str,
        data: Dict[str, Any],
        overwrite: bool = False
    ) -> bool:
        """
        Save episode data to HDF5 file
        
        Args:
            filepath: Path to save HDF5 file
            data: Dictionary containing episode data
            overwrite: Whether to overwrite existing file
            
        Returns:
            bool: True if save successful
        """
        try:
            filepath = Path(filepath)
            
            # Check if file exists
            if filepath.exists() and not overwrite:
                self.logger.error(f"File already exists: {filepath}")
                return False
            
            # Create parent directory if needed
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # Save to HDF5
            with h5py.File(filepath, "w") as f:
                # Save main datasets
                main_keys = ["image", "state", "action", "force", "timestamp"]
                for key in main_keys:
                    if key in data and len(data[key]) > 0:
                        arr = data[key]
                        
                        # Create dataset with compression
                        if key == "image":
                            # Images use chunking for better compression
                            f.create_dataset(
                                key,
                                data=arr,
                                compression=self.compression,
                                compression_opts=self.compression_level,
                                chunks=(1, *arr.shape[1:])
                            )
                        else:
                            f.create_dataset(
                                key,
                                data=arr,
                                compression=self.compression,
                                compression_opts=self.compression_level
                            )
                
                # Save per-sensor timestamps (v0.3.1+)
                for ts_key in ["timestamp_camera", "timestamp_pose", "timestamp_force"]:
                    if ts_key in data and len(data[ts_key]) > 0:
                        f.create_dataset(
                            ts_key,
                            data=data[ts_key],
                            compression=self.compression,
                            compression_opts=self.compression_level
                        )
                
                # Save metadata as attributes
                if "metadata" in data:
                    for key, value in data["metadata"].items():
                        f.attrs[key] = value
            
            self.logger.info(f"Episode saved to {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save episode: {e}")
            return False
    
    def load_episode(self, filepath: str) -> Optional[Dict[str, Any]]:
        """
        Load episode data from HDF5 file
        
        Args:
            filepath: Path to HDF5 file
            
        Returns:
            dict: Episode data or None if load failed
        """
        try:
            filepath = Path(filepath)
            
            if not filepath.exists():
                self.logger.error(f"File not found: {filepath}")
                return None
            
            data = {}
            
            with h5py.File(filepath, "r") as f:
                # Load main datasets
                for key in ["image", "state", "action", "force", "timestamp"]:
                    if key in f:
                        data[key] = f[key][:]
                    else:
                        data[key] = np.array([])
                
                # Load per-sensor timestamps (v0.3.1+)
                for ts_key in ["timestamp_camera", "timestamp_pose", "timestamp_force"]:
                    if ts_key in f:
                        data[ts_key] = f[ts_key][:]
                
                # Load metadata
                metadata = {}
                for key in f.attrs:
                    metadata[key] = f.attrs[key]
                data["metadata"] = metadata
            
            self.logger.info(f"Episode loaded from {filepath}")
            return data
            
        except Exception as e:
            self.logger.error(f"Failed to load episode: {e}")
            return None
    
    def get_episode_info(self, filepath: str) -> Optional[Dict[str, Any]]:
        """
        Get episode metadata without loading full data
        
        Args:
            filepath: Path to HDF5 file
            
        Returns:
            dict: Episode metadata or None if load failed
        """
        try:
            filepath = Path(filepath)
            
            if not filepath.exists():
                self.logger.error(f"File not found: {filepath}")
                return None
            
            info = {}
            
            with h5py.File(filepath, "r") as f:
                # Get dataset shapes
                for key in ["image", "state", "action", "force", "timestamp", 
                           "timestamp_camera", "timestamp_pose", "timestamp_force"]:
                    if key in f:
                        info[f"{key}_shape"] = f[key].shape
                
                # Get metadata
                for key in f.attrs:
                    info[key] = f.attrs[key]
            
            return info
            
        except Exception as e:
            self.logger.error(f"Failed to get episode info: {e}")
            return None
    
    @staticmethod
    def generate_filename(prefix: str = "episode", extension: str = ".hdf5") -> str:
        """
        Generate filename with timestamp
        
        Args:
            prefix: Filename prefix
            extension: File extension
            
        Returns:
            str: Generated filename
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{timestamp}{extension}"

