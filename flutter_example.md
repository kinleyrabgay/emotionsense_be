// emotion_detection_service.dart
import 'dart:io';
import 'package:http/http.dart' as http;
import 'dart:convert';

class EmotionDetectionService {
  // Replace with your actual API endpoint
  static const String apiUrl = 'http://your-api-url/api/emotion-detection/detect-anonymous';
  
  /// Detects emotion from an image file
  /// Returns a Map with emotion and confidence
  static Future<Map<String, dynamic>> detectEmotion(File imageFile) async {
    try {
      // Create multipart request
      final request = http.MultipartRequest('POST', Uri.parse(apiUrl));
      
      // Add the image file
      final file = await http.MultipartFile.fromPath('file', imageFile.path);
      request.files.add(file);
      
      // Send the request
      final response = await request.send();
      
      // Get response as string
      final responseString = await response.stream.bytesToString();
      
      // Parse response JSON
      if (response.statusCode == 200) {
        return jsonDecode(responseString);
      } else {
        print('Error: ${response.statusCode} - $responseString');
        return {
          'emotion': 'error',
          'confidence': 0.0,
        };
      }
    } catch (e) {
      print('Exception during emotion detection: $e');
      return {
        'emotion': 'error',
        'confidence': 0.0,
      };
    }
  }
} 