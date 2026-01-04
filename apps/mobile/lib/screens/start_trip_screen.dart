import 'dart:async';
import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';

import '../core/api_client.dart';
import '../core/token_storage.dart';
import 'live_monitoring_screen.dart';
import 'previous_trips_screen.dart'; // Add this import

class StartTripScreen extends StatefulWidget {
  const StartTripScreen({super.key});

  @override
  State<StartTripScreen> createState() => _StartTripScreenState();
}

class _StartTripScreenState extends State<StartTripScreen> {
  static const Color primaryBlue = Color(0xFF2563EB);
  static const Color primaryDeep = Color(0xFF1D4ED8);
  static const Color primaryLight = Color(0xFFEFF6FF);
  static const Color inkColor = Color(0xFF0E1113);
  static const Color grayInactive = Color(0xFF8A8F98);
  static const Color grayBorder = Color(0xFFDADDE1);
  static const Color grayBg = Color(0xFFF1F2F4);
  static const Color whiteColor = Color(0xFFFFFFFF);

  bool locationEnabled = false;
  bool cameraEnabled = false;
  bool isLoading = false;

  double distanceKm = 5;

  Position? _pos;
  StreamSubscription<Position>? _posSub;

  bool get canStart => locationEnabled && cameraEnabled && !isLoading;

  @override
  void dispose() {
    _posSub?.cancel();
    super.dispose();
  }

  // ================= LOCATION =================
  Future<void> _startLocation() async {
    if (!await Geolocator.isLocationServiceEnabled()) {
      _toast('Please enable GPS');
      await Geolocator.openLocationSettings();
      return;
    }

    var perm = await Geolocator.checkPermission();
    if (perm == LocationPermission.denied) {
      perm = await Geolocator.requestPermission();
    }

    if (perm == LocationPermission.denied ||
        perm == LocationPermission.deniedForever) {
      _toast('Location permission denied');
      return;
    }

    _posSub?.cancel();
    _posSub = Geolocator.getPositionStream(
      locationSettings: const LocationSettings(
        accuracy: LocationAccuracy.best,
        distanceFilter: 5,
      ),
    ).listen((p) => setState(() => _pos = p));

    final p = await Geolocator.getCurrentPosition();
    setState(() => _pos = p);
  }

  Future<void> _stopLocation() async {
    await _posSub?.cancel();
    _posSub = null;
    setState(() => _pos = null);
  }

