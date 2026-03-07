import 'dart:convert';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../models/owner.dart';
import '../models/vehicle.dart';
import '../services/owner_service.dart';
import '../services/vehicle_service.dart';
import '../core/token_storage.dart';
import '../core/api_client.dart';

// ✅ NEW
import '../services/notification_service.dart';
import '../models/notification_model.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  Owner? _owner;
  List<Vehicle> _vehicles = [];
  bool _loading = true;

  // ✅ NEW: real protective alerts from backend (using dedicated endpoint)
  List<NotificationModel> _protective = [];

  // ✅ NEW: recent real trips from /api/sessions
  List<_TripItem> _trips = [];

  // ✅ NEW: unseen protective count for badge
  int get _unseenProtectiveCount =>
      _protective.where((n) => n.isRead == false).length;

  Future<void> _load() async {
    try {
      final me = await OwnerService.me();
      final v = await VehicleService.mine();

      // ✅ protective fetch must NOT break owner/vehicle load
      List<NotificationModel> protective = [];
      try {
        protective = await NotificationService.getProtectiveAlerts();
      } catch (_) {
        protective = [];
      }

      // ✅ NEW: recent trips fetch must NOT break page load
      List<_TripItem> recentTrips = [];
      try {
        recentTrips = await _fetchRecentTrips();
      } catch (_) {
        recentTrips = [];
      }

      if (!mounted) return;

      setState(() {
        _owner = me;
        _vehicles = v;
        _protective = protective.take(3).toList();
        _trips = recentTrips;
      });
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  // ✅ NEW: fetch latest 3 trips from same API used in PreviousTripsScreen
  Future<List<_TripItem>> _fetchRecentTrips() async {
    try {
      String? token;
      try {
        token = await TokenStorage.read();
      } catch (_) {
        token = null;
      }

      final Map<String, String> headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      };

      if (token != null && token.isNotEmpty) {
        headers['Authorization'] = 'Bearer $token';
      }

      final response = await ApiClient.dio.get(
        '/api/sessions',
        options: Options(headers: headers),
      );

      dynamic responseData;
      if (response.data is String) {
        responseData = jsonDecode(response.data as String);
      } else {
        responseData = response.data;
      }

      List<dynamic> trips = [];
      if (responseData is List) {
        trips = responseData;
      } else if (responseData is Map && responseData.containsKey('data')) {
        trips = responseData['data'] is List
            ? responseData['data'] as List<dynamic>
            : [];
      }

      // Sort latest first using startedAt
      trips.sort((a, b) {
        final aDate = DateTime.tryParse((a['startedAt'] ?? '').toString()) ??
            DateTime.fromMillisecondsSinceEpoch(0);
        final bDate = DateTime.tryParse((b['startedAt'] ?? '').toString()) ??
            DateTime.fromMillisecondsSinceEpoch(0);
        return bDate.compareTo(aDate);
      });

      final latest3 = trips.take(3).toList();

      return latest3.map((trip) {
        final tripName =
            (trip['name'] ?? trip['route'] ?? 'Unnamed Trip').toString();
        final startedAt = (trip['startedAt'] ?? '').toString();
        final endedAt = trip['endedAt']?.toString();

        return _TripItem(
          date: _formatTripDate(startedAt),
          route: tripName,
          distance: _buildTripDistanceText(trip),
          duration: _calculateTripDuration(startedAt, endedAt),
        );
      }).toList();
    } catch (_) {
      return [];
    }
  }

  // ✅ NEW
  String _formatTripDate(String dateString) {
    try {
      final date = DateTime.parse(dateString).toLocal();
      return DateFormat('MMM dd, yyyy').format(date);
    } catch (_) {
      return 'Unknown date';
    }
  }

  // ✅ NEW
  String _calculateTripDuration(String startTime, String? endTime) {
    try {
      final start = DateTime.parse(startTime);
      final end = endTime != null ? DateTime.parse(endTime) : DateTime.now();
      final duration = end.difference(start);

      if (duration.inHours > 0) {
        return '${duration.inHours}h ${duration.inMinutes % 60}m';
      }
      return '${duration.inMinutes} min';
    } catch (_) {
      return 'Ongoing';
    }
  }

  // ✅ NEW
  String _buildTripDistanceText(dynamic trip) {
    final possibleKeys = [
      'distance',
      'distanceKm',
      'distance_km',
      'totalDistance',
      'tripDistance'
    ];

    for (final key in possibleKeys) {
      final value = trip[key];
      if (value != null) {
        final number = double.tryParse(value.toString());
        if (number != null) {
          return '${number.toStringAsFixed(1)} km';
        }
      }
    }

    return '-- km';
  }

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _logout() async {
    await TokenStorage.clear();
    if (!mounted) return;
    Navigator.of(context).pushNamedAndRemoveUntil('/login', (r) => false);
  }

  @override
  Widget build(BuildContext context) {
    final name = _owner?.fullName.split(' ').first ?? 'Ethan';

    return Scaffold(
      backgroundColor: Colors.black,
      bottomNavigationBar: _EnhancedBottomBar(
        currentIndex: 0,
        onTap: (i) {
          if (i == 1) Navigator.pushNamed(context, '/profile');
          if (i == 2) Navigator.pushNamed(context, '/violations');
          if (i == 3) Navigator.pushNamed(context, '/alerts');
        },
      ),
      body: _loading
          ? const Center(
              child: CircularProgressIndicator(
                strokeWidth: 2,
                valueColor: AlwaysStoppedAnimation(Color(0xFF2563EB)),
              ),
            )
          : RefreshIndicator(
              onRefresh: _load,
              color: const Color(0xFF2563EB),
              child: CustomScrollView(
                primary: true,
                slivers: [
                  SliverAppBar(
                    backgroundColor: Colors.black,
                    floating: true,
                    pinned: false,
                    elevation: 0,
                    toolbarHeight: 80,
                    title: Padding(
                      padding: const EdgeInsets.only(top: 10),
                      child: Row(
                        children: [
                          Container(
                            width: 48,
                            height: 48,
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              image: _owner?.imageUrl != null
                                  ? DecorationImage(
                                      image: NetworkImage(_owner!.imageUrl!),
                                      fit: BoxFit.cover,
                                    )
                                  : null,
                              color: Colors.orange.shade100,
                            ),
                            child: _owner?.imageUrl == null
                                ? Image.network(
                                    'https://i.pravatar.cc/150?img=11',
                                    fit: BoxFit.cover,
                                  )
                                : null,
                          ),
                          const SizedBox(width: 12),
                          Text(
                            'Welcome, $name',
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 22,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const Spacer(),

                          // ✅ UPDATED: Bell icon shows unseen count badge
                          IconButton(
                            onPressed: () =>
                                Navigator.pushNamed(context, '/alerts'),
                            icon: Stack(
                              clipBehavior: Clip.none,
                              children: [
                                const Icon(Icons.notifications_outlined,
                                    color: Colors.white, size: 28),
                                if (_unseenProtectiveCount > 0)
                                  Positioned(
                                    right: -2,
                                    top: -4,
                                    child: Container(
                                      padding: const EdgeInsets.symmetric(
                                          horizontal: 6, vertical: 2),
                                      decoration: BoxDecoration(
                                        color: const Color(0xFF2563EB),
                                        borderRadius: BorderRadius.circular(12),
                                        border: Border.all(
                                          color: Colors.black,
                                          width: 2,
                                        ),
                                      ),
                                      child: Text(
                                        _unseenProtectiveCount > 99
                                            ? '99+'
                                            : '$_unseenProtectiveCount',
                                        style: const TextStyle(
                                          color: Colors.white,
                                          fontSize: 10,
                                          fontWeight: FontWeight.w800,
                                        ),
                                      ),
                                    ),
                                  ),
                              ],
                            ),
                          ),
                          IconButton(
                            onPressed: () {},
                            icon: const Icon(Icons.search,
                                color: Colors.white, size: 28),
                          ),
                        ],
                      ),
                    ),
                  ),
                  SliverList(
                    delegate: SliverChildListDelegate([
                      if (_vehicles.isEmpty)
                        Padding(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 20, vertical: 10),
                          child: _AddVehicleBanner(
                            onAdd: () =>
                                Navigator.pushNamed(context, '/vehicle-add')
                                    .then((_) => _load()),
                            onSkip: () {},
                          ),
                        ),
                      const SizedBox(height: 24),
                      Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 20),
                        child: _EnhancedQuickActions(
                          onAdd: () =>
                              Navigator.pushNamed(context, '/vehicle-add')
                                  .then((_) => _load()),
                          onMyVehicles: () =>
                              Navigator.pushNamed(context, '/vehicles')
                                  .then((_) => _load()),
                          onTrips: () => Navigator.pushNamed(context, '/trips'),
                          onViolations: () =>
                              Navigator.pushNamed(context, '/violations'),
                        ),
                      ),
                      const SizedBox(height: 24),
                      if (_vehicles.isNotEmpty) ...[
                        Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 20),
                          child: _EnhancedSectionHeader(
                            title: 'My Vehicles',
                            subtitle:
                                '${_vehicles.length} vehicle${_vehicles.length > 1 ? 's' : ''} registered',
                            actionText: 'View all',
                            onAction: () =>
                                Navigator.pushNamed(context, '/vehicles')
                                    .then((_) => _load()),
                          ),
                        ),
                        const SizedBox(height: 20),
                        SizedBox(
                          height: 250,
                          child: ListView.separated(
                            primary: false,
                            shrinkWrap: true,
                            scrollDirection: Axis.horizontal,
                            physics: const BouncingScrollPhysics(),
                            padding: const EdgeInsets.symmetric(horizontal: 20),
                            itemCount: _vehicles.length,
                            separatorBuilder: (_, __) =>
                                const SizedBox(width: 16),
                            itemBuilder: (_, i) {
                              final v = _vehicles[i];
                              String? cover;
                              if (v.images is Map) {
                                final map = v.images as Map<dynamic, dynamic>;
                                final any = map['front'] ??
                                    map['plate'] ??
                                    map['back'] ??
                                    map['side'];
                                if (any is String &&
                                    any.isNotEmpty &&
                                    any.startsWith('http')) {
                                  cover = any;
                                }
                              }
                              final subtitle =
                                  ((v.vehicleModel ?? v.vehicleType) ?? '')
                                      .toString()
                                      .trim();
                              return _EnhancedVehicleCard(
                                plate: v.plateNo,
                                subtitle: subtitle,
                                imageUrl: cover,
                                active: true,
                                onTap: () => Navigator.pushNamed(
                                    context, '/vehicle-detail',
                                    arguments: v.id),
                              );
                            },
                          ),
                        ),
                        const SizedBox(height: 12),
                      ],

                      // ✅ Protective Alerts Section
                      Padding(
                        padding: const EdgeInsets.fromLTRB(20, 32, 20, 16),
                        child: _EnhancedSectionHeader(
                          title: 'Protective Alerts',
                          subtitle: 'important notifications',
                          actionText: 'View all',
                          onAction: () =>
                              Navigator.pushNamed(context, '/alerts'),
                        ),
                      ),
                      if (_protective.isEmpty)
                        Padding(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 20, vertical: 6),
                          child: _EnhancedAlertCard(
                            title: 'No protective alerts',
                            subtitle: 'You have no nearby safety alerts yet.',
                            cta: 'View',
                            onPressed: () =>
                                Navigator.pushNamed(context, '/alerts'),
                          ),
                        )
                      else
                        ..._protective.map((n) => Padding(
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 20, vertical: 6),
                              child: _EnhancedAlertCard(
                                title: 'Protective Alert',
                                subtitle: '${n.message}\n${n.location}',
                                cta: n.isRead ? 'Viewed' : 'Open',
                                onPressed: () async {
                                  await NotificationService
                                      .markProtectiveAsRead(n.id);
                                  if (!context.mounted) return;
                                  _load();
                                },
                              ),
                            )),

                      // ✅ Trip History Section
                      Padding(
                        padding: const EdgeInsets.fromLTRB(20, 32, 20, 16),
                        child: _EnhancedSectionHeader(
                          title: 'Recent Trips',
                          subtitle: 'Your latest journeys',
                          actionText: 'View all',
                          onAction: () =>
                              Navigator.pushNamed(context, '/trips'),
                        ),
                      ),
                      Container(
                        margin: const EdgeInsets.symmetric(horizontal: 20),
                        decoration: BoxDecoration(
                          color: Colors.grey.shade900,
                          borderRadius: BorderRadius.circular(20),
                          boxShadow: [
                            BoxShadow(
                              color: Colors.black.withOpacity(0.3),
                              blurRadius: 20,
                              offset: const Offset(0, 4),
                            ),
                          ],
                          border: Border.all(
                            color: Colors.grey.shade800,
                            width: 1,
                          ),
                        ),
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(20),
                          child: _trips.isEmpty
                              ? Padding(
                                  padding: const EdgeInsets.all(20),
                                  child: Row(
                                    children: [
                                      Container(
                                        width: 44,
                                        height: 44,
                                        decoration: BoxDecoration(
                                          color: const Color(0xFF0C4A6E),
                                          borderRadius:
                                              BorderRadius.circular(12),
                                        ),
                                        child: const Icon(
                                          Icons.route_rounded,
                                          color: Color(0xFF38BDF8),
                                          size: 20,
                                        ),
                                      ),
                                      const SizedBox(width: 16),
                                      Expanded(
                                        child: Text(
                                          'No recent trips found',
                                          style: TextStyle(
                                            color: Colors.grey.shade400,
                                            fontSize: 14,
                                            fontWeight: FontWeight.w600,
                                          ),
                                        ),
                                      ),
                                    ],
                                  ),
                                )
                              : Column(
                                  children: [
                                    for (int i = 0; i < _trips.length; i++)
                                      _EnhancedTripRow(
                                        item: _trips[i],
                                        isLast: i == _trips.length - 1,
                                      ),
                                  ],
                                ),
                        ),
                      ),

                      // Live Monitoring Button
                      Padding(
                        padding: const EdgeInsets.fromLTRB(20, 24, 20, 8),
                        child: Container(
                          decoration: BoxDecoration(
                            gradient: const LinearGradient(
                              colors: [
                                Color(0xFF2563EB),
                                Color(0xFF1D4ED8),
                              ],
                            ),
                            borderRadius: BorderRadius.circular(16),
                            boxShadow: [
                              BoxShadow(
                                color: const Color(0xFF2563EB).withOpacity(0.5),
                                blurRadius: 15,
                                offset: const Offset(0, 6),
                              ),
                            ],
                          ),
                          child: ElevatedButton(
                            onPressed: () =>
                                Navigator.pushNamed(context, '/monitor'),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.transparent,
                              shadowColor: Colors.transparent,
                              foregroundColor: Colors.white,
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 24, vertical: 16),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(16),
                              ),
                            ),
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Container(
                                  padding: const EdgeInsets.all(6),
                                  decoration: BoxDecoration(
                                    color: Colors.white.withOpacity(0.2),
                                    shape: BoxShape.circle,
                                  ),
                                  child: const Icon(Icons.videocam_rounded,
                                      size: 20),
                                ),
                                const SizedBox(width: 12),
                                const Text(
                                  'Live Monitoring',
                                  style: TextStyle(
                                    fontSize: 16,
                                    fontWeight: FontWeight.w700,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(height: 32),
                    ]),
                  ),
                ],
              ),
            ),
    );
  }
}

