import 'dart:io';
import 'package:flutter/foundation.dart';

/// Storage helper for persisting and loading the user's custom server URL override.
///
/// Ensures that:
/// - Settings screen URL changes persist across app restarts.
/// - Fresh installs and release builds default to the production Render URL.
/// - Stale local dev URLs (e.g. 127.0.0.1:8000) do NOT override production in release mode.
class ServerUrlStorage {
  ServerUrlStorage._();

  static String? _inMemoryOverride;

  /// Check if a URL points to a local development machine or emulator.
  static bool isLocalUrl(String url) {
    final lower = url.trim().toLowerCase();
    return lower.contains('127.0.0.1') ||
        lower.contains('localhost') ||
        lower.contains('10.0.2.2') ||
        lower.contains('10.20.43.105') ||
        lower.startsWith('http://192.168.') ||
        lower.startsWith('http://10.');
  }

  static File _getStorageFile() {
    try {
      final baseDir = Directory.systemTemp;
      return File('${baseDir.path}${Platform.pathSeparator}medintel_server_url.txt');
    } catch (_) {
      return File('medintel_server_url.txt');
    }
  }

  /// Synchronously loads the saved URL if present and valid.
  static String? getSavedUrlSync() {
    if (_inMemoryOverride != null && _inMemoryOverride!.isNotEmpty) {
      if (kReleaseMode && isLocalUrl(_inMemoryOverride!)) {
        return null;
      }
      return _inMemoryOverride;
    }

    try {
      final file = _getStorageFile();
      if (file.existsSync()) {
        final content = file.readAsStringSync().trim();
        if (content.isNotEmpty) {
          // If in release mode and the file contains a local development URL,
          // ignore it so production is not hijacked on fresh installs or release upgrades.
          if (kReleaseMode && isLocalUrl(content)) {
            return null;
          }
          _inMemoryOverride = content;
          return content;
        }
      }
    } catch (_) {
      // Ignore filesystem access exceptions (e.g. sandboxed test harnesses)
    }
    return null;
  }

  /// Persists the active server URL to internal storage.
  static Future<void> saveUrl(String url) async {
    final sanitized = url.trim();
    _inMemoryOverride = sanitized;
    try {
      final file = _getStorageFile();
      await file.writeAsString(sanitized, flush: true);
    } catch (_) {
      // Non-fatal: in-memory override continues to work for the session.
    }
  }

  /// Resets the storage override.
  static Future<void> clear() async {
    _inMemoryOverride = null;
    try {
      final file = _getStorageFile();
      if (await file.exists()) {
        await file.delete();
      }
    } catch (_) {}
  }
}
