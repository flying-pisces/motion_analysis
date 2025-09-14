# Motion Analysis and Video Assembly Tool

A comprehensive tool for analyzing factory floor videos to extract motion patterns, generate action code descriptions, and create training videos with code overlays.

## Features

- **Video Analysis**: Computer vision-based motion detection and pattern recognition
- **Action Code Generation**: Automatic generation of structured pseudocode from motion patterns
- **Video Assembly**: Combine raw footage with generated code to create training materials
- **GUI Interface**: User-friendly Tkinter-based interface for all operations
- **Utilities**: Video splitting, configuration management, and batch processing
- **Extensible**: Configurable parameters and modular architecture

## Installation

### Prerequisites

- Python 3.8 or higher
- FFmpeg (for video processing)

### Install Dependencies

```bash
cd motion_analyzer
pip install -r requirements.txt
```

### Install FFmpeg

**macOS (using Homebrew):**
```bash
brew install ffmpeg
```

**Windows:**
Download from https://ffmpeg.org/download.html

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install ffmpeg
```

## Usage

### GUI Application

Launch the main GUI application:

```bash
python main.py
```

The application provides three main tabs:

1. **Video Analysis**: Upload factory floor videos and analyze motion patterns
2. **Video Assembly**: Combine raw videos with action code to create training materials
3. **Utilities**: Additional tools for video processing and configuration

### Command Line Usage

You can also use the modules programmatically:

```python
from src.video_analyzer import MotionAnalyzer
from src.video_assembler import VideoAssembler

# Analyze a video
analyzer = MotionAnalyzer()
action_code, metadata = analyzer.analyze_video('input_video.mp4', 'output_dir')

# Assemble training video
assembler = VideoAssembler()
result = assembler.assemble_training_video(
    'raw_video.mp4',
    'action_code.txt',
    'training_video.mp4'
)
```

## Project Structure

```
motion_analyzer/
├── src/
│   ├── gui_app.py           # Main GUI application
│   ├── video_analyzer.py    # Motion analysis module
│   └── video_assembler.py   # Video assembly module
├── config/
│   ├── analysis_config.json # Analysis parameters
│   └── assembly_config.json # Assembly parameters
├── data/
│   ├── input/              # Input videos and example files
│   │   ├── twitter_video.mp4        # Example training video (ground truth)
│   │   ├── human_operation_only.mp4 # Example factory floor video
│   │   └── code_from_video.txt      # Example generated action code
│   ├── output/             # Generated analysis and assembly results
│   └── models/             # Future ML model storage
├── tests/                  # Unit tests (future)
├── docs/                   # Additional documentation
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

### Video File Storage

- **Input Videos**: Store your factory floor videos in `data/input/`
- **Example Files**: The repository includes example videos and generated code:
  - `twitter_video.mp4`: Complete training video with human operation + code overlay
  - `human_operation_only.mp4`: Factory floor footage (human operations only)
  - `code_from_video.txt`: Generated action code from the analysis
- **Output Files**: Analysis results and assembled videos are saved in `data/output/`

### Supported Video Formats

The application supports the following video formats:
- **MP4** (recommended) - Best compatibility and quality
- **AVI** - Common format, good compatibility
- **MOV** - Apple QuickTime format
- **MKV** - Matroska format, supports multiple streams
- **WMV** - Windows Media Video
- **FLV** - Flash Video format

## Configuration

### Analysis Configuration

Edit `config/analysis_config.json` to customize motion detection:

- `motion_threshold`: Sensitivity for motion detection (lower = more sensitive)
- `contour_min_area`: Minimum area for motion regions
- `frame_skip`: Skip frames for performance (higher = faster but less accurate)
- `roi_top_ratio`: Focus area ratio (0.48 = top 48% of video)

### Assembly Configuration

Edit `config/assembly_config.json` to customize video assembly:

- `code_overlay_height_ratio`: Portion of video for code overlay
- `code_background_color`: Background color for code section [R, G, B]
- `code_text_color`: Text color for code [R, G, B]
- `code_font_size`: Font size for code text
- `output_fps`: Frame rate of assembled video
- `output_quality`: Video quality (18-28, lower is better)

## Workflow

### 1. Video Analysis

