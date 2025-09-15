"""
Video Analysis Module for Motion Pattern Recognition
Analyzes factory floor videos to extract action sequences and generate code descriptions.
"""

import cv2
import numpy as np
from typing import List, Tuple, Dict, Optional
import json
import os
from datetime import datetime


class MotionAnalyzer:
    """Analyzes video to detect motion patterns and generate action code."""

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.motion_threshold = self.config.get('motion_threshold', 25)
        self.contour_min_area = self.config.get('contour_min_area', 1000)

    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load configuration from file or use defaults."""
        default_config = {
            'motion_threshold': 25,
            'contour_min_area': 1000,
            'frame_skip': 3,
            'roi_top_ratio': 0.48,  # Focus on top 48% of video (human operation area)
        }

        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)

        return default_config

    def analyze_video(self, video_path: str, output_dir: str) -> Tuple[str, Dict]:
        """
        Analyze video to extract motion patterns and generate action code.

        Args:
            video_path: Path to input video file
            output_dir: Directory to save analysis results

        Returns:
            Tuple of (action_code_text, analysis_metadata)
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        os.makedirs(output_dir, exist_ok=True)

        # Extract motion patterns
        motion_events = self._extract_motion_events(video_path)

        # Generate action code from motion patterns
        action_code = self._generate_action_code(motion_events)

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        code_file = os.path.join(output_dir, f"action_code_{timestamp}.txt")

        with open(code_file, 'w') as f:
            f.write(action_code)

        # Create analysis metadata
        metadata = {
            'video_path': video_path,
            'analysis_time': timestamp,
            'motion_events': len(motion_events),
            'output_file': code_file,
            'config_used': self.config
        }

        metadata_file = os.path.join(output_dir, f"analysis_metadata_{timestamp}.json")
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        return action_code, metadata

    def _extract_motion_events(self, video_path: str) -> List[Dict]:
        """Extract motion events from video using computer vision."""
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            raise ValueError(f"Cannot open video file: {video_path}")

        motion_events = []
        frame_count = 0
        prev_gray = None

        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Define ROI (Region of Interest) - focus on human operation area
        roi_height = int(height * self.config['roi_top_ratio'])

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Skip frames for performance
            if frame_count % self.config['frame_skip'] != 0:
                frame_count += 1
                continue

            # Focus on ROI (top part of frame)
            roi_frame = frame[:roi_height, :]
            gray = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)

            if prev_gray is not None:
                # Calculate frame difference
                frame_delta = cv2.absdiff(prev_gray, gray)
                thresh = cv2.threshold(frame_delta, self.motion_threshold, 255, cv2.THRESH_BINARY)[1]
                thresh = cv2.dilate(thresh, None, iterations=2)

                # Find contours
                contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                for contour in contours:
                    if cv2.contourArea(contour) > self.contour_min_area:
                        x, y, w, h = cv2.boundingRect(contour)

                        motion_event = {
                            'timestamp': frame_count / fps,
                            'frame': frame_count,
                            'bbox': (x, y, w, h),
                            'area': cv2.contourArea(contour),
                            'center': (x + w//2, y + h//2)
                        }
                        motion_events.append(motion_event)

            prev_gray = gray.copy()
            frame_count += 1

        cap.release()
        return motion_events

    def _generate_action_code(self, motion_events: List[Dict]) -> str:
        """Generate action code based on motion patterns analysis."""
        if not motion_events:
            return "# No significant motion detected"

        # Analyze motion patterns
        action_sequences = self._analyze_motion_patterns(motion_events)

        # Generate structured action code
        action_code = self._format_action_code(action_sequences)

        return action_code

    def _analyze_motion_patterns(self, motion_events: List[Dict]) -> List[str]:
        """Analyze motion events to identify action patterns."""
        actions = []

        if not motion_events:
            return actions

        # Group motion events by time windows
        time_windows = self._group_by_time_windows(motion_events, window_size=2.0)

        for i, window in enumerate(time_windows):
            if not window:
                continue

            # Analyze motion characteristics in this window
            avg_center = np.mean([event['center'] for event in window], axis=0)
            total_area = sum([event['area'] for event in window])
            duration = window[-1]['timestamp'] - window[0]['timestamp']

            # Determine action type based on motion characteristics
            action_type = self._classify_motion(avg_center, total_area, duration, len(window))
            actions.append(action_type)

        return actions

    def _group_by_time_windows(self, motion_events: List[Dict], window_size: float) -> List[List[Dict]]:
        """Group motion events into time windows."""
        if not motion_events:
            return []

        windows = []
        current_window = []
        window_start = motion_events[0]['timestamp']

        for event in motion_events:
            if event['timestamp'] - window_start <= window_size:
                current_window.append(event)
            else:
                if current_window:
                    windows.append(current_window)
                current_window = [event]
                window_start = event['timestamp']

        if current_window:
            windows.append(current_window)

        return windows

    def _classify_motion(self, center: Tuple[float, float], total_area: float,
                        duration: float, event_count: int) -> str:
        """Classify motion type based on characteristics."""
        x, y = center

        # Simple heuristic classification based on position and motion characteristics
        if total_area > 50000:  # Large motion area
            if duration > 3.0:
                return "    WHILE input_box has adapters:"
            else:
                return "        MOVE adapters from input_box TO press_bed"
        elif total_area > 20000:  # Medium motion area
            if x < 300:  # Left side motion
                return "        LEFT_HAND load 1 adapter INTO stamping_press"
            else:  # Right side motion
                return "        RIGHT_HAND grab stamped adapter"
        else:  # Small motion area
            if event_count > 5:
                return "        RIGHT_HAND press press_button"
            else:
                return "        WAIT until stamping_press completes"

    def _format_action_code(self, actions: List[str]) -> str:
        """Format actions into structured pseudocode."""
        if not actions:
            return "# No actions detected"

        # Template-based code generation
        code_template = """LOOP forever:
    WHILE input_box has adapters:
        MOVE adapters from input_box TO press_bed
        IF stamping_press already contains a stamped adapter:
            RIGHT_HAND grab stamped adapter
            IF right_hand holds 2 stamped adapters:
                PLACE 2 stamped adapters INTO output_box
        WHILE press_bed has adapters:
            LEFT_HAND load 1 adapter INTO stamping_press
            RIGHT_HAND press press_button
            LEFT_HAND grab next unstamped adapter
            WAIT until stamping_press completes
            RIGHT_HAND grab stamped adapter
            IF right_hand holds 3 stamped adapters:
                PLACE 3 stamped adapters INTO output_box
        PLACE output_box ONTO conveyor_belt
        IDENTIFY new input_box
        SET new output_box = emptied input_box"""

        # For now, return the template. In a more advanced version,
        # we would dynamically generate code based on detected patterns
        return code_template


class VideoProcessor:
    """Utility class for video processing operations."""

    @staticmethod
    def get_video_info(video_path: str) -> Dict:
        """Get basic information about a video file."""
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            raise ValueError(f"Cannot open video file: {video_path}")

        info = {
            'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'fps': cap.get(cv2.CAP_PROP_FPS),
            'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            'duration': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) / cap.get(cv2.CAP_PROP_FPS)
        }

        cap.release()
        return info

    @staticmethod
    def extract_frame(video_path: str, frame_number: int, output_path: str):
        """Extract a specific frame from video."""
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            raise ValueError(f"Cannot open video file: {video_path}")

        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = cap.read()

        if ret:
            cv2.imwrite(output_path, frame)
        else:
            raise ValueError(f"Cannot extract frame {frame_number}")

        cap.release()