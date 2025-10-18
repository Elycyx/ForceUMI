# Time Synchronization Analysis and Improvements

## Current Issues

### 1. Single Timestamp Problem
Currently, all sensors share one timestamp recorded at the start of the collection loop:
```python
timestamp = time.time()
camera.read()      # Takes ~33ms (30fps)
pose_sensor.read() # Takes ~10ms
force_sensor.read()# Takes ~5ms
# All data labeled with same timestamp, but actually 48ms span!
```

### 2. Sequential Reading Delays
Sensors are read sequentially, introducing cumulative delays:
- Camera: captured at t+0ms
- Pose: captured at t+33ms
- Force: captured at t+43ms

But all marked as time t, causing synchronization errors during replay.

## Solutions Implemented

### Solution 1: Per-Sensor Timestamps (Recommended)
Record individual timestamps for each sensor immediately after reading:

```python
# Camera
t_camera_start = time.time()
image = camera.read()
t_camera = time.time()

# Pose
t_pose_start = time.time()
state = pose_sensor.read()
t_pose = time.time()

# Force
t_force_start = time.time()
force = force_sensor.read()
t_force = time.time()
```

### Solution 2: Concurrent Reading
Use threading to read sensors in parallel (reduces total latency):
```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=3) as executor:
    camera_future = executor.submit(read_camera_with_timestamp)
    pose_future = executor.submit(read_pose_with_timestamp)
    force_future = executor.submit(read_force_with_timestamp)
    
    results = [f.result() for f in [camera_future, pose_future, force_future]]
```

### Solution 3: Interpolation During Replay
For replay, interpolate data to common timestamps:
- Choose a reference sensor (e.g., camera with stable FPS)
- Interpolate other sensors' data to camera timestamps

## Implementation Status

- [x] Add per-sensor timestamp recording in collector
- [x] Update Episode dataclass to store multiple timestamps
- [x] Update HDF5 structure to save sensor-specific timestamps
- [x] Enhance replay to use interpolation for synchronization
- [x] Add timestamp analysis tools

## Expected Improvements

- **Accuracy**: Sub-millisecond timestamp precision per sensor
- **Replay Quality**: Smooth playback with proper temporal alignment
- **Analysis**: Detailed timing information for debugging

