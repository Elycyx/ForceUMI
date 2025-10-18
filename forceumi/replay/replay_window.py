"""
Replay window for visualizing collected episodes.

This module provides a GUI window for replaying HDF5 episodes with
synchronized visualization of all data streams.
"""

import cv2
import numpy as np
import logging
import time
from typing import Optional, Dict, Any
from collections import deque
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg

from .player import EpisodePlayer


class ReplayWindow:
    """
    OpenCV-based replay window for visualizing episodes.
    
    Provides synchronized visualization of:
    - Camera images
    - Force/torque data
    - State (pose) data
    - Action data
    
    Keyboard controls:
    - Space: Play/Pause
    - Left/Right Arrow: Step backward/forward (1 frame)
    - Up/Down Arrow: Increase/decrease playback speed
    - Home: Jump to start
    - End: Jump to end
    - L: Toggle loop
    - Q/ESC: Quit
    """
    
    def __init__(self, episode_path: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the replay window.
        
        Args:
            episode_path: Path to HDF5 episode file
            config: Optional configuration dict
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.player = EpisodePlayer(episode_path)
        
        # Configuration
        if config is None:
            config = {}
        self.config = config
        
        # Window settings
        self.image_display_size = config.get('image_display_size', (800, 600))
        self.plot_size = (800, 400)
        self.plot_history = config.get('plot_history', 300)  # frames
        
        # Data buffers for plotting
        self.force_buffer = deque(maxlen=self.plot_history)
        self.torque_buffer = deque(maxlen=self.plot_history)
        self.state_history = deque(maxlen=self.plot_history)
        self.action_history = deque(maxlen=self.plot_history)
        
        # UI state
        self.running = True
        self.show_help = True
        
        # Create windows
        self._init_windows()
        
        # Display first frame
        self._display_frame(self.player.get_frame(0))
        
        self.logger.info("Replay window initialized")
    
    def _init_windows(self):
        """Initialize OpenCV windows."""
        cv2.namedWindow('Replay - Image', cv2.WINDOW_NORMAL)
        cv2.namedWindow('Replay - Force/Torque', cv2.WINDOW_NORMAL)
        cv2.namedWindow('Replay - State/Action', cv2.WINDOW_NORMAL)
        
        # Resize windows
        cv2.resizeWindow('Replay - Image', self.image_display_size[0], self.image_display_size[1])
        cv2.resizeWindow('Replay - Force/Torque', self.plot_size[0], self.plot_size[1])
        cv2.resizeWindow('Replay - State/Action', self.plot_size[0], self.plot_size[1])
        
        self.logger.debug("Windows initialized")
    
    def _display_frame(self, frame_data: Dict[str, Any]):
        """
        Display a frame of data.
        
        Args:
            frame_data: Frame data from player
        """
        # Update data buffers
        if frame_data.get('force') is not None:
            force = frame_data['force']
            self.force_buffer.append(force[:3])  # fx, fy, fz
            self.torque_buffer.append(force[3:])  # mx, my, mz
        
        if frame_data.get('state') is not None:
            self.state_history.append(frame_data['state'])
        
        if frame_data.get('action') is not None:
            self.action_history.append(frame_data['action'])
        
        # Display image
        self._update_image_display(frame_data)
        
        # Display force/torque plot
        self._update_force_plot()
        
        # Display state/action plot
        self._update_state_action_plot()
    
    def _update_image_display(self, frame_data: Dict[str, Any]):
        """Update the image display window."""
        image = frame_data.get('image')
        
        if image is not None:
            # Convert to BGR if needed
            if len(image.shape) == 3 and image.shape[2] == 3:
                display_image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            else:
                display_image = image.copy()
            
            # Resize to display size
            display_image = cv2.resize(display_image, self.image_display_size)
        else:
            # Create blank image
            display_image = np.zeros((self.image_display_size[1], self.image_display_size[0], 3), dtype=np.uint8)
            cv2.putText(display_image, "No Image Data", (50, display_image.shape[0]//2),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2)
        
        # Add overlay with info
        self._add_replay_overlay(display_image, frame_data)
        
        cv2.imshow('Replay - Image', display_image)
    
    def _add_replay_overlay(self, image: np.ndarray, frame_data: Dict[str, Any]):
        """Add overlay information to the image."""
        frame_idx = frame_data['frame_idx']
        current, total, progress = self.player.get_progress()
        
        # Status text
        status = "PLAYING" if self.player.is_playing else "PAUSED"
        status_color = (0, 255, 0) if self.player.is_playing else (0, 165, 255)
        
        # Top overlay
        overlay = image.copy()
        cv2.rectangle(overlay, (0, 0), (image.shape[1], 120), (0, 0, 0), -1)
        image[:] = cv2.addWeighted(overlay, 0.6, image, 0.4, 0)
        
        # Frame info
        cv2.putText(image, f"Frame: {current + 1}/{total}", (10, 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(image, f"Progress: {progress:.1f}%", (10, 55),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(image, f"Speed: {self.player.playback_speed:.1f}x", (10, 85),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(image, f"Loop: {'ON' if self.player.loop else 'OFF'}", (10, 115),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Status indicator
        cv2.putText(image, status, (image.shape[1] - 150, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, status_color, 2)
        
        # Timestamp if available
        if frame_data.get('timestamp') is not None:
            timestamp_text = f"Time: {frame_data['timestamp']:.3f}s"
            cv2.putText(image, timestamp_text, (image.shape[1] - 250, 80),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # Help text (if enabled)
        if self.show_help:
            help_y = image.shape[0] - 10
            help_texts = [
                "Space: Play/Pause  |  Left/Right: Step  |  Up/Down: Speed",
                "Home: Start  |  End: End  |  L: Loop  |  H: Hide Help  |  Q: Quit"
            ]
            for i, text in enumerate(reversed(help_texts)):
                y_pos = help_y - i * 25
                # Black background for readability
                (text_width, text_height), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                cv2.rectangle(image, (5, y_pos - text_height - 5), (text_width + 10, y_pos + 5), (0, 0, 0), -1)
                cv2.putText(image, text, (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    
    def _update_force_plot(self):
        """Update the force/torque plot."""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 5))
        fig.patch.set_facecolor('white')
        
        if len(self.force_buffer) > 0:
            forces = np.array(self.force_buffer)
            torques = np.array(self.torque_buffer)
            
            # Force plot
            ax1.plot(forces[:, 0], 'r-', label='Fx', linewidth=1.5)
            ax1.plot(forces[:, 1], 'g-', label='Fy', linewidth=1.5)
            ax1.plot(forces[:, 2], 'b-', label='Fz', linewidth=1.5)
            ax1.set_ylabel('Force (N)', fontsize=10)
            ax1.legend(loc='upper right', fontsize=8)
            ax1.grid(True, alpha=0.3)
            ax1.set_title('Force Data', fontsize=11)
            
            # Torque plot
            ax2.plot(torques[:, 0], 'r-', label='Mx', linewidth=1.5)
            ax2.plot(torques[:, 1], 'g-', label='My', linewidth=1.5)
            ax2.plot(torques[:, 2], 'b-', label='Mz', linewidth=1.5)
            ax2.set_ylabel('Torque (Nm)', fontsize=10)
            ax2.set_xlabel('Frame', fontsize=10)
            ax2.legend(loc='upper right', fontsize=8)
            ax2.grid(True, alpha=0.3)
            ax2.set_title('Torque Data', fontsize=11)
        else:
            ax1.text(0.5, 0.5, 'No Force Data', ha='center', va='center', fontsize=14)
            ax2.text(0.5, 0.5, 'No Torque Data', ha='center', va='center', fontsize=14)
        
        plt.tight_layout()
        
        # Convert to image
        canvas = FigureCanvasAgg(fig)
        canvas.draw()
        buf = canvas.buffer_rgba()
        plot_img = np.asarray(buf)
        plot_img = cv2.cvtColor(plot_img[:, :, :3], cv2.COLOR_RGB2BGR)
        
        plt.close(fig)
        
        cv2.imshow('Replay - Force/Torque', plot_img)
    
    def _update_state_action_plot(self):
        """Update the state/action plot."""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 5))
        fig.patch.set_facecolor('white')
        
        if len(self.state_history) > 0:
            states = np.array(self.state_history)
            
            # State plot (position and orientation)
            ax1.plot(states[:, 0], 'r-', label='X', linewidth=1.5, alpha=0.8)
            ax1.plot(states[:, 1], 'g-', label='Y', linewidth=1.5, alpha=0.8)
            ax1.plot(states[:, 2], 'b-', label='Z', linewidth=1.5, alpha=0.8)
            ax1.set_ylabel('Position (m)', fontsize=10)
            ax1.legend(loc='upper right', fontsize=8)
            ax1.grid(True, alpha=0.3)
            ax1.set_title('State - Position & Gripper', fontsize=11)
            
            # Add gripper on secondary axis
            ax1_twin = ax1.twinx()
            ax1_twin.plot(states[:, 6], 'k--', label='Gripper', linewidth=1.5, alpha=0.6)
            ax1_twin.set_ylabel('Gripper', fontsize=10)
            ax1_twin.legend(loc='upper left', fontsize=8)
        else:
            ax1.text(0.5, 0.5, 'No State Data', ha='center', va='center', fontsize=14)
        
        if len(self.action_history) > 0:
            actions = np.array(self.action_history)
            
            # Action plot
            ax2.plot(actions[:, 0], 'r-', label='ΔX', linewidth=1.5, alpha=0.8)
            ax2.plot(actions[:, 1], 'g-', label='ΔY', linewidth=1.5, alpha=0.8)
            ax2.plot(actions[:, 2], 'b-', label='ΔZ', linewidth=1.5, alpha=0.8)
            ax2.set_ylabel('Delta Position (m)', fontsize=10)
            ax2.set_xlabel('Frame', fontsize=10)
            ax2.legend(loc='upper right', fontsize=8)
            ax2.grid(True, alpha=0.3)
            ax2.set_title('Action - Relative Motion', fontsize=11)
        else:
            ax2.text(0.5, 0.5, 'No Action Data', ha='center', va='center', fontsize=14)
        
        plt.tight_layout()
        
        # Convert to image
        canvas = FigureCanvasAgg(fig)
        canvas.draw()
        buf = canvas.buffer_rgba()
        plot_img = np.asarray(buf)
        plot_img = cv2.cvtColor(plot_img[:, :, :3], cv2.COLOR_RGB2BGR)
        
        plt.close(fig)
        
        cv2.imshow('Replay - State/Action', plot_img)
    
    def _handle_key(self, key: int):
        """
        Handle keyboard input.
        
        Args:
            key: Key code from cv2.waitKey()
        """
        if key == -1:
            return
        
        # Space: Play/Pause
        if key == ord(' '):
            self.player.toggle_play_pause()
        
        # Left Arrow: Step backward
        elif key == 81 or key == 2:  # Left arrow (different codes on different systems)
            self.player.pause()
            self.player.seek_relative(-1)
            self._display_frame(self.player.get_frame())
        
        # Right Arrow: Step forward
        elif key == 83 or key == 3:  # Right arrow
            self.player.pause()
            self.player.seek_relative(1)
            self._display_frame(self.player.get_frame())
        
        # Up Arrow: Increase speed
        elif key == 82 or key == 0:  # Up arrow
            self.player.set_speed(self.player.playback_speed + 0.5)
            self.logger.info(f"Speed: {self.player.playback_speed}x")
        
        # Down Arrow: Decrease speed
        elif key == 84 or key == 1:  # Down arrow
            self.player.set_speed(self.player.playback_speed - 0.5)
            self.logger.info(f"Speed: {self.player.playback_speed}x")
        
        # Home: Jump to start
        elif key == ord('h') or key == 80:
            self.player.seek(0)
            self._display_frame(self.player.get_frame())
        
        # End: Jump to end
        elif key == ord('e') or key == 87:
            self.player.seek(self.player.total_frames - 1)
            self._display_frame(self.player.get_frame())
        
        # L: Toggle loop
        elif key == ord('l'):
            self.player.set_loop(not self.player.loop)
            self.logger.info(f"Loop: {'ON' if self.player.loop else 'OFF'}")
        
        # H: Toggle help
        elif key == ord('h'):
            self.show_help = not self.show_help
        
        # Q or ESC: Quit
        elif key == ord('q') or key == 27:
            self.running = False
    
    def run(self):
        """Run the replay window main loop."""
        self.logger.info("Starting replay...")
        self.logger.info(f"Episode info: {self.player.get_info()}")
        
        # Start playing
        self.player.play()
        
        while self.running:
            # Update player and get new frame if ready
            frame_data = self.player.update()
            
            if frame_data is not None:
                self._display_frame(frame_data)
            
            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF
            self._handle_key(key)
        
        # Cleanup
        cv2.destroyAllWindows()
        self.logger.info("Replay window closed")


def main():
    """Entry point for replay window."""
    import sys
    import argparse
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Parse arguments
    parser = argparse.ArgumentParser(description='Replay ForceUMI episode')
    parser.add_argument('episode', type=str, help='Path to episode HDF5 file')
    parser.add_argument('--config', type=str, help='Optional config file', default=None)
    
    args = parser.parse_args()
    
    # Load config if provided
    config = None
    if args.config:
        from forceumi.config import ConfigManager
        config = ConfigManager.load_config(args.config)
    
    # Create and run replay window
    window = ReplayWindow(args.episode, config)
    window.run()


if __name__ == '__main__':
    main()

