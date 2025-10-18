# Time Synchronization Guide

This guide explains how ForceUMI handles time synchronization across multiple sensors and how to diagnose timing issues.

## Understanding the Problem

### Sequential Reading Delays

When collecting data from multiple sensors, they are read sequentially:

```
t=0ms:   Start collection loop
t=0ms:   Read camera        → takes ~33ms (@ 30fps)
t=33ms:  Read pose sensor   → takes ~10ms
t=43ms:  Read force sensor  → takes ~5ms
t=48ms:  All data collected
```

**Problem**: If all data is labeled with timestamp `t=0ms`, we lose ~48ms of timing information!

### Impact on Multi-Modal Learning

- **Training**: Models may learn incorrect temporal correlations
- **Replay**: Visual lag between different data streams
- **Analysis**: Inaccurate timing measurements

## ForceUMI's Solution

### Per-Sensor Timestamps (v0.3.1+)

Each sensor gets its own timestamp recorded immediately after reading:

```python
# Camera
image = camera.read()
timestamp_camera = time.time()  # ← Accurate camera timestamp

# Pose
state = pose.read()
timestamp_pose = time.time()    # ← Accurate pose timestamp

# Force
force = force.read()
timestamp_force = time.time()   # ← Accurate force timestamp
```

### HDF5 Structure

```
episode.hdf5
├── /timestamp          # Main loop timestamp (backward compat)
├── /timestamp_camera   # Camera-specific timestamp
├── /timestamp_pose     # Pose-specific timestamp
└── /timestamp_force    # Force-specific timestamp
```

## Diagnosing Time Sync Issues

### Step 1: Collect an Episode

Collect data as usual. New episodes automatically include per-sensor timestamps.

### Step 2: Run Timestamp Analysis

```bash
python analyze_timestamps.py data/episode_20250118_143025.hdf5
```

### Step 3: Interpret Results

The tool provides several metrics:

#### Frame Intervals
```
Camera Sensor:
  Interval: 33.2 ± 1.5ms
  FPS: 30.1
```
- **Mean interval**: Should match expected sensor rate
- **Std deviation**: Lower is better (< 5ms is good)
- **Large std**: Indicates timing jitter or system load

#### Inter-Sensor Delays
```
Pose→Camera delay:
  Mean: 35.4ms
  Std:  2.1ms
```
- Shows how much lag exists between sensors
- **Consistent delays** (low std): Good! System is stable
- **Variable delays** (high std): Problem! System under load

#### Visual Plots

1. **Timeline**: Shows when each sensor captures data
   - Should see parallel lines
   - Gaps indicate missed frames

2. **Inter-Sensor Delays**: Shows timing differences over time
   - Should be relatively flat
   - Spikes indicate temporary issues

3. **Frame Intervals**: Shows consistency of each sensor
   - Should be stable around mean
   - Large variations indicate problems

## Common Issues and Solutions

### Issue 1: High Camera Delay (~30-50ms)

**Cause**: Camera is typically the slowest sensor

**Solutions**:
- ✅ **Expected behavior** - cameras have inherent capture delay
- Consider using hardware-triggered cameras for better sync
- Use camera timestamps for accurate timing

### Issue 2: Variable Delays (High Std Deviation)

**Symptoms**:
```
Camera delay:
  Mean: 33.4ms
  Std:  15.2ms  ← Too high!
```

**Causes**:
- System CPU overload
- USB bandwidth saturation
- Other processes competing for resources

**Solutions**:
1. Close unnecessary applications
2. Reduce GUI update rate in config:
   ```yaml
   gui:
     update_interval: 100  # Slower updates = less load
   ```
3. Lower camera resolution/FPS
4. Use dedicated USB controllers for each sensor

### Issue 3: Missed Frames

**Symptoms**: Gaps in timeline plot, varying frame counts per sensor

**Causes**:
- Sensor read failures
- Collection rate faster than sensor can provide
- Network delays (for TCP sensors like force sensor)

**Solutions**:
1. Check sensor connections
2. Lower `max_fps` in collector config:
   ```python
   collector = DataCollector(max_fps=20)  # Instead of 30
   ```
3. Check force sensor network latency

### Issue 4: Replay Looks Unsynchronized

**Cause**: Replay system uses main timestamp instead of per-sensor timestamps

**Solution**: Use the new replay system (v0.3.1+) which handles per-sensor timestamps correctly

## Best Practices

### 1. Match Collection Rate to Slowest Sensor

```python
# If camera is 30fps, don't try to collect at 60fps
collector = DataCollector(max_fps=30)
```

### 2. Use Hardware Triggering (If Available)

Hardware-triggered cameras and synchronized sensors eliminate most timing issues.

### 3. Minimize System Load

- Close unnecessary applications
- Use dedicated machine for data collection
- Disable desktop effects and animations

### 4. Regular Calibration

Periodically check timing quality:
```bash
# Quick check
python analyze_timestamps.py data/latest_episode.hdf5

# Detailed analysis
python verify_data_quality.py data/
```

### 5. Document Your Setup

Record your timing analysis results:
```
System: Ubuntu 20.04, Intel i7-9700K
Camera: 640x480 @ 30fps → 33.2±1.5ms
Pose:   VR tracker → 10.5±0.8ms
Force:  TCP @ 50Hz → 20.1±1.2ms
Inter-sensor delay: 35±2ms (stable)
```

## Advanced: Using Timestamps in Training

### Option 1: Align to Common Timeline

```python
import numpy as np
from scipy import interpolate

# Get per-sensor timestamps
ts_camera = data['timestamp_camera']
ts_pose = data['timestamp_pose']
ts_force = data['timestamp_force']

# Use camera as reference (most stable)
t_ref = ts_camera

# Interpolate other sensors to camera timestamps
pose_interp = interpolate.interp1d(ts_pose, data['state'], 
                                   axis=0, fill_value='extrapolate')
force_interp = interpolate.interp1d(ts_force, data['force'],
                                    axis=0, fill_value='extrapolate')

# Aligned data
aligned_state = pose_interp(t_ref)
aligned_force = force_interp(t_ref)
```

### Option 2: Learn from Raw Timestamps

Include timestamps as features:
```python
# Relative timestamps (from first frame)
t0 = ts_camera[0]
rel_ts_camera = ts_camera - t0
rel_ts_pose = ts_pose - t0
rel_ts_force = ts_force - t0

# Model can learn temporal relationships
features = {
    'image': images,
    'state': states,
    'force': forces,
    'ts_camera': rel_ts_camera,
    'ts_pose': rel_ts_pose,
    'ts_force': rel_ts_force
}
```

## Troubleshooting

### "Episode does not have per-sensor timestamps"

Your episode was collected with an older version (< v0.3.1).

**Solution**: Re-collect data with updated code, or upgrade episode format:
```python
# TODO: Add upgrade script
```

### Analysis tool crashes

**Possible causes**:
- Corrupted HDF5 file
- Missing dependencies (matplotlib)

**Solutions**:
```bash
# Check file
h5ls episode.hdf5

# Install dependencies
pip install matplotlib scipy
```

### Timestamps seem wrong (future dates, negative intervals)

**Cause**: System clock changed during collection

**Solution**: 
- Ensure NTP synchronization is disabled during collection
- Use relative timestamps (from first frame) for analysis

## See Also

- [Data Quality Verification](../verify_data_quality.py)
- [Replay Guide](REPLAY_GUIDE.md)
- [Units and Conventions](../UNITS_AND_CONVENTIONS.md)

