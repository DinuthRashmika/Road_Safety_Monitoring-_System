import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/notification_model.dart';
import './pay_fine_screen.dart';
import '../core/api_client.dart';

class ViolationDetailsScreen extends StatefulWidget {
  final NotificationModel notification;

  const ViolationDetailsScreen({
    super.key,
    required this.notification,
  });

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
  }

  String? _buildViolationImageUrl() {
    final rel = widget.notification.violationImage;
    if (rel == null || rel.trim().isEmpty) return null;

    String normalized = rel.replaceAll('\\', '/').trim();
    normalized = normalized.replaceFirst(RegExp(r'^/+'), '');

    if (normalized.startsWith('http://') || normalized.startsWith('https://')) {
      return Uri.encodeFull(normalized);
    }

    final base = ApiClient.dio.options.baseUrl.replaceAll(RegExp(r'\/+$'), '');

    final url = normalized.startsWith('static/')
        ? '$base/$normalized'
        : '$base/static/$normalized';

    return Uri.encodeFull(url);
  }

  Map<String, dynamic> _parseViolationDetails() {
    final message = widget.notification.message;

    final details = <String, dynamic>{
      'violationType': widget.notification.violationType ?? 'Violation',
      'detectedSpeed': 84,
      'speedLimit': 50,
      'cameraId': 'CCTV-CMB-104',
      'confidence': 98,
    };

    if ((widget.notification.violationType ?? '').trim().isNotEmpty) {
      details['violationType'] = widget.notification.violationType!;
    } else if (message.contains("'")) {
      final start = message.indexOf("'") + 1;
      final end = message.lastIndexOf("'");
      if (start > 0 && end > start) {
        details['violationType'] = message.substring(start, end);
      }
    }

    final speedRegex = RegExp(r'(\d+)\s*km/h');
    final match = speedRegex.firstMatch(message);
    if (match != null) {
      details['detectedSpeed'] = int.tryParse(match.group(1)!) ?? 84;
    }

    if (message.contains('CCTV')) {
      final cameraRegex = RegExp(r'CCTV-[A-Z]+-\d+');
      final cameraMatch = cameraRegex.firstMatch(message);
      if (cameraMatch != null) {
        details['cameraId'] = cameraMatch.group(0)!;
      }
    }

    return details;
  }

  double _getFineAmountValue() {
    if (widget.notification.fineAmount != null && widget.notification.fineAmount! > 0) {
      return widget.notification.fineAmount!;
    }

    final regex = RegExp(r'([0-9]+)');
    final match = regex.firstMatch(widget.notification.message);
    if (match != null) {
      return double.tryParse(match.group(1)!) ?? 12500.0;
    }

    return 12500.0;
  }

  String _extractFineDisplay() {
    if (widget.notification.fineAmount != null) {
      final value = widget.notification.fineAmount!;
      return 'LKR ${value.toStringAsFixed(0)}';
    }

    final regex = RegExp(r'LKR\s*([0-9.,]+)');
    final match = regex.firstMatch(widget.notification.message);
    return match != null ? 'LKR ${match.group(1)}' : 'LKR 12,500';
  }

  Future<void> _navigateToPayFineScreen() async {
    final amount = _getFineAmountValue();

    final result = await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => PayFineScreen(
          notification: widget.notification,
          amount: amount,
        ),
      ),
    );

    if (result == true && mounted) {
      setState(() {
        _isPaid = true;
      });

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
    await _navigateToPayFineScreen();
  }

  @override
  Widget build(BuildContext context) {
    final fineString = _extractFineDisplay();
    final dateStr = DateFormat('MMM d, yyyy').format(widget.notification.createdAt);
    final timeStr = DateFormat('h:mm a').format(widget.notification.createdAt);
    final overSpeed =
        (_violationDetails['detectedSpeed'] as int) - (_violationDetails['speedLimit'] as int);
    final evidenceUrl = _buildViolationImageUrl();

    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.black,
        elevation: 0,
        centerTitle: true,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new, color: Colors.white, size: 20),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text(
          'Violation Details',
          style: TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.w700,
            fontSize: 18,
          ),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.more_vert, color: Colors.white),
            onPressed: () {},
          ),
        ],
      ),
      body: SingleChildScrollView(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 10),
          child: Column(
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  _buildBadge(
                    _violationDetails['violationType'].toString().toUpperCase(),
                    const Color(0xFF1E3A8A),
                    const Color(0xFF60A5FA),
                  ),
                  const SizedBox(width: 12),
                  _buildBadge(
                    _isPaid ? 'Paid' : 'Unpaid',
                    _isPaid ? const Color(0xFF065F46) : const Color(0xFF1E3A8A),
                    _isPaid ? const Color(0xFF34D399) : const Color(0xFF60A5FA),
                  ),
                ],
              ),
              const SizedBox(height: 16),

              Text(
                '${widget.notification.vehiclePlate} • $dateStr • $timeStr • ${widget.notification.location}',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: Colors.grey.shade400,
                  fontSize: 13,
                  fontWeight: FontWeight.w500,
                ),
              ),
              const SizedBox(height: 24),

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
                      valueColor:
                          overSpeed > 0 ? const Color(0xFFF87171) : const Color(0xFF60A5FA),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 20),

              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: Colors.grey.shade900,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: Colors.grey.shade800),
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
                              color: Colors.white,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            'Due date: ${DateFormat('MMM d, yyyy').format(widget.notification.createdAt.add(const Duration(days: 30)))}',
                            style: TextStyle(color: Colors.grey.shade400, fontSize: 13),
                          ),
                          const SizedBox(height: 4),
                          RichText(
                            text: TextSpan(
                              style: TextStyle(fontSize: 13, color: Colors.grey.shade400),
                              children: [
                                const TextSpan(text: 'Severity: '),
                                TextSpan(
                                  text: _violationDetails['violationType'] == 'Speeding' &&
                                          overSpeed > 30
                                      ? 'High'
                                      : 'Medium',
                                  style: const TextStyle(
                                    color: Color(0xFFF87171),
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
                          style: TextStyle(color: Colors.grey.shade400, fontSize: 13),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          'Case ID: ${widget.notification.id.length >= 6 ? widget.notification.id.substring(0, 6).toUpperCase() : widget.notification.id.toUpperCase()}',
                          style: TextStyle(color: Colors.grey.shade500, fontSize: 12),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),

              if (evidenceUrl != null) ...[
                Container(
                  width: double.infinity,
                  decoration: BoxDecoration(
                    color: Colors.grey.shade900,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: Colors.grey.shade800),
                  ),
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Padding(
                          padding: EdgeInsets.fromLTRB(20, 18, 20, 12),
                          child: Text(
                            'Violation Evidence',
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w700,
                              color: Colors.white,
                            ),
                          ),
                        ),
                        AspectRatio(
                          aspectRatio: 16 / 9,
                          child: Image.network(
                            evidenceUrl,
                            fit: BoxFit.cover,
                            loadingBuilder: (context, child, progress) {
                              if (progress == null) return child;
                              return Center(
                                child: CircularProgressIndicator(
                                  valueColor: AlwaysStoppedAnimation(
                                    const Color(0xFF60A5FA).withOpacity(0.8),
                                  ),
                                ),
                              );
                            },
                            errorBuilder: (context, error, stack) {
                              return Center(
                                child: Padding(
                                  padding: const EdgeInsets.all(16),
                                  child: Column(
                                    mainAxisAlignment: MainAxisAlignment.center,
                                    children: [
                                      const Icon(
                                        Icons.broken_image,
                                        color: Colors.white54,
                                        size: 40,
                                      ),
                                      const SizedBox(height: 8),
                                      Text(
                                        'Failed to load image',
                                        style: TextStyle(color: Colors.grey.shade400),
                                      ),
                                      const SizedBox(height: 6),
                                      Text(
                                        evidenceUrl,
                                        textAlign: TextAlign.center,
                                        style: TextStyle(
                                          color: Colors.grey.shade600,
                                          fontSize: 11,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              );
                            },
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 24),
              ],

              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: Colors.grey.shade900,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: Colors.grey.shade800),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Violation Details',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w700,
                        color: Colors.white,
                      ),
                    ),
                    const SizedBox(height: 16),
                    _buildDetailRow('Type:', _violationDetails['violationType'].toString()),
                    _buildDetailRow('Vehicle:', widget.notification.vehiclePlate),
                    _buildDetailRow('Location:', widget.notification.location),
                    _buildDetailRow('Date & Time:', '$dateStr at $timeStr'),
                    _buildDetailRow('Camera ID:', _violationDetails['cameraId'].toString()),
                    _buildDetailRow('Confidence:', '${_violationDetails['confidence']}%'),
                  ],
                ),
              ),
              const SizedBox(height: 24),

              Row(
                children: [
                  Expanded(
                    child: ElevatedButton(
                      onPressed: _isPaid || _isLoading ? null : _handlePayment,
                      style: ElevatedButton.styleFrom(
                        backgroundColor:
                            _isPaid ? Colors.grey.shade700 : const Color(0xFF2563EB),
                        padding: const EdgeInsets.symmetric(vertical: 16),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                        elevation: 0,
                      ),
                      child: _isLoading
                          ? const SizedBox(
                              height: 18,
                              width: 18,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                color: Colors.white,
                              ),
                            )
                          : _isPaid
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
                        if (evidenceUrl == null) return;

                        showDialog(
                          context: context,
                          builder: (context) => Dialog(
                            backgroundColor: Colors.black,
                            insetPadding: const EdgeInsets.all(12),
                            child: InteractiveViewer(
                              child: ClipRRect(
                                borderRadius: BorderRadius.circular(12),
                                child: Image.network(
                                  evidenceUrl,
                                  fit: BoxFit.contain,
                                  errorBuilder: (context, error, stackTrace) {
                                    return const Padding(
                                      padding: EdgeInsets.all(24),
                                      child: Center(
                                        child: Text(
                                          'Failed to load image',
                                          style: TextStyle(color: Colors.white),
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
                      style: OutlinedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 16),
                        side: const BorderSide(color: Color(0xFF2563EB)),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                        backgroundColor: Colors.transparent,
                      ),
                      child: const Text(
                        'View Evidence',
                        style: TextStyle(
                          fontWeight: FontWeight.w600,
                          fontSize: 16,
                          color: Color(0xFF60A5FA),
                        ),
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 24),

              Center(
                child: TextButton(
                  onPressed: () {},
                  child: const Text(
                    'Appeal',
                    style: TextStyle(
                      color: Color(0xFF60A5FA),
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
                  style: TextStyle(color: Colors.grey.shade500, fontSize: 12),
                ),
              ),
              const SizedBox(height: 20),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildBadge(String text, Color bgColor, Color textColor) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        text,
        style: TextStyle(
          color: textColor,
          fontWeight: FontWeight.w700,
          fontSize: 12,
        ),
      ),
    );
  }

  Widget _buildStatCard(String value, String unit, String label, {Color? valueColor}) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.grey.shade900,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey.shade800),
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
                  color: valueColor ?? Colors.white,
                ),
              ),
              const SizedBox(width: 4),
              Text(
                unit,
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: valueColor ?? Colors.grey.shade300,
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            label,
            style: TextStyle(color: Colors.grey.shade500, fontSize: 11),
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
              style: TextStyle(
                color: Colors.grey.shade400,
                fontSize: 14,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(
                color: Colors.white,
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