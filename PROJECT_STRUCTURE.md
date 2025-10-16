# ForceUMI Project Structure

This document provides a comprehensive overview of the ForceUMI project structure.

## Directory Tree

```
forceumi/
├── .github/
│   └── workflows/
│       └── tests.yml              # GitHub Actions CI/CD configuration
│
├── forceumi/                      # Main package directory
│   ├── __init__.py               # Package initialization
│   │
│   ├── devices/                  # Device interface modules
│   │   ├── __init__.py          # Device package exports
│   │   ├── base.py              # Base device class (abstract)
│   │   ├── camera.py            # RGB fisheye camera interface
│   │   ├── pose_sensor.py       # UMI 6DOF pose sensor interface
│   │   └── force_sensor.py      # 6-axis force/torque sensor interface
│   │
│   ├── data/                     # Data management modules
│   │   ├── __init__.py          # Data package exports
│   │   ├── episode.py           # Episode data container class
│   │   └── hdf5_manager.py      # HDF5 file I/O manager
│   │
│   ├── gui/                      # Graphical user interface
│   │   ├── __init__.py          # GUI package exports
│   │   ├── main_window.py       # Main application window
│   │   ├── widgets.py           # Custom UI widgets
│   │   └── visualizers.py       # Data visualization components
│   │
│   ├── collector.py              # Main data collection manager
│   └── config.py                 # Configuration management
│
├── examples/                      # Example scripts and tutorials
│   ├── README.md                 # Examples documentation
│   ├── basic_collection.py       # Basic programmatic collection
│   ├── launch_gui.py             # GUI launcher script
│   ├── read_episode.py           # Episode data reader
│   └── config_example.yaml       # Example configuration file
│
├── tests/                         # Test suite
│   ├── __init__.py               # Test package initialization
│   ├── test_devices.py           # Device module tests
│   ├── test_data.py              # Data management tests
│   ├── test_collector.py         # Collector tests
│   └── test_config.py            # Configuration tests
│
├── .gitignore                     # Git ignore patterns
├── CONTRIBUTING.md                # Contribution guidelines
├── LICENSE                        # MIT License
├── PROJECT_STRUCTURE.md           # This file
├── QUICKSTART.md                  # Quick start guide
├── README.md                      # Main documentation
├── pytest.ini                     # Pytest configuration
├── requirements.txt               # Python dependencies
└── setup.py                       # Package installation script
```

## Module Descriptions

### Core Modules

#### `forceumi/collector.py`
Main data collection orchestrator. Handles:
- Multi-device synchronization
- Thread-safe data buffering
- Episode lifecycle management
- Automatic data saving

**Key Classes:**
- `DataCollector`: Main collector class

#### `forceumi/config.py`
Configuration management system. Features:
- YAML/JSON file support
- Nested configuration access
- Default configuration values
- Deep merge functionality

**Key Classes:**
- `Config`: Configuration manager

### Device Modules (`forceumi/devices/`)

#### `base.py`
Abstract base class defining the standard device interface.

**Key Classes:**
- `BaseDevice`: Abstract base class with standard methods

**Standard Methods:**
- `connect()`: Connect to device
- `disconnect()`: Disconnect from device
- `read()`: Read data from device
- `is_connected()`: Check connection status

#### `camera.py`
RGB fisheye camera interface using OpenCV.

**Key Classes:**
- `Camera`: Camera device implementation

**Features:**
- Configurable resolution and FPS
- BGR to RGB conversion
- Property introspection

#### `pose_sensor.py`
UMI 6DOF pose sensor interface.

**Key Classes:**
- `PoseSensor`: Pose sensor implementation

**Features:**
- Serial communication support
- Calibration functionality
- 7D state output [x, y, z, rx, ry, rz, gripper]

#### `force_sensor.py`
6-axis force/torque sensor interface.

**Key Classes:**
- `ForceSensor`: Force sensor implementation

