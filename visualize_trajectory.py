"""
Visualize Action Trajectory and Initial Coordinate Frame from HDF5 Files

This script reads HDF5 files and visualizes:
1. Action trajectory (by accumulating action deltas)
2. State trajectory (actual position sequence)
3. Initial coordinate frame
4. Gripper state (represented by color or size)
"""

import sys
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from pathlib import Path
from forceumi.data import HDF5Manager


def plot_coordinate_frame(
    ax,
    origin: np.ndarray,
    rotation_matrix: np.ndarray = None,
    scale: float = 0.1,
    label: str = "Frame"
):
    """
    Plot a coordinate frame
    
    Args:
        ax: matplotlib 3D axis
        origin: Frame origin [x, y, z]
        rotation_matrix: 3x3 rotation matrix (if None, uses identity matrix)
        scale: Axis length
        label: Frame label
    """
    if rotation_matrix is None:
        rotation_matrix = np.eye(3)
    
    # X-axis - red
    x_axis = rotation_matrix[:, 0] * scale
    ax.quiver(origin[0], origin[1], origin[2],
              x_axis[0], x_axis[1], x_axis[2],
              color='red', linewidth=2, arrow_length_ratio=0.3)
    
    # Y-axis - green
    y_axis = rotation_matrix[:, 1] * scale
    ax.quiver(origin[0], origin[1], origin[2],
              y_axis[0], y_axis[1], y_axis[2],
              color='green', linewidth=2, arrow_length_ratio=0.3)
    
    # Z-axis - blue
    z_axis = rotation_matrix[:, 2] * scale
    ax.quiver(origin[0], origin[1], origin[2],
              z_axis[0], z_axis[1], z_axis[2],
              color='blue', linewidth=2, arrow_length_ratio=0.3)
    
    # Add label
    ax.text(origin[0], origin[1], origin[2], label, fontsize=10, weight='bold')


def euler_to_rotation_matrix(euler_angles: np.ndarray) -> np.ndarray:
    """
    Convert Euler angles to rotation matrix
    
    Args:
        euler_angles: Euler angles [rx, ry, rz] (radians)
    
    Returns:
        3x3 rotation matrix
    """
    rx, ry, rz = euler_angles
    
    # Rotation around X-axis
    Rx = np.array([
        [1, 0, 0],
        [0, np.cos(rx), -np.sin(rx)],
        [0, np.sin(rx), np.cos(rx)]
    ])
    
    # Rotation around Y-axis
    Ry = np.array([
        [np.cos(ry), 0, np.sin(ry)],
        [0, 1, 0],
        [-np.sin(ry), 0, np.cos(ry)]
    ])
    
    # Rotation around Z-axis
    Rz = np.array([
        [np.cos(rz), -np.sin(rz), 0],
        [np.sin(rz), np.cos(rz), 0],
        [0, 0, 1]
    ])
    
    # Combined rotation matrix (ZYX order)
    return Rz @ Ry @ Rx


def compute_trajectory_from_actions(
    initial_state: np.ndarray,
    actions: np.ndarray
) -> np.ndarray:
    """
    Compute trajectory by accumulating actions
    
    Args:
        initial_state: Initial state [x, y, z, rx, ry, rz, gripper]
        actions: Actions array (N, 7) [dx, dy, dz, drx, dry, drz, gripper]
    
    Returns:
        Trajectory array (N+1, 7) - includes initial state
    """
    trajectory = np.zeros((len(actions) + 1, 7))
    trajectory[0] = initial_state
    
    for i, action in enumerate(actions):
        # Note: gripper value in action is absolute, not incremental
        trajectory[i + 1, :6] = trajectory[i, :6] + action[:6]
        trajectory[i + 1, 6] = action[6]  # Gripper is absolute value
    
    return trajectory


