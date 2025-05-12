"""
Emotion Detection API Routes
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status, Form, Request, Body
from fastapi.responses import JSONResponse, PlainTextResponse
import logging
from typing import Optional
import base64
import json

from app.utils.emotion_detection import detect_emotion
from app.core.security import get_current_user
# from app.schemas.user import User

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/detect", response_description="Detect emotions in an image")
async def detect_emotions_in_image(
    file: UploadFile = File(None),
    image: UploadFile = File(None),
    request: Request = None,
):
    """
    Detects emotions in the provided image.
    
    - **file** or **image**: An image file containing one or more faces
    
    Returns a JSON object with detected emotion and confidence.
    """
    try:
        logger.info(f"Processing emotion detection request")
        logger.info(f"Content-Type: {request.headers.get('content-type')}")
        
        # Get image bytes from the request
        image_bytes = None
        
        # Check if we have a file (try both field names)
        if image and image.filename:
            logger.info(f"Processing image field: {image.filename}, content_type: {image.content_type}")
            image_bytes = await image.read()
        elif file and file.filename:
            logger.info(f"Processing file field: {file.filename}, content_type: {file.content_type}")
            image_bytes = await file.read()
        else:
            # Try to read raw body data
            logger.info("No file found, trying to read raw body data")
            body = await request.body()
            if body:
                image_bytes = body
                logger.info(f"Read {len(body)} bytes from request body")
        
        # If we still don't have image data, return an error
        if not image_bytes:
            logger.error("No image data found in request")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No image data found in request"
            )
        
        # Process the image with the emotion detection model
        result = detect_emotion(image_bytes)
        
        # Check for errors
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
        
        # Prepare response with just the essential information
        if "faces" in result and len(result["faces"]) > 0:
            face = result["faces"][0]  # Get the first face
            response = {
                "emotion": face["emotion"],
                "confidence": face["confidence"]
            }
        else:
            response = {
                "emotion": "no_face",
                "confidence": 0.0
            }
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response
        )
        
    except HTTPException as e:
        # Re-raise HTTP exceptions to preserve status code
        raise
    except Exception as e:
        logger.error(f"Unexpected error in emotion detection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.post("/detect-anonymous", response_description="Detect emotions in an image without authentication")
async def detect_emotions_anonymous(
    file: UploadFile = File(None),
    image: UploadFile = File(None),
    request: Request = None,
):
    """
    Detects emotions in the provided image without requiring authentication.
    
    - **file** or **image**: An image file containing one or more faces
    
    Returns a JSON object with detected emotion and confidence.
    """
    try:
        logger.info("Processing anonymous emotion detection request")
        logger.info(f"Content-Type: {request.headers.get('content-type')}")
        
        # Get image bytes from the request
        image_bytes = None
        
        # Check if we have a file (try both field names)
        if image and image.filename:
            logger.info(f"Processing image field: {image.filename}, content_type: {image.content_type}")
            image_bytes = await image.read()
        elif file and file.filename:
            logger.info(f"Processing file field: {file.filename}, content_type: {file.content_type}")
            image_bytes = await file.read()
        else:
            # Try to read raw body data
            logger.info("No file found, trying to read raw body data")
            body = await request.body()
            if body:
                image_bytes = body
                logger.info(f"Read {len(body)} bytes from request body")
        
        # If we still don't have image data, return an error
        if not image_bytes:
            logger.error("No image data found in request")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No image data found in request"
            )
        
        # Process the image with the emotion detection model
        result = detect_emotion(image_bytes)
        
        # Check for errors
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
        
        # Prepare response with just the essential information
        if "faces" in result and len(result["faces"]) > 0:
            face = result["faces"][0]  # Get the first face
            response = {
                "emotion": face["emotion"],
                "confidence": face["confidence"]
            }
        else:
            response = {
                "emotion": "no_face",
                "confidence": 0.0
            }
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response
        )
        
    except HTTPException as e:
        # Re-raise HTTP exceptions to preserve status code
        raise
    except Exception as e:
        logger.error(f"Unexpected error in anonymous emotion detection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.post("/debug", response_description="Debug endpoint to inspect request data")
async def debug_request(request: Request):
    """
    Debug endpoint to inspect request data.
    Returns information about the request to help debug client-server integration.
    """
    try:
        # Get request headers
        headers = {k: v for k, v in request.headers.items()}
        
        # Try to read body
        body = await request.body()
        body_length = len(body) if body else 0
        
        # Read form data if possible
        form_data = {}
        if "multipart/form-data" in headers.get("content-type", ""):
            try:
                # We can't actually parse form data here since the body has been consumed
                # Just indicate it was multipart
                form_data = {"info": "Multipart form data detected"}
            except:
                form_data = {"error": "Could not parse form data"}
        
        # Prepare response
        debug_info = {
            "headers": headers,
            "body_length": body_length,
            "body_preview": str(body[:100]) if body else None,
            "form_data": form_data,
            "method": request.method,
            "url": str(request.url),
            "client": {"host": request.client.host, "port": request.client.port},
        }
        
        return JSONResponse(status_code=200, content=debug_info)
    
    except Exception as e:
        logger.error(f"Error in debug endpoint: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Debug endpoint error: {str(e)}"}
        ) 