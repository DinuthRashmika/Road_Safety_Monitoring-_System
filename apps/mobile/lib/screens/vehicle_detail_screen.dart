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
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    final vehicle = v!;
    final cover = _cover(vehicle);
    final photos = _allPhotos(vehicle);

    return Scaffold(
      backgroundColor: const Color(0xFFF7F8FA),
      body: RefreshIndicator(
        onRefresh: () async => _load(vehicle.id),
        child: NestedScrollView(
          headerSliverBuilder: (_, __) => [
            SliverAppBar(
              elevation: 0,
              pinned: true,
              stretch: true,
              backgroundColor: Colors.white,
              foregroundColor: Colors.black87,
              expandedHeight: 260,
              title: Text(vehicle.plateNo),
              flexibleSpace: FlexibleSpaceBar(
                stretchModes: const [StretchMode.zoomBackground, StretchMode.fadeTitle],
                background: Stack(
                  fit: StackFit.expand,
                  children: [
                    if (cover != null)
                      Hero(
                        tag: 'vehicle-cover-${vehicle.id}',
                        child: Image.network(cover, fit: BoxFit.cover),
                      )
                    else
                      Container(
                        color: const Color(0xFFF2F4F7),
                        child: const Center(
                          child: Icon(Icons.directions_car_filled, size: 72, color: Colors.black26),
                        ),
                      ),
                    // gradient overlay
                    Positioned.fill(
                      child: DecoratedBox(
                        decoration: BoxDecoration(
                          gradient: LinearGradient(
                            begin: Alignment.topCenter,
                            end: Alignment.bottomCenter,
                            colors: [
                              Colors.black.withOpacity(0.05),
                              Colors.black.withOpacity(0.35),
                            ],
                          ),
                        ),
                      ),
                    ),
                    // bottom title stack
                    Positioned(
                      left: 16,
                      right: 16,
                      bottom: 16,
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.end,
                        children: [
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Text(
                                  vehicle.plateNo,
                                  style: const TextStyle(
                                    color: Colors.white,
                                    fontSize: 24,
                                    fontWeight: FontWeight.w900,
                                  ),
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  '${vehicle.vehicleModel.isNotEmpty ? vehicle.vehicleModel : vehicle.vehicleType}',
                                  style: TextStyle(
                                    color: Colors.white.withOpacity(0.9),
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                              ],
                            ),
                          ),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                            decoration: BoxDecoration(
                              color: Colors.white.withOpacity(0.9),
                              borderRadius: BorderRadius.circular(999),
                            ),
                            child: const Text(
                              'Active',
                              style: TextStyle(
                                color: Color(0xFF1F9D57),
                                fontWeight: FontWeight.w800,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
          body: ListView(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
            children: [
              // Info card
              _Card(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const _SectionTitle('Vehicle Info'),
                    const Divider(height: 20),
                    _infoRow(Icons.confirmation_number_outlined, 'Plate Number', vehicle.plateNo),
                    _infoRow(Icons.category_outlined, 'Type', vehicle.vehicleType),
                    _infoRow(Icons.directions_car_outlined, 'Model', vehicle.vehicleModel),
                    _infoRow(Icons.event_outlined, 'Registered', vehicle.registrationDate),
                  ],
                ),
              ),
              const SizedBox(height: 12),

              // Photos
              _Card(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const _SectionTitle('Photos'),
                    const SizedBox(height: 8),
                    if (photos.isEmpty)
                      Container(
                        height: 110,
                        alignment: Alignment.center,
                        decoration: BoxDecoration(
                          color: const Color(0xFFF2F4F7),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: const Text('No photos uploaded', style: TextStyle(color: Colors.black45)),
                      )
                    else
                      GridView.builder(
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
                        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                          crossAxisCount: 3,
                          mainAxisSpacing: 8,
                          crossAxisSpacing: 8,
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
                                pageBuilder: (_, __, ___) => _PhotoViewer(url: url, tag: 'p-$i-${vehicle.id}'),
                              ),
                            ),
                            child: Hero(
                              tag: 'p-$i-${vehicle.id}',
                              child: ClipRRect(
                                borderRadius: BorderRadius.circular(10),
                                child: Image.network(url, fit: BoxFit.cover),
                              ),
                            ),
                          );
                        },
                      ),
                  ],
                ),
              ),
              const SizedBox(height: 12),

              // Actions (optional Edit hook)
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: () => Navigator.pushNamed(context, '/vehicle-edit', arguments: vehicle.id),
                      icon: const Icon(Icons.edit_outlined),
                      label: const Text('Edit Details'),
                      style: OutlinedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: FilledButton.icon(
                      onPressed: () => _openGallery(context, photos),
                      icon: const Icon(Icons.photo_library_outlined),
                      label: const Text('Open Gallery'),
                      style: FilledButton.styleFrom(
                        backgroundColor: const Color(0xFF2563EB),
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
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
  }

  void _openGallery(BuildContext context, List<String> photos) {
    if (photos.isEmpty) return;
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => _GalleryScreen(photos: photos, baseTag: 'g-${v!.id}'),
      ),
    );
  }

  Widget _infoRow(IconData icon, String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 10),
      child: Row(
        children: [
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              color: const Color(0xFFEAF2FF),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(icon, color: const Color(0xFF2563EB)),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(label, style: const TextStyle(color: Colors.black54, fontWeight: FontWeight.w600)),
          ),
          const SizedBox(width: 8),
          Text(value, style: const TextStyle(color: Colors.black87, fontWeight: FontWeight.w700)),
        ],
      ),
    );
  }
}

/* ---------- small reusable bits ---------- */

class _Card extends StatelessWidget {
  const _Card({required this.child});
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFFE6E9EF)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.04),
            blurRadius: 12,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: child,
    );
  }
}

class _SectionTitle extends StatelessWidget {
  const _SectionTitle(this.text);
  final String text;

  @override
  Widget build(BuildContext context) {
    return Text(
      text,
      style: const TextStyle(
        fontWeight: FontWeight.w800,
        fontSize: 16,
        color: Colors.black87,
      ),
    );
  }
}

/* ---------- Simple full-screen photo viewer ---------- */

class _PhotoViewer extends StatelessWidget {
  const _PhotoViewer({required this.url, required this.tag});
  final String url;
  final String tag;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => Navigator.pop(context),
      child: Scaffold(
        backgroundColor: Colors.black,
        body: Center(
          child: Hero(
            tag: tag,
            child: InteractiveViewer(
              minScale: 0.6,
              maxScale: 4,
              child: Image.network(url, fit: BoxFit.contain),
            ),
          ),
        ),
      ),
    );
  }
}

class _GalleryScreen extends StatefulWidget {
  const _GalleryScreen({required this.photos, required this.baseTag});
  final List<String> photos;
  final String baseTag;

  @override
  State<_GalleryScreen> createState() => _GalleryScreenState();
}

class _GalleryScreenState extends State<_GalleryScreen> {
  late final PageController _pc = PageController();

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
              itemBuilder: (_, i) => Center(
                child: Hero(
                  tag: '${widget.baseTag}-$i',
                  child: InteractiveViewer(
                    minScale: 0.6,
                    maxScale: 4,
                    child: Image.network(widget.photos[i], fit: BoxFit.contain),
                  ),
                ),
              ),
            ),
            Positioned(
              top: 8,
              left: 8,
              child: IconButton(
                icon: const Icon(Icons.close, color: Colors.white),
                onPressed: () => Navigator.pop(context),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