**Features:**
- Serial communication support
- Bias/zeroing functionality
- 6-axis output [fx, fy, fz, mx, my, mz]

### Data Modules (`forceumi/data/`)

#### `episode.py`
Episode data container for single collection sessions.

**Key Classes:**
- `Episode`: Episode data container

**Features:**
- Frame-by-frame data accumulation
- Automatic timestamp tracking
- Metadata management
- Dictionary conversion

#### `hdf5_manager.py`
HDF5 file I/O manager for episode data.

**Key Classes:**
- `HDF5Manager`: HDF5 file manager

**Features:**
- Compressed data storage
- Chunked datasets for images
- Metadata as attributes
- Episode info extraction

**HDF5 File Structure:**
```
episode_YYYYMMDD_HHMMSS.hdf5
├── /image           # (N, H, W, 3) uint8
├── /state           # (N, 7) float32 - [x,y,z,rx,ry,rz,gripper]
├── /action          # (N, 7) float32 - [dx,dy,dz,drx,dry,drz,gripper]
├── /force           # (N, 6) float32 - [fx,fy,fz,mx,my,mz]
├── /timestamp       # (N,) float64
└── /metadata        # attributes

Note: gripper value is always absolute (not delta)
```

### GUI Modules (`forceumi/gui/`)

#### `main_window.py`
Main application window with full UI.

**Key Classes:**
- `MainWindow`: Main GUI window

**Features:**
- Device connection management
- Real-time data visualization
- Episode control
- Configuration loading/saving
- Logging display

#### `widgets.py`
Custom UI components.

**Key Classes:**
- `StatusIndicator`: LED-style status display
- `DevicePanel`: Device connection panel
- `ControlPanel`: Collection control panel
- `LogPanel`: Log message display

#### `visualizers.py`
Data visualization components.

**Key Classes:**
- `ImageViewer`: Real-time image display
- `ForceViewer`: Force data plotting
- `StateViewer`: Pose/state display

## Example Scripts

### `examples/basic_collection.py`
Demonstrates simple programmatic data collection without GUI.

### `examples/launch_gui.py`
Simple GUI launcher with configuration loading.

### `examples/read_episode.py`
Reads and displays statistics from saved episode files.

### `examples/config_example.yaml`
Template configuration file with all available options.

## Testing

### Test Organization

Tests are organized by module:
- `test_devices.py`: Device interface tests
- `test_data.py`: Data management tests
- `test_collector.py`: Collector functionality tests
- `test_config.py`: Configuration tests

### Running Tests

```bash
# All tests
pytest

# Specific module
pytest tests/test_devices.py

# With coverage
pytest --cov=forceumi --cov-report=html
```

## Dependencies

### Core Dependencies
- **numpy**: Numerical computing
- **h5py**: HDF5 file I/O
- **PyYAML**: YAML configuration files

### GUI Dependencies
- **PyQt5**: GUI framework
- **pyqtgraph**: Real-time plotting
- **matplotlib**: Data visualization

### Image Processing
- **opencv-python**: Camera interface
- **Pillow**: Image processing

## Configuration

Configuration files support YAML or JSON format with the following structure:

```yaml
devices:
  camera: { ... }
  pose_sensor: { ... }
  force_sensor: { ... }

data:
  save_dir: "./data"
  compression: "gzip"
  auto_save: true

collector:
  max_fps: 30.0

gui:
  window_title: "..."
  update_interval: 33
```

## Entry Points

The package provides a command-line entry point:

```bash
forceumi-collect  # Launch GUI
```

Or use module execution:

```bash
python -m forceumi.gui.main_window
```

## Development

### Adding New Devices

1. Create new file in `forceumi/devices/`
2. Inherit from `BaseDevice`
3. Implement required methods
4. Add to `devices/__init__.py`
5. Create tests in `tests/test_devices.py`

### Adding New Features

1. Create feature branch
2. Implement with tests
3. Update documentation
4. Submit pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

