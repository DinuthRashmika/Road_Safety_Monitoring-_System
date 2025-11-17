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

  // Mock data (replace with real data from your APIs)
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
    _TripItem(
        date: 'Aug 18, 2023',
        route: 'Downtown → Home',
        distance: '12.5 km',
        duration: '32 min'),
    _TripItem(
        date: 'Aug 17, 2023',
        route: 'Work → Gym',
        distance: '5.2 km',
        duration: '15 min'),
    _TripItem(
        date: 'Aug 16, 2023',
        route: 'Home → Airport',
        distance: '28.1 km',
        duration: '45 min'),
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
      backgroundColor: const Color(0xFFF8FAFD),
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
              child: CircularProgressIndicator.adaptive(
                valueColor: AlwaysStoppedAnimation(Color(0xFF2563EB)),
              ),
            )
          : RefreshIndicator(
              onRefresh: _load,
              color: const Color(0xFF2563EB),
              child: CustomScrollView(
                primary: true,
                slivers: [
                  // Enhanced Header - FIXED: Increased height and better padding
                  SliverAppBar(
                    expandedHeight: 160, // Increased from 140 to 160
                    flexibleSpace: FlexibleSpaceBar(
                      background: Container(
                        decoration: const BoxDecoration(
                          gradient: LinearGradient(
                            begin: Alignment.topLeft,
                            end: Alignment.bottomRight,
                            colors: [
                              Color(0xFF2563EB),
                              Color(0xFF1D4ED8),
                            ],
                          ),
                        ),
                        child: SafeArea(
                          bottom: false,
                          child: Padding(
                            padding: const EdgeInsets.fromLTRB(24, 16, 24, 24), // Increased bottom padding
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                _EnhancedHeaderBar(
                                  profileImage: _owner?.imageUrl,
                                  onProfile: () =>
                                      Navigator.pushNamed(context, '/profile')
                                          .then((_) => _load()),
                                  onBell: () =>
                                      Navigator.pushNamed(context, '/alerts'),
                                  onLogout: _logout,
                                ),
                                const SizedBox(height: 20), // Increased spacing
                                // FIXED: Better text layout with proper constraints
                                Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      'Welcome back, $name! 👋',
                                      style: const TextStyle(
                                        fontSize: 22, // Slightly smaller font
                                        fontWeight: FontWeight.w800,
                                        color: Colors.white,
                                        height: 1.2,
                                      ),
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                    const SizedBox(height: 6), // Added spacing
                                    Text(
                                      'Ready to hit the road?',
                                      style: TextStyle(
                                        fontSize: 14,
                                        fontWeight: FontWeight.w500,
                                        color: Colors.white.withOpacity(0.9),
                                      ),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                    ),
                    backgroundColor: const Color(0xFF2563EB),
                    elevation: 0,
                    forceElevated: false,
                  ),

                  // Main Content
                  SliverList(
                    delegate: SliverChildListDelegate([
                      const SizedBox(height: 24),

                      // Promo card when no vehicles
                      if (_vehicles.isEmpty)
                        Padding(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 20, vertical: 8),
                          child: _BeautifulPromoCard(
                            onAdd: () =>
                                Navigator.pushNamed(context, '/vehicle-add')
                                    .then((_) => _load()),
                            onSkip: () {},
                          ),
                        ),

                      // Quick actions with enhanced design
                      Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 20),
                        child: _EnhancedQuickActions(
                          onAdd: () =>
                              Navigator.pushNamed(context, '/vehicle-add')
                                  .then((_) => _load()),
                          onMyVehicles: () =>
                              Navigator.pushNamed(context, '/vehicles')
                                  .then((_) => _load()),
                          onTrips: () =>
                              Navigator.pushNamed(context, '/trips'),
                          onViolations: () =>
                              Navigator.pushNamed(context, '/violations'),
                        ),
                      ),

                      const SizedBox(height: 24),

                     // My Vehicles Section - FIXED: Better spacing and layout
if (_vehicles.isNotEmpty) ...[
  Padding(
    padding: const EdgeInsets.symmetric(horizontal: 20),
    child: _EnhancedSectionHeader(
      title: 'My Vehicles',
      subtitle: '${_vehicles.length} vehicle${_vehicles.length > 1 ? 's' : ''} registered',
      actionText: 'View all',
      onAction: () =>
          Navigator.pushNamed(context, '/vehicles')
              .then((_) => _load()),
    ),
  ),
  const SizedBox(height: 20), // Increased from 16 to 20
  SizedBox(
    height: 250, // Increased from 220 to 240
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
        
        // FIXED: Better image URL handling to prevent yellow/black issues
        String? cover;
        if (v.images is Map) {
          final map = v.images as Map<dynamic, dynamic>;
          // Try multiple possible image keys
          final any = map['front'] ?? map['plate'] ?? map['back'] ?? map['side'];
          if (any is String && any.isNotEmpty && any.startsWith('http')) {
            cover = any;
          }
        }

        final subtitle = ((v.vehicleModel ?? v.vehicleType) ?? '')
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
  const SizedBox(height: 12), // Increased from 8 to 12
],
                      // Protective Alerts Section
                      Padding(
                        padding: const EdgeInsets.fromLTRB(20, 32, 20, 16),
                        child: _EnhancedSectionHeader(
                          title: 'Protective Alerts',
                          subtitle: 'Stay updated with important notifications',
                          actionText: 'View all',
                          onAction: () =>
                              Navigator.pushNamed(context, '/alerts'),
                        ),
                      ),
                      ..._alerts.map((a) => Padding(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 20, vertical: 6),
                            child: _EnhancedAlertCard(
                              title: a.title,
                              subtitle: a.subtitle,
                              cta: a.cta,
                              onPressed: () {},
                            ),
                          )),

                      // Trip History Section
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
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(20),
                          boxShadow: [
                            BoxShadow(
                              color: const Color(0xFF1D4ED8).withOpacity(0.08),
                              blurRadius: 20,
                              offset: const Offset(0, 4),
                            ),
                          ],
                          border: Border.all(
                            color: const Color(0xFFF1F5F9),
                            width: 1,
                          ),
                        ),
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(20),
                          child: Column(
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
                                color: const Color(0xFF2563EB).withOpacity(0.3),
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

/* ====================== ENHANCED UI COMPONENTS ====================== */

class _EnhancedHeaderBar extends StatelessWidget {
  const _EnhancedHeaderBar({
    this.profileImage,
    this.onProfile,
    this.onBell,
    this.onLogout,
  });

  final String? profileImage;
  final VoidCallback? onProfile;
  final VoidCallback? onBell;
  final VoidCallback? onLogout;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        // Profile Avatar
        GestureDetector(
          onTap: onProfile,
          child: Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.2),
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: Colors.white.withOpacity(0.3)),
              image: profileImage != null && profileImage!.isNotEmpty
                  ? DecorationImage(
                      image: NetworkImage(profileImage!),
                      fit: BoxFit.cover,
                    )
                  : null,
            ),
            child: profileImage == null || profileImage!.isEmpty
                ? const Icon(Icons.person, color: Colors.white, size: 20)
                : null,
          ),
        ),
        const Spacer(),
        
        // Notification Bell
        Container(
          decoration: BoxDecoration(
            color: Colors.white.withOpacity(0.15),
            borderRadius: BorderRadius.circular(12),
          ),
          child: IconButton(
            onPressed: onBell,
            icon: const Icon(Icons.notifications_none_rounded,
                color: Colors.white, size: 22),
            padding: const EdgeInsets.all(8),
            constraints: const BoxConstraints(minWidth: 44, minHeight: 44),
          ),
        ),
        const SizedBox(width: 8),
        
        // Logout Button
        Container(
          decoration: BoxDecoration(
            color: Colors.white.withOpacity(0.15),
            borderRadius: BorderRadius.circular(12),
          ),
          child: IconButton(
            onPressed: onLogout,
            icon: const Icon(Icons.logout, color: Colors.white, size: 20),
            padding: const EdgeInsets.all(8),
            constraints: const BoxConstraints(minWidth: 44, minHeight: 44),
          ),
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
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            Color(0xFFE0F2FE),
            Color(0xFFF0F9FF),
          ],
        ),
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF0EA5E9).withOpacity(0.1),
            blurRadius: 20,
            offset: const Offset(0, 8),
          ),
        ],
        border: Border.all(color: const Color(0xFFBAE6FD), width: 1),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: const Color(0xFF0EA5E9).withOpacity(0.1),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: const Text(
                    'GET STARTED',
                    style: TextStyle(
                      color: Color(0xFF0369A1),
                      fontSize: 12,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 0.5,
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                const Text(
                  'Add Your First Vehicle',
                  style: TextStyle(
                    fontWeight: FontWeight.w800,
                    fontSize: 20,
                    color: Color(0xFF0F172A),
                    height: 1.2,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  'Start your journey by adding a vehicle to access all features and track your trips.',
                  style: TextStyle(
                    color: const Color(0xFF475569).withOpacity(0.8),
                    fontSize: 14,
                    height: 1.4,
                  ),
                ),
                const SizedBox(height: 20),
                Row(
                  children: [
                    ElevatedButton(
                      onPressed: onAdd,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF0EA5E9),
                        foregroundColor: Colors.white,
                        elevation: 0,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                        padding: const EdgeInsets.symmetric(
                            horizontal: 24, vertical: 14),
                      ),
                      child: const Text(
                        'Add Vehicle',
                        style: TextStyle(
                          fontWeight: FontWeight.w700,
                          fontSize: 14,
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    TextButton(
                      onPressed: onSkip,
                      style: TextButton.styleFrom(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 20, vertical: 14),
                      ),
                      child: Text(
                        'Skip',
                        style: TextStyle(
                          color: const Color(0xFF64748B),
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(width: 20),
          Container(
            width: 80,
            height: 80,
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [
                  Color(0xFF0EA5E9),
                  Color(0xFF0284C7),
                ],
              ),
              borderRadius: BorderRadius.circular(20),
              boxShadow: [
                BoxShadow(
                  color: const Color(0xFF0EA5E9).withOpacity(0.4),
                  blurRadius: 15,
                  offset: const Offset(0, 8),
                ),
              ],
            ),
            child: const Icon(
              Icons.directions_car_filled_rounded,
              color: Colors.white,
              size: 32,
            ),
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
    Widget actionTile(IconData icon, String label, VoidCallback onTap, Color color) => 
        Column(
          children: [
            Container(
              width: 64,
              height: 64,
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [
                    color.withOpacity(0.1),
                    color.withOpacity(0.05),
                ],
                ),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: color.withOpacity(0.2)),
              ),
              child: Material(
                color: Colors.transparent,
                borderRadius: BorderRadius.circular(16),
                child: InkWell(
                  onTap: onTap,
                  borderRadius: BorderRadius.circular(16),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(icon, color: color, size: 24),
                    ],
                  ),
                ),
              ),
            ),
            const SizedBox(height: 8),
            Text(
              label,
              style: const TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w600,
                color: Color(0xFF475569),
              ),
              textAlign: TextAlign.center,
            ),
          ],
        );

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF1D4ED8).withOpacity(0.08),
            blurRadius: 20,
            offset: const Offset(0, 4),
          ),
        ],
        border: Border.all(color: const Color(0xFFF1F5F9)),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          actionTile(Icons.add_rounded, 'Add\nVehicle', onAdd, const Color(0xFF0EA5E9)),
          actionTile(Icons.directions_car_rounded, 'My\nVehicles', onMyVehicles, const Color(0xFF10B981)),
          actionTile(Icons.route_rounded, 'Trip\nHistory', onTrips, const Color(0xFFF59E0B)),
          actionTile(Icons.warning_amber_rounded, 'Violations\n', onViolations, const Color(0xFFEF4444)),
        ],
      ),
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
                    color: Color(0xFF0F172A),
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  subtitle,
                  style: TextStyle(
                    fontSize: 14,
                    color: const Color(0xFF475569).withOpacity(0.8),
                  ),
                ),
              ],
            ),
            const Spacer(),
            if (actionText != null)
              Container(
                decoration: BoxDecoration(
                  color: const Color(0xFFF1F5F9),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: TextButton(
                  onPressed: onAction,
                  style: TextButton.styleFrom(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                  ),
                  child: Text(
                    actionText!,
                    style: const TextStyle(
                      fontWeight: FontWeight.w600,
                      color: Color(0xFF475569),
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
              color: Colors.white,
              borderRadius: BorderRadius.circular(20),
              boxShadow: [
                BoxShadow(
                  color: const Color(0xFF1D4ED8).withOpacity(0.08),
                  blurRadius: 15,
                  offset: const Offset(0, 4),
                ),
              ],
              border: Border.all(color: const Color(0xFFF1F5F9)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // FIXED: Better image handling to prevent yellow/black issues
                Container(
                  height: 120,
                  width: double.infinity,
                  decoration: BoxDecoration(
                    borderRadius: const BorderRadius.only(
                      topLeft: Radius.circular(20),
                      topRight: Radius.circular(20),
                    ),
                    gradient: const LinearGradient(
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                      colors: [
                        Color(0xFFF8FAFD),
                        Color(0xFFF1F5F9),
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
                
                // Content Section - FIXED: Better text constraints to prevent overflow
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
                          color: Color(0xFF0F172A),
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      const SizedBox(height: 4),
                      // FIXED: Added proper text constraints to prevent overflow
                      SizedBox(
                        height: 20, // Fixed height to prevent layout shifts
                        child: Text(
                          subtitle,
                          style: TextStyle(
                            color: const Color(0xFF64748B),
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
                            color: const Color(0xFFDCFCE7),
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Container(
                                width: 6,
                                height: 6,
                                decoration: const BoxDecoration(
                                  color: Color(0xFF16A34A),
                                  shape: BoxShape.circle,
                                ),
                              ),
                              const SizedBox(width: 6),
                              const Text(
                                'Active',
                                style: TextStyle(
                                  color: Color(0xFF166534),
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

// NEW: Separate widget to handle vehicle images properly
class _VehicleImageHandler extends StatelessWidget {
  final String? imageUrl;

  const _VehicleImageHandler({this.imageUrl});

  @override
  Widget build(BuildContext context) {
    // If no image URL or invalid URL, show placeholder
    if (imageUrl == null || imageUrl!.isEmpty || !imageUrl!.startsWith('http')) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFFE2E8F0),
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.directions_car_filled_rounded,
                color: Color(0xFF475569),
                size: 32,
              ),
            ),
          ],
        ),
      );
    }

    // If we have a valid image URL, try to load it with error handling
    return Image.network(
      imageUrl!,
      fit: BoxFit.cover,
      width: double.infinity,
      height: double.infinity,
      errorBuilder: (context, error, stackTrace) {
        // If image fails to load, show placeholder
        return Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: const Color(0xFFE2E8F0),
                  shape: BoxShape.circle,
                ),
                child: const Icon(
                  Icons.directions_car_filled_rounded,
                  color: Color(0xFF475569),
                  size: 32,
                ),
              ),
            ],
          ),
        );
      },
      loadingBuilder: (context, child, loadingProgress) {
        if (loadingProgress == null) return child;
        return Center(
          child: CircularProgressIndicator(
            value: loadingProgress.expectedTotalBytes != null
                ? loadingProgress.cumulativeBytesLoaded / loadingProgress.expectedTotalBytes!
                : null,
            color: const Color(0xFF2563EB),
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
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF1D4ED8).withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, 2),
          ),
        ],
        border: Border.all(color: const Color(0xFFF1F5F9)),
      ),
      child: Row(
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: const Color(0xFFFEF3F2),
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Icon(
              Icons.warning_amber_rounded,
              color: Color(0xFFDC2626),
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
                    color: Color(0xFF0F172A),
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  subtitle,
                  style: TextStyle(
                    color: const Color(0xFF64748B),
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
                  Color(0xFFDC2626),
                  Color(0xFFEF4444),
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
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
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
                  color: const Color(0xFFF1F5F9),
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
                color: const Color(0xFFF0F9FF),
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Icon(
                Icons.route_rounded,
                color: Color(0xFF0EA5E9),
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
                      color: Color(0xFF0F172A),
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    item.date,
                    style: TextStyle(
                      color: const Color(0xFF64748B),
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
                    color: Color(0xFF0F172A),
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  item.duration,
                  style: TextStyle(
                    color: const Color(0xFF64748B),
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
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 20,
            offset: const Offset(0, -5),
          ),
        ],
        border: const Border(
          top: BorderSide(
            color: Color(0xFFF1F5F9),
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
          color: isActive ? const Color(0xFFF0F9FF) : Colors.transparent,
          borderRadius: BorderRadius.circular(16),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              isActive ? activeIcon : icon,
              color: isActive ? const Color(0xFF0EA5E9) : const Color(0xFF94A3B8),
              size: 24,
            ),
            const SizedBox(height: 4),
            Text(
              label,
              style: TextStyle(
                color: isActive ? const Color(0xFF0EA5E9) : const Color(0xFF94A3B8),
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

/* ====================== DATA MODELS ====================== */

class _AlertItem {
  final String title;
  final String subtitle;
  final String cta;
  const _AlertItem(
      {required this.title, required this.subtitle, required this.cta});
}

class _TripItem {
  final String date;
  final String route;
  final String distance;
  final String duration;
  const _TripItem(
      {required this.date,
      required this.route,
      required this.distance,
      required this.duration});
}