import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';
import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:image/image.dart' as img;
import 'package:web_socket_channel/web_socket_channel.dart';

const String kTinyWebPBase64 =
    'UklGRlIAAABXRUJQVlA4WAoAAAABAAAAAQAAAQAAQUxQSCwAAAA='; // fallback sample

String wsUrl(String sessionId, String token) =>
    'ws://127.0.0.1:8000/ws/sessions/$sessionId?token=$token';

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
  WebSocketChannel? _ch;
  StreamSubscription? _wsSub;

  CameraController? _cam;
  bool _cameraReady = false;

  String? _latestAlertText;

  // exact 2 fps sender: keep latest frame and a periodic timer
  CameraImage? _latestImage;
  Timer? _sendTimer;

  @override
  void initState() {
    super.initState();
    _connectWs();
    _initCamera();
    _startSenderTimer(); // fires every 500ms
  }

  // ------------------ WebSocket ------------------
  void _connectWs() {
    final url = wsUrl(widget.sessionId, widget.token);
    _ch = WebSocketChannel.connect(Uri.parse(url));

    _wsSub = _ch!.stream.listen(
      (msg) {
        try {
          final Map data =
              (msg is String) ? jsonDecode(msg) : jsonDecode(utf8.decode(msg as List<int>));
          if (data['alert'] is Map) {
            final a = data['alert'] as Map;
            final type = (a['type'] ?? '').toString().toLowerCase();
            final conf = (a['confidence'] ?? '').toString();
            setState(() => _latestAlertText = _prettyAlert(type, conf));
          }
        } catch (_) {}
      },
      onError: (_) => setState(() => _latestAlertText = 'Connection error'),
      onDone: () => setState(() => _latestAlertText = 'Disconnected'),
    );
  }

  // ------------------ Camera ------------------
  Future<void> _initCamera() async {
    try {
      final cams = await availableCameras();
      CameraDescription desc = cams.first;
      for (final c in cams) {
        if (c.lensDirection == CameraLensDirection.front) {
          desc = c;
          break;
        }
      }

      final controller = CameraController(
        desc,
        ResolutionPreset.low, // reduce CPU; we’ll crop/resize
        enableAudio: false,
        imageFormatGroup: ImageFormatGroup.yuv420,
      );
      _cam = controller;
      await controller.initialize();

      await controller.startImageStream((CameraImage image) {
        // keep only the most recent frame; the timer will pick it up at 2 fps
        _latestImage = image;
      });

      if (mounted) setState(() => _cameraReady = true);
    } catch (_) {
      if (mounted) setState(() => _cameraReady = false);
      // No camera? We'll still send tiny placeholders when the timer ticks.
    }
  }

  void _startSenderTimer() {
    _sendTimer = Timer.periodic(const Duration(milliseconds: 500), (_) async {
      final now = DateTime.now();
      final ts = now.millisecondsSinceEpoch / 1000.0;

      final imgFrame = _latestImage;
      if (imgFrame == null) {
        _ch?.sink.add(jsonEncode({'frame': kTinyWebPBase64, 'ts': ts, 'format': 'webp'}));
        return;
      }

      try {
        // Convert YUV420 -> RGB
        final rgb = _yuv420ToRgb(imgFrame);

        // Crop square + resize to 480x480 (center crop)
        final roi = img.copyResizeCropSquare(rgb, size: 480);

        // Encode JPEG (cross-platform, fast enough, widely supported)
        final jpgBytes = img.encodeJpg(roi, quality: 75);
        final b64 = base64Encode(jpgBytes);

        _ch?.sink.add(jsonEncode({'frame': b64, 'ts': ts, 'format': 'jpeg'}));
      } catch (_) {
        _ch?.sink.add(jsonEncode({'frame': kTinyWebPBase64, 'ts': ts, 'format': 'webp'}));
      }
    });
  }

  img.Image _yuv420ToRgb(CameraImage camImg) {
    final width = camImg.width;
    final height = camImg.height;

    final pY = camImg.planes[0];
    final pU = camImg.planes[1];
    final pV = camImg.planes[2];

    final out = Uint8List(width * height * 3);
    int idx = 0;

    for (int y = 0; y < height; y++) {
      final uvRow = y >> 1;
      for (int x = 0; x < width; x++) {
        final uvCol = x >> 1;

        final yp = y * pY.bytesPerRow + x;
        final up = uvRow * pU.bytesPerRow + uvCol * (pU.bytesPerPixel ?? 1);
        final vp = uvRow * pV.bytesPerRow + uvCol * (pV.bytesPerPixel ?? 1);

        final Y = pY.bytes[yp].toDouble();
        final U = pU.bytes[up].toDouble();
        final V = pV.bytes[vp].toDouble();

        double R = Y + 1.402 * (V - 128.0);
        double G = Y - 0.344136 * (U - 128.0) - 0.714136 * (V - 128.0);
        double B = Y + 1.772 * (U - 128.0);

        out[idx++] = R.clamp(0.0, 255.0).toInt();
        out[idx++] = G.clamp(0.0, 255.0).toInt();
        out[idx++] = B.clamp(0.0, 255.0).toInt();
      }
    }

    return img.Image.fromBytes(
      width: width,
      height: height,
      bytes: out.buffer,
      numChannels: 3,
      order: img.ChannelOrder.rgb,
    );
  }

  String _prettyAlert(String type, String conf) {
    switch (type) {
      case 'seatbelt':
        return 'Seatbelt violation ($conf)';
      case 'phone':
        return 'Phone in hand ($conf)';
      case 'drowsiness':
        return 'Drowsiness detected.';
      default:
        return 'Alert: $type ($conf)';
    }
  }

  @override
  void dispose() {
    _sendTimer?.cancel();
    _wsSub?.cancel();
    _ch?.sink.close();
    _cam?.stopImageStream().catchError((_) {});
    _cam?.dispose();
    super.dispose();
  }

  void _stopSession() {
    _sendTimer?.cancel();
    _wsSub?.cancel();
    _ch?.sink.close();
    _cam?.stopImageStream().catchError((_) {});
    _cam?.dispose();
    if (mounted) Navigator.of(context).pop();
  }

  @override
  Widget build(BuildContext context) {
    const ink = Color(0xFF0E1113);
    const grayBorder = Color(0xFFDADDE1);

    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new, color: ink),
          onPressed: _stopSession,
        ),
        title: const Text('Monitoring Active',
            style: TextStyle(color: ink, fontWeight: FontWeight.w700)),
        centerTitle: true,
        backgroundColor: Colors.white,
        elevation: 0.5,
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Container(
            decoration: BoxDecoration(
              color: Colors.white,
              border: Border.all(color: const Color(0xFFF1F2F4)),
              borderRadius: BorderRadius.circular(20),
              boxShadow: const [BoxShadow(color: Colors.black12, blurRadius: 8, offset: Offset(0, 2))],
            ),
            padding: const EdgeInsets.all(16),
            child: AspectRatio(
              aspectRatio: 1.6,
              child: Stack(
                children: [
                  Container(
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: grayBorder.withOpacity(0.6), width: 2),
                    ),
                    child: Center(
                      child: Text(
                        _cameraReady ? 'Streaming ROI 480×480' : 'Driver ROI 480×480',
                        style: TextStyle(color: Colors.grey.shade600, fontSize: 18),
                      ),
                    ),
                  ),
                  Positioned(
                    right: 8,
                    top: 8,
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(20),
                        boxShadow: const [BoxShadow(color: Colors.black12, blurRadius: 4)],
                      ),
                      child: Row(
                        children: const [
                          CircleAvatar(radius: 5, backgroundColor: Colors.green),
                          SizedBox(width: 6),
                          Text('LIVE', style: TextStyle(fontWeight: FontWeight.w700)),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),

          const SizedBox(height: 16),

          if (_latestAlertText != null)
            Container(
              decoration: BoxDecoration(
                color: const Color(0xFFFFE7E7),
                borderRadius: BorderRadius.circular(28),
              ),
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
              child: Row(
                children: [
                  const Icon(Icons.shield, color: Colors.red),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      _latestAlertText!,
                      style: const TextStyle(
                        color: Colors.red,
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                ],
              ),
            ),

          const SizedBox(height: 32),

          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 8),
            child: ElevatedButton(
              onPressed: _stopSession,
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.red,
                foregroundColor: Colors.white,
                minimumSize: const Size.fromHeight(56),
                shape: const StadiumBorder(),
                textStyle: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800),
              ),
              child: const Text('Stop Session'),
            ),
          ),
          const SizedBox(height: 8),
          const Center(
            child: Text('Save clip & stop',
                style: TextStyle(color: Colors.black54, fontWeight: FontWeight.w500)),
          ),
        ],
      ),
    );
  }
}
