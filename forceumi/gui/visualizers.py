"""
Data Visualizers

Components for visualizing different types of data.
"""

import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
import pyqtgraph as pg
from typing import Optional


class ImageViewer(QWidget):
    """Widget for displaying RGB images"""
    
    def __init__(self, width: int = 640, height: int = 480, parent=None):
        """
        Initialize image viewer
        
        Args:
            width: Display width
            height: Display height
            parent: Parent widget
        """
        super().__init__(parent)
        self.display_width = width
        self.display_height = height
        
        self.initUI()
    
    def initUI(self):
        """Initialize UI components"""
        layout = QVBoxLayout()
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(self.display_width, self.display_height)
        self.image_label.setStyleSheet("border: 1px solid black; background-color: #2b2b2b;")
        
        layout.addWidget(self.image_label)
        self.setLayout(layout)
    
    def update_image(self, image: np.ndarray):
        """
        Update displayed image
        
        Args:
            image: RGB image array (H, W, 3)
        """
        if image is None or len(image.shape) != 3:
            return
        
        h, w, c = image.shape
        
        # Convert to QImage
        bytes_per_line = c * w
        q_image = QImage(image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        # Scale to display size
        pixmap = QPixmap.fromImage(q_image)
        scaled_pixmap = pixmap.scaled(
            self.display_width,
            self.display_height,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        
        self.image_label.setPixmap(scaled_pixmap)
    
    def clear(self):
        """Clear displayed image"""
        self.image_label.clear()


class ForcePlotter(QWidget):
    """Widget for plotting force/torque data"""
    
    def __init__(self, max_points: int = 500, parent=None):
        """
        Initialize force plotter
        
        Args:
            max_points: Maximum number of points to display
            parent: Parent widget
        """
        super().__init__(parent)
        self.max_points = max_points
        
        # Data buffers
        self.force_data = {
            "fx": [], "fy": [], "fz": [],
            "mx": [], "my": [], "mz": []
        }
        
        self.initUI()
    
    def initUI(self):
        """Initialize UI components"""
        layout = QVBoxLayout()
        
        # Create plot widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.setLabel('left', 'Force/Torque')
        self.plot_widget.setLabel('bottom', 'Sample')
        self.plot_widget.addLegend()
        
        # Create plot curves
        self.curves = {}
        colors = {
            "fx": "r", "fy": "g", "fz": "b",
            "mx": "c", "my": "m", "mz": "y"
        }
        
        for key, color in colors.items():
            self.curves[key] = self.plot_widget.plot(
                pen=pg.mkPen(color, width=2),
                name=key
            )
        
        layout.addWidget(self.plot_widget)
        self.setLayout(layout)
    
    def update_force(self, force: np.ndarray):
        """
        Update force plot with new data
        
        Args:
            force: 6-axis force/torque [fx, fy, fz, mx, my, mz]
        """
        if force is None or len(force) != 6:
            return
        
        # Add new data
        labels = ["fx", "fy", "fz", "mx", "my", "mz"]
        for i, label in enumerate(labels):
            self.force_data[label].append(force[i])
            
            # Keep only max_points
            if len(self.force_data[label]) > self.max_points:
                self.force_data[label].pop(0)
        
        # Update plots
        for label in labels:
            self.curves[label].setData(self.force_data[label])
    
    def clear(self):
        """Clear all plot data"""
        for key in self.force_data:
            self.force_data[key].clear()
            self.curves[key].setData([])


class PoseDisplay(QWidget):
    """Widget for displaying pose data"""
    
    def __init__(self, parent=None):
        """
        Initialize pose display
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.initUI()
    
    def initUI(self):
        """Initialize UI components"""
        layout = QVBoxLayout()
        
        # Create labels for pose data
        self.pose_labels = {}
        labels = ["x", "y", "z", "rx", "ry", "rz", "gripper"]
        
        for label in labels:
            label_widget = QLabel(f"{label}: 0.000")
            label_widget.setStyleSheet("font-family: monospace; font-size: 12pt;")
            self.pose_labels[label] = label_widget
            layout.addWidget(label_widget)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def update_pose(self, pose: np.ndarray):
        """
        Update pose display
        
        Args:
            pose: 7D state [x, y, z, rx, ry, rz, gripper]
        """
        if pose is None or len(pose) != 7:
            return
        
        labels = ["x", "y", "z", "rx", "ry", "rz", "gripper"]
        for i, label in enumerate(labels):
            self.pose_labels[label].setText(f"{label}: {pose[i]:.3f}")
    
    def clear(self):
        """Clear pose display"""
        labels = ["x", "y", "z", "rx", "ry", "rz", "gripper"]
        for label in labels:
            self.pose_labels[label].setText(f"{label}: 0.000")


class ActionDisplay(QWidget):
    """Widget for displaying action data"""
    
    def __init__(self, parent=None):
        """
        Initialize action display
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.initUI()
    
    def initUI(self):
        """Initialize UI components"""
        layout = QVBoxLayout()
        
        # Create labels for action data
        self.action_labels = {}
        labels = ["dx", "dy", "dz", "drx", "dry", "drz", "gripper"]
        
        for label in labels:
            label_widget = QLabel(f"{label}: 0.000")
            label_widget.setStyleSheet("font-family: monospace; font-size: 12pt;")
            self.action_labels[label] = label_widget
            layout.addWidget(label_widget)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def update_action(self, action: np.ndarray):
        """
        Update action display
        
        Args:
            action: 7D action [dx, dy, dz, drx, dry, drz, gripper]
                   Note: gripper is always absolute value
        """
        if action is None or len(action) != 7:
            return
        
        labels = ["dx", "dy", "dz", "drx", "dry", "drz", "gripper"]
        for i, label in enumerate(labels):
            self.action_labels[label].setText(f"{label}: {action[i]:.3f}")
    
    def clear(self):
        """Clear action display"""
        labels = ["dx", "dy", "dz", "drx", "dry", "drz", "gripper"]
        for label in labels:
            self.action_labels[label].setText(f"{label}: 0.000")


# Aliases for convenience
ForceViewer = ForcePlotter
StateViewer = PoseDisplay
