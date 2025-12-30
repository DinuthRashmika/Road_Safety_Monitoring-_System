import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:yuv_to_png/yuv_to_png.dart'; // Added import

/// ⚠️ MUST match StartTripScreen IP
String wsUrl(String sessionId, String token) =>
    'ws://192.168.8.174:8000/ws/sessions/$sessionId?token=$token';

class LiveMonitoringScreen extends StatefulWidget {
  final String sessionId;
  final String token;
  final String driverName;

  const LiveMonitoringScreen({
    super.key,
    required this.sessionId,
    required this.token,
    required this.driverName,
  });

  @override
  State<LiveMonitoringScreen> createState() => _LiveMonitoringScreenState();
}

class _LiveMonitoringScreenState extends State<LiveMonitoringScreen> {
  WebSocketChannel? _channel;
  StreamSubscription? _wsSub;

  CameraController? _cam;
  CameraImage? _latestImage;
  Timer? _sendTimer;

  bool _cameraReady = false;
  bool _isSending = false;
  String? _latestAlertText;

  // ================= INIT =================
  @override
  void initState() {
    super.initState();
    _connectWs();
    _initCamera();
    _startSenderTimer();
  }

  // ================= WEBSOCKET =================
  void _connectWs() {
    _channel = WebSocketChannel.connect(
      Uri.parse(wsUrl(widget.sessionId, widget.token)),
    );

    _wsSub = _channel!.stream.listen(
      (msg) {
        try {
          final data = jsonDecode(msg);
          if (data['alert'] is Map) {
            final alert = data['alert'];
            setState(() {
              _latestAlertText = _prettyAlert(
                alert['type']?.toString() ?? '',
                alert['confidence']?.toString() ?? '',
              );
            });
          }
        } catch (_) {}
      },
      onError: (_) => setState(() => _latestAlertText = 'Connection error'),
      onDone: () => setState(() => _latestAlertText = 'Disconnected'),
    );
  }

  // ================= CAMERA =================
  Future<void> _initCamera() async {
    final cams = await availableCameras();
    final frontCam = cams.firstWhere(
      (c) => c.lensDirection == CameraLensDirection.front,
      orElse: () => cams.first,
    );

    _cam = CameraController(
      frontCam,
      ResolutionPreset.low,
      enableAudio: false,
      imageFormatGroup: ImageFormatGroup.yuv420,
    );

    await _cam!.initialize();

    await _cam!.startImageStream((image) {
      _latestImage = image;
    });

    if (mounted) setState(() => _cameraReady = true);
  }

  // ================= YUV TO PNG CONVERSION (USING yuv_to_png) =================
  Future<Uint8List?> _convertYuvToPng(CameraImage cameraImage) async {
    try {
      if (_cam == null || !_cam!.value.isInitialized) return null;
      
      // Convert YUV to PNG using the yuv_to_png package
      Uint8List pngBytes = YuvToPng.yuvToPng(
        cameraImage,
        lensDirection: _cam!.description.lensDirection,
      );
      return pngBytes;
    } catch (e) {
      print("Error converting YUV to PNG: $e");
      return null;
    }
  }

  // ================= CONVERT BYTES TO BASE64 =================
  String _convertBytesToBase64(Uint8List bytes) {
    String base64Image = base64Encode(bytes);
    // Optional: Add MIME type prefix for web/API compatibility
    // String base64WithPrefix = "data:image/png;base64,$base64Image";
    return base64Image;
  }

  // ================= PROCESS CAMERA IMAGE AND GET BASE64 =================
  Future<String?> _processCameraImageAndGetBase64() async {
    if (_latestImage == null || _cam == null) return null;

    // 1. Convert YUV to PNG bytes
    Uint8List? pngBytes = await _convertYuvToPng(_latestImage!);

    if (pngBytes != null) {
      // 2. Encode PNG bytes to Base64 string
      String base64String = _convertBytesToBase64(pngBytes);
      
      // DEBUG: Print first few characters to verify
      print("Base64 Image String length: ${base64String.length}");
      print("First 50 chars: ${base64String.substring(0, min(50, base64String.length))}");
      
      return base64String;
    } else {
      return null;
    }
  }

  // Helper function to get minimum of two numbers
  int min(int a, int b) => a < b ? a : b;

  // ================= FRAME SENDER (1 FPS SAFE) =================
  void _startSenderTimer() {
    _sendTimer = Timer.periodic(const Duration(seconds: 1), (_) async {
      if (_isSending || _latestImage == null || _cam == null) return;

      _isSending = true;
      final ts = DateTime.now().millisecondsSinceEpoch / 1000;

      try {
        // Get Base64 string directly using yuv_to_png
        String? base64Image = await _processCameraImageAndGetBase64();

        if (base64Image != null) {
          // Send to websocket
          _channel?.sink.add(jsonEncode({
            'frame': base64Image,
            'format': 'png', // Changed from 'jpg' to 'png'
            'ts': ts,
          }));
        } else {
          print('Failed to convert image to base64');
        }
      } catch (e) {
        print('Frame send error: $e');
      } finally {
        _isSending = false;
      }
    });
  }

  // ================= ALERT TEXT =================
  String _prettyAlert(String type, String conf) {
    switch (type.toLowerCase()) {
      case 'seatbelt':
        return 'Seatbelt violation ($conf)';
      case 'phone':
        return 'Phone usage detected ($conf)';
      case 'drowsiness':
        return 'Drowsiness detected';
      default:
        return 'Alert: $type ($conf)';
    }
  }

  // ================= STOP =================
  void _stopSession() {
    _sendTimer?.cancel();
    _wsSub?.cancel();
    _channel?.sink.close();
    _cam?.stopImageStream();
    _cam?.dispose();
    Navigator.pop(context);
  }

  @override
  void dispose() {
    _stopSession();
    super.dispose();
  }

  // ================= UI =================
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Monitoring Active'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios),
          onPressed: _stopSession,
        ),
      ),
      body: Column(
        children: [
          const SizedBox(height: 16),
          AspectRatio(
            aspectRatio: 1,
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(24),
                child: _cameraReady && _cam != null
                    ? CameraPreview(_cam!)
                    : const Center(child: CircularProgressIndicator()),
              ),
            ),
          ),
          if (_latestAlertText != null)
            Container(
              margin: const EdgeInsets.all(16),
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: Colors.red.shade100,
                borderRadius: BorderRadius.circular(24),
              ),
              child: Row(
                children: [
                  const Icon(Icons.warning, color: Colors.red),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      _latestAlertText!,
                      style: const TextStyle(
                        color: Colors.red,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }
}