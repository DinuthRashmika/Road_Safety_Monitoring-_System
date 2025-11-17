import 'package:flutter/material.dart';
import '../models/vehicle.dart';
import '../services/vehicle_service.dart';

class VehicleDetailScreen extends StatefulWidget {
  const VehicleDetailScreen({super.key});
  @override
  State<VehicleDetailScreen> createState() => _VehicleDetailScreenState();
}

class _VehicleDetailScreenState extends State<VehicleDetailScreen> {
  Vehicle? v;
  bool _loading = true;

  Future<void> _load(String id) async {
    final data = await VehicleService.byId(id);
    setState(() {
      v = data;
      _loading = false;
    });
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final id = ModalRoute.of(context)!.settings.arguments as String;
    _load(id);
  }

  String? _cover(Vehicle x) {
    final map = x.images;
    final s = (map['front'] ?? map['plate'] ?? map['back'] ?? map['right'] ?? map['left']);
    return (s is String && s.isNotEmpty) ? s : null;
  }

  List<String> _allPhotos(Vehicle x) {
    return [
      x.images['front'],
      x.images['back'],
      x.images['right'],
      x.images['left'],
      x.images['plate'],
    ].whereType<String>().where((s) => s.isNotEmpty).toList();
  }

  @override
  Widget build(BuildContext context) {
    if (_loading || v == null) {
      return Scaffold(
        backgroundColor: const Color(0xFFF8FAFD),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                width: 80,
                height: 80,
                decoration: BoxDecoration(
                  color: const Color(0xFFF0F9FF),
                  borderRadius: BorderRadius.circular(40),
                ),
                child: const CircularProgressIndicator.adaptive(
                  valueColor: AlwaysStoppedAnimation(Color(0xFF0EA5E9)),
                ),
              ),
              const SizedBox(height: 20),
              const Text(
                'Loading vehicle details...',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                  color: Color(0xFF475569),
                ),
              ),
            ],
          ),
        ),
      );
    }
    final vehicle = v!;
    final cover = _cover(vehicle);
    final photos = _allPhotos(vehicle);

    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFD),
      body: RefreshIndicator(
        onRefresh: () async => _load(vehicle.id),
        color: const Color(0xFF0EA5E9),
        backgroundColor: const Color(0xFFF8FAFD),
        child: CustomScrollView(
          slivers: [
            // Enhanced App Bar with Hero Image
            SliverAppBar(
              elevation: 0,
              pinned: true,
              stretch: true,
              backgroundColor: Colors.white,
              foregroundColor: const Color(0xFF0F172A),
              expandedHeight: 320,
              flexibleSpace: _EnhancedVehicleHeader(
                vehicle: vehicle,
                coverImage: cover,
              ),
              bottom: PreferredSize(
                preferredSize: const Size.fromHeight(0),
                child: Container(
                  height: 20,
                  decoration: const BoxDecoration(
                    color: Color(0xFFF8FAFD),
                    borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
                  ),
                ),
              ),
            ),

            // Main Content
            SliverList(
              delegate: SliverChildListDelegate([
                // Vehicle Info Card
                Padding(
                  padding: const EdgeInsets.fromLTRB(20, 8, 20, 12),
                  child: _EnhancedInfoCard(vehicle: vehicle),
                ),

                // Photos Section
                Padding(
                  padding: const EdgeInsets.fromLTRB(20, 8, 20, 12),
                  child: _EnhancedPhotosCard(
                    vehicle: vehicle,
                    photos: photos,
                  ),
                ),

                // Action Buttons
                Padding(
                  padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
                  child: _EnhancedActionButtons(
                    vehicle: vehicle,
                    photos: photos,
                  ),
                ),
              ]),
            ),
          ],
        ),
      ),
    );
  }

  void _openGallery(BuildContext context, List<String> photos) {
    if (photos.isEmpty) return;
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => _EnhancedGalleryScreen(photos: photos, baseTag: 'g-${v!.id}'),
      ),
    );
  }
}

/* ====================== ENHANCED HEADER ====================== */

class _EnhancedVehicleHeader extends StatelessWidget {
  final Vehicle vehicle;
  final String? coverImage;

  const _EnhancedVehicleHeader({required this.vehicle, this.coverImage});

