#!/usr/bin/env python3
"""Standalone server test - no uvicorn reload"""
import sys
import os

# Change to backend directory
os.chdir('Z:/horgame/f1/rag/backend')
sys.path.insert(0, '.')

# Force no reload
from app.main import app

if __name__ == "__main__":
    import uvicorn
    print("Starting server on http://0.0.0.0:8000")
    uvicorn.run(app, host='0.0.0.0', port=8000, log_level="info", reload=False)