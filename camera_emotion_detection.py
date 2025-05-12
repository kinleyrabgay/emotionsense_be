#!/usr/bin/env python
"""
Camera-based Emotion Detection Test
Captures video from the camera, takes a photo every 3 seconds,
sends it to the emotion detection API, and displays the results
"""
import cv2
import time
import requests
import numpy as np
import os
import argparse
from datetime import datetime
from io import BytesIO
import threading

def analyze_frame(frame, api_url):
    """
    Send a frame to the emotion detection API and return the result
    """
    try:
        # Convert frame to JPEG format
        _, buffer = cv2.imencode('.jpg', frame)
        
        # Prepare the file for uploading
        files = {
            "file": ("frame.jpg", buffer.tobytes(), "image/jpeg")
        }
        
        # Make the POST request to the API
        response = requests.post(api_url, files=files, timeout=5)
        
        # Return the result if successful
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error from API: {response.status_code}")
            print(response.text)
            return None
    
    except Exception as e:
        print(f"Error sending frame to API: {str(e)}")
        return None

def draw_emotion_results(frame, result):
    """
    Draw emotion detection results on the frame
    """
    if not result:
        return frame
    
    # Get frame dimensions
    frame_h, frame_w = frame.shape[:2]
    
    # Create a copy of the frame to draw on
    overlay = frame.copy()
    
    # Make the panel wider
    panel_width = 280  # Increased from 220
    panel_height = frame_h
    panel_x = frame_w - panel_width
    
    # Create dark panel background
    cv2.rectangle(overlay, (panel_x, 0), (frame_w, frame_h), (20, 20, 30), -1)
    
    # Add transparency
    alpha = 0.8  # Increased opacity for better readability
    frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)
    
    # Add title to panel with bigger font
    cv2.putText(frame, "EMOTION ANALYSIS", (panel_x + 15, 35), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    
    # Add horizontal line below title
    cv2.line(frame, (panel_x + 15, 50), (frame_w - 15, 50), (200, 200, 200), 2)
    
    if result.get('face_detected', False):
        # Get face location
        face_loc = result.get('face_location', {})
        x = face_loc.get('x', 0)
        y = face_loc.get('y', 0)
        w = face_loc.get('width', 0)
        h = face_loc.get('height', 0)
        
        # Make sure face box doesn't overlap with info panel
        if x + w > panel_x:
            # If face box overlaps with panel, adjust the display
            # Just draw box up to the panel edge
            actual_width = min(w, panel_x - x)
            cv2.rectangle(frame, (x, y), (x + actual_width, y + h), (0, 255, 0), 2)
        else:
            # Draw regular rectangle around face
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        # Draw emotion label above the face, ensuring it doesn't overlap with panel
        emotion = result.get('emotion', 'unknown')
        confidence = result.get('confidence', 0) * 100
        label = f"{emotion}: {confidence:.1f}%"
        
        # Adjust label position to avoid panel overlap
        label_width = len(label) * 12  # Approximate width of text
        label_x = x
        if x + label_width > panel_x:
            label_x = max(0, panel_x - label_width - 10)
        
        # Add a dark background for label text with larger size
        text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
        cv2.rectangle(frame, (label_x, y - 35), (label_x + text_size[0] + 10, y - 5), (0, 0, 0), -1)
        cv2.putText(frame, label, (label_x + 5, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
        # Display emotions in the info panel with larger text
        cv2.putText(frame, "Status:", (panel_x + 15, 90), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (150, 150, 150), 1)
        cv2.putText(frame, "FACE DETECTED", (panel_x + 90, 90), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Primary emotion with larger text
        cv2.putText(frame, "Primary Emotion:", (panel_x + 15, 125), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (150, 150, 150), 1)
        cv2.putText(frame, emotion.upper(), (panel_x + 15, 155), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
        
        # Confidence with larger display
        cv2.putText(frame, f"Confidence: {confidence:.1f}%", (panel_x + 15, 190), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
        
        # Add horizontal line
        cv2.line(frame, (panel_x + 15, 210), (frame_w - 15, 210), (150, 150, 150), 2)
        
        # Display all emotions in the panel
        cv2.putText(frame, "ALL EMOTIONS:", (panel_x + 15, 240), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 255), 1)
        
        y_offset = 270
        emotions = result.get('all_emotions', {})
        for emotion_name, prob in emotions.items():
            # Create a bar chart for each emotion
            bar_length = int(prob * 180)  # Scale probability to max bar length
            
            # Draw emotion name with larger font
            cv2.putText(frame, f"{emotion_name}:", (panel_x + 15, y_offset), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (220, 220, 220), 1)
            
            # Draw bar background - make it taller and wider
            cv2.rectangle(frame, (panel_x + 15, y_offset + 7), (panel_x + 200, y_offset + 22), (50, 50, 50), -1)
            
            # Draw actual value bar - make it taller
            color = (0, 255, 0)  # Green for high values
            if prob < 0.3:
                color = (0, 165, 255)  # Orange for low values
            elif prob < 0.6:
                color = (0, 255, 255)  # Yellow for medium values
                
            cv2.rectangle(frame, (panel_x + 15, y_offset + 7), (panel_x + 15 + bar_length, y_offset + 22), color, -1)
            
            # Draw percentage text with better contrast and larger font
            percentage_text = f"{prob * 100:.1f}%"
            text_x = panel_x + 220  # Fixed position for percentage text
            # Add background for percentage text
            text_size = cv2.getTextSize(percentage_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)[0]
            cv2.rectangle(frame, (text_x - 5, y_offset - 5), (text_x + text_size[0] + 5, y_offset + 15), (20, 20, 20), -1)
            cv2.putText(frame, percentage_text, (text_x, y_offset + 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
            y_offset += 40  # Increase spacing between emotions
    else:
        # Display "No face detected" message in the info panel with larger text
        cv2.putText(frame, "Status:", (panel_x + 15, 90), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (150, 150, 150), 1)
        cv2.putText(frame, "NO FACE DETECTED", (panel_x + 90, 90), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    # Add help text at the bottom of panel
    cv2.putText(frame, "Press 'q' to quit", (panel_x + 15, frame_h - 25), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
    
    return frame

def main():
    parser = argparse.ArgumentParser(description="Camera-based Emotion Detection")
    parser.add_argument("--url", default="http://localhost:8000/api/emotion-detection/detect-anonymous",
                        help="URL of the emotion detection API endpoint")
    parser.add_argument("--interval", type=float, default=3.0,
                        help="Interval between API calls in seconds")
    parser.add_argument("--camera", type=int, default=0,
                        help="Camera index (default is 0)")
    
    args = parser.parse_args()
    
    # Initialize the camera
    cap = cv2.VideoCapture(args.camera)
    
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return
    
    print(f"Starting camera feed with emotion detection every {args.interval} seconds")
    print(f"API URL: {args.url}")
    print("Press 'q' to quit")
    
    # Initialize variables
    last_analysis_time = 0
    current_result = None
    analysis_in_progress = False
    
    def analyze_in_background(frame):
        nonlocal current_result, analysis_in_progress
        result = analyze_frame(frame, args.url)
        current_result = result
        analysis_in_progress = False
    
    # Main loop
    while True:
        # Capture frame
        ret, frame = cap.read()
        
        if not ret:
            print("Failed to grab frame")
            break
        
        # Flip horizontally for a mirror effect
        frame = cv2.flip(frame, 1)
        
        # Check if it's time to analyze a new frame
        current_time = time.time()
        if (current_time - last_analysis_time >= args.interval) and not analysis_in_progress:
            last_analysis_time = current_time
            analysis_in_progress = True
            
            # Create a copy of the current frame for analysis
            analysis_frame = frame.copy()
            
            # Start analysis in a separate thread
            analysis_thread = threading.Thread(target=analyze_in_background, args=(analysis_frame,))
            analysis_thread.daemon = True
            analysis_thread.start()
            
            # Get frame dimensions for the analyzing message
            frame_h, frame_w = frame.shape[:2]
            panel_width = 280
            panel_x = frame_w - panel_width
            
            # Create a copy of the frame to draw on for the panel
            overlay = frame.copy()
            
            # Create dark panel background
            cv2.rectangle(overlay, (panel_x, 0), (frame_w, frame_h), (20, 20, 30), -1)
            
            # Add transparency
            alpha = 0.8
            frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)
            
            # Display "Analyzing..." message in the info panel
            cv2.putText(frame, "EMOTION ANALYSIS", (panel_x + 15, 35), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.line(frame, (panel_x + 15, 50), (frame_w - 15, 50), (200, 200, 200), 2)
            cv2.putText(frame, "Status: Analyzing...", (panel_x + 15, 90), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 1)
            
            # Add help text at the bottom of panel
            cv2.putText(frame, "Press 'q' to quit", (panel_x + 15, frame_h - 25), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        
        # Draw results on the frame if available
        if current_result:
            frame = draw_emotion_results(frame, current_result)
        
        # Display the frame
        cv2.imshow("Emotion Detection", frame)
        
        # Check for 'q' key to exit
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
    
    # Release resources
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main() 