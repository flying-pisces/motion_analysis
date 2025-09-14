"""
GUI Application for Motion Analysis and Video Assembly
Provides a user-friendly interface for analyzing factory floor videos and creating training materials.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from typing import Optional, Dict
import os
import threading
from datetime import datetime
import json

from video_analyzer import MotionAnalyzer, VideoProcessor
from video_assembler import VideoAssembler, VideoSplitter


class MotionAnalyzerGUI:
    """Main GUI application for motion analysis and video assembly."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Motion Analysis and Video Assembly Tool")
        self.root.geometry("900x700")

        # Initialize components
        self.motion_analyzer = MotionAnalyzer()
        self.video_assembler = VideoAssembler()
        self.video_splitter = VideoSplitter()

        # GUI state variables
        self.current_video_path = tk.StringVar()
        self.current_code_path = tk.StringVar()
        self.analysis_results = None

        # Setup GUI
        self.setup_gui()

    def setup_gui(self):
        """Initialize the GUI layout."""
        # Create main notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create tabs
        self.create_analysis_tab()
        self.create_assembly_tab()
        self.create_utilities_tab()

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var,
                                   relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_analysis_tab(self):
        """Create the video analysis tab."""
        analysis_frame = ttk.Frame(self.notebook)
        self.notebook.add(analysis_frame, text="Video Analysis")

        # Title
        title_label = ttk.Label(analysis_frame, text="Factory Floor Video Analysis",
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(10, 20))

        # Video input section
        input_frame = ttk.LabelFrame(analysis_frame, text="Input Video", padding=10)
        input_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(input_frame, text="Select factory floor video:").pack(anchor=tk.W)

        video_frame = ttk.Frame(input_frame)
        video_frame.pack(fill=tk.X, pady=5)

        self.video_entry = ttk.Entry(video_frame, textvariable=self.current_video_path,
                                    width=60, state='readonly')
        self.video_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(video_frame, text="Browse",
                  command=self.browse_video_file).pack(side=tk.RIGHT, padx=(5, 0))

        # Video info section
        self.video_info_frame = ttk.LabelFrame(analysis_frame, text="Video Information", padding=10)
        self.video_info_frame.pack(fill=tk.X, padx=10, pady=5)

        self.video_info_text = scrolledtext.ScrolledText(self.video_info_frame, height=4,
                                                        state='disabled')
        self.video_info_text.pack(fill=tk.BOTH, expand=True)

        # Analysis controls
        controls_frame = ttk.Frame(analysis_frame)
        controls_frame.pack(fill=tk.X, padx=10, pady=10)

        self.analyze_btn = ttk.Button(controls_frame, text="Analyze Video",
                                     command=self.start_analysis, style='Accent.TButton')
        self.analyze_btn.pack(side=tk.LEFT)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(controls_frame, variable=self.progress_var,
                                           mode='indeterminate')
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))

        # Results section
        results_frame = ttk.LabelFrame(analysis_frame, text="Analysis Results", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.results_text = scrolledtext.ScrolledText(results_frame, height=15)
        self.results_text.pack(fill=tk.BOTH, expand=True)

        # Results controls
        results_controls = ttk.Frame(results_frame)
        results_controls.pack(fill=tk.X, pady=(5, 0))

        ttk.Button(results_controls, text="Save Action Code",
                  command=self.save_action_code).pack(side=tk.LEFT)

        ttk.Button(results_controls, text="Copy to Assembly",
                  command=self.copy_to_assembly).pack(side=tk.LEFT, padx=(10, 0))

    def create_assembly_tab(self):
        """Create the video assembly tab."""
        assembly_frame = ttk.Frame(self.notebook)
        self.notebook.add(assembly_frame, text="Video Assembly")

        # Title
        title_label = ttk.Label(assembly_frame, text="Training Video Assembly",
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(10, 20))

        # Input files section
        inputs_frame = ttk.LabelFrame(assembly_frame, text="Input Files", padding=10)
        inputs_frame.pack(fill=tk.X, padx=10, pady=5)

        # Raw video input
        ttk.Label(inputs_frame, text="Raw video file:").pack(anchor=tk.W)
        raw_video_frame = ttk.Frame(inputs_frame)
        raw_video_frame.pack(fill=tk.X, pady=2)

        self.raw_video_entry = ttk.Entry(raw_video_frame, width=50, state='readonly')
        self.raw_video_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(raw_video_frame, text="Browse",
                  command=self.browse_raw_video).pack(side=tk.RIGHT, padx=(5, 0))

        # Action code input
        ttk.Label(inputs_frame, text="Action code file:").pack(anchor=tk.W, pady=(10, 0))
        code_frame = ttk.Frame(inputs_frame)
        code_frame.pack(fill=tk.X, pady=2)

        self.code_entry = ttk.Entry(code_frame, textvariable=self.current_code_path,
                                   width=50, state='readonly')
        self.code_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(code_frame, text="Browse",
                  command=self.browse_code_file).pack(side=tk.RIGHT, padx=(5, 0))

        # Assembly preview section
        preview_frame = ttk.LabelFrame(assembly_frame, text="Code Preview", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.code_preview = scrolledtext.ScrolledText(preview_frame, height=8)
        self.code_preview.pack(fill=tk.BOTH, expand=True)

        # Assembly controls
        assembly_controls = ttk.Frame(assembly_frame)
        assembly_controls.pack(fill=tk.X, padx=10, pady=10)

        self.assemble_btn = ttk.Button(assembly_controls, text="Assemble Training Video",
                                      command=self.start_assembly, style='Accent.TButton')
        self.assemble_btn.pack(side=tk.LEFT)

        self.assembly_progress = ttk.Progressbar(assembly_controls, mode='indeterminate')
        self.assembly_progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))

        # Output section
        output_frame = ttk.LabelFrame(assembly_frame, text="Output", padding=10)
        output_frame.pack(fill=tk.X, padx=10, pady=5)

        self.output_text = scrolledtext.ScrolledText(output_frame, height=6, state='disabled')
        self.output_text.pack(fill=tk.BOTH, expand=True)

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

        split_input_frame = ttk.Frame(splitter_frame)
        split_input_frame.pack(fill=tk.X, pady=5)

        self.split_video_entry = ttk.Entry(split_input_frame, width=50, state='readonly')
        self.split_video_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(split_input_frame, text="Browse",
                  command=self.browse_training_video).pack(side=tk.RIGHT, padx=(5, 0))

        ttk.Button(splitter_frame, text="Split Video",
                  command=self.split_training_video).pack(pady=5)

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

        about_text = """Motion Analysis and Video Assembly Tool v1.0

This tool analyzes factory floor videos to extract motion patterns and generate
action code descriptions. It can also assemble training videos by combining
raw footage with generated code overlays.

Features:
• Computer vision-based motion analysis
• Automatic action code generation
• Training video assembly with code overlays
• Video splitting utilities
• Configurable analysis parameters

For support and documentation, please refer to the README file."""

        about_label = ttk.Label(about_frame, text=about_text, justify=tk.LEFT, wraplength=600)
        about_label.pack(anchor=tk.W)

    # Event handlers for Analysis tab
    def browse_video_file(self):
        """Browse and select a video file for analysis."""
        file_path = filedialog.askopenfilename(
            title="Select Factory Floor Video",
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv"), ("All files", "*.*")]
        )

        if file_path:
            self.current_video_path.set(file_path)
            self.load_video_info(file_path)

    def load_video_info(self, video_path: str):
        """Load and display video information."""
        try:
            info = VideoProcessor.get_video_info(video_path)

            info_text = f"""File: {os.path.basename(video_path)}
Dimensions: {info['width']} x {info['height']} pixels
Duration: {info['duration']:.1f} seconds
Frame Rate: {info['fps']:.1f} fps
Total Frames: {info['frame_count']:,}
"""

            self.video_info_text.config(state='normal')
            self.video_info_text.delete(1.0, tk.END)
            self.video_info_text.insert(1.0, info_text)
            self.video_info_text.config(state='disabled')

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load video info: {str(e)}")

    def start_analysis(self):
        """Start video analysis in a separate thread."""
        if not self.current_video_path.get():
            messagebox.showwarning("Warning", "Please select a video file first.")
            return

        self.analyze_btn.config(state='disabled')
        self.progress_bar.start()
        self.status_var.set("Analyzing video...")

        # Clear previous results
        self.results_text.delete(1.0, tk.END)

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
        self.progress_bar.stop()
        self.analyze_btn.config(state='normal')
        self.status_var.set("Analysis complete")

        if self.analysis_results:
            # Display results
            action_code = self.analysis_results['action_code']
            metadata = self.analysis_results['metadata']

            result_text = f"Action Code Generated:\n{'='*50}\n\n{action_code}\n\n"
            result_text += f"Analysis Metadata:\n{'='*50}\n"
            result_text += f"Motion Events: {metadata['motion_events']}\n"
            result_text += f"Output File: {metadata['output_file']}\n"
            result_text += f"Analysis Time: {metadata['analysis_time']}\n"

            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(1.0, result_text)

    def analysis_error(self, error_msg: str):
        """Handle analysis error."""
        self.progress_bar.stop()
        self.analyze_btn.config(state='normal')
        self.status_var.set("Analysis failed")
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
                with open(file_path, 'w') as f:
                    f.write(self.analysis_results['action_code'])
                messagebox.showinfo("Success", f"Action code saved to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {str(e)}")

    def copy_to_assembly(self):
        """Copy current analysis results to the assembly tab."""
        if not self.analysis_results:
            messagebox.showwarning("Warning", "No analysis results to copy.")
            return

        # Set the raw video path
        self.raw_video_entry.delete(0, tk.END)
        self.raw_video_entry.insert(0, self.current_video_path.get())

        # Set the action code path
        code_file_path = self.analysis_results['metadata']['output_file']
        self.current_code_path.set(code_file_path)

        # Load code preview
        self.load_code_preview(code_file_path)

        # Switch to assembly tab
        self.notebook.select(1)
        messagebox.showinfo("Success", "Analysis results copied to assembly tab.")

    # Event handlers for Assembly tab
    def browse_raw_video(self):
        """Browse for raw video file."""
        file_path = filedialog.askopenfilename(
            title="Select Raw Video",
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv"), ("All files", "*.*")]
        )

        if file_path:
            self.raw_video_entry.delete(0, tk.END)
            self.raw_video_entry.insert(0, file_path)

    def browse_code_file(self):
        """Browse for action code file."""
        file_path = filedialog.askopenfilename(
            title="Select Action Code File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )

        if file_path:
            self.current_code_path.set(file_path)
            self.load_code_preview(file_path)

    def load_code_preview(self, code_path: str):
        """Load and display code preview."""
        try:
            with open(code_path, 'r') as f:
                code_content = f.read()

            self.code_preview.delete(1.0, tk.END)
            self.code_preview.insert(1.0, code_content)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load code file: {str(e)}")

    def start_assembly(self):
        """Start video assembly process."""
        raw_video = self.raw_video_entry.get()
        code_file = self.current_code_path.get()

        if not raw_video or not code_file:
            messagebox.showwarning("Warning", "Please select both raw video and code files.")
            return

        # Choose output path
        output_path = filedialog.asksaveasfilename(
            title="Save Assembled Video",
            defaultextension=".mp4",
            filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")]
        )

        if not output_path:
            return

        self.assemble_btn.config(state='disabled')
        self.assembly_progress.start()
        self.status_var.set("Assembling training video...")

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
        self.assembly_progress.stop()
        self.assemble_btn.config(state='normal')
        self.status_var.set("Assembly complete")

        # Display results
        result_text = f"Training Video Assembled Successfully!\n{'='*50}\n\n"
        result_text += f"Output File: {output_path}\n"
        result_text += f"Assembly Time: {metadata['assembly_time']}\n"
        result_text += f"Original Dimensions: {metadata['original_dimensions']}\n"
        result_text += f"Assembled Dimensions: {metadata['assembled_dimensions']}\n"
        result_text += f"Duration: {metadata['duration']:.1f} seconds\n"

        if metadata.get('output_file_size'):
            size_mb = metadata['output_file_size'] / (1024 * 1024)
            result_text += f"Output File Size: {size_mb:.1f} MB\n"

        self.output_text.config(state='normal')
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(1.0, result_text)
        self.output_text.config(state='disabled')

        messagebox.showinfo("Success", f"Training video saved to:\n{output_path}")

    def assembly_error(self, error_msg: str):
        """Handle assembly error."""
        self.assembly_progress.stop()
        self.assemble_btn.config(state='normal')
        self.status_var.set("Assembly failed")
        messagebox.showerror("Assembly Error", f"Failed to assemble video: {error_msg}")

    # Event handlers for Utilities tab
    def browse_training_video(self):
        """Browse for training video to split."""
        file_path = filedialog.askopenfilename(
            title="Select Training Video to Split",
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv"), ("All files", "*.*")]
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
            self.status_var.set("Splitting video...")

            result = self.video_splitter.split_training_video(video_path, output_dir)

            message = f"Video split successfully!\n\n"
            message += f"Raw video: {result['raw_video_path']}\n"
            message += f"Code image: {result['code_image_path']}"

            messagebox.showinfo("Success", message)
            self.status_var.set("Split complete")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to split video: {str(e)}")
            self.status_var.set("Split failed")

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

    root.mainloop()


if __name__ == "__main__":
    main()