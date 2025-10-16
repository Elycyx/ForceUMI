"""
Main Window for ForceUMI Data Collection

Primary GUI interface for the data collection system.
"""

import sys
import logging
from pathlib import Path
from typing import Optional

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QSplitter, QMessageBox, QFileDialog
)
from PyQt5.QtCore import QTimer, Qt

from forceumi.collector import DataCollector
from forceumi.devices import Camera, PoseSensor, ForceSensor
from forceumi.config import Config
from forceumi.gui.widgets import DevicePanel, ControlPanel, LogPanel
from forceumi.gui.visualizers import ImageViewer, ForceViewer, StateViewer


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class MainWindow(QMainWindow):
    """Main application window for ForceUMI data collection"""
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize main window
        
        Args:
            config: Configuration object
        """
        super().__init__()
        
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
            max_fps=collector_config.get("max_fps", 30.0)
        )
        
        # Setup UI
        self.init_ui()
        
        # Setup update timer
        update_interval = self.config.get("gui.update_interval", 33)
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(update_interval)
        
        # Logging handler
        self.setup_logging()
    
    def init_ui(self):
        """Initialize user interface"""
        window_title = self.config.get("gui.window_title", "ForceUMI Data Collection")
        self.setWindowTitle(window_title)
        self.setGeometry(100, 100, 1400, 900)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout()
        
        # Left panel - Controls and device status
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        
        self.device_panel = DevicePanel()
        self.device_panel.connect_clicked.connect(self.on_connect_devices)
        self.device_panel.disconnect_clicked.connect(self.on_disconnect_devices)
        
        self.control_panel = ControlPanel()
        self.control_panel.start_clicked.connect(self.on_start_episode)
        self.control_panel.stop_clicked.connect(self.on_stop_episode)
        self.control_panel.save_clicked.connect(self.on_save_episode)
        
        self.log_panel = LogPanel()
        
        left_layout.addWidget(self.device_panel)
        left_layout.addWidget(self.control_panel)
        left_layout.addWidget(self.log_panel)
        left_layout.addStretch()
        
        left_panel.setLayout(left_layout)
        left_panel.setMaximumWidth(400)
        
        # Right panel - Visualizations
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        
        # Image viewer
        self.image_viewer = ImageViewer()
        
        # Splitter for force and state viewers
        bottom_splitter = QSplitter(Qt.Horizontal)
        
        self.force_viewer = ForceViewer()
        self.state_viewer = StateViewer()
        
        bottom_splitter.addWidget(self.force_viewer)
        bottom_splitter.addWidget(self.state_viewer)
        
        right_layout.addWidget(self.image_viewer, stretch=2)
        right_layout.addWidget(bottom_splitter, stretch=1)
        
        right_panel.setLayout(right_layout)
        
        # Add panels to main layout
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)
        
        central_widget.setLayout(main_layout)
        
        # Menu bar
        self.create_menu_bar()
        
        # Status bar
        self.statusBar().showMessage("Ready")
    
    def create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        load_config_action = file_menu.addAction("Load Config")
        load_config_action.triggered.connect(self.on_load_config)
        
        save_config_action = file_menu.addAction("Save Config")
        save_config_action.triggered.connect(self.on_save_config)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self.on_about)
    
    def setup_logging(self):
        """Setup logging to GUI"""
        class GUILogHandler(logging.Handler):
            def __init__(self, log_panel):
                super().__init__()
                self.log_panel = log_panel
            
            def emit(self, record):
                msg = self.format(record)
                level = record.levelname
                self.log_panel.append_log(msg, level)
        
        handler = GUILogHandler(self.log_panel)
        handler.setFormatter(logging.Formatter('%(name)s - %(message)s'))
        logging.getLogger("forceumi").addHandler(handler)
    
    def on_connect_devices(self, device: str):
        """Handle device connection"""
        self.log_panel.append_log("Connecting devices...", "INFO")
        status = self.collector.connect_devices()
        
        for device_name, connected in status.items():
            self.device_panel.update_device_status(device_name, connected)
            
            if connected:
                self.log_panel.append_log(f"{device_name} connected", "INFO")
            else:
                self.log_panel.append_log(f"{device_name} connection failed", "ERROR")
    
    def on_disconnect_devices(self, device: str):
        """Handle device disconnection"""
        self.log_panel.append_log("Disconnecting devices...", "INFO")
        status = self.collector.disconnect_devices()
        
        for device_name, disconnected in status.items():
            self.device_panel.update_device_status(device_name, False)
            
            if disconnected:
                self.log_panel.append_log(f"{device_name} disconnected", "INFO")
    
    def on_start_episode(self):
        """Handle episode start"""
        task_description = self.control_panel.get_task_description()
        
        metadata = {}
        if task_description:
            metadata["task_description"] = task_description
        
        success = self.collector.start_episode(metadata=metadata)
        
        if success:
            self.control_panel.set_collecting_state(True)
            self.log_panel.append_log("Episode started", "INFO")
            self.statusBar().showMessage("Collecting data...")
        else:
            self.log_panel.append_log("Failed to start episode", "ERROR")
            QMessageBox.warning(self, "Error", "Failed to start episode")
    
    def on_stop_episode(self):
        """Handle episode stop"""
        filepath = self.collector.stop_episode()
        
        self.control_panel.set_collecting_state(False)
        
        if filepath:
            self.log_panel.append_log(f"Episode saved to {filepath}", "INFO")
            self.statusBar().showMessage(f"Episode saved: {filepath}")
        else:
            self.log_panel.append_log("Episode stopped", "INFO")
            self.statusBar().showMessage("Episode stopped")
    
    def on_save_episode(self):
        """Handle manual episode save"""
        if self.collector.current_episode is None:
            QMessageBox.warning(self, "Warning", "No episode to save")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Episode",
            str(Path(self.collector.save_dir) / "episode.hdf5"),
            "HDF5 Files (*.hdf5 *.h5)"
        )
        
        if filename:
            filepath = self.collector.save_current_episode(filename)
            if filepath:
                self.log_panel.append_log(f"Episode saved to {filepath}", "INFO")
            else:
                self.log_panel.append_log("Failed to save episode", "ERROR")
    
    def on_load_config(self):
        """Handle config loading"""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Load Configuration",
            "",
            "Config Files (*.yaml *.yml *.json)"
        )
        
        if filename:
            success = self.config.load(filename)
            if success:
                self.log_panel.append_log(f"Configuration loaded from {filename}", "INFO")
                QMessageBox.information(
                    self, "Success",
                    "Configuration loaded. Please restart the application for changes to take effect."
                )
            else:
                self.log_panel.append_log("Failed to load configuration", "ERROR")
    
    def on_save_config(self):
        """Handle config saving"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Configuration",
            "config.yaml",
            "Config Files (*.yaml *.yml *.json)"
        )
        
        if filename:
            success = self.config.save(filename)
            if success:
                self.log_panel.append_log(f"Configuration saved to {filename}", "INFO")
            else:
                self.log_panel.append_log("Failed to save configuration", "ERROR")
    
    def on_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About ForceUMI",
            "<h2>ForceUMI Data Collection System</h2>"
            "<p>Version 0.1.0</p>"
            "<p>A comprehensive data collection system for robotic arm devices.</p>"
            "<p>Supports RGB camera, pose sensor, and force sensor data acquisition.</p>"
        )
    
    def update_display(self):
        """Update display with latest data"""
        # Get latest frame
        frame_data = self.collector.get_latest_frame(timeout=0.001)
        
        if frame_data:
            # Update image viewer
            if "image" in frame_data:
                self.image_viewer.update_image(frame_data["image"])
            
            # Update force viewer
            if "force" in frame_data:
                self.force_viewer.update_force(frame_data["force"])
            
            # Update state viewer
            if "state" in frame_data:
                self.state_viewer.update_pose(frame_data["state"])
        
        # Update stats
        if self.collector.is_collecting():
            stats = self.collector.get_episode_stats()
            self.control_panel.update_stats(
                frames=stats.get("num_frames", 0),
                duration=stats.get("duration", 0.0),
                fps=stats.get("num_frames", 0) / max(stats.get("duration", 1.0), 0.001)
            )
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Stop collection if running
        if self.collector.is_collecting():
            reply = QMessageBox.question(
                self,
                "Confirm Exit",
                "Data collection is in progress. Stop and exit?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.collector.stop_episode()
            else:
                event.ignore()
                return
        
        # Disconnect devices
        self.collector.disconnect_devices()
        
        event.accept()


def main():
    """Main entry point for GUI application"""
    app = QApplication(sys.argv)
    
    # Load config if exists
    config_path = Path("config.yaml")
    config = Config(str(config_path) if config_path.exists() else None)
    
    # Create and show main window
    window = MainWindow(config)
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

