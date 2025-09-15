// Video Preview Controller
class VideoController {
    constructor() {
        this.video = document.getElementById('videoPlayer');
        this.progressBar = document.getElementById('progressBar');
        this.timeDisplay = document.getElementById('timeDisplay');
        this.clockDisplay = document.getElementById('clockDisplay');
        this.placeholder = document.getElementById('videoPlaceholder');
        this.analyzeBtn = document.getElementById('analyzeBtn');
        this.isPlaying = false;
        this.isDragging = false;

        this.setupEventListeners();
    }

    setupEventListeners() {
        // Video file input
        document.getElementById('videoFile').addEventListener('change', (e) => this.handleFileSelect(e));

        // Video controls
        this.video.addEventListener('click', () => this.togglePlayPause());
        this.video.addEventListener('loadedmetadata', () => this.onVideoLoaded());
        this.video.addEventListener('timeupdate', () => this.updateProgress());
        this.video.addEventListener('ended', () => this.handleVideoEnd());

        // Progress bar controls
        this.progressBar.addEventListener('mousedown', () => this.isDragging = true);
        this.progressBar.addEventListener('mouseup', () => this.isDragging = false);
        this.progressBar.addEventListener('input', (e) => this.handleSeek(e));
    }

    handleFileSelect(event) {
        const file = event.target.files[0];
        if (file && file.type.startsWith('video/')) {
            const url = URL.createObjectURL(file);
            this.video.src = url;
            this.video.style.display = 'block';
            this.placeholder.style.display = 'none';

            // Update file path display
            document.getElementById('videoPath').value = file.name;

            // Enable analyze button
            this.analyzeBtn.disabled = false;
            document.getElementById('analysisStatus').textContent = 'Video loaded - Ready to analyze';
        }
    }

    onVideoLoaded() {
        this.updateTimeDisplay();
        this.progressBar.max = this.video.duration;

        // Auto-play on load
        this.play();
    }

    togglePlayPause() {
        if (this.isPlaying) {
            this.pause();
        } else {
            this.play();
        }
    }

    play() {
        this.video.play();
        this.isPlaying = true;
    }

    pause() {
        this.video.pause();
        this.isPlaying = false;
    }

    handleSeek(event) {
        if (this.isDragging) {
            const time = parseFloat(event.target.value);
            this.video.currentTime = time;
            this.updateTimeDisplay();
        }
    }

    updateProgress() {
        if (!this.isDragging) {
            this.progressBar.value = this.video.currentTime;
            this.updateTimeDisplay();
            this.updateClock();
        }
    }

    updateTimeDisplay() {
        const current = this.formatTime(this.video.currentTime);
        const total = this.formatTime(this.video.duration);
        this.timeDisplay.textContent = `${current} / ${total}`;
    }

    updateClock() {
        const time = this.video.currentTime || 0;
        this.clockDisplay.textContent = `${time.toFixed(1)}s`;
    }

    formatTime(seconds) {
        if (isNaN(seconds)) return '0:00';
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    handleVideoEnd() {
        // Loop video
        this.video.currentTime = 0;
        this.play();
    }
}

// Analysis Module
class AnalysisModule {
    constructor() {
        this.analyzeBtn = document.getElementById('analyzeBtn');
        this.assembleBtn = document.getElementById('assembleBtn');
        this.resultsText = document.getElementById('resultsText');
        this.analysisResults = null;
        this.timestampedLines = [];

        this.setupEventListeners();
    }

    setupEventListeners() {
        this.analyzeBtn.addEventListener('click', () => this.startAnalysis());
        this.assembleBtn.addEventListener('click', () => this.startAssembly());
    }

    startAnalysis() {
        const videoFile = document.getElementById('videoFile').files[0];
        if (!videoFile) {
            alert('Please select a video file first.');
            return;
        }

        this.analyzeBtn.disabled = true;
        document.getElementById('analysisStatus').textContent = 'Analyzing video...';

        // Simulate analysis (in real implementation, this would call a backend API)
        setTimeout(() => {
            this.simulateAnalysisResults();
        }, 2000);
    }

    simulateAnalysisResults() {
        // Generate sample timestamped action code
        const actionCode = `[000.0s] LOOP forever:
[003.0s]     WHILE input_box has adapters:
[006.0s]         MOVE adapters from input_box TO press_bed
[009.0s]         IF stamping_press already contains a stamped adapter:
[012.0s]             RIGHT_HAND grab stamped adapter
[015.0s]             IF right_hand holds 2 stamped adapters:
[018.0s]                 PLACE 2 stamped adapters INTO output_box
[021.0s]         WHILE press_bed has adapters:
[024.0s]             LEFT_HAND load 1 adapter INTO stamping_press
[027.0s]             RIGHT_HAND press press_button
[030.0s]             LEFT_HAND grab next unstamped adapter
[033.0s]             WAIT until stamping_press completes

Analysis Summary:
=====================================
Motion Events Detected: 12
Analysis Time: 2.1 seconds
Output File: analysis_output.txt`;

        this.resultsText.value = actionCode;
        this.analysisResults = { actionCode };

        // Show video info
        this.showVideoInfo();

        // Update status
        this.analyzeBtn.disabled = false;
        document.getElementById('analysisStatus').textContent = 'Analysis complete';

        // Enable assembly
        this.assembleBtn.disabled = false;
        document.getElementById('assemblyStatus').textContent = 'Ready to generate training video preview';
    }

