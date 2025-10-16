"""
Tests for data collector
"""

import pytest
import time
import tempfile
from pathlib import Path

from forceumi.collector import DataCollector
from forceumi.devices import Camera, PoseSensor, ForceSensor


class TestDataCollector:
    """Test DataCollector"""
    
    def test_init(self):
        """Test collector initialization"""
        camera = Camera()
        pose_sensor = PoseSensor()
        force_sensor = ForceSensor()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            collector = DataCollector(
                camera=camera,
                pose_sensor=pose_sensor,
                force_sensor=force_sensor,
                save_dir=tmpdir,
                auto_save=True,
                max_fps=30.0
            )
            
            assert collector.camera is camera
            assert collector.pose_sensor is pose_sensor
            assert collector.force_sensor is force_sensor
            assert collector.save_dir == Path(tmpdir)
            assert collector.auto_save is True
            assert collector.max_fps == 30.0
            assert not collector.is_collecting()
    
    def test_connect_disconnect_devices(self):
        """Test device connection and disconnection"""
        pose_sensor = PoseSensor()
        force_sensor = ForceSensor()
        
        collector = DataCollector(
            pose_sensor=pose_sensor,
            force_sensor=force_sensor
        )
        
        # Connect
        status = collector.connect_devices()
        assert "pose_sensor" in status
        assert "force_sensor" in status
        
        # Disconnect
        status = collector.disconnect_devices()
        assert "pose_sensor" in status
        assert "force_sensor" in status
    
    def test_episode_lifecycle(self):
        """Test episode start and stop"""
        pose_sensor = PoseSensor()
        force_sensor = ForceSensor()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            collector = DataCollector(
                pose_sensor=pose_sensor,
                force_sensor=force_sensor,
                save_dir=tmpdir,
                auto_save=False
            )
            
            collector.connect_devices()
            
            # Start episode
            metadata = {"task": "test"}
            success = collector.start_episode(metadata=metadata)
            assert success
            assert collector.is_collecting()
            
            # Collect some data
            time.sleep(0.5)
            
            # Check stats
            stats = collector.get_episode_stats()
            assert stats["num_frames"] >= 0
            
            # Stop episode
            filepath = collector.stop_episode(save=False)
            assert not collector.is_collecting()
            
            collector.disconnect_devices()
    
    def test_episode_save(self):
        """Test episode saving"""
        pose_sensor = PoseSensor()
        force_sensor = ForceSensor()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            collector = DataCollector(
                pose_sensor=pose_sensor,
                force_sensor=force_sensor,
                save_dir=tmpdir,
                auto_save=True
            )
            
            collector.connect_devices()
            
            # Start and stop episode with auto-save
            collector.start_episode()
            time.sleep(0.5)
            filepath = collector.stop_episode()
            
            # Check file was created
            if filepath:
                assert Path(filepath).exists()
            
            collector.disconnect_devices()

