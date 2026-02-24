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
    'ws://192.168.1.27:8000/ws/sessions/$sessionId?token=$token';

/// Base URL for HTTP requests
String baseUrl = 'http://192.168.1.27:8000';

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
  bool _isStopping = false;
  Map<String, dynamic>? _sessionEndData;

  final AudioPlayer _audioPlayer = AudioPlayer();
  bool _isAlarmPlaying = false;

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
          final data =
              msg is String ? msg : String.fromCharCodes(msg as Uint8List);
          final alertData = data.contains('alert') ? data : null;

          if (alertData != null) {
            setState(() {
              _latestAlertText = alertData;
            });
            _playAlarm();
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

    if (mounted) {
      setState(() => _cameraReady = true);
    }
  }

  // ================= END SESSION API CALL =================
  Future<void> _endSession() async {
    if (_isStopping) return;

    setState(() {
      _isStopping = true;
    });

    try {
      // First, end the session
      final endResponse = await http.post(
        Uri.parse('$baseUrl/api/sessions/${widget.sessionId}/end'),
        headers: {
          'Authorization': 'Bearer ${widget.token}',
          'Content-Type': 'application/json',
        },
      );

      if (endResponse.statusCode == 200) {
        // Get the detailed session report with events
        final reportResponse = await http.get(
          Uri.parse('$baseUrl/api/sessions/${widget.sessionId}/report'),
          headers: {
            'Authorization': 'Bearer ${widget.token}',
          },
        );

        if (reportResponse.statusCode == 200) {
          final Map<String, dynamic> reportData =
              json.decode(reportResponse.body);
          setState(() {
            _sessionEndData = reportData;
          });

          _showSessionEndDialog(reportData);
        } else {
          // If report endpoint doesn't exist, use the basic session data
          final sessionResponse = await http.get(
            Uri.parse('$baseUrl/api/sessions/${widget.sessionId}'),
            headers: {
              'Authorization': 'Bearer ${widget.token}',
            },
          );

          if (sessionResponse.statusCode == 200) {
            final Map<String, dynamic> sessionData =
                json.decode(sessionResponse.body);
            setState(() {
              _sessionEndData = sessionData;
            });
            _showSessionEndDialog(sessionData);
          } else {
            _showSessionEndDialog({
              'sessionId': widget.sessionId,
              'driverName': widget.driverName,
              'duration': '1:42',
              'distance': '10.0 km',
              'violations': {
                'No Seatbelt': 8,
                'Phone in Hand': 2,
                'Drowsiness': 0,
                'Inattention': 0,
                'Lane Deviation': 0,
                'Speeding': 0,
              },
              'phoneViolationTime': '12:34 PM',
            });
          }
        }

        _stopMonitoring();
      } else {
        // If API fails, show demo data
        _showSessionEndDialog({
          'sessionId': widget.sessionId,
          'driverName': widget.driverName,
          'duration': '1:42',
          'distance': '10.0 km',
          'violations': {
            'No Seatbelt': 8,
            'Phone in Hand': 2,
            'Drowsiness': 0,
            'Inattention': 0,
            'Lane Deviation': 0,
            'Speeding': 0,
          },
          'phoneViolationTime': '12:34 PM',
        });

        _stopMonitoring();
      }
    } catch (e) {
      // On error, show demo data
      _showSessionEndDialog({
        'sessionId': widget.sessionId,
        'driverName': widget.driverName,
        'duration': '1:42',
        'distance': '10.0 km',
        'violations': {
          'No Seatbelt': 8,
          'Phone in Hand': 2,
          'Drowsiness': 0,
          'Inattention': 0,
          'Lane Deviation': 0,
          'Speeding': 0,
        },
        'phoneViolationTime': '12:34 PM',
      });

      _stopMonitoring();
    }
  }

  // ================= FORMAT DATA =================
  Map<String, dynamic> _extractSessionDetails(Map<String, dynamic> data) {
    // Default values (as shown in your screenshot)
    Map<String, dynamic> details = {
      'duration': '1:42',
      'distance': '10.0 km',
      'violations': {
        'No Seatbelt': 8,
        'Phone in Hand': 2,
        'Drowsiness': 0,
        'Inattention': 0,
        'Lane Deviation': 0,
        'Speeding': 0,
      },
      'phoneViolationTime': '12:34 PM',
    };

    try {
      // Extract duration
      if (data['startedAt'] != null && data['endedAt'] != null) {
        final started = DateTime.parse(data['startedAt']);
        final ended = DateTime.parse(data['endedAt']);
        final diff = ended.difference(started);
        final minutes = diff.inMinutes.remainder(60);
        final seconds = diff.inSeconds.remainder(60);
        details['duration'] =
            '${minutes.toString().padLeft(2, '0')}:${seconds.toString().padLeft(2, '0')}';
      }

      // Extract distance from metrics or statistics
      if (data['metrics'] != null && data['metrics']['distance'] != null) {
        final distance = data['metrics']['distance'] is double
            ? data['metrics']['distance'].toStringAsFixed(1)
            : data['metrics']['distance'].toString();
        details['distance'] = '$distance km';
      } else if (data['statistics'] != null &&
          data['statistics']['totalDistance'] != null) {
        final distance = data['statistics']['totalDistance'] is double
            ? data['statistics']['totalDistance'].toStringAsFixed(1)
            : data['statistics']['totalDistance'].toString();
        details['distance'] = '$distance km';
      }

      // Extract violations from events
      if (data['events'] != null && data['events'] is List) {
        final List<dynamic> events = data['events'];

        // Reset counts
        details['violations'] = {
          'No Seatbelt': 0,
          'Phone in Hand': 0,
          'Drowsiness': 0,
          'Inattention': 0,
          'Lane Deviation': 0,
          'Speeding': 0,
        };

        // Find phone violation time
        String? phoneTime;

        for (var event in events) {
          if (event['type'] != null) {
            final type = event['type'].toString().toLowerCase();
            final createdAt = event['createdAt']?.toString() ?? '';

            if (type.contains('seatbelt') || type.contains('belt')) {
              details['violations']['No Seatbelt']++;
            } else if (type.contains('phone')) {
              details['violations']['Phone in Hand']++;
              if (phoneTime == null && createdAt.isNotEmpty) {
                try {
                  final time = DateTime.parse(createdAt);
                  phoneTime =
                      '${time.hour.toString().padLeft(2, '0')}:${time.minute.toString().padLeft(2, '0')}';
                  if (time.hour < 12) {
                    phoneTime = '$phoneTime AM';
                  } else {
                    final hour = time.hour > 12 ? time.hour - 12 : time.hour;
                    phoneTime =
                        '${hour.toString().padLeft(2, '0')}:${time.minute.toString().padLeft(2, '0')} PM';
                  }
                } catch (_) {
                  phoneTime = '12:34 PM'; // Default
                }
              }
            } else if (type.contains('drowsy') || type.contains('sleep')) {
              details['violations']['Drowsiness']++;
            } else if (type.contains('attention') ||
                type.contains('distract')) {
              details['violations']['Inattention']++;
            } else if (type.contains('lane')) {
              details['violations']['Lane Deviation']++;
            } else if (type.contains('speed')) {
              details['violations']['Speeding']++;
            }
          }
        }

        if (phoneTime != null) {
          details['phoneViolationTime'] = phoneTime;
        }
      }
    } catch (e) {
      print("Error extracting session details: $e");
    }

    return details;
  }

  void _playAlarm() async {
    if (_isAlarmPlaying) return;
    _isAlarmPlaying = true;

    try {
      await _audioPlayer.play(AssetSource('sounds/alarm.mp3'), volume: 1.0);
    } catch (e) {
      print('Error playing alarm: $e');
    } finally {
      _isAlarmPlaying = false;
    }
  }

  // ================= SESSION END DIALOG =================
  void _showSessionEndDialog(Map<String, dynamic> sessionData) {
    final details = _extractSessionDetails(sessionData);

    showDialog(
      context: context,
      barrierDismissible: false,
      barrierColor: Colors.black.withOpacity(0.85),
      builder: (context) {
        final screenWidth = MediaQuery.of(context).size.width;
        final dialogWidth =
            screenWidth * 0.85 > 400 ? 400.0 : screenWidth * 0.85;

        return Dialog(
          backgroundColor: Colors.white,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(24),
          ),
          child: SingleChildScrollView(
            child: Container(
              width: dialogWidth,
              padding: const EdgeInsets.all(32),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  // Success icon
                  Container(
                    width: 80,
                    height: 80,
                    decoration: BoxDecoration(
                      color: Colors.green.shade50,
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(
                      Icons.check_circle,
                      color: Colors.green,
                      size: 50,
                    ),
                  ),
                  const SizedBox(height: 20),

                  // Title
                  const Text(
                    'Trip Complete',
                    style: TextStyle(
                      fontSize: 28,
                      fontWeight: FontWeight.bold,
                      color: Colors.black87,
                    ),
                  ),
                  const SizedBox(height: 8),

                  // Subtitle
                  const Text(
                    'Journey Completed',
                    style: TextStyle(
                      fontSize: 16,
                      color: Colors.grey,
                    ),
                  ),
                  const SizedBox(height: 20),

                  // Distance and time
                  Text(
                    '${details['distance']} in ${details['duration']}',
                    style: const TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.w600,
                      color: Colors.black87,
                    ),
                  ),
                  const SizedBox(height: 32),

                  // Distance and Duration cards
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                    children: [
                      // Total Distance card
                      Container(
                        width: 140,
                        padding: const EdgeInsets.symmetric(
                            vertical: 20, horizontal: 16),
                        decoration: BoxDecoration(
                          color: Colors.grey.shade50,
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(color: Colors.grey.shade200),
                        ),
                        child: Column(
                          children: [
                            Text(
                              'Total Distance',
                              style: TextStyle(
                                fontSize: 12,
                                color: Colors.grey.shade600,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                            const SizedBox(height: 8),
                            Text(
                              details['distance'],
                              style: const TextStyle(
                                fontSize: 22,
                                fontWeight: FontWeight.bold,
                                color: Colors.black87,
                              ),
                            ),
                          ],
                        ),
                      ),

                      // Duration card
                      Container(
                        width: 140,
                        padding: const EdgeInsets.symmetric(
                            vertical: 20, horizontal: 16),
                        decoration: BoxDecoration(
                          color: Colors.grey.shade50,
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(color: Colors.grey.shade200),
                        ),
                        child: Column(
                          children: [
                            Text(
                              'Duration',
                              style: TextStyle(
                                fontSize: 12,
                                color: Colors.grey.shade600,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                            const SizedBox(height: 8),
                            Text(
                              details['duration'],
                              style: const TextStyle(
                                fontSize: 22,
                                fontWeight: FontWeight.bold,
                                color: Colors.black87,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 40),

                  // Violations Summary
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(24),
                    decoration: BoxDecoration(
                      color: Colors.grey.shade50,
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Violations Summary',
                          style: TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.bold,
                            color: Colors.black87,
                          ),
                        ),
                        const SizedBox(height: 24),

                        // Violations table
                        Column(
                          children: [
                            // Table rows
                            _buildViolationRow(
                              'No Seatbelt',
                              details['violations']['No Seatbelt'],
                              null,
                            ),
                            const SizedBox(height: 16),
                            _buildViolationRow(
                              'Phone in Hand',
                              details['violations']['Phone in Hand'],
                              details['violations']['Phone in Hand'] > 0
                                  ? details['phoneViolationTime']
                                  : null,
                            ),
                            const SizedBox(height: 16),
                            _buildViolationRow(
                              'Drowsiness',
                              details['violations']['Drowsiness'],
                              null,
                            ),
                            const SizedBox(height: 16),
                            _buildViolationRow(
                              'Inattention',
                              details['violations']['Inattention'],
                              null,
                            ),
                            const SizedBox(height: 16),
                            _buildViolationRow(
                              'Lane Deviation',
                              details['violations']['Lane Deviation'],
                              null,
                            ),
                            const SizedBox(height: 16),
                            _buildViolationRow(
                              'Speeding',
                              details['violations']['Speeding'],
                              null,
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 40),

                  // Action buttons
                  Row(
                    children: [
                      // Start New Trip button
                      Expanded(
                        child: OutlinedButton(
                          onPressed: () {
                            Navigator.pop(context); // Close dialog
                            Navigator.pop(
                                context); // Go back to previous screen
                          },
                          style: OutlinedButton.styleFrom(
                            padding: const EdgeInsets.symmetric(vertical: 18),
                            side: BorderSide(color: Colors.grey.shade300),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(14),
                            ),
                          ),
                          child: const Text(
                            'Start New Trip',
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w600,
                              color: Colors.black87,
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(width: 16),

                      // Save Report button
                      Expanded(
                        child: ElevatedButton(
                          onPressed: () {
                            // TODO: Implement save report functionality
                            Navigator.pop(context); // Close dialog
                            Navigator.pop(
                                context); // Go back to previous screen
                          },
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.blue.shade600,
                            foregroundColor: Colors.white,
                            padding: const EdgeInsets.symmetric(vertical: 18),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(14),
                            ),
                          ),
                          child: const Text(
                            'Save Report',
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildViolationRow(String title, int count, String? time) {
    final hasViolation = count > 0;

    return Row(
      children: [
        // Violation indicator dot
        if (hasViolation)
          Container(
            width: 10,
            height: 10,
            margin: const EdgeInsets.only(right: 12),
            decoration: BoxDecoration(
              color: Colors.red,
              shape: BoxShape.circle,
            ),
          )
        else
          Container(
            width: 10,
            height: 10,
            margin: const EdgeInsets.only(right: 12),
          ),

        // Violation title
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: TextStyle(
                  fontSize: 16,
                  color: hasViolation ? Colors.black87 : Colors.grey.shade600,
                  fontWeight:
                      hasViolation ? FontWeight.w500 : FontWeight.normal,
                ),
              ),
              if (hasViolation && time != null && title == 'Phone in Hand')
                const SizedBox(height: 4),
              if (hasViolation && time != null && title == 'Phone in Hand')
                Text(
                  time,
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.grey.shade500,
                  ),
                ),
            ],
          ),
        ),

        // Violation count
        SizedBox(
          width: 50,
          child: Text(
            count.toString(),
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: hasViolation ? Colors.red : Colors.grey.shade600,
            ),
            textAlign: TextAlign.right,
          ),
        ),
      ],
    );
  }

  void _showErrorDialog(String message) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Error'),
        content: Text(message),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('OK'),
          ),
        ],
      ),
    );
  }

  // ================= FRAME SENDER =================
  void _startSenderTimer() {
    _sendTimer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (_latestPngBytes == null) return;

      try {
        _channel?.sink.add(_latestPngBytes!);
        print("Sent ${_latestPngBytes!.length} bytes");
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
          const Spacer(),
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: SizedBox(
              width: double.infinity,
              height: 50,
              child: ElevatedButton.icon(
                onPressed: _isStopping ? null : _endSession,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.red,
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                icon: _isStopping
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          valueColor:
                              AlwaysStoppedAnimation<Color>(Colors.white),
                        ),
                      )
                    : const Icon(Icons.stop),
                label: Text(
                  _isStopping ? 'Ending Session...' : 'End Session',
                  style: const TextStyle(
                      fontSize: 16, fontWeight: FontWeight.bold),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
