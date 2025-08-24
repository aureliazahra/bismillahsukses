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
        padding: const EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ==== HEADER BAR ====
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
              child: const Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    "Founded Logs",
                    style: TextStyle(
                      fontSize: 28,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                  SizedBox(height: 4),
                  Text(
                    "Detected missing people on available cameras will automatically recorded as logs here",
                    style: TextStyle(
                      fontSize: 14,
                      color: Colors.white70,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            // ==== TABLE HEADER ====
            Container(
              padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
              decoration: BoxDecoration(
                color: const Color(0xFF1A237E),
                borderRadius: const BorderRadius.only(
                  topLeft: Radius.circular(12),
                  topRight: Radius.circular(12),
                ),
              ),
              child: Row(
                children: const [
                  Expanded(
                      flex: 2,
                      child: Text("Date",
                          style: TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.bold))),
                  Expanded(
                      flex: 2,
                      child: Text("Time",
                          style: TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.bold))),
                  Expanded(
                      flex: 3,
                      child: Text("Camera",
                          style: TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.bold))),
                  Expanded(
                      flex: 2,
                      child: Text("Person Name",
                          style: TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.bold))),
                  Expanded(
                      flex: 2,
                      child: Text("Match Score",
                          style: TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.bold))),
                ],
              ),
            ),

            // ==== TABLE ROWS ====
            Expanded(
              child: ListView.builder(
                itemCount: logs.length,
                itemBuilder: (context, index) {
                  final log = logs[index];
                  return Container(
                    padding: const EdgeInsets.symmetric(
                        vertical: 12, horizontal: 8),
                    decoration: const BoxDecoration(
                      color: Color(0xFF283593),
                      border: Border(
                        bottom: BorderSide(color: Colors.white24, width: 0.5),
                      ),
                    ),
                    child: Row(
                      children: [
                        Expanded(
                            flex: 2,
                            child: Text(log["date"],
                                style: const TextStyle(
                                    color: Colors.white, fontSize: 14))),
                        Expanded(
                            flex: 2,
                            child: Text(log["time"],
                                style: const TextStyle(
                                    color: Colors.white, fontSize: 14))),
                        Expanded(
                            flex: 3,
                            child: Text(log["camera"],
                                style: const TextStyle(
                                    color: Colors.white, fontSize: 14))),
                        Expanded(
                            flex: 2,
                            child: Text(log["person"],
                                style: const TextStyle(
                                    color: Colors.white, fontSize: 14))),
                        Expanded(
                            flex: 2,
                            child: Text(log["score"].toStringAsFixed(2),
                                style: const TextStyle(
                                    color: Colors.white70, fontSize: 14))),
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
