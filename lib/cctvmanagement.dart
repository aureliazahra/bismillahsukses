import 'package:flutter/material.dart';

class CctvManagement extends StatefulWidget {
  const CctvManagement({super.key});

  @override
  State<CctvManagement> createState() => _CctvManagementState();
}

class _CctvManagementState extends State<CctvManagement> {
  List<Map<String, String>> cameraData = [];

  @override
  void initState() {
    super.initState();
    // Simulasi load data awal
    loadCameraData();
  }

  void loadCameraData() {
    // Ini contoh data awal (nanti bisa diganti fetch API atau WebSocket)
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
          "status": "Active",
          "lastUpdated": "Jul 29, 2025 - 14:02"
        },
        {
          "id": "CAM-003",
          "location": "Gate C",
          "status": "Offline",
          "lastUpdated": "Jul 29, 2025 - 14:02"
        },
        {
          "id": "CAM-004",
          "location": "Gate D",
          "status": "Active",
          "lastUpdated": "Jul 29, 2025 - 14:01"
        },
      ];
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0B1220),
      body: Center(
        child: Container(
          width: 600,
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
                headingRowColor: MaterialStateProperty.all(Colors.transparent),
                dataRowColor: MaterialStateProperty.all(Colors.transparent),
                columnSpacing: 40,
                columns: const [
                  DataColumn(
                    label: Text(
                      "ID",
                      style: TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  DataColumn(
                    label: Text(
                      "Location",
                      style: TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  DataColumn(
                    label: Text(
                      "Status",
                      style: TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  DataColumn(
                    label: Text(
                      "Last Updated",
                      style: TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ],
                rows: cameraData.map((cam) {
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
    );
  }
}
