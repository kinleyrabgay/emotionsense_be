"""
Emotion Detection API Routes
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Request
from fastapi.responses import JSONResponse, FileResponse
import logging
import cv2
import numpy as np
import os
import imutils
from datetime import datetime
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.models import load_model

from app.utils.emotion_detection import detect_emotion, EMOTIONS
from app.core.security import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

# Create debug directory
DEBUG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'debug')
os.makedirs(DEBUG_DIR, exist_ok=True)

@router.post("/detect", response_description="Detect emotions in an image")
async def detect_emotions_in_image(
    file: UploadFile = File(None),
    image: UploadFile = File(None),
    request: Request = None,
    user_id: str = None,
):
    """
    Detects emotions in the provided image.
    
    - **file** or **image**: An image file containing one or more faces
    - Or JSON with base64 image data: {"image": "base64_encoded_image_data", "user_id": "user_id_string"}
    - Optionally provide user_id to update user's emotion history
    
    Returns a JSON object with detected emotion and confidence.
    """
    try:
        # Get image bytes from the request
        image_bytes = None
        received_user_id = user_id
        
        # Check if we have a file (try both field names)
        if image and image.filename:
            image_bytes = await image.read()
        elif file and file.filename:
            image_bytes = await file.read()
        else:
            # Try to read and parse JSON body
            content_type = request.headers.get("content-type", "").lower()
            if "application/json" in content_type:
                try:
                    json_data = await request.json()
                    if "image" in json_data and json_data["image"]:
                        # Handle base64 encoded image data
                        base64_data = json_data["image"]
                        
                        # Remove data URL prefix if present
                        if "base64," in base64_data:
                            base64_data = base64_data.split("base64,")[1]
                            
                        import base64
                        try:
                            image_bytes = base64.b64decode(base64_data)
                        except Exception as e:
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Invalid base64 image data: {str(e)}"
                            )
                        
                        # Check for user_id in JSON
                        if not received_user_id and "user_id" in json_data:
                            received_user_id = json_data["user_id"]
                except ValueError:
                    pass  # Not valid JSON
            
            # If JSON parsing failed, try to read raw body data
            if not image_bytes:
                body = await request.body()
                if body:
                    image_bytes = body
        
        # If we still don't have image data, return an error
        if not image_bytes:
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
        
        current_time = datetime.utcnow().isoformat()
        
        # Prepare response with just the essential information
        if "faces" in result and len(result["faces"]) > 0:
            face = result["faces"][0]  # Get the first face
            emotion_name = face["emotion"]
            
            # Update user emotion history if user_id is provided
            user_updated = False
            if received_user_id:
                from app.models.user import Emotion as UserEmotion
                from app.services.user_service import UserService
                try:
                    # Get emotion enum from string
                    emotion_enum = getattr(UserEmotion, emotion_name.upper(), None)
                    if emotion_enum:
                        # Update user's emotion history with confidence
                        success = await UserService.update_emotion(received_user_id, emotion_enum, face["confidence"])
                        user_updated = success
                except Exception as e:
                    # Log but don't fail the request
                    logger.error(f"Error updating user emotion: {str(e)}")
            
            response = {
                "status": 200,
                "message": "Emotion detected successfully",
                "data": {
                    "emotion": emotion_name,
                    "confidence": face["confidence"],
                    "timestamp": current_time,
                    "user_updated": user_updated
                }
            }
        else:
            response = {
                "status": 200,
                "message": "No face detected in the image",
                "data": {
                    "emotion": "no_face",
                    "confidence": 0.0,
                    "timestamp": current_time,
                    "user_updated": False
                }
            }
            
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing request: {str(e)}"
        )

# @router.post("/simple-detect", response_description="Simple emotion detection for frontend testing")
# async def simple_detect(
#     file: UploadFile = File(...),
# ):
#     """
#     Simple emotion detection endpoint specifically designed for frontend testing.
#     It follows the example implementation closely to ensure compatibility.
#     """
#     try:
#         # Read image bytes
#         image_bytes = await file.read()
        
#         # Convert to numpy array
#         nparr = np.frombuffer(image_bytes, np.uint8)
#         frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
#         if frame is None:
#             return JSONResponse(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 content={"error": "Invalid image format"}
#             )
        