  @override
  Widget build(BuildContext context) {
    return FlexibleSpaceBar(
      stretchModes: const [StretchMode.zoomBackground, StretchMode.fadeTitle],
      background: Stack(
        fit: StackFit.expand,
        children: [
          // Background Image
          if (coverImage != null)
            Hero(
              tag: 'vehicle-cover-${vehicle.id}',
              child: Image.network(
                coverImage!,
                fit: BoxFit.cover,
                errorBuilder: (context, error, stackTrace) {
                  return _VehicleImagePlaceholder();
                },
                loadingBuilder: (context, child, loadingProgress) {
                  if (loadingProgress == null) return child;
                  return const Center(
                    child: CircularProgressIndicator.adaptive(
                      valueColor: AlwaysStoppedAnimation(Color(0xFF0EA5E9)),
                    ),
                  );
                },
              ),
            )
          else
            _VehicleImagePlaceholder(),

          // Gradient Overlay
          Positioned.fill(
            child: DecoratedBox(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [
                    Colors.transparent,
                    Colors.black.withOpacity(0.6),
                  ],
                  stops: const [0.5, 1.0],
                ),
              ),
            ),
          ),

          // Vehicle Info Overlay
          Positioned(
            left: 24,
            right: 24,
            bottom: 40,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  decoration: BoxDecoration(
                    color: const Color(0xFF0EA5E9),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    vehicle.plateNo,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 20,
                      fontWeight: FontWeight.w800,
                      letterSpacing: 1.2,
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            vehicle.vehicleModel.isNotEmpty ? vehicle.vehicleModel : vehicle.vehicleType,
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 18,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            vehicle.vehicleType,
                            style: TextStyle(
                              color: Colors.white.withOpacity(0.8),
                              fontSize: 14,
                            ),
                          ),
                        ],
                      ),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(
                          colors: [
                            Color(0xFF10B981),
                            Color(0xFF059669),
                          ],
                        ),
                        borderRadius: BorderRadius.circular(20),
                        boxShadow: [
                          BoxShadow(
                            color: const Color(0xFF10B981).withOpacity(0.3),
                            blurRadius: 8,
                            offset: const Offset(0, 2),
                          ),
                        ],
                      ),
                      child: const Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.check_circle_rounded, size: 16, color: Colors.white),
                          SizedBox(width: 6),
                          Text(
                            'Active',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 14,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _VehicleImagePlaceholder extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            Color(0xFF0EA5E9),
            Color(0xFF0284C7),
          ],
        ),
      ),
      child: const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.directions_car_filled_rounded,
              size: 80,
              color: Colors.white,
            ),
            SizedBox(height: 12),
            Text(
              'Vehicle Image',
              style: TextStyle(
                color: Colors.white,
                fontSize: 16,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/* ====================== ENHANCED INFO CARD ====================== */

class _EnhancedInfoCard extends StatelessWidget {
  final Vehicle vehicle;

  const _EnhancedInfoCard({required this.vehicle});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(24),
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
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(Icons.info_rounded, color: Color(0xFF0EA5E9), size: 20),
              SizedBox(width: 8),
              Text(
                'Vehicle Information',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w800,
                  color: Color(0xFF0F172A),
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),
          _EnhancedInfoRow(
            icon: Icons.confirmation_number_rounded,
            label: 'Plate Number',
            value: vehicle.plateNo,
            color: Color(0xFF0EA5E9),
          ),
          const SizedBox(height: 16),
          _EnhancedInfoRow(
            icon: Icons.category_rounded,
            label: 'Vehicle Type',
            value: vehicle.vehicleType,
            color: Color(0xFF10B981),
          ),
          const SizedBox(height: 16),
          _EnhancedInfoRow(
            icon: Icons.directions_car_rounded,
            label: 'Vehicle Model',
            value: vehicle.vehicleModel.isNotEmpty ? vehicle.vehicleModel : 'Not specified',
            color: Color(0xFFF59E0B),
          ),
          const SizedBox(height: 16),
          _EnhancedInfoRow(
            icon: Icons.calendar_today_rounded,
            label: 'Registration Date',
            value: vehicle.registrationDate,
            color: Color(0xFFEF4444),
          ),
        ],
      ),
    );
  }
}

