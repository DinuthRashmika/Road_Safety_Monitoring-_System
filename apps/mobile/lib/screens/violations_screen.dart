import 'package:flutter/material.dart';

class ViolationsScreen extends StatefulWidget {
  const ViolationsScreen({super.key});

  @override
  State<ViolationsScreen> createState() => _ViolationsScreenState();
}

class _ViolationsScreenState extends State<ViolationsScreen> {
  String _selectedFilter = 'All';
  String _sortBy = 'Time';

  // Dummy violation data matching the image
  final List<Violation> _violations = const [
    Violation(
      type: 'Phone usage while driving',
      plateNumber: 'KA01AB1234',
      vehicleModel: 'Toyota Camry',
      confidence: 0.92,
      time: '14:32',
      location: 'Galle Rd, Colombo 04',
      severity: 'Critical',
    ),
    Violation(
      type: 'Speeding',
      plateNumber: 'KA01AB1234',
      vehicleModel: 'Toyota Camry',
      confidence: 0.85,
      time: '10:15',
      location: 'Marine Drive, Colombo 03',
      severity: 'High',
    ),
    Violation(
      type: 'Lane departure',
      plateNumber: 'KA01AB1234',
      vehicleModel: 'Toyota Camry',
      confidence: 0.78,
      time: '08:45',
      location: 'High-Level Rd, Nugegoda',
      severity: 'Medium',
    ),
    Violation(
      type: 'Seatbelt violation',
      plateNumber: 'KA01AB1234',
      vehicleModel: 'Toyota Camry',
      confidence: 0.95,
      time: '16:20',
      location: 'Baseline Rd, Borella',
      severity: 'Critical',
    ),
    Violation(
      type: 'Aggressive driving',
      plateNumber: 'KA01AB1234',
      vehicleModel: 'Toyota Camry',
      confidence: 0.88,
      time: '12:55',
      location: 'Parliament Rd, Rajagiriya',
      severity: 'Low',
    ),
  ];

  List<Violation> get _filteredViolations {
    if (_selectedFilter == 'All') return _violations;
    return _violations.where((v) => v.severity == _selectedFilter).toList();
  }

