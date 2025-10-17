"""
OpenCV-based Data Visualizer

Uses OpenCV's highgui module for visualization to avoid Qt conflicts.
"""

import cv2
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from typing import Optional, Dict, Any
from collections import deque
import time


class CVVisualizer:
    """OpenCV-based visualizer for ForceUMI data collection"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize visualizer
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Window names
        self.win_main = "ForceUMI - Main View"
        self.win_force = "ForceUMI - Force Data"
        self.win_state = "ForceUMI - State Data"
        self.win_control = "ForceUMI - Control Panel"
        
        # Display settings
        self.img_width = self.config.get("image_width", 640)
        self.img_height = self.config.get("image_height", 480)
        self.force_plot_width = 800
        self.force_plot_height = 400
        self.state_plot_width = 600
        self.state_plot_height = 300
        self.control_width = 400
        self.control_height = 200
        
        # Data buffers
        self.max_points = self.config.get("force_plot_length", 500)
        self.force_buffer = {
            "fx": deque(maxlen=self.max_points),
            "fy": deque(maxlen=self.max_points),
            "fz": deque(maxlen=self.max_points),
            "mx": deque(maxlen=self.max_points),
            "my": deque(maxlen=self.max_points),
            "mz": deque(maxlen=self.max_points),
        }
        self.state_buffer = {
            "x": deque(maxlen=self.max_points),
            "y": deque(maxlen=self.max_points),
            "z": deque(maxlen=self.max_points),
            "rx": deque(maxlen=self.max_points),
            "ry": deque(maxlen=self.max_points),
            "rz": deque(maxlen=self.max_points),
            "gripper": deque(maxlen=self.max_points),
        }
        
        # Current data
        self.current_image = None
        self.current_force = None
        self.current_state = None
        
        # Status
        self.is_collecting = False
        self.is_connected = False
        self.frame_count = 0
        self.fps = 0.0
        self.duration = 0.0
        
        # Initialize windows
        self._init_windows()
        
    def _init_windows(self):
        """Initialize OpenCV windows"""
        # Main image window
        cv2.namedWindow(self.win_main, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.win_main, self.img_width, self.img_height)
        
        # Force data window
        cv2.namedWindow(self.win_force, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.win_force, self.force_plot_width, self.force_plot_height)
        
        # State data window
        cv2.namedWindow(self.win_state, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.win_state, self.state_plot_width, self.state_plot_height)
        
        # Control panel window
        cv2.namedWindow(self.win_control, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.win_control, self.control_width, self.control_height)
        
        # Display initial content
        self._show_placeholder_image()
        self._update_force_plot()
        self._update_state_plot()
        self._update_control_panel()
    
    def _show_placeholder_image(self):
        """Show placeholder when no image available"""
        placeholder = np.zeros((self.img_height, self.img_width, 3), dtype=np.uint8)
        cv2.putText(placeholder, "No Image", 
                   (self.img_width//2 - 80, self.img_height//2),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (128, 128, 128), 2)
        cv2.imshow(self.win_main, placeholder)
    
    def update_image(self, image: np.ndarray):
        """
        Update displayed image
        
        Args:
            image: RGB image array (H, W, 3)
        """
        if image is None:
            self._show_placeholder_image()
            return
        
        self.current_image = image.copy()
        
        # Convert RGB to BGR for OpenCV
        image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        # Resize if needed
        if image_bgr.shape[:2] != (self.img_height, self.img_width):
            image_bgr = cv2.resize(image_bgr, (self.img_width, self.img_height))
        
        # Add status overlay
        self._add_status_overlay(image_bgr)
        
        cv2.imshow(self.win_main, image_bgr)
    
    def _add_status_overlay(self, image: np.ndarray):
        """Add status information overlay to image"""
        # Status text
        if self.is_collecting:
            status = "COLLECTING"
            color = (0, 255, 0)  # Green
        elif self.is_connected:
            status = "CONNECTED"
            color = (255, 255, 0)  # Yellow
        else:
            status = "DISCONNECTED"
            color = (0, 0, 255)  # Red
        
        # Add semi-transparent background
        overlay = image.copy()
        cv2.rectangle(overlay, (10, 10), (250, 60), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.3, image, 0.7, 0, image)
        
        # Add text
        cv2.putText(image, status, (20, 35),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        cv2.putText(image, f"Frames: {self.frame_count}", (20, 55),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    def update_force(self, force: np.ndarray):
        """
        Update force data
        
        Args:
            force: 6D force array [fx, fy, fz, mx, my, mz]
        """
        if force is None or len(force) != 6:
            return
        
        self.current_force = force.copy()
        
        # Update buffers
        self.force_buffer["fx"].append(force[0])
        self.force_buffer["fy"].append(force[1])
        self.force_buffer["fz"].append(force[2])
        self.force_buffer["mx"].append(force[3])
        self.force_buffer["my"].append(force[4])
        self.force_buffer["mz"].append(force[5])
        
        self._update_force_plot()
    
    def _update_force_plot(self):
        """Update force plot using matplotlib"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 4))
        
        # Force plot
        if len(self.force_buffer["fx"]) > 0:
            x = list(range(len(self.force_buffer["fx"])))
            ax1.plot(x, list(self.force_buffer["fx"]), 'r-', label='Fx', linewidth=1)
            ax1.plot(x, list(self.force_buffer["fy"]), 'g-', label='Fy', linewidth=1)
            ax1.plot(x, list(self.force_buffer["fz"]), 'b-', label='Fz', linewidth=1)
            ax1.set_ylabel('Force (N)')
            ax1.legend(loc='upper right', fontsize=8)
            ax1.grid(True, alpha=0.3)
        
        # Torque plot
        if len(self.force_buffer["mx"]) > 0:
            x = list(range(len(self.force_buffer["mx"])))
            ax2.plot(x, list(self.force_buffer["mx"]), 'r-', label='Mx', linewidth=1)
            ax2.plot(x, list(self.force_buffer["my"]), 'g-', label='My', linewidth=1)
            ax2.plot(x, list(self.force_buffer["mz"]), 'b-', label='Mz', linewidth=1)
            ax2.set_xlabel('Samples')
            ax2.set_ylabel('Torque (Nm)')
            ax2.legend(loc='upper right', fontsize=8)
            ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Convert to image
        fig.canvas.draw()
        plot_img = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
        plot_img = plot_img.reshape(fig.canvas.get_width_height()[::-1] + (3,))
        
        # Convert RGB to BGR
        plot_img_bgr = cv2.cvtColor(plot_img, cv2.COLOR_RGB2BGR)
        
        # Resize to fit window
        plot_img_bgr = cv2.resize(plot_img_bgr, 
                                   (self.force_plot_width, self.force_plot_height))
        
        cv2.imshow(self.win_force, plot_img_bgr)
        plt.close(fig)
    
    def update_state(self, state: np.ndarray):
        """
        Update state data
        
        Args:
            state: 7D state array [x, y, z, rx, ry, rz, gripper]
        """
        if state is None or len(state) != 7:
            return
        
        self.current_state = state.copy()
        
        # Update buffers
        self.state_buffer["x"].append(state[0])
        self.state_buffer["y"].append(state[1])
        self.state_buffer["z"].append(state[2])
        self.state_buffer["rx"].append(state[3])
        self.state_buffer["ry"].append(state[4])
        self.state_buffer["rz"].append(state[5])
        self.state_buffer["gripper"].append(state[6])
        
        self._update_state_plot()
    
    def _update_state_plot(self):
        """Update state plot and display"""
        # Create text display with current values
        display = np.ones((self.state_plot_height, self.state_plot_width, 3), 
                         dtype=np.uint8) * 255
        
        if self.current_state is not None:
            y_offset = 40
            line_height = 35
            
            cv2.putText(display, "Current State:", (20, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
            y_offset += line_height
            
            labels = ["X:", "Y:", "Z:", "RX:", "RY:", "RZ:", "Gripper:"]
            for i, (label, value) in enumerate(zip(labels, self.current_state)):
                text = f"{label} {value:8.3f}"
                cv2.putText(display, text, (20, y_offset + i * line_height),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (50, 50, 50), 1)
        else:
            cv2.putText(display, "No State Data", (150, 150),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (128, 128, 128), 2)
        
        cv2.imshow(self.win_state, display)
    
    def update_status(self, is_collecting: bool, is_connected: bool, 
                     frame_count: int = 0, duration: float = 0.0):
        """
        Update collection status
        
        Args:
            is_collecting: Whether currently collecting
            is_connected: Whether devices are connected
            frame_count: Number of frames collected
            duration: Collection duration in seconds
        """
        self.is_collecting = is_collecting
        self.is_connected = is_connected
        self.frame_count = frame_count
        self.duration = duration
        
        if duration > 0:
            self.fps = frame_count / duration
        else:
            self.fps = 0.0
        
        self._update_control_panel()
    
    def _update_control_panel(self):
        """Update control panel display"""
        panel = np.ones((self.control_height, self.control_width, 3), 
                       dtype=np.uint8) * 240
        
        y_offset = 30
        line_height = 30
        
        # Title
        cv2.putText(panel, "ForceUMI Control", (20, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
        y_offset += line_height + 10
        
        # Status
        status_color = (0, 150, 0) if self.is_connected else (0, 0, 200)
        status_text = "Connected" if self.is_connected else "Disconnected"
        cv2.putText(panel, f"Status: {status_text}", (20, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 1)
        y_offset += line_height
        
        # Collection status
        coll_color = (0, 200, 0) if self.is_collecting else (100, 100, 100)
        coll_text = "COLLECTING" if self.is_collecting else "Idle"
        cv2.putText(panel, f"Collection: {coll_text}", (20, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, coll_color, 1)
        y_offset += line_height
        
        # Stats
        cv2.putText(panel, f"Frames: {self.frame_count}", (20, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (50, 50, 50), 1)
        y_offset += line_height
        
        cv2.putText(panel, f"FPS: {self.fps:.1f}", (20, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (50, 50, 50), 1)
        
        # Add instructions at bottom
        cv2.line(panel, (10, self.control_height - 65), 
                (self.control_width - 10, self.control_height - 65), (200, 200, 200), 1)
        
        instructions = [
            "Keys:",
            "C: Connect  D: Disconnect",
            "S: Start    E: Stop/Save",
            "Q: Quit"
        ]
        
        small_y = self.control_height - 55
        for instr in instructions:
            cv2.putText(panel, instr, (20, small_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (80, 80, 80), 1)
            small_y += 15
        
        cv2.imshow(self.win_control, panel)
    
    def wait_key(self, delay: int = 1) -> int:
        """
        Wait for key press
        
        Args:
            delay: Wait time in milliseconds
            
        Returns:
            int: Key code (-1 if no key pressed)
        """
        return cv2.waitKey(delay) & 0xFF
    
    def close(self):
        """Close all windows"""
        cv2.destroyAllWindows()
    
    def is_window_open(self) -> bool:
        """
        Check if windows are still open
        
        Returns:
            bool: True if at least one window is open
        """
        try:
            # Check if main window is still open
            return cv2.getWindowProperty(self.win_main, cv2.WND_PROP_VISIBLE) >= 1
        except:
            return False

