import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/notification_model.dart';
import '../services/payment_service.dart';
import './pay_fine_screen.dart'; // Import the PayFineScreen

class ViolationDetailsScreen extends StatefulWidget {
  final NotificationModel notification;

  const ViolationDetailsScreen({super.key, required this.notification});

  @override
  State<ViolationDetailsScreen> createState() => _ViolationDetailsScreenState();
}

class _ViolationDetailsScreenState extends State<ViolationDetailsScreen> {
  bool _isPaid = false;
  bool _isLoading = false;
  late Map<String, dynamic> _violationDetails;

  @override
  void initState() {
    super.initState();
    _violationDetails = _parseViolationDetails();
    // _isPaid = widget.notification.isPaid; // Uncomment if your model has this
  }

  // --- Parse violation details from notification message ---
  Map<String, dynamic> _parseViolationDetails() {
    final message = widget.notification.message;
    final details = {
      'violationType': 'Speeding',
      'detectedSpeed': 84,
      'speedLimit': 50,
      'cameraId': 'CCTV-CMB-104',
      'confidence': 98,
    };

    // Extract violation type from message
    if (message.contains("'")) {
      final start = message.indexOf("'") + 1;
      final end = message.lastIndexOf("'");
      if (start > 0 && end > start) {
        details['violationType'] = message.substring(start, end);
      }
    }

    // Try to extract speed values if available in message
    final speedRegex = RegExp(r'(\d+)\s*km/h');
    final match = speedRegex.firstMatch(message);
    if (match != null) {
      details['detectedSpeed'] = int.tryParse(match.group(1)!) ?? 84;
    }

    // Extract camera ID if available
    if (message.contains('CCTV')) {
      final cameraRegex = RegExp(r'CCTV-[A-Z]+-\d+');
      final cameraMatch = cameraRegex.firstMatch(message);
      if (cameraMatch != null) {
        details['cameraId'] = cameraMatch.group(0)!;
      }
    }

    return details;
  }

  // --- Logic Helpers ---

  double _getFineAmountValue() {
    final regex = RegExp(r'([0-9]+)');
    final match = regex.firstMatch(widget.notification.message);
    if (match != null) {
      return double.tryParse(match.group(1)!) ?? 12500.0;
    }
    return 12500.0;
  }

  String _extractFineDisplay() {
    final regex = RegExp(r'LKR\s*([0-9.,]+)');
    final match = regex.firstMatch(widget.notification.message);
    return match != null ? 'LKR ${match.group(1)}' : 'LKR 12,500';
  }

  String _getSeverityColor() {
    final message = widget.notification.message.toLowerCase();
    if (message.contains('critical') || message.contains('5000')) return '#DC2626';
    if (message.contains('high') || message.contains('2000')) return '#EA580C';
    return '#CA8A04';
  }