/* ====================== UI COMPONENTS (UNCHANGED) ====================== */

class _AddVehicleBanner extends StatelessWidget {
  final VoidCallback onAdd;
  final VoidCallback onSkip;

  const _AddVehicleBanner({required this.onAdd, required this.onSkip});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: Colors.grey.shade900,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: Colors.grey.shade800),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Add your first vehicle',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: Colors.white,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Get started by adding a vehicle to your\naccount.',
            style: TextStyle(
              fontSize: 14,
              color: Colors.grey.shade400,
              height: 1.5,
            ),
          ),
          const SizedBox(height: 20),
          Row(
            children: [
              ElevatedButton(
                onPressed: onAdd,
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF2563EB),
                  foregroundColor: Colors.white,
                  elevation: 0,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(30),
                  ),
                  padding:
                      const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                ),
                child: const Text(
                  'Add Vehicle',
                  style: TextStyle(
                    fontWeight: FontWeight.w600,
                    fontSize: 14,
                  ),
                ),
              ),
              const SizedBox(width: 16),
              TextButton(
                onPressed: onSkip,
                style: TextButton.styleFrom(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                ),
                child: const Text(
                  'Skip for now',
                  style: TextStyle(
                    color: Color(0xFF2563EB),
                    fontWeight: FontWeight.w600,
                    fontSize: 14,
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _EnhancedQuickActions extends StatelessWidget {
  const _EnhancedQuickActions({
    required this.onAdd,
    required this.onMyVehicles,
    required this.onTrips,
    required this.onViolations,
  });

  final VoidCallback onAdd;
  final VoidCallback onMyVehicles;
  final VoidCallback onTrips;
  final VoidCallback onViolations;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        _QuickActionSquare(
            icon: Icons.add, label: 'Add Vehicle', onTap: onAdd),
        _QuickActionSquare(
            icon: Icons.directions_car_outlined,
            label: 'My Vehicles',
            onTap: onMyVehicles),
        _QuickActionSquare(
            icon: Icons.assignment_outlined,
            label: 'Trip History',
            onTap: onTrips),
        _QuickActionSquare(
            icon: Icons.warning_amber_rounded,
            label: 'Violations',
            onTap: onViolations),
      ],
    );
  }
}

