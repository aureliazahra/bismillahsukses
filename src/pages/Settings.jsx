import React from 'react'
import { createPortal } from 'react-dom'
import HeaderCard from '../components/ui/HeaderCard.jsx'
import Card from '../components/ui/Card.jsx'
import { settingsOptions as OPT_FROM_MOCK } from '../data/mock.js'

/* ========= API helpers ========= */
const API_BASE = '' // Vite dev proxy -> FastAPI
const asJson = async (res) => {
  if (!res.ok) {
    const t = await res.text().catch(()=>'')
    throw new Error(t || `HTTP ${res.status}`)
  }
  return res.status === 204 ? null : res.json()
}
const api = {
  getCfg: () => fetch(`${API_BASE}/api/app-config`).then(asJson),
  putCfg: (patch) => fetch(`${API_BASE}/api/app-config`, {
    method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(patch)
  }).then(asJson),
}

/* ========= Toast (result apply) ========= */
function Toast({ kind = 'ok', text = '', onClose }) {
  React.useEffect(() => { const id = setTimeout(onClose, 1400); return () => clearTimeout(id) }, [onClose])
  return createPortal(
    <div style={{ position: 'fixed', inset: 'auto 20px 20px auto', zIndex: 4000 }} aria-live="polite">
      <div className="glass-section" style={{
        padding: '10px 14px', borderRadius: 12, minWidth: 220, textAlign: 'center', fontWeight: 600,
        color: kind === 'ok' ? '#7cfab3' : '#ff9aa5',
        boxShadow: '0 8px 24px rgba(0,0,0,.35)',
        background: 'linear-gradient(180deg, rgba(8,20,48,.75), rgba(8,12,32,.65))',
        border: '1px solid rgba(126, 232, 255, .18)', backdropFilter: 'blur(6px)',
      }}>{text}</div>
    </div>, document.body
  )
}

/* ========= Stabilizer ========= */
function useStableSettingsLayers() {
  React.useEffect(() => {
    const root = document.querySelector('.settings-page')
    if (!root) return
    const els = root.querySelectorAll('.header-card, .settings-card, .glass-section')
    const prev = new Map()
    els.forEach(el => {
      prev.set(el, {
        transform: el.style.transform, willChange: el.style.willChange,
        backface: el.style.backfaceVisibility, contain: el.style.contain
      })
      el.style.transform = (el.style.transform ? el.style.transform + ' ' : '') + 'translate3d(0,0,0)'
      el.style.backfaceVisibility = 'hidden'
      el.style.willChange = 'transform'
      el.style.contain = 'paint'
    })
    const doc = document.documentElement
    const prevGutter = doc.style.scrollbarGutter
    doc.style.scrollbarGutter = 'stable'
    return () => {
      els.forEach(el => {
        const p = prev.get(el) || {}
        el.style.transform = p.transform || ''
        el.style.willChange = p.willChange || ''
        el.style.backfaceVisibility = p.backface || ''
        el.style.contain = p.contain || ''
      })
      doc.style.scrollbarGutter = prevGutter
    }
  }, [])
}

/* ========= Inputs ========= */

function LockInput({ label, type = 'text', defaultValue = '' }) {
  const [ro, setRo] = React.useState(true)
  return (
    <div className="field">
      {label && <label className="label">{label}</label>}
      <input
        className="input input--glass"
        type={type}
        defaultValue={defaultValue}
        readOnly={ro}
        onFocus={() => setRo(false)}
        onBlur={() => setRo(true)}
      />
    </div>
  )
}

