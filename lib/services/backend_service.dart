import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class BackendService {
  static const String _prefsKeyBaseUrl = 'backend_base_url';
  static const String defaultBaseUrl = 'http://10.0.2.2:8000';

  static String _baseUrl = defaultBaseUrl;

  static Future<void> init() async {
    final prefs = await SharedPreferences.getInstance();
    _baseUrl = prefs.getString(_prefsKeyBaseUrl) ?? defaultBaseUrl;
  }

  static String get baseUrl => _baseUrl;

  static Future<void> setBaseUrl(String url) async {
    _baseUrl = url;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_prefsKeyBaseUrl, _baseUrl);
  }

  static Uri _uri(String path) => Uri.parse('$_baseUrl$path');

  static Future<bool> pingHealth() async {
    try {
      final res = await http.get(_uri('/health')).timeout(const Duration(seconds: 3));
      if (res.statusCode == 200) {
        final data = json.decode(res.body);
        return data is Map && data['status'] == 'ok';
      }
      return false;
    } catch (_) {
      return false;
    }
  }
}


