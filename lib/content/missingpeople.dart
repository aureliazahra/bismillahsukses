import 'package:flutter/material.dart';

class MissingPeoplePage extends StatefulWidget {
  const MissingPeoplePage({super.key});

  @override
  State<MissingPeoplePage> createState() => _MissingPeoplePageState();
}

class _MissingPeoplePageState extends State<MissingPeoplePage> {
  // Contoh data awal (nanti bisa diganti dari API/database)
  List<Map<String, String>> missingPeople = [
    {
      "reportedTime": "2025-08-12",
      "photo": "", // path atau URL foto
      "name": "Rudy",
      "result": "Not yet found"
    },
    {
      "reportedTime": "2025-08-12",
      "photo": "",
      "name": "Sity",
      "result": "Not yet found"
    },
    {
      "reportedTime": "2025-08-12",
      "photo": "",
      "name": "Rudy",
      "result": "Founded"
    },
    {
      "reportedTime": "2025-08-12",
      "photo": "",
      "name": "Dody",
      "result": "Founded"
    },
    {
      "reportedTime": "2025-08-12",
      "photo": "",
      "name": "Andy",
      "result": "Not yet found"
    },
    {
      "reportedTime": "2025-08-12",
      "photo": "",
      "name": "Dody",
      "result": "Founded"
    },
    {
      "reportedTime": "2025-08-12",
      "photo": "",
      "name": "Upin",
      "result": "Founded"
    },
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0B1220),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Search Bar & Notification Icon
            Row(
              children: [
                Expanded(
                  child: TextField(
                    decoration: InputDecoration(
                      filled: true,
                      fillColor: Colors.white10,
                      hintText: "Search",
                      hintStyle: const TextStyle(color: Colors.white54),
                      prefixIcon: const Icon(Icons.search, color: Colors.white54),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(15),
                        borderSide: BorderSide.none,
                      ),
                    ),
                    style: const TextStyle(color: Colors.white),
                  ),
                ),
                const SizedBox(width: 15),
                IconButton(
                  icon: const Icon(Icons.notifications, color: Colors.white),
                  onPressed: () {},
                ),
              ],
            ),
            const SizedBox(height: 20),

            // Title & Button
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  "Missing People",
                  style: TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
                ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.blueAccent,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(10),
                    ),
                  ),
                  onPressed: () {
                    // Tambah data baru
                  },
                  child: const Text("Add New Missing Person"),
                ),
              ],
            ),
            const SizedBox(height: 10),
            const Text(
              "Manage missing people",
              style: TextStyle(color: Colors.white54),
            ),
            const SizedBox(height: 20),

            // Table Header
            Container(
              padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 8),
              decoration: BoxDecoration(
                color: Colors.blue.shade900,
                borderRadius: BorderRadius.circular(10),
              ),
              child: Row(
                children: const [
                  Expanded(
                      flex: 2,
                      child: Text("Reported Time",
                          style: TextStyle(color: Colors.white))),
                  Expanded(
                      flex: 1,
                      child:
                          Text("Photo", style: TextStyle(color: Colors.white))),
                  Expanded(
                      flex: 2,
                      child: Text("Person Name",
                          style: TextStyle(color: Colors.white))),
                  Expanded(
                      flex: 2,
                      child:
                          Text("Result", style: TextStyle(color: Colors.white))),
                ],
              ),
            ),

            // List Data
            Expanded(
              child: ListView.builder(
                itemCount: missingPeople.length,
                itemBuilder: (context, index) {
                  final person = missingPeople[index];
                  return Container(
                    margin: const EdgeInsets.only(top: 5),
                    padding:
                        const EdgeInsets.symmetric(vertical: 10, horizontal: 8),
                    decoration: BoxDecoration(
                      color: Colors.blue.shade800,
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Row(
                      children: [
                        Expanded(
                          flex: 2,
                          child: Text(person["reportedTime"] ?? "",
                              style: const TextStyle(color: Colors.white)),
                        ),
                        Expanded(
                          flex: 1,
                          child: Container(
                            width: 40,
                            height: 40,
                            decoration: BoxDecoration(
                              color: Colors.white24,
                              borderRadius: BorderRadius.circular(5),
                            ),
                            child: person["photo"]!.isEmpty
                                ? const Icon(Icons.person,
                                    color: Colors.white70)
                                : Image.network(person["photo"]!),
                          ),
                        ),
                        Expanded(
                          flex: 2,
                          child: Text(person["name"] ?? "",
                              style: const TextStyle(color: Colors.white)),
                        ),
                        Expanded(
                          flex: 2,
                          child: Text(person["result"] ?? "",
                              style: const TextStyle(
                                  color: Colors.white, fontSize: 14)),
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