  // Navigate to PayFineScreen
  Future<void> _navigateToPayFineScreen() async {
    final amount = _getFineAmountValue();
    
    // Navigate to PayFineScreen and wait for result
    final result = await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => PayFineScreen(
          notification: widget.notification,
          amount: amount,
        ),
      ),
    );

    // If payment was successful (result is true), update the state
    if (result == true && mounted) {
      setState(() {
        _isPaid = true;
      });
      
      // Show success message
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Payment successful! Violation marked as paid.'),
          backgroundColor: Colors.green,
          duration: Duration(seconds: 3),
        ),
      );
    }
  }

  Future<void> _handlePayment() async {
    // Navigate to payment screen instead of processing payment directly
    await _navigateToPayFineScreen();
  }

  @override
  Widget build(BuildContext context) {
    final fineString = _extractFineDisplay();
    final dateStr = DateFormat('MMM d, yyyy').format(widget.notification.createdAt);
    final timeStr = DateFormat('h:mm a').format(widget.notification.createdAt);
    final overSpeed = _violationDetails['detectedSpeed'] - _violationDetails['speedLimit'];

    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        centerTitle: true,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new, color: Colors.black, size: 20),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text(
          'Violation Details',
          style: TextStyle(color: Colors.black, fontWeight: FontWeight.w700, fontSize: 18),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.more_vert, color: Colors.black),
            onPressed: () {},
          ),
        ],
      ),
      body: SingleChildScrollView(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 10),
          child: Column(
            children: [
              // 1. Badges Row
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  _buildBadge(
                    _violationDetails['violationType'].toUpperCase(),
                    const Color(0xFFEFF6FF),
                    const Color(0xFF2563EB),
                  ),
                  const SizedBox(width: 12),
                  _buildBadge(
                    _isPaid ? 'Paid' : 'Unpaid',
                    _isPaid ? const Color(0xFFDCFCE7) : const Color(0xFFEFF6FF),
                    _isPaid ? const Color(0xFF16A34A) : const Color(0xFF2563EB),
                  ),
                ],
              ),
              const SizedBox(height: 16),

              // 2. Context Info
              Text(
                '${widget.notification.vehiclePlate} • $dateStr • $timeStr • ${widget.notification.location}',
                textAlign: TextAlign.center,
                style: const TextStyle(
                  color: Color(0xFF6B7280),
                  fontSize: 13,
                  fontWeight: FontWeight.w500,
                ),
              ),
              const SizedBox(height: 24),

              // 3. Video Player UI (Replica) - Show relevant violation image
              Container(
                height: 220,
                width: double.infinity,
                decoration: BoxDecoration(
                  color: Colors.black87,
                  borderRadius: BorderRadius.circular(16),
                  image: const DecorationImage(
                    image: NetworkImage(
                      'https://images.unsplash.com/photo-1542282088-fe8426682b8f?q=80&w=1000&auto=format&fit=crop',
                    ),
                    fit: BoxFit.cover,
                    opacity: 0.6,
                  ),
                ),
                child: Stack(
                  children: [
                    // Play Button
                    Center(
                      child: Container(
                        width: 50,
                        height: 50,
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.3),
                          shape: BoxShape.circle,
                          border: Border.all(color: Colors.white, width: 2),
                        ),
                        child: const Icon(Icons.play_arrow_rounded, color: Colors.white, size: 32),
                      ),
                    ),
                    // Controls Overlay
                    Positioned(
                      bottom: 12,
                      left: 12,
                      right: 12,
                      child: Row(
                        children: [
                          const Text('00:10', style: TextStyle(color: Colors.white, fontSize: 12)),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Container(
                              height: 4,
                              decoration: BoxDecoration(
                                color: Colors.white.withOpacity(0.3),
                                borderRadius: BorderRadius.circular(2),
                              ),
                              child: Row(
                                children: [
                                  Container(
                                    width: 40,
                                    height: 4,
                                    decoration: BoxDecoration(
                                      color: Colors.white,
                                      borderRadius: BorderRadius.circular(2),
                                    ),
                                  ),
                                  Container(
                                    width: 12,
                                    height: 12,
                                    decoration: const BoxDecoration(
                                      color: Colors.white,
                                      shape: BoxShape.circle,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                          const SizedBox(width: 10),
                          const Icon(Icons.volume_off, color: Colors.white, size: 20),
                          const SizedBox(width: 8),
                          const Icon(Icons.fullscreen, color: Colors.white, size: 20),
                        ],
                      ),
                    ),
                    // Violation type overlay
                    Positioned(
                      top: 12,
                      left: 12,
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                        decoration: BoxDecoration(
                          color: Colors.black.withOpacity(0.6),
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Text(
                          _violationDetails['violationType'],
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),

              // 4. Stats Row - Dynamically show violation data
              Row(
                children: [
                  Expanded(
                    child: _buildStatCard(
                      '${_violationDetails['detectedSpeed']}',
                      'km/h',
                      'Detected Speed',
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: _buildStatCard(
                      '${_violationDetails['speedLimit']}',
                      'zone',
                      'Speed Limit',
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: _buildStatCard(
                      '+$overSpeed',
                      'over',
                      'Over by',
                      valueColor: overSpeed > 0 ? const Color(0xFFDC2626) : const Color(0xFF2563EB),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 20),

              // 5. Fine Details Card
              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: const Color(0xFFF9FAFB),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            fineString,
                            style: const TextStyle(
                              fontSize: 22,
                              fontWeight: FontWeight.w800,
                              color: Color(0xFF111827),
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            'Due date: ${DateFormat('MMM d, yyyy').format(widget.notification.createdAt.add(const Duration(days: 30)))}',
                            style: const TextStyle(color: Color(0xFF6B7280), fontSize: 13),
                          ),
                          const SizedBox(height: 4),
                          RichText(
                            text: TextSpan(
                              style: const TextStyle(fontSize: 13, color: Color(0xFF6B7280)),
                              children: [
                                const TextSpan(text: 'Severity: '),
                                TextSpan(
                                  text: _violationDetails['violationType'] == 'Speeding' && overSpeed > 30
                                      ? 'High'
                                      : 'Medium',
                                  style: const TextStyle(
                                    color: Color(0xFFDC2626),
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        Text(
                          'Due: ${DateFormat('MMM d, yyyy').format(widget.notification.createdAt.add(const Duration(days: 30)))}',
                          style: const TextStyle(color: Color(0xFF6B7280), fontSize: 13),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          'Case ID: ${widget.notification.id.substring(0, 6).toUpperCase()}',
                          style: const TextStyle(color: Color(0xFF9CA3AF), fontSize: 12),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),

              // 6. Violation Details Card
              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: const Color(0xFFF9FAFB),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Violation Details',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w700,
                        color: Color(0xFF111827),
                      ),
                    ),
                    const SizedBox(height: 16),
                    _buildDetailRow('Type:', _violationDetails['violationType']),
                    _buildDetailRow('Vehicle:', widget.notification.vehiclePlate),
                    _buildDetailRow('Location:', widget.notification.location),
                    _buildDetailRow('Date & Time:', '$dateStr at $timeStr'),
                    _buildDetailRow('Camera ID:', _violationDetails['cameraId']),
                    _buildDetailRow('Confidence:', '${_violationDetails['confidence']}%'),
                  ],
                ),
              ),
              const SizedBox(height: 24),

              // 7. Buttons
              Row(
                children: [
                  Expanded(
                    child: ElevatedButton(
                      onPressed: _isPaid ? null : _handlePayment,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: _isPaid ? Colors.grey : const Color(0xFF2563EB),
                        padding: const EdgeInsets.symmetric(vertical: 16),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                        elevation: 0,
                      ),
                      child: _isPaid
                          ? const Text(
                              'Paid',
                              style: TextStyle(
                                fontWeight: FontWeight.w600,
                                fontSize: 16,
                                color: Colors.white,
                              ),
                            )
                          : const Text(
                              'Pay Fine',
                              style: TextStyle(
                                fontWeight: FontWeight.w600,
                                fontSize: 16,
                                color: Colors.white,
                              ),
                            ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: OutlinedButton(
                      onPressed: () {
                        // Handle view video
                      },
                      style: OutlinedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 16),
                        side: const BorderSide(color: Color(0xFF2563EB)),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                      child: const Text(
                        'View Evidence',
                        style: TextStyle(
                          fontWeight: FontWeight.w600,
                          fontSize: 16,
                          color: Color(0xFF2563EB),
                        ),
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 24),

              // 8. Footer
              Center(
                child: TextButton(
                  onPressed: () {},
                  child: const Text(
                    'Appeal',
                    style: TextStyle(
                      color: Color(0xFF2563EB),
                      fontWeight: FontWeight.w600,
                      fontSize: 15,
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 8),
              Center(
                child: Text(
                  'Evidence captured by ${_violationDetails['cameraId']} • Confidence ${_violationDetails['confidence']}%',
                  style: const TextStyle(color: Color(0xFF9CA3AF), fontSize: 12),
                ),
              ),
              const SizedBox(height: 20),
            ],
          ),
        ),
      ),
    );
  }

  // --- Widget Builders ---

  Widget _buildBadge(String text, Color bgColor, Color textColor) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        text,
        style: TextStyle(color: textColor, fontWeight: FontWeight.w700, fontSize: 12),
      ),
    );
  }

  Widget _buildStatCard(String value, String unit, String label, {Color? valueColor}) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFFF9FAFB),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.baseline,
            textBaseline: TextBaseline.alphabetic,
            children: [
              Text(
                value,
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.w800,
                  color: valueColor ?? const Color(0xFF111827),
                ),
              ),
              const SizedBox(width: 4),
              Text(
                unit,
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: valueColor ?? const Color(0xFF111827),
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            label,
            style: const TextStyle(color: Color(0xFF9CA3AF), fontSize: 11),
          ),
        ],
      ),
    );
  }

  Widget _buildDetailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 100,
            child: Text(
              label,
              style: const TextStyle(
                color: Color(0xFF6B7280),
                fontSize: 14,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(
                color: Color(0xFF111827),
                fontSize: 14,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ],
      ),
    );
  }
}