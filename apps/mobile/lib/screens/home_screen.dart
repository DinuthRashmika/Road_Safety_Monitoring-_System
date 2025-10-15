import 'package:flutter/material.dart';
import '../models/owner.dart';
import '../models/vehicle.dart';
import '../services/owner_service.dart';
import '../services/vehicle_service.dart';
import '../core/token_storage.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  Owner? _owner;
  List<Vehicle> _vehicles = [];
  bool _loading = true;

  // --- mock data for sections (replace with real later) ---
  final List<_AlertItem> _alerts = const [
    _AlertItem(
      title: 'Insurance expiring soon',
      subtitle: 'Honda Civic (XYZ 789) - Expires in 15 days',
      cta: 'Renew',
    ),
    _AlertItem(
      title: 'Service due',
      subtitle: 'Toyota Camry (ABC 123) - Next service at 30,000 km',
      cta: 'Book',
    ),
    _AlertItem(
      title: 'License renewal',
      subtitle: 'Your driving license expires on Oct 31, 2023',
      cta: 'View',
    ),
  ];

  final List<_TripItem> _trips = const [
    _TripItem(date: 'Aug 18, 2023', route: 'Downtown → Home', distance: '12.5 km', duration: '32 min'),
    _TripItem(date: 'Aug 17, 2023', route: 'Work → Gym',     distance: '5.2 km',  duration: '15 min'),
    _TripItem(date: 'Aug 16, 2023', route: 'Home → Airport',  distance: '28.1 km', duration: '45 min'),
  ];

  Future<void> _load() async {
    try {
      final me = await OwnerService.me();
      final v = await VehicleService.mine();
      setState(() {
        _owner = me;
        _vehicles = v;
      });
    } finally {
      setState(() => _loading = false);
    }
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
    final name = _owner?.fullName.split(' ').first ?? 'Driver';

    return Scaffold(
      backgroundColor: const Color(0xFFF7F8FA),
      bottomNavigationBar: _BottomBar(
        currentIndex: 0,
        onTap: (i) {
          if (i == 1) Navigator.pushNamed(context, '/profile');
          if (i == 2) Navigator.pushNamed(context, '/violations');
          if (i == 3) Navigator.pushNamed(context, '/alerts');
        },
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _load,
              child: CustomScrollView(
                slivers: [
                  // Header
                  SliverToBoxAdapter(
                    child: SafeArea(
                      bottom: false,
                      child: Padding(
                        padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
                        child: _HeaderBar(
                          title: 'Welcome, $name',
                          profileImage: _owner?.imageUrl,
                          onProfile: () => Navigator.pushNamed(context, '/profile').then((_) => _load()),
                          onBell: () => Navigator.pushNamed(context, '/alerts'),
                          onLogout: _logout,
                        ),
                      ),
                    ),
                  ),

                  // Promo card when no vehicles - BEAUTIFUL DESIGN
                  if (_vehicles.isEmpty)
                    SliverToBoxAdapter(
                      child: Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                        child: _BeautifulPromoCard(
                          onAdd: () => Navigator.pushNamed(context, '/vehicle-add').then((_) => _load()),
                          onSkip: () {},
                        ),
                      ),
                    ),

                  // Quick actions
                  SliverToBoxAdapter(
                    child: Padding(
                      padding: const EdgeInsets.fromLTRB(16, 14, 16, 16),
                      child: _QuickActions(
                        onAdd: () => Navigator.pushNamed(context, '/vehicle-add').then((_) => _load()),
                        onMyVehicles: () => Navigator.pushNamed(context, '/vehicles').then((_) => _load()),
                        onTrips: () => Navigator.pushNamed(context, '/trips'),
                        onViolations: () => Navigator.pushNamed(context, '/violations'),
                      ),
                    ),
                  ),

                  // My Vehicles
                  if (_vehicles.isNotEmpty) ...[
                    SliverToBoxAdapter(
                      child: Padding(
                        padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
                        child: _SectionHeader(
                          title: 'My Vehicles',
                          actionText: 'View all',
                          onAction: () => Navigator.pushNamed(context, '/vehicles').then((_) => _load()),
                        ),
                      ),
                    ),
                    SliverToBoxAdapter(
                      child: SizedBox(
                        height: 200, // ⬅️ taller to avoid overflow
                        child: ListView.separated(
                          padding: const EdgeInsets.symmetric(horizontal: 16),
                          scrollDirection: Axis.horizontal,
                          itemCount: _vehicles.length,
                          separatorBuilder: (_, __) => const SizedBox(width: 12),
                          itemBuilder: (_, i) {
                            final v = _vehicles[i];

                            // cover image (null-safe)
                            String? cover;
                            if (v.images is Map) {
                              final map = v.images as Map<dynamic, dynamic>;
                              final any = map['front'] ?? map['plate'];
                              if (any is String && any.isNotEmpty) cover = any;
                            }

                            // subtitle: prefer model, else type
                            final subtitle = ((v.vehicleModel ?? v.vehicleType) ?? '').toString().trim();

                            return _VehicleCard(
                              plate: v.plateNo,
                              subtitle: subtitle,
                              imageUrl: cover,
                              active: true,
                              onTap: () => Navigator.pushNamed(context, '/vehicle-detail', arguments: v.id),
                            );
                          },
                        ),
                      ),
                    ),
                  ],

                  // Protective Alerts
                  SliverToBoxAdapter(
                    child: Padding(
                      padding: const EdgeInsets.fromLTRB(16, 24, 16, 12),
                      child: _SectionHeader(
                        title: 'Protective Alerts',
                        actionText: 'View all alerts',
                        onAction: () => Navigator.pushNamed(context, '/alerts'),
                      ),
                    ),
                  ),
                  SliverList(
                    delegate: SliverChildBuilderDelegate(
                      (context, i) {
                        final a = _alerts[i];
                        return Padding(
                          padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
                          child: _AlertCard(
                            title: a.title,
                            subtitle: a.subtitle,
                            cta: a.cta,
                            onPressed: () {},
                          ),
                        );
                      },
                      childCount: _alerts.length,
                    ),
                  ),

                  // Trip History block
                  SliverToBoxAdapter(
                    child: Padding(
                      padding: const EdgeInsets.fromLTRB(16, 24, 16, 12),
                      child: _SectionHeader(
                        title: 'Trip History',
                        actionText: 'View all history',
                        onAction: () => Navigator.pushNamed(context, '/trips'),
                      ),
                    ),
                  ),
                  SliverToBoxAdapter(
                    child: Container(
                      margin: const EdgeInsets.symmetric(horizontal: 16),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(color: const Color(0xFFE6E9EF)),
                      ),
                      child: Column(
                        children: [
                          for (final t in _trips) _TripRow(item: t),
                        ],
                      ),
                    ),
                  ),
                  SliverToBoxAdapter(
                    child: Padding(
                      padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
                      child: Align(
                        alignment: Alignment.centerRight,
                        child: ElevatedButton.icon(
                          onPressed: () => Navigator.pushNamed(context, '/monitor'),
                          icon: const Icon(Icons.videocam_rounded, size: 18),
                          label: const Text('Live Monitoring'),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: const Color(0xFF2563EB),
                            foregroundColor: Colors.white,
                            elevation: 0,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12),
                            ),
                            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                          ),
                        ),
                      ),
                    ),
                  ),
                  const SliverToBoxAdapter(child: SizedBox(height: 24)),
                ],
              ),
            ),
    );
  }
}

