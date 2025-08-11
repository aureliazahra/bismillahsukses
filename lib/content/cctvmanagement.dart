import 'package:flutter/material.dart';

class CCTVManagementPage extends StatefulWidget {
  const CCTVManagementPage({super.key});

  @override
  State<CCTVManagementPage> createState() => _CCTVManagementPageState();
}

class _CCTVManagementPageState extends State<CCTVManagementPage> {
  String selectedFilter = "All";

  List<Map<String, String>> cameraData = [];

  @override
  void initState() {
    super.initState();
    loadCameraData();
  }

  void loadCameraData() {
    // Simulasi data awal (nanti ganti dengan API/WebSocket)
    setState(() {
      cameraData = [
        {
          "id": "CAM-001",
          "location": "Gate A",
          "status": "Active",
          "lastUpdated": "Jul 29, 2025 - 14:03"
        },
        {
          "id": "CAM-002",
          "location": "Gate B",
          "status": "Offline",
          "lastUpdated": "Jul 29, 2025 - 14:02"
        },
        {
          "id": "CAM-003",
          "location": "Gate C",
          "status": "Active",
          "lastUpdated": "Jul 29, 2025 - 14:01"
        },
        {
          "id": "CAM-004",
          "location": "Gate D",
          "status": "Offline",
          "lastUpdated": "Jul 29, 2025 - 14:00"
        },
      ];
    });
  }

  List<Map<String, String>> get filteredData {
    if (selectedFilter == "All") return cameraData;
    return cameraData
        .where((cam) => cam['status'] == selectedFilter)
        .toList();
  }

  Widget buildFilterButton(String label) {
    bool isSelected = selectedFilter == label;
    return GestureDetector(
      onTap: () {
        setState(() {
          selectedFilter = label;
        });
      },
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 8),
        decoration: BoxDecoration(
          color: isSelected ? const Color(0xFF00C6FF) : Colors.transparent,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: const Color(0xFF00C6FF)),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: isSelected ? Colors.white : const Color(0xFF00C6FF),
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0B1220),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Title & Subtitle
            const Text(
              "CCTV Management",
              style: TextStyle(
                color: Colors.white,
                fontSize: 28,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 4),
            const Text(
              "One Trace, One Hope.",
              style: TextStyle(
                color: Colors.white70,
                fontSize: 16,
              ),
            ),
            const SizedBox(height: 20),

            // Filter Buttons
            Row(
              children: [
                buildFilterButton("All"),
                const SizedBox(width: 10),
                buildFilterButton("Active"),
                const SizedBox(width: 10),
                buildFilterButton("Offline"),
              ],
            ),
            const SizedBox(height: 20),

            // Table
            Expanded(
              child: Container(
                width: double.infinity,
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFF0F1E36), Color(0xFF081325)],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(12),
                  child: SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
                    child: DataTable(
                      headingRowColor:
                          WidgetStateProperty.all(Colors.transparent),
                      dataRowColor:
                          WidgetStateProperty.all(Colors.transparent),
                      columnSpacing: 40,
                      columns: const [
                        DataColumn(
                          label: Text("ID",
                              style: TextStyle(
                                  color: Colors.white,
                                  fontWeight: FontWeight.bold)),
                        ),
                        DataColumn(
                          label: Text("Location",
                              style: TextStyle(
                                  color: Colors.white,
                                  fontWeight: FontWeight.bold)),
                        ),
                        DataColumn(
                          label: Text("Status",
                              style: TextStyle(
                                  color: Colors.white,
                                  fontWeight: FontWeight.bold)),
                        ),
                        DataColumn(
                          label: Text("Last Updated",
                              style: TextStyle(
                                  color: Colors.white,
                                  fontWeight: FontWeight.bold)),
                        ),
                      ],
                      rows: filteredData.map((cam) {
                        final status = cam['status'] ?? '';
                        return DataRow(
                          cells: [
                            DataCell(Text(
                              cam['id'] ?? '',
                              style: const TextStyle(color: Colors.white),
                            )),
                            DataCell(Text(
                              cam['location'] ?? '',
                              style: const TextStyle(color: Colors.white),
                            )),
                            DataCell(Text(
                              status,
                              style: TextStyle(
                                color: status == "Active"
                                    ? const Color(0xFF00C6FF)
                                    : const Color(0xFFFF6B35),
                                fontWeight: FontWeight.bold,
                              ),
                            )),
                            DataCell(Text(
                              cam['lastUpdated'] ?? '',
                              style: const TextStyle(
                                color: Colors.white70,
                                fontSize: 12,
                              ),
                            )),
                          ],
                        );
                      }).toList(),
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
