import React from 'react'

export default function Input({ label, ...props }) {
  return (
    <div className="field">
      {label && <label className="label">{label}</label>}
      <input className="input" {...props} />
    </div>
  )
}