import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'

export default function Topbar() {
  const nav = useNavigate()
  const [unread, setUnread] = useState(3)

  const handleBellClick = () => {
    setUnread(0)
    nav('/notifications')
  }

  return (
    <div
      className="topbar"
      style={{
        position: 'relative',
        width: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'flex-end', // dorong semua ke kanan
      }}
    >
      {/* SEARCH ICON (kiri dari pasangan ikon, tapi tetap di sisi kanan layar) */}
      <div className="search-icon" aria-label="Search" style={{ marginRight: 12 }}>
        <svg width="30" height="30" viewBox="0 0 24 24" fill="none">
          <path
            d="M21 21l-4.3-4.3M11 18a7 7 0 1 1 0-14 7 7 0 0 1 0 14Z"
            stroke="#bfe8ff"
            strokeWidth="3"
            strokeLinecap="round"
          />
        </svg>
      </div>

      {/* BELL ICON (paling kanan) */}
      <div className="bell" onClick={handleBellClick} style={{ cursor: 'pointer' }}>
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
          <path
            d="M12 22a2 2 0 0 0 2-2H10a2 2 0 0 0 2 2Zm6-6V11a6 6 0 0 0-5-5.9V4a1 1 0 0 0-2 0v1.1A6 6 0 0 0 6 11v5l-2 2v1h16v-1l-2-2Z"
            fill="#e9f5ff"
          />
        </svg>
      </div>
    </div>
  )
}