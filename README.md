# Motion Analysis and Video Assembly Tool

A comprehensive solution for analyzing factory floor videos and generating training materials with precise motion tracking and action code generation.

## 🌐 Live Demos

| Platform | URL | Features |
|----------|-----|----------|
| **GitLab Pages** | https://chuck.yin.gitlab.io/motion_analysis_dfm/ | CI/CD deployment, staging environment |
| **GitHub Pages** | https://flying-pisces.github.io/motion_analysis/ | Mirror deployment |

## 🏗 Project Architecture

This repository serves **multiple deployment platforms** from a single codebase:

### 📱 Platform Deployments

- **Web Application**: Browser-based interface with video preview and modal training player
- **Desktop Application**: Full-featured Python/Tkinter app with advanced processing
- **Multi-Platform CI/CD**: Automated deployment to both GitLab and GitHub Pages

### 🔄 Git Remotes

```bash
# GitLab (Primary development)
gitlab    git@gitlab.com:chuck.yin/motion_analysis_dfm.git

# GitHub (Public mirror)
origin    git@github.com:flying-pisces/motion_analysis.git
```

## 🚀 Quick Start

### 🌐 Web Application (Recommended)
Visit either deployment:
- **GitLab**: https://chuck.yin.gitlab.io/motion_analysis_dfm/
- **GitHub**: https://flying-pisces.github.io/motion_analysis/

### 💻 Desktop Application
```bash
cd motion_analyzer
pip install -r requirements.txt
python main.py
```

## 📋 Features

### 🎥 Video Processing
- **Upload Support**: MP4, AVI, MOV, MKV, WMV, FLV
- **Interactive Preview**: Click to play/pause, drag progress bar to seek
- **Real-time Clock**: Sub-second accuracy timing display
- **Auto-loop Playback**: Continuous video review

### 🔍 Motion Analysis
- **Pattern Recognition**: Automated motion event detection
- **Timestamped Output**: Precise action code with timing
- **Progressive Display**: Synchronized text highlighting during playback
- **Export Options**: Save analysis results to file

### 🎬 Training Video Assembly
- **Modal Player**: Immersive full-screen preview experience
- **Side-by-side Layout**: Video + synchronized action code
- **Real-time Highlighting**: Active line tracking during playback
- **Professional Controls**: Play/pause, seek, restart functionality

### 🛠 Utilities
- **Video Splitting**: Extract components from training videos
- **Configuration**: Customizable analysis and assembly settings
- **Multi-format Support**: Comprehensive video format compatibility

## 📁 Project Structure

```
motion_analysis_dfm/
├── deployment/
│   ├── github-pages/       # GitHub Pages deployment
│   │   ├── index.html
│   │   ├── styles.css
│   │   └── script.js
│   └── gitlab-pages/       # GitLab Pages deployment
│       ├── index.html
│       ├── styles.css
│       ├── script.js
│       └── README_GITLAB.md
├── motion_analyzer/        # Desktop application
│   ├── main.py            # Application entry point
│   ├── src/               # Source code modules
│   │   ├── gui_app.py     # Enhanced GUI with progress bar
│   │   ├── video_analyzer.py    # Motion analysis engine
│   │   ├── video_assembler.py   # Video assembly tools
│   │   └── training_video_player.py  # Training video player
│   ├── config/            # Configuration files
│   │   ├── analysis_config.json
│   │   └── assembly_config.json
│   ├── data/              # Example videos and data
│   │   ├── input/         # Sample videos
│   │   └── output/        # Generated results
│   ├── requirements.txt   # Python dependencies
│   └── test_app.py       # Test utilities
├── docs/                  # Documentation
│   └── DEPLOYMENT.md      # Deployment guide
├── .gitlab-ci.yml        # GitLab CI/CD configuration
├── index.html            # Root web files (deployed copies)
├── styles.css
├── script.js
└── README.md             # This file
```

## 🛠 Development Workflow

### Branch Strategy
- **`main`**: Production releases (auto-deploys to both platforms)
- **`develop`**: Development branch (deploys to GitLab staging)
- **`gh-pages`**: GitHub Pages deployment branch
- **`feature/*`**: Feature development branches

### Local Development
```bash
# Clone repository
git clone git@gitlab.com:chuck.yin/motion_analysis_dfm.git
cd motion_analysis_dfm

# Web development
cd deployment/gitlab-pages
python -m http.server 8000

# Desktop development
cd motion_analyzer
python main.py
```

### Deployment Process
1. **Development**: Work in `feature/` branches
2. **Integration**: Merge to `develop` for staging testing
3. **Release**: Merge to `main` for production deployment
4. **Cross-platform**: Changes sync to both GitLab and GitHub

## 🏭 Installation & Usage

