"""
Coordinate Transformation Utilities

Provides functions for 3D pose transformations, including:
- Euler angle <-> Rotation matrix conversions
- Quaternion <-> Rotation matrix conversions  
- Relative pose calculations
- Pose transformations
- Coordinate frame alignment
"""

import numpy as np
from typing import Tuple, Optional


def rotate_frame_z_90_cw(pose: np.ndarray, preserve_gripper: bool = True) -> np.ndarray:
    """
    Rotate pose frame 90 degrees clockwise around z-axis (viewed from +z).
    
    This aligns the coordinate system with the force sensor coordinate system.
    
    Transformation (for position and orientation):
    - new_x = old_y
    - new_y = -old_x
    - new_z = old_z
    
    Args:
        pose: 7D pose [x, y, z, rx, ry, rz, gripper] with angles in radians
        preserve_gripper: If True, keep gripper value unchanged
    
    Returns:
        Transformed 7D pose in the rotated frame
    """
    result = pose.copy()
    
    # Position transformation: rotate point 90° CW around z-axis
    x, y, z = pose[0], pose[1], pose[2]
    result[0] = y      # new_x = old_y
    result[1] = -x     # new_y = -old_x
    result[2] = z      # new_z = old_z (unchanged)
    
    # Orientation transformation
    # Convert Euler angles to rotation matrix
    R = euler_to_matrix(pose[3], pose[4], pose[5])
    
    # Z-axis rotation matrix (90° clockwise = -90° = 270°)
    # When viewed from +z, clockwise means negative rotation
    theta = -np.pi / 2  # -90 degrees
    R_z_90cw = np.array([
        [np.cos(theta), -np.sin(theta), 0],
        [np.sin(theta),  np.cos(theta), 0],
        [0,              0,              1]
    ])
    # Which simplifies to:
    # R_z_90cw = [[0, 1, 0],
    #             [-1, 0, 0],
    #             [0, 0, 1]]
    
    # Apply rotation: R_new = R_z_90cw @ R
    R_new = R_z_90cw @ R
    
    # Convert back to Euler angles
    euler_new = matrix_to_euler(R_new)
    result[3:6] = euler_new
    
    # Gripper unchanged (always absolute)
    if preserve_gripper:
        result[6] = pose[6]
    
    return result


def rotate_frame_z_90_ccw(pose: np.ndarray, preserve_gripper: bool = True) -> np.ndarray:
    """
    Rotate pose frame 90 degrees counter-clockwise around z-axis (viewed from +z).
    
    This is the inverse of rotate_frame_z_90_cw().
    
    Transformation (for position and orientation):
    - new_x = -old_y
    - new_y = old_x
    - new_z = old_z
    
    Args:
        pose: 7D pose [x, y, z, rx, ry, rz, gripper] with angles in radians
        preserve_gripper: If True, keep gripper value unchanged
    
    Returns:
        Transformed 7D pose in the rotated frame
    """
    result = pose.copy()
    
    # Position transformation: rotate point 90° CCW around z-axis
    x, y, z = pose[0], pose[1], pose[2]
    result[0] = -y     # new_x = -old_y
    result[1] = x      # new_y = old_x
    result[2] = z      # new_z = old_z (unchanged)
    
    # Orientation transformation
    # Convert Euler angles to rotation matrix
    R = euler_to_matrix(pose[3], pose[4], pose[5])
    
    # Z-axis rotation matrix (90° counter-clockwise = +90°)
    # When viewed from +z, counter-clockwise means positive rotation
    theta = np.pi / 2  # +90 degrees
    R_z_90ccw = np.array([
        [np.cos(theta), -np.sin(theta), 0],
        [np.sin(theta),  np.cos(theta), 0],
        [0,              0,              1]
    ])
    # Which simplifies to:
    # R_z_90ccw = [[0, -1, 0],
    #              [1,  0, 0],
    #              [0,  0, 1]]
    
    # Apply rotation: R_new = R_z_90ccw @ R
    R_new = R_z_90ccw @ R
    
    # Convert back to Euler angles
    euler_new = matrix_to_euler(R_new)
    result[3:6] = euler_new
    
    # Gripper unchanged (always absolute)
    if preserve_gripper:
        result[6] = pose[6]
    
    return result


