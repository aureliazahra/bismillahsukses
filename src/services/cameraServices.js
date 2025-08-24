// src/services/camerasService.js
const API = '/api/cameras/manage';

async function asJson(res) {
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(text || `HTTP ${res.status}`)
  }
  return res.status === 204 ? null : res.json()
}

export const camerasService = {
  async list() {
    const res = await fetch(API);
    return asJson(res);
  },
  async create(data) {
    const res = await fetch(API, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return asJson(res);
  },
  async update(id, data) {
    const res = await fetch(`${API}/${encodeURIComponent(id)}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return asJson(res);
  },
  async remove(id) {
    const res = await fetch(`${API}/${encodeURIComponent(id)}`, { method: 'DELETE' });
    return asJson(res);
  },
  async testSource(source) {
    const res = await fetch(`${API}/test`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source }),
    });
    return asJson(res);
  },
  async start(id) {
    const res = await fetch(`${API}/${encodeURIComponent(id)}/start`, { method: 'POST' });
    return asJson(res);
  },
  async stop(id) {
    const res = await fetch(`${API}/${encodeURIComponent(id)}/stop`, { method: 'POST' });
    return asJson(res);
  },
};