/* ====================== UI bits ====================== */

class _HeaderBar extends StatelessWidget {
  const _HeaderBar({
    required this.title,
    this.profileImage,
    this.onProfile,
    this.onBell,
    this.onLogout,
  });

  final String title;
  final String? profileImage;
  final VoidCallback? onProfile;
  final VoidCallback? onBell;
  final VoidCallback? onLogout;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        GestureDetector(
          onTap: onProfile,
          child: Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: const Color(0xFFE8EEF6),
              borderRadius: BorderRadius.circular(12),
              image: profileImage != null && profileImage!.isNotEmpty
                  ? DecorationImage(
                      image: NetworkImage(profileImage!),
                      fit: BoxFit.cover,
                    )
                  : null,
            ),
            child: profileImage == null || profileImage!.isEmpty
                ? const Icon(Icons.person, color: Colors.black54)
                : null,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Text(
            title,
            style: const TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.w800,
              color: Colors.black87,
            ),
            overflow: TextOverflow.ellipsis,
          ),
        ),
        IconButton(
          onPressed: onBell,
          icon: const Icon(Icons.notifications_none_rounded, size: 24),
          padding: EdgeInsets.zero,
          constraints: const BoxConstraints(minWidth: 40, minHeight: 40),
        ),
        IconButton(
          onPressed: onLogout,
          icon: const Icon(Icons.logout, size: 20),
          padding: EdgeInsets.zero,
          constraints: const BoxConstraints(minWidth: 40, minHeight: 40),
        ),
      ],
    );
  }
}