#         # Save original for debug
#         debug_dir = os.path.join(DEBUG_DIR, "simple_detect")
#         os.makedirs(debug_dir, exist_ok=True)
        
#         # Process exactly like example code
#         frame = imutils.resize(frame, width=300)
#         gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
#         # Use same cascade and parameters
#         cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
#         face_detection = cv2.CascadeClassifier(cascade_path)
        
#         faces = face_detection.detectMultiScale(
#             gray, 
#             scaleFactor=1.1, 
#             minNeighbors=5, 
#             minSize=(30, 30), 
#             flags=cv2.CASCADE_SCALE_IMAGE
#         )
        
#         # If no face found, return no_face
#         if len(faces) == 0:
#             current_time = datetime.utcnow().isoformat()
#             return JSONResponse(
#                 status_code=status.HTTP_200_OK,
#                 content={
#                     "status": 200,
#                     "message": "No face detected in the image",
#                     "data": {
#                         "emotion": "no_face",
#                         "confidence": 0.0,
#                         "timestamp": current_time
#                     }
#                 }
#             )
        
#         # Sort faces by size (largest first)
#         faces = sorted(faces, reverse=True, key=lambda x: (x[2] - x[0]) * (x[3] - x[1]))
#         (fX, fY, fW, fH) = faces[0]
        
#         # Extract the ROI
#         roi = gray[fY:fY + fH, fX:fX + fW]
#         roi = cv2.resize(roi, (64, 64))
        
#         # Preprocess for model
#         roi = roi.astype("float") / 255.0
#         roi = img_to_array(roi)
#         roi = np.expand_dims(roi, axis=0)
        
#         # Load model and predict
#         model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
#                               'assets', 'model', 'model.hdf5')
        
#         if not os.path.exists(model_path):
#             return JSONResponse(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 content={"error": f"Model file not found at {model_path}"}
#             )
        
#         # Load the model and predict
#         emotion_classifier = load_model(model_path, compile=False)
#         preds = emotion_classifier.predict(roi, verbose=0)[0]
        
#         # Get emotion label and probability
#         emotion_probability = float(np.max(preds))
#         emotion_label = EMOTIONS[np.argmax(preds)]
        
#         # Create probabilities dictionary for visualization
#         emotion_probs = {}
#         for i, emotion in enumerate(EMOTIONS):
#             emotion_probs[emotion] = float(preds[i])
        
#         # Return the result
#         current_time = datetime.utcnow().isoformat()
#         return JSONResponse(
#             status_code=status.HTTP_200_OK,
#             content={
#                 "status": 200,
#                 "message": "Emotion detected successfully",
#                 "data": {
#                     "emotion": emotion_label,
#                     "confidence": emotion_probability,
#                     "timestamp": current_time,
#                     "all_emotions": emotion_probs,
#                     "face_location": {
#                         "x": int(fX),
#                         "y": int(fY),
#                         "width": int(fW),
#                         "height": int(fH)
#                     }
#                 }
#             }
#         )
        
