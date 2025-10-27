# ForceUMI Data Collection System

ForceUMI is a comprehensive data collection system for robotic arm devices, supporting synchronized acquisition of RGB images, 6DOF poses, actions, and force sensor data.

## Features

- 📸 **Multi-modal Data Collection**: RGB fisheye camera, UMI pose (6DOF), action (delta pose), force (6-axis force sensor)
- 💾 **HDF5 Storage**: Efficient data storage format with compression and fast access
- 🎨 **Real-time Visualization**: OpenCV-based GUI with live image display, force curves, and pose data (no Qt conflicts)
- 🔄 **Continuous Collection**: Episode-based mode with independent saving
- ⚙️ **Flexible Configuration**: YAML configuration file support for different scenarios

## Installation

### From Source

```bash
conda create -n forceumi python=3.10
conda activate forceumi
git clone https://github.com/Elycyx/ForceUMI.git
cd ForceUMI
pip install -e .
```

This will install the package in editable mode along with all dependencies.

### Hardware Support

**For VR tracker-based pose sensing** (using PyTracker):

```bash
git clone https://github.com/Elycyx/PyTracker.git
cd PyTracker
pip install -e .
cd ..
```
**Note**: Requires SteamVR and compatible VR hardware. See [PyTracker Setup Guide](docs/PYTRACKER_SETUP.md) for details.

**For Sunrise force sensor** (using PyForce):

```bash
git clone https://github.com/Elycyx/PyForce.git
cd PyForce
pip install -e .
cd ..
```

**Note**: Requires Sunrise (宇立) 6-axis force/torque sensor connected via TCP/IP. See [PyForce Setup Guide](docs/PYFORCE_SETUP.md) for details.

## Quick Start

### 1. Launch GUI Collection Program

```bash
python -m forceumi.gui.cv_main_window
```

Or use the example launcher:

```bash
python examples/launch_gui.py
```

Or use the command-line tool:

```bash
forceumi-collect
```

**Keyboard Controls:**
- `C` - Connect devices
- `D` - Disconnect devices
- `S` - Start collection
- `E` - Stop/Save episode
- `Q` - Quit application

### 2. Programmatic Usage

```python
from forceumi.collector import DataCollector
from forceumi.devices import Camera, PoseSensor, ForceSensor

# Initialize devices
camera = Camera()
pose_sensor = PoseSensor()
force_sensor = ForceSensor()

# Create collector
collector = DataCollector(
    camera=camera,
    pose_sensor=pose_sensor,
    force_sensor=force_sensor,
    save_dir="./data"
)

# Start episode
collector.start_episode()

# ... collect data ...

# Stop and save
collector.stop_episode()
```

### 3. Read HDF5 Data

```python
from forceumi.data import HDF5Manager

# Load episode
manager = HDF5Manager()
data = manager.load_episode("data/episode_20250101_120000.hdf5")

print(f"Images: {data['image'].shape}")
print(f"States: {data['state'].shape}")
print(f"Actions: {data['action'].shape}")
print(f"Forces: {data['force'].shape}")
print(f"Timestamps: {data['timestamp'].shape}")
print(f"Metadata: {data['metadata']}")
```

### 4. Replay Collected Episodes

Visualize previously collected episodes with synchronized playback:

```bash
# Using the command-line tool
forceumi-replay data/episode_20250101_120000.hdf5

# Or using Python script
python examples/replay_episode.py data/episode_20250101_120000.hdf5
```

**Keyboard Controls:**
- `Space` - Play/Pause
- `Left/Right Arrow` - Step backward/forward (1 frame)
- `Up/Down Arrow` - Increase/decrease playback speed
- `Home` - Jump to start
- `End` - Jump to end
- `L` - Toggle loop
- `H` - Toggle help display
- `Q` or `ESC` - Quit

The replay window shows:
- **Main image display** with playback controls and status
- **Force/Torque plots** showing the 6-axis sensor data history
- **State/Action plots** showing pose and motion data

### 5. Analyze Time Synchronization

Check the quality of time synchronization in your collected data:

```bash
python analyze_timestamps.py data/episode_20250101_120000.hdf5
```

This tool provides:
- Per-sensor frame rates and intervals
- Inter-sensor delay analysis
- Timing jitter statistics
- Visualization plots of timestamp quality

### 6. Convert to LeRobot Format

Convert ForceUMI data to LeRobot format for robot learning:

```bash
# Install LeRobot (in a separate environment)
conda create -n lerobot python=3.10
conda activate lerobot
pip install lerobot

# Convert a session (basic)
python convert_forceumi_to_lerobot.py \
  --data_dir data/session_20250118_143000 \
  --output_repo_id username/forceumi-task1 \
  --task "Pick and place task" \
  --target_size 224 224

# Fast conversion with parallel processing (5-10x faster)
python convert_forceumi_to_lerobot.py \
  --data_dir data/session_20250118_143000 \
  --output_repo_id username/forceumi-task1 \
  --task "Pick and place task" \
  --target_size 224 224 \
  --num_workers 8 \
  --parallel_episodes 4

# Convert and push to HuggingFace Hub
python convert_forceumi_to_lerobot.py \
  --data_dir data/session_20250118_143000 \
  --output_repo_id username/forceumi-task1 \
  --task "Pick and place task" \
  --target_size 224 224 \
  --skip_frames 5 \
  --num_workers 8 \
  --parallel_episodes 4 \
  --push_to_hub
```

See [LeRobot Conversion Guide](docs/LEROBOT_CONVERSION.md) and [Parallel Conversion Guide](docs/PARALLEL_CONVERSION.md) for complete documentation.

