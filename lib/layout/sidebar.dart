import 'package:flutter/material.dart';

class Sidebar extends StatelessWidget {
  final int selectedPage;
  final List<String> menuItems;
  final Function(int) onMenuTap;
  final VoidCallback onLogout; // tambahkan ini

  const Sidebar({
    super.key,
    required this.selectedPage,
    required this.menuItems,
    required this.onMenuTap,
    required this.onLogout, // wajib diisi
  });

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

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 250,
      color: const Color(0xFF111A2E),
      child: Column(
        children: [
          const SizedBox(height: 20),
          Center(
            child: Image.asset(
              'assets/images/obserra.png',
              width: 140,
            ),
          ),
          const SizedBox(height: 30),
          for (int i = 0; i < menuItems.length; i++)
            InkWell(
              onTap: () => onMenuTap(i),
              child: Container(
                color: selectedPage == i
                    ? Colors.blue.withOpacity(0.2)
                    : Colors.transparent,
                padding:
                    const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                child: Row(
                  children: [
                    Icon(
                      _getIconForMenu(menuItems[i]),
                      color: Colors.white,
                      size: 20,
                    ),
                    const SizedBox(width: 12),
                    Text(
                      menuItems[i],
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 14,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          const Spacer(),
          // Tombol Logout
          InkWell(
            onTap: onLogout,
            child: Container(
              padding:
                  const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              color: Colors.transparent,
              child: Row(
                children: const [
                  Icon(
                    Icons.logout,
                    color: Colors.white,
                    size: 20,
                  ),
                  SizedBox(width: 12),
                  Text(
                    'Logout',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 14,
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 20),
        ],
      ),
    );
  }
}