#     except Exception as e:
#         return JSONResponse(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             content={"error": f"Failed to process image: {str(e)}"}
#         )
async def simple_detect(
    file: UploadFile = File(...),
):
    """
    Simple emotion detection endpoint specifically designed for frontend testing.
    It follows the example implementation closely to ensure compatibility.
    """
    try:
        # Read image bytes
        image_bytes = await file.read()
        
        # Convert to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Invalid image format"}
            )
        
        # Save original for debug
        debug_dir = os.path.join(DEBUG_DIR, "simple_detect")
        os.makedirs(debug_dir, exist_ok=True)
        
        # Process exactly like example code
        frame = imutils.resize(frame, width=300)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Use same cascade and parameters
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        face_detection = cv2.CascadeClassifier(cascade_path)
        
        faces = face_detection.detectMultiScale(
            gray, 
            scaleFactor=1.1, 
            minNeighbors=5, 
            minSize=(30, 30), 
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        # If no face found, return no_face
        if len(faces) == 0:
            current_time = datetime.utcnow().isoformat()
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "status": 200,
                    "message": "No face detected in the image",
                    "data": {
                        "emotion": "no_face",
                        "confidence": 0.0,
                        "timestamp": current_time
                    }
                }
            )
        
        # Sort faces by size (largest first)
        faces = sorted(faces, reverse=True, key=lambda x: (x[2] - x[0]) * (x[3] - x[1]))
        (fX, fY, fW, fH) = faces[0]
        
        # Extract the ROI
        roi = gray[fY:fY + fH, fX:fX + fW]
        roi = cv2.resize(roi, (64, 64))
        
        # Preprocess for model
        roi = roi.astype("float") / 255.0
        roi = img_to_array(roi)
        roi = np.expand_dims(roi, axis=0)
        
        # Load model and predict
        model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
                              'assets', 'model', 'model.hdf5')
        
        if not os.path.exists(model_path):
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": f"Model file not found at {model_path}"}
            )
        
        # Load the model and predict
        emotion_classifier = load_model(model_path, compile=False)
        preds = emotion_classifier.predict(roi, verbose=0)[0]
        
        # Get emotion label and probability
        emotion_probability = float(np.max(preds))
        emotion_label = EMOTIONS[np.argmax(preds)]
        
        # Create probabilities dictionary for visualization
        emotion_probs = {}
        for i, emotion in enumerate(EMOTIONS):
            emotion_probs[emotion] = float(preds[i])
        
        # Return the result
        current_time = datetime.utcnow().isoformat()
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": 200,
                "message": "Emotion detected successfully",
                "data": {
                    "emotion": emotion_label,
                    "confidence": emotion_probability,
                    "timestamp": current_time,
                    "all_emotions": emotion_probs,
                    "face_location": {
                        "x": int(fX),
                        "y": int(fY),
                        "width": int(fW),
                        "height": int(fH)
                    }
                }
            }
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"Failed to process image: {str(e)}"}
        )
async def simple_detect(
    file: UploadFile = File(...),
):
    """
    Simple emotion detection endpoint specifically designed for frontend testing.
    It follows the example implementation closely to ensure compatibility.
    """
    try:
        # Read image bytes
        image_bytes = await file.read()
        
        # Convert to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Invalid image format"}
            )
        
        # Save original for debug
        debug_dir = os.path.join(DEBUG_DIR, "simple_detect")
        os.makedirs(debug_dir, exist_ok=True)
        
        # Process exactly like example code
        frame = imutils.resize(frame, width=300)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Use same cascade and parameters
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        face_detection = cv2.CascadeClassifier(cascade_path)
        
        faces = face_detection.detectMultiScale(
            gray, 
            scaleFactor=1.1, 
            minNeighbors=5, 
            minSize=(30, 30), 
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        # If no face found, return no_face
        if len(faces) == 0:
            current_time = datetime.utcnow().isoformat()
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "status": 200,
                    "message": "No face detected in the image",
                    "data": {
                        "emotion": "no_face",
                        "confidence": 0.0,
                        "timestamp": current_time
                    }
                }
            )
        
        # Sort faces by size (largest first)
        faces = sorted(faces, reverse=True, key=lambda x: (x[2] - x[0]) * (x[3] - x[1]))
        (fX, fY, fW, fH) = faces[0]
        
        # Extract the ROI
        roi = gray[fY:fY + fH, fX:fX + fW]
        roi = cv2.resize(roi, (64, 64))
        
        # Preprocess for model
        roi = roi.astype("float") / 255.0
        roi = img_to_array(roi)
        roi = np.expand_dims(roi, axis=0)
        
        # Load model and predict
        model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
                              'assets', 'model', 'model.hdf5')
        
        if not os.path.exists(model_path):
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": f"Model file not found at {model_path}"}
            )
        
        # Load the model and predict
        emotion_classifier = load_model(model_path, compile=False)
        preds = emotion_classifier.predict(roi, verbose=0)[0]
        
        # Get emotion label and probability
        emotion_probability = float(np.max(preds))
        emotion_label = EMOTIONS[np.argmax(preds)]
        
        # Create probabilities dictionary for visualization
        emotion_probs = {}
        for i, emotion in enumerate(EMOTIONS):
            emotion_probs[emotion] = float(preds[i])
        
        # Return the result
        current_time = datetime.utcnow().isoformat()
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": 200,
                "message": "Emotion detected successfully",
                "data": {
                    "emotion": emotion_label,
                    "confidence": emotion_probability,
                    "timestamp": current_time,
                    "all_emotions": emotion_probs,
                    "face_location": {
                        "x": int(fX),
                        "y": int(fY),
                        "width": int(fW),
                        "height": int(fH)
                    }
                }
            }
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"Failed to process image: {str(e)}"}
        )

