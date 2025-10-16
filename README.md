# ForceUMI Data Collection System

ForceUMI is a comprehensive data collection system for robotic arm devices, supporting synchronized acquisition of RGB images, 6DOF poses, actions, and force sensor data.

## Features

- 📸 **Multi-modal Data Collection**: RGB fisheye camera, UMI pose (6DOF), action (delta pose), force (6-axis force sensor)
- 💾 **HDF5 Storage**: Efficient data storage format with compression and fast access
- 🎨 **Real-time Visualization**: Complete GUI interface with live image display, force curves, and pose data
- 🔄 **Continuous Collection**: Episode-based mode with independent saving
- ⚙️ **Flexible Configuration**: YAML configuration file support for different scenarios

## Installation

### From Source

```bash
git clone https://github.com/yourusername/forceumi.git
cd forceumi
pip install -e .
```

This will install the package in editable mode along with all dependencies.

### Optional: VR Tracking Support

For VR tracker-based pose sensing (using PyTracker):

```bash
pip install git+https://github.com/Elycyx/PyTracker.git
```

**Note**: Requires SteamVR and compatible VR hardware. See [PyTracker Setup Guide](docs/PYTRACKER_SETUP.md) for details.

## Quick Start

### 1. Launch GUI Collection Program

```bash
python forceumi/gui/main_window.py
```

Or use the command-line tool:

```bash
forceumi-collect
```

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

## Data Format

Each episode is saved as an HDF5 file with the following structure:

```
episode_<timestamp>.hdf5
├── /image           # shape: (N, H, W, 3), dtype: uint8
├── /state           # shape: (N, 7), dtype: float32, [x,y,z,rx,ry,rz,gripper]
├── /action          # shape: (N, 7), dtype: float32, [dx,dy,dz,drx,dry,drz,gripper]
├── /force           # shape: (N, 6), dtype: float32, [fx,fy,fz,mx,my,mz]
├── /timestamp       # shape: (N,), dtype: float64
└── /metadata        # attributes: fps, duration, task_description, etc.

Note: gripper value is always absolute (not delta)
```

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
│   ├── gui/              # Graphical interface
│   │   ├── __init__.py
│   │   ├── main_window.py
│   │   ├── widgets.py
│   │   └── visualizers.py
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


