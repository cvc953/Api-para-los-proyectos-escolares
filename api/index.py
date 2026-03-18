# api/index.py - Entry point for Vercel Serverless Functions
# This file wraps the FastAPI app to work with Vercel's Python runtime

import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app as application

# For Vercel, export the app as 'app'
app = application
