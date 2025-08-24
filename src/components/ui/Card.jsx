import React from 'react'

export default function Card({ className = '', padded = true, children, style }) {
  return (
    <div className={`card ${padded ? 'padded' : ''} ${className}`} style={style}>
      {children}
    </div>
  )
}