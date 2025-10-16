"""
Test PyTracker Integration with PoseSensor

This example demonstrates how to use the PoseSensor class with PyTracker
for VR tracking-based pose estimation.
"""

import time
from forceumi.devices import PoseSensor


def main():
    """Test PyTracker integration"""
    print("ForceUMI PyTracker Integration Test")
    print("=" * 50)
    
    # Check if PyTracker is available
    try:
        import pytracker
        print("✓ PyTracker is installed")
    except ImportError:
        print("✗ PyTracker is NOT installed")
        print("\nTo install PyTracker, run:")
        print("  pip install git+https://github.com/Elycyx/PyTracker.git")
        print("\nMake sure SteamVR is running with VR hardware connected.")
        return
    
    print("\nMake sure:")
    print("1. SteamVR is running")
    print("2. VR tracker is connected and tracked")
    print("3. You have a config.json file (optional) to name your devices")
    print()
    
    # Initialize pose sensor
    # Option 1: Use default tracker name
    print("Initializing PoseSensor with default tracker name 'tracker_1'...")
    sensor = PoseSensor(device_name="tracker_1")
    
    # Option 2: Use custom config file
    # sensor = PoseSensor(device_name="my_tracker", config_file="config.json")
    
    # Connect to the tracker
    print("\nConnecting to tracker...")
    if not sensor.connect():
        print("Failed to connect. Check the available devices above.")
        return
    
    print("\n✓ Connected successfully!")
    
    # Get device info
    info = sensor.get_device_info()
    print(f"\nDevice Info:")
    print(f"  Name: {info.get('device_name')}")
    print(f"  Type: {info.get('device_type')}")
    print(f"  Serial: {info.get('serial')}")
    
    # Read pose data in real-time
    print("\n" + "=" * 50)
    print("Reading pose data (Ctrl+C to stop)...")
    print("=" * 50)
    print("Format: [x, y, z, rx, ry, rz, gripper]")
    print()
    
    try:
        frame_count = 0
        while True:
            # Read 7D state
            state = sensor.read()
            
            if state is not None:
                x, y, z, rx, ry, rz, gripper = state
                print(f"Frame {frame_count:4d} | "
                      f"Pos: [{x:6.3f}, {y:6.3f}, {z:6.3f}] | "
                      f"Rot: [{rx:6.3f}, {ry:6.3f}, {rz:6.3f}] | "
                      f"Gripper: {gripper:.3f}")
                frame_count += 1
            else:
                print("Warning: Failed to read pose data")
            
            time.sleep(0.033)  # ~30 Hz
    
    except KeyboardInterrupt:
        print("\n\nStopped by user")
    
    # Test velocity reading
    print("\nReading velocity...")
    velocity = sensor.get_velocity()
    if velocity is not None:
        print(f"Linear velocity: {velocity}")
    
    angular_velocity = sensor.get_angular_velocity()
    if angular_velocity is not None:
        print(f"Angular velocity: {angular_velocity}")
    
    # Test sampling
    print("\nCollecting 100 samples at 50 Hz...")
    samples = sensor.sample(num_samples=100, sample_rate=50.0)
    if samples is not None:
        print(f"Collected {len(samples)} samples")
        print(f"Sample shape: {samples.shape}")
        print(f"First sample: {samples[0]}")
        print(f"Last sample: {samples[-1]}")
    
    # Test quaternion format
    print("\nReading pose in quaternion format...")
    quat_pose = sensor.get_pose_quaternion()
    if quat_pose is not None:
        print(f"Quaternion pose (8D): {quat_pose}")
    
    # Disconnect
    print("\nDisconnecting...")
    sensor.disconnect()
    print("✓ Disconnected")
    
    print("\n" + "=" * 50)
    print("Test completed successfully!")


if __name__ == "__main__":
    main()

