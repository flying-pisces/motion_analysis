#!/usr/bin/env python3
"""
Test script for object tracking functionality
Tests the new object detection and tracking features
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.object_tracker import ObjectTracker, ObjectType
from src.video_analyzer import MotionAnalyzer
import cv2
import numpy as np


def test_object_tracker():
    """Test the object tracker with a simple synthetic video."""
    print("Testing Object Tracker...")

    # Create a simple test video frame
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    # Add some colored rectangles to simulate objects
    # DUT (green rectangle in center)
    cv2.rectangle(frame, (250, 200), (350, 280), (0, 255, 0), -1)

    # Hand (skin color rectangle on left)
    cv2.rectangle(frame, (100, 150), (180, 220), (139, 169, 219), -1)

    # Conveyor (yellow rectangle at bottom)
    cv2.rectangle(frame, (0, 400), (640, 480), (0, 255, 255), -1)

    # Initialize tracker
    tracker = ObjectTracker()

    # Process the frame
    tracked_objects = tracker.process_frame(frame)

    print(f"Detected {len(tracked_objects)} objects:")
    for obj in tracked_objects:
        print(f"  - {obj.object_type.value} (ID: {obj.id}, Confidence: {obj.confidence:.2f})")

    # Draw tracked objects
    annotated_frame = tracker.draw_tracked_objects(frame, tracked_objects)

    # Save test result
    cv2.imwrite('test_tracking_result.jpg', annotated_frame)
    print("Test result saved as 'test_tracking_result.jpg'")


def test_motion_analyzer_with_tracking():
    """Test the motion analyzer with tracking enabled."""
    print("\nTesting Motion Analyzer with Object Tracking...")

    # Check if test video exists
    test_videos = [
        'data/input/Manufacturing Assembly Operations.mp4',
        'data/input/human_operation_only.mp4',
        'data/input/twitter_video.mp4'
    ]

    test_video = None
    for video_path in test_videos:
        if os.path.exists(video_path):
            test_video = video_path
            break

    if test_video is None:
        print("No test video found. Skipping video analysis test.")
        return

    print(f"Using test video: {test_video}")

    # Initialize analyzer with tracking enabled
    analyzer = MotionAnalyzer()
    analyzer.enable_object_tracking = True
    analyzer.config['save_tracked_video'] = True

    try:
        # Run analysis
        output_dir = "test_output"
        os.makedirs(output_dir, exist_ok=True)

        action_code, metadata = analyzer.analyze_video(test_video, output_dir)

        print("Analysis completed successfully!")
        print(f"Motion events detected: {metadata.get('motion_events', 0)}")
        print(f"Object tracking enabled: {metadata.get('object_tracking_enabled', False)}")

        if 'tracked_objects' in metadata:
            tracking_stats = metadata['tracked_objects']
            print(f"Tracking statistics: {tracking_stats}")

        print(f"Output saved to: {metadata.get('output_file', 'Unknown')}")

    except Exception as e:
        print(f"Analysis failed: {str(e)}")


def test_object_types():
    """Test object type enumeration."""
    print("\nTesting Object Types...")

    for obj_type in ObjectType:
        print(f"  - {obj_type.name}: {obj_type.value}")


if __name__ == "__main__":
    print("=== Object Tracking Test Suite ===\n")

    test_object_types()
    test_object_tracker()
    test_motion_analyzer_with_tracking()

    print("\n=== Test Suite Complete ===")
    print("\nTo run the full application with object tracking:")
    print("1. python main.py")
    print("2. Go to 'Object Tracking' tab")
    print("3. Load a video and click 'Enable Tracking'")
    print("4. Or use 'Analyze with Object Tracking' in the main tab")