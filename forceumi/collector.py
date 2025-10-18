"""
Data Collection Manager

Coordinates multi-device synchronized data acquisition.
"""

import threading
import queue
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Callable

from forceumi.devices import Camera, PoseSensor, ForceSensor
from forceumi.data import Episode, HDF5Manager
from forceumi.utils.transforms import relative_pose


class DataCollector:
    """Manages synchronized data collection from multiple devices"""
    
    def __init__(
        self,
        camera: Optional[Camera] = None,
        pose_sensor: Optional[PoseSensor] = None,
        force_sensor: Optional[ForceSensor] = None,
        save_dir: str = "./data",
        auto_save: bool = True,
        max_fps: float = 30.0,
        warmup_duration: float = 2.0
    ):
        """
        Initialize data collector
        
        Args:
            camera: Camera device instance
            pose_sensor: Pose sensor device instance
            force_sensor: Force sensor device instance
            save_dir: Directory to save episodes
            auto_save: Whether to automatically save episodes
            max_fps: Maximum collection framerate
            warmup_duration: Warmup duration in seconds before actual collection starts
        """
        self.camera = camera
        self.pose_sensor = pose_sensor
        self.force_sensor = force_sensor
        self.save_dir = Path(save_dir)
        self.auto_save = auto_save
        self.max_fps = max_fps
        self.warmup_duration = warmup_duration
        
        self.hdf5_manager = HDF5Manager()
        self.current_episode = None
        self.logger = logging.getLogger("forceumi.DataCollector")
        
        # Collection state
        self._collecting = False
        self._warming_up = False
        self._warmup_start_time = None
        self._collection_thread = None
        self._stop_event = threading.Event()
        
        # Reference pose for action calculation (first valid frame)
        self._reference_pose = None
        
        # Data queue for thread communication
        self._data_queue = queue.Queue(maxsize=100)
        
        # Callbacks
        self._frame_callbacks = []
        
        # Create save directory
        self.save_dir.mkdir(parents=True, exist_ok=True)
    
    def connect_devices(self) -> Dict[str, bool]:
        """
        Connect all devices
        
        Returns:
            dict: Connection status for each device
        """
        status = {}
        
        if self.camera is not None:
            status["camera"] = self.camera.connect()
        
        if self.pose_sensor is not None:
            status["pose_sensor"] = self.pose_sensor.connect()
        
        if self.force_sensor is not None:
            status["force_sensor"] = self.force_sensor.connect()
        
        self.logger.info(f"Device connection status: {status}")
        return status
    
    def disconnect_devices(self) -> Dict[str, bool]:
        """
        Disconnect all devices
        
        Returns:
            dict: Disconnection status for each device
        """
        status = {}
        
        if self.camera is not None:
            status["camera"] = self.camera.disconnect()
        
        if self.pose_sensor is not None:
            status["pose_sensor"] = self.pose_sensor.disconnect()
        
        if self.force_sensor is not None:
            status["force_sensor"] = self.force_sensor.disconnect()
        
        self.logger.info(f"Device disconnection status: {status}")
        return status
    
    def start_episode(self, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Start a new collection episode
        
        Args:
            metadata: Optional metadata for the episode
            
        Returns:
            bool: True if episode started successfully
        """
        if self._collecting:
            self.logger.warning("Already collecting data")
            return False
        
        # Create new episode
        self.current_episode = Episode()
        if metadata:
            self.current_episode.metadata.update(metadata)
        
        # Reset reference pose for new episode
        self._reference_pose = None
        
        # Start collection thread with warmup
        self._stop_event.clear()
        self._collecting = True
        self._warming_up = True
        self._warmup_start_time = time.time()
        self._collection_thread = threading.Thread(target=self._collection_loop, daemon=True)
        self._collection_thread.start()
        
        self.logger.info(f"Episode collection started (warmup: {self.warmup_duration}s)")
        return True
    
    def stop_episode(self, save: Optional[bool] = None) -> Optional[str]:
        """
        Stop current episode collection
        
        Args:
            save: Whether to save episode (defaults to auto_save setting)
            
        Returns:
            str: Path to saved file if saved, None otherwise
        """
        if not self._collecting:
            self.logger.warning("Not currently collecting data")
            return None
        
        # Stop collection
        self._stop_event.set()
        self._collecting = False
        
        if self._collection_thread is not None:
            self._collection_thread.join(timeout=2.0)
        
        # Finalize episode
        if self.current_episode:
            self.current_episode.finalize()
        
        self.logger.info("Episode collection stopped")
        
        # Save episode
        save = save if save is not None else self.auto_save
        if save and self.current_episode:
            return self.save_current_episode()
        
        return None
    
    def save_current_episode(self, filepath: Optional[str] = None) -> Optional[str]:
        """
        Save current episode to HDF5 file
        
        Args:
            filepath: Optional custom filepath
            
        Returns:
            str: Path to saved file or None if save failed
        """
        if self.current_episode is None:
            self.logger.warning("No episode to save")
            return None
        
        if filepath is None:
            filename = HDF5Manager.generate_filename()
            filepath = str(self.save_dir / filename)
        
        data = self.current_episode.to_dict()
        success = self.hdf5_manager.save_episode(filepath, data)
        
        if success:
            self.logger.info(f"Episode saved to {filepath}")
            return filepath
        else:
            self.logger.error("Failed to save episode")
            return None
    
    def _collection_loop(self):
        """Main collection loop running in separate thread"""
        frame_interval = 1.0 / self.max_fps
        
        while not self._stop_event.is_set():
            start_time = time.time()
            
            # Check if warmup period is complete
            if self._warming_up:
                elapsed_warmup = time.time() - self._warmup_start_time
                if elapsed_warmup >= self.warmup_duration:
                    self._warming_up = False
                    self.logger.info("Warmup complete, starting data collection")
            
            # Read from all devices
            frame_data = {}
            timestamp = time.time()
            
            if self.camera and self.camera.is_connected():
                image = self.camera.read()
                if image is not None:
                    frame_data["image"] = image
            
            if self.pose_sensor and self.pose_sensor.is_connected():
                state = self.pose_sensor.read()
                if state is not None:
                    frame_data["state"] = state
                    
                    # Compute action as relative pose from first frame
                    if self._reference_pose is None:
                        # First valid frame: set as reference and action is zero pose
                        self._reference_pose = state.copy()
                        # Action for first frame is zero (tracker at reference frame)
                        action = state.copy()
                        action[:6] = 0.0  # Zero position and orientation
                        # Keep gripper value (always absolute)
                        frame_data["action"] = action
                        self.logger.info(f"Reference pose set: {self._reference_pose[:6]}")
                    else:
                        # Subsequent frames: compute relative pose
                        action = relative_pose(state, self._reference_pose, preserve_gripper=True)
                        frame_data["action"] = action
            
            if self.force_sensor and self.force_sensor.is_connected():
                force = self.force_sensor.read()
                if force is not None:
                    frame_data["force"] = force
            
            # Add frame to episode (only after warmup)
            if frame_data:
                if not self._warming_up:
                    # Only save data after warmup is complete
                    self.current_episode.add_frame(
                        image=frame_data.get("image"),
                        state=frame_data.get("state"),
                        action=frame_data.get("action"),
                        force=frame_data.get("force"),
                        timestamp=timestamp
                    )
                
                # Always put data in queue for GUI updates (even during warmup)
                # Add warmup flag to frame data
                frame_data["_warming_up"] = self._warming_up
                try:
                    self._data_queue.put_nowait(frame_data)
                except queue.Full:
                    pass  # Skip if queue is full
                
                # Call callbacks
                for callback in self._frame_callbacks:
                    try:
                        callback(frame_data)
                    except Exception as e:
                        self.logger.error(f"Callback error: {e}")
            
            # Maintain framerate
            elapsed = time.time() - start_time
            sleep_time = frame_interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    def get_latest_frame(self, timeout: float = 0.1) -> Optional[Dict[str, Any]]:
        """
        Get latest frame data from queue
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            dict: Frame data or None if no data available
        """
        try:
            return self._data_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def add_frame_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """
        Add callback to be called for each frame
        
        Args:
            callback: Function to call with frame data
        """
        self._frame_callbacks.append(callback)
    
    def is_collecting(self) -> bool:
        """
        Check if currently collecting data
        
        Returns:
            bool: True if collecting
        """
        return self._collecting
    
    def is_warming_up(self) -> bool:
        """
        Check if currently in warmup phase
        
        Returns:
            bool: True if warming up
        """
        return self._warming_up
    
    def get_warmup_progress(self) -> float:
        """
        Get warmup progress
        
        Returns:
            float: Progress from 0.0 to 1.0, or 0.0 if not warming up
        """
        if not self._warming_up or self._warmup_start_time is None:
            return 0.0
        
        elapsed = time.time() - self._warmup_start_time
        return min(elapsed / self.warmup_duration, 1.0)
    
    def get_episode_stats(self) -> Dict[str, Any]:
        """
        Get statistics for current episode
        
        Returns:
            dict: Episode statistics
        """
        if self.current_episode is None:
            return {}
        
        stats = {
            "num_frames": len(self.current_episode),
            "duration": time.time() - self.current_episode.start_time if self.current_episode.start_time else 0,
            "metadata": self.current_episode.metadata,
            "warming_up": self._warming_up,
        }
        
        # Add warmup progress if in warmup phase
        if self._warming_up:
            stats["warmup_progress"] = self.get_warmup_progress()
            stats["warmup_remaining"] = max(0, self.warmup_duration - (time.time() - self._warmup_start_time))
        
        return stats
    
    def __enter__(self):
        """Context manager support"""
        self.connect_devices()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager support"""
        if self._collecting:
            self.stop_episode()
        self.disconnect_devices()
        return False