class _QuickActionSquare extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;

  const _QuickActionSquare(
      {required this.icon, required this.label, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        GestureDetector(
          onTap: onTap,
          child: Container(
            width: 64,
            height: 64,
            decoration: BoxDecoration(
              color: Colors.grey.shade900,
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: Colors.grey.shade800),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.2),
                  blurRadius: 10,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: Icon(icon, color: Colors.grey.shade300, size: 28),
          ),
        ),
        const SizedBox(height: 8),
        Text(
          label,
          style: TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.w600,
            color: Colors.grey.shade300,
          ),
        ),
      ],
    );
  }
}

class _EnhancedSectionHeader extends StatelessWidget {
  const _EnhancedSectionHeader({
    required this.title,
    required this.subtitle,
    this.actionText,
    this.onAction,
  });

  final String title;
  final String subtitle;
  final String? actionText;
  final VoidCallback? onAction;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.w800,
                    color: Colors.white,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  subtitle,
                  style: TextStyle(
                    fontSize: 14,
                    color: Colors.grey.shade400,
                  ),
                ),
              ],
            ),
            const Spacer(),
            if (actionText != null)
              Container(
                decoration: BoxDecoration(
                  color: Colors.grey.shade800,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: TextButton(
                  onPressed: onAction,
                  style: TextButton.styleFrom(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                  ),
                  child: Text(
                    actionText!,
                    style: TextStyle(
                      fontWeight: FontWeight.w600,
                      color: Colors.grey.shade300,
                      fontSize: 13,
                    ),
                  ),
                ),
              ),
          ],
        ),
      ],
    );
  }
}