  // ================= SESSION =================
  Future<void> _createSessionAndGo() async {
    setState(() => isLoading = true);

    try {
      // Get auth token
      final token = await TokenStorage.read();

      // Prepare headers
      final Map<String, String> headers = {
        'Content-Type': 'application/json',
      };

      if (token != null && token.isNotEmpty) {
        headers['Authorization'] = 'Bearer $token';
      }

      final res = await ApiClient.dio.post(
        '/api/sessions',
        data: {
          'name': 'Drive Session',
          'distanceKm': distanceKm.toInt(),
          'locationEnabled': locationEnabled,
          'cameraEnabled': cameraEnabled,
          'lat': _pos?.latitude ?? 0,
          'lng': _pos?.longitude ?? 0,
        },
        options: Options(headers: headers),
      );

      final data = res.data is Map ? res.data : jsonDecode(res.data as String);

      final sessionId =
          (data['id'] ?? data['_id'] ?? data['sessionId']).toString();

      if (!mounted) return;

      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) => LiveMonitoringScreen(
            sessionId: sessionId,
            token: token ?? '',
            driverName: 'Driver',
          ),
        ),
      );
    } catch (e) {
      print('Error creating session: $e');
      _toast('Create session failed');
    } finally {
      setState(() => isLoading = false);
    }
  }

  // ================= UI =================
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF6F7F9),
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        centerTitle: true,
        title: const Text('Start Trip', style: TextStyle(color: Colors.black)),
        leading: const BackButton(color: Colors.black),
        actions: const [
          Padding(
            padding: EdgeInsets.only(right: 12),
            child: Icon(Icons.help_outline, color: Colors.black),
          )
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            // ========= SAFETY =========
            _card(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: const [
                      CircleAvatar(
                        radius: 18,
                        backgroundColor: Color(0xFFEFF6FF),
                        child: Icon(Icons.shield, color: primaryBlue),
                      ),
                      SizedBox(width: 12),
                      Text('Enable Safety Features',
                          style: TextStyle(
                              fontSize: 16, fontWeight: FontWeight.bold)),
                    ],
                  ),
                  const SizedBox(height: 16),
                  _switchRow(
                    title: 'Location',
                    subtitle: 'Track distance accurately',
                    value: locationEnabled,
                    onChanged: (v) async {
                      setState(() => locationEnabled = v);
                      v ? await _startLocation() : await _stopLocation();
                      if (!v) setState(() => cameraEnabled = false);
                    },
                  ),
                  const SizedBox(height: 12),
                  _switchRow(
                    title: 'Camera',
                    subtitle:
                        'Monitor driver behavior – face/hands only\nOnly cropped driver view; no raw video stored.',
                    value: cameraEnabled,
                    onChanged: locationEnabled
                        ? (v) => setState(() => cameraEnabled = v)
                        : null,
                  ),
                ],
              ),
            ),

            const SizedBox(height: 16),

            // ========= DISTANCE =========
            _card(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Set Distance Goal',
                      style:
                          TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 6),
                  const Text('Choose total trip distance.',
                      style: TextStyle(color: Colors.grey)),
                  const SizedBox(height: 28),
                  Stack(
                    clipBehavior: Clip.none,
                    children: [
                      Slider(
                        min: 1,
                        max: 50,
                        divisions: 49,
                        value: distanceKm,
                        activeColor: primaryBlue,
                        onChanged: (v) => setState(() => distanceKm = v),
                      ),
                      Positioned(
                        left: ((distanceKm - 1) / 49) *
                            (MediaQuery.of(context).size.width - 96),
                        top: -26,
                        child: Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 10, vertical: 4),
                          decoration: BoxDecoration(
                            color: primaryBlue,
                            borderRadius: BorderRadius.circular(14),
                          ),
                          child: Text(
                            '${distanceKm.toStringAsFixed(1)} km',
                            style: const TextStyle(
                                color: Colors.white,
                                fontSize: 12,
                                fontWeight: FontWeight.bold),
                          ),
                        ),
                      ),
                    ],
                  ),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: const [
                      Text('1'),
                      Text('5'),
                      Text('10'),
                      Text('20'),
                      Text('30'),
                      Text('40'),
                      Text('50'),
                    ],
                  )
                ],
              ),
            ),

            const SizedBox(height: 16),

            // ========= TIPS =========
            Container(
              width: double.infinity, // 👈 makes it full width
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFFEFF6FF),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: const [
                  Text(
                    'Tips',
                    style: TextStyle(
                      color: primaryBlue,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  SizedBox(height: 8),
                  Text('• Mount on dashboard',
                      style: TextStyle(color: primaryBlue)),
                  Text('• Face & shoulders visible',
                      style: TextStyle(color: primaryBlue)),
                  Text('• Volume on', style: TextStyle(color: primaryBlue)),
                ],
              ),
            ),

            const SizedBox(height: 24),

            // ========= BUTTON =========
            SizedBox(
              width: double.infinity,
              height: 52,
              child: ElevatedButton(
                onPressed: canStart ? _createSessionAndGo : null,
                style: ElevatedButton.styleFrom(
                  backgroundColor:
                      canStart ? primaryBlue : const Color(0xFFD1D5DB),
                  foregroundColor: Colors.white, // 👈 TEXT COLOR
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(14),
                  ),
                ),
                child: isLoading
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Colors.white,
                        ),
                      )
                    : const Text(
                        'Start Monitoring',
                        style: TextStyle(fontWeight: FontWeight.bold),
                      ),
              ),
            ),

            const SizedBox(height: 12),

            // ========= VIEW PREVIOUS TRIPS BUTTON =========
            TextButton(
              onPressed: () {
                // Navigate to PreviousTripsScreen
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => const PreviousTripsScreen(),
                  ),
                );
              },
              child: const Text('View Previous Trips',
                  style: TextStyle(color: primaryBlue)),
            ),
          ],
        ),
      ),
    );
  }

  // ================= HELPERS =================
  static Widget _card({required Widget child}) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        boxShadow: const [
          BoxShadow(
            color: Color(0x14000000),
            blurRadius: 16,
            offset: Offset(0, 8),
          )
        ],
      ),
      child: child,
    );
  }

  static Widget _switchRow({
    required String title,
    required String subtitle,
    required bool value,
    ValueChanged<bool>? onChanged,
  }) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(title,
                  style: const TextStyle(
                      fontSize: 15, fontWeight: FontWeight.w600)),
              const SizedBox(height: 4),
              Text(subtitle,
                  style: const TextStyle(fontSize: 13, color: Colors.grey)),
            ],
          ),
        ),
        Switch(
          value: value,
          activeColor: primaryBlue,
          onChanged: onChanged,
        ),
      ],
    );
  }

  void _toast(String msg) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
  }
}
