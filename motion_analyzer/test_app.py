#!/usr/bin/env python3
"""
Quick test script to verify the motion analyzer setup and functionality.
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test that all modules can be imported."""
    try:
        from src.video_analyzer import MotionAnalyzer, VideoProcessor
        from src.video_assembler import VideoAssembler, VideoSplitter
        print("✓ All modules imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_example_data():
    """Check if example data files exist."""
    data_dir = os.path.join(os.path.dirname(__file__), 'data', 'input')

    required_files = [
        'twitter_video.mp4',
        'human_operation_only.mp4',
        'code_from_video.txt'
    ]

    missing_files = []
    for file in required_files:
        file_path = os.path.join(data_dir, file)
        if os.path.exists(file_path):
            print(f"✓ Found: {file}")
        else:
            print(f"✗ Missing: {file}")
            missing_files.append(file)

    return len(missing_files) == 0

def test_config_files():
    """Check configuration files."""
    config_dir = os.path.join(os.path.dirname(__file__), 'config')

    config_files = [
        'analysis_config.json',
        'assembly_config.json'
    ]

    for config_file in config_files:
        config_path = os.path.join(config_dir, config_file)
        if os.path.exists(config_path):
            print(f"✓ Config found: {config_file}")
        else:
            print(f"✗ Config missing: {config_file}")

def test_basic_functionality():
    """Test basic functionality without GUI."""
    try:
        from src.video_analyzer import MotionAnalyzer
        from src.video_assembler import VideoAssembler

        # Test analyzer initialization
        analyzer = MotionAnalyzer()
        print("✓ MotionAnalyzer initialized")

        # Test assembler initialization
        assembler = VideoAssembler()
        print("✓ VideoAssembler initialized")

        # Test video info reading (if example video exists)
        example_video = os.path.join(os.path.dirname(__file__), 'data', 'input', 'human_operation_only.mp4')
        if os.path.exists(example_video):
            from src.video_analyzer import VideoProcessor
            info = VideoProcessor.get_video_info(example_video)
            print(f"✓ Video info read: {info['width']}x{info['height']}, {info['duration']:.1f}s")

        return True

    except Exception as e:
        print(f"✗ Functionality test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Motion Analysis Tool - Setup Test")
    print("=" * 40)

    all_passed = True

    print("\n1. Testing imports...")
    all_passed &= test_imports()

    print("\n2. Testing example data...")
    all_passed &= test_example_data()

    print("\n3. Testing configuration files...")
    test_config_files()

    print("\n4. Testing basic functionality...")
    all_passed &= test_basic_functionality()

    print("\n" + "=" * 40)
    if all_passed:
        print("✓ All tests passed! The application is ready to use.")
        print("\nTo start the GUI application, run:")
        print("  python main.py")
    else:
        print("✗ Some tests failed. Please check the setup.")
        print("\nMake sure you have:")
        print("  - Installed requirements: pip install -r requirements.txt")
        print("  - FFmpeg installed and in PATH")
        print("  - Example data files in data/input/")

if __name__ == "__main__":
    main()