class _EnhancedVehicleCard extends StatelessWidget {
  const _EnhancedVehicleCard({
    required this.plate,
    required this.subtitle,
    this.imageUrl,
    this.active = false,
    this.onTap,
  });

  final String plate;
  final String subtitle;
  final String? imageUrl;
  final bool active;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 240,
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(20),
          child: Container(
            decoration: BoxDecoration(
              color: Colors.grey.shade900,
              borderRadius: BorderRadius.circular(20),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.3),
                  blurRadius: 15,
                  offset: const Offset(0, 4),
                ),
              ],
              border: Border.all(color: Colors.grey.shade800),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  height: 120,
                  width: double.infinity,
                  decoration: BoxDecoration(
                    borderRadius: const BorderRadius.only(
                      topLeft: Radius.circular(20),
                      topRight: Radius.circular(20),
                    ),
                    gradient: LinearGradient(
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                      colors: [
                        Colors.grey.shade900,
                        Colors.grey.shade800,
                      ],
                    ),
                  ),
                  child: ClipRRect(
                    borderRadius: const BorderRadius.only(
                      topLeft: Radius.circular(20),
                      topRight: Radius.circular(20),
                    ),
                    child: _VehicleImageHandler(imageUrl: imageUrl),
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        plate,
                        style: const TextStyle(
                          fontWeight: FontWeight.w800,
                          fontSize: 16,
                          color: Colors.white,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      const SizedBox(height: 4),
                      SizedBox(
                        height: 20,
                        child: Text(
                          subtitle,
                          style: TextStyle(
                            color: Colors.grey.shade400,
                            fontSize: 13,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      const SizedBox(height: 12),
                      if (active)
                        Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 12, vertical: 6),
                          decoration: BoxDecoration(
                            color: const Color(0xFF064E3B).withOpacity(0.3),
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Container(
                                width: 6,
                                height: 6,
                                decoration: const BoxDecoration(
                                  color: Color(0xFF10B981),
                                  shape: BoxShape.circle,
                                ),
                              ),
                              const SizedBox(width: 6),
                              const Text(
                                'Active',
                                style: TextStyle(
                                  color: Color(0xFF10B981),
                                  fontSize: 12,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                            ],
                          ),
                        ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _VehicleImageHandler extends StatelessWidget {
  final String? imageUrl;
  const _VehicleImageHandler({this.imageUrl});

  @override
  Widget build(BuildContext context) {
    if (imageUrl == null ||
        imageUrl!.isEmpty ||
        !imageUrl!.startsWith('http')) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.grey.shade800,
                shape: BoxShape.circle,
              ),
              child: Icon(
                Icons.directions_car_filled_rounded,
                color: Colors.grey.shade400,
                size: 32,
              ),
            ),
          ],
        ),
      );
    }
    return Image.network(
      imageUrl!,
      fit: BoxFit.cover,
      width: double.infinity,
      height: double.infinity,
      errorBuilder: (context, error, stackTrace) {
        return Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.grey.shade800,
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  Icons.directions_car_filled_rounded,
                  color: Colors.grey.shade400,
                  size: 32,
                ),
              ),
            ],
          ),
        );
      },
      loadingBuilder: (context, child, loadingProgress) {
        if (loadingProgress == null) return child;
        return const Center(
          child: CircularProgressIndicator(
            color: Color(0xFF2563EB),
          ),
        );
      },
    );
  }
}

