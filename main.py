#!/usr/bin/env python3
"""
Main entry point for the Motion Analysis and Video Assembly Tool.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.gui_app import main

if __name__ == "__main__":
    main()