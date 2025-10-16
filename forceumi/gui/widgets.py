"""
Custom GUI Widgets

Custom UI components for the ForceUMI data collection interface.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QTextEdit, QGroupBox,
    QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette
from typing import Optional


class StatusIndicator(QWidget):
    """LED-style status indicator widget"""
    
    def __init__(self, label: str = "", parent: Optional[QWidget] = None):
        """
        Initialize status indicator
        
        Args:
            label: Label text
            parent: Parent widget
        """
        super().__init__(parent)
        self.is_active = False
        
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # LED indicator
        self.led = QFrame()
        self.led.setFixedSize(16, 16)
        self.led.setFrameShape(QFrame.Box)
        self.led.setLineWidth(1)
        self.update_status(False)
        
        # Label
        self.label = QLabel(label)
        
        layout.addWidget(self.led)
        layout.addWidget(self.label)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def update_status(self, active: bool):
        """
        Update indicator status
        
        Args:
            active: Whether indicator is active
        """
        self.is_active = active
        
        if active:
            self.led.setStyleSheet("background-color: #00ff00; border: 1px solid #00aa00;")
        else:
            self.led.setStyleSheet("background-color: #888888; border: 1px solid #555555;")


class DevicePanel(QGroupBox):
    """Panel displaying device connection status"""
    
    connect_clicked = pyqtSignal(str)  # device name
    disconnect_clicked = pyqtSignal(str)  # device name
    
    def __init__(self, title: str = "Devices", parent: Optional[QWidget] = None):
        """
        Initialize device panel
        
        Args:
            title: Panel title
            parent: Parent widget
        """
        super().__init__(title, parent)
        
        layout = QVBoxLayout()
        
        # Device status indicators
        self.camera_status = StatusIndicator("Camera")
        self.pose_status = StatusIndicator("Pose Sensor")
        self.force_status = StatusIndicator("Force Sensor")
        
        layout.addWidget(self.camera_status)
        layout.addWidget(self.pose_status)
        layout.addWidget(self.force_status)
        
        # Control buttons
        btn_layout = QHBoxLayout()
        
        self.btn_connect_all = QPushButton("Connect All")
        self.btn_connect_all.clicked.connect(self._on_connect_all)
        
        self.btn_disconnect_all = QPushButton("Disconnect All")
        self.btn_disconnect_all.clicked.connect(self._on_disconnect_all)
        
        btn_layout.addWidget(self.btn_connect_all)
        btn_layout.addWidget(self.btn_disconnect_all)
        
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def update_device_status(self, device: str, connected: bool):
        """
        Update device connection status
        
        Args:
            device: Device name
            connected: Connection status
        """
        if device == "camera":
            self.camera_status.update_status(connected)
        elif device == "pose_sensor":
            self.pose_status.update_status(connected)
        elif device == "force_sensor":
            self.force_status.update_status(connected)
    
    def _on_connect_all(self):
        """Handle connect all button click"""
        self.connect_clicked.emit("all")
    
    def _on_disconnect_all(self):
        """Handle disconnect all button click"""
        self.disconnect_clicked.emit("all")


class ControlPanel(QGroupBox):
    """Panel with collection control buttons"""
    
    start_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()
    save_clicked = pyqtSignal()
    
    def __init__(self, title: str = "Collection Control", parent: Optional[QWidget] = None):
        """
        Initialize control panel
        
        Args:
            title: Panel title
            parent: Parent widget
        """
        super().__init__(title, parent)
        
        layout = QVBoxLayout()
        
        # Task description
        desc_layout = QHBoxLayout()
        desc_layout.addWidget(QLabel("Task:"))
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("Enter task description...")
        desc_layout.addWidget(self.task_input)
        layout.addLayout(desc_layout)
        
        # Control buttons
        btn_layout = QHBoxLayout()
        
        self.btn_start = QPushButton("Start Episode")
        self.btn_start.clicked.connect(self.start_clicked)
        self.btn_start.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        
        self.btn_stop = QPushButton("Stop Episode")
        self.btn_stop.clicked.connect(self.stop_clicked)
        self.btn_stop.setEnabled(False)
        self.btn_stop.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
        
        self.btn_save = QPushButton("Save")
        self.btn_save.clicked.connect(self.save_clicked)
        self.btn_save.setEnabled(False)
        
        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_stop)
        btn_layout.addWidget(self.btn_save)
        
        layout.addLayout(btn_layout)
        
        # Status display
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setBold(True)
        self.status_label.setFont(font)
        layout.addWidget(self.status_label)
        
        # Stats display
        stats_layout = QHBoxLayout()
        
        self.frames_label = QLabel("Frames: 0")
        self.duration_label = QLabel("Duration: 0.0s")
        self.fps_label = QLabel("FPS: 0.0")
        
        stats_layout.addWidget(self.frames_label)
        stats_layout.addWidget(self.duration_label)
        stats_layout.addWidget(self.fps_label)
        
        layout.addLayout(stats_layout)
        
        self.setLayout(layout)
    
    def set_collecting_state(self, collecting: bool):
        """
        Update UI state for collection
        
        Args:
            collecting: Whether currently collecting
        """
        self.btn_start.setEnabled(not collecting)
        self.btn_stop.setEnabled(collecting)
        self.task_input.setEnabled(not collecting)
        
        if collecting:
            self.status_label.setText("Collecting...")
            self.status_label.setStyleSheet("color: green;")
        else:
            self.status_label.setText("Ready")
            self.status_label.setStyleSheet("color: black;")
    
    def update_stats(self, frames: int, duration: float, fps: float):
        """
        Update collection statistics
        
        Args:
            frames: Number of frames collected
            duration: Collection duration in seconds
            fps: Current FPS
        """
        self.frames_label.setText(f"Frames: {frames}")
        self.duration_label.setText(f"Duration: {duration:.1f}s")
        self.fps_label.setText(f"FPS: {fps:.1f}")
    
    def get_task_description(self) -> str:
        """
        Get task description from input
        
        Returns:
            str: Task description
        """
        return self.task_input.text()


class LogPanel(QGroupBox):
    """Panel displaying log messages"""
    
    def __init__(self, title: str = "Log", parent: Optional[QWidget] = None):
        """
        Initialize log panel
        
        Args:
            title: Panel title
            parent: Parent widget
        """
        super().__init__(title, parent)
        
        layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        
        layout.addWidget(self.log_text)
        
        # Clear button
        self.btn_clear = QPushButton("Clear Log")
        self.btn_clear.clicked.connect(self.clear_log)
        layout.addWidget(self.btn_clear)
        
        self.setLayout(layout)
    
    def append_log(self, message: str, level: str = "INFO"):
        """
        Append log message
        
        Args:
            message: Log message
            level: Log level (INFO, WARNING, ERROR)
        """
        color_map = {
            "INFO": "black",
            "WARNING": "orange",
            "ERROR": "red",
        }
        color = color_map.get(level, "black")
        
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        self.log_text.append(
            f'<span style="color: {color};">[{timestamp}] {level}: {message}</span>'
        )
        
        # Auto-scroll to bottom
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
    
    def clear_log(self):
        """Clear log messages"""
        self.log_text.clear()

