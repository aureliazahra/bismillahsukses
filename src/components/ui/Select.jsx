import React from 'react'

export default function Select({ label, options = [], ...props }) {
  return (
    <div className="field">
      {label && <label className="label">{label}</label>}
      <select className="select" {...props}>
        {options.map(o => <option key={o.value ?? o} value={o.value ?? o}>{o.label ?? o}</option>)}
      </select>
    </div>
  )
}