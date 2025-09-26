"""
Object Detection and Tracking Module for Motion Analysis
Identifies and tracks different object types: DUT (Device Under Test), hands, conveyor, fixtures
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from enum import Enum
import json
from collections import deque
from dataclasses import dataclass, field


class ObjectType(Enum):
    """Enumeration for different object types in factory floor videos."""
    DUT = "DUT"  # Device Under Test - main object being manipulated
    LEFT_HAND = "Left Hand"
    RIGHT_HAND = "Right Hand"
    CONVEYOR = "Conveyor Belt"
    FIXTURE = "Fixture"
    UNKNOWN = "Unknown"


@dataclass
class TrackedObject:
    """Represents a tracked object in the video."""
    id: int
    object_type: ObjectType
    bbox: Tuple[int, int, int, int]  # (x, y, width, height)
    center: Tuple[int, int]
    area: float
    color_histogram: Optional[np.ndarray] = None
    motion_history: deque = field(default_factory=lambda: deque(maxlen=30))
    confidence: float = 0.5
    first_seen_frame: int = 0
    last_seen_frame: int = 0
    velocity: Tuple[float, float] = (0.0, 0.0)

    def update_position(self, new_bbox: Tuple[int, int, int, int], frame_num: int):
        """Update object position and calculate velocity."""
        old_center = self.center
        self.bbox = new_bbox
        self.center = (new_bbox[0] + new_bbox[2]//2, new_bbox[1] + new_bbox[3]//2)
        self.area = new_bbox[2] * new_bbox[3]

        # Calculate velocity
        if self.last_seen_frame > 0:
            frames_diff = frame_num - self.last_seen_frame
            if frames_diff > 0:
                self.velocity = (
                    (self.center[0] - old_center[0]) / frames_diff,
                    (self.center[1] - old_center[1]) / frames_diff
                )

        self.last_seen_frame = frame_num
        self.motion_history.append(self.center)


class ObjectTracker:
    """Advanced object tracker that distinguishes between DUT and handlers."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the object tracker with configuration."""
        self.config = self._load_config(config_path)
        self.tracked_objects: Dict[int, TrackedObject] = {}
        self.next_object_id = 0
        self.frame_count = 0

        # Initialize background subtractor for better motion detection
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            detectShadows=True, varThreshold=16
        )

        # Color ranges for skin detection (hands)
        self.skin_lower = np.array([0, 20, 70], dtype=np.uint8)
        self.skin_upper = np.array([20, 255, 255], dtype=np.uint8)

        # Initialize Kalman filters for object tracking
        self.kalman_filters: Dict[int, cv2.KalmanFilter] = {}

    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load configuration from file or use defaults."""
        default_config = {
            'min_object_area': 500,
            'max_object_area': 50000,
            'hand_detection_threshold': 0.6,
            'dut_persistence_frames': 10,
            'max_distance_threshold': 100,
            'conveyor_y_position_ratio': 0.7,  # Bottom 30% of frame
            'fixture_motion_threshold': 5,  # Pixels per frame
            'dut_color_consistency_threshold': 0.7,
        }

        if config_path and cv2.os.path.exists(config_path):
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)

        return default_config

    def process_frame(self, frame: np.ndarray) -> List[TrackedObject]:
        """Process a single frame to detect and track objects."""
        self.frame_count += 1
        height, width = frame.shape[:2]

        # Apply background subtraction
        fg_mask = self.bg_subtractor.apply(frame)

        # Detect hands using skin color detection
        hand_regions = self._detect_hands(frame)

        # Detect moving objects
        moving_objects = self._detect_moving_objects(frame, fg_mask)

        # Classify objects based on various features
        classified_objects = self._classify_objects(
            moving_objects, hand_regions, frame, height, width
        )

        # Update tracking
        self._update_tracking(classified_objects)

        return list(self.tracked_objects.values())

    def _detect_hands(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detect hands using skin color detection."""
        # Convert to YCrCb color space for better skin detection
        ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)

        # Define skin color range in YCrCb
        min_YCrCb = np.array([0, 133, 77], dtype=np.uint8)
        max_YCrCb = np.array([255, 173, 127], dtype=np.uint8)

        # Create skin mask
        skin_mask = cv2.inRange(ycrcb, min_YCrCb, max_YCrCb)

        # Apply morphological operations to reduce noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
        skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_OPEN, kernel)
        skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_CLOSE, kernel)

        # Find contours
        contours, _ = cv2.findContours(skin_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        hand_regions = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > self.config['min_object_area']:
                x, y, w, h = cv2.boundingRect(contour)
                # Filter by aspect ratio (hands are roughly square to slightly rectangular)
                aspect_ratio = w / h if h > 0 else 0
                if 0.5 < aspect_ratio < 2.0:
                    hand_regions.append((x, y, w, h))

        return hand_regions

    def _detect_moving_objects(self, frame: np.ndarray, fg_mask: np.ndarray) -> List[Dict]:
        """Detect moving objects from foreground mask."""
        # Apply morphological operations to clean up the mask
        kernel = np.ones((5, 5), np.uint8)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)

        # Find contours
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        objects = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if self.config['min_object_area'] < area < self.config['max_object_area']:
                x, y, w, h = cv2.boundingRect(contour)

                # Calculate color histogram for the region
                roi = frame[y:y+h, x:x+w]
                hist = cv2.calcHist([roi], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
                hist = cv2.normalize(hist, hist).flatten()

                objects.append({
                    'bbox': (x, y, w, h),
                    'area': area,
                    'center': (x + w//2, y + h//2),
                    'histogram': hist,
                    'contour': contour
                })

        return objects

    def _classify_objects(self, moving_objects: List[Dict], hand_regions: List[Tuple],
                         frame: np.ndarray, height: int, width: int) -> List[Dict]:
        """Classify detected objects into specific types."""
        classified = []

        for obj in moving_objects:
            x, y, w, h = obj['bbox']
            center = obj['center']

            # Initialize classification
            obj_type = ObjectType.UNKNOWN
            confidence = 0.5

            # Check if object matches hand regions
            hand_overlap = self._calculate_overlap_with_regions(obj['bbox'], hand_regions)
            if hand_overlap > self.config['hand_detection_threshold']:
                # Determine left or right hand based on position
                if center[0] < width // 2:
                    obj_type = ObjectType.LEFT_HAND
                else:
                    obj_type = ObjectType.RIGHT_HAND
                confidence = hand_overlap

            # Check if object is in conveyor belt region (bottom of frame)
            elif center[1] > height * self.config['conveyor_y_position_ratio']:
                # Check if object has horizontal motion pattern
                if obj['area'] > 5000:  # Large object at bottom
                    obj_type = ObjectType.CONVEYOR
                    confidence = 0.7

            # Check for fixture (stationary large objects)
            elif obj['area'] > 10000:
                # Fixtures are typically large and relatively stationary
                if self._is_stationary_object(obj):
                    obj_type = ObjectType.FIXTURE
                    confidence = 0.6

            # Default to DUT for medium-sized moving objects
            else:
                # DUT objects are typically consistent in color and size
                if 1000 < obj['area'] < 10000:
                    obj_type = ObjectType.DUT
                    confidence = 0.7

            obj['type'] = obj_type
            obj['confidence'] = confidence
            classified.append(obj)

        return classified

    def _calculate_overlap_with_regions(self, bbox: Tuple, regions: List[Tuple]) -> float:
        """Calculate maximum overlap between bbox and regions."""
        if not regions:
            return 0.0

        x1, y1, w1, h1 = bbox
        max_overlap = 0.0

        for x2, y2, w2, h2 in regions:
            # Calculate intersection
            x_left = max(x1, x2)
            y_top = max(y1, y2)
            x_right = min(x1 + w1, x2 + w2)
            y_bottom = min(y1 + h1, y2 + h2)

            if x_right > x_left and y_bottom > y_top:
                intersection_area = (x_right - x_left) * (y_bottom - y_top)
                bbox_area = w1 * h1
                overlap = intersection_area / bbox_area if bbox_area > 0 else 0
                max_overlap = max(max_overlap, overlap)

        return max_overlap

    def _is_stationary_object(self, obj: Dict) -> bool:
        """Check if object is stationary based on motion history."""
        # For new objects, we can't determine if stationary yet
        center = obj['center']

        # Find if this object was tracked before
        min_distance = float('inf')
        matched_id = None

        for obj_id, tracked in self.tracked_objects.items():
            if tracked.last_seen_frame >= self.frame_count - 5:  # Recently seen
                dist = np.sqrt((center[0] - tracked.center[0])**2 +
                             (center[1] - tracked.center[1])**2)
                if dist < min_distance and dist < self.config['max_distance_threshold']:
                    min_distance = dist
                    matched_id = obj_id

        if matched_id is not None:
            tracked = self.tracked_objects[matched_id]
            # Check motion history
            if len(tracked.motion_history) > 5:
                positions = list(tracked.motion_history)
                max_movement = 0
                for i in range(1, len(positions)):
                    dist = np.sqrt((positions[i][0] - positions[i-1][0])**2 +
                                 (positions[i][1] - positions[i-1][1])**2)
                    max_movement = max(max_movement, dist)

                return max_movement < self.config['fixture_motion_threshold']

        return False

    def _update_tracking(self, classified_objects: List[Dict]):
        """Update tracking information for classified objects."""
        # Match detected objects with existing tracked objects
        matched_objects = set()

        for obj in classified_objects:
            center = obj['center']
            obj_type = obj['type']

            # Find closest existing tracked object of same type
            min_distance = float('inf')
            matched_id = None

            for obj_id, tracked in self.tracked_objects.items():
                if tracked.object_type == obj_type or tracked.object_type == ObjectType.UNKNOWN:
                    # Use Kalman filter prediction if available
                    predicted_pos = self._predict_position(obj_id)
                    if predicted_pos is not None:
                        dist = np.sqrt((center[0] - predicted_pos[0])**2 +
                                     (center[1] - predicted_pos[1])**2)
                    else:
                        dist = np.sqrt((center[0] - tracked.center[0])**2 +
                                     (center[1] - tracked.center[1])**2)

                    if dist < min_distance and dist < self.config['max_distance_threshold']:
                        min_distance = dist
                        matched_id = obj_id

            if matched_id is not None:
                # Update existing object
                tracked = self.tracked_objects[matched_id]
                tracked.update_position(obj['bbox'], self.frame_count)
                tracked.color_histogram = obj['histogram']
                tracked.confidence = obj['confidence']
                if tracked.object_type == ObjectType.UNKNOWN:
                    tracked.object_type = obj_type
                matched_objects.add(matched_id)

                # Update Kalman filter
                self._update_kalman_filter(matched_id, center)
            else:
                # Create new tracked object
                new_obj = TrackedObject(
                    id=self.next_object_id,
                    object_type=obj_type,
                    bbox=obj['bbox'],
                    center=center,
                    area=obj['area'],
                    color_histogram=obj['histogram'],
                    confidence=obj['confidence'],
                    first_seen_frame=self.frame_count,
                    last_seen_frame=self.frame_count
                )
                self.tracked_objects[self.next_object_id] = new_obj

                # Initialize Kalman filter for new object
                self._init_kalman_filter(self.next_object_id, center)

                self.next_object_id += 1

        # Remove objects that haven't been seen recently
        objects_to_remove = []
        for obj_id, tracked in self.tracked_objects.items():
            if obj_id not in matched_objects:
                if self.frame_count - tracked.last_seen_frame > self.config['dut_persistence_frames']:
                    objects_to_remove.append(obj_id)

        for obj_id in objects_to_remove:
            del self.tracked_objects[obj_id]
            if obj_id in self.kalman_filters:
                del self.kalman_filters[obj_id]

    def _init_kalman_filter(self, obj_id: int, center: Tuple[int, int]):
        """Initialize Kalman filter for object tracking."""
        kf = cv2.KalmanFilter(4, 2)
        kf.measurementMatrix = np.array([[1, 0, 0, 0],
                                        [0, 1, 0, 0]], np.float32)
        kf.transitionMatrix = np.array([[1, 0, 1, 0],
                                       [0, 1, 0, 1],
                                       [0, 0, 1, 0],
                                       [0, 0, 0, 1]], np.float32)
        kf.processNoiseCov = 0.03 * np.eye(4, dtype=np.float32)

        # Initialize state
        kf.statePre = np.array([center[0], center[1], 0, 0], dtype=np.float32)
        kf.statePost = np.array([center[0], center[1], 0, 0], dtype=np.float32)

        self.kalman_filters[obj_id] = kf

    def _predict_position(self, obj_id: int) -> Optional[Tuple[int, int]]:
        """Predict object position using Kalman filter."""
        if obj_id in self.kalman_filters:
            kf = self.kalman_filters[obj_id]
            prediction = kf.predict()
            return (int(prediction[0]), int(prediction[1]))
        return None

    def _update_kalman_filter(self, obj_id: int, center: Tuple[int, int]):
        """Update Kalman filter with measurement."""
        if obj_id in self.kalman_filters:
            kf = self.kalman_filters[obj_id]
            measurement = np.array([[center[0]], [center[1]]], dtype=np.float32)
            kf.correct(measurement)

    def draw_tracked_objects(self, frame: np.ndarray, objects: List[TrackedObject]) -> np.ndarray:
        """Draw bounding boxes and labels for tracked objects."""
        result_frame = frame.copy()

        # Define colors for different object types
        colors = {
            ObjectType.DUT: (0, 255, 0),  # Green for DUT
            ObjectType.LEFT_HAND: (255, 0, 0),  # Blue for left hand
            ObjectType.RIGHT_HAND: (0, 0, 255),  # Red for right hand
            ObjectType.CONVEYOR: (255, 255, 0),  # Cyan for conveyor
            ObjectType.FIXTURE: (128, 0, 128),  # Purple for fixture
            ObjectType.UNKNOWN: (128, 128, 128)  # Gray for unknown
        }

        for obj in objects:
            color = colors.get(obj.object_type, (128, 128, 128))
            x, y, w, h = obj.bbox

            # Draw bounding box
            cv2.rectangle(result_frame, (x, y), (x + w, y + h), color, 2)

            # Draw label with confidence
            label = f"{obj.object_type.value} #{obj.id} ({obj.confidence:.2f})"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)

            # Draw label background
            cv2.rectangle(result_frame, (x, y - label_size[1] - 4),
                        (x + label_size[0], y), color, -1)

            # Draw label text
            cv2.putText(result_frame, label, (x, y - 2),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

            # Draw center point
            cv2.circle(result_frame, obj.center, 3, color, -1)

            # Draw motion trail
            if len(obj.motion_history) > 1:
                points = list(obj.motion_history)
                for i in range(1, len(points)):
                    cv2.line(result_frame, points[i-1], points[i], color, 1)

        # Draw statistics
        stats_text = f"Tracked Objects: {len(objects)}"
        cv2.putText(result_frame, stats_text, (10, 30),
                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Draw object counts by type
        type_counts = {}
        for obj in objects:
            type_counts[obj.object_type] = type_counts.get(obj.object_type, 0) + 1

        y_offset = 60
        for obj_type, count in type_counts.items():
            color = colors.get(obj_type, (128, 128, 128))
            text = f"{obj_type.value}: {count}"
            cv2.putText(result_frame, text, (10, y_offset),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            y_offset += 25

        return result_frame

    def get_object_statistics(self) -> Dict:
        """Get statistics about tracked objects."""
        stats = {
            'total_objects': len(self.tracked_objects),
            'frame_count': self.frame_count,
            'objects_by_type': {},
            'average_confidence': 0.0
        }

        total_confidence = 0.0
        for obj in self.tracked_objects.values():
            obj_type = obj.object_type.value
            stats['objects_by_type'][obj_type] = stats['objects_by_type'].get(obj_type, 0) + 1
            total_confidence += obj.confidence

        if stats['total_objects'] > 0:
            stats['average_confidence'] = total_confidence / stats['total_objects']

        return stats