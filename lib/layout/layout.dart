import 'package:flutter/material.dart';
import 'sidebar.dart';

class MainLayout extends StatefulWidget {
  final List<Widget> pages;
  final List<String> menuItems;

  const MainLayout({
    super.key,
    required this.pages,
    required this.menuItems,
  });

  @override
  State<MainLayout> createState() => _MainLayoutState();
}

class _MainLayoutState extends State<MainLayout> {
  int selectedPage = 0;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0B1220),
      body: Row(
        children: [
          Sidebar(
            selectedPage: selectedPage,
            menuItems: widget.menuItems,
            onMenuTap: (index) {
              setState(() => selectedPage = index);
            }, onLogout: () {  },
          ),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: widget.pages[selectedPage],
            ),
          ),
        ],
      ),
    );
  }
}