1. **Upload Video**: Select a factory floor video showing human operations
2. **Configure Analysis**: Adjust motion detection parameters if needed
3. **Analyze**: The tool will detect motion patterns and generate action code
4. **Review Results**: Examine the generated pseudocode and motion events
5. **Save**: Export the action code to a text file

### 2. Video Assembly

1. **Select Raw Video**: Choose the original factory floor video
2. **Select Action Code**: Use the generated code file from analysis
3. **Preview**: Review the code that will be overlaid
4. **Assemble**: Create the training video with code overlay
5. **Save**: Export the assembled training video

### 3. Training Video Format

The assembled training video has two sections:

- **Top Section**: Raw factory floor footage (human operations)
- **Bottom Section**: Generated action code with syntax highlighting

This format matches the original Twitter video structure, making it suitable for training purposes.

## Quick Start with Example Files

The repository includes example files to test the application:

1. **Test Analysis**:
   - Use `data/input/human_operation_only.mp4` as input
   - This will generate action code similar to `data/input/code_from_video.txt`

2. **Test Assembly**:
   - Raw video: `data/input/human_operation_only.mp4`
   - Action code: `data/input/code_from_video.txt`
   - This will create a training video similar to `data/input/twitter_video.mp4`

3. **Test Video Splitting**:
   - Use `data/input/twitter_video.mp4` to extract components
   - This demonstrates how to split existing training videos

## Advanced Features

### Batch Processing

For processing multiple videos, you can create scripts using the core modules:

```python
import os
from src.video_analyzer import MotionAnalyzer
from src.video_assembler import VideoAssembler

analyzer = MotionAnalyzer()
assembler = VideoAssembler()

# Process all videos in a directory
input_dir = "data/input"
for video_file in os.listdir(input_dir):
    if video_file.endswith('.mp4'):
        video_path = os.path.join(input_dir, video_file)

        # Analyze
        action_code, metadata = analyzer.analyze_video(video_path, "data/output")

        # Assemble
        output_path = f"data/output/training_{video_file}"
        assembler.assemble_training_video(
            video_path, metadata['output_file'], output_path
        )
```

### Custom Motion Classification

The motion classification can be customized by modifying the `_classify_motion` method in `video_analyzer.py`. The current implementation uses heuristic rules based on:

- Motion area size
- Duration
- Position in frame
- Event frequency

### Video Splitting

Use the utilities tab to split existing training videos back into their components:

1. Select a training video
2. Choose output directory
3. Extract raw video and code image

## Troubleshooting

### Common Issues

1. **FFmpeg not found**: Make sure FFmpeg is installed and in your PATH
2. **Video won't load**: Check that the video format is supported (MP4, AVI, MOV, MKV, WMV, FLV)
3. **Analysis takes too long**: Increase `frame_skip` in analysis configuration
4. **Poor motion detection**: Adjust `motion_threshold` and `contour_min_area`
5. **Assembly fails**: Check that both input files exist and are readable
6. **Unsupported codec**: If a video file won't load, try converting it to MP4 format using FFmpeg

### Performance Tips

- Use `frame_skip` parameter to speed up analysis
- Crop videos to focus on relevant areas before processing
- Use lower resolution videos for faster processing
- Adjust `roi_top_ratio` to focus on specific areas

## Development

### Adding New Features

The modular design makes it easy to extend functionality:

1. **New Analysis Methods**: Add to `video_analyzer.py`
2. **New Assembly Options**: Add to `video_assembler.py`
3. **GUI Enhancements**: Modify `gui_app.py`
4. **Configuration Options**: Update config JSON files

### Testing

Run the application with example data:

```bash
# The included example files can be used for testing
python main.py
```

Use the provided example videos in `data/input/` to test functionality.

## Example Use Cases

1. **Manufacturing Training**: Analyze assembly line operations and create training materials
2. **Quality Control**: Document standard procedures with visual and textual descriptions
3. **Process Documentation**: Capture and codify manual processes
4. **Training Content**: Create consistent training videos for new employees

## Future Enhancements

- Machine learning-based motion classification
- Multi-camera support
- Real-time processing
- Export to various formats
- Integration with manufacturing systems
- Automated quality assessment

## Support

For issues, questions, or contributions:

1. Check the troubleshooting section
2. Review configuration options
3. Examine example usage
4. Create issues for bugs or feature requests

## License

This project is provided as-is for educational and commercial use. Please ensure compliance with any relevant video processing and AI regulations in your jurisdiction.
