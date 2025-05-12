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

logger = logging.getLogger(__name__)

# Emotion labels (from the reference code)
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
    logger.info(f"Emotion detection model loaded successfully from {MODEL_PATH}")
except Exception as e:
    logger.error(f"Failed to load emotion detection model: {str(e)}")
    emotion_classifier = None

def preprocess_image(image_bytes):
    """
    Preprocess the image bytes for emotion detection
    """
    try:
        # Convert image bytes to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        # Decode the image
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Resize the frame
        frame = imutils.resize(frame, width=300)
        
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces using Haar cascade
        faces = face_detection.detectMultiScale(
            gray, 
            scaleFactor=1.1, 
            minNeighbors=5, 
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        # If no faces are detected, return None
        if len(faces) == 0:
            return None, frame, []
        
        # Sort faces by size (largest face first)
        faces = sorted(faces, reverse=True, key=lambda x: (x[2] - x[0]) * (x[3] - x[1]))
        
        face_data = []
        face_locations = []
        
        # Process the largest face detected
        for face in faces:
            (fX, fY, fW, fH) = face
            face_locations.append((fX, fY, fW, fH))
            
            # Extract ROI of the face from grayscale image
            roi = gray[fY:fY + fH, fX:fX + fW]
            
            # Resize to expected input size (64x64 as per example)
            roi = cv2.resize(roi, (64, 64))
            
            # Preprocess for model
            roi = roi.astype("float") / 255.0
            roi = img_to_array(roi)
            roi = np.expand_dims(roi, axis=0)
            
            face_data.append(roi)
        
        return face_data, frame, face_locations
    
    except Exception as e:
        logger.error(f"Error preprocessing image: {str(e)}")
        return None, None, []

def detect_emotion(image_bytes):
    """
    Detect emotions in the provided image bytes
    
    Returns:
        A dict with detected emotion, confidence, and face location
    """
    if emotion_classifier is None:
        logger.error("Emotion detection model not loaded")
        return {"error": "Emotion detection model not loaded"}
    
    try:
        # Preprocess the image
        face_data, frame, face_locations = preprocess_image(image_bytes)
        
        if face_data is None or len(face_data) == 0:
            return {"faces": [], "message": "No faces detected in the image"}
        
        results = []
        
        # Process each face
        for i, roi in enumerate(face_data):
            # Predict emotions
            preds = emotion_classifier.predict(roi, verbose=0)[0]
            emotion_probability = float(np.max(preds))
            emotion_label = EMOTIONS[np.argmax(preds)]
            
            # Create a dictionary of emotions and their probabilities
            emotion_probabilities = {}
            for j, emotion in enumerate(EMOTIONS):
                emotion_probabilities[emotion] = float(preds[j])
            
            # Create a result dictionary for this face
            face_result = {
                "face_location": {
                    "x": int(face_locations[i][0]),
                    "y": int(face_locations[i][1]),
                    "width": int(face_locations[i][2]),
                    "height": int(face_locations[i][3])
                },
                "emotion": emotion_label,
                "confidence": emotion_probability,
                "emotion_probabilities": emotion_probabilities
            }
            
            results.append(face_result)
        
        return {
            "faces": results, 
            "message": f"{len(results)} face(s) detected"
        }
    
    except Exception as e:
        logger.error(f"Error detecting emotions: {str(e)}")
        return {"error": f"Failed to process image: {str(e)}"} 