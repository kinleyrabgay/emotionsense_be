"""
Main module for Render deployment
"""
# Import the FastAPI app from the app package
from app.main import app

# This file exists solely to satisfy Render's default startup command
# The actual app is defined in app/main.py

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 