/* Select — menu dibikin PORTAL (z-index tinggi), TANPA styling visual di JSX */
/* Select — menu di-PORTAL, close pakai 'click' dan abaikan klik di dalam menu */
function DSSelect({ label, options = [], defaultValue, onChange, disabled = false }) {
  const [open, setOpen] = React.useState(false);
  const [value, setValue] = React.useState(defaultValue ?? (options[0]?.value ?? options[0]));
  const btnRef = React.useRef(null);
  const menuRef = React.useRef(null);                  // <— ref ke panel menu
  const [pos, setPos] = React.useState({ top: 0, left: 0, width: 0 });

  React.useEffect(() => {
    setValue(defaultValue ?? (options[0]?.value ?? options[0]));
  }, [defaultValue, options]);

  const getLabel = (val) => {
    const found = options.find(o => (o.value ?? o) === val);
    return found?.label ?? found ?? '';
  };

  const measure = () => {
    const r = btnRef.current?.getBoundingClientRect();
    if (!r) return;
    setPos({ top: r.bottom + 6, left: r.left, width: r.width });
  };

  const handleToggle = () => {
    if (disabled) return;
    measure();
    setOpen(v => !v);
  };

  const handleSelect = (val) => {
    setValue(val);
    onChange?.(val);
    setOpen(false);
  };

  React.useEffect(() => {
    if (!open) return;

    const onDocClick = (e) => {
      // kalau klik di tombol atau di dalam menu, jangan tutup dulu
      if (btnRef.current?.contains(e.target)) return;
      if (menuRef.current?.contains(e.target)) return;
      setOpen(false);
    };

    // PENTING: pakai 'click', bukan 'mousedown'
    document.addEventListener('click', onDocClick);
    const onResizeScroll = () => measure();
    window.addEventListener('resize', onResizeScroll);
    window.addEventListener('scroll', onResizeScroll, true);

    return () => {
      document.removeEventListener('click', onDocClick);
      window.removeEventListener('resize', onResizeScroll);
      window.removeEventListener('scroll', onResizeScroll, true);
    };
  }, [open]);

  const menu = open ? createPortal(
    <div className="ds-portal" style={{ position: 'fixed', top: pos.top, left: pos.left, width: pos.width, zIndex: 3500 }}>
      <div ref={menuRef} className="ds-select__menu" role="listbox" tabIndex={-1}>
        <ul className="ds-select__list">
          {options.map((o, idx) => {
            const val = o.value ?? o;
            const lab = o.label ?? o;
            const selected = val === value;
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
                    <path d="M5 12l5 5 9-9" stroke="#BEE8FF" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                )}
              </li>
            );
          })}
        </ul>
      </div>
    </div>,
    document.body
  ) : null;

  return (
    <div className="field ds-select">
      {label && <label className="label">{label}</label>}
      <button
        ref={btnRef}
        type="button"
        className="ds-select__trigger"
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={handleToggle}
        disabled={disabled}
        style={disabled ? { opacity: 0.6, cursor: 'not-allowed' } : undefined}
      >
        <span className="ds-select__value">{getLabel(value)}</span>
        <span className="ds-select__caret" aria-hidden="true" />
      </button>
      {menu}
    </div>
  );
}