  void _navigateToViolationDetails(BuildContext context, Violation violation) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => ViolationDetailsScreen(violation: violation),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF7F8FA),
      appBar: AppBar(
        title: const Text(
          'Enterprise Violation History',
          style: TextStyle(
            fontWeight: FontWeight.w800,
            fontSize: 20,
            color: Colors.black87,
          ),
        ),
        backgroundColor: Colors.white,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded, size: 20),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Title
            const Text(
              'Violation History',
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.w800,
                color: Colors.black87,
              ),
            ),
            const SizedBox(height: 16),
            
            // Filter Chips
            SizedBox(
              height: 40,
              child: ListView(
                scrollDirection: Axis.horizontal,
                children: [
                  _FilterChip(
                    label: 'All 120',
                    isSelected: _selectedFilter == 'All',
                    onTap: () => setState(() => _selectedFilter = 'All'),
                  ),
                  const SizedBox(width: 8),
                  _FilterChip(
                    label: 'Critical 10',
                    isSelected: _selectedFilter == 'Critical',
                    onTap: () => setState(() => _selectedFilter = 'Critical'),
                    backgroundColor: const Color(0xFFFEE2E2),
                    textColor: const Color(0xFFDC2626),
                  ),
                  const SizedBox(width: 8),
                  _FilterChip(
                    label: 'High 30',
                    isSelected: _selectedFilter == 'High',
                    onTap: () => setState(() => _selectedFilter = 'High'),
                    backgroundColor: const Color(0xFFFFEDD5),
                    textColor: const Color(0xFFEA580C),
                  ),
                  const SizedBox(width: 8),
                  _FilterChip(
                    label: 'Medium 50',
                    isSelected: _selectedFilter == 'Medium',
                    onTap: () => setState(() => _selectedFilter = 'Medium'),
                    backgroundColor: const Color(0xFFFEF3C7),
                    textColor: const Color(0xFFCA8A04),
                  ),
                  const SizedBox(width: 8),
                  _FilterChip(
                    label: 'Low 30',
                    isSelected: _selectedFilter == 'Low',
                    onTap: () => setState(() => _selectedFilter = 'Low'),
                    backgroundColor: const Color(0xFFDCFCE7),
                    textColor: const Color(0xFF16A34A),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            
            // Sort Row
            Row(
              children: [
                const Text(
                  'Sort by:',
                  style: TextStyle(
                    color: Colors.black54,
                    fontWeight: FontWeight.w500,
                    fontSize: 14,
                  ),
                ),
                const SizedBox(width: 8),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: const Color(0xFFE6E9EF)),
                  ),
                  child: DropdownButton<String>(
                    value: _sortBy,
                    onChanged: (value) => setState(() => _sortBy = value!),
                    underline: const SizedBox(),
                    icon: const Icon(Icons.arrow_drop_down, size: 16),
                    style: const TextStyle(fontSize: 14, color: Colors.black87),
                    items: const [
                      DropdownMenuItem(
                        value: 'Time',
                        child: Text('Time'),
                      ),
                      DropdownMenuItem(
                        value: 'Severity',
                        child: Text('Severity'),
                      ),
                      DropdownMenuItem(
                        value: 'Type',
                        child: Text('Type'),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            
            // Divider
            Container(
              height: 1,
              color: const Color(0xFFE6E9EF),
            ),
            const SizedBox(height: 16),
            
            // Violations List
            Expanded(
              child: ListView.separated(
                itemCount: _filteredViolations.length,
                separatorBuilder: (context, index) => const SizedBox(height: 12),
                itemBuilder: (context, index) {
                  final violation = _filteredViolations[index];
                  return GestureDetector(
                    onTap: () => _navigateToViolationDetails(context, violation),
                    child: _ViolationCard(violation: violation),
                  );
                },
              ),
            ),
          ],
        ),
      ),
      // Bottom Navigation Bar
      bottomNavigationBar: Container(
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
                  isActive: false,
                  onTap: () => Navigator.pushNamedAndRemoveUntil(context, '/home', (route) => false),
                ),
                _BottomBarItem(
                  icon: Icons.person_outline,
                  activeIcon: Icons.person,
                  label: 'Profile',
                  isActive: false,
                  onTap: () => Navigator.pushNamed(context, '/profile'),
                ),
                _BottomBarItem(
                  icon: Icons.report_gmailerrorred_outlined,
                  activeIcon: Icons.report,
                  label: 'Violations',
                  isActive: true,
                  onTap: () {},
                ),
                _BottomBarItem(
                  icon: Icons.shield_outlined,
                  activeIcon: Icons.shield,
                  label: 'Alerts',
                  isActive: false,
                  onTap: () => Navigator.pushNamed(context, '/alerts'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class ViolationDetailsScreen extends StatelessWidget {
  final Violation violation;

  const ViolationDetailsScreen({super.key, required this.violation});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF7F8FA),
      appBar: AppBar(
        title: const Text(
          'Violation Details',
          style: TextStyle(
            fontWeight: FontWeight.w800,
            fontSize: 20,
            color: Colors.black87,
          ),
        ),
        backgroundColor: Colors.white,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded, size: 20),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Violation Header
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: const Color(0xFFE6E9EF)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        violation.type.toUpperCase(),
                        style: const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.w800,
                          color: Colors.black87,
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                        decoration: BoxDecoration(
                          color: const Color(0xFFFEE2E2),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: const Text(
                          'Unpaid',
                          style: TextStyle(
                            color: Color(0xFFDC2626),
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    '${violation.plateNumber} • Apr 20, 2024 • ${violation.time} • ${violation.location}',
                    style: const TextStyle(
                      color: Colors.black54,
                      fontSize: 14,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            // Speed Information Card
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: const Color(0xFFE6E9EF)),
              ),
              child: Column(
                children: [
                  // Time
                  const Text(
                    '08:18',
                    style: TextStyle(
                      fontSize: 32,
                      fontWeight: FontWeight.w800,
                      color: Colors.black87,
                    ),
                  ),
                  const SizedBox(height: 20),

                  // Speed Stats
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: [
                      _SpeedStat(
                        value: '84 km/h',
                        label: 'Actual speed',
                        valueColor: const Color(0xFFDC2626),
                      ),
                      _SpeedStat(
                        value: '50 zone',
                        label: 'Limit',
                        valueColor: const Color(0xFF16A34A),
                      ),
                      _SpeedStat(
                        value: '+34 over',
                        label: 'Over by',
                        valueColor: const Color(0xFFDC2626),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            // Fine Information
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: const Color(0xFFE6E9EF)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'LKR 12,500',
                    style: TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.w800,
                      color: Colors.black87,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      _FineDetail(
                        icon: Icons.calendar_today_outlined,
                        text: 'Due: Apr 30, 2024',
                      ),
                      const SizedBox(width: 16),
                      _FineDetail(
                        icon: Icons.fingerprint_outlined,
                        text: 'Case ID: RV-38291',
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      _FineDetail(
                        icon: Icons.credit_card_outlined,
                        text: 'Points: -3',
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            // Action Buttons
            Row(
              children: [
                Expanded(
                  child: _ActionButton(
                    text: 'Pay Fine',
                    icon: Icons.payment_outlined,
                    backgroundColor: const Color(0xFF2563EB),
                    textColor: Colors.white,
                    onTap: () {},
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _ActionButton(
                    text: 'View Video',
                    icon: Icons.videocam_outlined,
                    backgroundColor: const Color(0xFFF3F4F6),
                    textColor: Colors.black87,
                    onTap: () {},
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _ActionButton(
                    text: 'Appeal',
                    icon: Icons.gavel_outlined,
                    backgroundColor: const Color(0xFFF3F4F6),
                    textColor: Colors.black87,
                    onTap: () {},
                  ),
                ),
              ],
            ),
            const SizedBox(height: 20),

            // Evidence Information
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFFF3F4F6),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                children: [
                  const Icon(Icons.info_outline, size: 16, color: Colors.black54),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Evidence captured by CCTV-CMB-104 • Confidence ${(violation.confidence * 100).toInt()}%',
                      style: const TextStyle(
                        color: Colors.black54,
                        fontSize: 14,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _SpeedStat extends StatelessWidget {
  final String value;
  final String label;
  final Color valueColor;

  const _SpeedStat({
    required this.value,
    required this.label,
    required this.valueColor,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(
          value,
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w700,
            color: valueColor,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          label,
          style: const TextStyle(
            fontSize: 12,
            color: Colors.black54,
          ),
        ),
      ],
    );
  }
}

class _FineDetail extends StatelessWidget {
  final IconData icon;
  final String text;

  const _FineDetail({
    required this.icon,
    required this.text,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 14, color: Colors.black54),
        const SizedBox(width: 4),
        Text(
          text,
          style: const TextStyle(
            fontSize: 14,
            color: Colors.black54,
          ),
        ),
      ],
    );
  }
}

class _ActionButton extends StatelessWidget {
  final String text;
  final IconData icon;
  final Color backgroundColor;
  final Color textColor;
  final VoidCallback onTap;

  const _ActionButton({
    required this.text,
    required this.icon,
    required this.backgroundColor,
    required this.textColor,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: backgroundColor,
          borderRadius: BorderRadius.circular(8),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 16, color: textColor),
            const SizedBox(width: 8),
            Text(
              text,
              style: TextStyle(
                color: textColor,
                fontSize: 14,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _FilterChip extends StatelessWidget {
  final String label;
  final bool isSelected;
  final VoidCallback onTap;
  final Color? backgroundColor;
  final Color? textColor;

  const _FilterChip({
    required this.label,
    required this.isSelected,
    required this.onTap,
    this.backgroundColor,
    this.textColor,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(
          color: isSelected 
              ? (backgroundColor ?? const Color(0xFF2563EB))
              : Colors.white,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: isSelected 
                ? (backgroundColor ?? const Color(0xFF2563EB))
                : const Color(0xFFE6E9EF),
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: isSelected 
                ? (textColor ?? Colors.white)
                : Colors.black54,
            fontSize: 14,
            fontWeight: FontWeight.w500,
          ),
        ),
      ),
    );
  }
}

class _ViolationCard extends StatelessWidget {
  final Violation violation;

  const _ViolationCard({required this.violation});

  Color _getSeverityColor(String severity) {
    switch (severity) {
      case 'Critical':
        return const Color(0xFFDC2626);
      case 'High':
        return const Color(0xFFEA580C);
      case 'Medium':
        return const Color(0xFFCA8A04);
      case 'Low':
        return const Color(0xFF16A34A);
      default:
        return const Color(0xFF6B7280);
    }
  }

  Color _getSeverityBackgroundColor(String severity) {
    switch (severity) {
      case 'Critical':
        return const Color(0xFFFEE2E2);
      case 'High':
        return const Color(0xFFFFEDD5);
      case 'Medium':
        return const Color(0xFFFEF3C7);
      case 'Low':
        return const Color(0xFFDCFCE7);
      default:
        return const Color(0xFFF3F4F6);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFE6E9EF)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Violation Type
          Text(
            violation.type,
            style: const TextStyle(
              fontWeight: FontWeight.w700,
              fontSize: 16,
              color: Colors.black87,
            ),
          ),
          const SizedBox(height: 8),
          
          // Vehicle and Confidence Info
          Row(
            children: [
              // License Plate and Model
              Expanded(
                child: Text(
                  '${violation.plateNumber} • ${violation.vehicleModel}',
                  style: const TextStyle(
                    color: Colors.black54,
                    fontSize: 14,
                  ),
                ),
              ),
              // Confidence
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: const Color(0xFFF3F4F6),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  '${(violation.confidence * 100).toInt()}%',
                  style: const TextStyle(
                    color: Colors.black54,
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          
          // Location and Time
          Row(
            children: [
              const Icon(Icons.location_on_outlined, size: 14, color: Colors.black45),
              const SizedBox(width: 4),
              Expanded(
                child: Text(
                  violation.location,
                  style: const TextStyle(
                    color: Colors.black45,
                    fontSize: 14,
                  ),
                ),
              ),
              const SizedBox(width: 12),
              const Icon(Icons.access_time, size: 14, color: Colors.black45),
              const SizedBox(width: 4),
              Text(
                violation.time,
                style: const TextStyle(
                  color: Colors.black45,
                  fontSize: 14,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          
          // Severity Badge
          Align(
            alignment: Alignment.centerRight,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: _getSeverityBackgroundColor(violation.severity),
                borderRadius: BorderRadius.circular(6),
              ),
              child: Text(
                violation.severity,
                style: TextStyle(
                  color: _getSeverityColor(violation.severity),
                  fontSize: 12,
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

class _BottomBarItem extends StatelessWidget {
  final IconData icon;
  final IconData activeIcon;
  final String label;
  final bool isActive;
  final VoidCallback onTap;

  const _BottomBarItem({
    required this.icon,
    required this.activeIcon,
    required this.label,
    required this.isActive,
    required this.onTap,
  });

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

class Violation {
  final String type;
  final String plateNumber;
  final String vehicleModel;
  final double confidence;
  final String time;
  final String location;
  final String severity;

  const Violation({
    required this.type,
    required this.plateNumber,
    required this.vehicleModel,
    required this.confidence,
    required this.time,
    required this.location,
    required this.severity,
  });
}