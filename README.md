# Emotion Detection API

Backend for the Emotion Detection application built with FastAPI and PostgreSQL.

## Features

- 🔐 User authentication with JWT tokens
- 🔄 Real-time updates with WebSockets
- 😀 Emotion tracking and storage
- 📱 RESTful API for emotion data access
- 👤 Face recognition login

## API Endpoints

- **Authentication**
  - POST `/api/auth/register` - Register a new user
  - POST `/api/auth/login` - Login and get JWT token
  - POST `/api/auth/refresh` - Refresh JWT token
  - GET `/api/auth/user/me` - Get current user profile

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

- **Face Recognition**
  - POST `/api/face/enroll` - Enroll face for login
  - POST `/api/face/login` - Login using face recognition
  - DELETE `/api/face/unenroll` - Remove face login data
  - GET `/api/face/status` - Check face login status

## Getting Started

### Prerequisites

- Python 3.9+
- PostgreSQL database

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
   DATABASE_URL=postgresql://user:password@localhost/emotion_detection
   SECRET_KEY=your_secret_key
   ACCESS_TOKEN_EXPIRE_MINUTES=1440
   ```

5. Run the application
   ```bash
   uvicorn app.main:app --reload
   ```

6. Access the API documentation at http://localhost:8000/docs

## Deployment

See [RENDER_DEPLOY.md](RENDER_DEPLOY.md) for instructions on deploying to Render.

## WebSockets

See [websocket_README.md](websocket_README.md) for WebSocket implementation details.

## Face Recognition

See [face_recognition_README.md](face_recognition_README.md) for details on the face recognition login feature.

## Database

The application uses PostgreSQL. In production, it's recommended to use a managed PostgreSQL service.

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