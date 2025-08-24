export const summary = {
  missingNotFound: 6,
  missingFounded: 27,
  activeCameras: 18,
  totalCameras: 20,
  detectionsToday: 3,
  possibleMatches: 14,
  confirmedMissing: 25
}

export const cameras = [
  { id: 'CAM-001', location: 'Gate A', status: 'Active', last: 'Jul 29, 2025 – 14:03' },
  { id: 'CAM-002', location: 'Gate B', status: 'Active', last: 'Jul 29, 2025 – 14:02' },
  { id: 'CAM-003', location: 'Gate C', status: 'Offline', last: 'Jul 02, 2025 – 14:02' },
  { id: 'CAM-004', location: 'Gate D', status: 'Active', last: 'Jul 29, 2025 – 14:00' },
  { id: 'CAM-005', location: 'Gate A', status: 'Active', last: 'Jul 29, 2025 – 14:03' },
  { id: 'CAM-006', location: 'Gate B', status: 'Active', last: 'Jul 29, 2025 – 14:02' },
  { id: 'CAM-007', location: 'Gate C', status: 'Offline', last: 'Jul 02, 2025 – 14:02' }
]

export const logs = [
  { date: '2025-08-12', time: '12:48:43', camera: 'IP Camera Inside', person: 'unknown', score: 0.00 },
  { date: '2025-08-12', time: '12:52:07', camera: 'IP Camera Outside', person: 'unknown', score: 0.12 },
  { date: '2025-08-12', time: '12:57:25', camera: 'IP Camera Inside', person: 'Siti', score: 0.87 },
  { date: '2025-08-12', time: '12:59:11', camera: 'IP Camera Gate', person: 'unknown', score: 0.03 },
  { date: '2025-08-12', time: '13:02:18', camera: 'IP Camera Outside', person: 'Budi', score: 0.91 },
  { date: '2025-08-12', time: '13:05:46', camera: 'IP Camera Inside', person: 'unknown', score: 0.05 },
  { date: '2025-08-12', time: '13:11:32', camera: 'IP Camera Gate', person: 'unknown', score: 0.78 },
  { date: '2025-08-12', time: '13:16:57', camera: 'IP Camera Outside', person: 'Rudi', score: 0.95 }
]

export const missingPeople = [
  { time: '2025-08-12', name: 'Budy', result: 'Not yet found' },
  { time: '2025-08-12', name: 'Sity', result: 'Not yet found' },
  { time: '2025-08-12', name: 'Rudy', result: 'Founded' },
  { time: '2025-08-12', name: 'Dody', result: 'Founded' },
  { time: '2025-08-12', name: 'Andy', result: 'Not yet found' },
  { time: '2025-08-12', name: 'Dedy', result: 'Founded' },
  { time: '2025-08-12', name: 'Upin', result: 'Founded' }
]

export const feeds = [
  { id: 'CAM-001', src: 'https://images.unsplash.com/photo-1501706362039-c06b2d715385?q=80&w=1200&auto=format&fit=crop', live: true },
  { id: 'CAM-002', src: 'https://images.unsplash.com/photo-1532058459566-09f4ff5c732f?q=80&w=1200&auto=format&fit=crop', live: true },
  { id: 'CAM-003', src: 'https://images.unsplash.com/photo-1508057198894-247b23fe5ade?q=80&w=1200&auto=format&fit=crop', live: true },
  { id: 'CAM-004', src: 'https://images.unsplash.com/photo-1517999349371-c43520457b23?q=80&w=1200&auto=format&fit=crop', live: true }
]

// --- Settings dropdown options (optional) ---
export const settingsOptions = {
  deviceOptions: [
    { label: 'GPU', value: 'gpu' },
    { label: 'CPU', value: 'cpu' },
  ],
  detectorOptions: [
    { label: 'insightface', value: 'insightface' }
  ],
  antispoofBackendOptions: [
    { label: 'off', value: 'off' },
    { label: 'heuristic', value: 'heuristic' },
    { label: 'heuristic medium', value: 'heuristic_medium' },
    { label: 'minifasnet', value: 'minifasnet' },
  ],
  preprocessOptions: [
    { label: 'bgr_norm', value: 'bgr_norm' },
    { label: 'rgb_norm', value: 'rgb_norm' },
    { label: 'rgb01', value: 'rgb01' },
    { label: 'bgr01', value: 'bgr01' },
  ],
  antispoofModeOptions: [
    { label: 'high', value: 'high' },
    { label: 'medium', value: 'medium' },
    { label: 'low', value: 'low' },
  ],
  saveModeOptions: [
    { label: 'photo', value: 'photo' },
    { label: 'video 3s', value: 'video3s' },
  ],
  saveWhichOptions: [
    { label: 'green only', value: 'green' },
    { label: 'green and orange', value: 'all' },
  ],
}
