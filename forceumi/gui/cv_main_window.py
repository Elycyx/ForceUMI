"""
OpenCV-based Main Window for ForceUMI Data Collection

Uses OpenCV's highgui module to avoid Qt conflicts with opencv-python.
"""

import sys
import time
import logging
import cv2
from pathlib import Path
from typing import Optional

from forceumi.collector import DataCollector
from forceumi.devices import Camera, PoseSensor, ForceSensor
from forceumi.config import Config
from forceumi.gui.cv_visualizer import CVVisualizer


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class CVMainWindow:
    """Main application window using OpenCV for ForceUMI data collection"""
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize main window
        
        Args:
            config: Configuration object
        """
        self.logger = logging.getLogger("forceumi.CVMainWindow")
        
        # Configuration
        self.config = config if config else Config()
        
        # Initialize devices
        camera_config = self.config.get("devices.camera", {})
        pose_config = self.config.get("devices.pose_sensor", {})
        force_config = self.config.get("devices.force_sensor", {})
        
        self.camera = Camera(**camera_config)
        self.pose_sensor = PoseSensor(**pose_config)
        self.force_sensor = ForceSensor(**force_config)
        
        # Initialize collector
        collector_config = self.config.get("collector", {})
        data_config = self.config.get("data", {})
        
        self.collector = DataCollector(
            camera=self.camera,
            pose_sensor=self.pose_sensor,
            force_sensor=self.force_sensor,
            save_dir=data_config.get("save_dir", "./data"),
            auto_save=data_config.get("auto_save", True),
            max_fps=collector_config.get("max_fps", 30.0),
            warmup_duration=collector_config.get("warmup_duration", 2.0)
        )
        
        # Initialize visualizer
        gui_config = {
            "image_width": self.config.get("gui.image_display_size", [640, 480])[0],
            "image_height": self.config.get("gui.image_display_size", [640, 480])[1],
            "force_plot_length": self.config.get("gui.force_plot_length", 500),
        }
        self.visualizer = CVVisualizer(gui_config)
        
        # State
        self.running = True
        self.update_interval = self.config.get("gui.update_interval", 33) / 1000.0  # Convert to seconds
        
        self.logger.info("CVMainWindow initialized")
    
    def on_connect_devices(self):
        """Handle device connection"""
        self.logger.info("Connecting devices...")
        status = self.collector.connect_devices()
        
        all_connected = all(status.values()) if status else False
        self.visualizer.update_status(
            is_collecting=self.collector.is_collecting(),
            is_connected=all_connected
        )
        
        for device_name, connected in status.items():
            if connected:
                self.logger.info(f"{device_name} connected")
            else:
                self.logger.error(f"{device_name} connection failed")
    
    def on_disconnect_devices(self):
        """Handle device disconnection"""
        self.logger.info("Disconnecting devices...")
        self.collector.disconnect_devices()
        
        self.visualizer.update_status(
            is_collecting=False,
            is_connected=False
        )
    
    def on_start_episode(self):
        """Handle episode start"""
        metadata = {
            "start_time": time.time(),
            "task_description": "Data collection episode"
        }
        
        success = self.collector.start_episode(metadata=metadata)
        
        if success:
            self.logger.info("Episode started")
            self.visualizer.update_status(
                is_collecting=True,
                is_connected=True
            )
        else:
            self.logger.error("Failed to start episode")
    
    def on_stop_episode(self):
        """Handle episode stop"""
        filepath = self.collector.stop_episode()
        
        if filepath:
            self.logger.info(f"Episode saved to {filepath}")
        else:
            self.logger.info("Episode stopped")
        
        self.visualizer.update_status(
            is_collecting=False,
            is_connected=True,
            frame_count=0,
            duration=0.0
        )
    
    def update_display(self):
        """Update display with latest data"""
        # Get latest frame
        frame_data = self.collector.get_latest_frame(timeout=0.001)
        
        if frame_data:
            # Check if warming up
            is_warming_up = frame_data.get("_warming_up", False)
            
            # Update image viewer with warmup indicator
            if "image" in frame_data:
                image = frame_data["image"].copy()
                
                # Add warmup indicator to image
                if is_warming_up:
                    stats = self.collector.get_episode_stats()
                    warmup_remaining = stats.get("warmup_remaining", 0.0)
                    
                    # Add orange "WARMING UP" text
                    overlay = image.copy()
                    cv2.rectangle(overlay, (10, 70), (280, 110), (0, 100, 255), -1)
                    cv2.addWeighted(overlay, 0.5, image, 0.5, 0, image)
                    
                    cv2.putText(image, f"WARMING UP ({warmup_remaining:.1f}s)", (20, 95),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 2)
                
                self.visualizer.update_image(image)
            
            # Update force viewer
            if "force" in frame_data:
                self.visualizer.update_force(frame_data["force"])
            
            # Update state viewer
            if "state" in frame_data:
                self.visualizer.update_state(frame_data["state"])
        
        # Update stats
        if self.collector.is_collecting():
            stats = self.collector.get_episode_stats()
            
            # Check if warming up
            is_warming_up = stats.get("warming_up", False)
            warmup_remaining = stats.get("warmup_remaining", 0.0)
            
            # Log warmup status
            if is_warming_up and not hasattr(self, '_last_warmup_log'):
                self.logger.info(f"Warming up sensors... ({warmup_remaining:.1f}s remaining)")
                self._last_warmup_log = time.time()
            elif is_warming_up and time.time() - self._last_warmup_log > 1.0:
                self.logger.info(f"Warming up... ({warmup_remaining:.1f}s remaining)")
                self._last_warmup_log = time.time()
            elif not is_warming_up and hasattr(self, '_last_warmup_log'):
                delattr(self, '_last_warmup_log')
            
            self.visualizer.update_status(
                is_collecting=True,
                is_connected=True,
                frame_count=stats.get("num_frames", 0),
                duration=stats.get("duration", 0.0)
            )
    
    def handle_keyboard(self, key: int):
        """
        Handle keyboard input
        
        Args:
            key: Key code from cv2.waitKey()
        """
        if key == ord('q') or key == ord('Q') or key == 27:  # Q or ESC
            self.logger.info("Quit requested")
            self.running = False
            
        elif key == ord('c') or key == ord('C'):
            self.logger.info("Connect devices requested")
            self.on_connect_devices()
            
        elif key == ord('d') or key == ord('D'):
            self.logger.info("Disconnect devices requested")
            self.on_disconnect_devices()
            
        elif key == ord('s') or key == ord('S'):
            if not self.collector.is_collecting():
                self.logger.info("Start collection requested")
                self.on_start_episode()
            
        elif key == ord('e') or key == ord('E'):
            if self.collector.is_collecting():
                self.logger.info("Stop collection requested")
                self.on_stop_episode()
    
    def run(self):
        """Main event loop"""
        self.logger.info("Starting main loop")
        
        last_update = time.time()
        
        try:
            while self.running:
                # Update display at specified interval
                current_time = time.time()
                if current_time - last_update >= self.update_interval:
                    self.update_display()
                    last_update = current_time
                
                # Handle keyboard input
                key = self.visualizer.wait_key(1)
                if key != 255 and key != -1:  # Key pressed
                    self.handle_keyboard(key)
                
                # Check if windows are still open
                if not self.visualizer.is_window_open():
                    self.logger.info("Windows closed")
                    self.running = False
                    
        except KeyboardInterrupt:
            self.logger.info("Interrupted by user")
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup resources"""
        self.logger.info("Cleaning up...")
        
        # Stop collection if running
        if self.collector.is_collecting():
            self.collector.stop_episode()
        
        # Disconnect devices
        self.collector.disconnect_devices()
        
        # Close visualizer
        self.visualizer.close()
        
        self.logger.info("Cleanup complete")


def main():
    """Main entry point for GUI application"""
    # Load config if exists
    config_path = Path("config.yaml")
    config = Config(str(config_path) if config_path.exists() else None)
    
    # Create and run main window
    window = CVMainWindow(config)
    
    print("\n" + "="*60)
    print("ForceUMI Data Collection System")
    print("="*60)
    print("\nKeyboard Controls:")
    print("  C - Connect devices")
    print("  D - Disconnect devices")
    print("  S - Start collection")
    print("  E - Stop/Save episode")
    print("  Q - Quit application")
    print("="*60 + "\n")
    
    window.run()


if __name__ == "__main__":
    main()

