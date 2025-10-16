# ForceUMI Examples

This directory contains example scripts demonstrating various uses of the ForceUMI system.

## Examples

### 1. Launch GUI (`launch_gui.py`)

Launch the full graphical interface for data collection:

```bash
python launch_gui.py
```

This will:
- Load configuration from `config.yaml` if available
- Launch the GUI with real-time visualization
- Allow interactive data collection

### 2. Basic Collection (`basic_collection.py`)

Programmatic data collection without GUI:

```bash
python basic_collection.py
```

This demonstrates:
- Initializing devices programmatically
- Starting and stopping episodes
- Automatic data saving
- Basic error handling

### 3. Read Episode (`read_episode.py`)

Read and analyze saved episode data:

```bash
python read_episode.py path/to/episode.hdf5
```

This shows:
- Loading HDF5 files
- Accessing episode metadata
- Analyzing data statistics
- Computing timing information

### 4. Configuration Example (`config_example.yaml`)

Example configuration file showing all available options:

```bash
cp config_example.yaml ../config.yaml
# Edit config.yaml as needed
```

## Creating Your Own Scripts

You can use these examples as templates for your own data collection workflows:

```python
from forceumi.collector import DataCollector
from forceumi.devices import Camera, PoseSensor, ForceSensor

# Initialize your devices
camera = Camera(device_id=0)
pose_sensor = PoseSensor(port="/dev/ttyUSB0")
force_sensor = ForceSensor(port="/dev/ttyUSB1")

# Create collector
collector = DataCollector(
    camera=camera,
    pose_sensor=pose_sensor,
    force_sensor=force_sensor,
    save_dir="./my_data"
)

# Your collection logic here
with collector:
    collector.start_episode(metadata={"task": "my_task"})
    # ... collect data ...
    collector.stop_episode()
```

## Tips

1. **Device Configuration**: Modify device parameters in `config.yaml` rather than hardcoding them
2. **Error Handling**: Always check device connection status before collecting
3. **Data Organization**: Use descriptive task names in metadata for easier organization
4. **Testing**: Test device connections before long collection sessions

## Need Help?

- Check the main README.md for installation instructions
- See CONTRIBUTING.md for development guidelines
- Open an issue on GitHub for bugs or questions