### Prerequisites
- **Web**: Modern browser with HTML5 video support
- **Desktop**: Python 3.8+, FFmpeg

### Desktop Installation
```bash
cd motion_analyzer
pip install -r requirements.txt

# Install FFmpeg
# macOS: brew install ffmpeg
# Windows: Download from https://ffmpeg.org/
# Linux: sudo apt install ffmpeg

python main.py
```

### Desktop Application Features
1. **Video Analysis Tab**: Upload and analyze factory floor videos
2. **Video Assembly Tab**: Combine raw footage with generated code
3. **Utilities Tab**: Video splitting, configuration, batch processing

### Web Application Features
1. **Interactive Video Preview**: Built-in progress bar with seeking
2. **Modal Training Player**: Immersive full-screen experience
3. **Real-time Synchronization**: Action code highlighting with video
4. **Responsive Design**: Works on desktop, tablet, and mobile

## 🎯 Workflow Examples

### 1. Web Application Workflow
1. **Upload Video**: Drag & drop or browse for factory floor video
2. **Preview**: Use progress bar to review content
3. **Analyze**: Click "Analyze Video" to generate timestamped action code
4. **Training Preview**: Click "Generate & Preview Training Video"
5. **Experience**: Watch synchronized highlighting in modal player

### 2. Desktop Application Workflow
1. **Analysis**: Load video → Configure parameters → Analyze motion
2. **Review**: Examine generated pseudocode and motion events
3. **Assembly**: Combine raw video with action code → Create training video
4. **Export**: Save training materials in various formats

### 3. Example Use Cases
- **Manufacturing Training**: Assembly line operation documentation
- **Quality Control**: Standard procedure capture and codification
- **Process Documentation**: Manual process analysis and training content
- **Training Content**: Consistent materials for new employee onboarding

## 📊 Technology Stack

### Web Application
- **Frontend**: Vanilla HTML5, CSS3, JavaScript (ES6+)
- **Video**: HTML5 Video API with custom controls
- **Styling**: Modern CSS with Flexbox/Grid
- **Deployment**: GitLab CI/CD, GitHub Pages

### Desktop Application
- **Language**: Python 3.8+
- **GUI Framework**: Tkinter with custom widgets (including progress bar)
- **Video Processing**: OpenCV (cv2)
- **Image Handling**: PIL (Pillow)

### CI/CD Pipeline
- **GitLab CI**: Automated testing and deployment
- **Build Validation**: HTML/CSS/JS validation
- **Multi-environment**: Production and staging deployments

## 🔧 Configuration

### Analysis Settings (Desktop)
```json
{
  "motion_threshold": 0.01,
  "min_contour_area": 500,
  "frame_skip": 5,
  "output_format": "json",
  "enable_visualization": true
}
```

### Assembly Settings (Desktop)
```json
{
  "layout": "side_by_side",
  "code_position": "right",
  "code_width_ratio": 0.3,
  "font_size": 14,
  "font_color": "#00FF00",
  "background_color": "#000000"
}
```

## 🚀 Advanced Features

### Web Application Highlights
- **Progress Bar Integration**: Interactive video seeking with time display
- **Modal Training Player**: Immersive side-by-side video + code experience
- **Real-time Highlighting**: Active line tracking during video playback
- **Responsive Design**: Seamless experience across devices
- **No Backend Required**: Pure browser-based solution

### Desktop Application Highlights
- **Computer Vision**: OpenCV-based motion detection
- **Configurable Analysis**: Adjustable parameters for different scenarios
- **Batch Processing**: Process multiple videos programmatically
- **Export Options**: Various output formats and quality settings

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Commit** changes: `git commit -m 'Add amazing feature'`
4. **Push** to branch: `git push origin feature/amazing-feature`
5. **Submit** a Pull Request (GitHub) or Merge Request (GitLab)

## 📊 Pipeline Status

[![GitLab Pipeline](https://gitlab.com/chuck.yin/motion_analysis_dfm/badges/main/pipeline.svg)](https://gitlab.com/chuck.yin/motion_analysis_dfm/-/commits/main)

## 🔗 Links

- **GitLab Repository**: https://gitlab.com/chuck.yin/motion_analysis_dfm
- **GitHub Mirror**: https://github.com/flying-pisces/motion_analysis
- **GitLab Pages**: https://chuck.yin.gitlab.io/motion_analysis_dfm/
- **GitHub Pages**: https://flying-pisces.github.io/motion_analysis/
- **Documentation**: See `docs/` directory for detailed guides

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🎯 Future Enhancements

- [ ] Machine learning-based motion classification
- [ ] Multi-camera support and synchronization
- [ ] Real-time processing capabilities
- [ ] Progressive Web App (PWA) features
- [ ] Integration with manufacturing systems
- [ ] Automated quality assessment tools