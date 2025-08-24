import React from 'react'

export default function TabPill({ options = [], value, onChange }) {
  return (
    <div className="tabs">
      {options.map(opt => (
        <button
          key={opt.value}
          className={`tab-pill ${value === opt.value ? 'active' : ''}`}
          onClick={() => onChange(opt.value)}
        >
          {opt.label}
        </button>
      ))}
    </div>
  )
}