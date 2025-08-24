import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { BRAND } from '../../config/brand.js'

function Icon({ name }) {
  const common = { width: 22, height: 22, fill: 'currentColor' }
  switch (name) {
    case 'dashboard':
      return (<svg viewBox="0 0 24 24" {...common}><path d="M3 3h8v8H3V3Zm10 0h8v5h-8V3ZM3 13h8v8H3v-8Zm10-4h8v12h-8V9Z"/></svg>)
    case 'camera':
      return (<svg viewBox="0 0 24 24" {...common}><path d="M17.5 7 15.8 5H9L7.5 7H4a3 3 0 0 0-3 3v6a3 3 0 0 0 3 3h16a3 3 0 0 0 3-3v-6a3 3 0 0 0-3-3h-2.5ZM12 17a4 4 0 1 1 0-8 4 4 0 0 1 0 8Z"/></svg>)
    case 'realtime':
      return (<svg viewBox="0 0 24 24" {...common}><path d="M12 12a5 5 0 1 0-5-5 5 5 0 0 0 5 5Zm0 2c-4.2 0-8 2.1-8 5v1h16v-1c0-2.9-3.8-5-8-5Z"/></svg>)
    case 'logs':
      return (<svg viewBox="0 0 24 24" {...common}><path d="M7 3h8l4 4v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Zm8 1.5V8h3.5L15 4.5ZM8 12h8v2H8v-2Zm0 4h8v2H8v-2Zm0-8h5v2H8V8Z"/></svg>)
    case 'people':
      return (<svg viewBox="0 0 24 24" {...common}><path d="M15 8a4 4 0 1 1-4-4 4 4 0 0 1 4 4ZM2 20v-1c0-3.3 4-5 8-5s8 1.7 8 5v1H2Z"/></svg>)
    case 'settings':
      return (<svg viewBox="0 0 24 24" {...common}><path d="M19.4 12.9a7.8 7.8 0 0 0 .1-1 7.8 7.8 0 0 0-.1-1l2-1.6a.5.5 0 0 0 .1-.6l-1.9-3.2a.5.5 0 0 0-.6-.2l-2.3.9a7.6 7.6 0 0 0-1.7-1L14.7 2a.5.5 0 0 0-.5-.3h-3.4a.5.5 0 0 0-.5.3L9 4.2a7.6 7.6 0 0 0-1.7 1l-2.3-.9a.5.5 0 0 0-.6.2L2.5 7.7a.5.5 0 0 0 .1.6l2 1.6a7.8 7.8 0 0 0-.1 1c0 .3 0 .7.1 1l-2 1.6a.5.5 0 0 0-.1.6l1.9 3.2a.5.5 0 0 0 .6.2l2.3-.9a7.6 7.6 0 0 0 1.7 1l1.3 2.2a.5.5 0 0 0 .5.3h3.4a.5.5 0 0 0 .5-.3l1.3-2.2a7.6 7.6 0 0 0 1.7-1l2.3.9a.5.5 0 0 0 .6-.2l1.9-3.2a.5.5 0 0 0-.1-.6l-2-1.6ZM12 15a3 3 0 1 1 0-6 3 3 0 0 1 0 6Z"/></svg>)
    default:
      return null
  }
}

export default function Sidebar() {
  const { pathname } = useLocation()
  const items = [
    { to: '/dashboard', label: 'Dashboard', icon: 'dashboard' },
    { to: '/cameras', label: 'CCTV Camera', icon: 'camera' },
    { to: '/realtime', label: 'Face Detection', icon: 'realtime' },
    { to: '/logs', label: 'History Logs', icon: 'logs' },
    { to: '/missing', label: 'Missing People', icon: 'people' }
  ]

  return (
    <aside className="sidebar">
      <div className="brand">
        <img src={BRAND.logo} alt={`${BRAND.name} logo`} />
        {/* tampilkan kembali nama brand */}
        <div className="name">{BRAND.name}</div>
      </div>

      <nav className="nav">
        {items.map(it => (
          <Link key={it.to} to={it.to} className={pathname === it.to ? 'active' : ''}>
            <div className="icon"><Icon name={it.icon} /></div>
            <div className="label">{it.label}</div>
          </Link>
        ))}
        <div className="nav-bottom">
          <Link to="/settings" className={pathname === '/settings' ? 'active' : ''}>
            <div className="icon"><Icon name="settings" /></div>
            <div className="label">Settings</div>
          </Link>
        </div>
      </nav>
    </aside>
  )
}