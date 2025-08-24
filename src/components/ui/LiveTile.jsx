import React from 'react'

export default function LiveTile({ src, title, live = false, onClick }) {
  const handleKey = (e) => {
    if (!onClick) return
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      onClick()
    }
  }

  return (
    <div
      className="live-tile"
      onClick={onClick}
      onKeyDown={handleKey}
      role="button"
      tabIndex={0}
      aria-label={`Open ${title}`}
    >
      <img src={src} alt={title} />
      <div className="tag">{title} {live ? '[Live]' : ''}</div>
    </div>
  )
}