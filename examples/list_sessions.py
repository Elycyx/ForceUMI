"""
Example: List and Browse Sessions

Demonstrates how to browse and analyze session-organized data.
"""

import sys
from pathlib import Path
import h5py


def list_sessions(data_dir: str = "data"):
    """
    List all sessions and their episodes.
    
    Args:
        data_dir: Path to data directory
    """
    data_path = Path(data_dir)
    
    if not data_path.exists():
        print(f"Data directory not found: {data_dir}")
        return
    
    # Find all sessions
    sessions = sorted(data_path.glob("session_*"))
    
    if not sessions:
        print(f"No sessions found in {data_dir}")
        return
    
    print("="*70)
    print(f"ForceUMI Data Sessions ({len(sessions)} total)")
    print("="*70)
    
    for i, session in enumerate(sessions, 1):
        print(f"\n📁 Session {i}: {session.name}")
        print("-"*70)
        
        # Find all episodes in this session
        episodes = sorted(session.glob("episode*.hdf5"))
        
        if not episodes:
            print("  No episodes")
            continue
        
        print(f"  Episodes: {len(episodes)}")
        
        # Analyze episodes
        total_frames = 0
        total_duration = 0
        
        for ep in episodes:
            try:
                with h5py.File(ep, 'r') as f:
                    num_frames = len(f['timestamp']) if 'timestamp' in f else 0
                    duration = f.attrs.get('duration', 0)
                    fps = f.attrs.get('fps', 0)
                    
                    total_frames += num_frames
                    total_duration += duration
                    
                    print(f"    • {ep.name:15s} {num_frames:4d} frames  {duration:6.2f}s  {fps:5.2f} FPS")
            except Exception as e:
                print(f"    • {ep.name:15s} [Error reading: {e}]")
        
        print(f"\n  Total: {total_frames} frames, {total_duration:.2f}s")
    
    print("\n" + "="*70)
    
    # Show latest session
    if sessions:
        latest = sessions[-1]
        print(f"\n💡 Latest session: {latest.name}")
        print(f"   Path: {latest}")
        
        episodes = sorted(latest.glob("episode*.hdf5"))
        if episodes:
            print(f"   {len(episodes)} episode(s)")


def analyze_session(session_path: str):
    """
    Detailed analysis of a specific session.
    
    Args:
        session_path: Path to session directory
    """
    session = Path(session_path)
    
    if not session.exists():
        print(f"Session not found: {session_path}")
        return
    
    print("="*70)
    print(f"Session Analysis: {session.name}")
    print("="*70)
    
    episodes = sorted(session.glob("episode*.hdf5"))
    
    if not episodes:
        print("No episodes in this session")
        return
    
    print(f"\nFound {len(episodes)} episode(s)\n")
    
    for i, ep in enumerate(episodes):
        print(f"Episode {i}:")
        print(f"  File: {ep.name}")
        
        try:
            with h5py.File(ep, 'r') as f:
                # Basic info
                num_frames = len(f['timestamp']) if 'timestamp' in f else 0
                duration = f.attrs.get('duration', 0)
                fps = f.attrs.get('fps', 0)
                
                print(f"  Frames: {num_frames}")
                print(f"  Duration: {duration:.2f}s")
                print(f"  FPS: {fps:.2f}")
                
                # Data types
                has_image = 'image' in f and len(f['image']) > 0
                has_state = 'state' in f and len(f['state']) > 0
                has_action = 'action' in f and len(f['action']) > 0
                has_force = 'force' in f and len(f['force']) > 0
                
                print(f"  Data:")
                print(f"    Image: {'✓' if has_image else '✗'}")
                print(f"    State: {'✓' if has_state else '✗'}")
                print(f"    Action: {'✓' if has_action else '✗'}")
                print(f"    Force: {'✓' if has_force else '✗'}")
                
                # Timestamps
                has_per_sensor = all([
                    'timestamp_camera' in f,
                    'timestamp_pose' in f,
                    'timestamp_force' in f
                ])
                print(f"    Per-sensor timestamps: {'✓' if has_per_sensor else '✗'}")
                
                # Metadata
                if 'task_description' in f.attrs:
                    print(f"  Task: {f.attrs['task_description']}")
                
        except Exception as e:
            print(f"  [Error: {e}]")
        
        print()


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Browse ForceUMI session data')
    parser.add_argument('path', nargs='?', default='data',
                       help='Data directory or specific session path')
    parser.add_argument('--analyze', action='store_true',
                       help='Show detailed analysis of a specific session')
    
    args = parser.parse_args()
    
    path = Path(args.path)
    
    # Check if it's a session directory
    if path.name.startswith('session_') and path.is_dir():
        analyze_session(str(path))
    else:
        # List all sessions in data directory
        list_sessions(str(path))
        
        if args.analyze:
            # Find latest session
            sessions = sorted(path.glob("session_*"))
            if sessions:
                print("\n" + "="*70)
                analyze_session(str(sessions[-1]))


if __name__ == '__main__':
    main()

