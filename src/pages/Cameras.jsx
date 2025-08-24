import React, { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createPortal } from 'react-dom'
import HeaderCard from '../components/ui/HeaderCard.jsx'
import TabPill from '../components/ui/TabPill.jsx'

// === API helpers (tanpa .env, pakai proxy Vite ke /api) ===
const API_BASE = '' // biarkan kosong; gunakan path relatif
const asJson = async (res) => {
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(text || `HTTP ${res.status}`)
  }
  return res.status === 204 ? null : res.json()
}
const api = {
  list: () => fetch(`${API_BASE}/api/cameras/manage`).then(asJson),
  create: (body) =>
    fetch(`${API_BASE}/api/cameras/manage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }).then(asJson),
  update: (id, body) =>
    fetch(`${API_BASE}/api/cameras/manage/${encodeURIComponent(id)}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }).then(asJson),
  remove: (id) =>
    fetch(`${API_BASE}/api/cameras/manage/${encodeURIComponent(id)}`, {
      method: 'DELETE',
    }).then(asJson),
  start: (id) =>
    fetch(`${API_BASE}/api/cameras/manage/${encodeURIComponent(id)}/start`, {
      method: 'POST',
    }).then(asJson),
  stop: (id) =>
    fetch(`${API_BASE}/api/cameras/manage/${encodeURIComponent(id)}/stop`, {
      method: 'POST',
    }).then(asJson),
}

