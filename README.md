# Emotion Detection API

Backend for the Emotion Detection application built with FastAPI and MongoDB.

## Features

- 🔐 User authentication with JWT tokens
- 🔄 Real-time updates with WebSockets
- 😀 Emotion tracking and storage
- 📱 RESTful API for emotion data access
- 🗄️ MongoDB for efficient document storage
- 🧠 AI-powered emotion detection from images

## API Endpoints

- **Authentication**
  - POST `/api/auth/register` - Register a new user
  - POST `/api/auth/login` - Login and get JWT token
  - GET `/api/auth/me` - Get current user profile
  - POST `/api/auth/logout` - Logout (clears auth cookies)

- **Users**
  - GET `/api/users/me` - Get current user profile
  - GET `/api/users/{user_id}` - Get user by ID
  - PATCH `/api/users/me/emotion` - Update current user's emotion

- **Emotions**
  - GET `/api/emotions/` - Get emotions for current user
  - POST `/api/emotions/` - Create a new emotion entry
  - GET `/api/emotions/{emotion_id}` - Get specific emotion entry
  - DELETE `/api/emotions/{emotion_id}` - Delete an emotion entry

- **WebSockets**
  - WebSocket `/api/ws` - Real-time emotion updates

- **Emotion Detection** (AI-powered)
  - POST `/api/emotion-detection/detect` - Detect emotions in an uploaded image (authenticated)
  - POST `/api/emotion-detection/detect-anonymous` - Detect emotions without authentication

## Getting Started

### Prerequisites

- Python 3.9+
- MongoDB database (local or MongoDB Atlas)

### Installation

1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/emotion-detection-backend.git
   cd emotion-detection-backend
   ```

2. Create a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables
   Create a `.env` file in the root directory with:
   ```
   DATABASE_URL=mongodb+srv://username:password@cluster.mongodb.net/dbname
   SECRET_KEY=your_secret_key
   ACCESS_TOKEN_EXPIRE_MINUTES=1440
   ```

5. Run the application
   ```bash
   uvicorn app.main:app --reload
   ```

6. Access the API documentation at http://localhost:8000/docs

## Deployment to Render

This application is configured for deployment on [Render](https://render.com).

### Deployment Files

- `render.yaml` - Render configuration for web service and database
- `build.sh` - Build script to install dependencies and run migrations
- `main.py` - Entry point for the application
- `Procfile` - Alternative startup command specification

### Deploying to Render

1. Fork this repository to your GitHub account
2. Create a new Render account or log in
3. Click "New" and select "Blueprint" from your Render dashboard
4. Connect your GitHub account and select your fork of this repository
5. Render will automatically detect the `render.yaml` file and set up your services
6. Provide the required environment variables:
   - `DATABASE_URL` - MongoDB connection string (Render can provide a MongoDB instance)
   - `SECRET_KEY` - Secret key for JWT token signing
   - `ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiration time in minutes (e.g., 1440 for 24 hours)
7. Deploy your application

## WebSockets

See [websocket_README.md](websocket_README.md) for WebSocket implementation details.

## Database

The application uses MongoDB for data storage. In production, it's recommended to use MongoDB Atlas.

## AI Emotion Detection

The API includes AI-powered emotion detection based on the [Emotion Recognition model](https://github.com/kinleyrabgay/Emotion-recognition/tree/master).

### How it works

1. Upload an image with one or more faces
2. The API detects faces using OpenCV
3. Each face is processed through a pre-trained deep learning model
4. The API returns the detected emotion and confidence level

### Using the Emotion Detection API

#### Request

```
POST /api/emotion-detection/detect-anonymous
Content-Type: multipart/form-data

file: [binary image data]
```

#### Response

```json
{
  "emotion": "happy",
  "confidence": 0.92
}
```

If no face is detected, you'll get:

```json
{
  "emotion": "no_face",
  "confidence": 0.0
}
```

### Testing the Emotion Detection API

Use the included `test_emotion_detection.py` script to test the API:

```bash
python test_emotion_detection.py path/to/your/image.jpg
```

### Supported Emotions

- angry
- disgust
- scared
- happy
- sad
- surprised
- neutral

## Development

### Testing

```bash
pytest
```

### Code Formatting

```bash
black app
```

## License

This project is licensed under the MIT License - see the LICENSE file for details. 