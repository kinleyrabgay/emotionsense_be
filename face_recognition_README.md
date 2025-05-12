# Face Recognition Login

This document explains how to use the face recognition login feature in the Emotion Detection API.

## Overview

The Face Recognition login system allows users to authenticate using their face instead of a password. The system uses the `face_recognition` library (which uses dlib under the hood) to create and compare face encodings, with a fallback to OpenCV if the main library is not available.

## Technical Implementation

The system uses one of two approaches for face recognition:

1. **Primary Method**: The `face_recognition` library (which requires dlib).
2. **Fallback Method**: OpenCV's cascade classifier and image comparison if face_recognition is not available.

The system automatically selects the appropriate method based on the available libraries.

## Requirements

The face recognition system requires:

1. A good quality image of the user's face
2. Proper lighting conditions
3. A frontend application capable of capturing or uploading images

## API Endpoints

### 1. Enroll a Face

Before a user can log in with their face, they must enroll by providing a face image.

**Endpoint:** `POST /api/face/enroll`

**Authentication:** Requires JWT token (user must be logged in)

**Request:**
- A multipart form with an image file

**Response:**
```json
{
  "status": 200,
  "message": "Face enrolled successfully",
  "data": {
    "user_id": 1,
    "has_face_login": true
  }
}
```

### 2. Login with Face

Once enrolled, a user can log in using their face.

**Endpoint:** `POST /api/face/login`

**Authentication:** None (this is a login endpoint)

**Request:**
- A multipart form with:
  - An image file
  - `email` field containing the user's email

**Response:**
```json
{
  "authenticated": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user_data": {
    "id": 1,
    "name": "Test User",
    "email": "test@example.com",
    "current_emotion": "happy"
  },
  "message": "Face login successful"
}
```

### 3. Unenroll Face

Users can remove their face data from the system.

**Endpoint:** `DELETE /api/face/unenroll`

**Authentication:** Requires JWT token

**Response:**
```json
{
  "status": 200,
  "message": "Face login data removed successfully"
}
```

### 4. Check Face Login Status

Check if a user has face login enabled.

**Endpoint:** `GET /api/face/status`

**Authentication:** Requires JWT token

**Response:**
```json
{
  "status": 200,
  "message": "Face login status retrieved successfully",
  "data": {
    "has_face_login": true
  }
}
```

## Implementation in Flutter

To implement face recognition in your Flutter application, follow these steps:

### 1. Add Dependencies

```yaml
dependencies:
  camera: ^0.10.0+4
  dio: ^5.0.0
  path_provider: ^2.0.15
  http_parser: ^4.0.2
```

### 2. Create Face Recognition Service

```dart
class FaceRecognitionService {
  final Dio _dio = Dio();
  final String _baseUrl = 'https://your-api-url.com/api';
  
  // Set the JWT token for authenticated requests
  void setToken(String token) {
    _dio.options.headers["Authorization"] = "Bearer $token";
  }
  
  // Enroll face (requires authentication)
  Future<bool> enrollFace(File imageFile) async {
    try {
      FormData formData = FormData.fromMap({
        "image": await MultipartFile.fromFile(
          imageFile.path,
          filename: "face.jpg",
          contentType: MediaType('image', 'jpeg'),
        ),
      });
      
      final response = await _dio.post(
        '$_baseUrl/face/enroll',
        data: formData,
      );
      
      return response.data['status'] == 200;
    } catch (e) {
      print('Error enrolling face: $e');
      return false;
    }
  }
  
  // Login with face
  Future<Map<String, dynamic>?> loginWithFace(File imageFile, String email) async {
    try {
      FormData formData = FormData.fromMap({
        "image": await MultipartFile.fromFile(
          imageFile.path,
          filename: "face.jpg",
          contentType: MediaType('image', 'jpeg'),
        ),
        "email": email,
      });
      
      final response = await _dio.post(
        '$_baseUrl/face/login',
        data: formData,
      );
      
      if (response.data['authenticated']) {
        return {
          'token': response.data['token'],
          'user': response.data['user_data'],
        };
      } else {
        throw Exception(response.data['message']);
      }
    } catch (e) {
      print('Face login error: $e');
      return null;
    }
  }
  
  // Check if user has face login enabled
  Future<bool> hasFaceLoginEnabled() async {
    try {
      final response = await _dio.get('$_baseUrl/face/status');
      return response.data['data']['has_face_login'] ?? false;
    } catch (e) {
      print('Error checking face login status: $e');
      return false;
    }
  }
  
  // Remove face login data
  Future<bool> unenrollFace() async {
    try {
      final response = await _dio.delete('$_baseUrl/face/unenroll');
      return response.data['status'] == 200;
    } catch (e) {
      print('Error removing face login: $e');
      return false;
    }
  }
}
```

### 3. Capture Images in Flutter