export default function Cameras() {
  // data list (ambil dari backend)
  const [list, setList] = useState([])

  /* ----------------------------- STATE --------------------------------- */
  const [tab, setTab] = useState('all')

  const cams = list.filter((c) => {
    if (tab === 'active') return (c.status || '').toLowerCase() === 'active'
    if (tab === 'offline') return (c.status || '').toLowerCase() === 'offline'
    return true
  })

  /* popup state */
  const [popup, setPopup] = useState({
    visible: false,
    x: 0,
    y: 0,
    camera: null,
    anchorBL: false,
  })

  /* which action was clicked (edit/delete) */
  const [actionType, setActionType] = useState(null)

  /* EDIT form state */
  const [editForm, setEditForm] = useState({ location: '', source: '' })

  /* ADD NEW CAMERA modal state */
  const [showAdd, setShowAdd] = useState(false)
  const [addForm, setAddForm] = useState({
    id: '',
    location: '',
    source: '',
    active: true,
    notes: '',
  })

  const navigate = useNavigate()

  // muat data dari backend
  const reload = async () => {
    try {
      const data = await api.list()
      setList(Array.isArray(data) ? data : [])
    } catch (e) {
      console.error('Gagal memuat kamera:', e)
      setList([])
    }
  }

  useEffect(() => {
    reload()
  }, [])

  /* ------------------------- ACTIONS ----------------------------------- */
  const showPopup = (e, camera) => {
    e.preventDefault()
    e.stopPropagation()

    const { clientX: cx, clientY: cy } = e
    const { innerWidth: vw, innerHeight: vh } = window

    const POPUP_WIDTH = 240
    const POPUP_HEIGHT = 240

    let x = cx
    let y = cy
    let anchorBL = false

    if (cx + 12 + POPUP_WIDTH > vw - 8) {
      x = cx - POPUP_WIDTH
      if (x < 8) x = 8
    } else {
      if (x < 8) x = 8
    }
    if (cy + 12 + POPUP_HEIGHT > vh - 8) {
      y = cy - POPUP_HEIGHT
      anchorBL = true
      if (y < 8) y = 8
    } else {
      if (y < 8) y = 8
    }

    setPopup({ visible: true, x, y, camera, anchorBL })
    setActionType(null)
  }

  const handleAction = async (action) => {
    if (!popup.camera) return

    if (action === 'delete') {
      setActionType('delete')
      return
    }

    if (action === 'edit') {
      setEditForm({ location: popup.camera.location || '', source: String(popup.camera.source ?? '') })
      setActionType('edit')
      return
    }

    if (action === 'preview') {
      navigate('/realtime')
      return
    }

    if (action === 'refresh') {
      setPopup((p) => ({ ...p, visible: false }))
      reload()
      return
    }

    // 'edit' atau 'delete' → buka modal sekunder
    setActionType(action)
    setPopup((p) => ({ ...p, visible: false }))
  }

  const confirmDelete = async () => {
    if (!popup.camera) return
    try {
      await api.remove(popup.camera.id)
      setList((prev) => prev.filter((x) => x.id !== popup.camera.id))
      setActionType(null)
    } catch (e) {
      console.error(e)
      alert('Gagal menghapus kamera')
    }
  }

  const applyEdit = async () => {
    if (!popup.camera) return
    try {
      const body = {}
      if (editForm.location.trim()) body.location = editForm.location.trim()
      if (editForm.source.trim()) {
        body.source = /^\d+$/.test(editForm.source.trim())
          ? parseInt(editForm.source.trim(), 10)
          : editForm.source.trim()
      }
      const row = await api.update(popup.camera.id, body)
      setList((prev) => prev.map((x) => (x.id === popup.camera.id ? { ...x, ...row } : x)))
      setActionType(null)
    } catch (e) {
      console.error(e)
      alert('Gagal menyimpan perubahan')
    }
  }

  const handleStart = async () => {
    if (!popup.camera) return
    try {
      await api.update(popup.camera.id, { active: true }) // wajib aktif lebih dulu
      await api.start(popup.camera.id)
      navigate('/realtime')
    } catch (e) {
      console.error(e)
      alert('Start gagal. Pastikan kamera Active dan sumber RTSP/ID benar.')
    }
  }

  const handleStop = async () => {
    if (!popup.camera) return
    try {
      await api.stop(popup.camera.id)
      await reload()
    } catch (e) {
      console.error(e)
    }
  }

  // === NEW: toggle start/stop langsung dari tabel ===
  const toggleCam = async (cam) => {
    if (!cam || !cam.id) return;
    try {
      if (String(cam.status).toLowerCase() === 'active') {
        await api.stop(cam.id);
      } else {
        await api.update(cam.id, { active: true });
        await api.start(cam.id);
      }
    } catch (e) {
      console.error(e);
      alert('Gagal mengubah status kamera.');
    } finally {
      reload();
    }
  }

  /* ------------------------ ADD NEW CAMERA ------------------------------ */
  const openAdd = () => setShowAdd(true)
  const closeAdd = () => setShowAdd(false)

  const onAddChange = (e) => {
    const { name, value } = e.target
    setAddForm((prev) => ({ ...prev, [name]: value }))
  }
  const toggleActive = () => setAddForm((prev) => ({ ...prev, active: !prev.active }))

  const submitAdd = async () => {
    const id = addForm.id?.trim() || `CAM-${Date.now()}`
    const payload = {
      id,
      location: addForm.location?.trim() || `Camera ${id}`,
      source: /^\d+$/.test(addForm.source.trim())
        ? parseInt(addForm.source.trim(), 10)
        : addForm.source.trim(),
      active: !!addForm.active, // backend tetap memaksa inactive saat create
      notes: addForm.notes || '',
    }

    try {
      await api.create(payload)
      setShowAdd(false)
      setAddForm({ id: '', location: '', source: '', active: true, notes: '' })
      reload()
    } catch (e) {
      console.error(e)
      alert('Gagal menambahkan kamera')
    }
  }

  /* ----------------------------- RENDER -------------------------------- */
  return (
    <div className="cameras-page">
      <HeaderCard
        title="Cameras"
        subtitle="Manage your cameras"
        right={
          <div className="cam-cta-wrap">
            <button className="btn btn-figma cam-cta" onClick={openAdd}>
              <span className="cam-cta__icon" aria-hidden="true">
                <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                  <path d="M17.5 7 15.8 5H9L7.5 7H4a3 3 0 0 0-3 3v6a3 3 0 0 0 3 3h2.5l1.5 2H15l1.5-2H19a3 3 0 0 0 3-3v-6a3 3 0 0 0-3-3h-2.5ZM12 17a4 4 0 1 1 0-8 4 4 0 0 1 0 8Z" />
                </svg>
              </span>
              <span>Add New Camera</span>
            </button>
          </div>
        }
      />

      {/* Tabs */}
      <div className="cam-tabs">
        <TabPill
          value={tab}
          onChange={setTab}
          options={[
            { value: 'all', label: 'All' },
            { value: 'active', label: 'Active' },
            { value: 'offline', label: 'Offline' },
          ]}
        />
      </div>

      {/* Table */}
      <div className="table-wrap cam-table-wrap">
        <table className="table cam-table">
          <thead>
            <tr>
              <th style={{ width: 160 }}>ID</th>
              <th style={{ width: 120 }}>Action</th>{/* NEW */}
              <th>Location</th>
              <th>Status</th>
              <th style={{ width: 260 }}>Last Updated</th>
            </tr>
          </thead>
          <tbody>
            {cams.map((c) => (
              <tr key={c.id} style={{ cursor: 'context-menu' }} onContextMenu={(e) => showPopup(e, c)}>
                <td>{c.id}</td>
                <td>
                  <button className="cam-btn cam-btn--secondary" onClick={() => toggleCam(c)}>
                    {String(c.status).toLowerCase() === 'active' ? 'Stop' : 'Start'}
                  </button>
                </td>
                <td>{c.location}</td>
                <td>
                  <span className={c.status === 'Active' ? 'cam-status-active' : 'cam-status-offline'}>
                    {c.status}
                  </span>
                </td>
                <td>{c.last}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Smart Pop-up (context menu) — TANPA blur background */}
      {popup.visible && (
        <div
          role="menu"
          className={`cam-menu${popup.anchorBL ? ' is-anchor-bl' : ''}`}
          style={{ top: popup.y, left: popup.x, position: 'fixed' }}
          onClick={(e) => e.stopPropagation()}
        >
          {menuItems.map((item) => (
            <button
              key={item.key}
              role="menuitem"
              onClick={() => handleAction(item.key)}
              className={`cam-menu__item${item.danger ? ' is-danger' : ''}`}
            >
              <span aria-hidden="true" className="cam-menu__icon">
                {item.icon({})}
              </span>
              <span className="cam-menu__label">{item.label}</span>
            </button>
          ))}
        </div>
      )}

      {/* Modal Add */}
      {showAdd &&
        createPortal(
          <div className="cam-modal" role="dialog" aria-modal="true" onClick={closeAdd}>
            <div className="cam-modal__sheet" onClick={(e) => e.stopPropagation()}>
              <h3 className="cam-modal__title">Add Camera</h3>
              <div className="cam-grid">
                <Field label="Camera ID">
                  <input type="text" name="id" value={addForm.id} onChange={onAddChange} className="cam-input" placeholder="Kamera CCTV 1" />
                </Field>

                <Field label="Location">
                  <input type="text" name="location" value={addForm.location} onChange={onAddChange} className="cam-input" placeholder="Ruang parkir belakang" />
                </Field>

                <Field label="Source">
                  <input
                    type="text"
                    name="source"
                    value={addForm.source}
                    onChange={onAddChange}
                    className="cam-input"
                    placeholder="0 atau rtsp://192.168.1.11:554/stream200"
                  />
                </Field>

                <Field label="Active">
                  <label className="toggle" onClick={(e) => e.stopPropagation()}>
                    <input type="checkbox" checked={!!addForm.active} onChange={toggleActive} />
                    <span className="switch" />
                  </label>
                </Field>

                <Field label="Notes">
                  <textarea name="notes" value={addForm.notes} onChange={onAddChange} className="cam-input" placeholder="Catatan opsional..." />
                </Field>
              </div>

              <div className="cam-actions">
                <button className="cam-btn cam-btn--primary" onClick={submitAdd}>
                  Save
                </button>
                <button className="cam-btn cam-btn--secondary" onClick={closeAdd}>
                  Cancel
                </button>
              </div>
            </div>
          </div>,
          document.body
        )}

      {/* Modal Delete */}
      {actionType === 'delete' &&
        createPortal(
          <div className="cam-modal" role="dialog" aria-modal="true" onClick={() => setActionType(null)}>
            <div className="cam-modal__sheet" onClick={(e) => e.stopPropagation()}>
              <h3 className="cam-modal__title">Delete Camera</h3>
              <p>Yakin ingin menghapus kamera <b>{popup.camera?.id}</b>?</p>
              <div className="cam-actions">
                <button className="cam-btn cam-btn--danger" onClick={confirmDelete}>Delete</button>
                <button className="cam-btn cam-btn--secondary" onClick={() => setActionType(null)}>Cancel</button>
              </div>
            </div>
          </div>,
          document.body
        )}

      {/* Modal Edit */}
      {actionType === 'edit' &&
        createPortal(
          <div className="cam-modal" role="dialog" aria-modal="true" onClick={() => setActionType(null)}>
            <div className="cam-modal__sheet" onClick={(e) => e.stopPropagation()}>
              <h3 className="cam-modal__title">Edit Camera</h3>

              <div className="cam-grid">
                <Field label="Location">
                  <input
                    type="text"
                    value={editForm.location}
                    onChange={(e) => setEditForm((f) => ({ ...f, location: e.target.value }))}
                    placeholder="Lobby depan"
                    className="cam-input"
                  />
                </Field>

                <Field label="Source">
                  <input
                    type="text"
                    value={editForm.source}
                    onChange={(e) => setEditForm((f) => ({ ...f, source: e.target.value }))}
                    placeholder="0 atau rtsp://..."
                    className="cam-input"
                  />
                </Field>

                {/* Field lainnya tetap visual */}
                <Field label="Display refresh (ms)">
                  <DSNumber defaultValue={50} step={1} min={0} />
                </Field>
                <Field label="Detect every N frames">
                  <DSNumber defaultValue={3} step={1} min={1} />
                </Field>
                <Field label="Reconnect delay (s)">
                  <DSNumber defaultValue={10} step={1} min={0} />
                </Field>
                <Field label="Auto set Active on Start">
                  <label className="toggle" onClick={(e) => e.stopPropagation()}>
                    <input type="checkbox" defaultChecked />
                    <span className="switch" />
                  </label>
                </Field>
                <Field label="Exposure gain">
                  <DSNumber defaultValue={1.4} step={0.01} min={0} />
                </Field>
                <Field label="Min luminance">
                  <DSNumber defaultValue={55} step={1} min={0} />
                </Field>
              </div>

              <div className="cam-actions">
                <button className="cam-btn cam-btn--primary" onClick={applyEdit}>
                  Apply Changes
                </button>
                <button className="cam-btn cam-btn--secondary" onClick={handleStart}>
                  Start
                </button>
                <button className="cam-btn cam-btn--secondary" onClick={handleStop}>
                  Stop
                </button>
                <button className="cam-btn cam-btn--secondary" onClick={() => setActionType(null)}>
                  Close
                </button>
              </div>
            </div>
          </div>,
          document.body
        )}
    </div>
  )
}

/* util kecil untuk membulatkan ke step (agar 0.1 + 0.2 aman) */
function roundToStep(value, step) {
  const dec = (String(step).split('.')[1] || '').length
  const pow = Math.pow(10, dec)
  return Math.round(value * pow) / pow
}

/* ------ helper kecil untuk label + input ----- */
function Field({ label, children }) {
  return (
    <div className="cam-field">
      <span className="cam-label">{label}</span>
      {children}
    </div>
  )
}

/* ------ DSNumber kecil, mengikuti tampilan Settings ----- */
function DSNumber({ defaultValue = 0, step = 1, min = -Infinity, max = Infinity, onChange }) {
  const [val, setVal] = useState(() => {
    const num = typeof defaultValue === 'number' ? defaultValue : parseFloat(defaultValue)
    return Number.isFinite(num) ? String(num) : '0'
  })

  const clamp = (n) => Math.min(Math.max(n, min), max)

  const set = (v) => {
    const num = clamp(parseFloat(v))
    const fixed = Number.isFinite(num) ? roundToStep(num, step) : 0
    setVal(String(fixed))
    onChange?.(fixed)
  }

  const inc = () => set((parseFloat(val) || 0) + step)
  const dec = () => set((parseFloat(val) || 0) - step)

  return (
    <div className="dsnumber">
      <button type="button" className="dsnumber__btn" onClick={dec} aria-label="decrease">−</button>
      <input
        type="number"
        className="dsnumber__input"
        step={step}
        min={Number.isFinite(min) ? min : undefined}
        max={Number.isFinite(max) ? max : undefined}
        value={val}
        onChange={(e) => set(e.target.value)}
      />
      <button type="button" className="dsnumber__btn" onClick={inc} aria-label="increase">+</button>
    </div>
  )
}

/* ---------------------- Ikon kecil ------------------------------------ */
const Icon = {
  edit: (props) => (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor" {...props}>
      <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25Zm17.71-10.46a1.004 1.004 0 0 0 0-1.42l-2.34-2.34a1.004 1.004 0 0 0-1.42 0l-1.83 1.83 3.75 3.75 1.84-1.82Z" />
    </svg>
  ),
  preview: (props) => (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor" {...props}>
      <path d="M12 5c-7.633 0-10 7-10 7s2.367 7 10 7 10-7 10-7-2.367-7-10-7Zm0 12a5 5 0 1 1 0-10 5 5 0 0 1 0 10Z" />
    </svg>
  ),
  refresh: (props) => (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor" {...props}>
      <path d="M17.65 6.35A7.95 7.95 0 0 0 12 4V1L7 6l5 5V7c3.31 0 6 2.69 6 6a6 6 0 0 1-6 6 6 6 0 0 1-5.65-3.65" />
    </svg>
  ),
  delete: (props) => (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor" {...props}>
      <path d="M6 7h12l-1 14H7L6 7Zm2-3h8l1 2H7l1-2Z" />
    </svg>
  ),
}

const menuItems = [
  { key: 'edit', label: 'Edit', danger: false, icon: Icon.edit },
  { key: 'preview', label: 'Live Preview', danger: false, icon: Icon.preview },
  { key: 'refresh', label: 'Refresh', danger: false, icon: Icon.refresh },
  { key: 'delete', label: 'Delete', danger: false, icon: Icon.delete },
]
