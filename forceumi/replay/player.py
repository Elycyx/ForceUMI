"""
Episode Player for replaying collected data.

This module provides the EpisodePlayer class which loads HDF5 episode files
and allows frame-by-frame playback with various controls.
"""

import logging
import time
import numpy as np
import h5py
from typing import Optional, Dict, Any, Tuple
from pathlib import Path


class EpisodePlayer:
    """
    Player for replaying collected episodes.
    
    Loads an HDF5 episode file and provides methods for frame-by-frame playback
    with controls for speed, seeking, and looping.
    """
    
    def __init__(self, episode_path: str):
        """
        Initialize the episode player.
        
        Args:
            episode_path: Path to the HDF5 episode file
        """
        self.episode_path = Path(episode_path)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Data containers
        self.images = None
        self.states = None
        self.actions = None
        self.forces = None
        self.timestamps = None
        self.metadata = {}
        
        # Playback state
        self.current_frame = 0
        self.total_frames = 0
        self.is_playing = False
        self.playback_speed = 1.0  # 1.0 = real-time
        self.loop = False
        
        # Timing
        self.last_frame_time = 0
        self.target_fps = 30  # Default, will be overridden by metadata
        
        # Load the episode
        self._load_episode()
    
    def _load_episode(self) -> bool:
        """
        Load episode data from HDF5 file.
        
        Returns:
            True if loading successful, False otherwise
        """
        try:
            if not self.episode_path.exists():
                self.logger.error(f"Episode file not found: {self.episode_path}")
                return False
            
            self.logger.info(f"Loading episode: {self.episode_path}")
            
            with h5py.File(self.episode_path, 'r') as f:
                # Load datasets
                if 'image' in f:
                    self.images = f['image'][:]
                if 'state' in f:
                    self.states = f['state'][:]
                if 'action' in f:
                    self.actions = f['action'][:]
                if 'force' in f:
                    self.forces = f['force'][:]
                if 'timestamp' in f:
                    self.timestamps = f['timestamp'][:]
                
                # Load metadata
                if 'metadata' in f:
                    meta_group = f['metadata']
                    for key in meta_group.attrs:
                        self.metadata[key] = meta_group.attrs[key]
                
                # Also check root attributes for metadata
                for key in f.attrs:
                    if key not in self.metadata:
                        self.metadata[key] = f.attrs[key]
            
            # Determine total frames
            if self.images is not None:
                self.total_frames = len(self.images)
            elif self.states is not None:
                self.total_frames = len(self.states)
            elif self.forces is not None:
                self.total_frames = len(self.forces)
            else:
                self.logger.error("No data found in episode file")
                return False
            
            # Get FPS from metadata
            if 'fps' in self.metadata:
                self.target_fps = float(self.metadata['fps'])
            elif 'camera_fps' in self.metadata:
                self.target_fps = float(self.metadata['camera_fps'])
            
            self.logger.info(f"Loaded episode: {self.total_frames} frames, {self.target_fps} FPS")
            self.logger.info(f"Metadata: {self.metadata}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load episode: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_frame(self, frame_idx: Optional[int] = None) -> Dict[str, Any]:
        """
        Get data for a specific frame.
        
        Args:
            frame_idx: Frame index to retrieve. If None, use current frame.
        
        Returns:
            Dictionary containing frame data:
            {
                'frame_idx': int,
                'image': np.ndarray or None,
                'state': np.ndarray or None,
                'action': np.ndarray or None,
                'force': np.ndarray or None,
                'timestamp': float or None
            }
        """
        if frame_idx is None:
            frame_idx = self.current_frame
        
        # Clamp to valid range
        frame_idx = max(0, min(frame_idx, self.total_frames - 1))
        
        frame_data = {'frame_idx': frame_idx}
        
        try:
            if self.images is not None:
                frame_data['image'] = self.images[frame_idx]
            else:
                frame_data['image'] = None
            
            if self.states is not None:
                frame_data['state'] = self.states[frame_idx]
            else:
                frame_data['state'] = None
            
            if self.actions is not None:
                frame_data['action'] = self.actions[frame_idx]
            else:
                frame_data['action'] = None
            
            if self.forces is not None:
                frame_data['force'] = self.forces[frame_idx]
            else:
                frame_data['force'] = None
            
            if self.timestamps is not None:
                frame_data['timestamp'] = self.timestamps[frame_idx]
            else:
                frame_data['timestamp'] = None
            
        except Exception as e:
            self.logger.error(f"Error getting frame {frame_idx}: {e}")
        
        return frame_data
    
    def play(self):
        """Start playback."""
        self.is_playing = True
        self.last_frame_time = time.time()
        self.logger.debug("Playback started")
    
    def pause(self):
        """Pause playback."""
        self.is_playing = False
        self.logger.debug("Playback paused")
    
    def toggle_play_pause(self):
        """Toggle between play and pause."""
        if self.is_playing:
            self.pause()
        else:
            self.play()
    
    def stop(self):
        """Stop playback and reset to first frame."""
        self.is_playing = False
        self.current_frame = 0
        self.logger.debug("Playback stopped")
    
    def seek(self, frame_idx: int):
        """
        Seek to a specific frame.
        
        Args:
            frame_idx: Target frame index
        """
        self.current_frame = max(0, min(frame_idx, self.total_frames - 1))
        self.last_frame_time = time.time()
        self.logger.debug(f"Seeked to frame {self.current_frame}")
    
    def seek_relative(self, delta_frames: int):
        """
        Seek relative to current frame.
        
        Args:
            delta_frames: Number of frames to skip (positive or negative)
        """
        self.seek(self.current_frame + delta_frames)
    
    def set_speed(self, speed: float):
        """
        Set playback speed.
        
        Args:
            speed: Playback speed multiplier (1.0 = real-time, 2.0 = 2x speed, etc.)
        """
        self.playback_speed = max(0.1, min(speed, 10.0))  # Clamp to 0.1x - 10x
        self.logger.debug(f"Playback speed set to {self.playback_speed}x")
    
    def set_loop(self, loop: bool):
        """
        Enable or disable looping.
        
        Args:
            loop: If True, loop back to start when reaching end
        """
        self.loop = loop
        self.logger.debug(f"Loop {'enabled' if loop else 'disabled'}")
    
    def update(self) -> Optional[Dict[str, Any]]:
        """
        Update playback state and return current frame if ready.
        
        Should be called regularly (e.g., in GUI update loop).
        Returns frame data if a new frame should be displayed, None otherwise.
        
        Uses actual timestamps for accurate playback timing.
        
        Returns:
            Frame data dict if new frame ready, None otherwise
        """
        if not self.is_playing:
            return None
        
        current_time = time.time()
        elapsed = current_time - self.last_frame_time
        
        # Calculate required interval based on actual timestamps (if available)
        if self.timestamps is not None and self.current_frame < len(self.timestamps) - 1:
            # Use actual timestamp difference for accurate playback
            actual_interval = self.timestamps[self.current_frame + 1] - self.timestamps[self.current_frame]
            frame_interval = actual_interval / self.playback_speed
        else:
            # Fallback to FPS-based interval
            frame_interval = (1.0 / self.target_fps) / self.playback_speed
        
        if elapsed >= frame_interval:
            # Time to advance to next frame
            # Use += instead of = to avoid accumulating timing drift
            self.last_frame_time += frame_interval
            
            # If we've fallen too far behind, resync
            if current_time - self.last_frame_time > frame_interval * 2:
                self.last_frame_time = current_time
            
            frame_data = self.get_frame(self.current_frame)
            
            # Advance frame
            self.current_frame += 1
            
            # Check for end of episode
            if self.current_frame >= self.total_frames:
                if self.loop:
                    self.current_frame = 0
                    self.last_frame_time = time.time()  # Reset timing for loop
                    self.logger.debug("Looping back to start")
                else:
                    self.pause()
                    self.current_frame = self.total_frames - 1
                    self.logger.debug("Reached end of episode")
            
            return frame_data
        
        return None
    
    def get_progress(self) -> Tuple[int, int, float]:
        """
        Get playback progress.
        
        Returns:
            Tuple of (current_frame, total_frames, progress_percentage)
        """
        progress = (self.current_frame / max(1, self.total_frames - 1)) * 100
        return self.current_frame, self.total_frames, progress
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get episode information.
        
        Returns:
            Dictionary with episode info
        """
        return {
            'path': str(self.episode_path),
            'total_frames': self.total_frames,
            'fps': self.target_fps,
            'duration': self.total_frames / self.target_fps if self.target_fps > 0 else 0,
            'has_image': self.images is not None,
            'has_state': self.states is not None,
            'has_action': self.actions is not None,
            'has_force': self.forces is not None,
            'has_timestamp': self.timestamps is not None,
            'metadata': self.metadata,
            'image_shape': self.images.shape if self.images is not None else None,
        }

