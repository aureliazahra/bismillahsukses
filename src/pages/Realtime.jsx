import React, { useEffect, useRef, useState, useCallback } from 'react'
import LiveTile from '../components/ui/LiveTile.jsx'

const API_BASE = (import.meta.env.VITE_API_URL || '').replace(/\/+$/, '')

// ====== Kebijakan koneksi agar halaman tidak "hilang" ======
// 1) Pool koneksi global (batasi stream simultan per origin)
// 2) Lazy stream hanya untuk tile yang terlihat (IntersectionObserver)
// 3) Ramp-up: mulai dari 1 stream, bertahap naik → kurangi "spike" beban network/renderer
const MAX_STREAMS = 4         // batas atas koneksi MJPEG simultan
const RAMP_STEP_MS = 1500     // jeda kenaikan slot
const STREAM_REFRESH_MS = 25000
const POLL_MS = 4000

export default function Realtime() {
  const [feeds, setFeeds] = useState([])
  const [error, setError] = useState('')
  const [fsIdx, setFsIdx] = useState(null)

  const pollRef = useRef(null)
  const mountedRef = useRef(false)
  const tileRefs = useRef(new Map())

  // Set indeks terlihat (viewport)
  const visibleSetRef = useRef(new Set())
  // Set indeks yang dialokasikan koneksi (aktif)
  const enabledSetRef = useRef(new Set())

  // Ramp-up slot koneksi
  const allowedStreamsRef = useRef(1)
  const rampTimerRef = useRef(null)

  const streamUrl = (idx, nonce) => `${API_BASE}/api/realtime/${idx}/stream?${nonce}`

  // ---------- Fullscreen helpers ----------
  const fsElement = () =>
    document.fullscreenElement || document.webkitFullscreenElement || document.msFullscreenElement || null

  const requestFs = (el) => {
    if (!el) return
    if (el.requestFullscreen) return el.requestFullscreen()
    if (el.webkitRequestFullscreen) return el.webkitRequestFullscreen()
    if (el.msRequestFullscreen) return el.msRequestFullscreen()
  }

  const exitFs = () => {
    if (document.exitFullscreen) return document.exitFullscreen()
    if (document.webkitExitFullscreen) return document.webkitExitFullscreen()
    if (document.msExitFullscreen) return document.msExitFullscreen()
  }

  const toggleFullscreen = (el) => {
    const cur = fsElement()
    if (cur && (cur === el || el.contains(cur))) {
      exitFs()
      return
    }
    requestFs(el)
  }

  const setTileRefForIndex = useCallback((idx, el) => {
    if (el) tileRefs.current.set(idx, el)
    else tileRefs.current.delete(idx)
  }, [])

  useEffect(() => {
    const handler = () => {
      const cur = fsElement()
      if (!cur) { setFsIdx(null); return }
      let found = null
      tileRefs.current.forEach((el, idx) => {
        if (el === cur || el.contains(cur)) found = idx
      })
      setFsIdx(found)
    }
    document.addEventListener('fullscreenchange', handler)
    document.addEventListener('webkitfullscreenchange', handler)
    document.addEventListener('MSFullscreenChange', handler)
    return () => {
      document.removeEventListener('fullscreenchange', handler)
      document.removeEventListener('webkitfullscreenchange', handler)
      document.removeEventListener('MSFullscreenChange', handler)
    }
  }, [])

  // ---------- IntersectionObserver: tandai tile yang terlihat ----------
  const ioRef = useRef(null)
  useEffect(() => {
    if (typeof window !== 'undefined' && 'IntersectionObserver' in window) {
      ioRef.current = new IntersectionObserver((entries) => {
        let changed = false
        entries.forEach((e) => {
          const idx = Number(e.target?.dataset?.idx ?? -1)
          if (idx < 0) return
          if (e.isIntersecting) {
            if (!visibleSetRef.current.has(idx)) {
              visibleSetRef.current.add(idx)
              changed = true
            }
          } else {
            if (visibleSetRef.current.delete(idx)) changed = true
          }
        })
        if (changed) reallocateStreams()
      }, { root: null, rootMargin: '128px', threshold: 0.01 })
    }
    return () => {
      try { ioRef.current?.disconnect() } catch {}
      ioRef.current = null
      visibleSetRef.current.clear()
    }
  }, [])

  const observeTiles = useCallback(() => {
    try {
      if (!ioRef.current) return
      ioRef.current.disconnect()
      tileRefs.current.forEach((el, idx) => {
        if (!el) return
        el.dataset.idx = String(idx)
        ioRef.current.observe(el)
      })
    } catch {}
  }, [])

  // ---------- Merge data cameras ----------
  const mergeFeeds = (incoming) => {
    const now = Date.now()
    setFeeds((prev) => {
      const prevMap = new Map(prev.map((f) => [f.index, f]))
      const out = (incoming || []).map((c) => {
        const idx = Number(c.index ?? 0)
        const name = String(c.name || `Camera ${idx + 1}`)
        const active = !!c.active
        const running = !!c.running
        const old = prevMap.get(idx) || {}

        const falseCount = running ? 0 : Math.min((old.falseCount || 0) + 1, 10)
        const stableRunning = running || (old.stableRunning && falseCount < 2)

        let lastSrcAt = old.lastSrcAt || 0
        let nonce = old.nonce || `v=${now}`
        let src = old.src || ''
        let version = old.version || 0

        if (old.src && (now - lastSrcAt > STREAM_REFRESH_MS)) {
          nonce = `v=${now}`
          lastSrcAt = now
        }

        const title = `${name} ${stableRunning ? '[Live]' : '[Not Active]'}`
        return {
          key: `cam-${idx}`,
          index: idx,
          name,
          active,
          running,
          stableRunning,
          falseCount,
          title,
          src,
          lastSrcAt,
          nonce,
          version,
        }
      })
      return out
    })
  }

  const loadFeeds = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/realtime/cameras`, { cache: 'no-store' })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const cams = await res.json()
      if (!mountedRef.current) return
      mergeFeeds(cams || [])
    } catch (e) {
      console.error(e)
      if (!mountedRef.current) return
      setError('Gagal memuat kamera')
    }
  }

  // ---------- Allocator: aktif/nonaktif stream sesuai viewport + pool + ramp-up ----------
  const reallocateStreams = useCallback(() => {
    if (!mountedRef.current) return
    const poolLimit = Math.min(allowedStreamsRef.current, MAX_STREAMS)

    setFeeds((prev) => {
      const now = Date.now()
      const visible = Array.from(visibleSetRef.current).sort((a, b) => a - b)

      const newEnabled = new Set()
      for (let i = 0; i < visible.length && newEnabled.size < poolLimit; i++) {
        newEnabled.add(visible[i])
      }
      enabledSetRef.current = newEnabled

      let changed = false
      const next = prev.map((f) => {
        const shouldEnable = f.active && f.stableRunning && newEnabled.has(f.index)
        if (shouldEnable) {
          if (!f.src) {
            const nonce = `v=${now}`
            changed = true
            return { ...f, src: streamUrl(f.index, nonce), nonce, lastSrcAt: now }
          }
          return f
        }
        if (f.src) {
          changed = true
          return { ...f, src: '', lastSrcAt: 0, version: (f.version || 0) + 1 }
        }
        return f
      })
      return changed ? next : prev
    })
  }, [])

  // Ramp-up slot koneksi (1 → MAX_STREAMS)
  const startRampUp = useCallback(() => {
    allowedStreamsRef.current = 1
    if (rampTimerRef.current) clearInterval(rampTimerRef.current)
    rampTimerRef.current = setInterval(() => {
      if (allowedStreamsRef.current >= MAX_STREAMS) {
        clearInterval(rampTimerRef.current)
        rampTimerRef.current = null
        return
      }
      allowedStreamsRef.current += 1
      reallocateStreams()
    }, RAMP_STEP_MS)
  }, [reallocateStreams])

  // ---------- Lifecycle ----------
  useEffect(() => {
    mountedRef.current = true
    startRampUp()
    loadFeeds()
    pollRef.current = setInterval(loadFeeds, POLL_MS)
    return () => {
      mountedRef.current = false
      if (pollRef.current) clearInterval(pollRef.current)
      if (rampTimerRef.current) clearInterval(rampTimerRef.current)
      // Putus semua stream (paksa unmount)
      setFeeds((prev) => prev.map((f) => ({
        ...f, src: '', lastSrcAt: 0, stableRunning: false, version: (f.version || 0) + 1,
      })))
      try { exitFs() } catch {}
      try { ioRef.current?.disconnect() } catch {}
      visibleSetRef.current.clear()
      enabledSetRef.current.clear()
      tileRefs.current.clear()
      allowedStreamsRef.current = 1
    }
  }, [startRampUp])

  // Saat jumlah tile berubah → pasang observer + alokasikan ulang
  useEffect(() => {
    if (!mountedRef.current) return
    observeTiles()
    reallocateStreams()
  }, [feeds.length, observeTiles, reallocateStreams])

  // Tick kecil untuk memastikan reallocator jalan walau tidak ada perubahan lain
  useEffect(() => {
    const t = setInterval(() => reallocateStreams(), 3000)
    return () => clearInterval(t)
  }, [reallocateStreams])

  // ---------- BUTTONS ----------
  const startAll = async () => {
    try {
      // reset ramp-up agar pembukaan stream bertahap
      allowedStreamsRef.current = 1
      if (rampTimerRef.current) clearInterval(rampTimerRef.current)
      startRampUp()

      await fetch(`${API_BASE}/api/realtime/start-all`, { method: 'POST' })
    } catch (e) {
      console.error(e)
    } finally {
      await loadFeeds()
      reallocateStreams()
    }
  }

  const stopAll = async () => {
    try {
      const r = await fetch(`${API_BASE}/api/realtime/stop-all`, { method: 'POST' })
      if (!r.ok) {
        const res = await fetch(`${API_BASE}/api/cameras/manage`, { cache: 'no-store' })
        if (res.ok) {
          const list = await res.json()
          await Promise.all(
            (list || []).map((c) =>
              fetch(`${API_BASE}/api/cameras/manage/${encodeURIComponent(c.id)}/stop`, { method: 'POST' })
                .catch(() => null)
            )
          )
        }
      }
    } catch (e) {
      console.error(e)
    } finally {
      setFeeds((prev) => prev.map((f) => ({
        ...f, src: '', lastSrcAt: 0, stableRunning: false, version: (f.version || 0) + 1,
      })))
      visibleSetRef.current.clear()
      enabledSetRef.current.clear()
      allowedStreamsRef.current = 1
      await loadFeeds()
    }
  }

  const onTileClick = () => {}
  const onTileDoubleClick = (feed) => {
    if (!feed.stableRunning) return
    const el = tileRefs.current.get(feed.index)
    if (el) toggleFullscreen(el)
  }

  const Header = (
    <div className="realtime-header">
      <div className="realtime-header-main">
        <span className="realtime-title">
          Face Detection
        </span>
        <span className="realtime-subtitle">
          Available cameras with real-time face detection
        </span>
        <div className="realtime-actions">
          <button className="logs-cta" type="button" onClick={startAll}>
            <span className="logs-cta__icon">
              <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
                <path d="M8 5v14l11-7-11-7z" fill="currentColor" />
              </svg>
            </span>
            <span className="logs-cta__label">Start All Cameras</span>
          </button>
          <button className="logs-cta" type="button" onClick={stopAll}>
            <span className="logs-cta__icon">
              <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
                <rect x="6" y="6" width="12" height="12" rx="2" fill="currentColor" />
              </svg>
            </span>
            <span className="logs-cta__label">Stop All Cameras</span>
          </button>
        </div>
      </div>
    </div>
  )

  if (error) {
    return (
      <div className="realtime-page">
        {Header}
        <div style={{ padding: 16, color: 'red' }}>{error}</div>
      </div>
    )
  }

  return (
    <div className="realtime-page">
      {Header}

      <div className="realtime-grid">
        {feeds.map((f) => {
          const isFS = fsIdx === f.index
          return (
            <div
              key={f.key}
              ref={(el) => setTileRefForIndex(f.index, el)}
              onClick={() => onTileClick(f)}
              onDoubleClick={() => onTileDoubleClick(f)}
              title={f.title}
              data-idx={f.index}
              style={{
                position: 'relative',
                ...(isFS ? {
                  display: 'grid',
                  placeItems: 'center',
                  background: 'black',
                  width: '100vw',
                  height: '100vh',
                  margin: 0,
                  padding: 0,
                } : {}),
              }}
            >
              {isFS ? (
                <img
                  key={`fs-${f.index}-${f.version}`}
                  src={f.src}
                  alt={`${f.name} fullscreen`}
                  decoding="async"
                  fetchpriority="low"
                  style={{
                    width: '100vw',
                    height: '100vh',
                    objectFit: 'contain',
                    display: 'block',
                  }}
                />
              ) : (
                <LiveTile
                  key={`tile-${f.index}-${f.version}-${f.nonce}`}
                  src={f.src}
                  title={`${f.name} ${f.stableRunning ? '[Live]' : '[Not Active]'}`}
                />
              )}

              {(!f.active || !f.stableRunning) && !isFS && (
                <div
                  aria-label="Not Active"
                  style={{
                    position: 'absolute',
                    inset: 0,
                    background: 'rgba(0,0,0,.55)',
                    display: 'grid',
                    placeItems: 'center',
                    borderRadius: 16,
                    pointerEvents: 'none',
                    color: '#eaf6ff',
                    fontWeight: 800,
                    letterSpacing: .2,
                  }}
                >
                  Not Active
                </div>
              )}
            </div>
          )
        })}
        {feeds.length === 0 && (
          <div style={{ padding: 16, opacity: .75 }}>Belum ada kamera terdaftar.</div>
        )}
      </div>
    </div>
  )
}
