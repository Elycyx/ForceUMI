"""
ForceUMI Data Collection System

Complete system for robotic arm data collection with multi-modal synchronized acquisition and visualization.
"""

__version__ = "0.1.0"

from forceumi.collector import DataCollector
from forceumi.config import Config

__all__ = ["DataCollector", "Config"]