class _EnhancedInfoRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final Color color;

  const _EnhancedInfoRow({
    required this.icon,
    required this.label,
    required this.value,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFFF8FAFD),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFFE2E8F0)),
      ),
      child: Row(
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: color.withOpacity(0.1),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(icon, color: color, size: 20),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                    color: Color(0xFF64748B),
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  value,
                  style: const TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w700,
                    color: Color(0xFF0F172A),
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

/* ====================== ENHANCED PHOTOS CARD ====================== */

class _EnhancedPhotosCard extends StatelessWidget {
  final Vehicle vehicle;
  final List<String> photos;

  const _EnhancedPhotosCard({required this.vehicle, required this.photos});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(24),
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
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(Icons.photo_library_rounded, color: Color(0xFF0EA5E9), size: 20),
              SizedBox(width: 8),
              Text(
                'Vehicle Photos',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w800,
                  color: Color(0xFF0F172A),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          if (photos.isEmpty)
            Container(
              height: 120,
              width: double.infinity,
              decoration: BoxDecoration(
                color: const Color(0xFFF8FAFD),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: const Color(0xFFE2E8F0)),
              ),
              child: const Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.photo_camera_rounded, size: 40, color: Color(0xFF94A3B8)),
                  SizedBox(height: 8),
                  Text(
                    'No photos available',
                    style: TextStyle(
                      color: Color(0xFF64748B),
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
            )
          else
            GridView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 3,
                mainAxisSpacing: 12,
                crossAxisSpacing: 12,
                childAspectRatio: 4 / 3,
              ),
              itemCount: photos.length,
              itemBuilder: (_, i) {
                final url = photos[i];
                return GestureDetector(
                  onTap: () => Navigator.push(
                    context,
                    PageRouteBuilder(
                      barrierColor: Colors.black,
                      pageBuilder: (_, __, ___) => _EnhancedPhotoViewer(url: url, tag: 'p-$i-${vehicle.id}'),
                    ),
                  ),
                  child: Hero(
                    tag: 'p-$i-${vehicle.id}',
                    child: Container(
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(14),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withOpacity(0.1),
                            blurRadius: 8,
                            offset: const Offset(0, 2),
                          ),
                        ],
                      ),
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(14),
                        child: Image.network(
                          url,
                          fit: BoxFit.cover,
                          errorBuilder: (context, error, stackTrace) {
                            return Container(
                              decoration: BoxDecoration(
                                color: const Color(0xFFF1F5F9),
                                borderRadius: BorderRadius.circular(14),
                              ),
                              child: const Icon(Icons.broken_image_rounded, color: Color(0xFF94A3B8)),
                            );
                          },
                          loadingBuilder: (context, child, loadingProgress) {
                            if (loadingProgress == null) return child;
                            return Container(
                              decoration: BoxDecoration(
                                color: const Color(0xFFF1F5F9),
                                borderRadius: BorderRadius.circular(14),
                              ),
                              child: Center(
                                child: CircularProgressIndicator(
                                  value: loadingProgress.expectedTotalBytes != null
                                      ? loadingProgress.cumulativeBytesLoaded / loadingProgress.expectedTotalBytes!
                                      : null,
                                  color: const Color(0xFF0EA5E9),
                                ),
                              ),
                            );
                          },
                        ),
                      ),
                    ),
                  ),
                );
              },
            ),
        ],
      ),
    );
  }
}

/* ====================== ENHANCED ACTION BUTTONS ====================== */

class _EnhancedActionButtons extends StatelessWidget {
  final Vehicle vehicle;
  final List<String> photos;

  const _EnhancedActionButtons({required this.vehicle, required this.photos});

