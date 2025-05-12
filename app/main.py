from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
import logging

from app.api.routes import auth, users, emotions, websockets
from app.database.database import create_tables, create_indexes, db, DB_NAME
import asyncio

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
# Set security module to DEBUG level for auth debugging
logging.getLogger('app.core.security').setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get environment settings
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app = FastAPI(
    title="Emotion Detection API",
    description="API for emotion detection and tracking with MongoDB",
    version="1.0.0",
    debug=DEBUG
)

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"]  # Expose all headers
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api", tags=["Users"])
app.include_router(emotions.router, prefix="/api", tags=["Emotions"])
app.include_router(websockets.router, prefix="/api", tags=["WebSockets"])

@app.on_event("startup")
async def startup_event():
    # Create database tables if they don't exist
    try:
        create_tables()
        # Create MongoDB indexes asynchronously
        await create_indexes()
        logger.info(f"Connected to MongoDB database: {DB_NAME}")
    except Exception as e:
        # Log the error but continue startup
        logger.error(f"Error initializing database: {str(e)}")
        logger.warning("Application starting with limited database functionality")
        # Don't re-raise the exception to allow the app to start

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """
    Root endpoint returning HTML landing page with API information
    """
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Emotion Detection API</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                line-height: 1.6;
                color: #333;
            }
            h1 {
                color: #2c3e50;
                border-bottom: 2px solid #eee;
                padding-bottom: 10px;
            }
            h2 {
                color: #3498db;
                margin-top: 30px;
            }
            .card {
                background-color: #f8f9fa;
                border-radius: 8px;
                padding: 20px;
                margin: 20px 0;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            a {
                color: #3498db;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
            .status {
                display: inline-block;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
                background-color: #2ecc71;
                color: white;
            }
            .mongo-badge {
                display: inline-block;
                padding: 4px 8px;
                border-radius: 4px;
                font-weight: bold;
                background-color: #13aa52;
                color: white;
                margin-left: 10px;
                font-size: 14px;
            }
        </style>
    </head>
    <body>
        <h1>Emotion Detection API <span class="mongo-badge">MongoDB</span></h1>
        <div class="status">API Online</div>
        
        <div class="card">
            <h2>API Documentation</h2>
            <p>Explore the available endpoints and how to use them:</p>
            <ul>
                <li><a href="/docs">Swagger UI Documentation</a></li>
                <li><a href="/redoc">ReDoc Documentation</a></li>
            </ul>
        </div>
        
        <div class="card">
            <h2>Features</h2>
            <ul>
                <li>User authentication with JWT tokens</li>
                <li>Real-time emotion updates via WebSockets</li>
                <li>Emotion tracking and storage</li>
                <li>RESTful API for emotion data access</li>
                <li>MongoDB for efficient document storage</li>
            </ul>
        </div>
        
        <div class="card">
            <h2>Getting Started</h2>
            <p>To use this API, you'll need to:</p>
            <ol>
                <li>Register a user account or login</li>
                <li>Use the JWT token for authenticated requests</li>
                <li>Connect to WebSockets for real-time updates</li>
            </ol>
            <p>Check out the <a href="/docs">documentation</a> for detailed information.</p>
        </div>
    </body>
    </html>
    """
    return html_content

@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring
    """
    return {"status": "healthy", "database": "MongoDB", "database_name": DB_NAME}

@app.get("/api/debug/request")
async def debug_request(request: Request):
    """
    Debug endpoint to return information about the request
    """
    headers = {k: v for k, v in request.headers.items()}
    return {
        "url": str(request.url),
        "method": request.method,
        "headers": headers,
        "client": {
            "host": request.client.host if request.client else None,
            "port": request.client.port if request.client else None
        },
        "path_params": request.path_params,
        "query_params": dict(request.query_params),
        "path": request.url.path,
        "server": {
            "host": request.url.hostname,
            "port": request.url.port
        }
    } 