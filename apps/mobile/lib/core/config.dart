import 'package:flutter/foundation.dart';
import 'dart:io';

class AppConfig {
  static String get baseUrl {
    // For web and desktop
    if (kIsWeb) return "http://localhost:8000";

    // For Android emulator
    if (Platform.isAndroid) {
      return "http://10.0.2.2:8000";
    }

    // For iOS simulator
    if (Platform.isIOS) return "http://127.0.0.1:8000";

    // For physical devices - USE YOUR PC's IP
    return "http://192.168.1.60:8000"; // ← CHANGED TO YOUR IP
  }
}