# Changelog

All notable changes to the ForceUMI project will be documented in this file.

## [0.1.0] - 2025-10-16

### Added
- **PyTracker Integration**: PoseSensor now supports VR tracking via PyTracker
  - Real-time 6DOF tracking from SteamVR devices
  - Support for VR trackers (HTC Vive, Tundra, etc.)
  - High-speed sampling up to 250+ Hz
  - Velocity and acceleration data
  - See `docs/PYTRACKER_SETUP.md` for setup guide

### Changed
- Simplified installation: now using `pip install -e .` for all dependencies
- **BREAKING**: Updated state and action dimensions from 6D to 7D
  - State now includes gripper: `[x, y, z, rx, ry, rz, gripper]`
  - Action now includes gripper: `[dx, dy, dz, drx, dry, drz, gripper]`
  - **Note**: Gripper value is always absolute (not delta) in both state and action

### Updated Files

#### Core Modules
- `forceumi/devices/pose_sensor.py`: Updated to return 7D state arrays
- `forceumi/data/episode.py`: Updated docstrings to reflect 7D data
- `forceumi/collector.py`: Handles 7D state and action data

#### GUI Components
- `forceumi/gui/visualizers.py`:
  - Updated `PoseDisplay` to show 7 dimensions (added gripper)
  - Updated `ActionDisplay` to show 7 dimensions (added gripper)
  - Added aliases: `ForceViewer = ForcePlotter`, `StateViewer = PoseDisplay`
- `forceumi/gui/main_window.py`: Updated to call `update_pose()` method

#### Documentation
- `README.md`: Updated HDF5 data format specification
- `QUICKSTART.md`: Updated data format description
- `PROJECT_STRUCTURE.md`: Updated module descriptions
- `IMPLEMENTATION_SUMMARY.md`: Updated HDF5 structure documentation

#### Tests
- `tests/test_devices.py`: Updated pose sensor tests for 7D output
- `tests/test_data.py`: Updated all episode and HDF5 tests for 7D data

### Data Format

The new HDF5 structure is:

```
episode_<timestamp>.hdf5
├── /image           # (N, H, W, 3) uint8 - RGB images
├── /state           # (N, 7) float32 - [x,y,z,rx,ry,rz,gripper]
├── /action          # (N, 7) float32 - [dx,dy,dz,drx,dry,drz,gripper]
├── /force           # (N, 6) float32 - [fx,fy,fz,mx,my,mz]
├── /timestamp       # (N,) float64 - Unix timestamps
└── /metadata        # Attributes

Note: gripper value is always absolute (not delta)
```

### Migration Guide

If you have existing code using the 6D format:

**Before:**
```python
state = np.zeros(6)  # [x, y, z, rx, ry, rz]
action = np.zeros(6)  # [dx, dy, dz, drx, dry, drz]
```

**After:**
```python
state = np.zeros(7)  # [x, y, z, rx, ry, rz, gripper]
action = np.zeros(7)  # [dx, dy, dz, drx, dry, drz, gripper]
```

**Important:** The gripper value in action is always absolute, not a delta value.

## Initial Release

### Added
- Complete data collection system for robotic arm devices
- Multi-modal data acquisition (RGB, pose, action, force)
- HDF5-based data storage with compression
- Real-time visualization GUI with PyQt5
- Comprehensive test suite
- Full documentation and examples
- CI/CD pipeline with GitHub Actions

### Features
- Device abstraction layer for camera, pose sensor, and force sensor
- Thread-safe data collection
- Episode-based data management
- YAML/JSON configuration support
- Real-time image display
- Live force sensor plotting
- Pose/state visualization
- Example scripts for basic usage

