#!/usr/bin/env python3

"""
Convert ForceUMI data to LeRobot dataset format.

This script converts HDF5 files collected with ForceUMI to the LeRobot 
dataset format for training robot policies.

Data Mapping:
- ForceUMI action → LeRobot observation.state
- ForceUMI force → LeRobot observation.effort  
- ForceUMI image → LeRobot observation.images
- LeRobot action: computed as delta between consecutive states
  - action[t] = state[t] - state[t-1] for pose (x,y,z,rx,ry,rz)
  - action[t].gripper = state[t].gripper (absolute value)
  - action[0] = [0,0,0,0,0,0, gripper] for first frame

NOTE: Please use the lerobot environment for this conversion.
"""

import os
import h5py
import numpy as np
import argparse
from pathlib import Path
from tqdm import tqdm
import cv2
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from functools import partial
import multiprocessing as mp
import time

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
        "observation.effort": {
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
    
    Note: ForceUMI action becomes LeRobot state.
    
    Args:
        hdf5_path: Path to HDF5 file
        
    Returns:
        tuple: (images, states, forces, metadata, fps, task)
              states here are from ForceUMI's action field
    """
    try:
        with h5py.File(hdf5_path, 'r') as f:
            # Load datasets
            images = np.array(f['image'])  # [T, H, W, 3]
            # Use ForceUMI action as LeRobot state
            states = np.array(f['action'])  # [T, 7]
            states[:, 5] += np.pi / 2 # make sure the initial orientation is 0
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
            
            return images, states, forces, metadata, fps, task
            
    except Exception as e:
        print(f"Error loading {hdf5_path}: {e}")
        return None, None, None, None, None, None


def compute_delta_actions(states: np.ndarray) -> np.ndarray:
    """
    Compute delta actions from states.
    
    Action at time t = state[t] - state[t-1]
    For the first frame, action = zeros (no previous frame)
    Gripper value remains absolute (copied from current state)
    
    Args:
        states: State array [T, 7] where each row is [x, y, z, rx, ry, rz, gripper]
        
    Returns:
        actions: Action array [T, 7] with delta pose and absolute gripper
    """
    T = states.shape[0]
    actions = np.zeros_like(states)
    
    # First frame: action is zero for pose, absolute for gripper
    actions[0, :6] = 0.0
    actions[0, 6] = states[0, 6]  # Gripper is absolute
    
    # Subsequent frames: compute delta
    for t in range(1, T):
        actions[t, :6] = states[t, :6] - states[t-1, :6]  # Delta pose
        actions[t, 6] = states[t, 6]  # Gripper remains absolute
    
    return actions


def resize_image_batch(image_batch: np.ndarray, target_size: tuple) -> np.ndarray:
    """
    Resize a batch of images (for parallel processing).
    
    Args:
        image_batch: Batch of images [batch_size, H, W, C]
        target_size: Target size (H, W)
        
    Returns:
        Resized images
    """
    target_H, target_W = target_size
    batch_size = image_batch.shape[0]
    C = image_batch.shape[3]
    
    resized = np.zeros((batch_size, target_H, target_W, C), dtype=image_batch.dtype)
    for i in range(batch_size):
        resized[i] = cv2.resize(
            image_batch[i],
            (target_W, target_H),
            interpolation=cv2.INTER_LINEAR
        )
    return resized


def preprocess_forceumi_data(images: np.ndarray, 
                             states: np.ndarray, 
                             forces: np.ndarray,
                             target_size: tuple = None,
                             num_workers: int = 4) -> tuple:
    """
    Preprocess ForceUMI data for LeRobot format with parallel image processing.
    
    Args:
        images: Image array [T, H, W, 3]
        states: State array [T, 7] (from ForceUMI action field)
        forces: Force array [T, 6]
        target_size: Optional target size for images (H, W)
        num_workers: Number of parallel workers for image processing
        
    Returns:
        tuple: Preprocessed (images, states, actions, forces)
    """
    # Ensure float32 type
    states = states.astype(np.float32)
    forces = forces.astype(np.float32)
    
    # Compute delta actions from states
    actions = compute_delta_actions(states)
    
    # Resize images if needed (with parallel processing)
    if target_size is not None and images is not None:
        T, H, W, C = images.shape
        target_H, target_W = target_size
        
        if (H, W) != (target_H, target_W):
            print(f"Resizing {T} images from {H}x{W} to {target_H}x{target_W} using {num_workers} workers...")
            
            # Split images into batches for parallel processing
            batch_size = max(1, T // (num_workers * 4))  # Create more batches than workers
            batches = []
            for i in range(0, T, batch_size):
                batches.append(images[i:min(i+batch_size, T)])
            
            # Process batches in parallel
            resize_func = partial(resize_image_batch, target_size=target_size)
            
            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                resized_batches = list(executor.map(resize_func, batches))
            
            # Concatenate results
            images = np.concatenate(resized_batches, axis=0)
            print(f"✓ Resized {T} images")
    
    # Ensure images are uint8
    if images is not None:
        if images.dtype != np.uint8:
            images = images.astype(np.uint8)
    
    return images, states, actions, forces


def _preprocess_episode_wrapper(args: tuple) -> dict:
    """
    Wrapper function for parallel processing (must be top-level for pickle).
    
    Args:
        args: Tuple of (hdf5_path, episode_name, skip_frames, target_image_size, num_workers)
        
    Returns:
        Preprocessed episode data dict or None
    """
    return load_and_preprocess_episode(*args)


def load_and_preprocess_episode(hdf5_path: str,
                               episode_name: str,
                               skip_frames: int,
                               target_image_size: tuple,
                               num_workers: int) -> dict:
    """
    Load and preprocess a single episode (for parallel processing).
    
    Args:
        hdf5_path: Path to HDF5 file
        episode_name: Episode name
        skip_frames: Number of frames to skip
        target_image_size: Target image size
        num_workers: Number of workers for image processing
        
    Returns:
        dict with preprocessed data or None if failed
    """
    # Load episode data
    images, states, forces, metadata, fps, task = load_forceumi_episode(hdf5_path)
    
    if images is None:
        return None
    
    # Preprocess data
    images, states, actions, forces = preprocess_forceumi_data(
        images, states, forces, target_image_size, num_workers
    )
    
    # Verify data consistency
    T = images.shape[0]
    if not (states.shape[0] == T and actions.shape[0] == T and forces.shape[0] == T):
        return None
    
    # Apply skip_frames
    start_frame = max(skip_frames, 0)
    
    return {
        'episode_name': episode_name,
        'images': images[start_frame:],
        'states': states[start_frame:],
        'actions': actions[start_frame:],
        'forces': forces[start_frame:],
        'task': task,
        'fps': fps,
        'metadata': metadata,
    }


def process_forceumi_episode(dataset: LeRobotDataset, 
                             task: str, 
                             hdf5_path: str,
                             episode_name: str,
                             skip_frames: int = 0,
                             target_image_size: tuple = None,
                             num_workers: int = 4) -> bool:
    """
    Process a single ForceUMI episode and add frames to the dataset.
    
    Note: 
    - ForceUMI action → LeRobot state
    - LeRobot action = delta between consecutive states (gripper absolute)
    
    Args:
        dataset: LeRobot dataset to add frames to
        task: Task description
        hdf5_path: Path to HDF5 episode file
        episode_name: Name of the episode
        skip_frames: Number of initial frames to skip
        target_image_size: Optional target size for images (H, W)
        num_workers: Number of parallel workers for image processing
        
    Returns:
        bool: True if episode was processed successfully
    """
    # Load episode data (states are from ForceUMI action field)
    images, states, forces, metadata, fps, task_from_file = \
        load_forceumi_episode(hdf5_path)
    
    if images is None:
        print(f'Episode {episode_name} could not be loaded, skipping')
        return False
    
    # Use task from file if not provided
    if task == "unknown_task" and task_from_file != "unknown_task":
        task = task_from_file
    
    # Preprocess data (this also computes delta actions, with parallel image processing)
    images, states, actions, forces = preprocess_forceumi_data(
        images, states, forces, target_image_size, num_workers
    )
    
    # Print data shapes
    print(f'Episode {episode_name} data shapes:')
    print(f'  images: {images.shape}')
    print(f'  states: {states.shape} (from ForceUMI action)')
    print(f'  actions: {actions.shape} (delta computed)')
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
            "observation.effort": forces[frame_idx],
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
    push_to_hub: bool = False,
    num_workers: int = 4,
    parallel_episodes: int = 1
):
    """
    Convert ForceUMI HDF5 files to LeRobot dataset format with parallel processing.
    
    Args:
        data_dir: Directory containing ForceUMI episodes (flat or session-based)
        output_repo_id: Repository ID for the output dataset
        task_description: Description of the task
        fps: Frames per second for video encoding
        robot_type: Type of robot (for metadata)
        skip_frames: Number of initial frames to skip per episode
        target_image_size: Optional target size for images (H, W)
        push_to_hub: Whether to push the dataset to HuggingFace Hub
        num_workers: Number of parallel workers for image processing (default: 4)
        parallel_episodes: Number of episodes to preprocess in parallel (default: 1, set to 2-4 for speedup)
    """
    start_time = time.time()
    
    print(f"Converting ForceUMI data from {data_dir} to LeRobot format...")
    print(f"Output repository: {output_repo_id}")
    print(f"Task: {task_description}")
    print(f"Parallel workers: {num_workers} (image processing), {parallel_episodes} (episode loading)")
    
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
        
        if parallel_episodes > 1:
            # Parallel preprocessing of episodes
            print(f"Using parallel preprocessing with {parallel_episodes} workers...")
            
            # Prepare arguments for parallel processing
            preprocess_args = [
                (str(episode_file), 
                 f"{session_name}/{episode_file.stem}",
                 skip_frames,
                 target_image_size,
                 num_workers)
                for episode_file in episode_files
            ]
            
            # Load and preprocess episodes in parallel
            with ProcessPoolExecutor(max_workers=parallel_episodes) as executor:
                preprocessed_episodes = list(tqdm(
                    executor.map(_preprocess_episode_wrapper, preprocess_args),
                    total=len(episode_files),
                    desc=f"Loading & preprocessing {session_name}"
                ))
            
            # Add preprocessed episodes to dataset (must be sequential for LeRobot)
            for episode_data in tqdm(preprocessed_episodes, desc=f"Saving {session_name}"):
                total_episodes += 1
                
                if episode_data is None:
                    print(f"✗ Skipped episode (preprocessing failed)")
                    continue
                
                # Get task
                task = task_description
                if task == "unknown_task" and episode_data['task'] != "unknown_task":
                    task = episode_data['task']
                
                # Add frames to dataset
                T = episode_data['images'].shape[0]
                for frame_idx in range(T):
                    frame = {
                        "action": episode_data['actions'][frame_idx],
                        "observation.state": episode_data['states'][frame_idx],
                        "observation.effort": episode_data['forces'][frame_idx],
                        "observation.images": episode_data['images'][frame_idx],
                    }
                    dataset.add_frame(frame=frame, task=task)
                
                successful_episodes += 1
                dataset.save_episode()
                print(f"✓ Saved episode {successful_episodes}: {episode_data['episode_name']}")
        else:
            # Sequential processing (original method)
            for episode_file in tqdm(episode_files, desc=f"Session {session_name}"):
                episode_name = episode_file.stem
                total_episodes += 1
                
                success = process_forceumi_episode(
                    dataset=dataset,
                    task=task_description,
                    hdf5_path=str(episode_file),
                    episode_name=f"{session_name}/{episode_name}",
                    skip_frames=skip_frames,
                    target_image_size=target_image_size,
                    num_workers=num_workers
                )
                
                if success:
                    successful_episodes += 1
                    dataset.save_episode()
                    print(f"✓ Saved episode {successful_episodes}: {session_name}/{episode_name}")
                else:
                    print(f"✗ Skipped episode: {session_name}/{episode_name}")
    
    elapsed_time = time.time() - start_time
    
    print(f"\n=== Conversion Summary ===")
    print(f"Total episodes processed: {total_episodes}")
    print(f"Successful episodes: {successful_episodes}")
    print(f"Conversion rate: {successful_episodes/total_episodes*100:.1f}%" if total_episodes > 0 else "No episodes processed")
    print(f"Total time: {elapsed_time:.1f}s ({elapsed_time/60:.1f} minutes)")
    if successful_episodes > 0:
        print(f"Average time per episode: {elapsed_time/successful_episodes:.1f}s")
    
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
    
    # Parallel processing arguments
    parser.add_argument("--num_workers", type=int, default=8,
                       help="Number of parallel workers for image processing (default: 4)")
    parser.add_argument("--parallel_episodes", type=int, default=1,
                       help="Number of episodes to preprocess in parallel (default: 1, recommended: 2-4)")
    
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
        push_to_hub=args.push_to_hub,
        num_workers=args.num_workers,
        parallel_episodes=args.parallel_episodes
    )


if __name__ == "__main__":
    main()

