"""
Episode Data Container

Manages data for a single collection episode.
"""

import numpy as np
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import time


@dataclass
class Episode:
    """Container for a single data collection episode"""
    
    images: List[np.ndarray] = field(default_factory=list)
    states: List[np.ndarray] = field(default_factory=list)
    actions: List[np.ndarray] = field(default_factory=list)
    forces: List[np.ndarray] = field(default_factory=list)
    timestamps: List[float] = field(default_factory=list)
    
    # Per-sensor timestamps for better synchronization
    timestamps_camera: List[float] = field(default_factory=list)
    timestamps_pose: List[float] = field(default_factory=list)
    timestamps_force: List[float] = field(default_factory=list)
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    
    def __post_init__(self):
        """Initialize episode with start time"""
        if self.start_time is None:
            self.start_time = time.time()
    
    def add_frame(
        self,
        image: Optional[np.ndarray] = None,
        state: Optional[np.ndarray] = None,
        action: Optional[np.ndarray] = None,
        force: Optional[np.ndarray] = None,
        timestamp: Optional[float] = None,
        timestamp_camera: Optional[float] = None,
        timestamp_pose: Optional[float] = None,
        timestamp_force: Optional[float] = None
    ):
        """
        Add a frame of data to the episode
        
        Args:
            image: RGB image (H, W, 3)
            state: 7D state [x, y, z, rx, ry, rz, gripper]
            action: 7D action [dx, dy, dz, drx, dry, drz, gripper]
                   Note: gripper is always absolute value
            force: 6-axis force [fx, fy, fz, mx, my, mz]
            timestamp: Main timestamp (defaults to current time)
            timestamp_camera: Camera-specific timestamp
            timestamp_pose: Pose sensor-specific timestamp
            timestamp_force: Force sensor-specific timestamp
        """
        if timestamp is None:
            timestamp = time.time()
        
        if image is not None:
            self.images.append(image)
            self.timestamps_camera.append(timestamp_camera if timestamp_camera is not None else timestamp)
        if state is not None:
            self.states.append(state)
            self.timestamps_pose.append(timestamp_pose if timestamp_pose is not None else timestamp)
        if action is not None:
            self.actions.append(action)
        if force is not None:
            self.forces.append(force)
            self.timestamps_force.append(timestamp_force if timestamp_force is not None else timestamp)
        
        self.timestamps.append(timestamp)
    
    def finalize(self):
        """Mark episode as complete"""
        self.end_time = time.time()
        
        # Update metadata
        self.metadata.update({
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.end_time - self.start_time,
            "num_frames": len(self.timestamps),
            "fps": len(self.timestamps) / (self.end_time - self.start_time) if self.end_time > self.start_time else 0,
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert episode to dictionary format
        
        Returns:
            dict: Episode data as numpy arrays
        """
        data = {
            "image": np.array(self.images) if self.images else np.array([]),
            "state": np.array(self.states) if self.states else np.array([]),
            "action": np.array(self.actions) if self.actions else np.array([]),
            "force": np.array(self.forces) if self.forces else np.array([]),
            "timestamp": np.array(self.timestamps) if self.timestamps else np.array([]),
            "metadata": self.metadata,
        }
        
        # Add per-sensor timestamps if available
        if self.timestamps_camera:
            data["timestamp_camera"] = np.array(self.timestamps_camera)
        if self.timestamps_pose:
            data["timestamp_pose"] = np.array(self.timestamps_pose)
        if self.timestamps_force:
            data["timestamp_force"] = np.array(self.timestamps_force)
        
        return data
    
    def clear(self):
        """Clear all data from episode"""
        self.images.clear()
        self.states.clear()
        self.actions.clear()
        self.forces.clear()
        self.timestamps.clear()
        self.timestamps_camera.clear()
        self.timestamps_pose.clear()
        self.timestamps_force.clear()
        self.metadata.clear()
        self.start_time = time.time()
        self.end_time = None
    
    def __len__(self) -> int:
        """Return number of frames in episode"""
        return len(self.timestamps)
    
    def __repr__(self) -> str:
        return (f"<Episode(frames={len(self)}, "
                f"duration={self.metadata.get('duration', 0):.2f}s)>")

