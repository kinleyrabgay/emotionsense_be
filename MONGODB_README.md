# MongoDB Implementation

This document explains the MongoDB integration in the Emotion Detection API.

## Overview

The application now uses MongoDB as its database, with the `pymongo` and `motor` libraries for asynchronous database operations. This implementation provides:

1. Better fit for the document-based data model
2. Easy scalability
3. Flexibility in schema evolution
4. Native support for arrays and nested objects

## Data Models

### User Model

```json
{
  "_id": ObjectId("..."),
  "name": "User Name",
  "email": "user@example.com",
  "password": "hashed_password",
  "profile": "profile_url",
  "currentEmotion": 4,  // Based on Emotion enum: 0=HAPPY, 1=SAD, 2=ANGRY, 3=SURPRISED, 4=NEUTRAL
  "isFaceAuthEnabled": false,
  "role": "employee",  // or "admin"
  "emotionHistory": [
    {
      "timestamp": ISODate("2023-09-15T14:30:00Z"),
      "emotion": 0  // HAPPY
    },
    {
      "timestamp": ISODate("2023-09-15T18:45:00Z"),
      "emotion": 1  // SAD
    }
  ],
  "createdAt": ISODate("2023-09-15T10:00:00Z"),
  "updatedAt": ISODate("2023-09-15T18:45:00Z"),
  "faceEncoding": BinData(0, "...")  // Binary face encoding data
}
```

### Emotion Model

```json
{
  "_id": ObjectId("..."),
  "userId": "user_id_string",
  "emotionType": 0,  // Based on Emotion enum
  "intensity": 8,  // Scale from 1-10
  "notes": "Feeling great today!",
  "recordedAt": ISODate("2023-09-15T14:30:00Z")
}
```

## Setup Instructions

### 1. Install MongoDB

**Mac OS X (using Homebrew):**
```bash
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
```

**Ubuntu:**
```bash
sudo apt-get install -y mongodb
sudo systemctl start mongodb
```

**Docker:**
```bash
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

### 2. Configure Environment

Update your `.env` file:
```
DATABASE_URL=mongodb://localhost:27017/emotion_detection
```

### 3. Install Python Dependencies

```bash
pip install motor pymongo
```

## Application Structure

- **Database Connection**: Using `motor.motor_asyncio.AsyncIOMotorClient` for async operations
- **Models**: Plain Python classes with `.to_dict()` and `.from_dict()` methods
- **Services**: Service classes that abstract database operations
- **APIs**: Fastify endpoints that use the services

## Indexes

The following indexes are created:

1. `{ "email": 1 }` (unique) on the users collection
2. `{ "userId": 1 }` on the emotions collection

## Migration Notes

If you're migrating from a previous SQL database:

1. The migration logic has been updated to work with MongoDB
2. Field names use camelCase in MongoDB but snake_case in the Python code
3. User emotion history is now embedded in the user document for faster retrieval 