## Data Organization

### Session-Based Storage (v0.3.2+)

Episodes are organized by session for better data management:

```
data/
├── session_20250118_143000/
│   ├── episode0.hdf5
│   ├── episode1.hdf5
│   ├── episode2.hdf5
│   └── ...
├── session_20250118_150530/
│   ├── episode0.hdf5
│   └── ...
└── ...
```

- **Session**: Created when you first start collecting in a program run
- **Episodes**: Numbered sequentially within each session (episode0, episode1, ...)
- **Benefits**: Easy to identify and batch process episodes from the same data collection session

See [Session Organization Guide](SESSION_ORGANIZATION.md) for details.

## Data Format

Each episode is saved as an HDF5 file with the following structure:

```
episode_<timestamp>.hdf5
├── /image              # shape: (N, H, W, 3), dtype: uint8
├── /state              # shape: (N, 7), dtype: float32
├── /action             # shape: (N, 7), dtype: float32
├── /force              # shape: (N, 6), dtype: float32
├── /timestamp          # shape: (N,), dtype: float64 (main loop timestamp)
├── /timestamp_camera   # shape: (N,), dtype: float64 (camera-specific)
├── /timestamp_pose     # shape: (N,), dtype: float64 (pose-specific)
├── /timestamp_force    # shape: (N,), dtype: float64 (force-specific)
└── /metadata           # attributes: fps, duration, task_description, etc.
```

**Note on Timestamps**: Each sensor has its own timestamp recorded immediately after data acquisition. This provides accurate temporal information for each modality and enables precise time synchronization analysis.

### Data Definitions:

- **state**: Tracker pose relative to station (base) coordinate system
  - Format: `[x, y, z, rx, ry, rz, gripper]`
  - Position (x,y,z) in meters
  - Orientation (rx,ry,rz) as Euler angles in radians
  - Gripper value (0.0 = closed, 1.0 = open, always absolute)

- **action**: Tracker pose relative to the first frame's coordinate system
  - Format: `[x, y, z, rx, ry, rz, gripper]`
  - Position and orientation are relative to the first frame
  - First frame action is `[0, 0, 0, 0, 0, 0, gripper]`
  - Subsequent frames express the pose transformation from the first frame
  - Gripper value is always absolute (same as state)
  
- **force**: 6-axis force/torque data
  - Format: `[fx, fy, fz, mx, my, mz]`
  - Forces (fx,fy,fz) in Newtons
  - Torques (mx,my,mz) in Newton-meters

**Note**: The gripper value in both state and action is always absolute (not delta)

## Configuration File

Create a `config.yaml` configuration file:

```yaml
devices:
  camera:
    device_id: 0
    width: 640
    height: 480
    fps: 30
  
  pose_sensor:
    port: /dev/ttyUSB0
    baudrate: 115200
  
  force_sensor:
    port: /dev/ttyUSB1
    baudrate: 115200

data:
  save_dir: ./data
  compression: gzip
  compression_level: 4

gui:
  window_title: "ForceUMI Data Collection"
  image_display_size: [640, 480]
  force_plot_length: 500
```

## Project Structure

```
forceumi/
├── forceumi/              # Main package
│   ├── __init__.py
│   ├── devices/          # Device interfaces
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── camera.py
│   │   ├── pose_sensor.py
│   │   └── force_sensor.py
│   ├── data/             # Data management
│   │   ├── __init__.py
│   │   ├── hdf5_manager.py
│   │   └── episode.py
│   ├── gui/              # Graphical interface (OpenCV-based)
│   │   ├── __init__.py
│   │   ├── cv_main_window.py
│   │   └── cv_visualizer.py
│   ├── replay/           # Episode replay
│   │   ├── __init__.py
│   │   ├── player.py     # Episode player
│   │   └── replay_window.py  # Replay GUI
│   ├── utils/            # Utility functions
│   │   ├── __init__.py
│   │   └── transforms.py # Coordinate transformations
│   ├── collector.py      # Collection manager
│   └── config.py         # Configuration management
├── examples/             # Example scripts
├── tests/                # Tests
├── requirements.txt
├── setup.py
└── README.md
```

## Development Guide

### Adding New Devices

1. Create a new device class in `forceumi/devices/`
2. Inherit from `BaseDevice` base class
3. Implement required methods: `connect()`, `disconnect()`, `read()`, `is_connected()`

```python
from forceumi.devices.base import BaseDevice

class MyDevice(BaseDevice):
    def connect(self):
        # Implement connection logic
        pass
    
    def disconnect(self):
        # Implement disconnection logic
        pass
    
    def read(self):
        # Implement read logic
        return data
    
    def is_connected(self):
        # Return connection status
        return True
```

## GUI System

The system uses **OpenCV's highgui** module for visualization instead of PyQt to avoid Qt backend conflicts between OpenCV and PyQt. This provides:

- ✅ **No Qt Conflicts**: Uses OpenCV's built-in Qt backend
- ✅ **Lightweight**: Minimal dependencies
- ✅ **Cross-platform**: Works on Linux, macOS, and Windows
- ✅ **Keyboard Control**: Simple keyboard shortcuts for all operations

### GUI Windows

1. **Main View**: Displays real-time camera feed with status overlay
2. **Force Data**: Shows force and torque plots
3. **State Data**: Displays current pose and gripper state
4. **Control Panel**: Shows status and keyboard shortcuts

### Technical Details

- Uses `cv2.imshow()` for image display
- Uses `matplotlib` with `Agg` backend for plot rendering
- All plots are rendered to images and displayed via OpenCV
- Event loop uses `cv2.waitKey()` for keyboard input


