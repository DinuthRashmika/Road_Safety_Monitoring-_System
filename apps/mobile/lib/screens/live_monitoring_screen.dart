import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:yuv_to_png/yuv_to_png.dart';
import 'package:audioplayers/audioplayers.dart';

/// ⚠️ MUST match backend IP
String wsUrl(String sessionId, String token) =>
    'ws://192.168.8.196:8000/ws/sessions/$sessionId?token=$token';

/// Base URL for HTTP requests
String baseUrl = 'http://192.168.8.196:8000';

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
  // ===== Theme =====
  static const Color primaryBlue = Color(0xFF2563EB);

  static const Color bgBlack = Colors.black;
  static const Color cardDark = Color(0xFF111827);
  static const Color borderDark = Color(0xFF1F2937);
  static const Color textWhite = Colors.white;
  static const Color textMuted = Color(0xFF9CA3AF);

  // alert colors (red)
  static const Color alertBg = Color(0xFF431C1C);
  static const Color alertText = Color(0xFFF87171);

  // no-alert colors (green)
  static const Color okBg = Color(0xFF064E3B);
  static const Color okText = Color(0xFF10B981);

  WebSocketChannel? _channel;
  StreamSubscription? _wsSub;

  CameraController? _cam;
  Timer? _sendTimer;

  bool _cameraReady = false;
  bool _isConverting = false;
  Uint8List? _latestPngBytes;

  // ===== Alerts state =====
  String? _latestAlertType; // only TYPE shown
  bool _alertsDisplayEnabled = true; // keep double tap toggle

  // 5 required categories (fixed row, no scroll)
  late final List<_AlertCategory> _categories;

  // Counts (categoryName -> count)
  final Map<String, int> _alertCounts = {};

  bool _isStopping = false;

  final AudioPlayer _audioPlayer = AudioPlayer();
  bool _isAlarmPlaying = false;

  @override
  void initState() {
    super.initState();

    _categories = const [
      _AlertCategory(name: 'Mobile Phone Usage', icon: Icons.phone_iphone),
      _AlertCategory(name: 'Drowsiness', icon: Icons.bedtime_outlined),
      _AlertCategory(name: 'Yawning', icon: Icons.mood_bad_outlined),
      _AlertCategory(name: 'Distraction', icon: Icons.visibility_off_outlined),
      _AlertCategory(
          name: 'No Seatbelt', icon: Icons.airline_seat_recline_normal),
    ];

    for (final c in _categories) {
      _alertCounts[c.name] = 0;
    }

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
          final data =
              msg is String ? msg : String.fromCharCodes(msg as Uint8List);

          if (data.toLowerCase().contains('alert')) {
            final alertType = _extractAlertType(data);
            if (alertType == null) return;

            setState(() {
              _latestAlertType = alertType;
              _alertCounts[alertType] = (_alertCounts[alertType] ?? 0) + 1;
            });

            _playAlarm();
          }
        } catch (_) {}
      },
      onError: (_) {},
      onDone: () {},
    );
  }

  // Extract alert TYPE only and map into your categories.
  String? _extractAlertType(String raw) {
    final s = raw.trim();

    // JSON
    if (s.startsWith('{') && s.endsWith('}')) {
      try {
        final m = jsonDecode(s);
        if (m is Map) {
          final type = (m['type'] ?? m['alert'] ?? m['name'] ?? '').toString();
          final msg =
              (m['message'] ?? m['msg'] ?? m['text'] ?? '').toString();
          return _mapToCategory(type, msg);
        }
      } catch (_) {}
    }

    // Plain text
    final cleaned =
        s.replaceFirst(RegExp(r'(?i)\balert\b\s*[:\-]?\s*'), '').trim();
    return _mapToCategory(cleaned, cleaned);
  }

  String? _mapToCategory(String type, String message) {
    final all = '${type.toLowerCase()} ${message.toLowerCase()}';

    if (all.contains('phone') || all.contains('mobile')) {
      return 'Mobile Phone Usage';
    }
    if (all.contains('drowsy') || all.contains('sleep')) {
      return 'Drowsiness';
    }
    if (all.contains('yawn')) {
      return 'Yawning';
    }
    if (all.contains('distract') ||
        all.contains('inattention') ||
        all.contains('attention')) {
      return 'Distraction';
    }
    if (all.contains('seatbelt') ||
        all.contains('seat belt') ||
        all.contains('belt') ||
        all.contains('no belt')) {
      return 'No Seatbelt';
    }
    return null;
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

    await _cam!.startImageStream((CameraImage image) {
      if (_isConverting) return;
      _isConverting = true;

      try {
        final Uint8List? pngBytes = YuvToPng.yuvToPng(
          image,
          lensDirection: _cam!.description.lensDirection,
        );

        if (pngBytes != null) {
          _latestPngBytes = pngBytes;
        }
      } catch (e) {
        print("YUV to PNG error: $e");
      } finally {
        _isConverting = false;
      }
    });

    if (mounted) setState(() => _cameraReady = true);
  }

  // ================= END SESSION + SUMMARY POPUP =================
  Future<void> _endSession() async {
    if (_isStopping) return;
    setState(() => _isStopping = true);

    Map<String, dynamic>? sessionData;

    try {
      await http.post(
        Uri.parse('$baseUrl/api/sessions/${widget.sessionId}/end'),
        headers: {
          'Authorization': 'Bearer ${widget.token}',
          'Content-Type': 'application/json',
        },
      );

      try {
        final res = await http.get(
          Uri.parse('$baseUrl/api/sessions/${widget.sessionId}'),
          headers: {'Authorization': 'Bearer ${widget.token}'},
        );
        if (res.statusCode == 200) {
          sessionData = json.decode(res.body);
        }
      } catch (_) {}

      _showSummaryPopup(sessionData);
      _stopMonitoring();
    } catch (_) {
      _showSummaryPopup(sessionData);
      _stopMonitoring();
    } finally {
      if (mounted) setState(() => _isStopping = false);
    }
  }

  void _showSummaryPopup(Map<String, dynamic>? sessionData) {
    final details = _extractSessionDetails(sessionData);

    showDialog(
      context: context,
      barrierDismissible: false,
      barrierColor: Colors.black.withOpacity(0.85),
      builder: (context) {
        return Dialog(
          backgroundColor: cardDark,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(24),
            side: const BorderSide(color: borderDark),
          ),
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  width: 72,
                  height: 72,
                  decoration: BoxDecoration(
                    color: okBg.withOpacity(0.30),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(
                    Icons.check_circle,
                    color: okText,
                    size: 46,
                  ),
                ),
                const SizedBox(height: 12),
                const Text(
                  'Session Summary',
                  style: TextStyle(
                    color: textWhite,
                    fontSize: 20,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                const SizedBox(height: 8),
                if (details != null)
                  Text(
                    '${details['distance']}  •  ${details['duration']}',
                    style: const TextStyle(
                      color: textMuted,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                const SizedBox(height: 14),
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: const Color(0xFF0B1220),
                    borderRadius: BorderRadius.circular(18),
                    border: Border.all(color: borderDark),
                  ),
                  child: Column(
                    children: _categories.map((c) {
                      final count = _alertCounts[c.name] ?? 0;
                      return Padding(
                        padding: const EdgeInsets.symmetric(vertical: 6),
                        child: Row(
                          children: [
                            Icon(c.icon, color: textMuted, size: 18),
                            const SizedBox(width: 10),
                            Expanded(
                              child: Text(
                                c.name,
                                style: const TextStyle(
                                  color: textWhite,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                            ),
                            Text(
                              count.toString(),
                              style: const TextStyle(
                                color: okText,
                                fontWeight: FontWeight.w900,
                              ),
                            ),
                          ],
                        ),
                      );
                    }).toList(),
                  ),
                ),
                const SizedBox(height: 16),
                SizedBox(
                  width: double.infinity,
                  child: OutlinedButton(
                    onPressed: () {
                      Navigator.pop(context);
                      Navigator.pop(context);
                    },
                    style: OutlinedButton.styleFrom(
                      side: const BorderSide(color: borderDark),
                      foregroundColor: textWhite,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(14),
                      ),
                      padding: const EdgeInsets.symmetric(vertical: 14),
                    ),
                    child: const Text(
                      'Close',
                      style: TextStyle(fontWeight: FontWeight.w800),
                    ),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Map<String, dynamic>? _extractSessionDetails(Map<String, dynamic>? data) {
    if (data == null) return null;

    try {
      String duration = '-';
      String distance = '-';

      if (data['startedAt'] != null && data['endedAt'] != null) {
        final started = DateTime.parse(data['startedAt']);
        final ended = DateTime.parse(data['endedAt']);
        final diff = ended.difference(started);
        final minutes = diff.inMinutes;
        final seconds = diff.inSeconds.remainder(60);
        duration =
            '${minutes.toString().padLeft(2, '0')}:${seconds.toString().padLeft(2, '0')}';
      }

      if (data['metrics'] != null && data['metrics']['distance'] != null) {
        final d = data['metrics']['distance'];
        distance = d is num ? '${d.toStringAsFixed(1)} km' : '$d km';
      } else if (data['statistics'] != null &&
          data['statistics']['totalDistance'] != null) {
        final d = data['statistics']['totalDistance'];
        distance = d is num ? '${d.toStringAsFixed(1)} km' : '$d km';
      }

      return {'duration': duration, 'distance': distance};
    } catch (_) {
      return null;
    }
  }

  // ================= FRAME SENDER =================
  void _startSenderTimer() {
    _sendTimer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (_latestPngBytes == null) return;
      try {
        _channel?.sink.add(_latestPngBytes!);
      } catch (e) {
        print("Error sending frame: $e");
      }
    });
  }

  // ================= STOP MONITORING =================
  void _stopMonitoring() {
    _sendTimer?.cancel();
    _wsSub?.cancel();
    _channel?.sink.close();
    _cam?.stopImageStream();
    _cam?.dispose();
    _audioPlayer.stop();
  }

  void _stopSession() {
    _stopMonitoring();
    Navigator.pop(context);
  }

  @override
  void dispose() {
    _stopMonitoring();
    super.dispose();
  }

  void _playAlarm() async {
    if (_isAlarmPlaying) return;
    _isAlarmPlaying = true;

    try {
      await _audioPlayer.play(AssetSource('sounds/alarm.mp3'), volume: 1.0);
    } catch (_) {} finally {
      _isAlarmPlaying = false;
    }
  }

  // ================= UI =================
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: bgBlack,
      appBar: AppBar(
        backgroundColor: bgBlack,
        elevation: 0,
        title: const Text(
          'Monitoring Active',
          style: TextStyle(color: textWhite, fontWeight: FontWeight.w800),
        ),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios, color: textWhite),
          onPressed: _stopSession,
        ),
      ),
      body: Column(
        children: [
          const SizedBox(height: 16),

          // ===== Camera preview =====
          AspectRatio(
            aspectRatio: 1,
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Container(
                decoration: BoxDecoration(
                  color: cardDark,
                  borderRadius: BorderRadius.circular(24),
                  border: Border.all(color: borderDark),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.35),
                      blurRadius: 16,
                      offset: const Offset(0, 8),
                    )
                  ],
                ),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(24),
                  child: _cameraReady && _cam != null
                      ? CameraPreview(_cam!)
                      : const Center(
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            valueColor: AlwaysStoppedAnimation(primaryBlue),
                          ),
                        ),
                ),
              ),
            ),
          ),

          const SizedBox(height: 12),

          // ✅ increased height alert box
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: _buildAlertTypeBox(),
          ),

          const SizedBox(height: 12),

          // ✅ FIXED 5 ITEMS in ONE ROW (no scrolling)
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Row(
              children: List.generate(_categories.length, (i) {
                final c = _categories[i];
                final count = _alertCounts[c.name] ?? 0;
                return Expanded(
                  child: Padding(
                    padding: EdgeInsets.only(
                      right: i == _categories.length - 1 ? 0 : 10,
                    ),
                    child: _AlertCategoryTile(
                      icon: c.icon,
                      count: count,
                    ),
                  ),
                );
              }),
            ),
          ),

          const Spacer(),

          // ===== End Session button =====
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: Container(
              width: double.infinity,
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF7F1D1D), Color(0xFFDC2626)],
                ),
                borderRadius: BorderRadius.circular(16),
                boxShadow: [
                  BoxShadow(
                    color: const Color(0xFFDC2626).withOpacity(0.35),
                    blurRadius: 14,
                    offset: const Offset(0, 6),
                  )
                ],
              ),
              child: SizedBox(
                height: 52,
                child: ElevatedButton.icon(
                  onPressed: _isStopping ? null : _endSession,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.transparent,
                    shadowColor: Colors.transparent,
                    foregroundColor: textWhite,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16),
                    ),
                  ),
                  icon: _isStopping
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            valueColor:
                                AlwaysStoppedAnimation<Color>(textWhite),
                          ),
                        )
                      : const Icon(Icons.stop),
                  label: Text(
                    _isStopping ? 'Ending Session...' : 'End Session',
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  /// ✅ Increased height alert box (bigger)
  Widget _buildAlertTypeBox() {
    const double fixedHeight = 72; // ✅ increased

    if (!_alertsDisplayEnabled) {
      return Align(
        alignment: Alignment.centerLeft,
        child: GestureDetector(
          onTap: () => setState(() => _alertsDisplayEnabled = true),
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
            decoration: BoxDecoration(
              color: const Color(0xFF0B1220),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: borderDark),
            ),
            child: const Text(
              'Alerts hidden (tap to show)',
              style: TextStyle(
                color: textMuted,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
        ),
      );
    }

    final type = _latestAlertType;
    final hasAlert = type != null && type.trim().isNotEmpty;

    return GestureDetector(
      onDoubleTap: () => setState(() => _alertsDisplayEnabled = false),
      child: SizedBox(
        height: fixedHeight,
        width: double.infinity,
        child: Container(
          alignment: Alignment.centerLeft,
          padding: const EdgeInsets.symmetric(horizontal: 16),
          decoration: BoxDecoration(
            color: hasAlert ? alertBg : okBg,
            borderRadius: BorderRadius.circular(20),
            border: Border.all(
              color: hasAlert
                  ? const Color(0xFF7F1D1D)
                  : const Color(0xFF065F46),
            ),
          ),
          child: Text(
            hasAlert ? type : 'No Any Alert',
            style: TextStyle(
              color: hasAlert ? alertText : okText,
              fontWeight: FontWeight.w900,
              fontSize: 16,
            ),
          ),
        ),
      ),
    );
  }
}

// ===== Models / Widgets =====

class _AlertCategory {
  final String name;
  final IconData icon;
  const _AlertCategory({required this.name, required this.icon});
}

/// ✅ Fixed tile for row (icon + count only)
class _AlertCategoryTile extends StatelessWidget {
  final IconData icon;
  final int count;

  const _AlertCategoryTile({
    required this.icon,
    required this.count,
  });

  static const Color cardDark = Color(0xFF111827);
  static const Color borderDark = Color(0xFF1F2937);
  static const Color textMuted = Color(0xFF9CA3AF);

  static const Color alertBg = Color(0xFF431C1C);
  static const Color alertText = Color(0xFFF87171);

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 84,
      padding: const EdgeInsets.symmetric(vertical: 10),
      decoration: BoxDecoration(
        color: cardDark,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: borderDark),
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            width: 38,
            height: 38,
            decoration: BoxDecoration(
              color: alertBg,
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: const Color(0xFF7F1D1D)),
            ),
            child: Icon(icon, color: alertText, size: 20),
          ),
          const SizedBox(height: 8),
          Text(
            count.toString(),
            style: const TextStyle(
              color: textMuted,
              fontWeight: FontWeight.w900,
              fontSize: 13,
            ),
          ),
        ],
      ),
    );
  }
}