def euler_to_matrix(roll: float, pitch: float, yaw: float) -> np.ndarray:
    """
    Convert Euler angles (roll, pitch, yaw) to rotation matrix
    Uses ZYX convention (yaw-pitch-roll)
    
    Args:
        roll: Rotation around X axis (radians)
        pitch: Rotation around Y axis (radians)
        yaw: Rotation around Z axis (radians)
        
    Returns:
        np.ndarray: 3x3 rotation matrix
    """
    # Roll (X-axis rotation)
    R_x = np.array([
        [1, 0, 0],
        [0, np.cos(roll), -np.sin(roll)],
        [0, np.sin(roll), np.cos(roll)]
    ])
    
    # Pitch (Y-axis rotation)
    R_y = np.array([
        [np.cos(pitch), 0, np.sin(pitch)],
        [0, 1, 0],
        [-np.sin(pitch), 0, np.cos(pitch)]
    ])
    
    # Yaw (Z-axis rotation)
    R_z = np.array([
        [np.cos(yaw), -np.sin(yaw), 0],
        [np.sin(yaw), np.cos(yaw), 0],
        [0, 0, 1]
    ])
    
    # Combined rotation: R = R_z * R_y * R_x
    R = R_z @ R_y @ R_x
    
    return R


def matrix_to_euler(R: np.ndarray) -> Tuple[float, float, float]:
    """
    Convert rotation matrix to Euler angles (roll, pitch, yaw)
    Uses ZYX convention
    
    Args:
        R: 3x3 rotation matrix
        
    Returns:
        tuple: (roll, pitch, yaw) in radians
    """
    sy = np.sqrt(R[0, 0]**2 + R[1, 0]**2)
    
    singular = sy < 1e-6
    
    if not singular:
        roll = np.arctan2(R[2, 1], R[2, 2])
        pitch = np.arctan2(-R[2, 0], sy)
        yaw = np.arctan2(R[1, 0], R[0, 0])
    else:
        roll = np.arctan2(-R[1, 2], R[1, 1])
        pitch = np.arctan2(-R[2, 0], sy)
        yaw = 0
    
    return roll, pitch, yaw


def quaternion_to_matrix(qw: float, qx: float, qy: float, qz: float) -> np.ndarray:
    """
    Convert quaternion to rotation matrix
    
    Args:
        qw: Quaternion w component
        qx: Quaternion x component
        qy: Quaternion y component
        qz: Quaternion z component
        
    Returns:
        np.ndarray: 3x3 rotation matrix
    """
    # Normalize quaternion
    norm = np.sqrt(qw**2 + qx**2 + qy**2 + qz**2)
    qw, qx, qy, qz = qw/norm, qx/norm, qy/norm, qz/norm
    
    # Compute rotation matrix
    R = np.array([
        [1 - 2*(qy**2 + qz**2), 2*(qx*qy - qw*qz), 2*(qx*qz + qw*qy)],
        [2*(qx*qy + qw*qz), 1 - 2*(qx**2 + qz**2), 2*(qy*qz - qw*qx)],
        [2*(qx*qz - qw*qy), 2*(qy*qz + qw*qx), 1 - 2*(qx**2 + qy**2)]
    ])
    
    return R


def matrix_to_quaternion(R: np.ndarray) -> Tuple[float, float, float, float]:
    """
    Convert rotation matrix to quaternion
    
    Args:
        R: 3x3 rotation matrix
        
    Returns:
        tuple: (qw, qx, qy, qz)
    """
    trace = np.trace(R)
    
    if trace > 0:
        s = 0.5 / np.sqrt(trace + 1.0)
        qw = 0.25 / s
        qx = (R[2, 1] - R[1, 2]) * s
        qy = (R[0, 2] - R[2, 0]) * s
        qz = (R[1, 0] - R[0, 1]) * s
    elif R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
        s = 2.0 * np.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2])
        qw = (R[2, 1] - R[1, 2]) / s
        qx = 0.25 * s
        qy = (R[0, 1] + R[1, 0]) / s
        qz = (R[0, 2] + R[2, 0]) / s
    elif R[1, 1] > R[2, 2]:
        s = 2.0 * np.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2])
        qw = (R[0, 2] - R[2, 0]) / s
        qx = (R[0, 1] + R[1, 0]) / s
        qy = 0.25 * s
        qz = (R[1, 2] + R[2, 1]) / s
    else:
        s = 2.0 * np.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1])
        qw = (R[1, 0] - R[0, 1]) / s
        qx = (R[0, 2] + R[2, 0]) / s
        qy = (R[1, 2] + R[2, 1]) / s
        qz = 0.25 * s
    
    return qw, qx, qy, qz


