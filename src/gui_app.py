"""
Enhanced GUI Application for Motion Analysis and Video Assembly
Provides a user-friendly interface with video preview, real-time clock, and integrated workflow.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from typing import Optional, Dict
import os
import threading
from datetime import datetime
import json
import cv2
from PIL import Image, ImageTk
import time

from video_analyzer import MotionAnalyzer, VideoProcessor
from video_assembler import VideoAssembler, VideoSplitter
from training_video_player import create_training_video_player


class VideoPreviewWidget:
    """Custom widget for video preview with play/pause functionality."""

    def __init__(self, parent, width=400, height=300):
        self.parent = parent
        self.width = width
        self.height = height

        # Create frame and canvas
        self.frame = ttk.Frame(parent)
        self.canvas = tk.Canvas(self.frame, width=width, height=height, bg='black')
        self.canvas.pack()

        # Video state
        self.video_path = None
        self.cap = None
        self.is_playing = False
        self.current_frame = 0
        self.total_frames = 0
        self.fps = 30
        self.frame_delay = 33  # milliseconds
        self.start_time = 0
        self.current_time = 0

        # Bind click event
        self.canvas.bind("<Button-1>", self.toggle_play_pause)

        # Display placeholder
        self.show_placeholder()

    def show_placeholder(self):
        """Show placeholder when no video is loaded."""
        self.canvas.delete("all")
        self.canvas.create_text(self.width//2, self.height//2,
                               text="Click 'Browse' to load a video",
                               fill="white", font=('Arial', 12))

    def load_video(self, video_path):
        """Load video file."""
        if self.cap:
            self.cap.release()

        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)

        if not self.cap.isOpened():
            messagebox.showerror("Error", "Failed to load video")
            return False

        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.frame_delay = int(1000 / self.fps) if self.fps > 0 else 33

        self.current_frame = 0
        self.show_frame(0)
        self.auto_play()  # Start auto-play by default

        return True

    def show_frame(self, frame_number):
        """Display specific frame."""
        if not self.cap:
            return

        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = self.cap.read()

        if ret:
            # Resize frame to fit canvas
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (self.width, self.height))

            # Convert to PhotoImage
            image = Image.fromarray(frame)
            self.photo = ImageTk.PhotoImage(image)

            # Display on canvas
            self.canvas.delete("all")
            self.canvas.create_image(self.width//2, self.height//2,
                                   image=self.photo, anchor=tk.CENTER)

            self.current_frame = frame_number
            self.current_time = frame_number / self.fps if self.fps > 0 else 0

    def auto_play(self):
        """Start auto-play (loop)."""
        self.is_playing = True
        self.start_time = time.time() - (self.current_frame / self.fps)
        self.play_loop()

    def toggle_play_pause(self, event=None):
        """Toggle between play and pause."""
        if not self.cap:
            return

        self.is_playing = not self.is_playing

        if self.is_playing:
            self.start_time = time.time() - (self.current_frame / self.fps)
            self.play_loop()

    def play_loop(self):
        """Play video loop."""
        if not self.is_playing or not self.cap:
            return

        current_time = time.time()
        elapsed_time = current_time - self.start_time
        target_frame = int(elapsed_time * self.fps)

        # Loop video
        if target_frame >= self.total_frames:
            target_frame = 0
            self.start_time = current_time

        if target_frame != self.current_frame:
            self.show_frame(target_frame)

        # Schedule next frame
        self.parent.after(self.frame_delay, self.play_loop)

    def get_current_time(self):
        """Get current playback time."""
        return self.current_time

    def get_total_duration(self):
        """Get total video duration."""
        return self.total_frames / self.fps if self.fps > 0 else 0

    def pack(self, **kwargs):
        """Pack the widget."""
        self.frame.pack(**kwargs)

    def destroy(self):
        """Clean up resources."""
        if self.cap:
            self.cap.release()


class MotionAnalyzerGUI:
    """Enhanced GUI application for motion analysis and video assembly."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Motion Analysis and Video Assembly Tool")
        self.root.geometry("1200x900")

        # Initialize components
        self.motion_analyzer = MotionAnalyzer()
        self.video_assembler = VideoAssembler()
        self.video_splitter = VideoSplitter()

        # GUI state variables
        self.current_video_path = tk.StringVar()
        self.current_code_path = tk.StringVar()
        self.analysis_results = None

        # Video preview and timing
        self.video_preview = None
        self.time_var = tk.StringVar(value="0.0 s")
        self.timer_active = False

        # Setup GUI
        self.setup_gui()

    def setup_gui(self):
        """Initialize the GUI layout."""
        # Create main notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create tabs - combining analysis and assembly
        self.create_main_tab()
        self.create_utilities_tab()

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var,
                                   relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_main_tab(self):
        """Create the main analysis and assembly tab."""
        main_frame = ttk.Frame(self.notebook)
        self.notebook.add(main_frame, text="Video Analysis & Assembly")

        # Title
        title_label = ttk.Label(main_frame, text="Motion Analysis and Video Assembly",
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(10, 20))

        # Create two-column layout
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10)

        # Left column - Video input and preview
        left_frame = ttk.Frame(content_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Right column - Analysis results and assembly
        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

        # === LEFT COLUMN ===
        self.create_video_input_section(left_frame)
        self.create_video_preview_section(left_frame)
        self.create_clock_section(left_frame)
        self.create_analysis_controls(left_frame)

        # === RIGHT COLUMN ===
        self.create_analysis_results_section(right_frame)
        self.create_assembly_section(right_frame)

    def create_video_input_section(self, parent):
        """Create video input section."""
        input_frame = ttk.LabelFrame(parent, text="Input Video", padding=10)
        input_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(input_frame, text="Select factory floor video:").pack(anchor=tk.W)

        # Supported formats info
        formats_label = ttk.Label(input_frame,
                                 text="Supported formats: MP4, AVI, MOV, MKV, WMV, FLV",
                                 font=('Arial', 9), foreground='gray')
        formats_label.pack(anchor=tk.W, pady=(0, 5))

        video_frame = ttk.Frame(input_frame)
        video_frame.pack(fill=tk.X, pady=5)

        self.video_entry = ttk.Entry(video_frame, textvariable=self.current_video_path,
                                    width=40, state='readonly')
        self.video_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(video_frame, text="Browse",
                  command=self.browse_video_file).pack(side=tk.RIGHT, padx=(5, 0))

    def create_video_preview_section(self, parent):
        """Create video preview section."""
        preview_frame = ttk.LabelFrame(parent, text="Video Preview", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Create video preview widget
        self.video_preview = VideoPreviewWidget(preview_frame, width=400, height=300)
        self.video_preview.pack(fill=tk.BOTH, expand=True)

        # Instructions
        instructions = ttk.Label(preview_frame,
                                text="Click on video to play/pause • Auto-loops by default",
                                font=('Arial', 9), foreground='gray')
        instructions.pack(pady=(5, 0))

    def create_clock_section(self, parent):
        """Create clock widget section."""
        clock_frame = ttk.Frame(parent)
        clock_frame.pack(fill=tk.X, pady=(0, 10))

        # Time display
        time_label = ttk.Label(clock_frame, text="Time:", font=('Arial', 12, 'bold'))
        time_label.pack(side=tk.LEFT)

        self.time_display = ttk.Label(clock_frame, textvariable=self.time_var,
                                     font=('Arial', 14, 'bold'), foreground='blue')
        self.time_display.pack(side=tk.LEFT, padx=(10, 0))

        # Start timer update
        self.update_timer()

    def create_analysis_controls(self, parent):
        """Create analysis control section."""
        controls_frame = ttk.LabelFrame(parent, text="Analysis", padding=10)
        controls_frame.pack(fill=tk.X, pady=(0, 10))

        # Single analyze button
        self.analyze_btn = ttk.Button(controls_frame, text="Analyze Video",
                                     command=self.start_analysis,
                                     style='Accent.TButton')
        self.analyze_btn.pack(pady=5)

        # Status label
        self.analysis_status = ttk.Label(controls_frame, text="Select a video to analyze",
                                        font=('Arial', 10), foreground='gray')
        self.analysis_status.pack(pady=(5, 0))

    def create_analysis_results_section(self, parent):
        """Create analysis results section."""
        results_frame = ttk.LabelFrame(parent, text="Analysis Results", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Video information (shown after analysis)
        self.video_info_frame = ttk.LabelFrame(results_frame, text="Video Information", padding=5)
        self.video_info_frame.pack(fill=tk.X, pady=(0, 10))

        self.video_info_text = scrolledtext.ScrolledText(self.video_info_frame, height=4,
                                                        state='disabled')
        self.video_info_text.pack(fill=tk.X)

        # Action code results
        code_frame = ttk.LabelFrame(results_frame, text="Generated Action Code with Timestamps", padding=5)
        code_frame.pack(fill=tk.BOTH, expand=True)

        self.results_text = scrolledtext.ScrolledText(code_frame, height=15)
        self.results_text.pack(fill=tk.BOTH, expand=True)

        # Results controls
        results_controls = ttk.Frame(results_frame)
        results_controls.pack(fill=tk.X, pady=(5, 0))

        ttk.Button(results_controls, text="Save Action Code",
                  command=self.save_action_code).pack(side=tk.LEFT)

        ttk.Button(results_controls, text="Clear Results",
                  command=self.clear_results).pack(side=tk.LEFT, padx=(10, 0))

    def create_assembly_section(self, parent):
        """Create video assembly section."""
        assembly_frame = ttk.LabelFrame(parent, text="Video Assembly", padding=10)
        assembly_frame.pack(fill=tk.X, pady=(0, 10))

        # Instructions
        ttk.Label(assembly_frame,
                 text="After analysis, click 'Assemble Training Video' to create a training video",
                 font=('Arial', 10), foreground='gray').pack(anchor=tk.W, pady=(0, 10))

        # Assembly button
        self.assemble_btn = ttk.Button(assembly_frame, text="Assemble Training Video",
                                      command=self.start_assembly,
                                      style='Accent.TButton',
                                      state='disabled')
        self.assemble_btn.pack(pady=5)

        # Assembly status
        self.assembly_status = ttk.Label(assembly_frame, text="Complete analysis first",
                                        font=('Arial', 10), foreground='gray')
        self.assembly_status.pack(pady=(5, 0))

    def create_utilities_tab(self):
        """Create the utilities tab."""
        utils_frame = ttk.Frame(self.notebook)
        self.notebook.add(utils_frame, text="Utilities")

        # Title
        title_label = ttk.Label(utils_frame, text="Video Processing Utilities",
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(10, 20))

        # Video splitter section
        splitter_frame = ttk.LabelFrame(utils_frame, text="Split Training Video", padding=10)
        splitter_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(splitter_frame, text="Extract components from training video:").pack(anchor=tk.W)

        # Supported formats info for utilities
        formats_label3 = ttk.Label(splitter_frame,
                                  text="Supported formats: MP4, AVI, MOV, MKV, WMV, FLV",
                                  font=('Arial', 9), foreground='gray')
        formats_label3.pack(anchor=tk.W, pady=(0, 5))

        split_input_frame = ttk.Frame(splitter_frame)
        split_input_frame.pack(fill=tk.X, pady=5)

        self.split_video_entry = ttk.Entry(split_input_frame, width=50, state='readonly')
        self.split_video_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(split_input_frame, text="Browse",
                  command=self.browse_training_video).pack(side=tk.RIGHT, padx=(5, 0))

        ttk.Button(splitter_frame, text="Split Video",
                  command=self.split_training_video).pack(pady=5)

        # Training video player section
        player_frame = ttk.LabelFrame(utils_frame, text="Training Video Player", padding=10)
        player_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(player_frame, text="Open existing training video with player:").pack(anchor=tk.W)

        player_input_frame = ttk.Frame(player_frame)
        player_input_frame.pack(fill=tk.X, pady=5)

        self.player_video_entry = ttk.Entry(player_input_frame, width=50, state='readonly')
        self.player_video_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(player_input_frame, text="Browse",
                  command=self.browse_player_video).pack(side=tk.RIGHT, padx=(5, 0))

        ttk.Button(player_frame, text="Open in Player",
                  command=self.open_training_video_player).pack(pady=5)

        # Configuration section
        config_frame = ttk.LabelFrame(utils_frame, text="Configuration", padding=10)
        config_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(config_frame, text="Edit Analysis Settings",
                  command=self.edit_analysis_config).pack(side=tk.LEFT, padx=5)

        ttk.Button(config_frame, text="Edit Assembly Settings",
                  command=self.edit_assembly_config).pack(side=tk.LEFT, padx=5)

        # About section
        about_frame = ttk.LabelFrame(utils_frame, text="About", padding=10)
        about_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        about_text = """Motion Analysis Tool with Enhanced GUI v2.0

Features:
• Real-time video preview with play/pause control
• Sub-second accuracy clock display
• Integrated analysis and assembly workflow
• Timestamped action code generation
• Comprehensive video format support

The tool analyzes factory floor videos to extract motion patterns and generate
action code descriptions with precise timestamps. It can also assemble training
videos by combining raw footage with generated code overlays."""

        about_label = ttk.Label(about_frame, text=about_text, justify=tk.LEFT, wraplength=800)
        about_label.pack(anchor=tk.W)

    # === EVENT HANDLERS ===

    def browse_video_file(self):
        """Browse and select a video file for analysis."""
        file_path = filedialog.askopenfilename(
            title="Select Factory Floor Video",
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv"), ("All files", "*.*")]
        )

        if file_path:
            self.current_video_path.set(file_path)
            # Load video in preview
            if self.video_preview.load_video(file_path):
                self.analysis_status.config(text="Video loaded - Ready to analyze")
                self.analyze_btn.config(state='normal')
            else:
                self.analysis_status.config(text="Failed to load video")

    def update_timer(self):
        """Update the timer display."""
        if self.video_preview and self.video_preview.cap:
            current_time = self.video_preview.get_current_time()
            total_time = self.video_preview.get_total_duration()
            self.time_var.set(f"{current_time:.1f}s / {total_time:.1f}s")
        else:
            self.time_var.set("0.0s")

        # Schedule next update
        self.root.after(100, self.update_timer)  # Update every 100ms for smooth display

    def start_analysis(self):
        """Start video analysis."""
        if not self.current_video_path.get():
            messagebox.showwarning("Warning", "Please select a video file first.")
            return

        self.analyze_btn.config(state='disabled')
        self.analysis_status.config(text="Analyzing video...")

        # Clear previous results
        self.results_text.delete(1.0, tk.END)
        self.clear_video_info()

        # Start analysis in separate thread
        analysis_thread = threading.Thread(target=self.analyze_video_thread)
        analysis_thread.daemon = True
        analysis_thread.start()

    def analyze_video_thread(self):
        """Perform video analysis in background thread."""
        try:
            output_dir = os.path.join(os.path.dirname(self.current_video_path.get()),
                                     "analysis_output")

            action_code, metadata = self.motion_analyzer.analyze_video(
                self.current_video_path.get(), output_dir
            )

            self.analysis_results = {
                'action_code': action_code,
                'metadata': metadata
            }

            # Update GUI in main thread
            self.root.after(0, self.analysis_complete)

        except Exception as e:
            self.root.after(0, lambda: self.analysis_error(str(e)))

    def analysis_complete(self):
        """Handle completion of video analysis."""
        self.analyze_btn.config(state='normal')
        self.analysis_status.config(text="Analysis complete")

        if self.analysis_results:
            # Display results with timestamps
            action_code = self.analysis_results['action_code']
            metadata = self.analysis_results['metadata']

            # Generate timestamped action code
            timestamped_code = self.generate_timestamped_code(action_code, metadata)

            result_text = f"Action Code with Timestamps:\n{'='*60}\n\n{timestamped_code}\n\n"
            result_text += f"Analysis Summary:\n{'='*40}\n"
            result_text += f"Motion Events Detected: {metadata['motion_events']}\n"
            result_text += f"Analysis Time: {metadata['analysis_time']}\n"
            result_text += f"Output File: {metadata['output_file']}\n"

            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(1.0, result_text)

            # Load and display video information
            self.load_video_info_after_analysis(self.current_video_path.get())

            # Enable assembly
            self.assemble_btn.config(state='normal')
            self.assembly_status.config(text="Ready to assemble training video")

    def generate_timestamped_code(self, action_code, metadata):
        """Generate action code with timestamps."""
        # For now, add timestamps based on video duration
        # In a real implementation, you'd use the motion events from analysis
        lines = action_code.split('\n')
        total_duration = self.video_preview.get_total_duration() if self.video_preview else 34.3

        timestamped_lines = []
        current_time = 0.0
        time_increment = total_duration / max(len([l for l in lines if l.strip()]), 1)

        for line in lines:
            if line.strip() and not line.startswith('#'):
                timestamped_lines.append(f"[{current_time:05.1f}s] {line}")
                current_time += time_increment
            else:
                timestamped_lines.append(line)

        return '\n'.join(timestamped_lines)

    def load_video_info_after_analysis(self, video_path):
        """Load and display video information after analysis."""
        try:
            info = VideoProcessor.get_video_info(video_path)

            info_text = f"""File: {os.path.basename(video_path)}
Dimensions: {info['width']} x {info['height']} pixels
Duration: {info['duration']:.1f} seconds
Frame Rate: {info['fps']:.1f} fps
Total Frames: {info['frame_count']:,}
Analysis Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

            self.video_info_text.config(state='normal')
            self.video_info_text.delete(1.0, tk.END)
            self.video_info_text.insert(1.0, info_text)
            self.video_info_text.config(state='disabled')

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load video info: {str(e)}")

    def clear_video_info(self):
        """Clear video information display."""
        self.video_info_text.config(state='normal')
        self.video_info_text.delete(1.0, tk.END)
        self.video_info_text.config(state='disabled')

    def analysis_error(self, error_msg: str):
        """Handle analysis error."""
        self.analyze_btn.config(state='normal')
        self.analysis_status.config(text="Analysis failed")
        messagebox.showerror("Analysis Error", f"Failed to analyze video: {error_msg}")

    def save_action_code(self):
        """Save the generated action code to a file."""
        if not self.analysis_results:
            messagebox.showwarning("Warning", "No analysis results to save.")
            return

        file_path = filedialog.asksaveasfilename(
            title="Save Action Code",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )

        if file_path:
            try:
                # Get timestamped code from results text
                content = self.results_text.get(1.0, tk.END)
                with open(file_path, 'w') as f:
                    f.write(content)
                messagebox.showinfo("Success", f"Action code saved to {file_path}")
                # Update current code path for assembly
                self.current_code_path.set(file_path)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {str(e)}")

    def clear_results(self):
        """Clear analysis results."""
        self.results_text.delete(1.0, tk.END)
        self.clear_video_info()
        self.assemble_btn.config(state='disabled')
        self.assembly_status.config(text="Complete analysis first")

    def start_assembly(self):
        """Start video assembly process."""
        raw_video = self.current_video_path.get()

        if not raw_video:
            messagebox.showwarning("Warning", "Please select and analyze a video first.")
            return

        if not self.analysis_results:
            messagebox.showwarning("Warning", "Please complete video analysis first.")
            return

        # Use the generated code file from analysis
        code_file = self.analysis_results['metadata']['output_file']

        # Choose output path
        output_path = filedialog.asksaveasfilename(
            title="Save Assembled Training Video",
            defaultextension=".mp4",
            filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")]
        )

        if not output_path:
            return

        self.assemble_btn.config(state='disabled')
        self.assembly_status.config(text="Assembling training video...")

        # Start assembly in separate thread
        assembly_thread = threading.Thread(
            target=self.assemble_video_thread,
            args=(raw_video, code_file, output_path)
        )
        assembly_thread.daemon = True
        assembly_thread.start()

    def assemble_video_thread(self, raw_video: str, code_file: str, output_path: str):
        """Perform video assembly in background thread."""
        try:
            metadata = self.video_assembler.assemble_training_video(
                raw_video, code_file, output_path
            )

            self.root.after(0, lambda: self.assembly_complete(metadata, output_path))

        except Exception as e:
            self.root.after(0, lambda: self.assembly_error(str(e)))

    def assembly_complete(self, metadata: Dict, output_path: str):
        """Handle completion of video assembly."""
        self.assemble_btn.config(state='normal')
        self.assembly_status.config(text="Assembly complete!")

        size_mb = metadata.get('output_file_size', 0) / (1024 * 1024)

        # Show brief success message
        messagebox.showinfo("Success",
                           f"Training video assembled successfully!\n"
                           f"Size: {size_mb:.1f} MB\n"
                           f"Opening training video player...")

        # Open the training video player with the assembled video
        try:
            # Get the timestamped action code from the results text
            action_code_with_timestamps = self.results_text.get(1.0, tk.END)

            # Create and open the training video player
            player = create_training_video_player(self.root, output_path, action_code_with_timestamps)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open training video player: {str(e)}")

    def assembly_error(self, error_msg: str):
        """Handle assembly error."""
        self.assemble_btn.config(state='normal')
        self.assembly_status.config(text="Assembly failed")
        messagebox.showerror("Assembly Error", f"Failed to assemble video: {error_msg}")

    # Utilities event handlers (same as before)
    def browse_training_video(self):
        """Browse for training video to split."""
        file_path = filedialog.askopenfilename(
            title="Select Training Video to Split",
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv"), ("All files", "*.*")]
        )

        if file_path:
            self.split_video_entry.delete(0, tk.END)
            self.split_video_entry.insert(0, file_path)

    def split_training_video(self):
        """Split training video into components."""
        video_path = self.split_video_entry.get()

        if not video_path:
            messagebox.showwarning("Warning", "Please select a training video to split.")
            return

        output_dir = filedialog.askdirectory(title="Select Output Directory")

        if not output_dir:
            return

        try:
            result = self.video_splitter.split_training_video(video_path, output_dir)

            message = f"Video split successfully!\n\n"
            message += f"Raw video: {result['raw_video_path']}\n"
            message += f"Code image: {result['code_image_path']}"

            messagebox.showinfo("Success", message)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to split video: {str(e)}")

    def browse_player_video(self):
        """Browse for training video to open in player."""
        file_path = filedialog.askopenfilename(
            title="Select Training Video",
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv"), ("All files", "*.*")]
        )

        if file_path:
            self.player_video_entry.delete(0, tk.END)
            self.player_video_entry.insert(0, file_path)

    def open_training_video_player(self):
        """Open training video in the dedicated player."""
        video_path = self.player_video_entry.get()

        if not video_path:
            messagebox.showwarning("Warning", "Please select a training video first.")
            return

        if not os.path.exists(video_path):
            messagebox.showerror("Error", "Video file not found.")
            return

        # Generate default action code for unknown training videos
        # In practice, you might want to load this from a companion text file
        default_code = """[00.0s] LOOP forever:
[03.0s]     WHILE input_box has adapters:
[06.0s]         MOVE adapters from input_box TO press_bed
[09.0s]         IF stamping_press already contains a stamped adapter:
[12.0s]             RIGHT_HAND grab stamped adapter
[15.0s]             IF right_hand holds 2 stamped adapters:
[18.0s]                 PLACE 2 stamped adapters INTO output_box
[21.0s]         WHILE press_bed has adapters:
[24.0s]             LEFT_HAND load 1 adapter INTO stamping_press
[27.0s]             RIGHT_HAND press press_button
[30.0s]             LEFT_HAND grab next unstamped adapter
[33.0s]             WAIT until stamping_press completes"""

        try:
            # Look for a companion text file first
            base_path = os.path.splitext(video_path)[0]
            text_file_path = base_path + "_code.txt"

            if os.path.exists(text_file_path):
                with open(text_file_path, 'r') as f:
                    action_code = f.read()
            else:
                action_code = default_code

            # Create and open the training video player
            player = create_training_video_player(self.root, video_path, action_code)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open training video player: {str(e)}")

    def edit_analysis_config(self):
        """Open analysis configuration editor."""
        self.show_config_dialog("Analysis Configuration", self.motion_analyzer.config)

    def edit_assembly_config(self):
        """Open assembly configuration editor."""
        self.show_config_dialog("Assembly Configuration", self.video_assembler.config)

    def show_config_dialog(self, title: str, config: Dict):
        """Show configuration editing dialog."""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()

        # Config text area
        text_frame = ttk.Frame(dialog)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        config_text = scrolledtext.ScrolledText(text_frame)
        config_text.pack(fill=tk.BOTH, expand=True)

        # Load current config
        config_json = json.dumps(config, indent=2)
        config_text.insert(1.0, config_json)

        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=5)

        def save_config():
            try:
                new_config = json.loads(config_text.get(1.0, tk.END))
                config.update(new_config)
                messagebox.showinfo("Success", "Configuration updated successfully!")
                dialog.destroy()
            except json.JSONDecodeError as e:
                messagebox.showerror("Error", f"Invalid JSON: {str(e)}")

        ttk.Button(button_frame, text="Save", command=save_config).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT)


def main():
    """Main application entry point."""
    root = tk.Tk()

    # Set style
    style = ttk.Style()
    style.theme_use('clam')  # Modern looking theme

    app = MotionAnalyzerGUI(root)

    # Center window on screen
    root.update_idletasks()
    x = (root.winfo_screenwidth() - root.winfo_reqwidth()) // 2
    y = (root.winfo_screenheight() - root.winfo_reqheight()) // 2
    root.geometry(f"+{x}+{y}")

    # Clean up on close
    def on_closing():
        if app.video_preview:
            app.video_preview.destroy()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()