import 'dart:async';
import 'dart:typed_data';

import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:yuv_to_png/yuv_to_png.dart';

/// ⚠️ MUST match backend IP
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
  Timer? _sendTimer;

  bool _cameraReady = false;
  bool _isConverting = false; // 🔐 lock for camera conversion
  Uint8List? _latestPngBytes;

  String? _latestAlertText;

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
          // Expecting JSON alerts only
          final data = msg is String ? msg : String.fromCharCodes(msg as Uint8List);
          final alertData = data.contains('alert') ? data : null;
          if (alertData != null) {
            setState(() {
              _latestAlertText = alertData;
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
      ResolutionPreset.low, // low res for performance
      enableAudio: false,
      imageFormatGroup: ImageFormatGroup.yuv420,
    );

    await _cam!.initialize();

    await _cam!.startImageStream((CameraImage image) {
      if (_isConverting) return; // drop frame if busy
      _isConverting = true;
       final png = _convertYuv420ToPng(image);

      try {
        final Uint8List? pngBytes = YuvToPng.yuvToPng(
          image,
          lensDirection: _cam!.description.lensDirection,
        );

        if (pngBytes != null) {
          _latestPngBytes = pngBytes; // store latest frame
        }
      } catch (e) {
        print("YUV to PNG error: $png");
      } finally {
        _isConverting = false;
      }
    });

    if (mounted) {
      setState(() => _cameraReady = true);
    }
  }

  Uint8List _convertYuv420ToPng(CameraImage image) {
  final width = image.width;
  final height = image.height;

  final yPlane = image.planes[0];
  final uPlane = image.planes[1];
  final vPlane = image.planes[2];



  for (int y = 0; y < height; y++) {
    for (int x = 0; x < width; x++) {
      final yp = y * yPlane.bytesPerRow + x;
      final uvIndex = (y ~/ 2) * uPlane.bytesPerRow + (x ~/ 2);

      final Y = yPlane.bytes[yp];
      final U = uPlane.bytes[uvIndex];
      final V = vPlane.bytes[uvIndex];

      int r = (Y + 1.402 * (V - 128)).round();
      int g = (Y - 0.344136 * (U - 128) - 0.714136 * (V - 128)).round();
      int b = (Y + 1.772 * (U - 128)).round();

      r = r.clamp(0, 255);
      g = g.clamp(0, 255);
      b = b.clamp(0, 255);

    }
  }

  return Uint8List.fromList([]);
}


  // ================= FRAME SENDER =================
  void _startSenderTimer() {
    _sendTimer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (_latestPngBytes == null) return;

      try {
        // Send raw PNG bytes directly
        _channel?.sink.add(_latestPngBytes!);
        print("Sent ${_latestPngBytes!.length} bytes");
      } catch (e) {
        print("Error sending frame: $e");
      }
    });
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
