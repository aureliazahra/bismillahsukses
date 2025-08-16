import 'dart:async';
import 'dart:typed_data';
import 'package:http/http.dart' as http;

class MjpegService {
  static const Duration _defaultRefreshRate = Duration(milliseconds: 100);

  /// Creates an MJPEG stream that properly parses the multipart stream
  static Stream<Uint8List> createMjpegStream(
    String url, {
    Duration timeout = const Duration(seconds: 10),
    Duration refreshRate = _defaultRefreshRate,
  }) {
    final controller = StreamController<Uint8List>();
    
    Timer.periodic(refreshRate, (timer) async {
      try {
        final response = await http.get(
          Uri.parse(url),
          headers: {
            'Accept': 'multipart/x-mixed-replace, image/jpeg',
            'Connection': 'keep-alive',
          },
        ).timeout(timeout);

        if (response.statusCode == 200 && response.bodyBytes.isNotEmpty) {
          // Parse MJPEG multipart response
          final frames = _parseMjpegResponse(response.bodyBytes);
          for (final frame in frames) {
            if (!controller.isClosed) {
              controller.add(frame);
            }
          }
        }
      } catch (e) {
        if (!controller.isClosed) {
          controller.addError(e);
        }
      }
    });

    return controller.stream;
  }

  /// Creates a simple frame-based stream for cameras that don't support proper MJPEG
  static Stream<Uint8List> createFrameStream(
    String url, {
    Duration timeout = const Duration(seconds: 5),
    Duration refreshRate = _defaultRefreshRate,
  }) {
    final controller = StreamController<Uint8List>();
    
    Timer.periodic(refreshRate, (timer) async {
      try {
        final response = await http.get(
          Uri.parse(url),
          headers: {
            'Accept': 'image/jpeg, image/png, */*',
          },
        ).timeout(timeout);

        if (response.statusCode == 200 && response.bodyBytes.isNotEmpty) {
          if (!controller.isClosed) {
            controller.add(response.bodyBytes);
          }
        }
      } catch (e) {
        if (!controller.isClosed) {
          controller.addError(e);
        }
      }
    });

    return controller.stream;
  }

  /// Parses MJPEG multipart response to extract individual frames
  static List<Uint8List> _parseMjpegResponse(Uint8List data) {
    final frames = <Uint8List>[];
    final boundary = _findBoundary(data);
    
    if (boundary == null) {
      // If no boundary found, treat as single image
      frames.add(data);
      return frames;
    }

    final parts = _splitByBoundary(data, boundary);
    for (final part in parts) {
      if (part.isNotEmpty) {
        final frame = _extractFrameFromPart(part);
        if (frame != null) {
          frames.add(frame);
        }
      }
    }

    return frames;
  }

  /// Finds the boundary string in the MJPEG response
  static String? _findBoundary(Uint8List data) {
    final dataString = String.fromCharCodes(data);
    final boundaryMatch = RegExp(r'boundary=([^\r\n]+)').firstMatch(dataString);
    return boundaryMatch?.group(1);
  }

  /// Splits the response by boundary
  static List<Uint8List> _splitByBoundary(Uint8List data, String boundary) {
    final boundaryBytes = '--$boundary'.codeUnits;
    final parts = <Uint8List>[];
    
    int startIndex = 0;
    for (int i = 0; i < data.length - boundaryBytes.length; i++) {
      bool found = true;
      for (int j = 0; j < boundaryBytes.length; j++) {
        if (data[i + j] != boundaryBytes[j]) {
          found = false;
          break;
        }
      }
      
      if (found) {
        if (startIndex < i) {
          parts.add(data.sublist(startIndex, i));
        }
        startIndex = i + boundaryBytes.length;
      }
    }
    
    if (startIndex < data.length) {
      parts.add(data.sublist(startIndex));
    }
    
    return parts;
  }

  /// Extracts the actual image data from a multipart part
  static Uint8List? _extractFrameFromPart(Uint8List part) {
    // Find the double CRLF that separates headers from content
    final doubleCrlf = [13, 10, 13, 10]; // \r\n\r\n
    int contentStart = -1;
    
    for (int i = 0; i < part.length - 3; i++) {
      if (part[i] == doubleCrlf[0] &&
          part[i + 1] == doubleCrlf[1] &&
          part[i + 2] == doubleCrlf[2] &&
          part[i + 3] == doubleCrlf[3]) {
        contentStart = i + 4;
        break;
      }
    }
    
    if (contentStart != -1 && contentStart < part.length) {
      return part.sublist(contentStart);
    }
    
    return null;
  }

  /// Tests if a URL supports proper MJPEG streaming
  static Future<bool> testMjpegSupport(String url) async {
    try {
      final response = await http.get(
        Uri.parse(url),
        headers: {
          'Accept': 'multipart/x-mixed-replace, image/jpeg',
        },
      ).timeout(const Duration(seconds: 5));

      if (response.statusCode == 200) {
        final contentType = response.headers['content-type'] ?? '';
        return contentType.contains('multipart/x-mixed-replace');
      }
    } catch (e) {
      print('Error testing MJPEG support: $e');
    }
    return false;
  }

  /// Creates the best available stream for a given camera URL
  static Stream<Uint8List> createOptimalStream(
    String url, {
    Duration timeout = const Duration(seconds: 10),
    Duration refreshRate = _defaultRefreshRate,
  }) async* {
    // First try to test MJPEG support
    final supportsMjpeg = await testMjpegSupport(url);
    
    if (supportsMjpeg) {
      yield* createMjpegStream(url, timeout: timeout, refreshRate: refreshRate);
    } else {
      yield* createFrameStream(url, timeout: timeout, refreshRate: refreshRate);
    }
  }
}
