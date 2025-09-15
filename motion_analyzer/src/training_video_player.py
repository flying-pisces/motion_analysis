"""
Training Video Player GUI
Displays assembled training videos with synchronized text highlighting and interactive controls.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Tuple, Optional
import cv2
from PIL import Image, ImageTk
import time
import threading
import os
import shutil


class TrainingVideoPlayer:
    """Dedicated player for training videos with synchronized text highlighting."""

    def __init__(self, parent, video_path: str, action_code_lines: List[str], timestamps: List[float]):
        self.parent = parent
        self.video_path = video_path
        self.action_code_lines = action_code_lines
        self.timestamps = timestamps

        # Create popup window
        self.window = tk.Toplevel(parent)
        self.window.title("Training Video Player")
        self.window.geometry("1000x800")
        self.window.transient(parent)

        # Video state
        self.cap = None
        self.is_playing = False
        self.current_frame = 0
        self.total_frames = 0
        self.fps = 30
        self.frame_delay = 33
        self.start_time = 0
        self.current_time = 0
        self.current_line_index = 0

        # GUI components
        self.video_canvas = None
        self.text_frame = None
        self.timer_labels = []
        self.text_labels = []
        self.current_time_var = tk.StringVar(value="00.0")

        self.setup_gui()
        self.load_video()

        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_gui(self):
        """Setup the training video player GUI."""
        # Main container
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Title
        title_label = ttk.Label(main_frame, text="Training Video Player",
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 10))

        # Video section (top half)
        video_frame = ttk.LabelFrame(main_frame, text="Video Preview", padding=10)
        video_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.video_canvas = tk.Canvas(video_frame, width=800, height=400, bg='black')
        self.video_canvas.pack(expand=True)

        # Bind video controls
        self.video_canvas.bind("<Button-1>", self.single_click_pause)
        self.video_canvas.bind("<Double-Button-1>", self.double_click_resume)

        # Instructions
        controls_label = ttk.Label(video_frame,
                                  text="Click to pause • Double-click to resume",
                                  font=('Arial', 9), foreground='gray')
        controls_label.pack(pady=(5, 0))

        # Text section (bottom half)
        text_frame = ttk.LabelFrame(main_frame, text="Action Code with Real-time Highlighting", padding=10)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Create scrollable text area with timer column
        self.create_text_display(text_frame)

        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))

        # Current time display
        ttk.Label(button_frame, text="Current Time:", font=('Arial', 12, 'bold')).pack(side=tk.LEFT)
        time_display = ttk.Label(button_frame, textvariable=self.current_time_var,
                                font=('Arial', 14, 'bold'), foreground='blue')
        time_display.pack(side=tk.LEFT, padx=(10, 20))

        # Control buttons
        ttk.Button(button_frame, text="⏸ Pause", command=self.pause_video).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="▶ Play", command=self.play_video).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="⏹ Stop", command=self.stop_video).pack(side=tk.LEFT, padx=5)

        # Save button
        ttk.Button(button_frame, text="💾 Save Video As...",
                  command=self.save_video, style='Accent.TButton').pack(side=tk.RIGHT, padx=5)

    def create_text_display(self, parent):
        """Create the text display area with timer column and highlighting."""
        # Create container frame
        container = ttk.Frame(parent)
        container.pack(fill=tk.BOTH, expand=True)

        # Create canvas and scrollbar for custom text display
        canvas = tk.Canvas(container, bg='white')
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        # Configure scrolling
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Create text lines with timestamps
        self.create_text_lines()

        # Store canvas reference for scrolling
        self.text_canvas = canvas

    def create_text_lines(self):
        """Create individual text lines with timestamps."""
        self.timer_labels = []
        self.text_labels = []

        for i, (line, timestamp) in enumerate(zip(self.action_code_lines, self.timestamps)):
            # Create frame for each line
            line_frame = ttk.Frame(self.scrollable_frame)
            line_frame.pack(fill=tk.X, pady=1)

            # Timer label (left side)
            timer_text = f"{timestamp:05.1f}s"
            timer_label = tk.Label(line_frame, text=timer_text,
                                  font=('Consolas', 10, 'bold'),
                                  fg='blue', bg='white', width=8, anchor='e')
            timer_label.pack(side=tk.LEFT, padx=(5, 10))
            self.timer_labels.append(timer_label)

            # Action code label (right side)
            text_label = tk.Label(line_frame, text=line,
                                 font=('Consolas', 10),
                                 fg='black', bg='white', anchor='w')
            text_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.text_labels.append(text_label)

    def load_video(self):
        """Load the training video."""
        if not os.path.exists(self.video_path):
            messagebox.showerror("Error", f"Video file not found: {self.video_path}")
            return False

        self.cap = cv2.VideoCapture(self.video_path)

        if not self.cap.isOpened():
            messagebox.showerror("Error", "Failed to load training video")
            return False

        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.frame_delay = int(1000 / self.fps) if self.fps > 0 else 33

        # Show first frame and start playing
        self.current_frame = 0
        self.show_frame(0)
        self.start_playback()

        return True

    def show_frame(self, frame_number):
        """Display specific frame and update text highlighting."""
        if not self.cap:
            return

        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = self.cap.read()

        if ret:
            # Calculate video dimensions to fit canvas
            canvas_width = self.video_canvas.winfo_width()
            canvas_height = self.video_canvas.winfo_height()

            if canvas_width > 1 and canvas_height > 1:  # Make sure canvas is initialized
                # Resize frame to fit canvas while maintaining aspect ratio
                h, w = frame.shape[:2]
                aspect_ratio = w / h

                if canvas_width / canvas_height > aspect_ratio:
                    # Canvas is wider, fit to height
                    new_height = canvas_height
                    new_width = int(canvas_height * aspect_ratio)
                else:
                    # Canvas is taller, fit to width
                    new_width = canvas_width
                    new_height = int(canvas_width / aspect_ratio)

                frame = cv2.resize(frame, (new_width, new_height))
            else:
                # Default size if canvas not ready
                frame = cv2.resize(frame, (800, 400))

            # Convert to PhotoImage
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(frame)
            self.photo = ImageTk.PhotoImage(image)

            # Display on canvas
            self.video_canvas.delete("all")
            self.video_canvas.create_image(canvas_width//2 if canvas_width > 1 else 400,
                                         canvas_height//2 if canvas_height > 1 else 200,
                                         image=self.photo, anchor=tk.CENTER)

            self.current_frame = frame_number
            self.current_time = frame_number / self.fps if self.fps > 0 else 0

            # Update time display
            self.current_time_var.set(f"{self.current_time:05.1f}s")

            # Update text highlighting
            self.update_text_highlighting()

    def update_text_highlighting(self):
        """Update text highlighting based on current time."""
        if not self.timestamps:
            return

        # Find current line index based on timestamp
        new_line_index = 0
        for i, timestamp in enumerate(self.timestamps):
            if self.current_time >= timestamp:
                new_line_index = i
            else:
                break

        # Update highlighting if line changed
        if new_line_index != self.current_line_index:
            # Reset previous line
            if self.current_line_index < len(self.text_labels):
                self.text_labels[self.current_line_index].config(bg='white', fg='black')
                self.timer_labels[self.current_line_index].config(bg='white', fg='blue')

            # Highlight current line
            if new_line_index < len(self.text_labels):
                self.text_labels[new_line_index].config(bg='yellow', fg='red')
                self.timer_labels[new_line_index].config(bg='yellow', fg='red')

            self.current_line_index = new_line_index

            # Auto-scroll to current line
            self.scroll_to_current_line()

    def scroll_to_current_line(self):
        """Auto-scroll text area to show current highlighted line."""
        if self.current_line_index < len(self.text_labels):
            # Calculate the position of the current line
            total_lines = len(self.text_labels)
            if total_lines > 0:
                scroll_position = self.current_line_index / total_lines
                # Scroll to show the line in the middle of the visible area
                scroll_position = max(0, scroll_position - 0.3)
                self.text_canvas.yview_moveto(scroll_position)

    def start_playback(self):
        """Start video playback."""
        self.is_playing = True
        self.start_time = time.time()
        self.play_loop()

    def play_loop(self):
        """Main playback loop."""
        if not self.is_playing or not self.cap:
            return

        current_time = time.time()
        elapsed_time = current_time - self.start_time
        target_frame = int(elapsed_time * self.fps)

        # Loop video when it reaches the end
        if target_frame >= self.total_frames:
            target_frame = 0
            self.start_time = current_time

        if target_frame != self.current_frame:
            self.show_frame(target_frame)

        # Schedule next frame
        self.window.after(self.frame_delay, self.play_loop)

    def single_click_pause(self, event=None):
        """Handle single click to pause."""
        self.pause_video()

    def double_click_resume(self, event=None):
        """Handle double click to resume."""
        self.play_video()

    def play_video(self):
        """Start/resume video playback."""
        if not self.is_playing and self.cap:
            self.is_playing = True
            self.start_time = time.time() - (self.current_frame / self.fps)
            self.play_loop()

    def pause_video(self):
        """Pause video playback."""
        self.is_playing = False

    def stop_video(self):
        """Stop video playback and return to beginning."""
        self.is_playing = False
        self.current_frame = 0
        self.show_frame(0)

    def save_video(self):
        """Save the training video to a new location."""
        if not os.path.exists(self.video_path):
            messagebox.showerror("Error", "Original video file not found")
            return

        # Ask user where to save
        save_path = filedialog.asksaveasfilename(
            title="Save Training Video",
            defaultextension=".mp4",
            filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")]
        )

        if save_path:
            try:
                # Copy the video file
                shutil.copy2(self.video_path, save_path)

                # Get file size
                size_mb = os.path.getsize(save_path) / (1024 * 1024)

                messagebox.showinfo("Success",
                                   f"Training video saved successfully!\n\n"
                                   f"Location: {save_path}\n"
                                   f"Size: {size_mb:.1f} MB")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to save video: {str(e)}")

    def on_close(self):
        """Handle window closing."""
        self.is_playing = False
        if self.cap:
            self.cap.release()
        self.window.destroy()


def create_training_video_player(parent, video_path: str, action_code_text: str):
    """Create and show training video player with parsed action code."""
    # Parse action code to extract lines and timestamps
    lines = action_code_text.split('\n')
    action_lines = []
    timestamps = []

    for line in lines:
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('='):
            # Try to extract timestamp if present
            if line.startswith('[') and ']' in line:
                # Extract timestamp: [12.5s] action
                try:
                    timestamp_part = line.split(']')[0][1:]  # Remove [ and ]
                    timestamp = float(timestamp_part.replace('s', ''))
                    action_part = line.split(']', 1)[1].strip()

                    timestamps.append(timestamp)
                    action_lines.append(action_part)
                except (ValueError, IndexError):
                    # If parsing fails, use line as-is with estimated timestamp
                    timestamps.append(len(action_lines) * 2.0)  # 2 second intervals
                    action_lines.append(line)
            else:
                # No timestamp, estimate based on position
                timestamps.append(len(action_lines) * 2.0)
                action_lines.append(line)

    # If no valid lines found, create a default
    if not action_lines:
        action_lines = ["LOOP forever:", "    WHILE input_box has adapters:", "        MOVE adapters from input_box TO press_bed"]
        timestamps = [0.0, 5.0, 10.0]

    # Create and show the player
    player = TrainingVideoPlayer(parent, video_path, action_lines, timestamps)
    return player


# Test function
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Hide main window

    # Test with sample data
    sample_code = """[00.0s] LOOP forever:
[02.5s]     WHILE input_box has adapters:
[05.0s]         MOVE adapters from input_box TO press_bed
[08.0s]         IF stamping_press already contains a stamped adapter:
[11.0s]             RIGHT_HAND grab stamped adapter
[14.0s]         WHILE press_bed has adapters:
[17.0s]             LEFT_HAND load 1 adapter INTO stamping_press
[20.0s]             RIGHT_HAND press press_button
[23.0s]             LEFT_HAND grab next unstamped adapter
[26.0s]             WAIT until stamping_press completes
[29.0s]             RIGHT_HAND grab stamped adapter
[32.0s]         PLACE output_box ONTO conveyor_belt"""

    # This would normally be called with a real video path
    video_path = "data/input/twitter_video.mp4"

    if os.path.exists(video_path):
        player = create_training_video_player(root, video_path, sample_code)
        root.mainloop()
    else:
        print("Test video not found. This module should be imported and used from the main GUI.")