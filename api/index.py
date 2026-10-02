"""
Vercel Serverless Function Entrypoint
Exposes the FastAPI application instance for Vercel Python runtime.
"""
import sys
import os

# Add parent directory to path to enable relative imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
