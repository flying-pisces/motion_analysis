# Downloaded Training Videos

## Manufacturing Assembly Operations.mp4
- **Source**: YouTube (https://www.youtube.com/watch?v=uqidiUvm5-E)
- **File Size**: 48 MB
- **Duration**: 2:10 (130 seconds)
- **Resolution**: 1080p
- **Format**: MP4 (H.264 video + AAC audio)
- **Downloaded**: 2025-09-14

### Content Description
This video appears to contain manufacturing assembly operations suitable for motion analysis training.

### Recommended Analysis Workflow

1. **Load in Desktop Application**:
   ```bash
   cd motion_analyzer
   python main.py
   ```
   - Browse and select "Manufacturing Assembly Operations.mp4"
   - The progress bar will allow you to preview different sections

2. **Run Motion Analysis**:
   - Click "Analyze Video" to detect motion patterns
   - The tool will generate timestamped action code
   - Review the detected motion events and action descriptions

3. **Create Training Video**:
   - Click "Generate & Preview Training Video"
   - The modal player will show:
     - Left: Original video with controls
     - Right: Synchronized action code with highlighting
   - Use the progress bar to seek to specific moments

4. **Export Results**:
   - Save the generated action code
   - Export the assembled training video
   - Use for training documentation

### Other Available Training Videos
- `human_operation_only.mp4` (9.1 MB) - Factory floor operations
- `twitter_video.mp4` (8.1 MB) - Example training video with code overlay
- `second_training_video.mp4` (1.3 MB) - Additional training sample
- `third_training_video.mp4` (3.8 MB) - Additional training sample

### Web Application Testing
You can also test the web version with these videos:
1. Visit: https://flying-pisces.github.io/motion_analysis/
2. Upload the video file
3. Use the interactive progress bar to preview
4. Run analysis and view synchronized results

### Notes
- The video has been optimized for web playback (H.264/AAC)
- Compatible with both desktop and web applications
- Suitable for motion analysis and action code generation