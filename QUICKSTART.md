# ForceUMI Quick Start Guide

Get started with ForceUMI data collection in 5 minutes!

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/forceumi.git
cd forceumi

# Install in editable mode with all dependencies
pip install -e .
```

## Option 1: GUI Mode (Recommended for Beginners)

### Step 1: Launch the GUI

```bash
python -m forceumi.gui.main_window
```

Or use the example script:

```bash
python examples/launch_gui.py
```

### Step 2: Connect Devices

1. Click "Connect All" in the Device panel
2. Check that all device indicators turn green
3. If a device fails to connect, check your configuration

### Step 3: Collect Data

1. Enter a task description (optional)
2. Click "Start Episode" to begin collecting
3. You'll see:
   - Real-time camera feed
   - Live force sensor data graphs
   - Current pose/state values
4. Click "Stop Episode" when done
5. Data is automatically saved to `./data/`

### Step 4: View Your Data

```bash
python examples/read_episode.py data/episode_YYYYMMDD_HHMMSS.hdf5
```

## Option 2: Programmatic Mode

### Basic Collection Script

```python
from forceumi.collector import DataCollector
from forceumi.devices import Camera, PoseSensor, ForceSensor
import time

# Initialize devices
camera = Camera(device_id=0)
pose_sensor = PoseSensor()
force_sensor = ForceSensor()

# Create collector
collector = DataCollector(
    camera=camera,
    pose_sensor=pose_sensor,
    force_sensor=force_sensor,
    save_dir="./data"
)

# Connect and collect
with collector:
    print("Starting collection...")
    collector.start_episode(metadata={"task": "my_first_task"})
    
    time.sleep(10)  # Collect for 10 seconds
    
    filepath = collector.stop_episode()
    print(f"Data saved to: {filepath}")
```

Save as `my_collection.py` and run:

```bash
python my_collection.py
```

## Configuration

Create a `config.yaml` file for custom settings:

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
  auto_save: true
```

Copy the example config:

```bash
cp examples/config_example.yaml config.yaml
```

## Data Format

Each episode is saved as an HDF5 file containing:

- `image`: RGB images (N, H, W, 3)
- `state`: 7D states (N, 7) - [x, y, z, rx, ry, rz, gripper]
- `action`: 7D actions (N, 7) - [dx, dy, dz, drx, dry, drz, gripper]
  - Note: gripper is always absolute value (not delta)
- `force`: 6-axis forces (N, 6) - [fx, fy, fz, mx, my, mz]
- `timestamp`: Timestamps (N,)
- `metadata`: Episode information

## Troubleshooting

### Camera Not Found

```python
# List available cameras
import cv2
for i in range(10):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        print(f"Camera found at index {i}")
        cap.release()
```

### Serial Port Issues

```bash
# List serial ports
ls /dev/ttyUSB*

# Check permissions
sudo chmod 666 /dev/ttyUSB0
```

### Import Errors

```bash
# Reinstall package and dependencies
pip install -e .
```

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore [examples/](examples/) for more use cases
- Check [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines
- Customize device classes for your specific hardware

## Need Help?

- Open an issue on GitHub
- Check the examples directory
- Review the API documentation in docstrings

Happy collecting! 🚀

