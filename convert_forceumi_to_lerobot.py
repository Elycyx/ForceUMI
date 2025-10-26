#!/usr/bin/env python3

"""
Convert ForceUMI data to LeRobot dataset format.

This script converts HDF5 files collected with ForceUMI to the LeRobot 
dataset format for training robot policies.

NOTE: Please use the lerobot environment for this conversion.
"""

import os
import h5py
import numpy as np
import argparse
from pathlib import Path
from tqdm import tqdm
import cv2

from lerobot.datasets.lerobot_dataset import LeRobotDataset


def create_forceumi_features(image_shape: tuple, fps: float) -> dict:
    """
    Create feature definition for ForceUMI data.
    
    Args:
        image_shape: Shape of images (H, W, C)
        fps: Frames per second
        
    Returns:
        Feature dictionary for LeRobot
    """
    H, W, C = image_shape
    
    features = {
        "action": {
            "dtype": "float32",
            "shape": (7,),  # 6D pose (x,y,z,rx,ry,rz) + 1 gripper
            "names": [
                "x",
                "y", 
                "z",
                "roll",
                "pitch",
                "yaw",
                "gripper",
            ]
        },
        "observation.state": {
            "dtype": "float32", 
            "shape": (7,),  # 6D pose (x,y,z,rx,ry,rz) + 1 gripper
            "names": [
                "x",
                "y",
                "z",
                "roll",
                "pitch",
                "yaw",
                "gripper",
            ]
        },
        "observation.force": {
            "dtype": "float32",
            "shape": (6,),  # fx,fy,fz,mx,my,mz
            "names": [
                "fx",
                "fy",
                "fz",
                "mx",
                "my",
                "mz",
            ]
        },
        "observation.images": {
            "dtype": "video",
            "shape": [H, W, C],
            "names": ["height", "width", "channels"],
            "video_info": {
                "video.height": H,
                "video.width": W,
                "video.codec": "av1",
                "video.pix_fmt": "yuv420p", 
                "video.is_depth_map": False,
                "video.fps": fps,
                "video.channels": C,
                "has_audio": False,
            },
        },
    }
    
    return features


def load_forceumi_episode(hdf5_path: str) -> tuple:
    """
    Load data from a ForceUMI HDF5 episode file.
    
    Args:
        hdf5_path: Path to HDF5 file
        
    Returns:
        tuple: (images, states, actions, forces, metadata)
    """
    try:
        with h5py.File(hdf5_path, 'r') as f:
            # Load datasets
            images = np.array(f['image'])  # [T, H, W, 3]
            states = np.array(f['state'])  # [T, 7]
            actions = np.array(f['action'])  # [T, 7]
            forces = np.array(f['force'])  # [T, 6]
            
            # Load metadata
            metadata = {}
            if 'metadata' in f.attrs:
                # If metadata is stored as group attributes
                for key in f.attrs.keys():
                    metadata[key] = f.attrs[key]
            
            # Try to get fps from metadata
            fps = metadata.get('fps', 30.0)
            task = metadata.get('task_description', 'unknown_task')
            
            return images, states, actions, forces, metadata, fps, task
            
    except Exception as e:
        print(f"Error loading {hdf5_path}: {e}")
        return None, None, None, None, None, None, None


def preprocess_forceumi_data(images: np.ndarray, 
                             states: np.ndarray, 
                             actions: np.ndarray,
                             forces: np.ndarray,
                             target_size: tuple = None) -> tuple:
    """
    Preprocess ForceUMI data for LeRobot format.
    
    Args:
        images: Image array [T, H, W, 3]
        states: State array [T, 7]
        actions: Action array [T, 7]
        forces: Force array [T, 6]
        target_size: Optional target size for images (H, W)
        
    Returns:
        tuple: Preprocessed (images, states, actions, forces)
    """
    # Ensure float32 type
    states = states.astype(np.float32)
    actions = actions.astype(np.float32)
    forces = forces.astype(np.float32)
    
    # Resize images if needed
    if target_size is not None and images is not None:
        T, H, W, C = images.shape
        target_H, target_W = target_size
        
        if (H, W) != (target_H, target_W):
            print(f"Resizing images from {H}x{W} to {target_H}x{target_W}")
            resized_images = np.zeros((T, target_H, target_W, C), dtype=images.dtype)
            
            for t in range(T):
                resized_images[t] = cv2.resize(
                    images[t], 
                    (target_W, target_H),
                    interpolation=cv2.INTER_LINEAR
                )
            images = resized_images
    
    # Ensure images are uint8
    if images is not None:
        if images.dtype != np.uint8:
            images = images.astype(np.uint8)
    
    return images, states, actions, forces


