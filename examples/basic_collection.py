"""
Basic Data Collection Example

Demonstrates simple programmatic data collection without GUI.
"""

import time
from forceumi.collector import DataCollector
from forceumi.devices import Camera, PoseSensor, ForceSensor


def main():
    """Basic collection example"""
    print("ForceUMI Basic Collection Example")
    print("=" * 50)
    
    # Initialize devices
    print("\n1. Initializing devices...")
    camera = Camera(device_id=0, width=640, height=480, fps=30)
    pose_sensor = PoseSensor(port="/dev/ttyUSB0")
    force_sensor = ForceSensor(port="/dev/ttyUSB1")
    
    # Create collector
    print("2. Creating data collector...")
    collector = DataCollector(
        camera=camera,
        pose_sensor=pose_sensor,
        force_sensor=force_sensor,
        save_dir="./data",
        auto_save=True
    )
    
    # Connect devices
    print("3. Connecting to devices...")
    status = collector.connect_devices()
    for device, connected in status.items():
        print(f"   {device}: {'Connected' if connected else 'Failed'}")
    
    # Start collection
    print("\n4. Starting data collection...")
    metadata = {
        "task_description": "Basic collection example",
        "operator": "example_user",
    }
    collector.start_episode(metadata=metadata)
    
    # Collect for 10 seconds
    print("   Collecting data for 10 seconds...")
    try:
        for i in range(10):
            time.sleep(1)
            stats = collector.get_episode_stats()
            print(f"   Frame {stats['num_frames']}, Duration: {stats['duration']:.1f}s")
    
    except KeyboardInterrupt:
        print("\n   Collection interrupted by user")
    
    # Stop and save
    print("\n5. Stopping collection...")
    filepath = collector.stop_episode()
    
    if filepath:
        print(f"   Episode saved to: {filepath}")
    
    # Disconnect devices
    print("6. Disconnecting devices...")
    collector.disconnect_devices()
    
    print("\nDone!")


if __name__ == "__main__":
    main()

