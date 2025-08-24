import React from 'react'

const API_BASE = (import.meta.env.VITE_API_URL || '').replace(/\/+$/, '')
const apiUrl = (path) => `${API_BASE}${path.startsWith('/') ? path : `/${path}`}`

export default function Logs() {
  const [rows, setRows] = React.useState([])

  React.useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch(apiUrl('/api/logs'), { cache: 'no-store' })
        if (!res.ok) throw new Error('HTTP ' + res.status)
        const data = await res.json()
        setRows(Array.isArray(data) ? data : [])
      } catch (e) {
        console.error('Failed to load logs:', e)
        setRows([])
      }
    }
    load()
  }, [])

  const handleOpenFoundedCaptures = async () => {
    // 1) Native bridge, if available
    if (window?.api?.openFoundedCaptures) {
      try {
        await window.api.openFoundedCaptures()
        return
      } catch (e) {
        console.warn('Native openFoundedCaptures failed, fallback...', e)
      }
    }

    // 2) Ask backend to open Windows Explorer directly
    try {
      const res = await fetch(apiUrl('/api/captures/open'), { method: 'POST' })
      if (res.ok) {
        // Optional: brief confirmation
        // alert('Opened in File Explorer.')
        return
      }
    } catch (_e) {}

    // 3) Fallback: open server-side browser page that lists files
    const browseUrl = apiUrl('/api/captures/browse')
    window.open(browseUrl, '_blank', 'noopener')
  }

  return (
    <div className="logs-page grid">
      <div className="logs-header">
        <span className="logs-title">Founded Logs</span>
        <span className="logs-subtitle">
          Detected missing people on available cameras will automatically recorded as logs here
        </span>
        <div className="logs-header-actions">
          <button
            type="button"
            className="logs-cta"
            onClick={handleOpenFoundedCaptures}
            aria-label="View Founded Captures"
            title="View Founded Captures"
          >
            <span className="logs-cta__icon" aria-hidden="true">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <path d="M3 6.75A1.75 1.75 0 0 1 4.75 5h4.086c.464 0 .908.185 1.236.514l1.414 1.414c.328.329.772.514 1.236.514H19.25A1.75 1.75 0 0 1 21 9.192v.558H7.42c-.79 0-1.49.485-1.76 1.21L3.2 18.5H2.75A1.75 1.75 0 0 1 1 16.75V6.75ZM7.42 11.75H22a1 1 0 0 1 .96 1.279l-1.8 6a1.75 1.75 0 0 1-1.68 1.221H5.5a1 1 0 0 1-.96-1.279l1.8-6a1.75 1.75 0 0 1 1.78-1.221Z" />
              </svg>
            </span>
            <span className="logs-cta__label">View Founded Captures</span>
          </button>
        </div>
      </div>

      <div className="table-wrap logs-table-wrap">
        <table className="table logs-table" role="table">
          <colgroup>
            <col style={{ width: '160px' }} />
            <col style={{ width: '120px' }} />
            <col />
            <col style={{ width: '200px' }} />
            <col style={{ width: '150px' }} />
          </colgroup>
          <thead>
            <tr>
              <th scope="col">Date</th>
              <th scope="col">Time</th>
              <th scope="col">Camera</th>
              <th scope="col">Person Name</th>
              <th scope="col">Match Score</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((l, i) => (
              <tr key={i}>
                <td>{l.date}</td>
                <td>{l.time}</td>
                <td>{l.camera}</td>
                <td>{l.person}</td>
                <td>{Number(l.score || 0).toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
    