def visualize_trajectory(
    filepath: str,
    show_action_trajectory: bool = True,
    frame_interval: int = 10
):
    """
    Visualize trajectory from HDF5 file
    
    Args:
        filepath: Path to HDF5 file
        show_action_trajectory: Whether to show trajectory computed from accumulated actions
        frame_interval: Interval for plotting coordinate frames along trajectory (e.g., 10 means every 10th frame)
    """
    # Load data
    print(f"Loading: {filepath}")
    manager = HDF5Manager()
    data = manager.load_episode(filepath)
    
    if data is None:
        print("Error: Failed to load episode data")
        return
    
    # Extract data
    states = data.get("state", np.array([]))
    actions = data.get("action", np.array([]))
    timestamps = data.get("timestamp", np.array([]))
    
    if len(states) == 0:
        print("Error: No state data available")
        return
    
    print(f"\nData Overview:")
    print(f"  Number of states: {len(states)}")
    print(f"  Number of actions: {len(actions)}")
    print(f"  Time span: {timestamps[-1] - timestamps[0]:.2f} seconds")
    
    # Create figure
    fig = plt.figure(figsize=(16, 12))
    
    # 3D trajectory plot
    ax1 = fig.add_subplot(221, projection='3d')
    
    # Plot initial coordinate frame
    initial_state = states[0]
    initial_position = initial_state[:3]
    initial_orientation = initial_state[3:6]
    
    # Calculate axis scale (based on trajectory range)
    position_range = np.max(states[:, :3], axis=0) - np.min(states[:, :3], axis=0)
    axis_scale = np.max(position_range) * 0.15  # Slightly smaller to avoid clutter
    
    initial_rotation = euler_to_rotation_matrix(initial_orientation)
    plot_coordinate_frame(ax1, initial_position, initial_rotation, 
                         scale=axis_scale, label="Initial Frame")
    
    # Plot coordinate frames along the trajectory at intervals
    state_positions = states[:, :3]
    state_orientations = states[:, 3:6]
    gripper_states = states[:, 6]
    
    for i in range(0, len(states), frame_interval):
        if i == 0:  # Skip initial frame (already plotted)
            continue
        position = state_positions[i]
        orientation = state_orientations[i]
        rotation = euler_to_rotation_matrix(orientation)
        plot_coordinate_frame(ax1, position, rotation, scale=axis_scale, label="")
    
    # Plot final coordinate frame if not already plotted
    if (len(states) - 1) % frame_interval != 0:
        final_position = state_positions[-1]
        final_orientation = state_orientations[-1]
        final_rotation = euler_to_rotation_matrix(final_orientation)
        plot_coordinate_frame(ax1, final_position, final_rotation, 
                            scale=axis_scale, label="Final Frame")
    
    # Use gripper state as color mapping
    colors = plt.cm.viridis(gripper_states / np.max(gripper_states) if np.max(gripper_states) > 0 else gripper_states)
    
    for i in range(len(state_positions) - 1):
        ax1.plot(state_positions[i:i+2, 0],
                state_positions[i:i+2, 1],
                state_positions[i:i+2, 2],
                color=colors[i], linewidth=2, alpha=0.7)
    
    # Mark start and end points
    ax1.scatter(*initial_position, color='green', s=200, marker='o', 
               label='Start Position', edgecolors='black', linewidths=2)
    ax1.scatter(*state_positions[-1], color='red', s=200, marker='X',
               label='End Position', edgecolors='black', linewidths=2)
    
    # If actions available, plot trajectory computed from accumulated actions
    if show_action_trajectory and len(actions) > 0:
        action_trajectory = compute_trajectory_from_actions(initial_state, actions)
        action_positions = action_trajectory[:, :3]
        ax1.plot(action_positions[:, 0],
                action_positions[:, 1],
                action_positions[:, 2],
                'r--', linewidth=1, alpha=0.5, label='Action Accumulated')
    
    ax1.set_xlabel('X (m)')
    ax1.set_ylabel('Y (m)')
    ax1.set_zlabel('Z (m)')
    ax1.set_title('3D Trajectory')
    ax1.legend()
    ax1.grid(True)
    
    # XY plane projection
    ax2 = fig.add_subplot(222)
    ax2.plot(state_positions[:, 0], state_positions[:, 1], 'b-', linewidth=2, label='Trajectory')
    ax2.scatter(initial_position[0], initial_position[1], color='green', s=150, 
               marker='o', label='Start', zorder=5, edgecolors='black', linewidths=2)
    ax2.scatter(state_positions[-1, 0], state_positions[-1, 1], color='red', s=150,
               marker='X', label='End', zorder=5, edgecolors='black', linewidths=2)
    ax2.set_xlabel('X (m)')
    ax2.set_ylabel('Y (m)')
    ax2.set_title('XY Plane Projection')
    ax2.grid(True)
    ax2.axis('equal')
    ax2.legend()
    
    # Position over time
    ax3 = fig.add_subplot(223)
    time_elapsed = timestamps - timestamps[0]
    ax3.plot(time_elapsed, state_positions[:, 0], 'r-', label='X', linewidth=2)
    ax3.plot(time_elapsed, state_positions[:, 1], 'g-', label='Y', linewidth=2)
    ax3.plot(time_elapsed, state_positions[:, 2], 'b-', label='Z', linewidth=2)
    ax3.set_xlabel('Time (s)')
    ax3.set_ylabel('Position (m)')
    ax3.set_title('Position over Time')
    ax3.grid(True)
    ax3.legend()
    
    # Gripper and orientation over time
    ax4 = fig.add_subplot(224)
    ax4_twin = ax4.twinx()
    
    # Gripper on left Y-axis
    line1 = ax4.plot(time_elapsed, gripper_states, 'purple', linewidth=2, label='Gripper')
    ax4.set_xlabel('Time (s)')
    ax4.set_ylabel('Gripper State', color='purple')
    ax4.tick_params(axis='y', labelcolor='purple')
    ax4.grid(True)
    
    # Orientation on right Y-axis
    orientations = states[:, 3:6]
    line2 = ax4_twin.plot(time_elapsed, np.rad2deg(orientations[:, 0]), 'r--', 
                         label='Roll', alpha=0.7)
    line3 = ax4_twin.plot(time_elapsed, np.rad2deg(orientations[:, 1]), 'g--', 
                         label='Pitch', alpha=0.7)
    line4 = ax4_twin.plot(time_elapsed, np.rad2deg(orientations[:, 2]), 'b--', 
                         label='Yaw', alpha=0.7)
    ax4_twin.set_ylabel('Orientation (degrees)', color='black')
    ax4_twin.tick_params(axis='y', labelcolor='black')
    
    # Combine legends
    lines = line1 + line2 + line3 + line4
    labels = [line.get_label() for line in lines]
    ax4.legend(lines, labels, loc='best')
    
    ax4.set_title('Gripper and Orientation over Time')
    
    # Add overall title
    metadata = data.get("metadata", {})
    duration = metadata.get("duration", timestamps[-1] - timestamps[0])
    num_frames = len(states)
    fps = metadata.get("fps", num_frames / duration if duration > 0 else 0)
    
    fig.suptitle(f'Episode Trajectory Visualization\n'
                f'Duration: {duration:.2f}s | Frames: {num_frames} | FPS: {fps:.2f}',
                fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    plt.show()
    
    # Print statistics
    print(f"\nTrajectory Statistics:")
    print(f"  Position Range:")
    print(f"    X: [{np.min(state_positions[:, 0]):.4f}, {np.max(state_positions[:, 0]):.4f}] m")
    print(f"    Y: [{np.min(state_positions[:, 1]):.4f}, {np.max(state_positions[:, 1]):.4f}] m")
    print(f"    Z: [{np.min(state_positions[:, 2]):.4f}, {np.max(state_positions[:, 2]):.4f}] m")
    
    # Calculate total trajectory length
    distances = np.linalg.norm(np.diff(state_positions, axis=0), axis=1)
    total_distance = np.sum(distances)
    print(f"  Total Trajectory Length: {total_distance:.4f} m")
    print(f"  Average Velocity: {total_distance / duration:.4f} m/s")
    
    if len(actions) > 0:
        print(f"\n  Action Statistics:")
        print(f"    Position Delta Mean: [{np.mean(actions[:, 0]):.6f}, {np.mean(actions[:, 1]):.6f}, {np.mean(actions[:, 2]):.6f}] m")
        print(f"    Position Delta Std: [{np.std(actions[:, 0]):.6f}, {np.std(actions[:, 1]):.6f}, {np.std(actions[:, 2]):.6f}] m")
        print(f"    Orientation Delta Mean: [{np.rad2deg(np.mean(actions[:, 3])):.4f}, {np.rad2deg(np.mean(actions[:, 4])):.4f}, {np.rad2deg(np.mean(actions[:, 5])):.4f}] degrees")


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python visualize_trajectory.py <path_to_episode.hdf5> [options]")
        print("\nExample:")
        print("  python visualize_trajectory.py data/episode_20250116_120000.hdf5")
        print("  python visualize_trajectory.py data/episode_20250116_120000.hdf5 --interval 5")
        print("\nOptional arguments:")
        print("  --no-action-trajectory    Do not show trajectory computed from accumulated actions")
        print("  --interval N              Plot coordinate frame every N frames (default: 10)")
        print("  --interval all            Plot coordinate frame at all frames")
        return
    
    filepath = sys.argv[1]
    show_action_trajectory = "--no-action-trajectory" not in sys.argv
    
    # Parse frame interval
    frame_interval = 10  # default
    if "--interval" in sys.argv:
        interval_idx = sys.argv.index("--interval")
        if interval_idx + 1 < len(sys.argv):
            interval_value = sys.argv[interval_idx + 1]
            if interval_value.lower() == "all":
                frame_interval = 1
            else:
                try:
                    frame_interval = int(interval_value)
                except ValueError:
                    print(f"Warning: Invalid interval value '{interval_value}', using default 10")
    
    if not Path(filepath).exists():
        print(f"Error: File does not exist: {filepath}")
        return
    
    print("=" * 60)
    print("ForceUMI Trajectory Visualization Tool")
    print("=" * 60)
    print(f"Settings: Frame interval = {frame_interval}")
    
    visualize_trajectory(filepath, show_action_trajectory, frame_interval)
    
    print("\n" + "=" * 60)
    print("Visualization Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()

