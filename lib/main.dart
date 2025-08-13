import 'package:flutter/material.dart';
import 'auth.dart';
import 'layout/layout.dart';
import 'content/dashboard.dart';
import 'content/cctvmanagement.dart';
import 'content/realtime.dart';
import 'content/historylogs.dart';
import 'content/missingpeople.dart';
import 'content/settings.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      home: const LoginPage(),
      routes: {
        '/login': (context) => const LoginPage(),
        '/home': (context) => MainLayout(
              menuItems: const [
                "Dashboard",
                "CCTV Management",
                "Real Time Face Detection",
                "History Logs",
                "Missing People",
                "Settings",
              ],
              pages: [
                const DashboardPage(),
                const CCTVManagementPage(),
                RealTimeDetectionPage(), // ganti dengan nama class yang benar
                const HistoryLogsPage(),
                const MissingPeoplePage(),
                const SettingsPage(),
              ],
            ),
      },
    );
  }
}
