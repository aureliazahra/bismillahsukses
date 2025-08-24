// src/config/api.js
export const API = {
  // Missing People
  missingPersons: '/api/missing',
  missingPerson: (id) => `/api/missing/${encodeURIComponent(id)}`,

  // Upload foto target (dipakai MissingPeople)
  targetUpload: '/api/targets/upload',

  // Opsional: dipakai halaman Logs / tombol view captures
  openCaptures: '/api/captures/open',
  logs: '/api/logs',
}
