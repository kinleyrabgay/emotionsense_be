# Real-Time Emotion Detection with WebSockets

This document explains how to use the WebSocket API for real-time emotion updates in the Emotion Detection application.

## Backend Implementation

The backend implements a WebSocket connection at `/api/ws` that requires authentication via a JWT token. This allows:

1. Real-time updates when a user's emotion changes
2. Multi-device synchronization (changes on one device reflect on others)
3. Efficient client-server communication

## Connection Workflow

### 1. Connect to the WebSocket

You can connect to the WebSocket endpoint using your JWT token in one of the following ways:

#### Option 1: Query Parameter
```
ws://your-server.com/api/ws?token=YOUR_JWT_TOKEN
```

#### Option 2: Authorization Header
Use the Authorization header with a Bearer token:
```
// Headers for connection
{
  "Authorization": "Bearer YOUR_JWT_TOKEN"
}
```

The token is the same one received from the login API.

### 2. Authentication

The server will:
- Validate your token
- Extract your user info
- Connect you to the real-time stream for your user

### 3. Message Types

#### From Server to Client:

- `connection_established`: Confirmation that you're connected
  ```json
  {
    "type": "connection_established",
    "message": "Connected to emotion detection WebSocket server",
    "timestamp": "2023-05-09T14:30:00.000Z",
    "user_id": "123"
  }
  ```

- `emotion_update`: Notification of an emotion change
  ```json
  {
    "type": "emotion_update",
    "user_id": "123",
    "emotion": "happy",
    "timestamp": "2023-05-09T14:35:00.000Z"
  }
  ```

- `error`: Error messages
  ```json
  {
    "type": "error",
    "message": "Invalid message format"
  }
  ```

#### From Client to Server:

- `ping`: Keep the connection alive
  ```json
  {
    "type": "ping",
    "timestamp": "2023-05-09T14:40:00.000Z"
  }
  ```

- `emotion_update`: Update your current emotion
  ```json
  {
    "type": "emotion_update",
    "emotion": "sad",
    "timestamp": "2023-05-09T14:45:00.000Z"
  }
  ```

## Flutter Integration

To implement the WebSocket connection in your Flutter app, you'll need to:

1. Add the `web_socket_channel` package to your `pubspec.yaml`:
   ```yaml
   dependencies:
     web_socket_channel: ^2.4.0
   ```

2. Create a WebSocket connection manager class:
   ```dart
   import 'dart:convert';
   import 'package:web_socket_channel/web_socket_channel.dart';
   import 'package:web_socket_channel/io.dart';

   class EmotionSocketManager {
     WebSocketChannel? _channel;
     bool _isConnected = false;
     String? _currentEmotion;
     final String _baseUrl;
     final String _token;
     final Function(String) _onEmotionUpdate;
     final Function(bool) _onConnectionStatusChange;

     // Constructor with required parameters
     EmotionSocketManager({
       required String baseUrl,
       required String token,
       required Function(String) onEmotionUpdate,
       required Function(bool) onConnectionStatusChange,
     }) : _baseUrl = baseUrl,
          _token = token,
          _onEmotionUpdate = onEmotionUpdate,
          _onConnectionStatusChange = onConnectionStatusChange;

     // Connect to the WebSocket server
     void connect() {
       try {
         // Option 1: Using query parameter
         final wsUrl = '$_baseUrl/api/ws?token=$_token';
         
         // Option 2: Using auth headers (uncomment to use this method)
         // final wsUrl = '$_baseUrl/api/ws';
         // final headers = {'Authorization': 'Bearer $_token'};
         // _channel = IOWebSocketChannel.connect(Uri.parse(wsUrl), headers: headers);
         
         _channel = IOWebSocketChannel.connect(wsUrl);
         
         // Process incoming messages
         _channel!.stream.listen(
           (dynamic message) {
             final data = jsonDecode(message);
             
             if (data['type'] == 'emotion_update') {
               _currentEmotion = data['emotion'];
               _onEmotionUpdate(_currentEmotion!);
             }
           },
           onDone: () {
             _isConnected = false;
             _onConnectionStatusChange(false);
           },
         );
         
         _isConnected = true;
         _onConnectionStatusChange(true);
       } catch (e) {
         _isConnected = false;
         _onConnectionStatusChange(false);
       }
     }

     // Send an emotion update
     void updateEmotion(String emotion) {
       if (_isConnected && _channel != null) {
         _channel!.sink.add(jsonEncode({
           'type': 'emotion_update',
           'emotion': emotion,
           'timestamp': DateTime.now().toIso8601String(),
         }));
       }
     }

     // Disconnect from the server
     void disconnect() {
       if (_channel != null) {
         _channel!.sink.close();
         _channel = null;
       }
       _isConnected = false;
       _onConnectionStatusChange(false);
     }
   }
   ```

## Testing WebSockets

You can test WebSocket connections using tools like:

1. [Postman](https://learning.postman.com/docs/sending-requests/supported-api-frameworks/websocket/)
2. [websocat](https://github.com/vi/websocat) command-line tool
3. Browser WebSocket clients

Example websocat commands:

Using query parameter:
```
websocat "ws://localhost:8000/api/ws?token=YOUR_JWT_TOKEN"
```

Using headers (Auth Bearer):
```
websocat -H="Authorization: Bearer YOUR_JWT_TOKEN" "ws://localhost:8000/api/ws"
```

## Security Considerations

1. Always use secured WebSockets (wss://) in production
2. The token in the query string is visible in server logs - using the Authorization header is more secure
3. Implement rate limiting to prevent DoS attacks 