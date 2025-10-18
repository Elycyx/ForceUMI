"""
Example: Reading Per-Sensor Timestamps

Demonstrates how to read and use per-sensor timestamps from collected episodes.
"""

import sys
import h5py
import numpy as np
from pathlib import Path


def read_with_timestamps(episode_path: str):
    """
    Read episode with per-sensor timestamps.
    
    Args:
        episode_path: Path to HDF5 episode file
    """
    print(f"Reading: {episode_path}\n")
    
    with h5py.File(episode_path, 'r') as f:
        # Read data arrays
        images = f['image'][:] if 'image' in f else None
        states = f['state'][:] if 'state' in f else None
        forces = f['force'][:] if 'force' in f else None
        
        # Read timestamps
        timestamps = f['timestamp'][:]
        
        # Check for per-sensor timestamps (v0.3.1+)
        has_per_sensor_ts = all([
            'timestamp_camera' in f,
            'timestamp_pose' in f,
            'timestamp_force' in f
        ])
        
        if has_per_sensor_ts:
            ts_camera = f['timestamp_camera'][:]
            ts_pose = f['timestamp_pose'][:]
            ts_force = f['timestamp_force'][:]
            
            print("✅ Per-sensor timestamps available!")
            print(f"\nFrames: {len(timestamps)}")
            print(f"Camera frames: {len(ts_camera)}")
            print(f"Pose frames: {len(ts_pose)}")
            print(f"Force frames: {len(ts_force)}")
            
            # Calculate delays (in milliseconds)
            min_frames = min(len(timestamps), len(ts_camera), len(ts_pose), len(ts_force))
            
            camera_delays = (ts_camera[:min_frames] - timestamps[:min_frames]) * 1000
            pose_delays = (ts_pose[:min_frames] - timestamps[:min_frames]) * 1000
            force_delays = (ts_force[:min_frames] - timestamps[:min_frames]) * 1000
            
            print(f"\n📊 Average Delays (from loop start):")
            print(f"  Camera: {np.mean(camera_delays):.2f}ms ± {np.std(camera_delays):.2f}ms")
            print(f"  Pose:   {np.mean(pose_delays):.2f}ms ± {np.std(pose_delays):.2f}ms")
            print(f"  Force:  {np.mean(force_delays):.2f}ms ± {np.std(force_delays):.2f}ms")
            
            # Inter-sensor delays
            cam_pose_delay = (ts_pose[:min_frames] - ts_camera[:min_frames]) * 1000
            pose_force_delay = (ts_force[:min_frames] - ts_pose[:min_frames]) * 1000
            
            print(f"\n⏱️  Inter-Sensor Delays:")
            print(f"  Camera → Pose: {np.mean(cam_pose_delay):.2f}ms ± {np.std(cam_pose_delay):.2f}ms")
            print(f"  Pose → Force:  {np.mean(pose_force_delay):.2f}ms ± {np.std(pose_force_delay):.2f}ms")
            
            # Example: Use camera timestamp for a specific frame
            frame_idx = len(timestamps) // 2  # Middle frame
            print(f"\n🔍 Example Frame #{frame_idx}:")
            print(f"  Loop timestamp:   {timestamps[frame_idx]:.6f}s")
            print(f"  Camera timestamp: {ts_camera[frame_idx]:.6f}s")
            print(f"  Pose timestamp:   {ts_pose[frame_idx]:.6f}s")
            print(f"  Force timestamp:  {ts_force[frame_idx]:.6f}s")
            
            # Example: Compute frame intervals
            if len(ts_camera) > 1:
                camera_intervals = np.diff(ts_camera) * 1000
                print(f"\n📷 Camera Frame Intervals:")
                print(f"  Mean: {np.mean(camera_intervals):.2f}ms")
                print(f"  Std:  {np.std(camera_intervals):.2f}ms")
                print(f"  FPS:  {1000/np.mean(camera_intervals):.2f}")
            
            # Example: Find synchronized data point
            print(f"\n🎯 Synchronized Data Example (Frame {frame_idx}):")
            if images is not None:
                print(f"  Image shape: {images[frame_idx].shape}")
            if states is not None:
                print(f"  State (pose): {states[frame_idx][:3]} (position)")
            if forces is not None:
                print(f"  Force: {forces[frame_idx][:3]} (fx, fy, fz)")
            
        else:
            print("⚠️  Per-sensor timestamps NOT available")
            print("   This episode was collected with an older version.")
            print("   Using main timestamp for all sensors.\n")
            
            print(f"Frames: {len(timestamps)}")
            if len(timestamps) > 1:
                intervals = np.diff(timestamps) * 1000
                print(f"Frame intervals: {np.mean(intervals):.2f}ms ± {np.std(intervals):.2f}ms")


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python read_timestamps.py <episode.hdf5>")
        print("\nExample:")
        print("  python read_timestamps.py data/episode_20250118_143025.hdf5")
        sys.exit(1)
    
    episode_path = sys.argv[1]
    
    if not Path(episode_path).exists():
        print(f"Error: File not found: {episode_path}")
        sys.exit(1)
    
    read_with_timestamps(episode_path)
    
    print("\n💡 Tips:")
    print("  - Run 'python analyze_timestamps.py <episode.hdf5>' for detailed analysis")
    print("  - Use per-sensor timestamps for accurate multi-modal alignment")
    print("  - Check inter-sensor delays to ensure good synchronization")


if __name__ == '__main__':
    main()

