import React from 'react'
import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar.jsx'
import Topbar from './Topbar.jsx'
import { BRAND } from '../../config/brand.js'

export default function AppShell() {
  const bgStyle = BRAND.background
    ? { '--bg-image': `url(${BRAND.background})` }
    : {}
  return (
    <div className="app-shell" style={bgStyle}>
      <Sidebar />
      <Topbar />
      <main className="app-content">
        <Outlet />
      </main>
    </div>
  )
}