"""
Timestamp Analysis Tool

Analyzes per-sensor timestamps in collected episodes to diagnose
time synchronization issues.
"""

import sys
import h5py
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path


def analyze_timestamps(episode_path: str):
    """
    Analyze timestamps in an episode file.
    
    Args:
        episode_path: Path to HDF5 episode file
    """
    print("="*60)
    print(f"Analyzing: {episode_path}")
    print("="*60)
    
    try:
        with h5py.File(episode_path, 'r') as f:
            # Load main timestamp
            timestamps = f['timestamp'][:] if 'timestamp' in f else None
            
            # Load per-sensor timestamps
            ts_camera = f['timestamp_camera'][:] if 'timestamp_camera' in f else None
            ts_pose = f['timestamp_pose'][:] if 'timestamp_pose' in f else None
            ts_force = f['timestamp_force'][:] if 'timestamp_force' in f else None
            
            # Check if we have per-sensor timestamps
            has_persensor_ts = any([ts_camera is not None, ts_pose is not None, ts_force is not None])
            
            if not has_persensor_ts:
                print("\n⚠️  WARNING: Episode does not have per-sensor timestamps!")
                print("   This episode was collected with an older version.")
                print("   Only basic timestamp analysis available.\n")
            
            # Basic info
            print(f"\nTotal Frames: {len(timestamps) if timestamps is not None else 0}")
            
            if timestamps is not None and len(timestamps) > 1:
                duration = timestamps[-1] - timestamps[0]
                avg_fps = len(timestamps) / duration
                print(f"Duration: {duration:.2f}s")
                print(f"Average FPS: {avg_fps:.2f}")
                
                # Frame intervals
                intervals = np.diff(timestamps)
                print(f"\nFrame Intervals:")
                print(f"  Mean: {np.mean(intervals)*1000:.2f}ms")
                print(f"  Std:  {np.std(intervals)*1000:.2f}ms")
                print(f"  Min:  {np.min(intervals)*1000:.2f}ms")
                print(f"  Max:  {np.max(intervals)*1000:.2f}ms")
            
            if has_persensor_ts:
                print("\n" + "="*60)
                print("PER-SENSOR TIMESTAMP ANALYSIS")
                print("="*60)
                
                # Analyze each sensor
                sensors = {
                    'Camera': ts_camera,
                    'Pose': ts_pose,
                    'Force': ts_force
                }
                
                sensor_stats = {}
                
                for name, ts in sensors.items():
                    if ts is not None and len(ts) > 1:
                        print(f"\n{name} Sensor:")
                        print(f"  Frames: {len(ts)}")
                        
                        # Intervals
                        intervals = np.diff(ts)
                        mean_interval = np.mean(intervals) * 1000
                        std_interval = np.std(intervals) * 1000
                        
                        print(f"  Interval: {mean_interval:.2f} ± {std_interval:.2f}ms")
                        print(f"  FPS: {1000/mean_interval:.2f}")
                        
                        sensor_stats[name] = {
                            'timestamps': ts,
                            'intervals': intervals,
                            'mean_interval': mean_interval,
                            'std_interval': std_interval
                        }
                
                # Calculate inter-sensor delays
                if len(sensor_stats) > 1:
                    print("\n" + "="*60)
                    print("INTER-SENSOR SYNCHRONIZATION")
                    print("="*60)
                    
                    # Find common frames (using main timestamp as reference)
                    min_frames = min(len(timestamps), 
                                   len(ts_camera) if ts_camera is not None else float('inf'),
                                   len(ts_pose) if ts_pose is not None else float('inf'),
                                   len(ts_force) if ts_force is not None else float('inf'))
                    
                    print(f"\nAnalyzing first {min_frames} synchronized frames:")
                    
                    # Calculate delays relative to loop timestamp
                    if ts_camera is not None and len(ts_camera) >= min_frames:
                        camera_delays = (ts_camera[:min_frames] - timestamps[:min_frames]) * 1000
                        print(f"\nCamera delay (from loop start):")
                        print(f"  Mean: {np.mean(camera_delays):.2f}ms")
                        print(f"  Std:  {np.std(camera_delays):.2f}ms")
                    
                    if ts_pose is not None and len(ts_pose) >= min_frames:
                        pose_delays = (ts_pose[:min_frames] - timestamps[:min_frames]) * 1000
                        print(f"\nPose delay (from loop start):")
                        print(f"  Mean: {np.mean(pose_delays):.2f}ms")
                        print(f"  Std:  {np.std(pose_delays):.2f}ms")
                    
                    if ts_force is not None and len(ts_force) >= min_frames:
                        force_delays = (ts_force[:min_frames] - timestamps[:min_frames]) * 1000
                        print(f"\nForce delay (from loop start):")
                        print(f"  Mean: {np.mean(force_delays):.2f}ms")
                        print(f"  Std:  {np.std(force_delays):.2f}ms")
                    
                    # Calculate relative delays between sensors
                    if ts_camera is not None and ts_pose is not None:
                        min_len = min(len(ts_camera), len(ts_pose))
                        cam_pose_delay = (ts_pose[:min_len] - ts_camera[:min_len]) * 1000
                        print(f"\nPose→Camera delay:")
                        print(f"  Mean: {np.mean(cam_pose_delay):.2f}ms")
                        print(f"  Std:  {np.std(cam_pose_delay):.2f}ms")
                    
                    if ts_pose is not None and ts_force is not None:
                        min_len = min(len(ts_pose), len(ts_force))
                        pose_force_delay = (ts_force[:min_len] - ts_pose[:min_len]) * 1000
                        print(f"\nForce→Pose delay:")
                        print(f"  Mean: {np.mean(pose_force_delay):.2f}ms")
                        print(f"  Std:  {np.std(pose_force_delay):.2f}ms")
                
                # Visualization
                print("\n" + "="*60)
                print("GENERATING PLOTS...")
                print("="*60)
                
                fig, axes = plt.subplots(2, 2, figsize=(14, 10))
                fig.suptitle(f'Timestamp Analysis: {Path(episode_path).name}', fontsize=14)
                
                # Plot 1: Timeline of all sensors
                ax = axes[0, 0]
                if timestamps is not None:
                    t0 = timestamps[0]
                    ax.plot((timestamps - t0), np.arange(len(timestamps)), 'k-', 
                           label='Main Loop', linewidth=2, alpha=0.5)
                if ts_camera is not None:
                    t0 = ts_camera[0] if timestamps is None else timestamps[0]
                    ax.plot((ts_camera - t0), np.arange(len(ts_camera)), 'r.', 
                           label='Camera', markersize=3)
                if ts_pose is not None:
                    t0 = ts_pose[0] if timestamps is None else timestamps[0]
                    ax.plot((ts_pose - t0), np.arange(len(ts_pose)), 'g.', 
                           label='Pose', markersize=3)
                if ts_force is not None:
                    t0 = ts_force[0] if timestamps is None else timestamps[0]
                    ax.plot((ts_force - t0), np.arange(len(ts_force)), 'b.', 
                           label='Force', markersize=3)
                ax.set_xlabel('Time (s)')
                ax.set_ylabel('Frame Index')
                ax.set_title('Sensor Timestamps Timeline')
                ax.legend()
                ax.grid(True, alpha=0.3)
                
                # Plot 2: Inter-sensor delays
                ax = axes[0, 1]
                if 'Camera' in sensor_stats and 'Pose' in sensor_stats:
                    min_len = min(len(ts_camera), len(ts_pose))
                    delays = (ts_pose[:min_len] - ts_camera[:min_len]) * 1000
                    ax.plot(delays, label='Pose - Camera', alpha=0.7)
                if 'Pose' in sensor_stats and 'Force' in sensor_stats:
                    min_len = min(len(ts_pose), len(ts_force))
                    delays = (ts_force[:min_len] - ts_pose[:min_len]) * 1000
                    ax.plot(delays, label='Force - Pose', alpha=0.7)
                ax.set_xlabel('Frame')
                ax.set_ylabel('Delay (ms)')
                ax.set_title('Inter-Sensor Delays')
                ax.legend()
                ax.grid(True, alpha=0.3)
                
                # Plot 3: Frame intervals
                ax = axes[1, 0]
                for name, stats in sensor_stats.items():
                    ax.plot(stats['intervals'] * 1000, label=name, alpha=0.7)
                ax.set_xlabel('Frame')
                ax.set_ylabel('Interval (ms)')
                ax.set_title('Frame Intervals')
                ax.legend()
                ax.grid(True, alpha=0.3)
                
                # Plot 4: Interval histograms
                ax = axes[1, 1]
                for name, stats in sensor_stats.items():
                    ax.hist(stats['intervals'] * 1000, bins=50, alpha=0.5, label=name)
                ax.set_xlabel('Interval (ms)')
                ax.set_ylabel('Count')
                ax.set_title('Frame Interval Distribution')
                ax.legend()
                ax.grid(True, alpha=0.3)
                
                plt.tight_layout()
                
                # Save plot
                plot_path = Path(episode_path).with_suffix('.timestamp_analysis.png')
                plt.savefig(plot_path, dpi=150)
                print(f"\n✅ Plot saved to: {plot_path}")
                
                # Show plot
                plt.show()
            
    except Exception as e:
        print(f"\n❌ Error analyzing episode: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python analyze_timestamps.py <episode.hdf5>")
        print("\nExample:")
        print("  python analyze_timestamps.py data/episode_20250118_143025.hdf5")
        sys.exit(1)
    
    episode_path = sys.argv[1]
    
    if not Path(episode_path).exists():
        print(f"Error: File not found: {episode_path}")
        sys.exit(1)
    
    analyze_timestamps(episode_path)


if __name__ == '__main__':
    main()