def process_forceumi_episode(dataset: LeRobotDataset, 
                             task: str, 
                             hdf5_path: str,
                             episode_name: str,
                             skip_frames: int = 0,
                             target_image_size: tuple = None) -> bool:
    """
    Process a single ForceUMI episode and add frames to the dataset.
    
    Args:
        dataset: LeRobot dataset to add frames to
        task: Task description
        hdf5_path: Path to HDF5 episode file
        episode_name: Name of the episode
        skip_frames: Number of initial frames to skip
        target_image_size: Optional target size for images (H, W)
        
    Returns:
        bool: True if episode was processed successfully
    """
    # Load episode data
    images, states, actions, forces, metadata, fps, task_from_file = \
        load_forceumi_episode(hdf5_path)
    
    if images is None:
        print(f'Episode {episode_name} could not be loaded, skipping')
        return False
    
    # Use task from file if not provided
    if task == "unknown_task" and task_from_file != "unknown_task":
        task = task_from_file
    
    # Preprocess data
    images, states, actions, forces = preprocess_forceumi_data(
        images, states, actions, forces, target_image_size
    )
    
    # Print data shapes
    print(f'Episode {episode_name} data shapes:')
    print(f'  images: {images.shape}')
    print(f'  states: {states.shape}')
    print(f'  actions: {actions.shape}')
    print(f'  forces: {forces.shape}')
    print(f'  fps: {fps}, task: {task}')
    
    # Verify data consistency
    T = images.shape[0]
    if not (states.shape[0] == T and 
            actions.shape[0] == T and 
            forces.shape[0] == T):
        print(f'Episode {episode_name} has inconsistent data shapes, skipping')
        return False
    
    # Add frames to dataset (skip first few frames if requested)
    start_frame = max(skip_frames, 0)
    
    for frame_idx in tqdm(range(start_frame, T), 
                         desc=f'Processing {episode_name}', leave=False):
        frame = {
            "action": actions[frame_idx],
            "observation.state": states[frame_idx],
            "observation.force": forces[frame_idx],
            "observation.images": images[frame_idx],
        }
        dataset.add_frame(frame=frame, task=task)
    
    return True


def find_forceumi_episodes(data_dir: str) -> list:
    """
    Find all ForceUMI episode files in a directory.
    
    Supports both flat structure and session-based structure:
    - Flat: data_dir/episode0.hdf5, episode1.hdf5, ...
    - Session: data_dir/session_XXX/episode0.hdf5, episode1.hdf5, ...
    
    Args:
        data_dir: Root data directory
        
    Returns:
        List of (session_path, episode_files) tuples
    """
    data_path = Path(data_dir)
    episode_groups = []
    
    # Check for session-based structure
    session_dirs = sorted(data_path.glob("session_*"))
    
    if session_dirs:
        print(f"Found {len(session_dirs)} session directories")
        for session_dir in session_dirs:
            episode_files = sorted(session_dir.glob("episode*.hdf5"))
            if episode_files:
                episode_groups.append((session_dir.name, episode_files))
                print(f"  {session_dir.name}: {len(episode_files)} episodes")
    else:
        # Check for flat structure
        episode_files = sorted(data_path.glob("episode*.hdf5"))
        if episode_files:
            episode_groups.append(("flat", episode_files))
            print(f"Found {len(episode_files)} episodes in flat structure")
    
    return episode_groups