class _BeautifulPromoCard extends StatelessWidget {
  const _BeautifulPromoCard({required this.onAdd, required this.onSkip});
  final VoidCallback onAdd;
  final VoidCallback onSkip;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            Color(0xFFEAF2FF),
            Color(0xFFF0F7FF),
          ],
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF2563EB).withOpacity(0.3)),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF2563EB).withOpacity(0.1),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Row(
        children: [
          // Text content
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Add your first vehicle',
                  style: TextStyle(
                    fontWeight: FontWeight.w800,
                    fontSize: 18,
                    color: Color(0xFF1E293B),
                  ),
                ),
                const SizedBox(height: 8),
                const Text(
                  'Get started by adding a vehicle to your account.',
                  style: TextStyle(
                    color: Color(0xFF64748B),
                    fontSize: 14,
                    height: 1.4,
                  ),
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    ElevatedButton(
                      onPressed: onAdd,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF2563EB),
                        foregroundColor: Colors.white,
                        elevation: 0,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                      ),
                      child: const Text(
                        'Add Vehicle',
                        style: TextStyle(
                          fontWeight: FontWeight.w600,
                          fontSize: 14,
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    TextButton(
                      onPressed: onSkip,
                      style: TextButton.styleFrom(
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                      ),
                      child: const Text(
                        'Skip for now',
                        style: TextStyle(
                          color: Color(0xFF64748B),
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          
          // Icon section
          const SizedBox(width: 16),
          Container(
            width: 60,
            height: 60,
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [
                  Color(0xFF3B82F6),
                  Color(0xFF2563EB),
                ],
              ),
              borderRadius: BorderRadius.circular(12),
              boxShadow: [
                BoxShadow(
                  color: const Color(0xFF2563EB).withOpacity(0.3),
                  blurRadius: 8,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: const Icon(
              Icons.add,
              color: Colors.white,
              size: 28,
            ),
          ),
        ],
      ),
    );
  }
}

class _QuickActions extends StatelessWidget {
  const _QuickActions({
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
    Widget tile(IconData icon, String label, VoidCallback onTap) => Column(
          children: [
            Material(
              color: Colors.white,
              borderRadius: BorderRadius.circular(16),
              child: InkWell(
                onTap: onTap,
                borderRadius: BorderRadius.circular(16),
                child: Container(
                  width: 70,
                  height: 70,
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: const Color(0xFFE6E9EF)),
                    color: Colors.white,
                  ),
                  child: Icon(icon, color: const Color(0xFF2563EB), size: 28),
                ),
              ),
            ),
            const SizedBox(height: 8),
            Text(
              label,
              style: const TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w500,
                color: Colors.black87,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        );

    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        tile(Icons.add, 'Add\nVehicle', onAdd),
        tile(Icons.directions_car_filled_outlined, 'My\nVehicles', onMyVehicles),
        tile(Icons.receipt_long_outlined, 'Trip\nHistory', onTrips),
        tile(Icons.warning_amber_outlined, 'Violations\nHistory', onViolations),
      ],
    );
  }
}

class _SectionHeader extends StatelessWidget {
  const _SectionHeader({required this.title, this.actionText, this.onAction});
  final String title;
  final String? actionText;
  final VoidCallback? onAction;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Text(
          title,
          style: const TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.w800,
            color: Colors.black87,
          ),
        ),
        const Spacer(),
        if (actionText != null)
          TextButton(
            onPressed: onAction,
            style: TextButton.styleFrom(
              padding: EdgeInsets.zero,
              tapTargetSize: MaterialTapTargetSize.shrinkWrap,
            ),
            child: Text(
              actionText!,
              style: const TextStyle(
                fontWeight: FontWeight.w600,
                color: Color(0xFF2563EB),
                fontSize: 14,
              ),
            ),
          ),
      ],
    );
  }
}