def pose_to_matrix(pose: np.ndarray) -> np.ndarray:
    """
    Convert pose [x, y, z, rx, ry, rz] to 4x4 transformation matrix
    
    Args:
        pose: 6D pose array [x, y, z, rx, ry, rz] (angles in radians)
        
    Returns:
        np.ndarray: 4x4 homogeneous transformation matrix
    """
    x, y, z, rx, ry, rz = pose[:6]
    
    # Get rotation matrix from Euler angles
    R = euler_to_matrix(rx, ry, rz)
    
    # Create 4x4 transformation matrix
    T = np.eye(4)
    T[:3, :3] = R
    T[:3, 3] = [x, y, z]
    
    return T


def matrix_to_pose(T: np.ndarray) -> np.ndarray:
    """
    Convert 4x4 transformation matrix to pose [x, y, z, rx, ry, rz]
    
    Args:
        T: 4x4 homogeneous transformation matrix
        
    Returns:
        np.ndarray: 6D pose array [x, y, z, rx, ry, rz] (angles in radians)
    """
    # Extract translation
    x, y, z = T[:3, 3]
    
    # Extract rotation and convert to Euler angles
    R = T[:3, :3]
    rx, ry, rz = matrix_to_euler(R)
    
    return np.array([x, y, z, rx, ry, rz], dtype=np.float32)


def inverse_transform(T: np.ndarray) -> np.ndarray:
    """
    Compute inverse of a 4x4 transformation matrix
    
    Args:
        T: 4x4 homogeneous transformation matrix
        
    Returns:
        np.ndarray: Inverse transformation matrix
    """
    # For rigid body transformations: T^-1 = [R^T, -R^T*t; 0, 1]
    R = T[:3, :3]
    t = T[:3, 3]
    
    T_inv = np.eye(4)
    T_inv[:3, :3] = R.T
    T_inv[:3, 3] = -R.T @ t
    
    return T_inv


def transform_pose(pose: np.ndarray, reference_pose: np.ndarray) -> np.ndarray:
    """
    Transform a pose from world frame to a reference frame
    
    Args:
        pose: Current pose [x, y, z, rx, ry, rz] in world frame
        reference_pose: Reference frame pose [x, y, z, rx, ry, rz] in world frame
        
    Returns:
        np.ndarray: Pose in reference frame [x, y, z, rx, ry, rz]
    """
    # Convert poses to transformation matrices
    T_world_current = pose_to_matrix(pose)
    T_world_reference = pose_to_matrix(reference_pose)
    
    # Compute relative transformation: T_ref_current = T_world_ref^-1 * T_world_current
    T_ref_inv = inverse_transform(T_world_reference)
    T_ref_current = T_ref_inv @ T_world_current
    
    # Convert back to pose
    relative_pose = matrix_to_pose(T_ref_current)
    
    return relative_pose


def relative_pose(pose: np.ndarray, reference_pose: np.ndarray, 
                  preserve_gripper: bool = True) -> np.ndarray:
    """
    Compute relative pose from reference frame
    Handles both 6D and 7D poses (with gripper)
    
    Args:
        pose: Current pose [x, y, z, rx, ry, rz, (gripper)] in world frame
        reference_pose: Reference frame pose [x, y, z, rx, ry, rz, (gripper)] in world frame
        preserve_gripper: If True, preserve gripper value from original pose
        
    Returns:
        np.ndarray: Relative pose in reference frame
    """
    # Handle gripper dimension
    has_gripper = len(pose) == 7
    
    # Extract 6D pose
    pose_6d = pose[:6]
    reference_6d = reference_pose[:6]
    
    # Compute relative 6D pose
    relative_6d = transform_pose(pose_6d, reference_6d)
    
    # Add gripper if present
    if has_gripper and preserve_gripper:
        gripper = pose[6]  # Keep absolute gripper value
        return np.append(relative_6d, gripper).astype(np.float32)
    else:
        return relative_6d.astype(np.float32)


def batch_relative_poses(poses: np.ndarray, reference_pose: np.ndarray) -> np.ndarray:
    """
    Compute relative poses for a batch of poses
    
    Args:
        poses: Array of poses, shape (N, 6) or (N, 7)
        reference_pose: Reference frame pose [x, y, z, rx, ry, rz, (gripper)]
        
    Returns:
        np.ndarray: Array of relative poses, same shape as input
    """
    N = poses.shape[0]
    relative_poses = np.zeros_like(poses)
    
    for i in range(N):
        relative_poses[i] = relative_pose(poses[i], reference_pose)
    
    return relative_poses

