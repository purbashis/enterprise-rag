#!/usr/bin/env python3
"""Test script to verify the app imports correctly"""
import sys
import os

# Change to backend directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Add current directory to path
sys.path.insert(0, os.getcwd())

try:
    from app.main import app
    print(f"SUCCESS: App created")
    print(f"Title: {app.title}")
    print(f"Routes: {len(app.routes)}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)