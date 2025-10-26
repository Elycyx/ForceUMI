# Changelog

All notable changes to the ForceUMI project will be documented in this file.

## [0.3.2] - 2025-10-19

### Changed (BREAKING)
- **Coordinate Frame Alignment**:
  - Action data now rotated 90° around z-axis to align with force sensor frame
  - Two rotation options: CW (`rotate_frame_z_90_cw`) or CCW (`rotate_frame_z_90_ccw`)
  - Default: Clockwise rotation - `new_x = old_y`, `new_y = -old_x`, `new_z = old_z`
  - Easy to switch: change `rotate_to_force_frame` variable in `collector.py`
  - Makes action and force data directly comparable in same coordinate system
  - State data unchanged (still in tracker frame)
  - See `ROTATION_DIRECTION_GUIDE.md` for choosing the right direction

- **Session-Based Episode Organization**:
  - Episodes now saved in session directories: `data/session_TIMESTAMP/episode0.hdf5, episode1.hdf5, ...`
  - Session created on first episode start of each program run
  - Episode counter auto-increments within session
  - Easier to manage and batch process related episodes
  - Backward compatible: old episode files still work

### Fixed
- **Replay Speed Accuracy**:
  - Now uses actual timestamps from data instead of just metadata FPS
  - Corrected timing accumulation to prevent drift
  - Added resync mechanism for consistent playback
  - Replay speed now accurately matches original recording speed

### Added
- `rotate_frame_z_90_cw()` - Clockwise 90° rotation around z-axis
- `rotate_frame_z_90_ccw()` - Counter-clockwise 90° rotation around z-axis  
- **LeRobot Dataset Conversion**:
  - `convert_forceumi_to_lerobot.py` - Convert ForceUMI data to LeRobot format
  - Support for both flat and session-based directory structures
  - Image resizing option for faster training
  - Skip frames option to remove unstable warmup data
  - Push to HuggingFace Hub support
  - `docs/LEROBOT_CONVERSION.md` - Complete conversion guide
  - `examples/convert_example.sh` - Conversion examples
  - `examples/verify_lerobot_dataset.py` - Verify converted datasets
- `examples/list_sessions.py` - Browse and analyze session data
- Session metadata in each episode (session_dir, episode_number)

## [0.3.1] - 2025-10-18

### Added
- **Per-Sensor Timestamp Recording**:
  - Each sensor (camera, pose, force) now has its own timestamp
  - Eliminates sequential reading delay errors
  - HDF5 files now contain `timestamp_camera`, `timestamp_pose`, `timestamp_force`
  - Backward compatible: old episodes still work with main `timestamp`
- **Timestamp Analysis Tool** (`analyze_timestamps.py`):
  - Diagnose time synchronization quality
  - Visualize inter-sensor delays
  - Calculate frame intervals and jitter
  - Generate detailed timing reports and plots

### Improved
- **Data Collection**: Individual timestamp per sensor for accurate synchronization
- **Time Accuracy**: Sub-millisecond precision for each modality

## [0.3.0] - 2025-10-18

### Changed (BREAKING)
- **Action Coordinate System**: Action data now represents pose relative to first frame instead of absolute pose
  - State: Still represents tracker pose relative to station (base) coordinate system
  - Action: Now represents tracker pose relative to the first frame's coordinate system
  - First frame action is `[0, 0, 0, 0, 0, 0, gripper]`
  - Subsequent frames express relative transformation from first frame
  - Gripper value remains absolute in both state and action

### Added
- **Coordinate Transformation Utilities** (`forceumi/utils/transforms.py`):
  - Euler angle <-> rotation matrix conversions
  - Quaternion <-> rotation matrix conversions
  - Pose transformation and relative pose calculation
  - Batch processing support
  - Example: `examples/test_transforms.py`

- **Sensor Warmup Feature**:
  - Configurable warmup period (default 2 seconds) before data collection
  - Ensures sensor readings stabilize before saving data
  - Reference pose (for action calculation) set after warmup completes
  - Visual warmup indicator in GUI
  - Configuration: `collector.warmup_duration`

- **Data Quality Verification** (`verify_data_quality.py`):
  - Analyze timestamp uniformity
  - Calculate actual FPS and jitter
  - Detect frame interval outliers
  - Verify data shapes

- **Episode Replay System** (`forceumi/replay/`):
  - Visualize previously collected episodes with synchronized playback
  - Three-window display: image, force/torque plots, state/action plots
  - Playback controls: play/pause, speed adjustment (0.1x-10x), frame stepping
  - Navigation: seek to start/end, jump to specific frame
  - Loop mode support
  - Command-line tool: `forceumi-replay`
  - Example script: `examples/replay_episode.py`

### Improved
- **Pose Sensor Reading**: 
  - Added retry mechanism for transient failures
  - **Automatic unit conversion**: Angles converted from degrees (PyTracker output) to radians (dataset format)
- **Force Sensor Reading**: Uses `get()` method for fresher data from background thread
- **GUI Display**: Shows warmup progress with countdown timer

### Updated
- `README.md`: Updated data format documentation with new action definition
- `forceumi/collector.py`: Implements relative pose calculation for action
- Project structure: Added `utils/` module for coordinate transformations

## [0.2.0] - 2025-10-17

### Changed (BREAKING)
- **GUI Migration to OpenCV**: Migrated from PyQt5 to OpenCV highgui to avoid Qt conflicts
  - Removed PyQt5 and pyqtgraph dependencies
  - New OpenCV-based GUI with keyboard controls
  - Added `cv_main_window.py` and `cv_visualizer.py`
  - Removed old PyQt files: `main_window.py`, `widgets.py`, and `visualizers.py`

### Added
- **OpenCV-based GUI**: New lightweight GUI using cv2.imshow
  - Four windows: Main View, Force Data, State Data, Control Panel
  - Keyboard shortcuts: C (connect), D (disconnect), S (start), E (stop), Q (quit)
  - Real-time status overlays
  - matplotlib-based plot rendering
  - No Qt backend conflicts

### Removed
- PyQt5 dependency (resolved Qt conflicts with opencv-python)
- pyqtgraph dependency

### Updated
- `requirements.txt`: Removed PyQt5 and pyqtgraph
- `setup.py`: Updated entry point to use cv_main_window
- `examples/launch_gui.py`: Now launches OpenCV GUI
- `README.md`: Updated with OpenCV GUI information and keyboard controls

### Notes
- All core functionality (data collection, devices, HDF5 storage) unchanged
- Configuration file format remains the same

## [0.1.0] - 2025-10-16

### Added
- **PyTracker Integration**: PoseSensor now supports VR tracking via PyTracker
  - Real-time 6DOF tracking from SteamVR devices
  - Support for VR trackers (HTC Vive, Tundra, etc.)
  - High-speed sampling up to 250+ Hz
  - Velocity and acceleration data
  - See `docs/PYTRACKER_SETUP.md` for setup guide

- **PyForce Integration**: ForceSensor now supports Sunrise force sensors via PyForce
  - Real-time 6-axis force/torque data acquisition
  - TCP/IP network communication
  - Zero calibration and bias compensation
  - Configurable sample rate (up to 1000 Hz)
  - Sensor configuration (compute unit, decouple matrix)
  - See `docs/PYFORCE_SETUP.md` for setup guide

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