def convert_forceumi_to_lerobot(
    data_dir: str,
    output_repo_id: str, 
    task_description: str,
    fps: int = 30,
    robot_type: str = "forceumi",
    skip_frames: int = 0,
    target_image_size: tuple = None,
    push_to_hub: bool = False
):
    """
    Convert ForceUMI HDF5 files to LeRobot dataset format.
    
    Args:
        data_dir: Directory containing ForceUMI episodes (flat or session-based)
        output_repo_id: Repository ID for the output dataset
        task_description: Description of the task
        fps: Frames per second for video encoding
        robot_type: Type of robot (for metadata)
        skip_frames: Number of initial frames to skip per episode
        target_image_size: Optional target size for images (H, W)
        push_to_hub: Whether to push the dataset to HuggingFace Hub
    """
    print(f"Converting ForceUMI data from {data_dir} to LeRobot format...")
    print(f"Output repository: {output_repo_id}")
    print(f"Task: {task_description}")
    
    # Find all episodes
    episode_groups = find_forceumi_episodes(data_dir)
    
    if not episode_groups:
        print(f"No episodes found in {data_dir}")
        return
    
    # Load first episode to get image dimensions
    first_session, first_episodes = episode_groups[0]
    first_episode_path = first_episodes[0]
    
    with h5py.File(first_episode_path, 'r') as f:
        sample_image = f['image'][0]
        H, W, C = sample_image.shape
        
    # Apply target size if specified
    if target_image_size is not None:
        H, W = target_image_size
    
    print(f"Image size: {H}x{W}x{C}")
    
    # Create features
    features = create_forceumi_features((H, W, C), fps)
    
    # Create LeRobot dataset
    dataset = LeRobotDataset.create(
        repo_id=output_repo_id,
        fps=fps,
        robot_type=robot_type,
        features=features,
    )
    
    total_episodes = 0
    successful_episodes = 0
    
    # Process all episodes
    for session_name, episode_files in episode_groups:
        print(f"\nProcessing session: {session_name}")
        
        for episode_file in tqdm(episode_files, desc=f"Session {session_name}"):
            episode_name = episode_file.stem
            total_episodes += 1
            
            success = process_forceumi_episode(
                dataset=dataset,
                task=task_description,
                hdf5_path=str(episode_file),
                episode_name=f"{session_name}/{episode_name}",
                skip_frames=skip_frames,
                target_image_size=target_image_size
            )
            
            if success:
                successful_episodes += 1
                dataset.save_episode()
                print(f"✓ Saved episode {successful_episodes}: {session_name}/{episode_name}")
            else:
                print(f"✗ Skipped episode: {session_name}/{episode_name}")
    
    print(f"\n=== Conversion Summary ===")
    print(f"Total episodes processed: {total_episodes}")
    print(f"Successful episodes: {successful_episodes}")
    print(f"Conversion rate: {successful_episodes/total_episodes*100:.1f}%" if total_episodes > 0 else "No episodes processed")
    
    if successful_episodes > 0:
        print(f"\nDataset created with {successful_episodes} episodes")
        
        if push_to_hub:
            print("Pushing dataset to HuggingFace Hub...")
            dataset.push_to_hub()
            print("✓ Dataset pushed to Hub successfully!")
        else:
            print("Dataset saved locally. Use --push_to_hub to upload to HuggingFace Hub.")
    else:
        print("No episodes were successfully converted!")


def main():
    parser = argparse.ArgumentParser(
        description="Convert ForceUMI data to LeRobot format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert a session directory
  python convert_forceumi_to_lerobot.py \\
    --data_dir data/session_20250101_120000 \\
    --output_repo_id username/forceumi-task1 \\
    --task "Pick and place task"
  
  # Convert entire data directory with all sessions
  python convert_forceumi_to_lerobot.py \\
    --data_dir data \\
    --output_repo_id username/forceumi-full \\
    --task "Various manipulation tasks" \\
    --skip_frames 5
  
  # Resize images and push to Hub
  python convert_forceumi_to_lerobot.py \\
    --data_dir data \\
    --output_repo_id username/forceumi-task1 \\
    --task "Assembly task" \\
    --target_size 224 224 \\
    --push_to_hub
        """
    )
    
    # Input/Output arguments
    parser.add_argument("--data_dir", required=True,
                       help="Directory containing ForceUMI episodes (flat or session-based)")
    parser.add_argument("--output_repo_id", required=True,
                       help="Output repository ID (e.g., 'username/dataset-name')")
    parser.add_argument("--task", required=True,
                       help="Task description (e.g., 'Pick and place task')")
    
    # Processing arguments
    parser.add_argument("--fps", type=int, default=30,
                       help="Frames per second for video encoding (default: 30)")
    parser.add_argument("--robot_type", default="forceumi",
                       help="Robot type identifier (default: forceumi)")
    parser.add_argument("--skip_frames", type=int, default=0,
                       help="Number of initial frames to skip per episode (default: 0)")
    parser.add_argument("--target_size", type=int, nargs=2, default=None,
                       metavar=("HEIGHT", "WIDTH"),
                       help="Target image size for resizing (e.g., 224 224)")
    
    # Output arguments
    parser.add_argument("--push_to_hub", action="store_true",
                       help="Push dataset to HuggingFace Hub after conversion")
    
    args = parser.parse_args()
    
    # Validate data directory
    if not os.path.exists(args.data_dir):
        print(f"Error: Data directory does not exist: {args.data_dir}")
        exit(1)
    
    # Convert target_size to tuple if provided
    target_size = tuple(args.target_size) if args.target_size else None
    
    # Run conversion
    convert_forceumi_to_lerobot(
        data_dir=args.data_dir,
        output_repo_id=args.output_repo_id,
        task_description=args.task,
        fps=args.fps,
        robot_type=args.robot_type,
        skip_frames=args.skip_frames,
        target_image_size=target_size,
        push_to_hub=args.push_to_hub
    )


if __name__ == "__main__":
    main()

