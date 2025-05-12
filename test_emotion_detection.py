#!/usr/bin/env python
"""
Test script for emotion detection API
"""
import requests
import argparse
import json

def main():
    parser = argparse.ArgumentParser(description="Test the emotion detection API")
    parser.add_argument("image_path", help="Path to the image file to test")
    parser.add_argument("--url", default="http://localhost:8000/api/emotion-detection/detect-anonymous",
                        help="URL of the emotion detection API endpoint")
    
    args = parser.parse_args()
    
    # Open the image file
    try:
        with open(args.image_path, "rb") as image_file:
            # Prepare the file for uploading
            files = {
                "file": (args.image_path, image_file, "image/jpeg")
            }
            
            # Make the POST request to the API
            print(f"Sending image to {args.url}")
            response = requests.post(args.url, files=files)
            
            # Check if request was successful
            if response.status_code == 200:
                result = response.json()
                print("\nEmotion Detection Results:")
                print(f"Face detected: {result.get('face_detected', False)}")
                
                if result.get('face_detected', False):
                    print(f"Primary emotion: {result.get('emotion')}")
                    print(f"Confidence: {result.get('confidence', 0) * 100:.2f}%")
                    
                    print("\nAll emotions:")
                    emotions = result.get('all_emotions', {})
                    for emotion, prob in emotions.items():
                        print(f"  {emotion}: {prob * 100:.2f}%")
                else:
                    print("No face was detected in the image.")
                    
            else:
                print(f"Error: {response.status_code}")
                print(response.text)
    
    except FileNotFoundError:
        print(f"Error: Could not find the image file at {args.image_path}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 