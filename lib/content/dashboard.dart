import 'package:flutter/material.dart';
import 'package:lolos/content/cctvmanagement.dart';
import 'package:lolos/content/missingpeople.dart';
import 'package:lolos/content/notification.dart';

class DashboardPage extends StatefulWidget {
  const DashboardPage({super.key});

  @override
  State<DashboardPage> createState() => _DashboardPageState();
}

class _DashboardPageState extends State<DashboardPage> {
  int selectedPage = 0;
  String searchQuery = "";
  // Jumlah permintaan yang belum diproses
  int unprocessedRequests = 6;
  int onProgress = 4; 
  int activeCameras = 18;
  int totalCameras = 20;
  int detectionsToday = 3;
  int possibleMatches = 14;
  int confirmedMissing = 25;

  // Sidebar menu
  final List<String> menuItems = [
    "Dashboard",
    "CCTV Management",
    "Real-Time Face",
    "Reports",
    "Admin Management",
    "Settings",
  ];

  void _navigateTo(Widget page) {
    Navigator.push(
      context,
      MaterialPageRoute(builder: (_) => page),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0B1220),
      body: Row(
        children: [
          

          // ===================== MAIN CONTENT =====================
          
          Expanded(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Expanded(
  child: SingleChildScrollView(
    padding: const EdgeInsets.all(16.0),
    child: Column(
                children: [
                  // === TOP BAR ===
                  Row(
                    children: [
                      const SizedBox(width: 12),
                      Expanded(
                        child: Container(
                          height: 40,
                          decoration: BoxDecoration(
                            borderRadius: BorderRadius.circular(10),
                            gradient: const LinearGradient(
                              colors: [
                                Color(0x331C3B6D),
                                Color(0x33102544),
                              ],
                              begin: Alignment.topLeft,
                              end: Alignment.bottomRight,
                            ),
                          ),
                          child: Row(
                            children: [
                              const SizedBox(width: 8),
                              Image.asset(
                                'assets/images/search_icon.png',
                                width: 18,
                                height: 18,
                                color: Colors.white.withOpacity(0.9),
                              ),
                              const SizedBox(width: 8),
                              Expanded(
                                child: TextField(
                                  style: const TextStyle(
                                    color: Colors.white,
                                    fontSize: 14,
                                  ),
                                  decoration: const InputDecoration(
                                    hintText: "Search",
                                    hintStyle: TextStyle(
                                      color: Colors.white54,
                                      fontSize: 14,
                                    ),
                                    border: InputBorder.none,
                                    isDense: true,
                                    contentPadding:
                                        EdgeInsets.symmetric(vertical: 8),
                                  ),
                                  onChanged: (value) {
                                    setState(() => searchQuery = value);
                                  },
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                      GestureDetector(
                        onTap: () {
                          _navigateTo(const NotificationsPage());
                        },
                        child: Stack(
                          clipBehavior: Clip.none,
                          children: [
                            Image.asset(
                              'assets/images/bell_icon.png',
                              width: 24,
                              height: 24,
                            ),
                            Positioned(
                              top: -2,
                              right: -2,
                              child: Container(
                                width: 8,
                                height: 8,
                                decoration: const BoxDecoration(
                                  color: Colors.red,
                                  shape: BoxShape.circle,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),

                  const SizedBox(height: 20),

                  // === DASHBOARD TITLE ===
                  const DashboardHeader(),

                  const SizedBox(height: 20),

                  // === USER REQUESTS & CAMERAS ===
                  DashboardStats(
                    unprocessedRequests: unprocessedRequests,
                    onProgress: onProgress,
                    activeCameras: activeCameras,
                    totalCameras: totalCameras,
                    onManageRequests: () =>
                        _navigateTo(const ManageRequestsPage()),
                    onViewCameras: () =>
                        _navigateTo(const CCTVManagementPage()),
                  ),

                  const SizedBox(height: 20),

                  // === MATCHES FACE DETECTED ===
                  Container(
  margin: const EdgeInsets.all(16),
  padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 24),
  decoration: BoxDecoration(
    color: const Color(0xFF1A1B3A),
    borderRadius: BorderRadius.circular(12),
  ),
  child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text(
                "Face Recognition Summary",
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                ),
              ),
              const SizedBox(height: 20),
  
  Row(
    mainAxisAlignment: MainAxisAlignment.spaceEvenly,
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      _buildSummaryStat(
        value: detectionsToday.toString(),
        label: "Detections\nToday",
      ),
      _buildSummaryStat(
        value: possibleMatches.toString(),
        label: "Possible\nMatches",
      ),
      _buildSummaryStat(
        value: confirmedMissing.toString(),
        label: "Confirmed\nMissing\nPerson",
      ),
    ],
  ),
            ],
),
                  ),

                ],
              ),
            ),
          ),
            ),
          ),
        ],
      ),
    );
    
    
  }

  IconData _getIconForMenu(String title) {
    switch (title) {
      case "Dashboard":
        return Icons.dashboard;
      case "CCTV Management":
        return Icons.videocam;
      case "Real-Time Face":
        return Icons.face;
      case "Reports":
        return Icons.description;
      case "Admin Management":
        return Icons.admin_panel_settings;
      case "Settings":
        return Icons.settings;
      default:
        return Icons.circle;
    }
  }

  static Widget _buildSidebarItem(IconData icon, String title,
      {bool isActive = false, VoidCallback? onTap}) {
    return InkWell(
      onTap: onTap,
      child: Container(
        color: isActive ? Colors.blue.withOpacity(0.2) : Colors.transparent,
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        child: Row(
          children: [
            Icon(icon, color: Colors.white, size: 20),
            const SizedBox(width: 12),
            Text(title,
                style: const TextStyle(color: Colors.white, fontSize: 14)),
          ],
        ),
      ),
    );
  }

  static Widget _buildStatBox(String value, String label) {
    return Column(
      children: [
        Text(
          value,
          style: const TextStyle(
            color: Colors.lightBlueAccent,
            fontSize: 28,
            fontWeight: FontWeight.bold,
          ),
        ),
        Text(
          label,
          textAlign: TextAlign.center,
          style: const TextStyle(color: Colors.white54, fontSize: 12),
        ),
      ],
    );
  }

  static Widget _buildBlueButton(String label) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: Colors.blueAccent,
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        label,
        style: const TextStyle(color: Colors.white, fontSize: 12),
      ),
    );
  }
}

// ================= HEADER =================
class DashboardHeader extends StatelessWidget {
  const DashboardHeader({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF0A0A2A), Color(0xFF131347)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: Colors.blue.withOpacity(0.3),
            blurRadius: 20,
            spreadRadius: 2,
            offset: const Offset(0, 5),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            "Dashboard",
            style: TextStyle(
              color: Colors.white,
              fontSize: 28,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 4),
          RichText(
            text: const TextSpan(
              children: [
                TextSpan(
                  text: "One Trace, ",
                  style: TextStyle(
                    color: Colors.white70,
                    fontSize: 16,
                  ),
                ),
                TextSpan(
                  text: "One Hope.",
                  style: TextStyle(
                    color: Color(0xFF57E6FF),
                    fontSize: 16,
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

// ================= stats =================
class DashboardStats extends StatelessWidget {
  final int unprocessedRequests;
  final int onProgress;
  final int activeCameras;
  final int totalCameras;
  final VoidCallback onManageRequests;
  final VoidCallback onViewCameras;

  const DashboardStats({
    super.key,
    required this.unprocessedRequests,
    required this.onProgress,
    required this.activeCameras,
    required this.totalCameras,
    required this.onManageRequests,
    required this.onViewCameras,
  });

  @override
  Widget build(BuildContext context) {
    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Left Card
          Expanded(
            flex: 2,
            child: Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF1B1A40), Color(0xFF12102A)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    "Reported Missing Person",
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 14,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(
                          child: _statusBox(
                              unprocessedRequests.toString(), "Not yet founded")),
                      const SizedBox(width: 12),
                      Expanded(
                          child: _statusBox(
                              onProgress.toString(), "Founded")),
                    ],
                  ),
                  const Spacer(),
                  const SizedBox(height: 20), // jarak lebih besar~
                  Align(
                    alignment: Alignment.center,
                    child:GradientPillButton(
  text: "View Reported Missing Person",
  onPressed: () {
    Navigator.push(context, MaterialPageRoute(
      builder: (context) => MissingPeoplePage(),
    ));
  },
),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(width: 16),
          // Right Card
          // Right Card (Updated Style)
Expanded(
  flex: 1,
  child: Container(
    padding: const EdgeInsets.all(20),
    decoration: BoxDecoration(
      gradient: const LinearGradient(
        colors: [Color(0xFF0D1B3A), Color(0xFF091225)],
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
      ),
      borderRadius: BorderRadius.circular(20),
      boxShadow: [
        BoxShadow(
          color: Colors.black.withOpacity(0.25),
          blurRadius: 12,
          offset: const Offset(0, 6),
        ),
      ],
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.center,
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        const Text(
          "Total Active Cameras",
          style: TextStyle(
            color: Colors.white,
            fontSize: 14,
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(height: 12),
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            ShaderMask(
              shaderCallback: (bounds) => const LinearGradient(
                colors: [Color(0xFF00C6FF), Color(0xFF0072FF)],
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
              ).createShader(Rect.fromLTWH(0, 0, bounds.width, bounds.height)),
              child: Text(
                activeCameras.toString(),
                style: const TextStyle(
                  fontSize: 50,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
              ),
            ),
            const SizedBox(width: 4),
            Text(
              "/$totalCameras",
              style: const TextStyle(
                color: Colors.white,
                fontSize: 24,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),
        GestureDetector(
          onTap: onViewCameras,
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 8),
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [Color(0xFF00C6FF), Color(0xFF0072FF)],
                begin: Alignment.centerLeft,
                end: Alignment.centerRight,
              ),
              borderRadius: BorderRadius.circular(30),
              boxShadow: [
                BoxShadow(
                  color: Colors.blueAccent.withOpacity(0.4),
                  blurRadius: 8,
                  offset: const Offset(0, 3),
                ),
              ],
            ),
            child: const Text(
              "View Cameras List",
              style: TextStyle(
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
),

        ],
      ),
    );
  }

  static Widget _statusBox(String number, String label) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 16),
      decoration: BoxDecoration(
        border: Border.all(color: Colors.blue.shade800, width: 1.5),
        borderRadius: BorderRadius.circular(8),
        color: const Color(0xFF101020),
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          _gradientNumber(number),
          const SizedBox(height: 4),
          Text(
            label,
            textAlign: TextAlign.center,
            style: const TextStyle(
              color: Colors.white70,
              fontSize: 12,
            ),
          ),
        ],
      ),
    );
  }

  static Widget _gradientNumber(String text, {double fontSize = 28}) {
    return ShaderMask(
      shaderCallback: (bounds) => const LinearGradient(
        colors: [Color(0xFF37C8F3), Color(0xFF1E87F0)],
        begin: Alignment.topCenter,
        end: Alignment.bottomCenter,
      ).createShader(Rect.fromLTWH(0, 0, bounds.width, bounds.height)),
      child: Text(
        text,
        style: TextStyle(
          fontSize: fontSize,
          fontWeight: FontWeight.bold,
          color: Colors.white,
        ),
      ),
    );
  }

  static Widget _gradientButton(String text, {required VoidCallback onPressed}) {
    return SizedBox(
      width: double.infinity,
      child: InkWell(
        borderRadius: BorderRadius.circular(30),
        onTap: onPressed,
        child: Ink(
          padding: const EdgeInsets.symmetric(vertical: 10),
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              colors: [Color(0xFF37C8F3), Color(0xFF1E87F0)],
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
            ),
            borderRadius: BorderRadius.circular(30),
          ),
          child: Center(
            child: Text(
              text,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 12,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ),
      ),
    );
  }
}

// =================== PLACEHOLDER PAGES ===================
class ManageRequestsPage extends StatelessWidget {
  const ManageRequestsPage({super.key});
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Manage Requests")),
      body: const Center(child: Text("Manage Requests Page")),
    );
  }
}



class DetectionLogsPage extends StatelessWidget {
  const DetectionLogsPage({super.key});
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Detection Logs")),
      body: const Center(child: Text("Detection Logs Page")),
    );
  }
}



// =================== Gradient Button ===================
class GradientPillButton extends StatelessWidget {
  final String text;
  final VoidCallback onPressed;

  const GradientPillButton({
    super.key,
    required this.text,
    required this.onPressed,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onPressed,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            colors: [Color(0xFF0072FF), Color(0xFF00C6FF)],
            begin: Alignment.centerLeft,
            end: Alignment.centerRight,
          ),
          borderRadius: BorderRadius.circular(30),
          border: Border.all(
            color: Colors.blueAccent.withOpacity(0.3),
            width: 1,
          ),
          boxShadow: [
            BoxShadow(
              color: Colors.blueAccent.withOpacity(0.4),
              blurRadius: 8,
              offset: const Offset(0, 3),
            ),
          ],
        ),
        child: Text(
          text,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 12,
            fontWeight: FontWeight.w600,
          ),
          textAlign: TextAlign.center,
        ),
      ),
    );
  }
}


Widget _buildSummaryStat({required String value, required String label}) {
  final lines = label.split("\n"); // biar gampang bikin 2-3 baris
  return Row(
    crossAxisAlignment: CrossAxisAlignment.end, // teks sejajar bawah angka
    children: [
      ShaderMask(
        shaderCallback: (bounds) => const LinearGradient(
          colors: [Color(0xFF00C6FF), Color(0xFF0072FF)],
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
        ).createShader(bounds),
        child: Text(
          value,
          style: const TextStyle(
            fontSize: 42,
            fontWeight: FontWeight.w900,
            color: Colors.white,
          ),
        ),
      ),
      const SizedBox(width: 6),
      Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: lines.map((line) {
          return Text(
            line,
            style: const TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.w500,
              color: Colors.white,
              height: 1.2,
            ),
          );
        }).toList(),
      ),
    ],
  );
}
