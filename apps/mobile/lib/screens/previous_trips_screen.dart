import 'dart:convert';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../core/api_client.dart';
import '../core/token_storage.dart';

class PreviousTripsScreen extends StatefulWidget {
  const PreviousTripsScreen({super.key});

  @override
  State<PreviousTripsScreen> createState() => _PreviousTripsScreenState();
}

class _PreviousTripsScreenState extends State<PreviousTripsScreen> {
  // Colors matching web design
  static const primaryColor = Color(0xFF2563EB);
  static const primaryDeep = Color(0xFF1D4ED8);
  static const primaryLight = Color(0xFFF8E9EB);
  static const inkColor = Color(0xFF0E1113);
  static const grayDark = Color(0xFF8A8F98);
  static const grayMedium = Color(0xFFDADDE1);
  static const grayLight = Color(0xFFF1F2F4);
  static const whiteColor = Color(0xFFFFFFFF);
  static const blackColor = Color(0xFF000000);

  List<dynamic> _trips = [];
  bool _isLoading = true;
  bool _hasError = false;
  bool _hasMore = true;
  String _errorMessage = '';
  int _currentPage = 1;
  final int _pageSize = 20;
  final ScrollController _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    _fetchTrips();
    _scrollController.addListener(_scrollListener);
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  void _scrollListener() {
    if (_scrollController.offset >=
            _scrollController.position.maxScrollExtent &&
        !_scrollController.position.outOfRange &&
        _hasMore &&
        !_isLoading) {
      _loadMoreTrips();
    }
  }

  Future<void> _fetchTrips({bool loadMore = false}) async {
    if (!loadMore) {
      setState(() {
        _isLoading = true;
        _hasError = false;
        _errorMessage = '';
        _currentPage = 1;
        _hasMore = true;
      });
    }

    try {
      // Get auth token
      String? token;
      try {
        token = await TokenStorage.read();
      } catch (e) {
        print('Error reading token: $e');
      }

      // Setup headers
      final Map<String, String> headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      };
      if (token != null && token.isNotEmpty) {
        headers['Authorization'] = 'Bearer $token';
      }

      // API call with pagination
      final response = await ApiClient.dio.get(
        '/api/sessions',
        options: Options(headers: headers),
      );

      // Parse response
      dynamic responseData;
      if (response.data is String) {
        responseData = jsonDecode(response.data as String);
      } else {
        responseData = response.data;
      }

      List<dynamic> newTrips = [];
      if (responseData is List) {
        newTrips = responseData;
      } else if (responseData is Map && responseData.containsKey('data')) {
        newTrips = responseData['data'] is List
            ? responseData['data'] as List<dynamic>
            : [];
      }

      // Pagination
      final startIndex = loadMore ? _trips.length : 0;
      final endIndex = startIndex + _pageSize;
      final paginatedTrips = newTrips.sublist(
        0,
        endIndex < newTrips.length ? endIndex : newTrips.length,
      );

      _hasMore = endIndex < newTrips.length;

      setState(() {
        if (loadMore) {
          _trips.addAll(paginatedTrips);
        } else {
          _trips = paginatedTrips;
        }
        _currentPage++;
      });
    } catch (e) {
      setState(() {
        _hasError = true;
        _errorMessage = e.toString();
        if (!loadMore) _trips = [];
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _loadMoreTrips() async {
    if (_isLoading || !_hasMore) return;
    await _fetchTrips(loadMore: true);
  }

  Future<void> _deleteTrip(String tripId) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Delete Trip'),
        content: const Text('Are you sure you want to delete this trip?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            style: ElevatedButton.styleFrom(backgroundColor: primaryColor),
            child: const Text('Delete'),
          ),
        ],
      ),
    );

    if (confirmed != true) return;

