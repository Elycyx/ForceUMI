#!/usr/bin/env python3
"""
Test Coordinate Transformation Functions

Verifies that the transformation utilities work correctly
"""

import numpy as np
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from forceumi.utils.transforms import (
    euler_to_matrix,
    matrix_to_euler,
    pose_to_matrix,
    matrix_to_pose,
    inverse_transform,
    relative_pose
)


def test_euler_matrix_conversion():
    """Test Euler angle <-> rotation matrix conversion"""
    print("Testing Euler angle <-> rotation matrix conversion...")
    
    # Test angles (roll, pitch, yaw)
    angles = [0.1, 0.2, 0.3]  # radians
    
    # Convert to matrix and back
    R = euler_to_matrix(*angles)
    angles_back = matrix_to_euler(R)
    
    # Check if we get back the same angles
    error = np.linalg.norm(np.array(angles) - np.array(angles_back))
    
    print(f"  Original angles: {np.array(angles)}")
    print(f"  Recovered angles: {np.array(angles_back)}")
    print(f"  Error: {error:.6f}")
    
    if error < 1e-6:
        print("  ✅ PASS\n")
        return True
    else:
        print("  ❌ FAIL\n")
        return False


def test_pose_matrix_conversion():
    """Test pose <-> transformation matrix conversion"""
    print("Testing pose <-> transformation matrix conversion...")
    
    # Test pose [x, y, z, rx, ry, rz]
    pose = np.array([1.0, 2.0, 3.0, 0.1, 0.2, 0.3])
    
    # Convert to matrix and back
    T = pose_to_matrix(pose)
    pose_back = matrix_to_pose(T)
    
    # Check if we get back the same pose
    error = np.linalg.norm(pose - pose_back)
    
    print(f"  Original pose: {pose}")
    print(f"  Recovered pose: {pose_back}")
    print(f"  Error: {error:.6f}")
    
    if error < 1e-6:
        print("  ✅ PASS\n")
        return True
    else:
        print("  ❌ FAIL\n")
        return False


def test_inverse_transform():
    """Test transformation matrix inversion"""
    print("Testing transformation matrix inversion...")
    
    # Create a transformation matrix
    pose = np.array([1.0, 2.0, 3.0, 0.1, 0.2, 0.3])
    T = pose_to_matrix(pose)
    
    # Compute inverse
    T_inv = inverse_transform(T)
    
    # T * T_inv should be identity
    identity = T @ T_inv
    error = np.linalg.norm(identity - np.eye(4))
    
    print(f"  T * T_inv error: {error:.6f}")
    
    if error < 1e-6:
        print("  ✅ PASS\n")
        return True
    else:
        print("  ❌ FAIL\n")
        return False


def test_relative_pose():
    """Test relative pose calculation"""
    print("Testing relative pose calculation...")
    
    # Reference pose (first frame)
    reference_pose = np.array([1.0, 2.0, 3.0, 0.0, 0.0, 0.0, 0.5])  # 7D with gripper
    
    # Current pose (moved 0.1m in x, 0.2m in y, rotated 0.1 rad in z)
    current_pose = np.array([1.1, 2.2, 3.0, 0.0, 0.0, 0.1, 0.7])
    
    # Compute relative pose
    action = relative_pose(current_pose, reference_pose)
    
    print(f"  Reference pose: {reference_pose}")
    print(f"  Current pose:   {current_pose}")
    print(f"  Relative pose (action): {action}")
    
    # The relative translation should be approximately [0.1, 0.2, 0.0]
    # in the reference frame (may differ due to rotation)
    expected_translation_magnitude = np.sqrt(0.1**2 + 0.2**2)
    actual_translation_magnitude = np.linalg.norm(action[:3])
    
    print(f"  Expected translation magnitude: {expected_translation_magnitude:.3f}")
    print(f"  Actual translation magnitude: {actual_translation_magnitude:.3f}")
    print(f"  Gripper (should be 0.7): {action[6]:.3f}")
    
    # Check that gripper is preserved
    gripper_correct = abs(action[6] - 0.7) < 1e-6
    
    if gripper_correct:
        print("  ✅ PASS (gripper preserved)\n")
        return True
    else:
        print("  ❌ FAIL (gripper not preserved)\n")
        return False


def test_identity_transform():
    """Test that relative pose of reference to itself is zero"""
    print("Testing identity transformation...")
    
    # Reference pose
    reference_pose = np.array([1.0, 2.0, 3.0, 0.1, 0.2, 0.3, 0.5])
    
    # Compute relative pose to itself
    action = relative_pose(reference_pose, reference_pose)
    
    print(f"  Reference pose: {reference_pose}")
    print(f"  Relative to itself: {action}")
    
    # Position and orientation should be zero, gripper preserved
    pose_error = np.linalg.norm(action[:6])
    gripper_correct = abs(action[6] - 0.5) < 1e-6
    
    print(f"  Pose error (should be ~0): {pose_error:.6f}")
    print(f"  Gripper (should be 0.5): {action[6]:.3f}")
    
    if pose_error < 1e-6 and gripper_correct:
        print("  ✅ PASS\n")
        return True
    else:
        print("  ❌ FAIL\n")
        return False


def main():
    """Run all tests"""
    print("="*60)
    print("Coordinate Transformation Tests")
    print("="*60 + "\n")
    
    results = []
    
    results.append(("Euler <-> Matrix", test_euler_matrix_conversion()))
    results.append(("Pose <-> Matrix", test_pose_matrix_conversion()))
    results.append(("Inverse Transform", test_inverse_transform()))
    results.append(("Relative Pose", test_relative_pose()))
    results.append(("Identity Transform", test_identity_transform()))
    
    # Summary
    print("="*60)
    print("Test Summary")
    print("="*60)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name:25s} {status}")
    
    total = len(results)
    passed = sum(results, key=lambda x: x[1])
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print("="*60)
    
    return all(r[1] for r in results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

