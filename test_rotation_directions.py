"""
Test script to compare CW and CCW rotations.

This helps determine which rotation direction aligns your system correctly.
"""

import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from forceumi.utils.transforms import rotate_frame_z_90_cw, rotate_frame_z_90_ccw


def test_rotation_comparison():
    """Compare CW and CCW rotations."""
    print("="*70)
    print("Rotation Direction Comparison")
    print("="*70)
    
    # Test case: movement along +x axis
    pose = np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5])
    
    print("\nOriginal pose (Tracker frame):")
    print(f"  Position: ({pose[0]:5.1f}, {pose[1]:5.1f}, {pose[2]:5.1f})")
    print(f"  Moving along +x axis")
    
    # Apply CW rotation
    cw_result = rotate_frame_z_90_cw(pose)
    print("\n1. Clockwise (CW) Rotation:")
    print(f"  Position: ({cw_result[0]:5.1f}, {cw_result[1]:5.1f}, {cw_result[2]:5.1f})")
    print(f"  Tracker +x → Force frame: ", end="")
    if np.isclose(cw_result[0], 0) and np.isclose(cw_result[1], -1):
        print("-y axis")
    elif np.isclose(cw_result[0], 0) and np.isclose(cw_result[1], 1):
        print("+y axis")
    elif np.isclose(cw_result[0], 1) and np.isclose(cw_result[1], 0):
        print("+x axis")
    elif np.isclose(cw_result[0], -1) and np.isclose(cw_result[1], 0):
        print("-x axis")
    
    # Apply CCW rotation
    ccw_result = rotate_frame_z_90_ccw(pose)
    print("\n2. Counter-Clockwise (CCW) Rotation:")
    print(f"  Position: ({ccw_result[0]:5.1f}, {ccw_result[1]:5.1f}, {ccw_result[2]:5.1f})")
    print(f"  Tracker +x → Force frame: ", end="")
    if np.isclose(ccw_result[0], 0) and np.isclose(ccw_result[1], -1):
        print("-y axis")
    elif np.isclose(ccw_result[0], 0) and np.isclose(ccw_result[1], 1):
        print("+y axis")
    elif np.isclose(ccw_result[0], 1) and np.isclose(ccw_result[1], 0):
        print("+x axis")
    elif np.isclose(ccw_result[0], -1) and np.isclose(ccw_result[1], 0):
        print("-x axis")
    
    # Visualization
    print("\n" + "="*70)
    print("Visualization (looking down from +z):")
    print("="*70)
    
    print("""
Original (Tracker frame):
     +y
      ↑
      |
−x ←--+--→ +x  (pose at +x direction)
      |
      ↓
     -y

After CW Rotation:
     +y
      |
      +--→ +x
      |
      ↓ (pose here, at -y)
     -y

After CCW Rotation:
     +y (pose here)
      ↑
      |
−x ←--+--→ +x
      |
      ↓
     -y
""")
    
    print("="*70)
    print("How to choose:")
    print("="*70)
    print("""
1. Move your tracker along its +x direction
2. Observe force sensor response

If force sensor shows response on:
  • -y axis → Use CW rotation (rotate_frame_z_90_cw)
  • +y axis → Use CCW rotation (rotate_frame_z_90_ccw)
  • +x axis → No rotation needed or 180° rotation
  • -x axis → 180° rotation needed

3. To change, edit forceumi/collector.py:
   
   # Line ~20:
   rotate_to_force_frame = rotate_frame_z_90_cw   # Change to _ccw if needed
""")


def test_inverse_property():
    """Test that CW and CCW are inverses of each other."""
    print("\n" + "="*70)
    print("Testing Inverse Property")
    print("="*70)
    
    original = np.array([1.5, 2.5, 3.5, 0.1, 0.2, 0.3, 0.7])
    
    # CW then CCW should return to original
    cw_result = rotate_frame_z_90_cw(original)
    back_to_original = rotate_frame_z_90_ccw(cw_result)
    
    position_match = np.allclose(back_to_original[:3], original[:3], atol=1e-10)
    orientation_match = np.allclose(back_to_original[3:6], original[3:6], atol=1e-6)
    gripper_match = np.isclose(back_to_original[6], original[6])
    
    print(f"\nOriginal pose:  {original}")
    print(f"After CW→CCW:   {back_to_original}")
    print(f"\nPosition matches:    {'✅' if position_match else '❌'}")
    print(f"Orientation matches: {'✅' if orientation_match else '❌'}")
    print(f"Gripper matches:     {'✅' if gripper_match else '❌'}")
    
    if position_match and orientation_match and gripper_match:
        print("\n✅ CW and CCW are correct inverses!")
    else:
        print("\n❌ Error: CW and CCW are not proper inverses!")


def main():
    """Run all tests."""
    test_rotation_comparison()
    test_inverse_property()
    
    print("\n" + "="*70)
    print("Summary")
    print("="*70)
    print("""
To switch rotation direction:

1. Edit forceumi/collector.py (around line 20)
2. Change:
   rotate_to_force_frame = rotate_frame_z_90_cw
   
   To:
   rotate_to_force_frame = rotate_frame_z_90_ccw

3. Restart data collection

For detailed guide, see: ROTATION_DIRECTION_GUIDE.md
""")


if __name__ == '__main__':
    main()