  void _openGallery(BuildContext context, List<String> photos) {
    if (photos.isEmpty) return;
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => _EnhancedGalleryScreen(photos: photos, baseTag: 'g-${vehicle.id}'),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        // Edit Button
        Expanded(
          child: Container(
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(16),
              boxShadow: [
                BoxShadow(
                  color: const Color(0xFF1D4ED8).withOpacity(0.08),
                  blurRadius: 15,
                  offset: const Offset(0, 4),
                ),
              ],
              border: Border.all(color: const Color(0xFFF1F5F9)),
            ),
            child: Material(
              color: Colors.transparent,
              child: InkWell(
                onTap: () => Navigator.pushNamed(context, '/vehicle-edit', arguments: vehicle.id),
                borderRadius: BorderRadius.circular(16),
                child: Container(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  child: const Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.edit_rounded, color: Color(0xFF475569), size: 20),
                      SizedBox(width: 8),
                      Text(
                        'Edit Details',
                        style: TextStyle(
                          fontWeight: FontWeight.w700,
                          fontSize: 15,
                          color: Color(0xFF475569),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
        const SizedBox(width: 16),
        
        // Gallery Button
        Expanded(
          child: Container(
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [
                  Color(0xFF0EA5E9),
                  Color(0xFF0284C7),
                ],
              ),
              borderRadius: BorderRadius.circular(16),
              boxShadow: [
                BoxShadow(
                  color: const Color(0xFF0EA5E9).withOpacity(0.3),
                  blurRadius: 15,
                  offset: const Offset(0, 6),
                ),
              ],
            ),
            child: Material(
              color: Colors.transparent,
              child: InkWell(
                onTap: () => _openGallery(context, photos),
                borderRadius: BorderRadius.circular(16),
                child: Container(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  child: const Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.photo_library_rounded, color: Colors.white, size: 20),
                      SizedBox(width: 8),
                      Text(
                        'Open Gallery',
                        style: TextStyle(
                          fontWeight: FontWeight.w700,
                          fontSize: 15,
                          color: Colors.white,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }
}

/* ====================== ENHANCED PHOTO VIEWER ====================== */

class _EnhancedPhotoViewer extends StatelessWidget {
  const _EnhancedPhotoViewer({required this.url, required this.tag});
  final String url;
  final String tag;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => Navigator.pop(context),
      child: Scaffold(
        backgroundColor: Colors.black,
        body: SafeArea(
          child: Stack(
            children: [
              Center(
                child: Hero(
                  tag: tag,
                  child: InteractiveViewer(
                    minScale: 0.6,
                    maxScale: 4,
                    child: Image.network(
                      url,
                      fit: BoxFit.contain,
                      errorBuilder: (context, error, stackTrace) {
                        return Container(
                          color: Colors.black,
                          child: const Center(
                            child: Icon(Icons.broken_image_rounded, size: 60, color: Colors.white54),
                          ),
                        );
                      },
                    ),
                  ),
                ),
              ),
              Positioned(
                top: 16,
                left: 16,
                child: Container(
                  decoration: BoxDecoration(
                    color: Colors.black.withOpacity(0.5),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: IconButton(
                    icon: const Icon(Icons.close_rounded, color: Colors.white),
                    onPressed: () => Navigator.pop(context),
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

class _EnhancedGalleryScreen extends StatefulWidget {
  const _EnhancedGalleryScreen({required this.photos, required this.baseTag});
  final List<String> photos;
  final String baseTag;

  @override
  State<_EnhancedGalleryScreen> createState() => _EnhancedGalleryScreenState();
}

class _EnhancedGalleryScreenState extends State<_EnhancedGalleryScreen> {
  late final PageController _pc = PageController();
  int _currentIndex = 0;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: SafeArea(
        child: Stack(
          children: [
            PageView.builder(
              controller: _pc,
              itemCount: widget.photos.length,
              onPageChanged: (index) => setState(() => _currentIndex = index),
              itemBuilder: (_, i) => Center(
                child: Hero(
                  tag: '${widget.baseTag}-$i',
                  child: InteractiveViewer(
                    minScale: 0.6,
                    maxScale: 4,
                    child: Image.network(
                      widget.photos[i],
                      fit: BoxFit.contain,
                      errorBuilder: (context, error, stackTrace) {
                        return Container(
                          color: Colors.black,
                          child: const Center(
                            child: Icon(Icons.broken_image_rounded, size: 60, color: Colors.white54),
                          ),
                        );
                      },
                    ),
                  ),
                ),
              ),
            ),
            
            // Close Button
            Positioned(
              top: 16,
              left: 16,
              child: Container(
                decoration: BoxDecoration(
                  color: Colors.black.withOpacity(0.5),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: IconButton(
                  icon: const Icon(Icons.close_rounded, color: Colors.white),
                  onPressed: () => Navigator.pop(context),
                ),
              ),
            ),
            
            // Index Indicator
            if (widget.photos.length > 1)
              Positioned(
                top: 16,
                right: 16,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  decoration: BoxDecoration(
                    color: Colors.black.withOpacity(0.5),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    '${_currentIndex + 1}/${widget.photos.length}',
                    style: const TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}