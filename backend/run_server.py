#!/usr/bin/env python3
"""Run the FastAPI server from the backend directory."""
import sys
import os

# Ensure we're in the backend directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Add current directory to path for module imports
sys.path.insert(0, os.getcwd())

# Now import and run uvicorn
import uvicorn
from app.main import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)