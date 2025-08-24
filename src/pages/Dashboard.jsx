import React from 'react'
import { useNavigate } from 'react-router-dom'
import HeaderCard from '../components/ui/HeaderCard.jsx'
import Card from '../components/ui/Card.jsx'
import { BRAND } from '../config/brand.js'

const API_BASE = (import.meta.env.VITE_API_URL || '').replace(/\/+$/, '')

export default function Dashboard() {
  const navigate = useNavigate()

  // state summary yang tadinya dari mock, kini diisi oleh backend
  const [summary, setSummary] = React.useState({
    missingNotFound: 0,
    missingFounded: 0,
    activeCameras: 0,
    totalCameras: 0,
    detectionsToday: 0,
    possibleMatches: 0,
    confirmedMissing: 0,
  })

  // Non-scroll khusus dashboard (dipertahankan)
  React.useEffect(() => {
    document.body.classList.add('page-dashboard')
    return () => document.body.classList.remove('page-dashboard')
  }, [])

  // Ambil ringkasan dashboard dari backend
  React.useEffect(() => {
    let alive = true
    ;(async () => {
      try {
        const res = await fetch(`${API_BASE}/api/dashboard-summary`, { cache: 'no-store' })
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const data = await res.json()
        if (alive && data) {
          // pastikan field yang diperlukan ada, sisanya default
          setSummary((prev) => ({
            ...prev,
            missingNotFound: Number(data.missingNotFound ?? 0),
            missingFounded: Number(data.missingFounded ?? 0),
            activeCameras: Number(data.activeCameras ?? 0),
            totalCameras: Number(data.totalCameras ?? 0),
            detectionsToday: Number(data.detectionsToday ?? 0),
            possibleMatches: Number(data.possibleMatches ?? 0),
            confirmedMissing: Number(data.confirmedMissing ?? 0),
          }))
        }
      } catch (err) {
        // diamkan agar UI tidak berubah / noisy; fallback tetap angka 0
        // console.error('Failed to load dashboard summary', err)
      }
    })()
    return () => { alive = false }
  }, [])

  return (
    <div className="dashboard-page">
      {/* HEADER */}
      <div className="dash-header">
        <HeaderCard
          title={
            <React.Fragment>
              <span className="header-title" style={{ display: 'block' }}>Dashboard</span>
            </React.Fragment>
          }
          subtitle={<span>{BRAND.tagline}</span>}
        />
      </div>

      {/* BARIS KARTU */}
      <div className="dash-row">
        {/* Reported Missing Person */}
        <Card>
          <div className="dash-card-body">
            <div className="tile-title">Reported Missing Person</div>

            <div className="report-tiles">
              <div className="tile">
                <div className="stat-big num-gradient">{summary.missingNotFound}</div>
                <div className="stat-sub">Not yet founded</div>
                
              </div>
              <div className="tile">
                <div className="stat-big num-gradient">{summary.missingFounded}</div>
                <div className="stat-sub">Founded</div>
                
              </div>
            </div>


            <button
              className="btn btn-figma"
              type="button"
              onClick={() => navigate('/logs')}
              aria-label="View Reported Missing Person"
            >
              View Reported Missing Person
            </button>
          </div>
        </Card>

        {/* Total Active Cameras */}
        <Card>
          <div className="dash-card-body">
            <div className="tile-title">Total Active Cameras</div>
            <div className="stat-big num-gradient" style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
              {summary.activeCameras}
              <span style={{ fontSize: 28, fontWeight: 700, color: '#dfeaff' }}>
                /{summary.totalCameras}
              </span>
            </div>
            <button
              className="btn btn-figma"
              type="button"
              onClick={() => navigate('/cameras')}
              aria-label="View Cameras List"
            >
              View Cameras List
            </button>
          </div>
        </Card>
      </div>

      {/* SUMMARY */}
      <div className="dash-summary card">
        <div style={{ fontWeight: 700, color: '#cfe5ff' }}>Face Recognition Summary</div>

        <div className="summary-band">
          <div className="card padded">
            <div className="stat-big num-gradient">{summary.detectionsToday}</div>
            <div className="stat-sub">Detections Today</div>
          </div>
          <div className="card padded">
            <div className="stat-big num-gradient">{summary.possibleMatches}</div>
            <div className="stat-sub">Possible Matches</div>
          </div>
          <div className="card padded">
            <div className="stat-big num-gradient">{summary.confirmedMissing}</div>
            <div className="stat-sub">Confirmed Missing Person</div>
          </div>
        </div>
      </div>
    </div>
  )
}
