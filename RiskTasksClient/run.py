#!/usr/bin/env python3
"""
Risk Tasks Client - Main Entry Point

Run this file to start the application.
It will show a launcher where users can choose between:
- Participant access (for study participants)
- Researcher access (password protected)
"""

import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import and run the launcher
from launcher import main

if __name__ == "__main__":
    print("Starting Risk Tasks Client...")
    print("Default researcher password: PIZZA")
    main()