import 'package:flutter/material.dart';

class CCTVManagementPage extends StatelessWidget {
  const CCTVManagementPage({super.key});

  @override
  Widget build(BuildContext context) {
    final cameras = [
      ["CAM-001", "Gate A", "Active", "Jul 29, 2025 - 14:03"],
      ["CAM-002", "Gate B", "Active", "Jul 29, 2025 - 14:02"],
      ["CAM-003", "Gate C", "Offline", "Jul 02, 2025 - 14:02"],
      ["CAM-004", "Gate D", "Active", "Jul 29, 2025 - 14:00"],
      ["CAM-001", "Gate A", "Active", "Jul 29, 2025 - 14:03"],
      ["CAM-002", "Gate B", "Active", "Jul 29, 2025 - 14:02"],
      ["CAM-003", "Gate C", "Offline", "Jul 02, 2025 - 14:02"],
    ];

    return Scaffold(
      backgroundColor: const Color(0xFF05051A),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // === HEADER CARD ===
            Container(
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
                    "CCTV Management",
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
                  const SizedBox(height: 16),
                  // Button Add New Camera
                  Container(
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(30),
                      gradient: const LinearGradient(
                        colors: [Color(0xFF3A5BFF), Color(0xFF192BC2)],
                      ),
                    ),
                    child: ElevatedButton.icon(
                      onPressed: () {},
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.transparent,
                        shadowColor: Colors.transparent,
                        padding: const EdgeInsets.symmetric(
                            horizontal: 20, vertical: 12),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(30),
                        ),
                      ),
                      icon: const Icon(Icons.add, size: 18, color: Colors.white),
                      label: const Text(
                        "Add New Camera",
                        style: TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.bold,
                            color: Colors.white),
                      ),
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 20),

            // === FILTER BUTTONS (Equal Width) ===
            Row(
              children: [
                Expanded(child: _filterButton("All", true)),
                const SizedBox(width: 10),
                Expanded(child: _filterButton("Active", false)),
                const SizedBox(width: 10),
                Expanded(child: _filterButton("Offline", false)),
              ],
            ),

            const SizedBox(height: 20),

            // === TABLE HEADER ===
            Container(
              padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 10),
              decoration: BoxDecoration(
                color: const Color(0xFF0F0F2F),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                children: const [
                  Expanded(flex: 2, child: _TableHeaderText("ID")),
                  Expanded(flex: 3, child: _TableHeaderText("Location")),
                  Expanded(flex: 2, child: _TableHeaderText("Status")),
                  Expanded(flex: 3, child: _TableHeaderText("Last Updated")),
                ],
              ),
            ),

            // === TABLE CONTENT ===
            Expanded(
              child: Container(
                decoration: BoxDecoration(
                  color: const Color(0xFF0A0A2A),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: ListView.builder(
                  itemCount: cameras.length,
                  itemBuilder: (context, index) {
                    final cam = cameras[index];
                    final isActive = cam[2] == "Active";
                    return Container(
                      padding: const EdgeInsets.symmetric(
                          vertical: 12, horizontal: 10),
                      decoration: BoxDecoration(
                        border: Border(
                          bottom: BorderSide(
                              color: Colors.white.withOpacity(0.05)),
                        ),
                      ),
                      child: Row(
                        children: [
                          Expanded(
                            flex: 2,
                            child: Text(
                              cam[0],
                              style: const TextStyle(color: Colors.white70),
                            ),
                          ),
                          Expanded(
                            flex: 3,
                            child: Text(
                              cam[1],
                              style: const TextStyle(color: Colors.white70),
                            ),
                          ),
                          Expanded(
                            flex: 2,
                            child: Text(
                              cam[2],
                              style: TextStyle(
                                color: isActive
                                    ? const Color(0xFF3DC9FF)
                                    : const Color(0xFFFF9900),
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                          Expanded(
                            flex: 3,
                            child: Text(
                              cam[3],
                              style: const TextStyle(color: Colors.white70),
                            ),
                          ),
                        ],
                      ),
                    );
                  },
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _filterButton(String text, bool isSelected) {
    return Container(
      decoration: BoxDecoration(
        color: isSelected ? Colors.blueAccent : const Color(0xFF1B1B3C),
        borderRadius: BorderRadius.circular(20),
      ),
      padding: const EdgeInsets.symmetric(vertical: 8), // lebar otomatis
      alignment: Alignment.center,
      child: Text(
        text,
        style: const TextStyle(
          color: Colors.white,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }
}

// === TABEL HEADER TEXT STYLE ===
class _TableHeaderText extends StatelessWidget {
  final String text;
  const _TableHeaderText(this.text);

  @override
  Widget build(BuildContext context) {
    return Text(
      text,
      style:
          const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
    );
  }
}