@router.post("/test-face-detection", response_description="Test face detection only")
async def test_face_detection(
    file: UploadFile = File(...),
):
    """
    Test endpoint that processes an image and returns face detection results only.
    This helps diagnose if the issue is with face detection or emotion classification.
    """
    try:
        # Read the image
        image_bytes = await file.read()
        
        # Save the input image
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        input_path = os.path.join(DEBUG_DIR, f"test_input_{timestamp}.jpg")
        with open(input_path, "wb") as f:
            f.write(image_bytes)
        
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Could not decode image"}
            )
        
        # Create a copy for drawing on
        original_size = image.shape
        display_image = image.copy()
        
        # Resize for processing - but keep display image at original size
        image = imutils.resize(image, width=500)
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply histogram equalization to enhance contrast
        gray = cv2.equalizeHist(gray)
        
        # Create directory for cascade files if it doesn't exist
        cascade_dir = os.path.join(DEBUG_DIR, "cascades")
        os.makedirs(cascade_dir, exist_ok=True)
        
        # Use default face cascade
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        
        # Load face detector
        face_cascade = cv2.CascadeClassifier(cascade_path)
        
        # Check if cascade loaded correctly
        if face_cascade.empty():
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": f"Failed to load face cascade, check logs for details"}
            )
        
        # Try multiple parameter sets for face detection
        detection_results = []
        
        param_sets = [
            # Standard parameters
            {"scaleFactor": 1.1, "minNeighbors": 5, "minSize": (30, 30)},
            # More sensitive parameters
            {"scaleFactor": 1.05, "minNeighbors": 3, "minSize": (20, 20)},
            # Most sensitive parameters
            {"scaleFactor": 1.03, "minNeighbors": 2, "minSize": (15, 15)},
        ]
        
        # Detect with each parameter set and save results
        for i, params in enumerate(param_sets):
            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=params["scaleFactor"],
                minNeighbors=params["minNeighbors"],
                minSize=params["minSize"],
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            
            # Create a copy to draw faces for this parameter set
            result_image = image.copy()
            
            # Record results
            result_info = {
                "params": params,
                "faces_found": len(faces),
                "faces": []
            }
            
            # Draw rectangles around faces
            for (x, y, w, h) in faces:
                cv2.rectangle(result_image, (x, y), (x+w, y+h), (0, 255, 0), 2)
                result_info["faces"].append({
                    "x": int(x),
                    "y": int(y),
                    "width": int(w),
                    "height": int(h)
                })
            
            # Save result image
            result_path = os.path.join(DEBUG_DIR, f"test_result_{timestamp}_params{i}.jpg")
            cv2.imwrite(result_path, result_image)
            
            # Add path to results
            result_info["result_image_path"] = result_path
            detection_results.append(result_info)
        
        # Save grayscale and enhanced images too
        cv2.imwrite(os.path.join(DEBUG_DIR, f"test_gray_{timestamp}.jpg"), gray)
        
        # Create a composite result with all parameter sets
        # First get the best result (most faces, or first one if tie)
        best_result_idx = max(range(len(detection_results)), 
                             key=lambda i: detection_results[i]["faces_found"]) 
        best_params = detection_results[best_result_idx]["params"]
        best_faces = detection_results[best_result_idx]["faces"]
        
        # Draw on original sized image
        scale_factor = original_size[1] / 500  # width ratio
        for face in best_faces:
            x = int(face["x"] * scale_factor)
            y = int(face["y"] * scale_factor)
            w = int(face["width"] * scale_factor)
            h = int(face["height"] * scale_factor)
            cv2.rectangle(display_image, (x, y), (x+w, y+h), (0, 255, 0), 3)
            
        # Add text with parameters used
        params_text = f"Scale: {best_params['scaleFactor']}, Neighbors: {best_params['minNeighbors']}"
        cv2.putText(display_image, params_text, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.putText(display_image, f"Faces: {len(best_faces)}", (10, 70), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        # Save final display image
        final_path = os.path.join(DEBUG_DIR, f"test_final_{timestamp}.jpg")
        cv2.imwrite(final_path, display_image)
        
        # Return results and also the path to the result image for download
        response = {
            "detection_results": detection_results,
            "best_result": {
                "params": best_params,
                "faces_found": len(best_faces),
                "faces": best_faces
            },
            "image_paths": {
                "input": input_path,
                "final": final_path
            }
        }
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"Test failed: {str(e)}"}
        )

