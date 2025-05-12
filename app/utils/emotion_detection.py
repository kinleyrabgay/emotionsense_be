"""
Emotion detection utility functions
Using pre-trained model to detect emotions from images
"""
import os
import cv2
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array
import logging
import imutils

logger = logging.getLogger(__name__)

# Emotion labels must match the model's training labels
EMOTIONS = ["angry", "disgust", "scared", "happy", "sad", "surprised", "neutral"]

# Get the absolute path to the model file
MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                        'assets', 'model', 'model.hdf5')

# Path to the Haar cascade file for face detection
CASCADE_PATH = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'

# Load the face detection model
face_detection = cv2.CascadeClassifier(CASCADE_PATH)

# Load the emotion model only once when the module is imported
try:
    # Load model without compiling to avoid optimizer issues
    emotion_classifier = load_model(MODEL_PATH, compile=False)
except Exception as e:
    logger.error(f"Failed to load emotion detection model: {str(e)}")
    emotion_classifier = None

def detect_emotion(image_bytes):
    """
    Detect emotions in the provided image bytes
    
    Returns:
        A dict with detected emotion, confidence, and face location
    """
    if emotion_classifier is None:
        return {"error": "Emotion detection model not loaded"}
    
    try:
        # Convert image bytes to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        
        # Decode the image
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return {"error": "Failed to decode image"}
            
        # Resize frame to width 300 (same as example)
        frame = imutils.resize(frame, width=300)
        
        # Create debug directory
        debug_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'debug')
        os.makedirs(debug_dir, exist_ok=True)
        
        # Convert to grayscale exactly as in example
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces with same parameters as example
        faces = face_detection.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        # If no faces detected, try more relaxed parameters
        if len(faces) == 0:
            faces = face_detection.detectMultiScale(
                gray,
                scaleFactor=1.05,
                minNeighbors=3,
                minSize=(20, 20),
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            
            # If still no faces, use center of image as fallback
            if len(faces) == 0:
                h, w = gray.shape
                center_x = w // 4
                center_y = h // 4
                center_w = w // 2
                center_h = h // 2
                faces = np.array([[center_x, center_y, center_w, center_h]])
        
        # If we have faces now
        if len(faces) > 0:
            results = []
            
            # Sort faces by size (largest first) - exactly as in example
            if len(faces) > 1:
                faces = sorted(faces, reverse=True, 
                               key=lambda x: (x[2] - x[0]) * (x[3] - x[1]))
            
            # Process each face (or just the largest if multiple)
            face_idx = 0  # Start with largest face
            (fX, fY, fW, fH) = faces[face_idx]
            
            # Extract ROI and process exactly as in example
            roi = gray[fY:fY + fH, fX:fX + fW]
            
            # Resize to 64x64 as in example
            roi = cv2.resize(roi, (64, 64))
            
            # Normalize and convert to array format exactly as in example
            roi = roi.astype("float") / 255.0
            roi = img_to_array(roi)
            roi = np.expand_dims(roi, axis=0)
            
            # Predict emotion
            preds = emotion_classifier.predict(roi, verbose=0)[0]
            
            emotion_probability = float(np.max(preds))
            emotion_index = np.argmax(preds)
            emotion_label = EMOTIONS[emotion_index]
            
            # Create emotion probabilities dictionary
            emotion_probs = {}
            for i, emotion in enumerate(EMOTIONS):
                emotion_probs[emotion] = float(preds[i])
            
            # Create face result
            face_result = {
                "face_location": {
                    "x": int(fX),
                    "y": int(fY),
                    "width": int(fW),
                    "height": int(fH)
                },
                "emotion": emotion_label,
                "confidence": emotion_probability,
                "emotion_probabilities": emotion_probs
            }
            
            results.append(face_result)
            
            return {
                "faces": results,
                "message": f"{len(results)} face(s) detected"
            }
        else:
            return {"faces": [], "message": "No faces detected in the image"}
    
    except Exception as e:
        return {"error": f"Failed to process image: {str(e)}"} 