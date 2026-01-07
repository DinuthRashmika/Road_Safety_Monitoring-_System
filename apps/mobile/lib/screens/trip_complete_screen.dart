import 'package:flutter/material.dart';

class TripCompleteScreen extends StatelessWidget {
  final Map<String, dynamic> sessionDetails;
  final String driverName;
  final String sessionId;

  const TripCompleteScreen({
    super.key,
    required this.sessionDetails,
    required this.driverName,
    required this.sessionId,
  });

  @override
  Widget build(BuildContext context) {
    // Extract data with safe defaults
    final distance = sessionDetails['distance']?.toString() ?? '5.0 km';
    final duration = sessionDetails['duration']?.toString() ?? '15:42';
    
    final Map<String, dynamic> violations = (sessionDetails['violations'] is Map)
        ? Map<String, dynamic>.from(sessionDetails['violations'] as Map)
        : {
            'No Seatbelt': 0,
            'Phone in Hand': 0,
            'Drowsiness': 0,
            'Inattention': 0,
            'Lane Deviation': 0,
            'Speeding': 0,
          };

    final phoneViolationTime = sessionDetails['phoneViolationTime']?.toString();

    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        title: const Text('Trip Complete'),
        backgroundColor: Colors.white,
        foregroundColor: Colors.black,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () {
            Navigator.popUntil(context, (route) => route.isFirst);
          },
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          child: Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              children: [
                // Success Icon
                Container(
                  width: 100,
                  height: 100,
                  decoration: BoxDecoration(
                    color: Colors.green.shade50,
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(
                    Icons.check_circle,
                    color: Colors.green,
                    size: 60,
                  ),
                ),
                const SizedBox(height: 20),
                
                // Title
                const Text(
                  'Trip Complete',
                  style: TextStyle(
                    fontSize: 28,
                    fontWeight: FontWeight.bold,
                    color: Colors.black87,
                  ),
                ),
                const SizedBox(height: 8),
                
                // Subtitle
                const Text(
                  'Journey Completed',
                  style: TextStyle(
                    fontSize: 16,
                    color: Colors.grey,
                  ),
                ),
                const SizedBox(height: 20),
                
                // Distance and Time
                Text(
                  '$distance in $duration',
                  style: const TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.w600,
                    color: Colors.black87,
                  ),
                ),
                const SizedBox(height: 32),
                
                // Distance and Duration Cards
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    _buildInfoCard('Total Distance', distance),
                    _buildInfoCard('Duration', duration),
                  ],
                ),
                const SizedBox(height: 40),
                
