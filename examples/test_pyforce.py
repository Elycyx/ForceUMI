"""
Test PyForce Integration with ForceSensor

This example demonstrates how to use the ForceSensor class with PyForce
for force/torque data acquisition from Sunrise (宇立) sensors.
"""

import time
from forceumi.devices import ForceSensor


def main():
    """Test PyForce integration"""
    print("ForceUMI PyForce Integration Test")
    print("=" * 50)
    
    # Check if PyForce is available
    try:
        from pyforce import ForceSensor as PyForceSensor
        print("✓ PyForce is installed")
    except ImportError:
        print("✗ PyForce is NOT installed")
        print("\nTo install PyForce, run:")
        print("  pip install git+https://github.com/Elycyx/PyForce.git")
        print("\nMake sure the Sunrise force sensor is connected to the network.")
        return
    
    print("\nMake sure:")
    print("1. Force sensor is powered on")
    print("2. Force sensor is connected to the network")
    print("3. IP address is configured correctly (default: 192.168.0.108)")
    print()
    
    # Get sensor configuration from user
    ip_addr = input("Enter sensor IP address [192.168.0.108]: ").strip() or "192.168.0.108"
    port = input("Enter sensor port [4008]: ").strip()
    port = int(port) if port else 4008
    
    # Initialize force sensor
    print(f"\nInitializing ForceSensor at {ip_addr}:{port}...")
    sensor = ForceSensor(ip_addr=ip_addr, port=port, sample_rate=100)
    
    # Connect to the sensor
    print("\nConnecting to force sensor...")
    if not sensor.connect():
        print("Failed to connect. Check:")
        print("  - Sensor is powered on")
        print("  - IP address and port are correct")
        print("  - Network connection is working (try: ping", ip_addr, ")")
        return
    
    print("\n✓ Connected successfully!")
    
    # Get sensor info
    info = sensor.get_sensor_info()
    if info:
        print(f"\nSensor Info:")
        for key, value in info.items():
            print(f"  {key}: {value}")
    
    # Zero calibration
    print("\n" + "=" * 50)
    print("Zero Calibration")
    print("=" * 50)
    print("Make sure no external forces are applied to the sensor...")
    input("Press Enter to start zero calibration...")
    
    if sensor.zero(num_samples=50):
        print(f"✓ Sensor zeroed successfully")
        print(f"  Bias: {sensor.bias}")
    else:
        print("✗ Zero calibration failed")
        return
    
    # Read force data in real-time
    print("\n" + "=" * 50)
    print("Reading force data (Ctrl+C to stop)...")
    print("=" * 50)
    print("Format: [fx, fy, fz, mx, my, mz]")
    print("Units: Force (N), Torque (Nm)")
    print()
    
    try:
        frame_count = 0
        while True:
            # Read 6-axis force/torque
            force = sensor.read()
            
            if force is not None:
                fx, fy, fz, mx, my, mz = force
                print(f"Frame {frame_count:4d} | "
                      f"Force: [{fx:7.3f}, {fy:7.3f}, {fz:7.3f}] N | "
                      f"Torque: [{mx:7.3f}, {my:7.3f}, {mz:7.3f}] Nm")
                frame_count += 1
            else:
                print("Warning: Failed to read force data")
            
            time.sleep(0.01)  # ~100 Hz
    
    except KeyboardInterrupt:
        print("\n\nStopped by user")
    
    # Test with timestamp
    print("\nReading force with timestamp...")
    data = sensor.get_with_timestamp()
    if data:
        print(f"Force/Torque: {data['ft']}")
        print(f"Timestamp: {data['timestamp']}")
    
    # Test sample rate change
    print("\nChanging sample rate to 200 Hz...")
    if sensor.set_sample_rate(200):
        print("✓ Sample rate changed successfully")
    
    # Disconnect
    print("\nDisconnecting...")
    sensor.disconnect()
    print("✓ Disconnected")
    
    print("\n" + "=" * 50)
    print("Test completed successfully!")


if __name__ == "__main__":
    main()