function DSNumber({ label, defaultValue = 0, min, max, step = 1, onChange, disabled = false }) {
  const [val, setVal] = React.useState(Number(defaultValue) || 0)
  const [active, setActive] = React.useState(false)

  React.useEffect(() => { setVal(Number(defaultValue) || 0) }, [defaultValue])

  const decimals = React.useMemo(() => {
    const s = String(step)
    return s.includes('.') ? s.split('.')[1].length : 0
  }, [step])

  const clamp = (n) => {
    let x = Number(n)
    if (!Number.isFinite(x)) x = 0
    if (typeof min === 'number') x = Math.max(x, min)
    if (typeof max === 'number') x = Math.min(x, max)
    const f = Math.pow(10, decimals)
    return Math.round(x * f) / f
  }
  const update = (n) => { const x = clamp(n); setVal(x); onChange?.(x) }
  const stepUp = () => update((val || 0) + step)
  const stepDown = () => update((val || 0) - step)

  const onWheel = (e) => {
    if (!active || disabled) return
    e.preventDefault()
    if (e.deltaY < 0) stepUp(); else stepDown()
  }

  return (
    <div className="field ds-num" onWheel={onWheel}>
      {label && <label className="label">{label}</label>}
      <div
        className="ds-num__wrap"
        tabIndex={disabled ? -1 : 0}
        onFocus={() => !disabled && setActive(true)}
        onBlur={() => setActive(false)}
        style={disabled ? { opacity: 0.6, cursor: 'not-allowed' } : undefined}
      >
        <input
          type="number"
          className="ds-num__field"
          value={val}
          min={min}
          max={max}
          step={step}
          readOnly={disabled || !active}
          onFocus={() => !disabled && setActive(true)}
          onBlur={() => setActive(false)}
          onChange={(e) => update(e.target.value)}
          onKeyDown={(e) => {
            if (disabled || !active) return
            if (e.key === 'ArrowUp') { e.preventDefault(); stepUp() }
            if (e.key === 'ArrowDown') { e.preventDefault(); stepDown() }
          }}
        />
        <div className="ds-num__stepper" aria-hidden="true">
          <button type="button" className="up" disabled={disabled} onMouseDown={() => setActive(true)} onClick={stepUp}>
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none">
              <path d="M7 14l5-5 5 5" stroke="#BEE8FF" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
          <button type="button" className="down" disabled={disabled} onMouseDown={() => setActive(true)} onClick={stepDown}>
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none">
              <path d="M7 10l5 5 5-5" stroke="#BEE8FF" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}

function DSRange({ label, min = 0, max = 10, step = 1, defaultValue = 2, onChange, disabled = false }) {
  const [val, setVal] = React.useState(defaultValue)
  const [active, setActive] = React.useState(false)
  React.useEffect(() => setVal(defaultValue), [defaultValue])
  const update = (v) => { const x = Number(v); setVal(x); onChange?.(x) }
  const pct = React.useMemo(() => max === min ? 0 : ((val - min) / (max - min)) * 100, [val, min, max])

  return (
    <div className="field ds-range" style={disabled ? { opacity: 0.6, cursor: 'not-allowed' } : undefined}>
      {label && <label className="label">{label}</label>}
      <div
        className={`ds-range__row ${active ? 'is-active' : ''}`}
        onFocus={() => !disabled && setActive(true)}
        onBlur={() => setActive(false)}
        tabIndex={disabled ? -1 : 0}
        style={{ '--pct': `${pct}%` }}
      >
        <input
          type="range"
          min={min} max={max} step={step} value={val}
          onChange={(e) => update(e.target.value)}
          className="ds-range__input"
          aria-valuemin={min} aria-valuemax={max} aria-valuenow={val}
          disabled={disabled}
        />
        <span className="ds-range__value">{val}</span>
      </div>
    </div>
  )
}

function DSFile({ label, defaultPath = 'models/antispoof/minifasnet/minifasnet.onnx', onChange, disabled = false }) {
  const [path, setPath] = React.useState(defaultPath)
  const ref = React.useRef(null)
  React.useEffect(() => setPath(defaultPath), [defaultPath])
  const pick = () => !disabled && ref.current?.click()
  const onFile = (e) => {
    const f = e.target.files?.[0]
    if (f) { setPath(f.name); onChange?.(f) }
  }
  return (
    <div className="field ds-file" style={disabled ? { opacity: 0.6, cursor: 'not-allowed' } : undefined}>
      {label && <label className="label">{label}</label>}
      <div className="ds-file__row" style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: 10, alignItems: 'center' }}>
        <input className="input input--glass" readOnly value={path} />
        <button type="button" className="btn-figma ds-file__btn" onClick={pick} disabled={disabled}>Browse ONNX...</button>
        <input type="file" accept=".onnx" ref={ref} style={{ display: 'none' }} onChange={onFile} />
      </div>
    </div>
  )
}

/* ===== Options dari mock.js ===== */
const {
  deviceOptions, detectorOptions, antispoofBackendOptions,
  preprocessOptions, antispoofModeOptions, saveModeOptions, saveWhichOptions,
} = OPT_FROM_MOCK

