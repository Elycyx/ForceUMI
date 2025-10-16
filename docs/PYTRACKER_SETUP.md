# PyTracker Setup Guide

This guide explains how to set up PyTracker for use with ForceUMI's pose sensor.

## What is PyTracker?

[PyTracker](https://github.com/Elycyx/PyTracker) is a Python wrapper for OpenVR tracking systems that provides easy access to VR device tracking data from SteamVR. ForceUMI uses it to capture 6DOF pose data from VR trackers.

## Prerequisites

1. **SteamVR**: Must be installed and running
2. **VR Hardware**: At least one VR tracker (e.g., HTC Vive Tracker, Tundra Tracker)
3. **Base Stations**: Properly set up and calibrated for room-scale tracking

## Installation

### Step 1: Install SteamVR

1. Install Steam from https://store.steampowered.com/
2. Install SteamVR from the Steam library
3. Set up your VR base stations and trackers
4. Run SteamVR to ensure tracking is working

### Step 2: Install PyTracker

```bash
pip install git+https://github.com/Elycyx/PyTracker.git
```

### Step 3: Verify Installation

```bash
python -c "import pytracker; print('PyTracker installed successfully')"
```

## Configuration

### Finding Your Devices

First, discover what devices are available:

```python
import pytracker

tracker = pytracker.Tracker()
tracker.print_discovered_objects()
```

This will output something like:

```
Index: 0 | Type: HMD | Serial: XXX-XXXXXXXX | Class: TrackedDeviceClass_HMD
Index: 1 | Type: Tracking Reference | Serial: LHB-XXXXXXXX | Class: TrackedDeviceClass_TrackingReference
Index: 2 | Type: Controller | Serial: XXX-XXXXXXXX | Class: TrackedDeviceClass_Controller
Index: 3 | Type: Tracker | Serial: LHR-XXXXXXXX | Class: TrackedDeviceClass_GenericTracker
```

### Creating a Configuration File

Create a `config.json` file to assign custom names to your devices:

```json
{
    "devices": [
        {
            "name": "arm_tracker",
            "type": "Tracker",
            "serial": "LHR-XXXXXXXX"
        },
        {
            "name": "tracking_reference_1",
            "type": "Tracking Reference",
            "serial": "LHB-XXXXXXXX"
        }
    ]
}
```

Replace `LHR-XXXXXXXX` with your actual tracker serial number from the discovery output.

## Using with ForceUMI

### Basic Usage

```python
from forceumi.devices import PoseSensor

# Initialize with default tracker name
sensor = PoseSensor(device_name="tracker_1")

# Or use custom config
sensor = PoseSensor(
    device_name="arm_tracker",
    config_file="config.json"
)

# Connect and read
sensor.connect()
state = sensor.read()  # Returns [x, y, z, rx, ry, rz, gripper]
sensor.disconnect()
```

### In Data Collection

```python
from forceumi.collector import DataCollector
from forceumi.devices import Camera, PoseSensor, ForceSensor

# Create devices
camera = Camera(device_id=0)
pose_sensor = PoseSensor(
    device_name="arm_tracker",
    config_file="config.json"
)
force_sensor = ForceSensor()

# Create collector
collector = DataCollector(
    camera=camera,
    pose_sensor=pose_sensor,
    force_sensor=force_sensor
)

# Collect data
collector.connect_devices()
collector.start_episode()
# ... data collection ...
collector.stop_episode()
```

## Configuration Options

### PoseSensor Parameters

- **device_name** (str): Name of the tracker device
  - Default: `"tracker_1"`
  - Use the name from your config.json or PyTracker's default names
  
- **config_file** (str, optional): Path to PyTracker config.json
  - Default: `None` (uses PyTracker's default device naming)
  
- **gripper_port** (str, optional): Serial port for gripper sensor
  - Default: `None`
  - Example: `"/dev/ttyUSB2"`

### Example config.yaml for ForceUMI

```yaml
devices:
  camera:
    device_id: 0
    width: 640
    height: 480
    fps: 30
  
  pose_sensor:
    device_name: "arm_tracker"
    config_file: "pytracker_config.json"
    gripper_port: "/dev/ttyUSB2"
  
  force_sensor:
    port: "/dev/ttyUSB1"
    baudrate: 115200
```

## Troubleshooting

### "PyTracker is not installed"

Install PyTracker:
```bash
pip install git+https://github.com/Elycyx/PyTracker.git
```

### "No devices found"

1. Ensure SteamVR is running
2. Check that trackers are powered on and tracked (green in SteamVR)
3. Verify base stations are visible to the trackers

### "Device 'tracker_1' not found"

The device name doesn't match. Run the discovery script to find available names:

```python
from forceumi.devices import PoseSensor

sensor = PoseSensor()
sensor.connect()  # This will print available devices
```

### Tracking Quality Issues

1. Ensure good lighting conditions
2. Check base station positioning (they should be mounted high, angled down)
3. Avoid reflective surfaces in the tracking volume
4. Keep the tracker within view of at least one base station

### "Failed to initialize OpenVR"

1. Restart SteamVR
2. Check VR headset is connected (even if not worn)
3. Verify SteamVR is in "ready" state (not in standby)

## Advanced Features

### High-Speed Sampling

PyTracker supports high-frequency sampling:

```python
# Collect 1000 samples at 250 Hz
samples = sensor.sample(num_samples=1000, sample_rate=250.0)
print(samples.shape)  # (1000, 7)
```

### Velocity and Acceleration

```python
# Get linear velocity
velocity = sensor.get_velocity()  # [vx, vy, vz]

# Get angular velocity
angular_vel = sensor.get_angular_velocity()  # [wx, wy, wz]
```

### Quaternion Format

```python
# Get pose as quaternion
quat_pose = sensor.get_pose_quaternion()
# Returns [x, y, z, qw, qx, qy, qz, gripper]
```

## Testing

Run the test script to verify everything is working:

```bash
python examples/test_pytracker.py
```

This will:
1. Check PyTracker installation
2. Connect to a tracker
3. Display real-time pose data
4. Test velocity reading
5. Test high-speed sampling

## References

- [PyTracker GitHub](https://github.com/Elycyx/PyTracker)
- [OpenVR Documentation](https://github.com/ValveSoftware/openvr)
- [SteamVR Setup Guide](https://help.steampowered.com/en/faqs/view/06D2-2F90-EECE-AFCE)

## Support

For PyTracker-specific issues, please check:
- PyTracker GitHub Issues
- OpenVR documentation

For ForceUMI integration issues:
- Check ForceUMI documentation
- Open an issue on ForceUMI GitHub

