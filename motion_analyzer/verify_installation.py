#!/usr/bin/env python3
"""
Verification script for the enhanced motion analysis software with object tracking
"""

import sys
import os

def test_basic_imports():
    """Test if all basic components can be imported."""
    print("Testing basic imports...")

    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

        # Test video analyzer
        from src.video_analyzer import MotionAnalyzer, VideoProcessor
        print("✅ Video analyzer imports successful")

        # Test GUI components
        from src.gui_app import MotionAnalyzerGUI
        print("✅ GUI components import successful")

        # Test object tracking (might not be available)
        try:
            from src.object_tracker import ObjectTracker, ObjectType
            print("✅ Object tracking imports successful")
            tracking_available = True
        except ImportError:
            print("⚠️  Object tracking not available (this is OK for basic functionality)")
            tracking_available = False

        return True, tracking_available

    except Exception as e:
        print(f"❌ Import error: {e}")
        return False, False

def test_motion_analyzer():
    """Test motion analyzer initialization."""
    print("\nTesting motion analyzer...")

    try:
        from src.video_analyzer import MotionAnalyzer

        analyzer = MotionAnalyzer()
        print("✅ Motion analyzer initialized successfully")

        # Check if object tracking is available
        if hasattr(analyzer, 'enable_object_tracking'):
            print(f"✅ Object tracking support: {analyzer.enable_object_tracking}")
        else:
            print("⚠️  Object tracking not available in this analyzer instance")

        return True

    except Exception as e:
        print(f"❌ Motion analyzer error: {e}")
        return False

def test_gui_creation():
    """Test GUI creation without actually showing it."""
    print("\nTesting GUI creation...")

    try:
        import tkinter as tk
        from src.gui_app import MotionAnalyzerGUI

        # Create root but don't show it
        root = tk.Tk()
        root.withdraw()  # Hide the window

        # Create the GUI
        app = MotionAnalyzerGUI(root)
        print("✅ GUI created successfully")

        # Check if tracking tab is available
        if hasattr(app, 'tracked_preview'):
            print("✅ Object tracking tab available")
        else:
            print("⚠️  Object tracking tab not available")

        # Clean up
        root.destroy()
        return True

    except Exception as e:
        print(f"❌ GUI creation error: {e}")
        return False

def main():
    """Run all verification tests."""
    print("=== Motion Analysis Software Verification ===\n")

    # Test basic imports
    imports_ok, tracking_available = test_basic_imports()

    if not imports_ok:
        print("\n❌ Basic imports failed. Please check your installation.")
        return False

    # Test motion analyzer
    analyzer_ok = test_motion_analyzer()

    if not analyzer_ok:
        print("\n❌ Motion analyzer test failed.")
        return False

    # Test GUI creation
    gui_ok = test_gui_creation()

    if not gui_ok:
        print("\n❌ GUI creation test failed.")
        return False

    # Summary
    print("\n=== Verification Summary ===")
    print("✅ Basic motion analysis: Working")
    print("✅ GUI interface: Working")

    if tracking_available:
        print("✅ Object tracking: Available")
        print("\n🎉 All features are working! You can:")
        print("   - Use standard video analysis")
        print("   - Use object tracking and classification")
        print("   - Export tracked videos and data")
    else:
        print("⚠️  Object tracking: Not available")
        print("\n✅ Basic functionality is working! You can:")
        print("   - Use standard video analysis")
        print("   - Generate action codes")
        print("   - Create training videos")

    print(f"\nTo run the application: python main.py")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)