import 'package:flutter/material.dart';

class CCTVManagementPage extends StatefulWidget {
  const CCTVManagementPage({super.key});

  @override
  State<CCTVManagementPage> createState() => _CCTVManagementPageState();
}

class _CCTVManagementPageState extends State<CCTVManagementPage> {
  String selectedFilter = "All";

  // Static camera data matching the image
  final List<Map<String, dynamic>> cameras = [
    {
      'id': 'CAM-001',
      'location': 'Gate A',
      'status': 'Active',
      'lastUpdated': '2m ago',
    },
    {
      'id': 'CAM-002',
      'location': 'Gate B',
      'status': 'Active',
      'lastUpdated': '1m ago',
    },
    {
      'id': 'CAM-003',
      'location': 'Gate C',
      'status': 'Offline',
      'lastUpdated': '17/7/2025 - 0:18',
    },
  ];

  List<Map<String, dynamic>> get filteredCameras {
    if (selectedFilter == "All") return cameras;
    return cameras.where((camera) => camera['status'] == selectedFilter).toList();
  }

  @override
  Widget build(BuildContext context) {
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
                      onPressed: () {
                        // Static button - no functionality
                      },
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
            
            Row(
              children: [
                Expanded(child: _filterButton("All", selectedFilter == "All")),
                const SizedBox(width: 10),
                Expanded(child: _filterButton("Active", selectedFilter == "Active")),
                const SizedBox(width: 10),
                Expanded(child: _filterButton("Offline", selectedFilter == "Offline")),
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
                  Expanded(flex: 2, child: _TableHeaderText("Actions")),
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
                  itemCount: filteredCameras.length,
                  itemBuilder: (context, index) {
                    final camera = filteredCameras[index];
                    final isActive = camera['status'] == "Active";
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
                              camera['id'],
                              style: const TextStyle(color: Colors.white70),
                            ),
                          ),
                          Expanded(
                            flex: 3,
                            child: Text(
                              camera['location'],
                              style: const TextStyle(color: Colors.white70),
                            ),
                          ),
                          Expanded(
                            flex: 2,
                            child: Text(
                              camera['status'],
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
                              camera['lastUpdated'],
                              style: const TextStyle(color: Colors.white70),
                            ),
                          ),
                          Expanded(
                            flex: 2,
                            child: Row(
                              children: [
                                IconButton(
                                  icon: Icon(
                                    isActive ? Icons.pause : Icons.play_arrow,
                                    color: Colors.white70,
                                    size: 20,
                                  ),
                                  onPressed: () {
                                    // Static button - no functionality
                                  },
                                ),
                                IconButton(
                                  icon: const Icon(
                                    Icons.settings,
                                    color: Colors.white70,
                                    size: 20,
                                  ),
                                  onPressed: () {
                                    // Static button - no functionality
                                  },
                                ),
                              ],
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
    return GestureDetector(
      onTap: () {
        setState(() {
          selectedFilter = text;
        });
      },
      child: Container(
        decoration: BoxDecoration(
          color: isSelected ? Colors.blueAccent : const Color(0xFF1B1B3C),
          borderRadius: BorderRadius.circular(20),
        ),
        padding: const EdgeInsets.symmetric(vertical: 8),
        alignment: Alignment.center,
        child: Text(
          text,
          style: const TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
    );
  }
}

// === TABLE HEADER TEXT STYLE ===
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