@router.get("/debug-image/{filename}", response_description="Get debug image")
async def get_debug_image(filename: str):
    """Get a debug image by filename"""
    filepath = os.path.join(DEBUG_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(filepath)

@router.post("/detect-anonymous", response_description="Detect emotions in an image without authentication")
async def detect_emotions_anonymous(
    file: UploadFile = File(None),
    image: UploadFile = File(None),
    request: Request = None,
    user_id: str = None,
):
    """
    Detects emotions in the provided image without requiring authentication.
    
    - **file** or **image**: An image file containing one or more faces
    - Or JSON with base64 image data: {"image": "base64_encoded_image_data", "user_id": "user_id_string"}
    - Optionally provide user_id to update user's emotion history
    
    Returns a JSON object with detected emotion and confidence.
    """
    try:
        # Get image bytes from the request
        image_bytes = None
        received_user_id = user_id
        
        # Check if we have a file (try both field names)
        if image and image.filename:
            image_bytes = await image.read()
        elif file and file.filename:
            image_bytes = await file.read()
        else:
            # Try to read and parse JSON body
            content_type = request.headers.get("content-type", "").lower()
            if "application/json" in content_type:
                try:
                    json_data = await request.json()
                    if "image" in json_data and json_data["image"]:
                        # Handle base64 encoded image data
                        base64_data = json_data["image"]
                        
                        # Remove data URL prefix if present
                        if "base64," in base64_data:
                            base64_data = base64_data.split("base64,")[1]
                            
                        import base64
                        try:
                            image_bytes = base64.b64decode(base64_data)
                        except Exception as e:
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Invalid base64 image data: {str(e)}"
                            )
                        
                        # Check for user_id in JSON
                        if not received_user_id and "user_id" in json_data:
                            received_user_id = json_data["user_id"]
                except ValueError:
                    pass  # Not valid JSON
            
            # If JSON parsing failed, try to read raw body data
            if not image_bytes:
                body = await request.body()
                if body:
                    image_bytes = body
        
        # If we still don't have image data, return an error
        if not image_bytes:
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
        
        current_time = datetime.utcnow().isoformat()
        
        # Prepare response with just the essential information
        if "faces" in result and len(result["faces"]) > 0:
            face = result["faces"][0]  # Get the first face
            emotion_name = face["emotion"]
            
            # Update user emotion history if user_id is provided
            user_updated = False
            if received_user_id:
                from app.models.user import Emotion as UserEmotion
                from app.services.user_service import UserService
                try:
                    # Get emotion enum from string
                    emotion_enum = getattr(UserEmotion, emotion_name.upper(), None)
                    if emotion_enum:
                        # Update user's emotion history with confidence
                        success = await UserService.update_emotion(received_user_id, emotion_enum, face["confidence"])
                        user_updated = success
                except Exception as e:
                    # Log but don't fail the request
                    logger.error(f"Error updating user emotion: {str(e)}")
            
            response = {
                "status": 200,
                "message": "Emotion detected successfully",
                "data": {
                    "emotion": emotion_name,
                    "confidence": face["confidence"],
                    "timestamp": current_time,
                    "user_updated": user_updated
                }
            }
        else:
            response = {
                "status": 200,
                "message": "No face detected in the image",
                "data": {
                    "emotion": "no_face",
                    "confidence": 0.0,
                    "timestamp": current_time,
                    "user_updated": False
                }
            }
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response
        )
        
    except HTTPException as e:
        # Re-raise HTTP exceptions to preserve status code
        raise
    except Exception as e:
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
        return JSONResponse(
            status_code=500,
            content={"error": f"Debug endpoint error: {str(e)}"}
        ) 