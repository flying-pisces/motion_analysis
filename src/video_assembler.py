"""
Video Assembly Module for Training Video Generation
Combines factory floor videos with generated action code to create training materials.
"""

import cv2
import numpy as np
from typing import List, Tuple, Dict, Optional
import os
import json
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import subprocess


class VideoAssembler:
    """Assembles training videos by combining raw footage with action code overlay."""

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)

    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load configuration from file or use defaults."""
        default_config = {
            'code_overlay_height_ratio': 0.52,  # Code takes up bottom 52% of assembled video
            'code_background_color': (40, 40, 40),  # Dark gray
            'code_text_color': (255, 255, 255),  # White
            'code_font_size': 18,
            'code_padding': 20,
            'line_height_multiplier': 1.4,
            'output_fps': 30,
            'output_quality': 23  # Lower is better (18-28 range)
        }

        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)

        return default_config

    def assemble_training_video(self, raw_video_path: str, action_code_path: str,
                               output_path: str) -> Dict:
        """
        Create a training video by combining raw footage with action code overlay.

        Args:
            raw_video_path: Path to the raw factory floor video
            action_code_path: Path to the generated action code text file
            output_path: Path for the assembled training video

        Returns:
            Dictionary containing assembly metadata
        """
        if not os.path.exists(raw_video_path):
            raise FileNotFoundError(f"Raw video not found: {raw_video_path}")

        if not os.path.exists(action_code_path):
            raise FileNotFoundError(f"Action code file not found: {action_code_path}")

        # Read action code
        with open(action_code_path, 'r') as f:
            action_code = f.read()

        # Get video properties
        video_info = self._get_video_info(raw_video_path)

        # Calculate dimensions for assembled video
        assembled_dimensions = self._calculate_assembled_dimensions(video_info)

        # Create assembled video
        assembly_info = self._create_assembled_video(
            raw_video_path, action_code, output_path, assembled_dimensions
        )

        # Create metadata
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        metadata = {
            'raw_video_path': raw_video_path,
            'action_code_path': action_code_path,
            'output_path': output_path,
            'assembly_time': timestamp,
            'original_dimensions': (video_info['width'], video_info['height']),
            'assembled_dimensions': assembled_dimensions,
            'duration': video_info['duration'],
            'fps': video_info['fps'],
            'config_used': self.config
        }
        metadata.update(assembly_info)

        return metadata

    def _get_video_info(self, video_path: str) -> Dict:
        """Get video information."""
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        info = {
            'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'fps': cap.get(cv2.CAP_PROP_FPS),
            'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            'duration': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) / cap.get(cv2.CAP_PROP_FPS)
        }

        cap.release()
        return info

    def _calculate_assembled_dimensions(self, video_info: Dict) -> Tuple[int, int]:
        """Calculate dimensions for the assembled video."""
        original_width = video_info['width']
        original_height = video_info['height']

        # The assembled video will be square with the same width as original
        # Top part: scaled raw video, bottom part: code overlay
        assembled_width = original_width
        assembled_height = int(original_width)  # Make it square like the original training video

        return assembled_width, assembled_height

    def _create_assembled_video(self, raw_video_path: str, action_code: str,
                               output_path: str, dimensions: Tuple[int, int]) -> Dict:
        """Create the assembled video with raw footage and code overlay."""
        assembled_width, assembled_height = dimensions

        # Calculate split - raw video on top, code on bottom
        code_section_height = int(assembled_height * self.config['code_overlay_height_ratio'])
        video_section_height = assembled_height - code_section_height

        # Create temporary video with resized raw footage
        temp_resized_path = output_path.replace('.mp4', '_temp_resized.mp4')
        self._resize_raw_video(raw_video_path, temp_resized_path,
                              assembled_width, video_section_height)

        # Create code overlay image
        code_overlay_path = output_path.replace('.mp4', '_code_overlay.png')
        self._create_code_overlay(action_code, code_overlay_path,
                                 assembled_width, code_section_height)

        # Combine video and code overlay using ffmpeg
        assembly_info = self._combine_video_and_overlay(
            temp_resized_path, code_overlay_path, output_path,
            assembled_width, assembled_height, video_section_height
        )

        # Clean up temporary files
        if os.path.exists(temp_resized_path):
            os.remove(temp_resized_path)
        if os.path.exists(code_overlay_path):
            os.remove(code_overlay_path)

        return assembly_info

    def _resize_raw_video(self, input_path: str, output_path: str,
                         width: int, height: int):
        """Resize raw video to fit in the top section."""
        cmd = [
            'ffmpeg', '-i', input_path,
            '-vf', f'scale={width}:{height}',
            '-c:a', 'copy',
            '-y', output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg error: {result.stderr}")

    def _create_code_overlay(self, action_code: str, output_path: str,
                           width: int, height: int):
        """Create static image overlay with action code."""
        # Create image with dark background
        bg_color = self.config['code_background_color']
        img = Image.new('RGB', (width, height), bg_color)
        draw = ImageDraw.Draw(img)

        # Try to load a system font, fallback to default
        try:
            # Try common system fonts
            font_paths = [
                '/System/Library/Fonts/Menlo.ttc',  # macOS
                '/System/Library/Fonts/Monaco.ttc',  # macOS
                'C:\\Windows\\Fonts\\consola.ttf',   # Windows
                '/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf',  # Linux
                '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'  # Linux
            ]

            font = None
            for font_path in font_paths:
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, self.config['code_font_size'])
                    break

            if font is None:
                font = ImageFont.load_default()

        except (OSError, IOError):
            font = ImageFont.load_default()

        # Draw text
        lines = action_code.split('\n')
        y_offset = self.config['code_padding']
        line_height = int(self.config['code_font_size'] * self.config['line_height_multiplier'])

        for line in lines:
            if y_offset + line_height > height - self.config['code_padding']:
                break  # Don't draw beyond image bounds

            draw.text((self.config['code_padding'], y_offset),
                     line, fill=self.config['code_text_color'], font=font)
            y_offset += line_height

        # Add line numbers
        x_offset = self.config['code_padding'] - 30
        y_offset = self.config['code_padding']
        for i, line in enumerate(lines, 1):
            if y_offset + line_height > height - self.config['code_padding']:
                break

            draw.text((x_offset, y_offset), f'{i:2d}',
                     fill=(150, 150, 150), font=font)
            y_offset += line_height

        img.save(output_path)

    def _combine_video_and_overlay(self, video_path: str, overlay_path: str,
                                  output_path: str, total_width: int,
                                  total_height: int, video_height: int) -> Dict:
        """Combine resized video with code overlay using ffmpeg."""

        # Create filter complex for vertical stacking
        filter_complex = (
            f"[0:v]scale={total_width}:{video_height}[vid];"
            f"[1:v]scale={total_width}:{total_height - video_height}[overlay];"
            f"[vid][overlay]vstack=inputs=2[out]"
        )

        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-loop', '1', '-i', overlay_path,
            '-filter_complex', filter_complex,
            '-map', '[out]',
            '-map', '0:a',  # Copy audio from original video
            '-c:v', 'libx264',
            '-crf', str(self.config['output_quality']),
            '-r', str(self.config['output_fps']),
            '-shortest',  # End when shortest input ends (video)
            '-y', output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg assembly error: {result.stderr}")

        # Get output file size
        output_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0

        return {
            'ffmpeg_command': ' '.join(cmd),
            'output_file_size': output_size,
            'assembly_successful': result.returncode == 0
        }


class VideoSplitter:
    """Utility class for splitting assembled training videos back into components."""

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)

    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load configuration."""
        default_config = {
            'code_overlay_height_ratio': 0.52
        }

        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)

        return default_config

    def split_training_video(self, training_video_path: str, output_dir: str) -> Dict:
        """
        Split a training video back into raw footage and code components.

        Args:
            training_video_path: Path to assembled training video
            output_dir: Directory to save split components

        Returns:
            Dictionary with paths to extracted components
        """
        if not os.path.exists(training_video_path):
            raise FileNotFoundError(f"Training video not found: {training_video_path}")

        os.makedirs(output_dir, exist_ok=True)

        # Get video info
        video_info = self._get_video_info(training_video_path)
        width, height = video_info['width'], video_info['height']

        # Calculate split dimensions
        code_section_height = int(height * self.config['code_overlay_height_ratio'])
        video_section_height = height - code_section_height

        # Extract video section (top part)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        raw_video_path = os.path.join(output_dir, f"extracted_raw_video_{timestamp}.mp4")

        self._extract_video_section(training_video_path, raw_video_path,
                                   width, video_section_height)

        # Extract code section (bottom part) as image
        code_image_path = os.path.join(output_dir, f"extracted_code_{timestamp}.png")
        self._extract_code_section(training_video_path, code_image_path,
                                  width, code_section_height, video_section_height)

        return {
            'raw_video_path': raw_video_path,
            'code_image_path': code_image_path,
            'original_dimensions': (width, height),
            'video_section_height': video_section_height,
            'code_section_height': code_section_height
        }

    def _get_video_info(self, video_path: str) -> Dict:
        """Get video information."""
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        info = {
            'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'fps': cap.get(cv2.CAP_PROP_FPS),
            'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            'duration': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) / cap.get(cv2.CAP_PROP_FPS)
        }

        cap.release()
        return info

    def _extract_video_section(self, input_path: str, output_path: str,
                              width: int, height: int):
        """Extract the top video section."""
        cmd = [
            'ffmpeg', '-i', input_path,
            '-vf', f'crop={width}:{height}:0:0',
            '-c:a', 'copy',
            '-y', output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg error extracting video: {result.stderr}")

    def _extract_code_section(self, input_path: str, output_path: str,
                             width: int, height: int, y_offset: int):
        """Extract the bottom code section as an image."""
        cmd = [
            'ffmpeg', '-i', input_path,
            '-vf', f'crop={width}:{height}:0:{y_offset}',
            '-vframes', '1',
            '-y', output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg error extracting code: {result.stderr}")