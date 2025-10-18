"""
Tests for data management modules
"""

import pytest
import numpy as np
import tempfile
from pathlib import Path

from forceumi.data import Episode, HDF5Manager


class TestEpisode:
    """Test Episode data container"""
    
    def test_init(self):
        """Test episode initialization"""
        episode = Episode()
        assert len(episode) == 0
        assert episode.start_time is not None
        assert episode.end_time is None
    
    def test_add_frame(self):
        """Test adding frames to episode"""
        episode = Episode()
        
        image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        state = np.random.randn(7).astype(np.float32)
        action = np.random.randn(7).astype(np.float32)
        force = np.random.randn(6).astype(np.float32)
        
        episode.add_frame(image=image, state=state, action=action, force=force,
                         timestamp_camera=1.0, timestamp_pose=1.01, timestamp_force=1.02)
        
        assert len(episode) == 1
        assert len(episode.images) == 1
        assert len(episode.states) == 1
        assert len(episode.actions) == 1
        assert len(episode.forces) == 1
        assert len(episode.timestamps) == 1
        assert len(episode.timestamps_camera) == 1
        assert len(episode.timestamps_pose) == 1
        assert len(episode.timestamps_force) == 1
    
    def test_finalize(self):
        """Test episode finalization"""
        episode = Episode()
        
        for _ in range(10):
            episode.add_frame(
                image=np.zeros((480, 640, 3), dtype=np.uint8),
                state=np.zeros(7, dtype=np.float32),
                action=np.zeros(7, dtype=np.float32),
                force=np.zeros(6, dtype=np.float32),
            )
        
        episode.finalize()
        
        assert episode.end_time is not None
        assert "duration" in episode.metadata
        assert "num_frames" in episode.metadata
        assert "fps" in episode.metadata
        assert episode.metadata["num_frames"] == 10
    
    def test_to_dict(self):
        """Test conversion to dictionary"""
        episode = Episode()
        
        episode.add_frame(
            image=np.zeros((480, 640, 3), dtype=np.uint8),
            state=np.zeros(7, dtype=np.float32),
            action=np.zeros(7, dtype=np.float32),
            force=np.zeros(6, dtype=np.float32),
        )
        
        data = episode.to_dict()
        
        assert "image" in data
        assert "state" in data
        assert "action" in data
        assert "force" in data
        assert "timestamp" in data
        assert "metadata" in data


class TestHDF5Manager:
    """Test HDF5 file manager"""
    
    def test_init(self):
        """Test manager initialization"""
        manager = HDF5Manager()
        assert manager.compression == "gzip"
        assert manager.compression_level == 4
    
    def test_save_and_load(self):
        """Test saving and loading episodes"""
        manager = HDF5Manager()
        
        # Create test data
        data = {
            "image": np.random.randint(0, 255, (10, 480, 640, 3), dtype=np.uint8),
            "state": np.random.randn(10, 7).astype(np.float32),
            "action": np.random.randn(10, 7).astype(np.float32),
            "force": np.random.randn(10, 6).astype(np.float32),
            "timestamp": np.arange(10, dtype=np.float64),
            "metadata": {
                "task": "test",
                "duration": 1.0,
                "fps": 10.0,
            }
        }
        
        # Save to temporary file
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test_episode.hdf5"
            
            success = manager.save_episode(str(filepath), data)
            assert success
            assert filepath.exists()
            
            # Load and verify
            loaded_data = manager.load_episode(str(filepath))
            assert loaded_data is not None
            
            assert np.array_equal(loaded_data["image"], data["image"])
            assert np.allclose(loaded_data["state"], data["state"])
            assert np.allclose(loaded_data["action"], data["action"])
            assert np.allclose(loaded_data["force"], data["force"])
            assert np.allclose(loaded_data["timestamp"], data["timestamp"])
            assert loaded_data["metadata"]["task"] == "test"
    
    def test_generate_filename(self):
        """Test filename generation"""
        filename = HDF5Manager.generate_filename()
        assert filename.startswith("episode_")
        assert filename.endswith(".hdf5")
        
        filename = HDF5Manager.generate_filename(prefix="test", extension=".h5")
        assert filename.startswith("test_")
        assert filename.endswith(".h5")

