import React from 'react'

export default function HeaderCard({ title, subtitle, right, children }) {
  return (
    <div className="header-card">
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16 }}>
        <div>
          <div className="header-title">{title}</div>
          {subtitle && <div className="header-sub">{subtitle}</div>}
        </div>
        {right}
      </div>
      {children}
    </div>
  )
}