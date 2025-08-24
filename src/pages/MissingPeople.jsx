import React, { useEffect, useLayoutEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
// import './MissingPeople.css'
import { missingPersonsService } from '../services/missingPersonsService'

/* Dropdown kustom (copy dari Settings) */
function DSSelect({ label, options = [], defaultValue, onChange }) {
  const [open, setOpen] = useState(false)
  const [value, setValue] = useState(defaultValue ?? (options[0]?.value ?? options[0]))
  const ref = useRef(null)

  const getLabel = (val) => {
    const found = options.find(o => (o.value ?? o) === val)
    return found?.label ?? found ?? ''
  }

  useEffect(() => {
    const close = (e) => {
      if (!ref.current) return
      if (!ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', close)
    return () => document.removeEventListener('mousedown', close)
  }, [])

  const handleSelect = (val) => {
    setValue(val)
    onChange?.(val)
    setOpen(false)
  }

  return (
    <div className="field ds-select" ref={ref}>
      {label && <label className="label">{label}</label>}
      <button
        type="button"
        className="ds-select__trigger"
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={() => setOpen(v => !v)}
      >
        <span className="ds-select__value">{getLabel(value)}</span>
        <span className="ds-select__caret" aria-hidden="true" />
      </button>

      {open && (
        <div className="ds-select__menu" role="listbox" tabIndex={-1}>
          <ul className="ds-select__list">
            {options.map((o, idx) => {
              const val = o.value ?? o
              const lab = o.label ?? o
              const selected = val === value
              return (
                <li
                  key={idx}
                  role="option"
                  aria-selected={selected}
                  className={`ds-select__item ${selected ? 'is-selected' : ''}`}
                  onClick={() => handleSelect(val)}
                >
                  <span>{lab}</span>
                  {selected && (
                    <svg className="check" width="14" height="14" viewBox="0 0 24 24" fill="none">
                      <path d="M5 12l5 5 9-9" stroke="#BEE8FF" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  )}
                </li>
              )
            })}
          </ul>
        </div>
      )}
    </div>
  )
}

/* Stabilizer layer + scrollbar-gutter */
function useStableMissingLayers() {
  useEffect(() => {
    const root = document.querySelector('.missing-page')
    if (!root) return
    const els = root.querySelectorAll('.mp-header, .mp-table-wrap')

    const prev = new Map()
    els.forEach(el => {
      prev.set(el, {
        transform: el.style.transform,
        willChange: el.style.willChange,
        backface: el.style.backfaceVisibility,
        contain: el.style.contain
      })
      el.style.transform = (el.style.transform ? el.style.transform + ' ' : '') + 'translate3d(0,0,0)'
      el.style.backfaceVisibility = 'hidden'
      el.style.willChange = 'transform'
      el.style.contain = 'paint'
    })

    const doc = document.documentElement
    const prevDocGutter = doc.style.scrollbarGutter
    doc.style.scrollbarGutter = 'stable'

    const scroller = document.querySelector('.app-content')
    const prevScrollerGutter = scroller?.style.scrollbarGutter
    if (scroller) scroller.style.scrollbarGutter = 'stable'

    return () => {
      els.forEach(el => {
        const p = prev.get(el) || {}
        el.style.transform = p.transform || ''
        el.style.willChange = p.willChange || ''
        el.style.backfaceVisibility = p.backface || ''
        el.style.contain = p.contain || ''
      })
      doc.style.scrollbarGutter = prevDocGutter
      if (scroller && prevScrollerGutter !== undefined) scroller.style.scrollbarGutter = prevScrollerGutter
    }
  }, [])
}

export default function MissingPeople() {
  const [people, setPeople] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // modal view/edit existing row
  const [selectedPerson, setSelectedPerson] = useState(null)
  const [formData, setFormData] = useState(null)
  const [isEditing, setIsEditing] = useState(false)

  // modal add new
  const [showAddModal, setShowAddModal] = useState(false)
  const [addForm, setAddForm] = useState({ full_name: '', notes: '', status: 'missing' })
  const [dragOver, setDragOver] = useState(false)
  const [uploadName, setUploadName] = useState('')
  const [uploadedImageUrl, setUploadedImageUrl] = useState('')

  // delete confirm modal
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)

  // refs untuk tinggi tbody (scroll internal)
  const wrapRef = useRef(null)
  const theadRef = useRef(null)
  const tbodyRef = useRef(null)
  const headerRef = useRef(null)

  useStableMissingLayers()

  // Load missing persons from database
  useEffect(() => {
    const loadMissingPersons = async () => {
      try {
        setLoading(true)
        const data = await missingPersonsService.getAll()
        setPeople(data)
        setError(null)
      } catch (err) {
        setError('Failed to load missing persons')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    loadMissingPersons()
  }, [])

  // Nonaktifkan scroll global 1 halaman → scroller hanya di tabel (tbody)
  useLayoutEffect(() => {
    const scroller = document.querySelector('.app-content')
    if (!scroller) return
    const prevOverflow = scroller.style.overflow
    scroller.style.overflow = 'hidden'
    return () => { scroller.style.overflow = prevOverflow }
  }, [])

  // Hitung tinggi tbody agar mengikuti sisa tinggi .app-content (memperhitungkan padding)
  const recalcTbodyHeight = () => {
    const wrap = wrapRef.current
    const thead = theadRef.current
    const tbody = tbodyRef.current
    const appContent = document.querySelector('.app-content')

    if (!wrap || !thead || !tbody || !appContent) return

    const acRect = appContent.getBoundingClientRect()
    const wrapRect = wrap.getBoundingClientRect()
    const cs = getComputedStyle(appContent)
    const padTop = parseFloat(cs.paddingTop) || 0
    const padBottom = parseFloat(cs.paddingBottom) || 0

    // Total area yang tersedia di dalam app-content (konten + padding)
    const acInnerH = appContent.clientHeight // termasuk padding, exclude border

    // Jarak wrap dari sisi atas app-content (menghormati padding top)
    const offsetFromTop = (wrapRect.top - acRect.top)

    // Sisa tinggi usable = tinggi inner - offset - paddingBottom
    const available = Math.max(acInnerH - offsetFromTop - padBottom, 120)

    wrap.style.height = available + 'px'

    // Tinggi tbody = sisa setelah dikurangi thead
    const headH = thead.offsetHeight
    const bodyH = Math.max(available - headH, 100)
    tbody.style.height = bodyH + 'px'
    tbody.style.maxHeight = bodyH + 'px'
    tbody.style.overflow = 'auto'
  }

  useLayoutEffect(() => {
    // jalankan setelah render & saat ukuran/rows berubah
    recalcTbodyHeight()
    const onResize = () => recalcTbodyHeight()
    window.addEventListener('resize', onResize)
    // sedikit delay untuk memastikan font/layout settle
    const id = requestAnimationFrame(recalcTbodyHeight)
    return () => { window.removeEventListener('resize', onResize); cancelAnimationFrame(id) }
  }, [people.length])

  // util waktu
  const formatDate = (dateString) => {
    if (!dateString) return '—'
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: '2-digit', 
      day: '2-digit' 
    })
  }

  const formatTime = (dateString) => {
    if (!dateString) return '—'
    const date = new Date(dateString)
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: true 
    })
  }

  // open existing modal
  const handleRowClick = (person) => {
    setSelectedPerson(person)
    setFormData({ ...person })
    setIsEditing(false)
  }
  const closeViewModal = () => { setSelectedPerson(null); setFormData(null); setIsEditing(false) }

  const handleFormChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const handleEditClick = () => setIsEditing(true)
  const handleCancelEdit = () => { setFormData({ ...selectedPerson }); setIsEditing(false) }
  
  const handleApplyChanges = async () => {
    try {
      const updatedPerson = await missingPersonsService.update(formData.id, formData)
      setPeople(prev => prev.map(p => (p.id === updatedPerson.id ? updatedPerson : p)))
      setSelectedPerson(updatedPerson)
      setIsEditing(false)
    } catch (err) {
      console.error('Failed to update missing person:', err)
      alert('Failed to update missing person')
    }
  }

  // Delete flow
  const openDeleteConfirm = () => setShowDeleteConfirm(true)
  const handleCancelDelete = () => setShowDeleteConfirm(false)
  
  const handleConfirmDelete = async () => {
    if (!selectedPerson) return
    try {
      await missingPersonsService.delete(selectedPerson.id)
      setPeople(prev => prev.filter(p => p.id !== selectedPerson.id))
      setShowDeleteConfirm(false)
      closeViewModal()
    } catch (err) {
      console.error('Failed to delete missing person:', err)
      alert('Failed to delete missing person')
    }
  }

  // add modal logic
  const handleAddNewPerson = () => {
    setAddForm({ full_name: '', notes: '', status: 'missing' })
    setUploadName('')
    setUploadedImageUrl('')
    setShowAddModal(true)
  }
  
  const handleAddChange = (e) => {
    const { name, value } = e.target
    setAddForm(prev => ({ ...prev, [name]: value }))
  }
  
  const handleAddCancel = () => setShowAddModal(false)
  
  const handleAddSave = async () => {
    if (!uploadedImageUrl) {
      alert('Please upload an image first')
      return
    }
    
    try {
      const newPersonData = {
        full_name: addForm.full_name || 'Unknown',
        target_image_url: uploadedImageUrl,
        status: addForm.status || 'missing',
        notes: addForm.notes || '',
        approval: 'pending'
      }
      
      const newPerson = await missingPersonsService.create(newPersonData)
      setPeople(prev => [newPerson, ...prev])
      setShowAddModal(false)
    } catch (err) {
      console.error('Failed to create missing person:', err)
      alert('Failed to create missing person')
    }
  }

  // upload/drag handlers
  const onFileChange = async (e) => { 
    const file = e.target.files?.[0]
    if (file) {
      setUploadName(file.name)
      try {
        const imageUrl = await missingPersonsService.uploadImage(file)
        setUploadedImageUrl(imageUrl)
      } catch (err) {
        console.error('Failed to upload image:', err)
        alert('Failed to upload image')
      }
    }
  }
  
  const onDrop = async (e) => { 
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files?.[0]
    if (file) {
      setUploadName(file.name)
      try {
        const imageUrl = await missingPersonsService.uploadImage(file)
        setUploadedImageUrl(imageUrl)
      } catch (err) {
        console.error('Failed to upload image:', err)
        alert('Failed to upload image')
      }
    }
  }
  
  const onDragOver = (e) => { e.preventDefault(); setDragOver(true) }
  const onDragLeave = () => setDragOver(false)

  if (loading) {
    return (
      <div className="missing-page" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
        <div>Loading missing persons...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="missing-page" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
        <div style={{ color: 'red' }}>{error}</div>
      </div>
    )
  }

  return (
    <>
      <div className="missing-page" style={{ display: 'grid', gridTemplateRows: 'max-content 1fr', gap: 18, height: '100%', minHeight: 0 }}>
        {/* Header */}
        <div className="mp-header" ref={headerRef}>
          <div className="mp-header-main">
            <div className="mp-title">Missing People</div>
            <div className="mp-sub">Manage missing people</div>

            <div className="mp-actions">
              <button className="mp-add-btn" type="button" onClick={handleAddNewPerson}>
                <svg width="20" height="20" fill="none" viewBox="0 0 20 20" aria-hidden="true">
                  <circle cx="10" cy="10" r="10" fill="#fff" fillOpacity="0.18" />
                  <path d="M10 5v10M5 10h10" stroke="#fff" strokeWidth="2" strokeLinecap="round" />
                </svg>
                Add New Missing Person
              </button>
            </div>
          </div>
        </div>

        {/* Table (header tetap, body scroll) */}
        <div className="mp-table-wrap" ref={wrapRef} style={{ minHeight: 0 }}>
          <table className="mp-table" style={{ width: '100%', borderCollapse: 'separate', borderSpacing: 0, tableLayout: 'fixed' }}>
            <thead ref={theadRef} style={{ display: 'table', width: '100%', tableLayout: 'fixed' }}>
              <tr>
                <th style={{ textAlign: 'center', width: '20%' }}>Reported Time</th>
                <th style={{ textAlign: 'center', width: '15%' }}>Photo</th>
                <th style={{ textAlign: 'center', width: '35%' }}>Person Name</th>
                <th style={{ textAlign: 'center', width: '30%' }}>Status</th>
              </tr>
            </thead>
            <tbody ref={tbodyRef} style={{ display: 'block', overflow: 'auto' }}>
              {people.map((p) => (
                <tr key={p.id} onClick={() => handleRowClick(p)} className="mp-row" style={{ display: 'table', width: '100%', tableLayout: 'fixed' }}>
                  <td className="mp-td mp-time" style={{ textAlign: 'center', verticalAlign: 'middle', width: '20%' }}>
                    <div className="mp-time-col" style={{ justifyItems: 'center', textAlign: 'center' }}>
                      <span>{formatDate(p.created_at)}</span>
                      <span className="mp-time-sub">{formatTime(p.created_at)}</span>
                    </div>
                  </td>
                  <td className="mp-td" style={{ textAlign: 'center', verticalAlign: 'middle', width: '15%' }}>
                    <div className="mp-photo">
                      {p.target_image_url && (
                        <img 
                          src={p.target_image_url} 
                          alt={p.full_name}
                          style={{ width: '40px', height: '40px', borderRadius: '50%', objectFit: 'cover' }}
                        />
                      )}
                    </div>
                  </td>
                  <td className="mp-td" style={{ textAlign: 'center', verticalAlign: 'middle', width: '35%' }}>
                    {p.full_name}
                  </td>
                  <td
                    className="mp-td"
                    style={{
                      textAlign: 'center',
                      verticalAlign: 'middle',
                      fontWeight: 700,
                      width: '30%',
                      color: p.status === 'found' ? '#7cfab3' : '#ff9aa5',
                    }}
                  >
                    {p.status}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal view/edit existing — via PORTAL */}
      {selectedPerson && formData && createPortal(
        <div className="mp-modal__overlay is-portal" onClick={closeViewModal}>
          <div className="mp-view__card" onClick={(e) => e.stopPropagation()}>
            <button className="mp-view__close" onClick={closeViewModal}>×</button>

            <h2 className="mp-view__title">Missing Person</h2>

            <div className="mp-view__body">
              <div className="mp-view__photo">
                {formData.target_image_url && (
                  <img 
                    src={formData.target_image_url} 
                    alt={formData.full_name}
                    style={{ width: '100%', height: '200px', objectFit: 'cover', borderRadius: '8px' }}
                  />
                )}
              </div>
              <div className="mp-view__detail">
                <div className="mp-field">
                  <label className="mp-label">Name</label>
                  {isEditing ? (
                    <input type="text" name="full_name" value={formData.full_name} onChange={handleFormChange} className="mp-text" />
                  ) : (
                    <div className="mp-text readonly">{formData.full_name}</div>
                  )}
                </div>

                <div className="mp-field">
                  <label className="mp-label">Additional Information</label>
                  {isEditing ? (
                    <input type="text" name="notes" value={formData.notes} onChange={handleFormChange} className="mp-text" />
                  ) : (
                    <div className="mp-text readonly">{formData.notes || '—'}</div>
                  )}
                </div>

                <div className="mp-field">
                  <label className="mp-label">Status</label>
                  {!isEditing ? (
                    <div
                      className="mp-text readonly"
                      style={{
                        color: formData.status === 'found' ? '#7cfab3' : '#ff9aa5',
                        fontWeight: 700,
                      }}
                    >
                      {formData.status}
                    </div>
                  ) : (
                    <div className="settings-page">
                      <DSSelect
                        options={[
                          { label: 'Found', value: 'found' },
                          { label: 'Missing', value: 'missing' },
                        ]}
                        defaultValue={formData.status}
                        onChange={(val) => setFormData(prev => ({ ...prev, status: val }))}
                      />
                    </div>
                  )}
                </div>

                <div className="mp-field">
                  <label className="mp-label">Approval</label>
                  <div className="mp-text readonly" style={{ color: '#ffd700', fontWeight: 700 }}>
                    {formData.approval}
                  </div>
                </div>
              </div>
            </div>

            <p className="mp-view__reported">
              Reported Missing Time:&nbsp;
              <strong>{`${formatDate(selectedPerson?.created_at)}  ${formatTime(selectedPerson?.created_at)}`}</strong>
            </p>

            <div className="mp-view__actions">
              {!isEditing ? (
                <>
                  <button className="mp-btn mp-btn--primary sm" onClick={handleEditClick}>Edit Information</button>
                  <button className="mp-btn mp-btn--danger sm" onClick={() => setShowDeleteConfirm(true)}>Delete Missing Person</button>
                </>
              ) : (
                <>
                  <button className="mp-btn mp-btn--primary sm" onClick={handleApplyChanges}>Apply Changes</button>
                  <button className="mp-btn mp-btn--ghost sm" onClick={handleCancelEdit}>Cancel</button>
                  <button className="mp-btn mp-btn--danger sm" onClick={() => setShowDeleteConfirm(true)}>Delete Missing Person</button>
                </>
              )}
            </div>
          </div>
        </div>,
        document.body
      )}

      {/* Add New Missing Person modal — tombol Result sama (DSSelect) */}
      {showAddModal && createPortal(
        <div className="mp-modal__overlay is-portal" onClick={handleAddCancel}>
          <div className="mp-modal" onClick={(e) => e.stopPropagation()}>
            <h2 className="mp-modal__title">Add Missing Person</h2>

            <div className="mp-add__content">
              {/* Upload/Dropzone */}
              <label
                className={`mp-upload${dragOver ? ' is-drag' : ''}`}
                onDragOver={onDragOver}
                onDragLeave={onDragLeave}
                onDrop={onDrop}
              >
                <input type="file" accept="image/*" onChange={onFileChange} hidden />
                {/* Jarak ikon dan teks dipersempit: gap 6px */}
                <div className="mp-upload__inner" style={{ gap: 6 }}>
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <path d="M12 3v12m0-12l-4 4m4-4l4 4M4 15v2a4 4 0 004 4h8a4 4 0 004-4v-2" stroke="#BEE8FF" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                  <div className="mp-upload__text">
                    {uploadName ? (
                      <>
                        <span className="file">Selected:</span>
                        <span className="name" title={uploadName}>{uploadName}</span>
                      </>
                    ) : (
                      <>
                        <strong>Upload or Drag</strong>
                        <span>Picture Here</span>
                      </>
                    )}
                  </div>
                </div>
              </label>

              {/* Form fields */}
              <div className="mp-add__form">
                <div className="mp-field">
                  <label className="mp-label">Name</label>
                  <input
                    type="text"
                    name="full_name"
                    value={addForm.full_name}
                    onChange={handleAddChange}
                    className="mp-input"
                    placeholder="Enter name"
                  />
                </div>

                <div className="mp-field">
                  <label className="mp-label">Additional Information</label>
                  <input
                    type="text"
                    name="notes"
                    value={addForm.notes}
                    onChange={handleAddChange}
                    className="mp-input"
                    placeholder="Any notes..."
                  />
                </div>

                <div className="mp-field">
                  <label className="mp-label">Status</label>
                  {/* Samakan dengan edit → DSSelect */}
                  <div className="settings-page">
                    <DSSelect
                      options={[
                        { label: 'Missing', value: 'missing' },
                        { label: 'Found', value: 'found' },
                      ]}
                      defaultValue={addForm.status}
                      onChange={(val) => setAddForm(prev => ({ ...prev, status: val }))}
                    />
                  </div>
                </div>

                <div className="mp-actions-row">
                  <button className="mp-btn mp-btn--primary" onClick={handleAddSave}>
                    Save Information
                  </button>
                  <button className="mp-btn mp-btn--ghost" onClick={handleAddCancel}>
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>,
        document.body
      )}

      {/* Delete confirmation modal */}
      {showDeleteConfirm && createPortal(
        <div className="mp-modal__overlay is-portal" onClick={handleCancelDelete}>
          <div className="mp-modal mp-modal--confirm" onClick={(e) => e.stopPropagation()}>
            <div className="mp-confirm">
              <h2 className="mp-confirm__title">Delete <span className="accent">Missing Person</span></h2>
              <p className="mp-confirm__desc">Are you sure you wanna delete this reported missing person?</p>
              <div className="mp-actions-row mp-confirm__actions">
                <button className="mp-btn mp-btn--ghost" onClick={handleCancelDelete}>Cancel</button>
                <button className="mp-btn mp-btn--primary" onClick={handleConfirmDelete}>Submit</button>
              </div>
            </div>
          </div>
        </div>,
        document.body
      )}
    </>
  )
}