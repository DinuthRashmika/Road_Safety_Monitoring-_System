import 'package:flutter/material.dart';
import 'package:intl/intl.dart'; // Add intl to pubspec.yaml for date formatting
import 'package:road_safety_app/screens/violation_details_screen.dart';
import '../models/notification_model.dart';
import '../services/notification_service.dart';

// Ensure you have a route or file for ViolationDetailsScreen
// import 'violation_details_screen.dart'; 

class ViolationsScreen extends StatefulWidget {
  const ViolationsScreen({super.key});

  @override
  State<ViolationsScreen> createState() => _ViolationsScreenState();
}

class _ViolationsScreenState extends State<ViolationsScreen> {
  String _selectedFilter = 'All';
  late Future<List<NotificationModel>> _notificationsFuture;

  @override
  void initState() {
    super.initState();
    _loadNotifications();
  }

  void _loadNotifications() {
    setState(() {
      _notificationsFuture = NotificationService.getMyNotifications();
    });
  }

  // Helper to determine severity based on fine amount or message content
  // Since your backend notification list is simple, we infer severity here
  String _inferSeverity(String message) {
    if (message.toLowerCase().contains('critical') || message.contains('5000')) return 'Critical';
    if (message.toLowerCase().contains('high') || message.contains('2000')) return 'High';
    return 'Medium';
  }

  // Helper to extract violation type from message if not provided explicitly
  String _extractType(String message) {
    if (message.contains("'")) {
      final start = message.indexOf("'") + 1;
      final end = message.lastIndexOf("'");
      if (start > 0 && end > start) {
        return message.substring(start, end);
      }
    }
    return "Traffic Violation";
  }

  List<NotificationModel> _applyFilter(List<NotificationModel> list) {
    if (_selectedFilter == 'All') return list;
    // Filtering logic based on inferred severity
    return list.where((n) => _inferSeverity(n.message) == _selectedFilter).toList();
  }

  void _navigateToViolationDetails(BuildContext context, NotificationModel notification) {
    // Mark as read when opened
    if (!notification.isRead) {
      NotificationService.markAsRead(notification.id).then((_) {
        // Optional: Refresh list to update UI state
        // _loadNotifications(); 
      });
    }

    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => ViolationDetailsScreen(notification: notification),
      ),
    ).then((_) => _loadNotifications()); // Refresh when returning
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF7F8FA),
      appBar: AppBar(
        title: const Text(
          'My Violations',
          style: TextStyle(fontWeight: FontWeight.w800, fontSize: 20, color: Colors.black87),
        ),
        backgroundColor: Colors.white,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded, size: 20),
          onPressed: () => Navigator.pop(context),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadNotifications,
          )
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Violation History',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.w800, color: Colors.black87),
            ),
            const SizedBox(height: 16),
            
            // Filter Chips
            SizedBox(
              height: 40,
              child: ListView(
                scrollDirection: Axis.horizontal,
                children: [
                  _FilterChip(
                    label: 'All',
                    isSelected: _selectedFilter == 'All',
                    onTap: () => setState(() => _selectedFilter = 'All'),
                  ),
                  const SizedBox(width: 8),
                  _FilterChip(
                    label: 'Critical',
                    isSelected: _selectedFilter == 'Critical',
                    onTap: () => setState(() => _selectedFilter = 'Critical'),
                    backgroundColor: const Color(0xFFFEE2E2),
                    textColor: const Color(0xFFDC2626),
                  ),
                  const SizedBox(width: 8),
                  _FilterChip(
                    label: 'High',
                    isSelected: _selectedFilter == 'High',
                    onTap: () => setState(() => _selectedFilter = 'High'),
                    backgroundColor: const Color(0xFFFFEDD5),
                    textColor: const Color(0xFFEA580C),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            
            // Real Data List
            Expanded(
              child: FutureBuilder<List<NotificationModel>>(
                future: _notificationsFuture,
                builder: (context, snapshot) {
                  if (snapshot.connectionState == ConnectionState.waiting) {
                    return const Center(child: CircularProgressIndicator());
                  } else if (snapshot.hasError) {
                    return Center(child: Text('Error: ${snapshot.error}'));
                  } else if (!snapshot.hasData || snapshot.data!.isEmpty) {
                    return const Center(child: Text('No violations found.'));
                  }

                  final filteredList = _applyFilter(snapshot.data!);

                  return ListView.separated(
                    itemCount: filteredList.length,
                    separatorBuilder: (context, index) => const SizedBox(height: 12),
                    itemBuilder: (context, index) {
                      final item = filteredList[index];
                      return GestureDetector(
                        onTap: () => _navigateToViolationDetails(context, item),
                        child: _ViolationCard(
                          notification: item,
                          severity: _inferSeverity(item.message),
                          type: _extractType(item.message),
                        ),
                      );
                    },
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ViolationCard extends StatelessWidget {
  final NotificationModel notification;
  final String severity;
  final String type;

  const _ViolationCard({
    required this.notification,
    required this.severity,
    required this.type,
  });

  Color _getSeverityColor(String severity) {
    switch (severity) {
      case 'Critical': return const Color(0xFFDC2626);
      case 'High': return const Color(0xFFEA580C);
      default: return const Color(0xFFCA8A04);
    }
  }

  Color _getSeverityBackgroundColor(String severity) {
    switch (severity) {
      case 'Critical': return const Color(0xFFFEE2E2);
      case 'High': return const Color(0xFFFFEDD5);
      default: return const Color(0xFFFEF3C7);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          // Highlight unread notifications with a blue border
          color: notification.isRead ? const Color(0xFFE6E9EF) : Colors.blue.withOpacity(0.5),
          width: notification.isRead ? 1 : 1.5,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                type,
                style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16, color: Colors.black87),
              ),
              if (!notification.isRead)
                Container(
                  width: 8, height: 8,
                  decoration: const BoxDecoration(color: Colors.blue, shape: BoxShape.circle),
                )
            ],
          ),
          const SizedBox(height: 8),
          
          Text(
            '${notification.vehiclePlate} • ${DateFormat('MMM d, h:mm a').format(notification.createdAt.toLocal())}',
            style: const TextStyle(color: Colors.black54, fontSize: 14),
          ),
          const SizedBox(height: 8),
          
          Row(
            children: [
              const Icon(Icons.location_on_outlined, size: 14, color: Colors.black45),
              const SizedBox(width: 4),
              Expanded(
                child: Text(
                  notification.location,
                  style: const TextStyle(color: Colors.black45, fontSize: 14),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: _getSeverityBackgroundColor(severity),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  severity,
                  style: TextStyle(
                    color: _getSeverityColor(severity),
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
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
          color: isSelected ? (backgroundColor ?? const Color(0xFF2563EB)) : Colors.white,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: isSelected ? (backgroundColor ?? const Color(0xFF2563EB)) : const Color(0xFFE6E9EF),
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: isSelected ? (textColor ?? Colors.white) : Colors.black54,
            fontSize: 14,
            fontWeight: FontWeight.w500,
          ),
        ),
      ),
    );
  }
}