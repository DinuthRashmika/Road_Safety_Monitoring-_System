import 'dart:async';
import 'dart:convert';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'live_monitoring_screen.dart';
import '../core/api_client.dart';
import '../core/token_storage.dart';

// =================== CONFIG ===================
const String kApiBase = 'http://127.0.0.1:8000';

class StartTripScreen extends StatefulWidget {
  const StartTripScreen({super.key});
  @override
  State<StartTripScreen> createState() => _StartTripScreenState();
}

class _StartTripScreenState extends State<StartTripScreen> {
  // Palette
  static const primary = Color(0xFF2563EB);
  static const primaryDeep = Color(0xFF1D4ED8);
  static const primaryLight = Color(0xFFEFF6FF);
  static const ink = Color(0xFF0E1113);
  static const grayInactive = Color(0xFF8A8F98);
  static const grayBorder = Color(0xFFDADDE1);
  static const grayBg = Color(0xFFF1F2F4);

  bool locationOn = false;
  bool cameraOn = false;

  final _nameCtrl = TextEditingController(text: 'WS Smoke Test');
  Position? _pos;
  StreamSubscription<Position>? _posSub;

  @override
  void dispose() {
    _posSub?.cancel();
    _nameCtrl.dispose();
    super.dispose();
  }

  // ---- GPS ----
  Future<void> _startLocation() async {
    final enabled = await Geolocator.isLocationServiceEnabled();
    if (!enabled) {
      _toast('Please enable device Location (GPS).');
      await Geolocator.openLocationSettings();
      return;
    }
    var perm = await Geolocator.checkPermission();
    if (perm == LocationPermission.denied) {
      perm = await Geolocator.requestPermission();
    }
    if (perm == LocationPermission.denied || perm == LocationPermission.deniedForever) {
      _toast('Location permission denied.');
      return;
    }
    _posSub?.cancel();
    _posSub = Geolocator.getPositionStream(
      locationSettings: const LocationSettings(
        accuracy: LocationAccuracy.best,
        distanceFilter: 5,
      ),
    ).listen((p) => setState(() => _pos = p));
    try {
      final now = await Geolocator.getCurrentPosition(desiredAccuracy: LocationAccuracy.high);
      setState(() => _pos = now);
    } catch (_) {}
  }

  Future<void> _stopLocation() async {
    await _posSub?.cancel();
    _posSub = null;
    setState(() => _pos = null);
  }

Future<String?> _readAuthToken() async {
  final sp = await TokenStorage.read(); // SharedPreferences?
  return sp;        // <-- use ?.
}

  // ---- Create session & navigate ----
  Future<void> _createSessionAndGo() async {
    final name = _nameCtrl.text.trim().isEmpty ? 'WS Smoke Test' : _nameCtrl.text.trim();

    double lat = 0, lng = 0;
    if (_pos == null) {
      try {
        final p = await Geolocator.getCurrentPosition(desiredAccuracy: LocationAccuracy.medium);
        lat = p.latitude;
        lng = p.longitude;
      } catch (_) {}
    } else {
      lat = _pos!.latitude;
      lng = _pos!.longitude;
    }

    final dio = Dio(BaseOptions(baseUrl: kApiBase));
    try {
      final res = await ApiClient.dio.post('/api/sessions', data: {
        'name': name
      });

      final data = res.data is Map ? (res.data as Map) : jsonDecode(res.data as String);
      final sessionId = (data['id'] ?? data['_id'] ?? data['sessionId'] ?? '').toString();
      if (sessionId.isEmpty) throw Exception('Missing session id.');

      final token = (await _readAuthToken()) ?? ''; // pass empty if you don’t use auth
      if (!mounted) return;
      Navigator.of(context).push(
        MaterialPageRoute(
          builder: (_) => LiveMonitoringScreen(
            sessionId: sessionId,
            token: token,
            driverName: name,
          ),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      _toast('Create session failed: $e');
    }
  }

  // ---- UI ----
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new, color: ink),
          onPressed: () => Navigator.of(context).maybePop(),
        ),
        title: const Text('Start Trip', style: TextStyle(color: ink, fontWeight: FontWeight.w700)),
        centerTitle: true,
        backgroundColor: Colors.white,
        elevation: 0.5,
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _card(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Driver Name',
                    style: TextStyle(fontWeight: FontWeight.w700, fontSize: 16, color: ink)),
                const SizedBox(height: 8),
                TextField(
                  controller: _nameCtrl,
                  decoration: InputDecoration(
                    hintText: 'Enter your name',
                    contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                      borderSide: const BorderSide(color: grayBorder),
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),
          _card(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Enable Safety Features',
                    style: TextStyle(fontWeight: FontWeight.w700, fontSize: 16, color: ink)),
                const SizedBox(height: 12),
                _rowToggle(
                  title: 'Location',
                  subtitle: 'Track distance accurately',
                  value: locationOn,
                  onChanged: (v) async {
                    setState(() => locationOn = v);
                    if (v) {
                      await _startLocation();
                    } else {
                      await _stopLocation();
                      setState(() => cameraOn = false);
                    }
                  },
                ),
                if (_pos != null)
                  Padding(
                    padding: const EdgeInsets.only(left: 4.0, top: 6),
                    child: Row(
                      children: [
                        const Icon(Icons.my_location, size: 16, color: primary),
                        const SizedBox(width: 6),
                        Text(
                          'Lat: ${_pos!.latitude.toStringAsFixed(6)}, '
                          'Lng: ${_pos!.longitude.toStringAsFixed(6)}',
                          style: const TextStyle(fontSize: 12, color: grayInactive),
                        ),
                      ],
                    ),
                  ),
                const SizedBox(height: 8),
                _rowToggle(
                  title: 'Camera',
                  subtitle: 'Monitor driver behavior - face/hands only',
                  value: cameraOn,
                  onChanged: locationOn ? (v) => setState(() => cameraOn = v) : null,
                ),
                const SizedBox(height: 8),
                const Center(
                  child: Text(
                    'Only cropped driver view; no raw video stored.',
                    style: TextStyle(fontSize: 12, color: grayInactive),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),
          ElevatedButton(
            onPressed: (locationOn && cameraOn) ? _createSessionAndGo : null,
            style: ElevatedButton.styleFrom(
              backgroundColor: primary,
              foregroundColor: Colors.white,
              minimumSize: const Size.fromHeight(52),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              textStyle: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16),
            ),
            child: const Text('Start Monitoring'),
          ),
        ],
      ),
    );
  }

  static Widget _card({required Widget child}) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border.all(color: grayBg),
        borderRadius: BorderRadius.circular(16),
        boxShadow: const [BoxShadow(color: Colors.black12, blurRadius: 6, offset: Offset(0, 2))],
      ),
      padding: const EdgeInsets.all(16),
      child: child,
    );
  }

  Widget _rowToggle({
    required String title,
    required String subtitle,
    required bool value,
    ValueChanged<bool>? onChanged,
  }) {
    return Row(
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(title, style: const TextStyle(fontWeight: FontWeight.w600, color: ink)),
              const SizedBox(height: 2),
              Text(subtitle, style: const TextStyle(fontSize: 13, color: grayInactive)),
            ],
          ),
        ),
        Switch.adaptive(
          value: value,
          onChanged: onChanged,
          activeColor: Colors.white,
          activeTrackColor: primary,
          inactiveTrackColor: const Color(0xFFE5E7EB),
        ),
      ],
    );
  }

  void _toast(String msg) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
  }
}