    try {
      String? token = await TokenStorage.read();
      final headers = {
        'Content-Type': 'application/json',
        if (token != null) 'Authorization': 'Bearer $token',
      };
      await ApiClient.dio.delete('/api/sessions/$tripId',
          options: Options(headers: headers));

      setState(() {
        _trips.removeWhere((trip) => trip['id'] == tripId);
      });

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Trip deleted successfully')),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to delete trip: $e')),
      );
    }
  }

  String _formatDate(String dateString) {
    try {
      final date = DateTime.parse(dateString).toLocal();
      return DateFormat('MMM dd, yyyy').format(date);
    } catch (_) {
      return 'Unknown date';
    }
  }

  String _formatTime(String dateString) {
    try {
      final date = DateTime.parse(dateString).toLocal();
      return DateFormat('hh:mm a').format(date);
    } catch (_) {
      return '';
    }
  }

  String _formatDateForDetails(String dateString) {
    try {
      final date = DateTime.parse(dateString).toLocal();
      return DateFormat('EEE, MMM dd, yyyy • hh:mm a').format(date);
    } catch (_) {
      return 'Unknown date';
    }
  }

  String _calculateDuration(String startTime, String? endTime) {
    try {
      final start = DateTime.parse(startTime);
      final end = endTime != null ? DateTime.parse(endTime) : DateTime.now();
      final duration = end.difference(start);
      if (duration.inHours > 0) return '${duration.inHours}h ${duration.inMinutes % 60}m';
      return '${duration.inMinutes}m';
    } catch (_) {
      return 'Ongoing';
    }
  }

  String _calculateDetailedDuration(String startTime, String? endTime) {
    try {
      final start = DateTime.parse(startTime);
      final end = endTime != null ? DateTime.parse(endTime) : DateTime.now();
      final duration = end.difference(start);
      
      if (duration.inDays > 0) {
        return '${duration.inDays} day${duration.inDays > 1 ? 's' : ''} '
               '${duration.inHours % 24} hour${duration.inHours % 24 > 1 ? 's' : ''}';
      } else if (duration.inHours > 0) {
        return '${duration.inHours} hour${duration.inHours > 1 ? 's' : ''} '
               '${duration.inMinutes % 60} minute${duration.inMinutes % 60 > 1 ? 's' : ''}';
      } else {
        return '${duration.inMinutes} minute${duration.inMinutes > 1 ? 's' : ''}';
      }
    } catch (_) {
      return 'Ongoing';
    }
  }

  int _getTotalViolations(Map<String, dynamic>? metrics) {
    if (metrics == null) return 0;
    int total = 0;
    metrics.forEach((key, value) {
      if (value is int) total += value;
      else if (value is String) total += int.tryParse(value) ?? 0;
    });
    return total;
  }

  String _getStatus(String? endTime) => endTime == null ? 'Active' : 'Completed';

  Color _getStatusColor(String status) {
    switch (status.toLowerCase()) {
      case 'active':
        return primaryColor;
      case 'completed':
        return Colors.green;
      default:
        return Colors.grey;
    }
  }

  Widget _buildViolationSummary(Map<String, dynamic>? metrics) {
    if (metrics == null || metrics.isEmpty) {
      return Text(
        'Clean drive',
        style: TextStyle(
          fontSize: 12,
          color: Colors.green,
          fontWeight: FontWeight.w500,
        ),
      );
    }
    
    final totalViolations = _getTotalViolations(metrics);
    if (totalViolations == 0) {
      return Text(
        'Clean drive',
        style: TextStyle(
          fontSize: 12,
          color: Colors.green,
          fontWeight: FontWeight.w500,
        ),
      );
    }
    
    // Get top 2 violations
    final violations = metrics.entries
        .where((entry) {
          int val = 0;
          if (entry.value is int) val = entry.value;
          else if (entry.value is String) val = int.tryParse(entry.value) ?? 0;
          return val > 0;
        })
        .map((entry) => entry.key)
        .take(2)
        .toList();
    
    if (violations.isEmpty) {
      return Text(
        '$totalViolations violation${totalViolations > 1 ? 's' : ''}',
        style: TextStyle(
          fontSize: 12,
          color: totalViolations >= 2 ? Colors.red : Colors.orange,
          fontWeight: FontWeight.w500,
        ),
      );
    }
    
    final violationNames = violations.map((key) {
      final words = key
          .replaceAllMapped(RegExp(r'([A-Z])'), (match) => ' ${match.group(0)}')
          .replaceAll('_', ' ')
          .split(' ')
          .where((word) => word.isNotEmpty)
          .map((word) => '${word[0].toUpperCase()}${word.substring(1).toLowerCase()}')
          .join(' ');
      return words.split(' ').first;
    }).join(' + ');
    
    return Text(
      '$violationNames',
      style: TextStyle(
        fontSize: 12,
        color: totalViolations >= 2 ? Colors.red : Colors.orange,
        fontWeight: FontWeight.w500,
      ),
      maxLines: 1,
      overflow: TextOverflow.ellipsis,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: grayLight.withOpacity(0.3),
      appBar: AppBar(
        backgroundColor: whiteColor,
        elevation: 0,
        centerTitle: true,
        title: const Text(
          'Trip History',
          style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: inkColor),
        ),
      ),
      body: _isLoading && _trips.isEmpty
          ? const Center(child: CircularProgressIndicator(color: primaryColor))
          : _hasError && _trips.isEmpty
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.error_outline, size: 64, color: grayDark),
                      const SizedBox(height: 16),
                      Text(
                        'Failed to load trips',
                        style: TextStyle(fontSize: 16, color: inkColor, fontWeight: FontWeight.w500),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        _errorMessage,
                        style: TextStyle(fontSize: 12, color: grayDark),
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: _fetchTrips,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: primaryColor,
                          foregroundColor: whiteColor,
                        ),
                        child: const Text('Retry'),
                      ),
                    ],
                  ),
                )
              : _trips.isEmpty
                  ? Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.calendar_today_outlined, size: 64, color: grayDark),
                          const SizedBox(height: 16),
                          Text(
                            'No trips found',
                            style: TextStyle(fontSize: 16, color: inkColor, fontWeight: FontWeight.w500),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            'Start a new trip to see it here',
                            style: TextStyle(fontSize: 14, color: grayDark),
                          ),
                        ],
                      ),
                    )
                  : RefreshIndicator(
                      onRefresh: () => _fetchTrips(),
                      color: primaryColor,
                      child: ListView.builder(
                        controller: _scrollController,
                        padding: const EdgeInsets.all(12),
                        itemCount: _trips.length + (_hasMore ? 1 : 0),
                        itemBuilder: (context, index) {
                          if (index == _trips.length) return _buildLoadMoreIndicator();
                          final trip = _trips[index];
                          final tripName = trip['name'] ?? 'Unnamed Trip';
                          final startTime = trip['startedAt'] ?? '';
                          final endTime = trip['endedAt'];
                          final metrics = trip['metrics'];
                          final tripId = trip['id'] ?? '';
                          final status = _getStatus(endTime);
                          final duration = _calculateDuration(startTime, endTime);
                          final totalViolations = _getTotalViolations(metrics != null ? Map<String, dynamic>.from(metrics) : null);

                          return Container(
                            margin: const EdgeInsets.only(bottom: 8),
                            decoration: BoxDecoration(
                              color: whiteColor,
                              borderRadius: BorderRadius.circular(12),
                              boxShadow: const [
                                BoxShadow(
                                  color: Color.fromRGBO(0, 0, 0, 0.04),
                                  blurRadius: 4,
                                  offset: Offset(0, 2),
                                ),
                              ],
                            ),
                            child: Material(
                              color: Colors.transparent,
                              child: InkWell(
                                onTap: () => _showTripDetails(context, trip),
                                borderRadius: BorderRadius.circular(12),
                                child: Padding(
                                  padding: const EdgeInsets.all(16),
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      // First row: Trip name and status
                                      Row(
                                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                        children: [
                                          Expanded(
                                            child: Text(
                                              tripName,
                                              style: const TextStyle(
                                                fontSize: 16,
                                                fontWeight: FontWeight.w600,
                                                color: inkColor,
                                              ),
                                              maxLines: 1,
                                              overflow: TextOverflow.ellipsis,
                                            ),
                                          ),
                                          Container(
                                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                            decoration: BoxDecoration(
                                              color: _getStatusColor(status).withOpacity(0.1),
                                              borderRadius: BorderRadius.circular(6),
                                            ),
                                            child: Text(
                                              status,
                                              style: TextStyle(
                                                fontSize: 11,
                                                color: _getStatusColor(status),
                                                fontWeight: FontWeight.w600,
                                              ),
                                            ),
                                          ),
                                        ],
                                      ),
                                      const SizedBox(height: 6),
                                      
                                      // Second row: Date and time
                                      Row(
                                        children: [
                                          Text(
                                            _formatDate(startTime),
                                            style: TextStyle(
                                              fontSize: 13,
                                              color: grayDark,
                                            ),
                                          ),
                                          const SizedBox(width: 8),
                                          Container(
                                            width: 4,
                                            height: 4,
                                            decoration: BoxDecoration(
                                              color: grayMedium,
                                              shape: BoxShape.circle,
                                            ),
                                          ),
                                          const SizedBox(width: 8),
                                          Text(
                                            _formatTime(startTime),
                                            style: TextStyle(
                                              fontSize: 13,
                                              color: grayDark,
                                            ),
                                          ),
                                        ],
                                      ),
                                      const SizedBox(height: 8),
                                      
                                      // Third row: Duration, violations, and action buttons in one line
                                      Row(
                                        children: [
                                          // Duration
                                          Row(
                                            children: [
                                              Icon(Icons.timer_outlined, size: 16, color: grayDark),
                                              const SizedBox(width: 4),
                                              Text(
                                                duration,
                                                style: TextStyle(
                                                  fontSize: 13,
                                                  fontWeight: FontWeight.w500,
                                                  color: inkColor,
                                                ),
                                              ),
                                            ],
                                          ),
                                          
                                          const SizedBox(width: 12),
                                          
                                          // Violations or clean drive
                                          Expanded(
                                            child: _buildViolationSummary(metrics != null ? Map<String, dynamic>.from(metrics) : null),
                                          ),
                                          
                                          const SizedBox(width: 12),
                                          
                                          // View button (now icon only)
                                          InkWell(
                                            onTap: () => _showTripDetails(context, trip),
                                            borderRadius: BorderRadius.circular(6),
                                            child: Container(
                                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                              decoration: BoxDecoration(
                                                color: primaryColor.withOpacity(0.1),
                                                borderRadius: BorderRadius.circular(6),
                                              ),
                                              child: Row(
                                                children: [
                                                  Icon(Icons.visibility_outlined, size: 14, color: primaryColor),
                                                  const SizedBox(width: 4),
                                                  Text(
                                                    'View',
                                                    style: TextStyle(
                                                      fontSize: 12,
                                                      color: primaryColor,
                                                      fontWeight: FontWeight.w500,
                                                    ),
                                                  ),
                                                ],
                                              ),
                                            ),
                                          ),
                                          
                                          const SizedBox(width: 8),
                                          
                                          // Delete button
                                          InkWell(
                                            onTap: () => _deleteTrip(tripId),
                                            borderRadius: BorderRadius.circular(6),
                                            child: Container(
                                              padding: const EdgeInsets.all(4),
                                              decoration: BoxDecoration(
                                                color: Colors.red.withOpacity(0.1),
                                                borderRadius: BorderRadius.circular(6),
                                              ),
                                              child: Icon(
                                                Icons.delete_outline,
                                                size: 14,
                                                color: Colors.red,
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
                        },
                      ),
                    ),
    );
  }

  Widget _buildLoadMoreIndicator() {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 16),
      child: Center(
        child: _hasMore
            ? const CircularProgressIndicator(color: primaryColor)
            : Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(color: grayLight, borderRadius: BorderRadius.circular(12)),
                child: Text('No more trips', style: TextStyle(fontSize: 14, color: grayDark)),
              ),
      ),
    );
  }

  void _showTripDetails(BuildContext context, dynamic trip) {
    final tripName = trip['name'] ?? 'Unnamed Trip';
    final startTime = trip['startedAt'] ?? '';
    final endTime = trip['endedAt'];
    final metrics = trip['metrics'] != null ? Map<String, dynamic>.from(trip['metrics']) : null;
    final status = _getStatus(endTime);
    final totalViolations = _getTotalViolations(metrics);
    
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: whiteColor,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.only(
          topLeft: Radius.circular(24),
          topRight: Radius.circular(24),
        ),
      ),
      builder: (context) {
        return DraggableScrollableSheet(
          initialChildSize: 0.85,
          minChildSize: 0.5,
          maxChildSize: 0.95,
          expand: false,
          builder: (context, scrollController) {
            return SingleChildScrollView(
              controller: scrollController,
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Header with title and close button
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Expanded(
                          child: Text(
                            'Trip Details',
                            style: TextStyle(
                              fontSize: 22,
                              fontWeight: FontWeight.bold,
                              color: inkColor,
                            ),
                          ),
                        ),
                        IconButton(
                          onPressed: () => Navigator.pop(context),
                          icon: const Icon(Icons.close),
                          color: grayDark,
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    
                    // Trip name
                    Text(
                      tripName,
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.w600,
                        color: primaryDeep,
                      ),
                    ),
                    const SizedBox(height: 20),
                    
                    // Status and dates section
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: grayLight.withOpacity(0.3),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: grayMedium),
                      ),
                      child: Column(
                        children: [
                          Row(
                            children: [
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                                decoration: BoxDecoration(
                                  color: _getStatusColor(status).withOpacity(0.1),
                                  borderRadius: BorderRadius.circular(8),
                                  border: Border.all(color: _getStatusColor(status).withOpacity(0.3)),
                                ),
                                child: Text(
                                  status.toUpperCase(),
                                  style: TextStyle(
                                    color: _getStatusColor(status),
                                    fontSize: 11,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 16),
                          
                          // Start time
                          Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Icon(Icons.play_circle_outline, size: 18, color: primaryColor),
                              const SizedBox(width: 10),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      'Start Time',
                                      style: TextStyle(
                                        fontSize: 11,
                                        color: grayDark,
                                        fontWeight: FontWeight.w500,
                                      ),
                                    ),
                                    const SizedBox(height: 2),
                                    Text(
                                      _formatDateForDetails(startTime),
                                      style: TextStyle(
                                        fontSize: 14,
                                        color: inkColor,
                                        fontWeight: FontWeight.w600,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 12),
                          
                          // End time or ongoing
                          Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Icon(
                                endTime == null ? Icons.timer_outlined : Icons.stop_circle_outlined,
                                size: 18,
                                color: endTime == null ? primaryColor : Colors.green,
                              ),
                              const SizedBox(width: 10),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      endTime == null ? 'Status' : 'End Time',
                                      style: TextStyle(
                                        fontSize: 11,
                                        color: grayDark,
                                        fontWeight: FontWeight.w500,
                                      ),
                                    ),
                                    const SizedBox(height: 2),
                                    Text(
                                      endTime == null 
                                          ? 'Currently Active' 
                                          : _formatDateForDetails(endTime),
                                      style: TextStyle(
                                        fontSize: 14,
                                        color: endTime == null ? primaryColor : inkColor,
                                        fontWeight: FontWeight.w600,
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
                    const SizedBox(height: 20),
                    
                    // Duration and violations summary
                    Row(
                      children: [
                        Expanded(
                          child: _buildDetailMetricItem(
                            icon: Icons.timer,
                            iconColor: primaryColor,
                            label: 'Duration',
                            value: _calculateDetailedDuration(startTime, endTime),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: _buildDetailMetricItem(
                            icon: Icons.warning,
                            iconColor: primaryColor,
                            label: 'Violations',
                            value: '$totalViolations',
                            isViolation: true,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 24),
                    
                    // Violations breakdown section
                    Text(
                      'Violations Breakdown',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                        color: inkColor,
                      ),
                    ),
                    const SizedBox(height: 12),
                    
                    if (metrics == null || metrics.isEmpty)
                      Container(
                        padding: const EdgeInsets.all(24),
                        decoration: BoxDecoration(
                          color: grayLight.withOpacity(0.3),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Column(
                          children: [
                            Icon(Icons.check_circle_outline, size: 40, color: Colors.green),
                            const SizedBox(height: 12),
                            Text(
                              'No violations detected',
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.w600,
                                color: Colors.green,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              'Great driving!',
                              style: TextStyle(
                                fontSize: 14,
                                color: grayDark,
                              ),
                            ),
                          ],
                        ),
                      )
                    else
                      Column(
                        children: metrics.entries.map((entry) {
                          int value = 0;
                          if (entry.value is int) value = entry.value;
                          else if (entry.value is String) value = int.tryParse(entry.value) ?? 0;
                          
                          if (value == 0) return const SizedBox.shrink();
                          
                          return Container(
                            margin: const EdgeInsets.only(bottom: 6),
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: whiteColor,
                              borderRadius: BorderRadius.circular(10),
                              border: Border.all(color: grayLight),
                            ),
                            child: Row(
                              children: [
                                Container(
                                  width: 36,
                                  height: 36,
                                  decoration: BoxDecoration(
                                    color: primaryLight,
                                    borderRadius: BorderRadius.circular(8),
                                  ),
                                  child: Center(
                                    child: Text(
                                      value.toString(),
                                      style: TextStyle(
                                        fontSize: 14,
                                        fontWeight: FontWeight.bold,
                                        color: primaryColor,
                                      ),
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 10),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        _formatViolationName(entry.key),
                                        style: TextStyle(
                                          fontSize: 14,
                                          fontWeight: FontWeight.w600,
                                          color: inkColor,
                                        ),
                                      ),
                                      const SizedBox(height: 2),
                                      Text(
                                        _getViolationDescription(entry.key),
                                        style: TextStyle(
                                          fontSize: 11,
                                          color: grayDark,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                          );
                        }).toList(),
                      ),
                    
                    const SizedBox(height: 20),
                    
                    // Trip ID section
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: grayLight.withOpacity(0.3),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Row(
                        children: [
                          Icon(Icons.info_outline, size: 18, color: grayDark),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  'Trip ID',
                                  style: TextStyle(
                                    fontSize: 11,
                                    color: grayDark,
                                    fontWeight: FontWeight.w500,
                                  ),
                                ),
                                const SizedBox(height: 2),
                                SelectableText(
                                  trip['id'] ?? 'N/A',
                                  style: TextStyle(
                                    fontSize: 13,
                                    color: inkColor,
                                    fontFamily: 'monospace',
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                    
                    const SizedBox(height: 24),
                    
                    // Action buttons
                    Row(
                      children: [
                        Expanded(
                          child: OutlinedButton(
                            onPressed: () => Navigator.pop(context),
                            style: OutlinedButton.styleFrom(
                              foregroundColor: primaryColor,
                              side: BorderSide(color: primaryColor),
                              padding: const EdgeInsets.symmetric(vertical: 14),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(10),
                              ),
                            ),
                            child: const Text('Close'),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: ElevatedButton(
                            onPressed: () => _deleteTrip(trip['id'] ?? ''),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.red,
                              foregroundColor: whiteColor,
                              padding: const EdgeInsets.symmetric(vertical: 14),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(10),
                              ),
                            ),
                            child: const Text('Delete Trip'),
                          ),
                        ),
                      ],
                    ),
                    
                    const SizedBox(height: 20),
                  ],
                ),
              ),
            );
          },
        );
      },
    );
  }

  Widget _buildDetailMetricItem({
    required IconData icon,
    required Color iconColor,
    required String label,
    required String value,
    bool isViolation = false,
  }) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: whiteColor,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: grayLight),
      ),
      child: Column(
        children: [
          Icon(icon, size: 22, color: iconColor),
          const SizedBox(height: 8),
          Text(
            label,
            style: TextStyle(
              fontSize: 11,
              color: grayDark,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            value,
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
              color: isViolation ? primaryColor : inkColor,
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  String _formatViolationName(String key) {
    // Convert snake_case or camelCase to Title Case
    final words = key
        .replaceAllMapped(RegExp(r'([A-Z])'), (match) => ' ${match.group(0)}')
        .replaceAll('_', ' ')
        .split(' ')
        .where((word) => word.isNotEmpty)
        .map((word) => '${word[0].toUpperCase()}${word.substring(1).toLowerCase()}')
        .join(' ');
    
    return words;
  }

  String _getViolationDescription(String key) {
    final Map<String, String> descriptions = {
      'speeding': 'Exceeding the speed limit',
      'hard_brake': 'Sudden and harsh braking',
      'hard_acceleration': 'Rapid acceleration',
      'sharp_turn': 'Taking turns too sharply',
      'distraction': 'Driver distraction detected',
      'fatigue': 'Signs of driver fatigue',
      'tailgating': 'Following too closely',
      'lane_drift': 'Unintentional lane departure',
      'phone_usage': 'Mobile phone usage while driving',
      'seatbelt': 'Seatbelt not fastened',
    };
    
    return descriptions[key.toLowerCase()] ?? 'Safety violation detected';
  }
}