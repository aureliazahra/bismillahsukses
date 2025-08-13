import 'package:flutter/material.dart';

class MissingPeoplePage extends StatelessWidget {
  const MissingPeoplePage({super.key});

  @override
  Widget build(BuildContext context) {
    // Data contoh
    final people = [
      ["2025-08-12", "Budy", "Not yet found"],
      ["2025-08-12", "Sity", "Not yet found"],
      ["2025-08-12", "Rudy", "Founded"],
      ["2025-08-12", "Dody", "Founded"],
      ["2025-08-12", "Andy", "Not yet found"],
      ["2025-08-12", "Dedy", "Founded"],
      ["2025-08-12", "Upin", "Founded"],
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
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    "Missing People",
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 26,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 5),
                  const Text(
                    "One Trace, One Hope.",
                    style: TextStyle(
                      color: Colors.white70,
                      fontSize: 14,
                    ),
                  ),
                  const SizedBox(height: 12),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                    decoration: BoxDecoration(
                      color: const Color(0xFF1E88E5),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: const Text(
                      "Add New Missing Person",
                      style: TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.w500),
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
                  Expanded(flex: 2, child: Text("Reported Time", style: TextStyle(color: Colors.white70, fontSize: 14, fontWeight: FontWeight.w500))),
                  SizedBox(width: 52), // lebar foto
                  Expanded(flex: 3, child: Text("Person Name", style: TextStyle(color: Colors.white70, fontSize: 14, fontWeight: FontWeight.w500))),
                  Expanded(flex: 3, child: Text("Result", style: TextStyle(color: Colors.white70, fontSize: 14, fontWeight: FontWeight.w500))),
                ],
              ),
            ),
            const SizedBox(height: 10),

            // Table Rows
            Expanded(
              child: ListView.builder(
                itemCount: people.length,
                itemBuilder: (context, index) {
                  final person = people[index];
                  return Container(
                    margin: const EdgeInsets.only(bottom: 8),
                    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
                    decoration: BoxDecoration(
                      color: const Color(0xFF1C1C3C).withOpacity(0.7),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Row(
                      children: [
                        Expanded(
                          flex: 2,
                          child: Text(
                            person[0],
                            style: const TextStyle(color: Colors.white, fontSize: 13),
                          ),
                        ),
                        Container(
                          width: 40,
                          height: 40,
                          decoration: BoxDecoration(
                            color: Colors.grey[400],
                            borderRadius: BorderRadius.circular(4),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          flex: 3,
                          child: Text(
                            person[1],
                            style: const TextStyle(color: Colors.white, fontSize: 13),
                          ),
                        ),
                        Expanded(
                          flex: 3,
                          child: Text(
                            person[2],
                            style: const TextStyle(color: Colors.white, fontSize: 13),
                          ),
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
    );
  }
}
