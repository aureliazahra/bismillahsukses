import 'package:flutter/material.dart';

class MissingPeoplePage extends StatefulWidget {
  const MissingPeoplePage({super.key});

  @override
  State<MissingPeoplePage> createState() => _MissingPeoplePageState();
}

class _MissingPeoplePageState extends State<MissingPeoplePage> {
  List<Map<String, String>> missingPeople = [
    {
      "reportedTime": "2025-08-12",
      "photo": "",
      "name": "Budy",
      "result": "Not yet found"
    },
    {
      "reportedTime": "2025-08-12",
      "photo": "",
      "name": "Sity",
      "result": "Npt yet founf"
    },
    {
      "reportedTime": "2025-08-12",
      "photo": "",
      "name": "RUdy",
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
      "name": "Dedy",
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
            // ==== HEADER BAR ====
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF3A8DFF), Color(0xFF2BC0E4)],
                  begin: Alignment.centerLeft,
                  end: Alignment.centerRight,
                ),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    "Missing People",
                    style: TextStyle(
                      fontSize: 26,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 5),
                  const Text(
                    "Manage missing people",
                    style: TextStyle(
                      fontSize: 16,
                      color: Colors.white70,
                    ),
                  ),
                  const SizedBox(height: 15),
                  // Tombol pill
                  Container(
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                        colors: [Color(0xFF1E3C72), Color(0xFF2A5298)],
                      ),
                      borderRadius: BorderRadius.circular(30),
                    ),
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.transparent,
                        shadowColor: Colors.transparent,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(30),
                        ),
                        padding: const EdgeInsets.symmetric(
                            horizontal: 24, vertical: 12),
                      ),
                      onPressed: () {},
                      child: const Text(
                        "Add New Missing Person",
                        style: TextStyle(fontSize: 14, color: Colors.white),
                      ),
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
                      child: Text("Reported Time",
                          style: TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.bold))),
                  Expanded(
                      flex: 1,
                      child: Text("Photo",
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
                      child: Text("Result",
                          style: TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.bold))),
                ],
              ),
            ),

            // ==== LIST DATA ====
            Expanded(
              child: ListView.builder(
                itemCount: missingPeople.length,
                itemBuilder: (context, index) {
                  final person = missingPeople[index];
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
                          child: Text(person["reportedTime"] ?? "",
                              style: const TextStyle(
                                  color: Colors.white, fontSize: 14)),
                        ),
                        Expanded(
                          flex: 1,
                          child: Container(
                            width: 35,
                            height: 35,
                            decoration: BoxDecoration(
                              color: Colors.white24,
                              borderRadius: BorderRadius.circular(6),
                            ),
                            child: person["photo"]!.isEmpty
                                ? const Icon(Icons.person,
                                    color: Colors.white70, size: 20)
                                : Image.network(person["photo"]!),
                          ),
                        ),
                        Expanded(
                          flex: 2,
                          child: Text(person["name"] ?? "",
                              style: const TextStyle(
                                  color: Colors.white, fontSize: 14)),
                        ),
                        Expanded(
                          flex: 2,
                          child: Text(person["result"] ?? "",
                              style: const TextStyle(
                                  color: Colors.white70, fontSize: 14)),
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
