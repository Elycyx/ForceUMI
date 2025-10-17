# PyForce Setup Guide

This guide explains how to set up PyForce for use with ForceUMI's force sensor.

## What is PyForce?

[PyForce](https://github.com/Elycyx/PyForce) is a Python package for collecting, visualizing, and saving force sensor data from Sunrise (宇立) force sensors. ForceUMI uses it to capture 6-axis force/torque data via TCP/IP.

## Prerequisites

1. **Sunrise Force Sensor**: Compatible 6-axis force/torque sensor
2. **Network Connection**: Sensor connected to the same network as your computer
3. **Sensor Configuration**: Know the IP address and port of your sensor

## Installation

### Step 1: Install PyForce

```bash
pip install git+https://github.com/Elycyx/PyForce.git
```

### Step 2: Verify Installation

```bash
python -c "from pyforce import ForceSensor; print('PyForce installed successfully')"
```

### Step 3: Configure Network

Ensure your force sensor is configured on the network:

1. Power on the force sensor
2. Connect it to your network (Ethernet)
3. Note the IP address (default is usually `192.168.0.108`)
4. Test connectivity: `ping 192.168.0.108`

## Configuration

### Finding Your Sensor

To check if your sensor is accessible:

```python
import socket

# Test TCP connection
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = sock.connect_ex(('192.168.0.108', 4008))

if result == 0:
    print("Sensor is accessible")
else:
    print("Cannot connect to sensor")

sock.close()
```

### Network Setup

If the sensor is on a different subnet:

1. **Static IP**: Configure your computer's network adapter with a static IP in the same subnet
   - Example: If sensor is `192.168.0.108`, set your PC to `192.168.0.100`
   - Subnet mask: `255.255.255.0`

2. **Router Configuration**: Ensure no firewall is blocking port 4008

## Using with ForceUMI

### Basic Usage

```python
from forceumi.devices import ForceSensor

# Initialize with default settings
sensor = ForceSensor(
    ip_addr="192.168.0.108",
    port=4008,
    sample_rate=100  # Optional: 100 Hz
)

# Connect and read
sensor.connect()

# Zero calibration (remove external forces first)
sensor.zero(num_samples=50)

# Read force data
force = sensor.read()  # Returns [fx, fy, fz, mx, my, mz]
print(f"Force: {force[:3]} N, Torque: {force[3:]} Nm")

sensor.disconnect()
```

### In Data Collection

```python
from forceumi.collector import DataCollector
from forceumi.devices import Camera, PoseSensor, ForceSensor

# Create devices
camera = Camera(device_id=0)
pose_sensor = PoseSensor(device_name="tracker_1")
force_sensor = ForceSensor(
    ip_addr="192.168.0.108",
    port=4008,
    sample_rate=100
)

# Create collector
collector = DataCollector(
    camera=camera,
    pose_sensor=pose_sensor,
    force_sensor=force_sensor
)

# Collect data
collector.connect_devices()

# Zero force sensor
force_sensor.zero(num_samples=50)

collector.start_episode()
# ... data collection ...
collector.stop_episode()
```

## Configuration Options

### ForceSensor Parameters

- **ip_addr** (str): Sensor IP address
  - Default: `"192.168.0.108"`
  - Find via sensor manual or network scan
  
- **port** (int): Sensor TCP port
  - Default: `4008`
  - Typically 4008 for Sunrise sensors
  
- **sample_rate** (int, optional): Sampling frequency in Hz
  - Default: `None` (uses sensor default)
  - Typical range: 10-1000 Hz
  - Higher rates require faster network

### Example config.yaml for ForceUMI

```yaml
devices:
  camera:
    device_id: 0
    width: 640
    height: 480
    fps: 30
  
  pose_sensor:
    device_name: "tracker_1"
    config_file: "pytracker_config.json"
  
  force_sensor:
    ip_addr: "192.168.0.108"
    port: 4008
    sample_rate: 100

data:
  save_dir: ./data
  auto_save: true
```

## Advanced Features

### Zero Calibration

Remove bias from sensor readings:

```python
# With no external forces applied:
sensor.zero(num_samples=100)
print(f"Bias: {sensor.bias}")
```

### Sample Rate Configuration

Change sampling frequency:

```python
sensor.set_sample_rate(200)  # 200 Hz
```

### Sensor Information

Query sensor details:

```python
info = sensor.get_sensor_info()
print(info)
```

### Compute Unit Configuration

Set computation unit:

```python
sensor.set_compute_unit("MVPV")
```

### Decouple Matrix

Set calibration matrix (from sensor calibration):

```python
matrix = "(0.272516,-62.753809,...)...\r\n"
sensor.set_decouple_matrix(matrix)
```

### With Timestamp

Get synchronized timestamp:

```python
data = sensor.get_with_timestamp()
# Returns: {'ft': np.ndarray, 'timestamp': float}
force = data['ft']
time = data['timestamp']
```

## Troubleshooting

### "PyForce is not installed"

Install PyForce:
```bash
pip install git+https://github.com/Elycyx/PyForce.git
```

### "Failed to connect to force sensor"

1. **Check power**: Ensure sensor is powered on
2. **Check network**: `ping 192.168.0.108`
3. **Check IP/port**: Verify correct address and port
4. **Check firewall**: Ensure port 4008 is not blocked
5. **Check subnet**: Ensure computer and sensor are on same network

### "No data received"

1. Verify sensor is in data streaming mode
2. Check sample rate is supported
3. Ensure `start_stream()` was called (done automatically in `connect()`)

### High Latency

1. Reduce sample rate
2. Use wired Ethernet (not WiFi)
3. Close other network applications
4. Check network switch/router performance

### Connection Drops

1. Check Ethernet cable
2. Verify network stability
3. Ensure sensor firmware is up to date
4. Check for network conflicts

## Data Format

PyForce returns force/torque data as numpy arrays:

```python
force = sensor.read()
# force = np.array([fx, fy, fz, mx, my, mz])
#   fx, fy, fz: Forces in X, Y, Z (Newtons)
#   mx, my, mz: Torques around X, Y, Z (Newton-meters)
```

## Performance

- **Typical Latency**: < 10ms (TCP/IP to Python)
- **Maximum Sample Rate**: 1000 Hz (network dependent)
- **Measurement Range**: Sensor dependent (check sensor specs)
- **Resolution**: Sensor dependent (typically 0.001 N, 0.0001 Nm)

## Testing

Run the test script to verify everything is working:

```bash
python examples/test_pyforce.py
```

This will:
1. Check PyForce installation
2. Prompt for sensor IP/port
3. Connect to sensor
4. Display sensor information
5. Perform zero calibration
6. Display real-time force data

## References

- [PyForce GitHub](https://github.com/Elycyx/PyForce)
- [PyForce中文文档](https://github.com/Elycyx/PyForce/blob/main/README_CN.md)
- [Sunrise Force Sensor Manual](https://www.sunrise-robot.com/) (check manufacturer)
- [ForceUMI Documentation](../README.md)

## Support

For PyForce-specific issues:
- Check PyForce GitHub Issues
- Review PyForce documentation

For ForceUMI integration issues:
- Check ForceUMI documentation
- Open an issue on ForceUMI GitHub