class _VehicleCard extends StatelessWidget {
  const _VehicleCard({
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
      width: 220,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: const Color(0xFFE6E9EF)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Flexible image area prevents overflow
              Expanded(
                child: Container(
                  width: double.infinity,
                  decoration: BoxDecoration(
                    color: const Color(0xFFF2F4F7),
                    borderRadius: BorderRadius.circular(12),
                    image: (imageUrl != null && imageUrl!.isNotEmpty)
                        ? DecorationImage(
                            image: NetworkImage(imageUrl!),
                            fit: BoxFit.cover,
                          )
                        : null,
                  ),
                  child: (imageUrl == null || imageUrl!.isEmpty)
                      ? const Center(
                          child: Icon(
                            Icons.directions_car_filled_outlined,
                            color: Colors.black38,
                            size: 40,
                          ),
                        )
                      : null,
                ),
              ),
              const SizedBox(height: 10),
              Text(
                plate,
                style: const TextStyle(
                  fontWeight: FontWeight.w800,
                  fontSize: 16,
                  color: Colors.black87,
                ),
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: 2),
              Text(
                subtitle,
                style: const TextStyle(color: Colors.black54, fontSize: 13.5),
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: 6),
              if (active)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: const Color(0xFFE8F7ED),
                    borderRadius: BorderRadius.circular(999),
                  ),
                  child: const Text(
                    'Active',
                    style: TextStyle(
                      color: Color(0xFF1F9D57),
                      fontSize: 12,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

class _AlertCard extends StatelessWidget {
  const _AlertCard({
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
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFFE6E9EF)),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    fontWeight: FontWeight.w800,
                    fontSize: 15,
                    color: Colors.black87,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  subtitle,
                  style: const TextStyle(color: Colors.black54, fontSize: 14),
                ),
              ],
            ),
          ),
          const SizedBox(width: 12),
          OutlinedButton(
            onPressed: onPressed,
            style: OutlinedButton.styleFrom(
              side: const BorderSide(color: Color(0xFF2563EB)),
              foregroundColor: const Color(0xFF2563EB),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
            ),
            child: Text(
              cta,
              style: const TextStyle(fontWeight: FontWeight.w600),
            ),
          ),
        ],
      ),
    );
  }
}

class _TripRow extends StatelessWidget {
  const _TripRow({required this.item});
  final _TripItem item;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        border: Border(
          bottom: BorderSide(
            color: const Color(0xFFE6E9EF).withOpacity(0.5),
          ),
        ),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  item.date,
                  style: const TextStyle(
                    fontWeight: FontWeight.w700,
                    fontSize: 14,
                    color: Colors.black87,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  item.route,
                  style: const TextStyle(color: Colors.black54, fontSize: 14),
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
                  fontSize: 14,
                  color: Colors.black87,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                item.duration,
                style: const TextStyle(color: Colors.black54, fontSize: 14),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _BottomBar extends StatelessWidget {
  const _BottomBar({required this.currentIndex, required this.onTap});
  final int currentIndex;
  final ValueChanged<int> onTap;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 10,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      child: SafeArea(
        top: false,
        child: SizedBox(
          height: 70,
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _BottomBarItem(
                icon: Icons.home_outlined,
                activeIcon: Icons.home_rounded,
                label: 'Home',
                isActive: currentIndex == 0,
                onTap: () => onTap(0),
              ),
              _BottomBarItem(
                icon: Icons.person_outline,
                activeIcon: Icons.person,
                label: 'Profile',
                isActive: currentIndex == 1,
                onTap: () => onTap(1),
              ),
              _BottomBarItem(
                icon: Icons.report_gmailerrorred_outlined,
                activeIcon: Icons.report,
                label: 'Violations',
                isActive: currentIndex == 2,
                onTap: () => onTap(2),
              ),
              _BottomBarItem(
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

class _BottomBarItem extends StatelessWidget {
  const _BottomBarItem({
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
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            isActive ? activeIcon : icon,
            color: isActive ? const Color(0xFF2563EB) : Colors.black54,
            size: 24,
          ),
          const SizedBox(height: 4),
          Text(
            label,
            style: TextStyle(
              color: isActive ? const Color(0xFF2563EB) : Colors.black54,
              fontSize: 12,
              fontWeight: isActive ? FontWeight.w600 : FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }
}

/* ====================== simple types ====================== */

class _AlertItem {
  final String title;
  final String subtitle;
  final String cta;
  const _AlertItem({required this.title, required this.subtitle, required this.cta});
}

class _TripItem {
  final String date;
  final String route;
  final String distance;
  final String duration;
  const _TripItem({required this.date, required this.route, required this.distance, required this.duration});
}