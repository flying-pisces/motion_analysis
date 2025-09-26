"""
Enhanced Video Preview Widget with Object Tracking Visualization
Shows real-time object detection and tracking overlays on video preview
"""

import tkinter as tk
from tkinter import ttk
import cv2
import numpy as np
from PIL import Image, ImageTk
import threading
import time
from typing import Optional, Callable, List, Dict
from object_tracker import ObjectTracker, ObjectType, TrackedObject


class TrackedVideoPreviewWidget:
    """Enhanced video preview widget with object tracking visualization."""

    def __init__(self, parent, width=600, height=400):
        self.parent = parent
        self.width = width
        self.height = height

        # Create main frame
        self.main_frame = ttk.Frame(parent)

        # Create two-panel layout
        self.video_frame = ttk.LabelFrame(self.main_frame, text="Video with Object Tracking", padding=5)
        self.video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.info_frame = ttk.LabelFrame(self.main_frame, text="Tracking Information", padding=5)
        self.info_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))

        # Video canvas
        self.canvas = tk.Canvas(self.video_frame, width=width, height=height, bg='black')
        self.canvas.pack()

        # Control buttons
        self.controls_frame = ttk.Frame(self.video_frame)
        self.controls_frame.pack(fill=tk.X, pady=(5, 0))

        self.play_btn = ttk.Button(self.controls_frame, text="▶ Play", command=self.toggle_play_pause)
        self.play_btn.pack(side=tk.LEFT, padx=2)

        self.track_btn = ttk.Button(self.controls_frame, text="🎯 Enable Tracking", command=self.toggle_tracking)
        self.track_btn.pack(side=tk.LEFT, padx=2)

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Scale(self.controls_frame, from_=0, to=100,
                                     orient=tk.HORIZONTAL, variable=self.progress_var,
                                     command=self.on_seek)
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Time label
        self.time_label = ttk.Label(self.controls_frame, text="0:00 / 0:00")
        self.time_label.pack(side=tk.RIGHT, padx=5)

        # Object tracking information display
        self.create_info_display()

        # Video state
        self.video_path = None
        self.cap = None
        self.is_playing = False
        self.current_frame = 0
        self.total_frames = 0
        self.fps = 30
        self.frame_delay = 33

        # Object tracking
        self.tracking_enabled = False
        self.object_tracker = ObjectTracker()
        self.tracked_objects = []

        # Callbacks
        self.time_update_callback = None
        self.object_update_callback = None

        # Display placeholder
        self.show_placeholder()

    def create_info_display(self):
        """Create information display panel for tracking data."""
        # Initialize display variables
        self.show_trajectories = tk.BooleanVar(value=True)
        self.show_labels = tk.BooleanVar(value=True)
        self.show_confidence = tk.BooleanVar(value=True)

        # Object count display
        count_frame = ttk.LabelFrame(self.info_frame, text="Object Counts", padding=5)
        count_frame.pack(fill=tk.X, pady=(0, 5))

        self.count_labels = {}
        for obj_type in [ObjectType.DUT, ObjectType.LEFT_HAND, ObjectType.RIGHT_HAND,
                        ObjectType.CONVEYOR, ObjectType.FIXTURE]:
            frame = ttk.Frame(count_frame)
            frame.pack(fill=tk.X, pady=1)

            # Color indicator
            color_box = tk.Canvas(frame, width=15, height=15)
            color_box.pack(side=tk.LEFT, padx=(0, 5))

            # Set color based on type
            colors = {
                ObjectType.DUT: "#00FF00",  # Green
                ObjectType.LEFT_HAND: "#0000FF",  # Blue
                ObjectType.RIGHT_HAND: "#FF0000",  # Red
                ObjectType.CONVEYOR: "#FFFF00",  # Yellow
                ObjectType.FIXTURE: "#800080"  # Purple
            }
            color = colors.get(obj_type, "#808080")
            color_box.create_rectangle(2, 2, 13, 13, fill=color, outline=color)

            # Count label
            label = ttk.Label(frame, text=f"{obj_type.value}: 0")
            label.pack(side=tk.LEFT)
            self.count_labels[obj_type] = label

        # Display options
        options_frame = ttk.LabelFrame(self.info_frame, text="Display Options", padding=5)
        options_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Checkbutton(options_frame, text="Show Trajectories",
                       variable=self.show_trajectories).pack(anchor=tk.W)
        ttk.Checkbutton(options_frame, text="Show Labels",
                       variable=self.show_labels).pack(anchor=tk.W)
        ttk.Checkbutton(options_frame, text="Show Confidence",
                       variable=self.show_confidence).pack(anchor=tk.W)

        # Statistics display
        stats_frame = ttk.LabelFrame(self.info_frame, text="Statistics", padding=5)
        stats_frame.pack(fill=tk.X, pady=(0, 5))

        self.stats_text = tk.Text(stats_frame, height=6, width=25, wrap=tk.WORD)
        self.stats_text.pack(fill=tk.BOTH)

        # Currently tracked objects list
        tracked_frame = ttk.LabelFrame(self.info_frame, text="Active Objects", padding=5)
        tracked_frame.pack(fill=tk.BOTH, expand=True)

        # Create treeview for tracked objects
        self.tracked_tree = ttk.Treeview(tracked_frame, columns=('Type', 'ID', 'Conf'),
                                        show='tree headings', height=8)
        self.tracked_tree.heading('#0', text='')
        self.tracked_tree.heading('Type', text='Type')
        self.tracked_tree.heading('ID', text='ID')
        self.tracked_tree.heading('Conf', text='Conf')

        self.tracked_tree.column('#0', width=0, stretch=False)
        self.tracked_tree.column('Type', width=80)
        self.tracked_tree.column('ID', width=40)
        self.tracked_tree.column('Conf', width=50)

        self.tracked_tree.pack(fill=tk.BOTH, expand=True)

    def show_placeholder(self):
        """Show placeholder when no video is loaded."""
        self.canvas.delete("all")
        self.canvas.create_text(self.width//2, self.height//2,
                               text="Load a video to see object tracking",
                               fill="white", font=('Arial', 14))
        self.canvas.create_text(self.width//2, self.height//2 + 30,
                               text="Click 'Enable Tracking' to start",
                               fill="gray", font=('Arial', 11))

    def load_video(self, video_path: str) -> bool:
        """Load video file."""
        if self.cap:
            self.cap.release()

        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)

        if not self.cap.isOpened():
            return False

        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.frame_delay = int(1000 / self.fps) if self.fps > 0 else 33

        self.current_frame = 0
        self.show_frame(0)

        # Reset tracking
        self.object_tracker = ObjectTracker()
        self.tracked_objects = []

        return True

    def show_frame(self, frame_number: int):
        """Display specific frame with optional tracking overlay."""
        if not self.cap:
            return

        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = self.cap.read()

        if ret:
            # Process frame with object tracker if enabled
            if self.tracking_enabled:
                self.tracked_objects = self.object_tracker.process_frame(frame)

                # Draw tracking overlays
                if self.tracked_objects:
                    frame = self.draw_tracking_overlay(frame, self.tracked_objects)

                # Update information displays
                self.update_tracking_info()

                # Notify callbacks
                if self.object_update_callback:
                    self.object_update_callback(self.tracked_objects)

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

            # Update progress and time
            self.current_frame = frame_number
            self.update_time_display()

    def draw_tracking_overlay(self, frame: np.ndarray, objects: List[TrackedObject]) -> np.ndarray:
        """Draw tracking overlays on the frame."""
        result_frame = frame.copy()

        # Define colors for different object types
        colors = {
            ObjectType.DUT: (0, 255, 0),  # Green
            ObjectType.LEFT_HAND: (255, 0, 0),  # Blue
            ObjectType.RIGHT_HAND: (0, 0, 255),  # Red
            ObjectType.CONVEYOR: (255, 255, 0),  # Cyan
            ObjectType.FIXTURE: (128, 0, 128),  # Purple
            ObjectType.UNKNOWN: (128, 128, 128)  # Gray
        }

        for obj in objects:
            color = colors.get(obj.object_type, (128, 128, 128))
            x, y, w, h = obj.bbox

            # Draw bounding box
            thickness = 3 if obj.object_type == ObjectType.DUT else 2
            cv2.rectangle(result_frame, (x, y), (x + w, y + h), color, thickness)

            # Draw label if enabled
            if self.show_labels.get():
                label = f"{obj.object_type.value}"
                if self.show_confidence.get():
                    label += f" ({obj.confidence:.2f})"

                label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)

                # Draw label background
                cv2.rectangle(result_frame, (x, y - label_size[1] - 6),
                            (x + label_size[0] + 4, y), color, -1)

                # Draw label text
                cv2.putText(result_frame, label, (x + 2, y - 3),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            # Draw center point
            cv2.circle(result_frame, obj.center, 4, color, -1)

            # Draw motion trajectory if enabled
            if self.show_trajectories.get() and len(obj.motion_history) > 1:
                points = list(obj.motion_history)
                for i in range(1, len(points)):
                    alpha = i / len(points)  # Fade older points
                    pt_color = tuple(int(c * alpha) for c in color)
                    cv2.line(result_frame, points[i-1], points[i], pt_color, 2)

        # Add frame information overlay
        info_text = f"Frame: {self.current_frame}/{self.total_frames} | Objects: {len(objects)}"
        cv2.putText(result_frame, info_text, (10, 30),
                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        return result_frame

    def update_tracking_info(self):
        """Update tracking information displays."""
        # Update object counts
        counts = {}
        for obj_type in ObjectType:
            counts[obj_type] = 0

        for obj in self.tracked_objects:
            counts[obj.object_type] += 1

        for obj_type, label in self.count_labels.items():
            count = counts.get(obj_type, 0)
            label.config(text=f"{obj_type.value}: {count}")

        # Update statistics
        stats = self.object_tracker.get_object_statistics()
        stats_text = f"Total tracked: {stats['total_objects']}\n"
        stats_text += f"Frame: {stats['frame_count']}\n"
        stats_text += f"Avg confidence: {stats['average_confidence']:.2f}\n"

        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats_text)

        # Update tracked objects tree
        self.tracked_tree.delete(*self.tracked_tree.get_children())
        for obj in sorted(self.tracked_objects, key=lambda x: x.id):
            self.tracked_tree.insert('', 'end',
                                   values=(obj.object_type.value,
                                          f"#{obj.id}",
                                          f"{obj.confidence:.2f}"))

    def update_time_display(self):
        """Update time display and progress bar."""
        current_time = self.current_frame / self.fps if self.fps > 0 else 0
        total_time = self.total_frames / self.fps if self.fps > 0 else 0

        # Format time as mm:ss
        current_str = f"{int(current_time//60)}:{int(current_time%60):02d}"
        total_str = f"{int(total_time//60)}:{int(total_time%60):02d}"
        self.time_label.config(text=f"{current_str} / {total_str}")

        # Update progress bar
        if self.total_frames > 0:
            progress = (self.current_frame / self.total_frames) * 100
            self.progress_var.set(progress)

        # Notify callback
        if self.time_update_callback:
            self.time_update_callback(current_time)

    def toggle_play_pause(self):
        """Toggle between play and pause."""
        if not self.cap:
            return

        self.is_playing = not self.is_playing

        if self.is_playing:
            self.play_btn.config(text="⏸ Pause")
            self.play_loop()
        else:
            self.play_btn.config(text="▶ Play")

    def toggle_tracking(self):
        """Toggle object tracking."""
        self.tracking_enabled = not self.tracking_enabled

        if self.tracking_enabled:
            self.track_btn.config(text="🎯 Disable Tracking")
            # Re-process current frame with tracking
            if self.cap:
                self.show_frame(self.current_frame)
        else:
            self.track_btn.config(text="🎯 Enable Tracking")
            self.tracked_objects = []
            self.update_tracking_info()
            # Re-show frame without tracking
            if self.cap:
                self.show_frame(self.current_frame)

    def play_loop(self):
        """Play video loop."""
        if not self.is_playing or not self.cap:
            return

        # Move to next frame
        next_frame = self.current_frame + 1
        if next_frame >= self.total_frames:
            next_frame = 0  # Loop back to start

        self.show_frame(next_frame)

        # Schedule next frame
        self.parent.after(self.frame_delay, self.play_loop)

    def on_seek(self, value):
        """Handle seek bar changes."""
        if not self.cap or not self.total_frames:
            return

        # Calculate target frame from percentage
        target_frame = int((float(value) / 100) * self.total_frames)
        self.show_frame(target_frame)

    def set_time_update_callback(self, callback: Callable):
        """Set callback for time updates."""
        self.time_update_callback = callback

    def set_object_update_callback(self, callback: Callable):
        """Set callback for object tracking updates."""
        self.object_update_callback = callback

    def pack(self, **kwargs):
        """Pack the widget."""
        self.main_frame.pack(**kwargs)

    def destroy(self):
        """Clean up resources."""
        if self.cap:
            self.cap.release()