class _EnhancedAlertCard extends StatelessWidget {
  const _EnhancedAlertCard({
    required this.title,
    required this.subtitle,
    required this.cta,
    this.onPressed,
  });

  final String title;
  final String subtitle;
  final String cta;
  final VoidCallback? onPressed;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.grey.shade900,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.3),
            blurRadius: 10,
            offset: const Offset(0, 2),
          ),
        ],
        border: Border.all(color: Colors.grey.shade800),
      ),
      child: Row(
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: const Color(0xFF431C1C),
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Icon(
              Icons.warning_amber_rounded,
              color: Color(0xFFF87171),
              size: 20,
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    fontWeight: FontWeight.w700,
                    fontSize: 15,
                    color: Colors.white,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  subtitle,
                  style: TextStyle(
                    color: Colors.grey.shade400,
                    fontSize: 13,
                    height: 1.3,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 12),
          Container(
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [
                  Color(0xFF7F1D1D),
                  Color(0xFFDC2626),
                ],
              ),
              borderRadius: BorderRadius.circular(10),
            ),
            child: ElevatedButton(
              onPressed: onPressed,
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.transparent,
                shadowColor: Colors.transparent,
                foregroundColor: Colors.white,
                padding:
                    const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(10),
                ),
              ),
              child: Text(
                cta,
                style: const TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _EnhancedTripRow extends StatelessWidget {
  const _EnhancedTripRow({required this.item, required this.isLast});
  final _TripItem item;
  final bool isLast;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        border: isLast
            ? null
            : Border(
                bottom: BorderSide(
                  color: Colors.grey.shade800,
                  width: 1,
                ),
              ),
      ),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Row(
          children: [
            Container(
              width: 44,
              height: 44,
              decoration: BoxDecoration(
                color: const Color(0xFF0C4A6E),
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Icon(
                Icons.route_rounded,
                color: Color(0xFF38BDF8),
                size: 20,
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    item.route,
                    style: const TextStyle(
                      fontWeight: FontWeight.w600,
                      fontSize: 15,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    item.date,
                    style: TextStyle(
                      color: Colors.grey.shade400,
                      fontSize: 13,
                    ),
                  ),
                ],
              ),
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  item.distance,
                  style: const TextStyle(
                    fontWeight: FontWeight.w700,
                    fontSize: 15,
                    color: Colors.white,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  item.duration,
                  style: TextStyle(
                    color: Colors.grey.shade400,
                    fontSize: 13,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _EnhancedBottomBar extends StatelessWidget {
  const _EnhancedBottomBar({required this.currentIndex, required this.onTap});
  final int currentIndex;
  final ValueChanged<int> onTap;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.black,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.3),
            blurRadius: 20,
            offset: const Offset(0, -5),
          ),
        ],
        border: Border(
          top: BorderSide(
            color: Colors.grey.shade800,
            width: 1,
          ),
        ),
      ),
      child: SafeArea(
        top: false,
        child: SizedBox(
          height: 80,
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _EnhancedBottomBarItem(
                icon: Icons.home_outlined,
                activeIcon: Icons.home_rounded,
                label: 'Home',
                isActive: currentIndex == 0,
                onTap: () => onTap(0),
              ),
              _EnhancedBottomBarItem(
                icon: Icons.person_outline,
                activeIcon: Icons.person,
                label: 'Profile',
                isActive: currentIndex == 1,
                onTap: () => onTap(1),
              ),
              _EnhancedBottomBarItem(
                icon: Icons.report_gmailerrorred_outlined,
                activeIcon: Icons.report,
                label: 'Violations',
                isActive: currentIndex == 2,
                onTap: () => onTap(2),
              ),
              _EnhancedBottomBarItem(
                icon: Icons.shield_outlined,
                activeIcon: Icons.shield,
                label: 'Alerts',
                isActive: currentIndex == 3,
                onTap: () => onTap(3),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _EnhancedBottomBarItem extends StatelessWidget {
  const _EnhancedBottomBarItem({
    required this.icon,
    required this.activeIcon,
    required this.label,
    required this.isActive,
    required this.onTap,
  });

  final IconData icon;
  final IconData activeIcon;
  final String label;
  final bool isActive;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(
          color: isActive ? const Color(0xFF1E3A8A) : Colors.transparent,
          borderRadius: BorderRadius.circular(16),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              isActive ? activeIcon : icon,
              color: isActive
                  ? const Color(0xFF60A5FA)
                  : Colors.grey.shade500,
              size: 24,
            ),
            const SizedBox(height: 4),
            Text(
              label,
              style: TextStyle(
                color: isActive
                    ? const Color(0xFF60A5FA)
                    : Colors.grey.shade500,
                fontSize: 12,
                fontWeight: isActive ? FontWeight.w700 : FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _TripItem {
  final String date;
  final String route;
  final String distance;
  final String duration;
  const _TripItem({
    required this.date,
    required this.route,
    required this.distance,
    required this.duration,
  });
}