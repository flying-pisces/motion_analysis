# Object Tracking and Classification Features

The motion analysis software has been enhanced to distinguish and track different objects in factory floor videos, specifically focusing on identifying the DUT (Device Under Test) versus the objects that handle/manipulate it.

## Object Types Detected

### 1. DUT (Device Under Test) - Green 🟢
- **Purpose**: The main object being manipulated, processed, or assembled
- **Detection Method**: Medium-sized moving objects with consistent color/shape
- **Visual Marker**: Green bounding box with thick border
- **Typical Characteristics**: 1000-10000 pixel area, consistent appearance

### 2. Left Hand - Blue 🔵
- **Purpose**: Operator's left hand performing manipulations
- **Detection Method**: Skin color detection + position analysis (left side of frame)
- **Visual Marker**: Blue bounding box
- **Typical Characteristics**: Skin tone color, moderate movement patterns

### 3. Right Hand - Red 🔴
- **Purpose**: Operator's right hand performing manipulations
- **Detection Method**: Skin color detection + position analysis (right side of frame)
- **Visual Marker**: Red bounding box
- **Typical Characteristics**: Skin tone color, moderate movement patterns

### 4. Conveyor Belt - Yellow 🟡
- **Purpose**: Automated transport system moving objects
- **Detection Method**: Large objects in bottom 30% of frame with horizontal motion
- **Visual Marker**: Yellow/cyan bounding box
- **Typical Characteristics**: Large area (>5000 pixels), bottom positioning

### 5. Fixture - Purple 🟣
- **Purpose**: Stationary equipment that holds/processes the DUT
- **Detection Method**: Large, relatively stationary objects
- **Visual Marker**: Purple bounding box
- **Typical Characteristics**: Large area (>10000 pixels), minimal movement

## New Features Added

### 1. Object Tracker Module (`src/object_tracker.py`)
- **Advanced tracking**: Uses Kalman filters for motion prediction
- **Color-based detection**: Implements skin detection for hands
- **Multi-object tracking**: Tracks multiple objects simultaneously with unique IDs
- **Confidence scoring**: Assigns confidence levels to each detection

### 2. Enhanced Video Analyzer (`src/video_analyzer.py`)
- **Integrated tracking**: Option to enable object tracking during analysis
- **Object-aware motion events**: Associates motion with specific object types
- **Enhanced action code**: Generates code based on object interactions
- **Export options**: Save tracked video with visual overlays

### 3. New GUI Components

#### Object Tracking Tab
- **Real-time preview**: Shows live object detection and tracking
- **Interactive controls**: Play/pause, seek, toggle tracking
- **Object statistics**: Live counts and confidence metrics
- **Export functions**: Save tracked videos and data

#### Enhanced Main Tab
- **Dual analysis modes**: Standard analysis + object tracking analysis
- **Tracking summary**: Shows detected object types and statistics
- **Visual feedback**: Color-coded object information

### 4. Tracked Video Preview Widget (`src/tracked_video_preview.py`)
- **Multi-panel interface**: Video + tracking information side-by-side
- **Real-time overlays**: Bounding boxes, labels, trajectories
- **Interactive options**: Toggle trajectories, labels, confidence display
- **Active object list**: TreeView showing currently tracked objects

## Usage Instructions

### Basic Object Tracking
1. **Launch Application**: `python main.py`
2. **Navigate to Object Tracking Tab**
3. **Load Video**: Click "Browse" and select your factory floor video
4. **Enable Tracking**: Click "🎯 Enable Tracking" button
5. **View Results**: See real-time object detection with color-coded boxes

### Analysis with Object Tracking
1. **Main Tab**: Load video in the main analysis tab
2. **Enhanced Analysis**: Click "Analyze with Object Tracking"
3. **Review Results**: See motion events associated with specific object types
4. **Export**: Save enhanced action code and tracking data

### Export Options
- **Tracked Video**: Export video file with object detection overlays
- **Tracking Data**: Export JSON file with object positions and statistics
- **Action Code**: Enhanced pseudocode with object-specific actions

## Technical Implementation

### Detection Pipeline
1. **Background Subtraction**: MOG2 algorithm for motion detection
2. **Skin Detection**: YCrCb color space analysis for hand detection
3. **Contour Analysis**: Shape and size filtering for object classification
4. **Kalman Filtering**: Motion prediction and smooth tracking
5. **Object Association**: Match detections across frames using distance/appearance

### Configuration Options
```json
{
  "enable_object_tracking": true,
  "save_tracked_video": false,
  "min_object_area": 500,
  "max_object_area": 50000,
  "hand_detection_threshold": 0.6,
  "conveyor_y_position_ratio": 0.7,
  "fixture_motion_threshold": 5
}
```

### Generated Action Code Examples

#### Without Object Tracking
```
LOOP forever:
    WHILE input_box has adapters:
        MOVE adapters from input_box TO press_bed
        LEFT_HAND load 1 adapter INTO stamping_press
        RIGHT_HAND press press_button
```

#### With Object Tracking
```
# Motion Analysis with Object Tracking
# Detected Objects: {'DUT': 3, 'Left Hand': 1, 'Right Hand': 1}

LOOP forever:
    # DUT (Device Under Test) Operations
    WHILE DUT present in workspace:
        # Two-handed manipulation detected
        LEFT_HAND position DUT for processing
        RIGHT_HAND perform operation on DUT
        IF DUT processing complete:
            MOVE DUT TO output_area
```

## Benefits of Object Tracking

### 1. **Precision**:
- Distinguish between the object being worked on (DUT) vs. the tools/hands doing the work
- More accurate motion event classification

### 2. **Context Awareness**:
- Understand which object is performing actions vs. being acted upon
- Generate more meaningful action descriptions

### 3. **Quality Control**:
- Identify when hands interact with DUT
- Track DUT movement through the workflow
- Detect fixture usage patterns

### 4. **Training Enhancement**:
- Visual overlays help trainees identify key objects
- Color-coded system makes it easy to follow object interactions
- Motion trails show movement patterns

## Testing

Run the test suite to verify object tracking functionality:

```bash
python test_object_tracking.py
```

This will test:
- Object type enumeration
- Basic object detection
- Motion analyzer integration
- Video processing pipeline

## Future Enhancements

Potential improvements for the object tracking system:
1. **Machine Learning**: Train custom models for factory-specific objects
2. **3D Tracking**: Add depth information for better spatial understanding
3. **Multi-Camera**: Support for multiple camera angles
4. **Quality Metrics**: Automated assessment of operation quality
5. **Real-time Alerts**: Notifications for unusual object interactions