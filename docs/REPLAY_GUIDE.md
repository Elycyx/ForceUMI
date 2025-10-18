# Episode Replay Guide

This guide explains how to use the ForceUMI replay system to visualize previously collected episodes.

## Overview

The replay system provides synchronized visualization of all data streams collected during an episode:
- RGB camera images
- Force/torque sensor data
- State (pose) data
- Action (relative motion) data

## Quick Start

### Command-Line Tool

The simplest way to replay an episode:

```bash
forceumi-replay data/episode_20250118_143025.hdf5
```

### Python Script

Using the example script:

```bash
python examples/replay_episode.py data/episode_20250118_143025.hdf5
```

With custom configuration:

```bash
python examples/replay_episode.py data/episode_20250118_143025.hdf5 --config config.yaml
```

## Keyboard Controls

| Key | Action |
|-----|--------|
| `Space` | Play/Pause |
| `Left Arrow` | Step backward (1 frame) |
| `Right Arrow` | Step forward (1 frame) |
| `Up Arrow` | Increase playback speed (+0.5x) |
| `Down Arrow` | Decrease playback speed (-0.5x) |
| `Home` | Jump to start |
| `End` | Jump to end |
| `L` | Toggle loop mode |
| `H` | Toggle help display |
| `Q` or `ESC` | Quit |

## Display Windows

The replay system opens three synchronized windows:

### 1. Main Image Window

Displays the camera feed with overlay information:
- Current frame number and total frames
- Playback progress percentage
- Playback speed multiplier
- Loop status (ON/OFF)
- Playback status (PLAYING/PAUSED)
- Timestamp (if available)
- Keyboard shortcuts help (toggleable)

### 2. Force/Torque Plot Window

Shows two synchronized plots:
- **Top plot**: Force components (Fx, Fy, Fz) in Newtons
- **Bottom plot**: Torque components (Mx, My, Mz) in Newton-meters

The plots show a sliding window of recent frames (configurable history length).

### 3. State/Action Plot Window

Shows two synchronized plots:
- **Top plot**: State position (X, Y, Z) in meters, with gripper value on secondary axis
- **Bottom plot**: Action relative position (ΔX, ΔY, ΔZ) in meters

## Playback Controls

### Speed Control

- Playback speed can be adjusted from **0.1x** to **10x**
- Default speed is **1.0x** (real-time)
- Use `Up/Down Arrow` keys to adjust in 0.5x increments
- The target FPS is read from episode metadata

### Frame Navigation

- **Step through frames**: Use `Left/Right Arrow` keys
  - Automatically pauses playback
  - Allows detailed inspection of specific frames
- **Jump to start**: Press `Home`
- **Jump to end**: Press `End`

### Loop Mode

- Enable loop mode by pressing `L`
- When enabled, playback automatically restarts from the beginning when reaching the end
- Useful for continuous visualization of episodes

## Programmatic Usage

You can also integrate the replay system into your own Python scripts:

```python
from forceumi.replay import EpisodePlayer, ReplayWindow

# Method 1: Using ReplayWindow (with GUI)
window = ReplayWindow('data/episode.hdf5')
window.run()

# Method 2: Using EpisodePlayer (programmatic access)
player = EpisodePlayer('data/episode.hdf5')

# Get episode info
info = player.get_info()
print(f"Total frames: {info['total_frames']}")
print(f"FPS: {info['fps']}")
print(f"Duration: {info['duration']}s")

# Play frame by frame
player.play()
while player.current_frame < player.total_frames:
    frame_data = player.update()
    if frame_data is not None:
        # Process frame_data
        print(f"Frame {frame_data['frame_idx']}")
        if frame_data['image'] is not None:
            # Do something with image
            pass
```

## EpisodePlayer API

### Initialization

```python
player = EpisodePlayer(episode_path='data/episode.hdf5')
```

### Playback Control Methods

| Method | Description |
|--------|-------------|
| `play()` | Start playback |
| `pause()` | Pause playback |
| `toggle_play_pause()` | Toggle between play and pause |
| `stop()` | Stop and reset to first frame |

### Navigation Methods

| Method | Description |
|--------|-------------|
| `seek(frame_idx)` | Jump to specific frame |
| `seek_relative(delta_frames)` | Seek relative to current frame |

### Configuration Methods

| Method | Description |
|--------|-------------|
| `set_speed(speed)` | Set playback speed (0.1x - 10.0x) |
| `set_loop(loop)` | Enable/disable loop mode |

### Data Access Methods

| Method | Returns |
|--------|---------|
| `get_frame(frame_idx)` | Dict with all data for specified frame |
| `get_progress()` | Tuple: (current_frame, total_frames, progress_percentage) |
| `get_info()` | Dict with episode information |

### Update Loop

Call `update()` regularly (e.g., in a GUI loop) to advance playback:

```python
while running:
    frame_data = player.update()  # Returns None if no new frame ready
    if frame_data is not None:
        # New frame available
        process_frame(frame_data)
```

## Frame Data Structure

The `get_frame()` method returns a dictionary with the following structure:

```python
{
    'frame_idx': int,              # Frame index (0-based)
    'image': np.ndarray,           # RGB image (H, W, 3) or None
    'state': np.ndarray,           # 7D state [x,y,z,rx,ry,rz,gripper] or None
    'action': np.ndarray,          # 7D action [x,y,z,rx,ry,rz,gripper] or None
    'force': np.ndarray,           # 6D force [fx,fy,fz,mx,my,mz] or None
    'timestamp': float             # Timestamp in seconds or None
}
```

## Configuration

You can customize the replay visualization by providing a configuration dict:

```python
# Option 1: Use a dict directly
config = {
    'image_display_size': (800, 600),  # Image window size
    'plot_history': 300,                # Number of frames in plots
}

window = ReplayWindow('data/episode.hdf5', config=config)

# Option 2: Load from config file
from forceumi.config import Config
config_obj = Config('config.yaml')
window = ReplayWindow('data/episode.hdf5', config=config_obj.config)
```

## Troubleshooting

### "Episode file not found"
- Check that the file path is correct
- Use absolute paths if relative paths are not working

### "No data found in episode file"
- The HDF5 file may be corrupted
- Verify the file was saved correctly during collection

### Playback is choppy
- Try reducing the playback speed
- Close other applications to free up system resources
- The plot history length may be too large; reduce it in config

### Images are not displaying
- Check that the episode contains image data
- The image may be in an unsupported format
- Try viewing with the HDF5Manager directly

### Plots show "No Data"
- The episode may not contain that type of data (force, state, action)
- This is normal if those sensors were not connected during collection

## Tips

1. **Frame-by-frame analysis**: Pause playback and use arrow keys to step through frames
2. **Quick overview**: Use 2x-5x speed for fast scanning
3. **Detailed inspection**: Use 0.1x-0.5x speed for slow-motion analysis
4. **Loop for comparison**: Enable loop mode to repeatedly watch specific behaviors
5. **Multiple episodes**: Open multiple terminal windows to compare episodes side-by-side

## See Also

- [Data Format Documentation](../README.md#data-format)
- [Action Coordinate System](../ACTION_COORDINATE_SYSTEM.md)
- [Units and Conventions](../UNITS_AND_CONVENTIONS.md)

