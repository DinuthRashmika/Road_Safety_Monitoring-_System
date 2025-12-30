import 'dart:async';
import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';

import '../core/api_client.dart';
import '../core/token_storage.dart';
import 'live_monitoring_screen.dart';

const String kApiBase = 'http://192.168.8.174:8000';

class StartTripScreen extends StatefulWidget {
  const StartTripScreen({super.key});

  @override
  State<StartTripScreen> createState() => _StartTripScreenState();
}

class _StartTripScreenState extends State<StartTripScreen> {
  static const primaryBlue = Color(0xFF2563EB);

  bool locationEnabled = false;
  bool cameraEnabled = false;
  bool isLoading = false;

  double distanceKm = 5;

  final _nameCtrl = TextEditingController(text: 'WS Smoke Test');

  Position? _pos;
  StreamSubscription<Position>? _posSub;

  bool get canStart => locationEnabled && cameraEnabled && !isLoading;

  @override
  void dispose() {
    _posSub?.cancel();
    _nameCtrl.dispose();
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
  Future<String?> _readAuthToken() async {
    return await TokenStorage.read();
  }

  Future<void> _createSessionAndGo() async {
    setState(() => isLoading = true);

    double lat = _pos?.latitude ?? 0;
    double lng = _pos?.longitude ?? 0;

    try {
      final res = await ApiClient.dio.post(
        '/api/sessions',
        data: {
          'name': _nameCtrl.text,
          'distanceKm': distanceKm.toInt(),
          'locationEnabled': locationEnabled,
          'cameraEnabled': cameraEnabled,
          'lat': lat,
          'lng': lng,
        },
      );

      final data = res.data is Map
          ? res.data
          : jsonDecode(res.data as String);

      final sessionId =
          (data['id'] ?? data['_id'] ?? data['sessionId']).toString();

      final token = (await _readAuthToken()) ?? '';

      if (!mounted) return;
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) => LiveMonitoringScreen(
            sessionId: sessionId,
            token: token,
            driverName: _nameCtrl.text,
          ),
        ),
      );
    } catch (e) {
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
        child: Column(children: [

          // ========= SAFETY CARD =========
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

                _switchTile(
                  title: 'Location',
                  subtitle: 'Track distance accurately',
                  value: locationEnabled,
                  onChanged: (v) async {
                    setState(() => locationEnabled = v);
                    v ? await _startLocation() : await _stopLocation();
                    if (!v) cameraEnabled = false;
                  },
                ),

                _switchTile(
                  title: 'Camera',
                  subtitle:
                      'Monitor driver behavior – face/hands only\nOnly cropped driver view; no raw video stored.',
                  value: cameraEnabled,
                  onChanged:
                      locationEnabled ? (v) => setState(() => cameraEnabled = v) : null,
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
                const SizedBox(height: 12),
                const Text('Choose total trip distance.',
                    style: TextStyle(color: Colors.grey)),

                const SizedBox(height: 24),

                Center(
                  child: Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(
                      color: primaryBlue,
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: Text(
                      '${distanceKm.toStringAsFixed(1)} km',
                      style: const TextStyle(
                          color: Colors.white, fontWeight: FontWeight.bold),
                    ),
                  ),
                ),

                Slider(
                  min: 1,
                  max: 50,
                  divisions: 49,
                  value: distanceKm,
                  activeColor: primaryBlue,
                  onChanged: (v) => setState(() => distanceKm = v),
                ),

                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: const [
                    Text('1'), Text('5'), Text('10'),
                    Text('20'), Text('30'), Text('40'), Text('50'),
                  ],
                )
              ],
            ),
          ),

          const SizedBox(height: 16),

          // ========= TIPS =========
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: const Color(0xFFEFF6FF),
              borderRadius: BorderRadius.circular(16),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: const [
                Text('Tips',
                    style: TextStyle(
                        color: primaryBlue,
                        fontWeight: FontWeight.bold)),
                SizedBox(height: 8),
                Text('• Mount on dashboard'),
                Text('• Face & shoulders visible'),
                Text('• Volume on'),
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
                    canStart ? primaryBlue : Colors.grey.shade300,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(14),
                ),
              ),
              child: const Text('Start Monitoring',
                  style: TextStyle(fontWeight: FontWeight.bold)),
            ),
          ),

          const SizedBox(height: 12),

          TextButton(
            onPressed: () {},
            child: const Text('View Previous Trips',
                style: TextStyle(color: primaryBlue)),
          )
        ]),
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

  static Widget _switchTile({
    required String title,
    required String subtitle,
    required bool value,
    ValueChanged<bool>? onChanged,
  }) {
    return SwitchListTile(
      contentPadding: EdgeInsets.zero,
      title: Text(title, style: const TextStyle(fontWeight: FontWeight.w600)),
      subtitle: Text(subtitle),
      value: value,
      activeColor: primaryBlue,
      onChanged: onChanged,
    );
  }

  void _toast(String msg) {
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text(msg)));
  }
}