export default function Settings() {
  const [toast, setToast] = React.useState(null)
  const showToast = (text, ok = true) => setToast({ text, ok })
  const closeToast = () => setToast(null)

  const [cfg, setCfg] = React.useState(null)

  // Local state
  const [device, setDevice] = React.useState('gpu')
  const [debug, setDebug] = React.useState(false)
  const [humanOnly, setHumanOnly] = React.useState(false)

  const [matchTh, setMatchTh] = React.useState(0.6)
  const [redCutoff, setRedCutoff] = React.useState(0.4)
  const [boxThick, setBoxThick] = React.useState(6)

  const [detector, setDetector] = React.useState('insightface')
  // 'off' | 'heuristic' | 'heuristic_medium' | 'minifasnet'  (selaras backend)
  const [antispoof, setAntispoof] = React.useState('off')
  const [onnxPath, setOnnxPath] = React.useState('models/antispoof/minifasnet/minifasnet.onnx')

  const [preprocess, setPreprocess] = React.useState('bgr_norm')
  const [liveIndex, setLiveIndex] = React.useState(2)
  const [asMode, setAsMode] = React.useState('medium')
  const [smoothK, setSmoothK] = React.useState(3)
  const [thrLow, setThrLow] = React.useState(0.4)
  const [thrMed, setThrMed] = React.useState(0.55)
  const [thrHigh, setThrHigh] = React.useState(0.7)
  const [minFace, setMinFace] = React.useState(90)
  const [minIO, setMinIO] = React.useState(38)
  const [suppressSmall, setSuppressSmall] = React.useState(true)

  const [logMode, setLogMode] = React.useState('photo')
  const [logWhich, setLogWhich] = React.useState('green')
  const [logInterval, setLogInterval] = React.useState(3)

  const antispoofDisabled = antispoof === 'off'
  const onnxDisabled = antispoof !== 'minifasnet'

  useStableSettingsLayers()

  // Load config
  React.useEffect(() => {
    (async () => {
      try {
        const c = await api.getCfg()
        setCfg(c)
        setDevice(String(c.device || 'CPU').toUpperCase() === 'GPU' ? 'gpu' : 'cpu')
        setDebug(!!c.debug)
        setHumanOnly(!!c.require_human_check)

        setMatchTh(Number(c.match_threshold ?? 0.6))
        setRedCutoff(Number(c.red_cutoff_threshold ?? 0.4))
        setBoxThick(Number(c.box_thickness_max ?? 6))

        setDetector(String(c.detector_backend || 'insightface'))
        setAntispoof(String(c.antispoof_backend || 'off'))
        setOnnxPath(String(c.antispoof_model_path || 'models/antispoof/minifasnet/minifasnet.onnx'))

        setPreprocess(String(c.antispoof_preprocess || 'bgr_norm'))
        setLiveIndex(Number(c.antispoof_live_index ?? 2))
        setAsMode(String(c.antispoof_mode || 'medium'))
        setSmoothK(Number(c.antispoof_smooth_k ?? 3))
        const th = c.antispoof_thresholds || {}
        setThrLow(Number(th.low ?? 0.4))
        setThrMed(Number(th.medium ?? 0.55))
        setThrHigh(Number(th.high ?? 0.7))
        setMinFace(Number(c.min_live_face_size ?? 90))
        setMinIO(Number(c.min_interocular_px ?? 38))
        setSuppressSmall(!!c.suppress_small_faces_when_antispoof)

        setLogMode(String(c.log_save_mode || 'photo'))
        setLogWhich(String(c.log_save_which || 'green'))
        setLogInterval(Number(c.log_interval_sec ?? 3))
      } catch (e) {
        console.error('Load config failed:', e)
        showToast('Failed to load config', false)
      }
    })()
  }, [])

  // Apply handlers
  const applyConfiguration = async () => {
    try {
      const res = await api.putCfg({ device, debug })
      setCfg(res); showToast('Configuration saved ✅', true)
    } catch (e) { console.error(e); showToast('Failed to save configuration ❌', false) }
  }
  const applyFaceRecog = async () => {
    try {
      const res = await api.putCfg({
        match_threshold: matchTh, red_cutoff_threshold: redCutoff,
        require_human_check: humanOnly, box_thickness_max: boxThick,
      })
      setCfg(res); showToast('Face recognition saved ✅', true)
    } catch (e) { console.error(e); showToast('Failed to save face recognition ❌', false) }
  }
  const applyAIModel = async () => {
    try {
      const patch = { detector_backend: detector, antispoof_backend: antispoof }
      if (!onnxDisabled) patch.antispoof_model_path = onnxPath
      const res = await api.putCfg(patch)
      setCfg(res); showToast('AI model saved ✅', true)
    } catch (e) { console.error(e); showToast('Failed to save AI model ❌', false) }
  }
  const applyLogs = async () => {
    try {
      const res = await api.putCfg({
        log_save_mode: logMode, log_save_which: logWhich, log_interval_sec: logInterval,
      })
      setCfg(res); showToast('Log settings saved ✅', true)
    } catch (e) { console.error(e); showToast('Failed to save log settings ❌', false) }
  }
  const applyAntispoof = async () => {
    try {
      const res = await api.putCfg({
        antispoof_preprocess: preprocess, antispoof_live_index: liveIndex, antispoof_mode: asMode,
        antispoof_smooth_k: smoothK,
        antispoof_thresholds: { low: thrLow, medium: thrMed, high: thrHigh },
        min_live_face_size: minFace, min_interocular_px: minIO,
        suppress_small_faces_when_antispoof: suppressSmall,
      })
      setCfg(res); showToast('Anti-spoof saved ✅', true)
    } catch (e) { console.error(e); showToast('Failed to save anti-spoof ❌', false) }
  }

  return (
    <div className="grid settings-page" style={{ gap: 18 }}>
      <HeaderCard title="Settings" subtitle="General and account settings, model, camera, and other adjustment" />

      <Card className="settings-card">
        <div className="grid" style={{ gap: 18 }}>
          {/* Account */}
          <div className="glass-section">
            <div className="section-title">Account</div>
            <div className="grid cols-2" style={{ gap: 14 }}>
              <LockInput label="Username:" defaultValue="supernovajuara1" />
              <LockInput label="Email:" type="email" defaultValue="worldchampionke5@yuhuuu.com" />
              <LockInput label="Password:" type="password" defaultValue="************" />
            </div>
            <div className="actions"><button className="btn-figma btn-logout">Logout</button></div>
          </div>

          {/* Configuration */}
          <div className="glass-section">
            <div className="section-title">Configuration</div>
            <div className="grid cols-2" style={{ gap: 14 }}>
              <DSSelect label="Device" defaultValue={device} options={deviceOptions} onChange={setDevice} />
              <div className="field toggle-row">
                <label className="label">Debug</label>
                <label className="toggle">
                  <input type="checkbox" checked={debug} onChange={e=>setDebug(e.target.checked)} />
                  <span className="switch" />
                </label>
              </div>
            </div>
            <div className="actions">
              <button className="btn-figma" onClick={applyConfiguration}>Apply Changes</button>
              <button className="btn-ghost">Cancel</button>
            </div>
          </div>

          {/* Face Recognition */}
          <div className="glass-section">
            <div className="section-title">Face Recognition</div>
            <div className="grid cols-2" style={{ gap: 14 }}>
              <DSNumber label="Match threshold (0-1)" defaultValue={matchTh} min={0} max={1} step={0.01} onChange={setMatchTh} />
              <DSNumber label="Red cutoff (<)" defaultValue={redCutoff} min={0} max={1} step={0.01} onChange={setRedCutoff} />
              <div className="field toggle-row">
                <label className="label">Require human-only check</label>
                <label className="toggle">
                  <input type="checkbox" checked={humanOnly} onChange={e=>setHumanOnly(e.target.checked)} />
                  <span className="switch" />
                </label>
              </div>
              <DSRange label="Small-face box thickness (max)" min={0} max={10} step={1} defaultValue={boxThick} onChange={setBoxThick} />
            </div>
            <div className="actions">
              <button className="btn-figma" onClick={applyFaceRecog}>Apply Changes</button>
              <button className="btn-ghost">Cancel</button>
            </div>
          </div>

          {/* AI Model */}
          <div className="glass-section">
            <div className="section-title">AI Model</div>
            <div className="grid cols-2" style={{ gap: 14 }}>
              <DSSelect label="Detector backend" defaultValue={detector} options={detectorOptions} onChange={setDetector} />
              <DSSelect label="Anti-Spoof backend" defaultValue={antispoof} options={antispoofBackendOptions} onChange={setAntispoof} />
              <DSFile label="ONNX MiniFASNet" defaultPath={onnxPath} onChange={()=>{}} disabled={onnxDisabled} />
            </div>
            <div className="actions">
              <button className="btn-figma" onClick={applyAIModel}>Apply Changes</button>
              <button className="btn-ghost">Cancel</button>
            </div>
          </div>

          {/* Logs */}
          <div className="glass-section">
            <div className="section-title">Logs</div>
            <div className="grid cols-2" style={{ gap: 14 }}>
              <DSSelect label="Save mode (match)" defaultValue={logMode} options={saveModeOptions} onChange={setLogMode} />
              <DSSelect label="Save which detections" defaultValue={logWhich} options={saveWhichOptions} onChange={setLogWhich} />
              <DSNumber label="Log interval (detik)" defaultValue={logInterval} min={0} step={1} onChange={setLogInterval} />
            </div>
            <div className="actions">
              <button className="btn-figma" onClick={applyLogs}>Apply Changes</button>
              <button className="btn-ghost">Cancel</button>
            </div>
          </div>

          {/* Anti-Spoof */}
          <div className="glass-section">
            <div className="section-title">Anti-spoof</div>

            <div style={antispoofDisabled ? { pointerEvents: 'none', opacity: .55, filter: 'grayscale(8%)' } : undefined}>
              <div className="grid cols-2" style={{ gap: 14 }}>
                <DSSelect label="Preprocess" defaultValue={preprocess} options={preprocessOptions} onChange={setPreprocess} />
                <DSNumber label="Live index (-1=auto)" defaultValue={liveIndex} min={-1} step={1} onChange={setLiveIndex} />
                <DSSelect label="Mode" defaultValue={asMode} options={antispoofModeOptions} onChange={setAsMode} />
                <DSNumber label="Smooth K" defaultValue={smoothK} min={0} step={1} onChange={setSmoothK} />

                <div className="field triple" style={{ gridColumn: '1 / -1' }}>
                  <label className="label">Threshold low/med/high</label>
                  <div className="triple-row" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: 10 }}>
                    <DSNumber defaultValue={thrLow} min={0} max={1} step={0.01} onChange={setThrLow} />
                    <DSNumber defaultValue={thrMed} min={0} max={1} step={0.01} onChange={setThrMed} />
                    <DSNumber defaultValue={thrHigh} min={0} max={1} step={0.01} onChange={setThrHigh} />
                  </div>
                </div>
              </div>

              <div className="grid cols-2" style={{ gap: 14, marginTop: 6 }}>
                <DSNumber label="Min live face size (px)" defaultValue={minFace} min={0} step={1} onChange={setMinFace} />
                <DSNumber label="Min inter-ocular (px)" defaultValue={minIO} min={0} step={1} onChange={setMinIO} />
                <div className="field toggle-row">
                  <label className="label">Suppress small faces</label>
                  <label className="toggle">
                    <input type="checkbox" checked={suppressSmall} onChange={e=>setSuppressSmall(e.target.checked)} />
                    <span className="switch" />
                  </label>
                </div>
              </div>
            </div>

            <div className="actions">
              <button className="btn-figma" onClick={applyAntispoof} disabled={antispoofDisabled}>Apply Changes</button>
              <button className="btn-ghost">Cancel</button>
            </div>
          </div>
        </div>
      </Card>

      {toast && <Toast kind={toast.ok ? 'ok' : 'err'} text={toast.text} onClose={closeToast} />}
    </div>
  )
}
