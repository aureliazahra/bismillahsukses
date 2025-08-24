
// src/config/api.ts
const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";
const WS_BASE  = import.meta.env.VITE_WS_URL  || "ws://localhost:8000";

export const API = {
  base: API_BASE,
  wsBase: WS_BASE,
  health: `${API_BASE}/api/health`,
  getAppConfig: `${API_BASE}/api/config/app`,
  putAppConfig: `${API_BASE}/api/config/app`,
  cameras: `${API_BASE}/api/cameras`,
  cameraStart: (idx: number) => `${API_BASE}/api/cameras/${idx}/start`,
  cameraStop:  (idx: number) => `${API_BASE}/api/cameras/${idx}/stop`,
  cameraStatus: `${API_BASE}/api/cameras/status`,
  targets: `${API_BASE}/api/targets`,
  targetUpload: `${API_BASE}/api/targets/upload`,
  targetDelete: (name: string) => `${API_BASE}/api/targets/${encodeURIComponent(name)}`,
  mjpg: (idx: number) => `${API_BASE}/api/stream/mjpg/${idx}`,
  sse: `${API_BASE}/api/events`,
  // Missing Persons API
  missingPersons: `${API_BASE}/api/missing-persons`,
  missingPerson: (id: number) => `${API_BASE}/api/missing-persons/${id}`,
};
