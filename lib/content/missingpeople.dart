import 'package:flutter/material.dart';
import 'package:lolos/content/addnewmissingperson.dart';
import 'package:lolos/content/missing_person_dialog.dart'; // pastikan file ini ada

class MissingPeoplePage extends StatefulWidget {
  const MissingPeoplePage({super.key});

  @override
  State<MissingPeoplePage> createState() => _MissingPeoplePageState();
}

class _MissingPeoplePageState extends State<MissingPeoplePage> {
  List<Map<String, dynamic>> missingPeople = [
    {
      "reportedTime": "2025-08-12",
      "photo": "",
      "name": "Budy",
      "result": "Not yet found",
      "info": "Wearing red jacket last seen near mall"
    },
    {
      "reportedTime": "2025-08-12",
      "photo": "",
      "name": "Sity",
      "result": "Not yet found",
      "info": "Last seen at school"
    },
    {
      "reportedTime": "2025-08-12",
      "photo": "",
      "name": "Rudy",
      "result": "Founded",
      "info": "Found in nearby park"
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
            // ==== HEADER ====
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
                    style: TextStyle(fontSize: 16, color: Colors.white70),
                  ),
                  const SizedBox(height: 15),
                  Container(
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(30),
                      gradient: const LinearGradient(
                        colors: [Color(0xFF3A5BFF), Color(0xFF192BC2)],
                      ),
                    ),
                    child: ElevatedButton.icon(
                      onPressed: () {
                        showDialog(
                          context: context,
                          builder: (context) {
                            return AddMissingPersonDialog(
                              onPersonAdded: (data) {
                                setState(() {
                                  missingPeople.add(data);
                                });
                              },
                            );
                          },
                        );
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
                      icon: const Icon(Icons.add,
                          size: 18, color: Colors.white),
                      label: const Text(
                        "Add New Missing People",
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            // ==== TABLE HEADER ====
            Container(
              padding:
                  const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
              decoration: const BoxDecoration(
                color: Color(0xFF1A237E),
                borderRadius: BorderRadius.only(
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
                  return InkWell(
                    onTap: () {
                      showDialog(
                        context: context,
                        builder: (_) =>
                            MissingPersonDetailDialog(data: person),
                      );
                    },
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                          vertical: 12, horizontal: 8),
                      decoration: const BoxDecoration(
                        color: Color(0xFF283593),
                        border: Border(
                          bottom:
                              BorderSide(color: Colors.white24, width: 0.5),
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
                              child: (person["photo"] ?? "").isEmpty
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