    showVideoInfo() {
        const video = document.getElementById('videoPlayer');
        const videoFile = document.getElementById('videoFile').files[0];

        if (videoFile && video.duration) {
            const info = `File: ${videoFile.name}
Dimensions: ${video.videoWidth} x ${video.videoHeight} pixels
Duration: ${video.duration.toFixed(1)} seconds
Frame Rate: 30.0 fps
Total Frames: ${Math.floor(video.duration * 30).toLocaleString()}
Analysis Completed: ${new Date().toLocaleString()}`;

            document.getElementById('videoInfo').textContent = info;
            document.getElementById('videoInfoPanel').style.display = 'block';
        }
    }

    startAssembly() {
        if (!this.analysisResults) {
            alert('Please complete video analysis first.');
            return;
        }

        this.assembleBtn.disabled = true;
        document.getElementById('assemblyStatus').textContent = 'Assembling training video...';

        // Simulate assembly
        setTimeout(() => {
            this.assembleBtn.disabled = false;
            document.getElementById('assemblyStatus').textContent = 'Assembly complete - Training video ready';
            alert('Training video assembled successfully! (In production, this would open a video player)');
        }, 2000);
    }
}

// Utilities Module
class UtilitiesModule {
    constructor() {
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Split video file input
        document.getElementById('splitVideoFile').addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                document.getElementById('splitVideoPath').value = file.name;
            }
        });

        // Player video file input
        document.getElementById('playerVideoFile').addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                document.getElementById('playerVideoPath').value = file.name;
            }
        });
    }
}

// Global Functions
function saveActionCode() {
    const content = document.getElementById('resultsText').value;
    if (!content) {
        alert('No analysis results to save.');
        return;
    }

    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'action_code.txt';
    a.click();
    URL.revokeObjectURL(url);
}

function clearResults() {
    document.getElementById('resultsText').value = '';
    document.getElementById('videoInfoPanel').style.display = 'none';
    document.getElementById('assembleBtn').disabled = true;
    document.getElementById('assemblyStatus').textContent = 'Complete analysis first';
}

function splitTrainingVideo() {
    const file = document.getElementById('splitVideoFile').files[0];
    if (!file) {
        alert('Please select a training video to split.');
        return;
    }
    alert('Video splitting functionality would be implemented with backend API.');
}

function openTrainingVideoPlayer() {
    const file = document.getElementById('playerVideoFile').files[0];
    if (!file) {
        alert('Please select a training video first.');
        return;
    }
    alert('Training video player would open in a new window/modal.');
}

function editAnalysisConfig() {
    const modal = document.getElementById('configModal');
    const title = document.getElementById('configTitle');
    const content = document.getElementById('configContent');

    title.textContent = 'Analysis Configuration';
    content.value = JSON.stringify({
        "motion_threshold": 0.01,
        "min_contour_area": 500,
        "frame_skip": 5,
        "output_format": "json",
        "enable_visualization": true
    }, null, 2);

    modal.style.display = 'block';
}

function editAssemblyConfig() {
    const modal = document.getElementById('configModal');
    const title = document.getElementById('configTitle');
    const content = document.getElementById('configContent');

    title.textContent = 'Assembly Configuration';
    content.value = JSON.stringify({
        "layout": "side_by_side",
        "code_position": "right",
        "code_width_ratio": 0.3,
        "font_size": 14,
        "font_color": "#00FF00",
        "background_color": "#000000"
    }, null, 2);

    modal.style.display = 'block';
}

function saveConfig() {
    const content = document.getElementById('configContent').value;
    try {
        JSON.parse(content);
        alert('Configuration saved successfully!');
        closeConfigModal();
    } catch (e) {
        alert('Invalid JSON format. Please check your configuration.');
    }
}

function closeConfigModal() {
    document.getElementById('configModal').style.display = 'none';
}

// Update status message
function updateStatus(message) {
    document.getElementById('statusMessage').textContent = message;
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    const videoController = new VideoController();
    const analysisModule = new AnalysisModule();
    const utilitiesModule = new UtilitiesModule();

    // Clock update timer
    setInterval(() => {
        videoController.updateClock();
    }, 100);

    // Close modal when clicking outside
    window.onclick = function(event) {
        const modal = document.getElementById('configModal');
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    }

    updateStatus('Ready');
});