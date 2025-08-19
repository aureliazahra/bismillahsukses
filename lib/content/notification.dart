import 'package:flutter/material.dart';

class NotificationsPage extends StatefulWidget {
  const NotificationsPage({super.key});

  @override
  State<NotificationsPage> createState() => _NotificationsPageState();
}

class _NotificationsPageState extends State<NotificationsPage> {
  // Contoh data notifikasi
  final List<Map<String, dynamic>> notifications = [
    {
      "title": "New Missing Person Report",
      "message": "A new missing person report has been added.",
      "time": "2 min ago",
      "icon": Icons.person_search,
      "color": Colors.lightBlueAccent,
    },
    {
      "title": "Camera Offline",
      "message": "CCTV Camera #5 is currently offline.",
      "time": "10 min ago",
      "icon": Icons.videocam_off,
      "color": Colors.redAccent,
    },
    {
      "title": "Face Detection Match",
      "message": "Possible match detected on Camera #2.",
      "time": "30 min ago",
      "icon": Icons.face,
      "color": Colors.orangeAccent,
    },
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0B1220),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0B1220),
        elevation: 0,
        title: const Text(
          "Notifications",
          style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
        ),
        centerTitle: true,
      ),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: ListView.builder(
          itemCount: notifications.length,
          itemBuilder: (context, index) {
            final notif = notifications[index];
            return Container(
              margin: const EdgeInsets.only(bottom: 16),
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF163B69), Color(0xFF0B1220)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: notif["color"].withOpacity(0.7),
                  width: 1,
                ),
                boxShadow: [
                  BoxShadow(
                    color: notif["color"].withOpacity(0.3),
                    blurRadius: 8,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Row(
                children: [
                  // Icon Notifikasi
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: notif["color"].withOpacity(0.2),
                    ),
                    child: Icon(
                      notif["icon"],
                      color: notif["color"],
                      size: 28,
                    ),
                  ),
                  const SizedBox(width: 16),

                  // Isi Notifikasi
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          notif["title"],
                          style: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                            color: Colors.white,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          notif["message"],
                          style: const TextStyle(
                            fontSize: 14,
                            color: Colors.white70,
                          ),
                        ),
                      ],
                    ),
                  ),

                  // Waktu
                  Text(
                    notif["time"],
                    style: const TextStyle(
                      fontSize: 12,
                      color: Colors.white54,
                    ),
                  ),
                ],
              ),
            );
          },
        ),
      ),
    );
  }
}
