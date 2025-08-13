import 'package:flutter/material.dart';

class HistoryLogsPage extends StatelessWidget {
  const HistoryLogsPage({super.key});

  @override
  Widget build(BuildContext context) {
    // Sample data logs (seperti gambar)
    final logs = [
      ["2025-08-12", "12:48:43", "IP Camera Inside", "unknown", 0.00],
      ["2025-08-12", "12:52:07", "IP Camera Outside", "unknown", 0.12],
      ["2025-08-12", "12:57:25", "IP Camera Inside", "Siti", 0.87],
      ["2025-08-12", "12:59:11", "IP Camera Gate", "unknown", 0.03],
      ["2025-08-12", "13:02:18", "IP Camera Outside", "Budi", 0.91],
      ["2025-08-12", "13:05:46", "IP Camera Inside", "unknown", 0.05],
      ["2025-08-12", "13:11:32", "IP Camera Gate", "unknown", 0.78],
      ["2025-08-12", "13:16:57", "IP Camera Outside", "Rudi", 0.95],
    ];

    return Scaffold(
      backgroundColor: const Color(0xFF0B1220),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF4AB1EB), Color(0xFF2D6AA6)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    "Founded Logs",
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 26,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  SizedBox(height: 5),
                  Text(
                    "Detected missing people on available cameras will automatically recorded as logs here",
                    style: TextStyle(
                      color: Colors.white70,
                      fontSize: 14,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 30),

            // Table Header
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
              decoration: BoxDecoration(
                color: const Color(0xFF1C1C3C),
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Row(
                children: [
                  Expanded(flex: 2, child: Text("Date", style: TextStyle(color: Colors.white70, fontSize: 14, fontWeight: FontWeight.w500))),
                  Expanded(flex: 2, child: Text("Time", style: TextStyle(color: Colors.white70, fontSize: 14, fontWeight: FontWeight.w500))),
                  Expanded(flex: 3, child: Text("Camera", style: TextStyle(color: Colors.white70, fontSize: 14, fontWeight: FontWeight.w500))),
                  Expanded(flex: 3, child: Text("Person Name", style: TextStyle(color: Colors.white70, fontSize: 14, fontWeight: FontWeight.w500))),
                  Expanded(flex: 2, child: Text("Match Score", style: TextStyle(color: Colors.white70, fontSize: 14, fontWeight: FontWeight.w500))),
                ],
              ),
            ),
            const SizedBox(height: 10),

            // Table Rows
            Expanded(
              child: ListView.builder(
                itemCount: logs.length,
                itemBuilder: (context, index) {
                  final log = logs[index];
                  return Container(
                    margin: const EdgeInsets.only(bottom: 8),
                    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
                    decoration: BoxDecoration(
                      color: const Color(0xFF1C1C3C).withOpacity(0.7),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Row(
                      children: [
                        Expanded(flex: 2, child: Text(log[0].toString(), style: const TextStyle(color: Colors.white, fontSize: 13))),
                        Expanded(flex: 2, child: Text(log[1].toString(), style: const TextStyle(color: Colors.white, fontSize: 13))),
                        Expanded(flex: 3, child: Text(log[2].toString(), style: const TextStyle(color: Colors.white, fontSize: 13))),
                        Expanded(flex: 3, child: Text(log[3].toString(), style: const TextStyle(color: Colors.white, fontSize: 13))),
                        Expanded(flex: 2, child: Text((log[4] as double).toStringAsFixed(2), style: const TextStyle(color: Colors.white, fontSize: 13))),
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
