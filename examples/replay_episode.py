"""
Example script for replaying collected episodes.

This script demonstrates how to use the replay functionality to visualize
previously collected HDF5 episodes.

Usage:
    python replay_episode.py <path_to_episode.hdf5>
    
Keyboard Controls:
    Space        - Play/Pause
    Left/Right   - Step backward/forward (1 frame)
    Up/Down      - Increase/decrease playback speed
    Home         - Jump to start
    End          - Jump to end
    L            - Toggle loop
    H            - Toggle help display
    Q/ESC        - Quit
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path if needed
if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).parent.parent))

from forceumi.replay import ReplayWindow
from forceumi.config import ConfigManager


def main():
    """Main function."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Check arguments
    if len(sys.argv) < 2:
        print("Usage: python replay_episode.py <path_to_episode.hdf5> [--config <config_file>]")
        print("\nExample:")
        print("  python replay_episode.py data/episode_20250117_123456.hdf5")
        print("  python replay_episode.py data/episode_20250117_123456.hdf5 --config examples/config_example.yaml")
        sys.exit(1)
    
    episode_path = sys.argv[1]
    
    # Check if file exists
    if not Path(episode_path).exists():
        logger.error(f"Episode file not found: {episode_path}")
        sys.exit(1)
    
    # Load config if provided
    config = None
    if len(sys.argv) > 3 and sys.argv[2] == '--config':
        config_path = sys.argv[3]
        logger.info(f"Loading config from: {config_path}")
        config = ConfigManager.load_config(config_path)
    
    # Create and run replay window
    logger.info(f"Loading episode: {episode_path}")
    window = ReplayWindow(episode_path, config)
    
    # Print episode info
    info = window.player.get_info()
    logger.info("=" * 60)
    logger.info("Episode Information:")
    logger.info(f"  Total Frames: {info['total_frames']}")
    logger.info(f"  FPS: {info['fps']}")
    logger.info(f"  Duration: {info['duration']:.2f}s")
    logger.info(f"  Has Image: {info['has_image']}")
    logger.info(f"  Has State: {info['has_state']}")
    logger.info(f"  Has Action: {info['has_action']}")
    logger.info(f"  Has Force: {info['has_force']}")
    if info['image_shape'] is not None:
        logger.info(f"  Image Shape: {info['image_shape']}")
    logger.info("=" * 60)
    
    # Run replay
    window.run()
    
    logger.info("Replay finished")


if __name__ == '__main__':
    main()