```dart
class FaceCaptureScreen extends StatefulWidget {
  final Function(File) onImageCaptured;
  
  const FaceCaptureScreen({Key? key, required this.onImageCaptured}) : super(key: key);
  
  @override
  _FaceCaptureScreenState createState() => _FaceCaptureScreenState();
}

class _FaceCaptureScreenState extends State<FaceCaptureScreen> {
  late CameraController _controller;
  late Future<void> _initializeControllerFuture;
  bool _isCameraReady = false;
  
  @override
  void initState() {
    super.initState();
    _initCamera();
  }
  
  Future<void> _initCamera() async {
    final cameras = await availableCameras();
    // Use the front camera for face capture
    final frontCamera = cameras.firstWhere(
      (camera) => camera.lensDirection == CameraLensDirection.front,
      orElse: () => cameras.first,
    );
    
    _controller = CameraController(
      frontCamera,
      ResolutionPreset.medium,
    );
    
    _initializeControllerFuture = _controller.initialize();
    await _initializeControllerFuture;
    
    if (mounted) {
      setState(() {
        _isCameraReady = true;
      });
    }
  }
  
  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }
  
  Future<void> _captureImage() async {
    try {
      await _initializeControllerFuture;
      final image = await _controller.takePicture();
      widget.onImageCaptured(File(image.path));
    } catch (e) {
      print('Error capturing image: $e');
    }
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Face Capture')),
      body: _isCameraReady
          ? Column(
              children: [
                Expanded(
                  child: CameraPreview(_controller),
                ),
                Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Text(
                    'Position your face in the center of the frame and ensure good lighting',
                    textAlign: TextAlign.center,
                  ),
                ),
              ],
            )
          : Center(child: CircularProgressIndicator()),
      floatingActionButton: FloatingActionButton(
        onPressed: _captureImage,
        child: Icon(Icons.camera),
      ),
      floatingActionButtonLocation: FloatingActionButtonLocation.centerFloat,
    );
  }
}
```

### 4. Example Login Screen

```dart
class FaceLoginScreen extends StatefulWidget {
  @override
  _FaceLoginScreenState createState() => _FaceLoginScreenState();
}

class _FaceLoginScreenState extends State<FaceLoginScreen> {
  final TextEditingController _emailController = TextEditingController();
  final FaceRecognitionService _faceService = FaceRecognitionService();
  String? _errorMessage;
  bool _isLoading = false;
  
  Future<void> _startFaceCapture() async {
    if (_emailController.text.isEmpty) {
      setState(() {
        _errorMessage = 'Please enter your email first';
      });
      return;
    }
    
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (context) => FaceCaptureScreen(
          onImageCaptured: (File imageFile) async {
            Navigator.of(context).pop();
            await _loginWithFace(imageFile);
          },
        ),
      ),
    );
  }
  
  Future<void> _loginWithFace(File imageFile) async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });
    
    try {
      final result = await _faceService.loginWithFace(
        imageFile, 
        _emailController.text
      );
      
      if (result != null) {
        // Store token and navigate to home
        final String token = result['token'];
        // Navigate to home screen
      } else {
        setState(() {
          _errorMessage = 'Face login failed. Try again or use password.';
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = e.toString();
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Face Login')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            TextField(
              controller: _emailController,
              decoration: InputDecoration(
                labelText: 'Email',
                border: OutlineInputBorder(),
              ),
              keyboardType: TextInputType.emailAddress,
            ),
            SizedBox(height: 20),
            if (_errorMessage != null)
              Padding(
                padding: const EdgeInsets.only(bottom: 20),
                child: Text(
                  _errorMessage!,
                  style: TextStyle(color: Colors.red),
                ),
              ),
            ElevatedButton(
              onPressed: _isLoading ? null : _startFaceCapture,
              child: _isLoading
                  ? CircularProgressIndicator(color: Colors.white)
                  : Text('Login with Face'),
              style: ElevatedButton.styleFrom(
                minimumSize: Size(double.infinity, 50),
              ),
            ),
            TextButton(
              onPressed: () {
                // Navigate to password login
              },
              child: Text('Login with Password Instead'),
            ),
          ],
        ),
      ),
    );
  }
}
```

## Installation Notes

The face recognition feature has two possible implementations:

### Primary Method (preferred)

Uses the `face_recognition` library which requires:
- dlib (C++ library)
- cmake
- Compiler tools

If using this method, you'll need to install system dependencies:

**macOS:**
```bash
brew install cmake
brew install dlib
pip install face-recognition
```

**Ubuntu/Debian:**
```bash
apt-get update
apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev
pip install face-recognition
```

### Fallback Method

If you encounter issues installing the `face_recognition` library, the system will automatically fall back to using OpenCV:

```bash
pip install opencv-python
```

This fallback method is less accurate but requires fewer dependencies.

## Security Considerations

1. **HTTPS Required**: Always use HTTPS in production to protect image data during transmission.

2. **Face Encoding Storage**: Face encodings are stored securely in the database as binary data.

3. **Liveness Detection**: The current implementation does not include liveness detection, which could make it vulnerable to photo-based spoofing attacks. Consider implementing liveness detection in a production environment.

4. **Fall Back Authentication**: Always provide password-based authentication as a fallback.

5. **Permission Management**: Ensure your app has appropriate camera permissions and handles user consent properly.

## Troubleshooting

1. **Face Not Detected**: Ensure adequate lighting and proper face positioning. The face should be clearly visible and centered in the frame.

2. **Low Recognition Accuracy**: The default tolerance value is 0.6. You may adjust this in the backend for stricter or more lenient matching.

3. **Performance Issues**: Face recognition can be CPU-intensive. Consider optimizing image size before upload.

4. **Installation Problems**: The `face_recognition` library depends on `dlib`, which requires certain system dependencies. Refer to the library documentation for installation help. 