                // Driver Info
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.blue.shade50,
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Row(
                    children: [
                      CircleAvatar(
                        backgroundColor: Colors.blue.shade100,
                        child: Text(
                          driverName.isNotEmpty ? driverName[0].toUpperCase() : 'D',
                          style: const TextStyle(
                            color: Colors.blue,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Driver: $driverName',
                              style: const TextStyle(
                                fontSize: 14,
                                fontWeight: FontWeight.bold,
                                color: Colors.black87,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              'Session ID: ${sessionId.length > 8 ? '${sessionId.substring(0, 8)}...' : sessionId}',
                              style: TextStyle(
                                fontSize: 12,
                                color: Colors.grey.shade600,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 40),
                
                // Violations Summary
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(24),
                  decoration: BoxDecoration(
                    color: Colors.grey.shade50,
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Violations Summary',
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                          color: Colors.black87,
                        ),
                      ),
                      const SizedBox(height: 24),
                      
                      // Violations Table
                      Column(
                        children: [
                          _buildViolationRow(
                            'No Seatbelt',
                            _getInt(violations['No Seatbelt']),
                            null,
                          ),
                          const SizedBox(height: 16),
                          _buildViolationRow(
                            'Phone in Hand',
                            _getInt(violations['Phone in Hand']),
                            phoneViolationTime,
                          ),
                          const SizedBox(height: 16),
                          _buildViolationRow(
                            'Drowsiness',
                            _getInt(violations['Drowsiness']),
                            null,
                          ),
                          const SizedBox(height: 16),
                          _buildViolationRow(
                            'Inattention',
                            _getInt(violations['Inattention']),
                            null,
                          ),
                          const SizedBox(height: 16),
                          _buildViolationRow(
                            'Lane Deviation',
                            _getInt(violations['Lane Deviation']),
                            null,
                          ),
                          const SizedBox(height: 16),
                          _buildViolationRow(
                            'Speeding',
                            _getInt(violations['Speeding']),
                            null,
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 40),
                
                // Action Buttons
                Row(
                  children: [
                    // Start New Trip Button
                    Expanded(
                      child: OutlinedButton(
                        onPressed: () {
                          Navigator.popUntil(context, (route) => route.isFirst);
                        },
                        style: OutlinedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(vertical: 18),
                          side: BorderSide(color: Colors.grey.shade300),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(14),
                          ),
                        ),
                        child: const Text(
                          'Start New Trip',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w600,
                            color: Colors.black87,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 16),
                    
                    // Save Report Button
                    Expanded(
                      child: ElevatedButton(
                        onPressed: () {
                          _saveReport(context);
                        },
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.blue.shade600,
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(vertical: 18),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(14),
                          ),
                        ),
                        child: const Text(
                          'Save Report',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
                
                // Additional Options
                const SizedBox(height: 20),
                Wrap(
                  spacing: 16,
                  runSpacing: 12,
                  alignment: WrapAlignment.center,
                  children: [
                    TextButton(
                      onPressed: () {
                        _showDetailedReport(context);
                      },
                      child: Text(
                        'View Full Report',
                        style: TextStyle(
                          fontSize: 14,
                          color: Colors.blue.shade600,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                    TextButton(
                      onPressed: () {
                        _shareReport(context);
                      },
                      child: Text(
                        'Share Report',
                        style: TextStyle(
                          fontSize: 14,
                          color: Colors.green.shade600,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildInfoCard(String title, String value) {
    return Container(
      width: 140,
      padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 16),
      decoration: BoxDecoration(
        color: Colors.grey.shade50,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.grey.shade200),
      ),
      child: Column(
        children: [
          Text(
            title,
            style: TextStyle(
              fontSize: 12,
              color: Colors.grey.shade600,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            value,
            style: const TextStyle(
              fontSize: 22,
              fontWeight: FontWeight.bold,
              color: Colors.black87,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildViolationRow(String title, int count, String? time) {
    final hasViolation = count > 0;
    
    return Row(
      children: [
        // Violation Indicator Dot
        Container(
          width: 10,
          height: 10,
          margin: const EdgeInsets.only(right: 12),
          decoration: BoxDecoration(
            color: hasViolation ? Colors.red : Colors.transparent,
            shape: BoxShape.circle,
            border: hasViolation ? null : Border.all(color: Colors.grey.shade400, width: 1),
          ),
        ),
        
        // Violation Title
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: TextStyle(
                  fontSize: 16,
                  color: hasViolation ? Colors.black87 : Colors.grey.shade600,
                  fontWeight: hasViolation ? FontWeight.w500 : FontWeight.normal,
                ),
              ),
              if (hasViolation && time != null && title == 'Phone in Hand')
                const SizedBox(height: 4),
              if (hasViolation && time != null && title == 'Phone in Hand')
                Text(
                  time,
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.grey.shade500,
                  ),
                ),
            ],
          ),
        ),
        
        // Violation Count
        SizedBox(
          width: 50,
          child: Text(
            count.toString(),
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: hasViolation ? Colors.red : Colors.grey.shade600,
            ),
            textAlign: TextAlign.right,
          ),
        ),
      ],
    );
  }

  int _getInt(dynamic value) {
    if (value == null) return 0;
    if (value is int) return value;
    if (value is String) return int.tryParse(value) ?? 0;
    if (value is double) return value.toInt();
    if (value is num) return value.toInt();
    return 0;
  }

  void _saveReport(BuildContext context) {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Report saved successfully!'),
        backgroundColor: Colors.green,
        duration: Duration(seconds: 2),
      ),
    );
    
    // In production, implement actual saving logic here
    print('=== Report Saved ===');
    print('Driver: $driverName');
    print('Session ID: $sessionId');

    print('Violations:');
    print('- No Seatbelt: ${_getInt(sessionDetails['violations']?['No Seatbelt'])}');
    print('- Phone in Hand: ${_getInt(sessionDetails['violations']?['Phone in Hand'])}');
    print('- Drowsiness: ${_getInt(sessionDetails['violations']?['Drowsiness'])}');
    print('- Inattention: ${_getInt(sessionDetails['violations']?['Inattention'])}');
    print('- Lane Deviation: ${_getInt(sessionDetails['violations']?['Lane Deviation'])}');
    print('- Speeding: ${_getInt(sessionDetails['violations']?['Speeding'])}');
  }

  void _showDetailedReport(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Detailed Trip Report'),
        content: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text(
                'Trip Summary',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: Colors.black87,
                ),
              ),
              const SizedBox(height: 12),
              _buildDetailRow('Driver Name:', driverName),
              _buildDetailRow('Session ID:', sessionId),
              _buildDetailRow('Distance:', sessionDetails['distance']?.toString() ?? '5.0 km'),
              _buildDetailRow('Duration:', sessionDetails['duration']?.toString() ?? '15:42'),
              
              const SizedBox(height: 20),
              const Text(
                'Violations Details',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: Colors.black87,
                ),
              ),
              const SizedBox(height: 12),
              _buildDetailRow('No Seatbelt:', _getInt(sessionDetails['violations']?['No Seatbelt']).toString()),
              _buildDetailRow('Phone in Hand:', _getInt(sessionDetails['violations']?['Phone in Hand']).toString()),
             
              const SizedBox(height: 20),
              const Text(
                'Session Data',
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.bold,
                  color: Colors.grey,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'Full session details:',
                style: TextStyle(
                  fontSize: 12,
                  color: Colors.grey.shade600,
                ),
              ),
              const SizedBox(height: 4),
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.grey.shade100,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  sessionDetails.toString(),
                  style: TextStyle(
                    fontSize: 10,
                    color: Colors.grey.shade700,
                    fontFamily: 'Monospace',
                  ),
                  maxLines: 5,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Close'),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              _saveReport(context);
            },
            child: const Text('Save Report'),
          ),
        ],
      ),
    );
  }

  Widget _buildDetailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 140,
            child: Text(
              label,
              style: TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w500,
                color: Colors.grey.shade700,
              ),
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(
                fontSize: 14,
                color: Colors.black87,
              ),
            ),
          ),
        ],
      ),
    );
  }

  void _shareReport(BuildContext context) {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Share functionality coming soon!'),
        backgroundColor: Colors.blue,
        duration: Duration(seconds: 2),
      ),
    );
    
    // In production, implement share functionality:
    // 1. Create PDF report
    // 2. Use share_plus package to share
    // 3. Or implement email/WhatsApp sharing
    
    print('Sharing report for session: $sessionId');
  }
}