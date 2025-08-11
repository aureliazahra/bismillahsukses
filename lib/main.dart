import 'package:flutter/material.dart';
import 'auth.dart';
import 'layout/layout.dart';
import 'content/dashboard.dart';
import 'content/cctvmanagement.dart';
import 'content/realtime.dart';
import 'content/reportuser.dart';

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
                "Real-Time Face",
                "Reports",
                "Admin Management",
                "Settings",
              ],
              pages: const [
                DashboardPage(),
                CCTVManagementPage(),
                RealTimeFacePage(),
                ReportUserPage(),
                Center(
                  child: Text(
                    "Admin Management Page",
                    style: TextStyle(color: Colors.white),
                  ),
                ),
                Center(
                  child: Text(
                    "Settings Page",
                    style: TextStyle(color: Colors.white),
                  ),
                ),
              ],
            ),
      },
    );
  }
}
