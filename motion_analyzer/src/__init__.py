"""
Motion Analysis and Video Assembly Tool

This package provides tools for analyzing factory floor videos and creating training materials.
"""

__version__ = "1.0.0"
__author__ = "Motion Analysis Team"
__email__ = "support@motionanalysis.com"

from .video_analyzer import MotionAnalyzer, VideoProcessor
from .video_assembler import VideoAssembler, VideoSplitter

__all__ = [
    'MotionAnalyzer',
    'VideoProcessor',
    'VideoAssembler',
    'VideoSplitter'
]