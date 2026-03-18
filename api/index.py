# api/index.py - Entry point for Vercel Serverless Functions
# This file wraps the FastAPI app to work with Vercel's Python runtime

from app.main import app

# Export the app instance for Vercel
# This is required by Vercel to find the ASGI application
handler = app
