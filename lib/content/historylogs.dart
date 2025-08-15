import 'package:flutter/material.dart';

class HistoryLogsPage extends StatefulWidget {
  const HistoryLogsPage({super.key});

  @override
  State<HistoryLogsPage> createState() => _HistoryLogsPageState();
}

class _HistoryLogsPageState extends State<HistoryLogsPage> {
  List<Map<String, dynamic>> logs = [
    {
      "date": "2025-08-12",
      "time": "12:48:43",
      "camera": "IP Camera Inside",
      "person": "unknown",
      "score": 0.00
    },
    {
      "date": "2025-08-12",
      "time": "12:52:07",
      "camera": "IP Camera Outside",
      "person": "unknown",
      "score": 0.12
    },
    {
      "date": "2025-08-12",
      "time": "12:57:25",
      "camera": "IP Camera Inside",
      "person": "Siti",
      "score": 0.87
    },
    {
      "date": "2025-08-12",
      "time": "12:59:11",
      "camera": "IP Camera Gate",
      "person": "unknown",
      "score": 0.03
    },
    {
      "date": "2025-08-12",
      "time": "13:02:18",
      "camera": "IP Camera Outside",
      "person": "Budi",
      "score": 0.91
    },
    {
      "date": "2025-08-12",
      "time": "13:05:46",
      "camera": "IP Camera Inside",
      "person": "unknown",
      "score": 0.05
    },
    {
      "date": "2025-08-12",
      "time": "13:11:32",
      "camera": "IP Camera Gate",
      "person": "unknown",
      "score": 0.78
    },
    {
      "date": "2025-08-12",
      "time": "13:16:57",
      "camera": "IP Camera Outside",
      "person": "Rudi",
      "score": 0.95
    },
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0B1220),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Search bar
            Container(
              height: 45,
              padding: const EdgeInsets.symmetric(horizontal: 12),
              decoration: BoxDecoration(
                color: const Color(0xFF111A2E),
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Row(
                children: [
                  Icon(Icons.search, color: Colors.white70),
                  SizedBox(width: 8),
                  Expanded(
                    child: TextField(
                      style: TextStyle(color: Colors.white),
                      decoration: InputDecoration(
                        hintText: "Search",
                        hintStyle: TextStyle(color: Colors.white54),
                        border: InputBorder.none,
                      ),
                    ),
                  )
                ],
              ),
            ),
            const SizedBox(height: 20),

            // Title
            const Text(
              "Founded Logs",
              style: TextStyle(
                color: Colors.white,
                fontSize: 22,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 4),
            const Text(
              "Detected missing people on available cameras will automatically recorded as logs here",
              style: TextStyle(color: Colors.white54, fontSize: 14),
            ),
            const SizedBox(height: 20),

            // Table header
            Container(
              padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
              decoration: BoxDecoration(
                color: const Color(0xFF111A2E),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                children: const [
                  Expanded(
                      flex: 2,
                      child: Text("Date",
                          style: TextStyle(color: Colors.white))),
                  Expanded(
                      flex: 2,
                      child: Text("Time",
                          style: TextStyle(color: Colors.white))),
                  Expanded(
                      flex: 3,
                      child: Text("Camera",
                          style: TextStyle(color: Colors.white))),
                  Expanded(
                      flex: 2,
                      child: Text("Person Name",
                          style: TextStyle(color: Colors.white))),
                  Expanded(
                      flex: 2,
                      child: Text("Match Score",
                          style: TextStyle(color: Colors.white))),
                ],
              ),
            ),

            // Table rows
            Expanded(
              child: ListView.builder(
                itemCount: logs.length,
                itemBuilder: (context, index) {
                  final log = logs[index];
                  return Container(
                    padding:
                        const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
                    decoration: BoxDecoration(
                      color: const Color(0xFF0E1A36),
                      border: Border(
                        bottom: BorderSide(
                            color: Colors.white.withOpacity(0.05), width: 1),
                      ),
                    ),
                    child: Row(
                      children: [
                        Expanded(
                            flex: 2,
                            child: Text(log["date"],
                                style: const TextStyle(color: Colors.white))),
                        Expanded(
                            flex: 2,
                            child: Text(log["time"],
                                style: const TextStyle(color: Colors.white))),
                        Expanded(
                            flex: 3,
                            child: Text(log["camera"],
                                style: const TextStyle(color: Colors.white))),
                        Expanded(
                            flex: 2,
                            child: Text(log["person"],
                                style: const TextStyle(color: Colors.white))),
                        Expanded(
                            flex: 2,
                            child: Text(log["score"].toStringAsFixed(2),
                                style: const TextStyle(color: Colors.white))),
                      ],
                    ),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}
