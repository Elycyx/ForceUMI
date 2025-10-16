"""
Read Episode Data Example

Demonstrates how to read and process saved episode data.
"""

import sys
from pathlib import Path
import numpy as np
from forceumi.data import HDF5Manager


def print_array_stats(name: str, array: np.ndarray):
    """Print statistics for an array"""
    if len(array) == 0:
        print(f"  {name}: No data")
        return
    
    print(f"  {name}:")
    print(f"    Shape: {array.shape}")
    print(f"    Dtype: {array.dtype}")
    
    if array.dtype in [np.float32, np.float64]:
        print(f"    Mean: {np.mean(array, axis=0)}")
        print(f"    Std: {np.std(array, axis=0)}")
        print(f"    Min: {np.min(array, axis=0)}")
        print(f"    Max: {np.max(array, axis=0)}")


def main():
    """Read episode example"""
    if len(sys.argv) < 2:
        print("Usage: python read_episode.py <path_to_episode.hdf5>")
        print("\nExample:")
        print("  python read_episode.py data/episode_20250116_120000.hdf5")
        return
    
    filepath = sys.argv[1]
    
    print("ForceUMI Episode Reader")
    print("=" * 50)
    print(f"\nReading: {filepath}")
    
    # Load episode
    manager = HDF5Manager()
    data = manager.load_episode(filepath)
    
    if data is None:
        print("Error: Failed to load episode")
        return
    
    print("\n" + "=" * 50)
    print("Episode Data Summary")
    print("=" * 50)
    
    # Print metadata
    print("\nMetadata:")
    if data["metadata"]:
        for key, value in data["metadata"].items():
            print(f"  {key}: {value}")
    else:
        print("  No metadata")
    
    # Print data statistics
    print("\nData Statistics:")
    print_array_stats("Images", data["image"])
    print_array_stats("States", data["state"])
    print_array_stats("Actions", data["action"])
    print_array_stats("Forces", data["force"])
    print_array_stats("Timestamps", data["timestamp"])
    
    # Calculate additional stats
    if len(data["timestamp"]) > 1:
        timestamps = data["timestamp"]
        duration = timestamps[-1] - timestamps[0]
        fps = len(timestamps) / duration if duration > 0 else 0
        
        print(f"\nTiming Statistics:")
        print(f"  Total Frames: {len(timestamps)}")
        print(f"  Duration: {duration:.2f} seconds")
        print(f"  Average FPS: {fps:.2f}")
        print(f"  Frame Intervals: mean={np.mean(np.diff(timestamps)):.4f}s, "
              f"std={np.std(np.diff(timestamps)):.4f}s")
    
    print("\n" + "=" * 50)
    print("Done!")


if __name__ == "__main__":
    main()

