#!/usr/bin/env python3
"""
YouTube Video Downloader for Training Data
Downloads videos for motion analysis training purposes.
"""

import os
import sys
import subprocess

def check_dependencies():
    """Check if required tools are installed."""
    try:
        # Check if yt-dlp is installed
        subprocess.run(['yt-dlp', '--version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("yt-dlp is not installed.")
        print("\nTo install yt-dlp, run one of the following commands:")
        print("  pip install yt-dlp")
        print("  brew install yt-dlp (on macOS)")
        print("  sudo apt install yt-dlp (on Ubuntu/Debian)")
        return False

def download_video(url, output_dir="motion_analyzer/data/input", quality="best"):
    """
    Download a YouTube video for training purposes.

    Args:
        url: YouTube video URL
        output_dir: Directory to save the video
        quality: Video quality (best, 1080p, 720p, etc.)
    """
    if not check_dependencies():
        return False

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Set output filename template
    output_template = os.path.join(output_dir, '%(title)s.%(ext)s')

    # Build yt-dlp command
    cmd = [
        'yt-dlp',
        '-f', f'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        '-o', output_template,
        '--merge-output-format', 'mp4',
        '--no-playlist',
        '--verbose',
        url
    ]

    print(f"Downloading video from: {url}")
    print(f"Saving to: {output_dir}")
    print(f"Quality: {quality}")
    print("-" * 50)

    try:
        # Execute download
        result = subprocess.run(cmd, capture_output=False, text=True)

        if result.returncode == 0:
            print("\n✅ Video downloaded successfully!")
            print(f"📁 Check the '{output_dir}' directory for the downloaded video.")
            return True
        else:
            print("\n❌ Download failed. Please check the URL and try again.")
            return False

    except Exception as e:
        print(f"\n❌ Error during download: {str(e)}")
        return False

def main():
    """Main function to download the specific training video."""

    # The video URL you want to download
    video_url = "https://www.youtube.com/watch?v=uqidiUvm5-E"

    print("=" * 60)
    print("YouTube Video Downloader for Motion Analysis Training")
    print("=" * 60)
    print()

    # Check if URL is provided as argument
    if len(sys.argv) > 1:
        video_url = sys.argv[1]

    # Download the video
    success = download_video(video_url)

    if success:
        print("\n" + "=" * 60)
        print("Next Steps:")
        print("1. Open the Motion Analysis GUI: python motion_analyzer/main.py")
        print("2. Load the downloaded video from 'motion_analyzer/data/input'")
        print("3. Run motion analysis to generate action code")
        print("4. Create training video with synchronized action code")
        print("=" * 60)

if __name__ == "__main__":
    main()