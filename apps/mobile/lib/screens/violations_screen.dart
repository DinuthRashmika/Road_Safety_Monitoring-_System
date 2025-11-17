import 'package:flutter/material.dart';

class ViolationsScreen extends StatefulWidget {
  const ViolationsScreen({super.key});

  @override
  State<ViolationsScreen> createState() => _ViolationsScreenState();
}

class _ViolationsScreenState extends State<ViolationsScreen> {
  String _selectedFilter = 'All';
  String _sortBy = 'Time';
  String _groupBy = 'Day';

  // Dummy violation data
  final List<Violation> _violations = const [
    Violation(
      type: 'Phone usage while driving',
      plateNumber: 'KA 01 AB 1234',
      vehicleModel: 'Toyota Camry',
      confidence: 0.92,
      time: '14:32',
      location: 'Galle Rd, Colombo 04',
      severity: 'Critical',
    ),
    Violation(
      type: 'Speeding',
      plateNumber: 'KA 01 AB 1234',
      vehicleModel: 'Toyota Camry',
      confidence: 0.85,
      time: '10:15',
      location: 'Marine Drive, Colombo 03',
      severity: 'High',
    ),
    Violation(
      type: 'Lane departure',
      plateNumber: 'KA 01 AB 1234',
      vehicleModel: 'Toyota Camry',
      confidence: 0.78,
      time: '08:45',
      location: 'High-Level Rd, Nugegoda',
      severity: 'Medium',
    ),
    Violation(
      type: 'Seatbelt violation',
      plateNumber: 'KA 01 AB 1234',
      vehicleModel: 'Toyota Camry',
      confidence: 0.95,
      time: '16:20',
      location: 'Baseline Rd, Borella',
      severity: 'Critical',
    ),
    Violation(
      type: 'Aggressive driving',
      plateNumber: 'KA 01 AB 1234',
      vehicleModel: 'Toyota Camry',
      confidence: 0.88,
      time: '12:55',
      location: 'Parliament Rd, Rajagiriya',
      severity: 'High',
    ),
  ];

  List<Violation> get _filteredViolations {
    if (_selectedFilter == 'All') return _violations;
    return _violations.where((v) => v.severity == _selectedFilter).toList();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF7F8FA),
      appBar: AppBar(
        title: const Text(
          'Violation History',
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
            // Filter Dropdown and Sort Options
            Row(
              children: [
                // Severity Filter Dropdown
                Expanded(
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: const Color(0xFFE6E9EF)),
                    ),
                    child: DropdownButton<String>(
                      value: _selectedFilter,
                      onChanged: (value) => setState(() => _selectedFilter = value!),
                      underline: const SizedBox(),
                      isExpanded: true,
                      icon: const Icon(Icons.arrow_drop_down, size: 20),
                      items: const [
                        DropdownMenuItem(
                          value: 'All',
                          child: Text('All Violations (120)'),
                        ),
                        DropdownMenuItem(
                          value: 'Critical',
                          child: Text('Critical (10)'),
                        ),
                        DropdownMenuItem(
                          value: 'High',
                          child: Text('High (30)'),
                        ),
                        DropdownMenuItem(
                          value: 'Medium',
                          child: Text('Medium (50)'),
                        ),
                        DropdownMenuItem(
                          value: 'Low',
                          child: Text('Low (30)'),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                // Sort Button
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: const Color(0xFFE6E9EF)),
                  ),
                  child: const Row(
                    children: [
                      Icon(Icons.sort, size: 16, color: Colors.black54),
                      SizedBox(width: 4),
                      Text('Sort', style: TextStyle(fontSize: 14)),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            
            // Sort and Group Options
            Row(
              children: [
                _DropdownOption(
                  value: _sortBy,
                  options: const ['Time', 'Severity', 'Type'],
                  onChanged: (value) => setState(() => _sortBy = value!),
                  label: 'Sort by:',
                ),
                const SizedBox(width: 16),
                _DropdownOption(
                  value: _groupBy,
                  options: const ['Day', 'Week', 'Month'],
                  onChanged: (value) => setState(() => _groupBy = value!),
                  label: 'Group by:',
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
                  return _ViolationCard(violation: violation);
                },
              ),
            ),
          ],
        ),
      ),
      // Bottom Navigation Bar matching home page style
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

class _DropdownOption extends StatelessWidget {
  final String value;
  final List<String> options;
  final ValueChanged<String?> onChanged;
  final String label;

  const _DropdownOption({
    required this.value,
    required this.options,
    required this.onChanged,
    required this.label,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Text(
          label,
          style: const TextStyle(
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
            value: value,
            onChanged: onChanged,
            underline: const SizedBox(),
            icon: const Icon(Icons.arrow_drop_down, size: 16),
            style: const TextStyle(fontSize: 14),
            items: options.map((String option) {
              return DropdownMenuItem<String>(
                value: option,
                child: Text(option),
              );
            }).toList(),
          ),
        ),
      ],
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
          // Violation Type and Severity
          Row(
            children: [
              Expanded(
                child: Text(
                  violation.type,
                  style: const TextStyle(
                    fontWeight: FontWeight.w700,
                    fontSize: 16,
                    color: Colors.black87,
                  ),
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: _getSeverityColor(violation.severity).withOpacity(0.1),
                  borderRadius: BorderRadius.circular(6),
                  border: Border.all(color: _getSeverityColor(violation.severity).withOpacity(0.3)),
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
            ],
          ),
          const SizedBox(height: 8),
          
          // Vehicle and Confidence Info
          Wrap(
            spacing: 8,
            children: [
              Text(
                '${violation.plateNumber} • ${violation.vehicleModel}',
                style: const TextStyle(
                  color: Colors.black54,
                  fontSize: 14,
                ),
              ),
              Container(
                width: 4,
                height: 4,
                decoration: const BoxDecoration(
                  color: Colors.black54,
                  shape: BoxShape.circle,
                ),
              ),
              Text(
                '${(violation.confidence * 100).toInt()}%',
                style: const TextStyle(
                  color: Colors.black54,
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                ),
              ),
              Container(
                width: 4,
                height: 4,
                decoration: const BoxDecoration(
                  color: Colors.black54,
                  shape: BoxShape.circle,
                ),
              ),
              Text(
                violation.time,
                style: const TextStyle(
                  color: Colors.black54,
                  fontSize: 14,
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          
          // Location
          Text(
            violation.location,
            style: const TextStyle(
              color: Colors.black45,
              fontSize: 14,
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