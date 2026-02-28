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
  // ===== Dark Theme (match your app) =====
  static const Color primaryBlue = Color(0xFF2563EB);
  static const Color primaryDeep = Color(0xFF1D4ED8);

  static const Color bgBlack = Colors.black;
  static const Color cardDark = Color(0xFF111827);
  static const Color borderDark = Color(0xFF1F2937);
  static const Color textWhite = Colors.white;
  static const Color textMuted = Color(0xFF9CA3AF);

  static const Color okGreen = Color(0xFF10B981);
  static const Color warnOrange = Color(0xFFF59E0B);
  static const Color dangerRed = Color(0xFFEF4444);

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
        // ignore: avoid_print
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

      // API call (your same endpoint)
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
        backgroundColor: cardDark,
        title: const Text('Delete Trip',
            style: TextStyle(color: textWhite, fontWeight: FontWeight.w800)),
        content: const Text(
          'Are you sure you want to delete this trip?',
          style: TextStyle(color: textMuted),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel', style: TextStyle(color: textMuted)),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            style: ElevatedButton.styleFrom(backgroundColor: dangerRed),
            child: const Text('Delete', style: TextStyle(color: textWhite)),
          ),
        ],
      ),
    );

    if (confirmed != true) return;

    try {
      String? token = await TokenStorage.read();
      final headers = {
        'Content-Type': 'application/json',
        if (token != null && token.isNotEmpty) 'Authorization': 'Bearer $token',
      };

      await ApiClient.dio.delete(
        '/api/sessions/$tripId',
        options: Options(headers: headers),
      );

      setState(() {
        _trips.removeWhere((trip) => (trip['id'] ?? '').toString() == tripId);
      });

      _snack('Trip deleted successfully', okGreen);
    } catch (e) {
      _snack('Failed to delete trip: $e', dangerRed);
    }
  }

  void _snack(String msg, Color color) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        backgroundColor: cardDark,
        content: Row(
          children: [
            Icon(Icons.info_outline, color: color, size: 18),
            const SizedBox(width: 10),
            Expanded(
              child: Text(
                msg,
                style: const TextStyle(color: textWhite),
              ),
            ),
          ],
        ),
      ),
    );
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
      if (duration.inHours > 0) {
        return '${duration.inHours}h ${duration.inMinutes % 60}m';
      }
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
      if (value is int)
        total += value;
      else if (value is String) total += int.tryParse(value) ?? 0;
    });
    return total;
  }

  String _getStatus(String? endTime) =>
      endTime == null ? 'Active' : 'Completed';

  Color _getStatusColor(String status) {
    switch (status.toLowerCase()) {
      case 'active':
        return primaryBlue;
      case 'completed':
        return okGreen;
      default:
        return textMuted;
    }
  }

  Widget _buildViolationSummary(Map<String, dynamic>? metrics) {
    if (metrics == null || metrics.isEmpty) {
      return const Text(
        'Clean drive',
        style: TextStyle(
          fontSize: 12,
          color: okGreen,
          fontWeight: FontWeight.w700,
        ),
      );
    }

    final totalViolations = _getTotalViolations(metrics);
    if (totalViolations == 0) {
      return const Text(
        'Clean drive',
        style: TextStyle(
          fontSize: 12,
          color: okGreen,
          fontWeight: FontWeight.w700,
        ),
      );
    }

    Color c = totalViolations >= 2 ? dangerRed : warnOrange;

    return Text(
      '$totalViolations violation${totalViolations > 1 ? 's' : ''}',
      style: TextStyle(
        fontSize: 12,
        color: c,
        fontWeight: FontWeight.w700,
      ),
      maxLines: 1,
      overflow: TextOverflow.ellipsis,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: bgBlack,
      appBar: AppBar(
        backgroundColor: bgBlack,
        elevation: 0,
        centerTitle: true,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: textWhite),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text(
          'Trip History',
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.w900,
            color: textWhite,
          ),
        ),
      ),
      body: _isLoading && _trips.isEmpty
          ? const Center(
              child: CircularProgressIndicator(
                color: primaryBlue,
                strokeWidth: 2,
              ),
            )
          : _hasError && _trips.isEmpty
              ? _buildErrorState()
              : _trips.isEmpty
                  ? _buildEmptyState()
                  : RefreshIndicator(
                      onRefresh: () => _fetchTrips(),
                      color: primaryBlue,
                      child: ListView.builder(
                        controller: _scrollController,
                        padding: const EdgeInsets.all(12),
                        itemCount: _trips.length + (_hasMore ? 1 : 0),
                        itemBuilder: (context, index) {
                          if (index == _trips.length) {
                            return _buildLoadMoreIndicator();
                          }

                          final trip = _trips[index];
                          final tripName = trip['name'] ?? 'Unnamed Trip';
                          final startTime = trip['startedAt'] ?? '';
                          final endTime = trip['endedAt'];
                          final metrics = trip['metrics'];
                          final tripId = (trip['id'] ?? '').toString();

                          final status = _getStatus(endTime?.toString());
                          final duration = _calculateDuration(
                              startTime.toString(), endTime?.toString());

                          return Container(
                            margin: const EdgeInsets.only(bottom: 10),
                            decoration: BoxDecoration(
                              color: cardDark,
                              borderRadius: BorderRadius.circular(16),
                              border: Border.all(color: borderDark),
                              boxShadow: [
                                BoxShadow(
                                  color: Colors.black.withOpacity(0.35),
                                  blurRadius: 14,
                                  offset: const Offset(0, 6),
                                )
                              ],
                            ),
                            child: Material(
                              color: Colors.transparent,
                              child: InkWell(
                                onTap: () => _showTripDetails(context, trip),
                                borderRadius: BorderRadius.circular(16),
                                child: Padding(
                                  padding: const EdgeInsets.all(16),
                                  child: Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                      // Trip name + status
                                      Row(
                                        children: [
                                          Expanded(
                                            child: Text(
                                              tripName.toString(),
                                              style: const TextStyle(
                                                fontSize: 16,
                                                fontWeight: FontWeight.w800,
                                                color: textWhite,
                                              ),
                                              maxLines: 1,
                                              overflow: TextOverflow.ellipsis,
                                            ),
                                          ),
                                          Container(
                                            padding: const EdgeInsets.symmetric(
                                                horizontal: 10, vertical: 6),
                                            decoration: BoxDecoration(
                                              color: _getStatusColor(status)
                                                  .withOpacity(0.18),
                                              borderRadius:
                                                  BorderRadius.circular(10),
                                              border: Border.all(
                                                color: _getStatusColor(status)
                                                    .withOpacity(0.35),
                                              ),
                                            ),
                                            child: Text(
                                              status,
                                              style: TextStyle(
                                                fontSize: 11,
                                                color: _getStatusColor(status),
                                                fontWeight: FontWeight.w800,
                                              ),
                                            ),
                                          ),
                                        ],
                                      ),
                                      const SizedBox(height: 8),

                                      // Date + time
                                      Row(
                                        children: [
                                          Text(
                                            _formatDate(startTime.toString()),
                                            style: const TextStyle(
                                              fontSize: 13,
                                              color: textMuted,
                                            ),
                                          ),
                                          const SizedBox(width: 8),
                                          Container(
                                            width: 4,
                                            height: 4,
                                            decoration: const BoxDecoration(
                                              color: borderDark,
                                              shape: BoxShape.circle,
                                            ),
                                          ),
                                          const SizedBox(width: 8),
                                          Text(
                                            _formatTime(startTime.toString()),
                                            style: const TextStyle(
                                              fontSize: 13,
                                              color: textMuted,
                                            ),
                                          ),
                                        ],
                                      ),
                                      const SizedBox(height: 10),

                                      // Duration + violations + actions
                                      Row(
                                        children: [
                                          Row(
                                            children: [
                                              const Icon(Icons.timer_outlined,
                                                  size: 16, color: textMuted),
                                              const SizedBox(width: 6),
                                              Text(
                                                duration,
                                                style: const TextStyle(
                                                  fontSize: 13,
                                                  fontWeight: FontWeight.w700,
                                                  color: textWhite,
                                                ),
                                              ),
                                            ],
                                          ),
                                          const SizedBox(width: 12),

                                          Expanded(
                                            child: _buildViolationSummary(
                                              metrics != null
                                                  ? Map<String, dynamic>.from(
                                                      metrics)
                                                  : null,
                                            ),
                                          ),

                                          const SizedBox(width: 10),

                                          // View
                                          InkWell(
                                            onTap: () =>
                                                _showTripDetails(context, trip),
                                            borderRadius:
                                                BorderRadius.circular(10),
                                            child: Container(
                                              padding:
                                                  const EdgeInsets.symmetric(
                                                      horizontal: 10,
                                                      vertical: 8),
                                              decoration: BoxDecoration(
                                                color: primaryBlue
                                                    .withOpacity(0.18),
                                                borderRadius:
                                                    BorderRadius.circular(10),
                                                border: Border.all(
                                                  color: primaryBlue
                                                      .withOpacity(0.35),
                                                ),
                                              ),
                                              child: Row(
                                                children: const [
                                                  Icon(
                                                    Icons.visibility_outlined,
                                                    size: 16,
                                                    color: primaryBlue,
                                                  ),
                                                  SizedBox(width: 6),
                                                  Text(
                                                    'View',
                                                    style: TextStyle(
                                                      fontSize: 12,
                                                      color: primaryBlue,
                                                      fontWeight:
                                                          FontWeight.w800,
                                                    ),
                                                  ),
                                                ],
                                              ),
                                            ),
                                          ),

                                          const SizedBox(width: 8),

                                          // Delete
                                          InkWell(
                                            onTap: () => _deleteTrip(tripId),
                                            borderRadius:
                                                BorderRadius.circular(10),
                                            child: Container(
                                              padding: const EdgeInsets.all(8),
                                              decoration: BoxDecoration(
                                                color:
                                                    dangerRed.withOpacity(0.18),
                                                borderRadius:
                                                    BorderRadius.circular(10),
                                                border: Border.all(
                                                  color: dangerRed
                                                      .withOpacity(0.35),
                                                ),
                                              ),
                                              child: const Icon(
                                                Icons.delete_outline,
                                                size: 16,
                                                color: dangerRed,
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

  Widget _buildErrorState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(22),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 64, color: textMuted),
            const SizedBox(height: 16),
            const Text(
              'Failed to load trips',
              style: TextStyle(
                  fontSize: 16, color: textWhite, fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 8),
            Text(
              _errorMessage,
              style: const TextStyle(fontSize: 12, color: textMuted),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            Container(
              decoration: BoxDecoration(
                gradient:
                    const LinearGradient(colors: [primaryBlue, primaryDeep]),
                borderRadius: BorderRadius.circular(14),
                boxShadow: [
                  BoxShadow(
                    color: primaryBlue.withOpacity(0.45),
                    blurRadius: 14,
                    offset: const Offset(0, 6),
                  )
                ],
              ),
              child: ElevatedButton(
                onPressed: _fetchTrips,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.transparent,
                  shadowColor: Colors.transparent,
                  foregroundColor: textWhite,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(14),
                  ),
                ),
                child: const Padding(
                  padding: EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                  child: Text('Retry',
                      style:
                          TextStyle(fontWeight: FontWeight.w900, fontSize: 14)),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildEmptyState() {
    return const Center(
      child: Padding(
        padding: EdgeInsets.all(22),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.calendar_today_outlined, size: 64, color: textMuted),
            SizedBox(height: 16),
            Text(
              'No trips found',
              style: TextStyle(
                  fontSize: 16, color: textWhite, fontWeight: FontWeight.w800),
            ),
            SizedBox(height: 8),
            Text(
              'Start a new trip to see it here',
              style: TextStyle(fontSize: 14, color: textMuted),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLoadMoreIndicator() {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 16),
      child: Center(
        child: _hasMore
            ? const CircularProgressIndicator(
                color: primaryBlue, strokeWidth: 2)
            : Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: cardDark,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: borderDark),
                ),
                child: const Text('No more trips',
                    style: TextStyle(fontSize: 14, color: textMuted)),
              ),
      ),
    );
  }

  void _showTripDetails(BuildContext context, dynamic trip) {
    final tripName = trip['name'] ?? 'Unnamed Trip';
    final startTime = (trip['startedAt'] ?? '').toString();
    final endTime = trip['endedAt']?.toString();
    final metrics = trip['metrics'] != null
        ? Map<String, dynamic>.from(trip['metrics'])
        : null;
    final status = _getStatus(endTime);
    final totalViolations = _getTotalViolations(metrics);

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: cardDark,
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
                padding: const EdgeInsets.all(22),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Header
                    Row(
                      children: [
                        const Expanded(
                          child: Text(
                            'Trip Details',
                            style: TextStyle(
                              fontSize: 22,
                              fontWeight: FontWeight.w900,
                              color: textWhite,
                            ),
                          ),
                        ),
                        IconButton(
                          onPressed: () => Navigator.pop(context),
                          icon: const Icon(Icons.close, color: textMuted),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),

                    Text(
                      tripName.toString(),
                      style: const TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.w800,
                        color: primaryBlue,
                      ),
                    ),
                    const SizedBox(height: 18),

                    // Status + times
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: const Color(0xFF0B1220),
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(color: borderDark),
                      ),
                      child: Column(
                        children: [
                          Row(
                            children: [
                              Container(
                                padding: const EdgeInsets.symmetric(
                                    horizontal: 10, vertical: 6),
                                decoration: BoxDecoration(
                                  color:
                                      _getStatusColor(status).withOpacity(0.18),
                                  borderRadius: BorderRadius.circular(10),
                                  border: Border.all(
                                    color: _getStatusColor(status)
                                        .withOpacity(0.35),
                                  ),
                                ),
                                child: Text(
                                  status.toUpperCase(),
                                  style: TextStyle(
                                    color: _getStatusColor(status),
                                    fontSize: 11,
                                    fontWeight: FontWeight.w900,
                                  ),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 14),
                          _detailRow(
                            icon: Icons.play_circle_outline,
                            iconColor: primaryBlue,
                            label: 'Start Time',
                            value: _formatDateForDetails(startTime),
                          ),
                          const SizedBox(height: 12),
                          _detailRow(
                            icon: endTime == null
                                ? Icons.timer_outlined
                                : Icons.stop_circle_outlined,
                            iconColor: endTime == null ? primaryBlue : okGreen,
                            label: endTime == null ? 'Status' : 'End Time',
                            value: endTime == null
                                ? 'Currently Active'
                                : _formatDateForDetails(endTime),
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 18),

                    Row(
                      children: [
                        Expanded(
                          child: _metricCard(
                            icon: Icons.timer,
                            iconColor: primaryBlue,
                            label: 'Duration',
                            value:
                                _calculateDetailedDuration(startTime, endTime),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: _metricCard(
                            icon: Icons.warning_amber_rounded,
                            iconColor: primaryBlue,
                            label: 'Violations',
                            value: '$totalViolations',
                            valueColor: totalViolations == 0
                                ? okGreen
                                : (totalViolations >= 2
                                    ? dangerRed
                                    : warnOrange),
                          ),
                        ),
                      ],
                    ),

                    const SizedBox(height: 20),

                    const Text(
                      'Violations Breakdown',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.w900,
                        color: textWhite,
                      ),
                    ),
                    const SizedBox(height: 12),

                    if (metrics == null || metrics.isEmpty)
                      Container(
                        padding: const EdgeInsets.all(22),
                        decoration: BoxDecoration(
                          color: const Color(0xFF0B1220),
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(color: borderDark),
                        ),
                        child: Column(
                          children: const [
                            Icon(Icons.check_circle_outline,
                                size: 40, color: okGreen),
                            SizedBox(height: 10),
                            Text(
                              'No violations detected',
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.w800,
                                color: okGreen,
                              ),
                            ),
                            SizedBox(height: 4),
                            Text('Great driving!',
                                style: TextStyle(color: textMuted)),
                          ],
                        ),
                      )
                    else
                      Column(
                        children: metrics.entries.map((entry) {
                          int value = 0;
                          if (entry.value is int)
                            value = entry.value;
                          else if (entry.value is String) {
                            value = int.tryParse(entry.value) ?? 0;
                          }

                          if (value == 0) return const SizedBox.shrink();

                          return Container(
                            margin: const EdgeInsets.only(bottom: 10),
                            padding: const EdgeInsets.all(14),
                            decoration: BoxDecoration(
                              color: const Color(0xFF0B1220),
                              borderRadius: BorderRadius.circular(14),
                              border: Border.all(color: borderDark),
                            ),
                            child: Row(
                              children: [
                                Container(
                                  width: 38,
                                  height: 38,
                                  decoration: BoxDecoration(
                                    color: primaryBlue.withOpacity(0.18),
                                    borderRadius: BorderRadius.circular(12),
                                    border: Border.all(
                                        color: primaryBlue.withOpacity(0.35)),
                                  ),
                                  child: Center(
                                    child: Text(
                                      value.toString(),
                                      style: const TextStyle(
                                        color: primaryBlue,
                                        fontWeight: FontWeight.w900,
                                      ),
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        _formatViolationName(entry.key),
                                        style: const TextStyle(
                                          fontSize: 14,
                                          fontWeight: FontWeight.w800,
                                          color: textWhite,
                                        ),
                                      ),
                                      const SizedBox(height: 4),
                                      Text(
                                        _getViolationDescription(entry.key),
                                        style: const TextStyle(
                                            fontSize: 12, color: textMuted),
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                          );
                        }).toList(),
                      ),

                    const SizedBox(height: 18),

                    Container(
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: const Color(0xFF0B1220),
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(color: borderDark),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.info_outline,
                              size: 18, color: textMuted),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text('Trip ID',
                                    style: TextStyle(
                                        fontSize: 11,
                                        color: textMuted,
                                        fontWeight: FontWeight.w700)),
                                const SizedBox(height: 4),
                                SelectableText(
                                  (trip['id'] ?? 'N/A').toString(),
                                  style: const TextStyle(
                                    fontSize: 13,
                                    color: textWhite,
                                    fontFamily: 'monospace',
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 18),

                    Row(
                      children: [
                        Expanded(
                          child: OutlinedButton(
                            onPressed: () => Navigator.pop(context),
                            style: OutlinedButton.styleFrom(
                              foregroundColor: primaryBlue,
                              side: BorderSide(
                                  color: primaryBlue.withOpacity(0.6)),
                              padding: const EdgeInsets.symmetric(vertical: 14),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(14),
                              ),
                            ),
                            child: const Text('Close',
                                style: TextStyle(fontWeight: FontWeight.w900)),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: ElevatedButton(
                            onPressed: () =>
                                _deleteTrip((trip['id'] ?? '').toString()),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: dangerRed,
                              foregroundColor: textWhite,
                              padding: const EdgeInsets.symmetric(vertical: 14),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(14),
                              ),
                            ),
                            child: const Text('Delete Trip',
                                style: TextStyle(fontWeight: FontWeight.w900)),
                          ),
                        ),
                      ],
                    ),

                    const SizedBox(height: 18),
                  ],
                ),
              ),
            );
          },
        );
      },
    );
  }

  Widget _detailRow({
    required IconData icon,
    required Color iconColor,
    required String label,
    required String value,
  }) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, size: 18, color: iconColor),
        const SizedBox(width: 10),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label,
                  style: const TextStyle(
                      fontSize: 11,
                      color: textMuted,
                      fontWeight: FontWeight.w700)),
              const SizedBox(height: 2),
              Text(value,
                  style: const TextStyle(
                      fontSize: 14,
                      color: textWhite,
                      fontWeight: FontWeight.w800)),
            ],
          ),
        ),
      ],
    );
  }

  Widget _metricCard({
    required IconData icon,
    required Color iconColor,
    required String label,
    required String value,
    Color valueColor = textWhite,
  }) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFF0B1220),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: borderDark),
      ),
      child: Column(
        children: [
          Icon(icon, size: 22, color: iconColor),
          const SizedBox(height: 8),
          Text(label,
              style: const TextStyle(
                  fontSize: 11, color: textMuted, fontWeight: FontWeight.w700)),
          const SizedBox(height: 6),
          Text(value,
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w900,
                color: valueColor,
              ),
              textAlign: TextAlign.center),
        ],
      ),
    );
  }

  String _formatViolationName(String key) {
    final words = key
        .replaceAllMapped(RegExp(r'([A-Z])'), (match) => ' ${match.group(0)}')
        .replaceAll('_', ' ')
        .split(' ')
        .where((word) => word.isNotEmpty)
        .map((word) =>
            '${word[0].toUpperCase()}${word.substring(1).toLowerCase()}')
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
