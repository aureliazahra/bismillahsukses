import 'package:flutter/material.dart';

class CctvManagement extends StatefulWidget {
  const CctvManagement({super.key});

  @override
  State<CctvManagement> createState() => _CctvManagementState();
}

class _CctvManagementState extends State<CctvManagement> {
  List<Map<String, String>> cctvData = [
    {
      "id": "CAM-001",
      "location": "Gate A",
      "status": "Active",
      "lastUpdated": "Jul 23, 2025 - 14:02"
    },
    {
      "id": "CAM-002",
      "location": "Gate B",
      "status": "Active",
      "lastUpdated": "Jul 23, 2025 - 14:03"
    },
    {
      "id": "CAM-003",
      "location": "Gate C",
      "status": "Offline",
      "lastUpdated": "Jul 23, 2025 - 14:05"
    },
    {
      "id": "CAM-004",
      "location": "Gate D",
      "status": "Active",
      "lastUpdated": "Jul 23, 2025 - 14:06"
    },
    {
      "id": "CAM-005",
      "location": "Gate E",
      "status": "Active",
      "lastUpdated": "Jul 23, 2025 - 14:09"
    },
    {
      "id": "CAM-006",
      "location": "Gate F",
      "status": "Offline",
      "lastUpdated": "Jul 23, 2025 - 14:10"
    },
  ];

  String filter = "All";

  @override
  Widget build(BuildContext context) {
    List<Map<String, String>> filteredData = filter == "All"
        ? cctvData
        : cctvData.where((cam) => cam["status"] == filter).toList();

    return Scaffold(
      backgroundColor: const Color(0xFF0B1220),
      body: Row(
        children: [
          // ===================== SIDEBAR =====================
          Container(
            width: 250,
            color: const Color(0xFF111A2E),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(height: 30),
                Center(
                  child: Image.asset(
                    "assets/logo_placeholder.png", // Ganti dengan path logo placeholder
                    width: 150,
                  ),
                ),
                const SizedBox(height: 40),
                _buildSidebarItem(Icons.dashboard, "Dashboard"),
                _buildSidebarItem(Icons.videocam, "CCTV Management",
                    isSelected: true),
                _buildSidebarItem(Icons.live_tv, "Real-Time Footage"),
                _buildSidebarItem(Icons.file_copy, "Reports from AI"),
                const Spacer(),
                _buildSidebarItem(Icons.admin_panel_settings, "Admin Management"),
                _buildSidebarItem(Icons.settings, "Settings"),
                const SizedBox(height: 20),
              ],
            ),
          ),

          // ===================== MAIN CONTENT =====================
          Expanded(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Top bar with search & bell icon
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      SizedBox(
                        width: 300,
                        child: TextField(
                          style: const TextStyle(color: Colors.white),
                          decoration: InputDecoration(
                            hintText: "Search",
                            hintStyle:
                                TextStyle(color: Colors.white.withOpacity(0.5)),
                            prefixIcon:
                                const Icon(Icons.search, color: Colors.white),
                            filled: true,
                            fillColor: const Color(0xFF1B2436),
                            border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(30),
                              borderSide: BorderSide.none,
                            ),
                          ),
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.notifications,
                            color: Colors.white),
                        onPressed: () {},
                      )
                    ],
                  ),
                  const SizedBox(height: 20),

                  // Title
                  const Text(
                    "CCTV Management",
                    style: TextStyle(
                        fontSize: 28,
                        fontWeight: FontWeight.bold,
                        color: Colors.white),
                  ),
                  const Text(
                    "One Trace, One Hope.",
                    style: TextStyle(color: Colors.white70, fontSize: 16),
                  ),
                  const SizedBox(height: 10),

                  // Add New Camera Button
                  ElevatedButton(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF0ABEFF),
                      padding:
                          const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                      shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(30)),
                    ),
                    onPressed: () {
                      // Action for adding camera
                    },
                    child: const Text(
                      "Add New Camera",
                      style: TextStyle(color: Colors.white, fontSize: 16),
                    ),
                  ),
                  const SizedBox(height: 20),

                  // Filter Tabs
                  Row(
                    children: [
                      _buildFilterButton("All"),
                      _buildFilterButton("Active"),
                      _buildFilterButton("Offline"),
                    ],
                  ),
                  const SizedBox(height: 20),

                  // Table Header
                  Container(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 20, vertical: 10),
                    color: const Color(0xFF1B2436),
                    child: const Row(
                      children: [
                        Expanded(
                          flex: 2,
                          child: Text("ID",
                              style:
                                  TextStyle(color: Colors.white, fontSize: 16)),
                        ),
                        Expanded(
                          flex: 3,
                          child: Text("Location",
                              style:
                                  TextStyle(color: Colors.white, fontSize: 16)),
                        ),
                        Expanded(
                          flex: 2,
                          child: Text("Status",
                              style:
                                  TextStyle(color: Colors.white, fontSize: 16)),
                        ),
                        Expanded(
                          flex: 3,
                          child: Text("Last Updated",
                              style:
                                  TextStyle(color: Colors.white, fontSize: 16)),
                        ),
                      ],
                    ),
                  ),

                  // Table Data
                  Expanded(
                    child: ListView.builder(
                      itemCount: filteredData.length,
                      itemBuilder: (context, index) {
                        var cam = filteredData[index];
                        return Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 20, vertical: 10),
                          decoration: BoxDecoration(
                            border: Border(
                              bottom: BorderSide(
                                  color: Colors.white.withOpacity(0.1)),
                            ),
                          ),
                          child: Row(
                            children: [
                              Expanded(
                                flex: 2,
                                child: Text(cam["id"]!,
                                    style: const TextStyle(color: Colors.white)),
                              ),
                              Expanded(
                                flex: 3,
                                child: Text(cam["location"]!,
                                    style: const TextStyle(color: Colors.white)),
                              ),
                              Expanded(
                                flex: 2,
                                child: Text(
                                  cam["status"]!,
                                  style: TextStyle(
                                      color: cam["status"] == "Active"
                                          ? Colors.blue
                                          : Colors.red),
                                ),
                              ),
                              Expanded(
                                flex: 3,
                                child: Text(cam["lastUpdated"]!,
                                    style: const TextStyle(color: Colors.white)),
                              ),
                            ],
                          ),
                        );
                      },
                    ),
                  ),
                ],
              ),
            ),
          )
        ],
      ),
    );
  }

  Widget _buildSidebarItem(IconData icon, String title,
      {bool isSelected = false}) {
    return Container(
      decoration: isSelected
          ? BoxDecoration(
              color: const Color(0xFF0ABEFF),
              borderRadius: BorderRadius.circular(10),
            )
          : null,
      margin: const EdgeInsets.symmetric(vertical: 5, horizontal: 10),
      child: ListTile(
        leading: Icon(icon, color: Colors.white),
        title: Text(
          title,
          style: const TextStyle(color: Colors.white),
        ),
        onTap: () {},
      ),
    );
  }

  Widget _buildFilterButton(String title) {
    bool isSelected = filter == title;
    return GestureDetector(
      onTap: () {
        setState(() {
          filter = title;
        });
      },
      child: Container(
        margin: const EdgeInsets.only(right: 10),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(
          color: isSelected ? const Color(0xFF0ABEFF) : const Color(0xFF1B2436),
          borderRadius: BorderRadius.circular(20),
        ),
        child: Text(
          title,
          style: const TextStyle(color: Colors.white),
        ),
      ),
    );
  }
}
