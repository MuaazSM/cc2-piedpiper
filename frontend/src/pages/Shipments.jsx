import { useState } from 'react'

const SHIPMENTS = [
  { id:'S001', origin:'Mumbai', dest:'Pune',   weight:850,  volume:12, priority:'High',   window:'08:00–14:00', status:'Consolidated', truck:'V001', group:'G1' },
  { id:'S002', origin:'Mumbai', dest:'Pune',   weight:620,  volume: 9, priority:'Medium', window:'07:30–15:00', status:'Consolidated', truck:'V001', group:'G1' },
  { id:'S003', origin:'Pune',   dest:'Delhi',  weight:1100, volume:18, priority:'High',   window:'09:00–20:00', status:'Consolidated', truck:'V004', group:'G2' },
  { id:'S004', origin:'Mumbai', dest:'Delhi',  weight:450,  volume: 7, priority:'Low',    window:'10:00–22:00', status:'Standalone',   truck:'V003', group:'G3' },
  { id:'S005', origin:'Mumbai', dest:'Pune',   weight:300,  volume: 5, priority:'Medium', window:'08:00–16:00', status:'Consolidated', truck:'V001', group:'G1' },
  { id:'S006', origin:'Pune',   dest:'Delhi',  weight:780,  volume:11, priority:'Medium', window:'10:00–21:00', status:'Consolidated', truck:'V004', group:'G2' },
]

const TRUCKS = [
  { id:'V001', route:'Mumbai → Pune',  shipments:['S001','S002','S005'], util:91, cap:2000, load:1770, color:'var(--page-accent)' },
  { id:'V003', route:'Mumbai → Delhi', shipments:['S004'],               util:32, cap:1500, load:450,  color:'#06b6d4' },
  { id:'V004', route:'Pune → Delhi',   shipments:['S003','S006'],        util:97, cap:2000, load:1880, color:'#10b981' },
]

const GROUP_COLORS = { G1:'var(--page-accent)', G2:'#10b981', G3:'#06b6d4' }
const PRIORITY_COLORS = { High:'#ef4444', Medium:'var(--page-accent)', Low:'#6b7280' }

export default function Shipments() {
  const [filter,   setFilter]   = useState('All')
  const [selected, setSelected] = useState(null)
  const [view,     setView]     = useState('list') // list | map

  const lanes = ['All', 'Mumbai → Pune', 'Pune → Delhi', 'Mumbai → Delhi']

  const filtered = filter === 'All'
    ? SHIPMENTS
    : SHIPMENTS.filter(s => `${s.origin} → ${s.dest}` === filter)

  const selShipment = SHIPMENTS.find(s => s.id === selected)
  const selTruck    = selShipment ? TRUCKS.find(t => t.id === selShipment.truck) : null

  return (
    <div className="lorri-shipments">
      <style>{`
        .lorri-shipments {
          min-height: 100vh; display: flex; flex-direction: column;
          position: relative; overflow-x: clip;
        }
        .lorri-shipments::before {
          content: '';
          position: fixed; inset: 0; z-index: 0;
          background-image: radial-gradient(circle, rgba(var(--page-glow-rgb), 0.18) 1px, transparent 1px);
          background-size: 32px 32px; pointer-events: none;
          mask-image: radial-gradient(ellipse 80% 80% at 50% 50%, black 30%, transparent 100%);
        }
        .shp-inner {
          position: relative; z-index: 1;
          max-width: 1160px; margin: 0 auto;
          padding: 5rem 3rem 6rem; width: 100%;
        }

        /* ── Hero ── */
        .shp-hero {
          display: grid; grid-template-columns: 1fr auto;
          align-items: flex-end; gap: 2rem;
          margin-bottom: 3rem; padding-bottom: 2.5rem;
          border-bottom: 1px solid var(--border);
        }
        .shp-hero-tag {
          display: inline-flex; align-items: center; gap: 6px;
          padding: 5px 14px; border-radius: 9999px;
          border: 1px solid rgba(var(--page-glow-rgb), 0.45);
          background: rgba(var(--page-glow-rgb), 0.1);
          font-size: 0.7rem; font-family: 'JetBrains Mono', monospace;
          color: var(--page-accent); letter-spacing: 0.12em; text-transform: uppercase;
          margin-bottom: 1rem;
          opacity: 0; animation: fadeSlideUp 0.45s ease 0.05s forwards;
        }
        .shp-hero h1 {
          font-family: 'Syne', sans-serif;
          font-size: clamp(2.2rem, 4vw, 3.8rem);
          font-weight: 800; line-height: 1.04; letter-spacing: -0.025em;
          margin-bottom: 0.8rem;
        }
        .shp-hero-sub {
          font-size: 0.95rem; color: var(--text-secondary); line-height: 1.7;
          opacity: 0; animation: fadeSlideUp 0.45s ease 0.55s forwards;
        }
        .shp-hero-right {
          text-align: right;
          opacity: 0; animation: fadeSlideUp 0.45s ease 0.65s forwards;
        }
        .shp-hero-num {
          font-family: 'Syne', sans-serif; font-size: 2.8rem; font-weight: 800;
          color: var(--page-accent); line-height: 1;
        }
        .shp-hero-lbl {
          font-size: 0.72rem; color: var(--text-muted);
          font-family: 'JetBrains Mono', monospace;
          text-transform: uppercase; letter-spacing: 0.1em; margin-top: 4px;
        }

        /* ── Stat bar ── */
        .shp-stats {
          display: grid; grid-template-columns: repeat(4,1fr);
          border: 1px solid var(--border); border-radius: 16px;
          overflow: hidden; margin-bottom: 2rem;
          opacity: 0; animation: fadeSlideUp 0.45s ease 0.3s forwards;
        }
        .shp-stat-cell {
          padding: 1.4rem 1.5rem;
          border-right: 1px solid var(--border);
          position: relative; overflow: hidden; transition: background 0.2s;
        }
        .shp-stat-cell:last-child { border-right: none; }
        .shp-stat-cell:hover { background: rgba(var(--page-glow-rgb), 0.04); }
        .shp-stat-cell::after {
          content: ''; position: absolute; bottom:0; left:0; right:0;
          height: 2px;
          background: linear-gradient(90deg, transparent, var(--page-accent), transparent);
          transform: scaleX(0); transition: transform 0.35s;
        }
        .shp-stat-cell:hover::after { transform: scaleX(1); }
        .shp-stat-val {
          font-family: 'Syne', sans-serif; font-size: 1.8rem; font-weight: 800;
          color: var(--page-accent); line-height: 1; margin-bottom: 3px;
        }
        .shp-stat-lbl {
          font-size: 0.72rem; color: var(--text-muted);
          font-family: 'JetBrains Mono', monospace;
          text-transform: uppercase; letter-spacing: 0.08em;
        }

        /* ── Toolbar ── */
        .shp-toolbar {
          display: flex; align-items: center; gap: 0.75rem;
          margin-bottom: 1.5rem; flex-wrap: wrap;
          opacity: 0; animation: fadeSlideUp 0.45s ease 0.4s forwards;
        }
        .shp-filter-btn {
          padding: 6px 14px; border-radius: 9999px; border: none;
          font-size: 0.72rem; font-family: 'JetBrains Mono', monospace;
          letter-spacing: 0.08em; cursor: pointer; transition: all 0.2s;
        }
        .shp-filter-btn.active {
          background: var(--page-accent); color: #0a0a0a; font-weight: 700;
          box-shadow: 0 0 16px rgba(var(--page-glow-rgb), 0.4);
        }
        .shp-filter-btn:not(.active) {
          background: rgba(var(--page-glow-rgb), 0.06);
          border: 1px solid rgba(var(--page-glow-rgb), 0.2);
          color: var(--text-muted);
        }
        .shp-filter-btn:not(.active):hover {
          border-color: var(--page-accent); color: var(--page-accent);
        }
        .shp-view-toggle {
          margin-left: auto; display: flex; gap: 0.4rem;
        }
        .shp-view-btn {
          padding: 6px 12px; border-radius: 8px; border: none;
          font-size: 0.7rem; font-family: 'JetBrains Mono', monospace;
          cursor: pointer; transition: all 0.2s;
          text-transform: uppercase; letter-spacing: 0.08em;
        }
        .shp-view-btn.active {
          background: rgba(var(--page-glow-rgb), 0.15);
          border: 1px solid rgba(var(--page-glow-rgb), 0.35);
          color: var(--page-accent);
        }
        .shp-view-btn:not(.active) {
          background: transparent;
          border: 1px solid var(--border);
          color: var(--text-muted);
        }

        /* ── Main layout ── */
        .shp-main {
          display: grid; grid-template-columns: 1.8fr 1fr;
          gap: 1.5rem; align-items: start;
        }

        /* ── Table ── */
        .shp-table-wrap {
          background: var(--card); border: 1px solid var(--border);
          border-radius: 18px; overflow: hidden;
          opacity: 0; animation: fadeSlideUp 0.5s ease 0.45s forwards;
        }
        .shp-table-header {
          padding: 1.1rem 1.25rem; border-bottom: 1px solid var(--border);
          display: flex; align-items: center; justify-content: space-between;
        }
        .shp-table-header-label {
          font-size: 0.68rem; font-family: 'JetBrains Mono', monospace;
          color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.12em;
        }
        .shp-count-badge {
          font-size: 0.65rem; padding: 2px 8px; border-radius: 5px;
          font-family: 'JetBrains Mono', monospace;
          background: rgba(var(--page-glow-rgb), 0.1);
          border: 1px solid rgba(var(--page-glow-rgb), 0.3);
          color: var(--page-accent);
        }
        .shp-table { width: 100%; border-collapse: collapse; }
        .shp-table th {
          padding: 0.7rem 1.1rem;
          font-size: 0.62rem; font-family: 'JetBrains Mono', monospace;
          text-transform: uppercase; letter-spacing: 0.1em;
          color: var(--text-muted); text-align: left;
          border-bottom: 1px solid var(--border);
        }
        .shp-table td {
          padding: 0.85rem 1.1rem; font-size: 0.82rem;
          border-bottom: 1px solid rgba(255,255,255,0.04);
          cursor: pointer; transition: background 0.15s;
        }
        .shp-table tr:last-child td { border-bottom: none; }
        .shp-table tr:hover td { background: rgba(var(--page-glow-rgb), 0.04); }
        .shp-table tr.row-selected td {
          background: rgba(var(--page-glow-rgb), 0.07);
        }
        .shp-id-cell {
          font-family: 'JetBrains Mono', monospace; font-weight: 700;
        }
        .shp-group-dot {
          width: 7px; height: 7px; border-radius: 50%;
          display: inline-block; margin-right: 6px;
          vertical-align: middle;
        }
        .shp-priority-badge {
          font-size: 0.6rem; padding: 2px 7px; border-radius: 4px;
          font-family: 'JetBrains Mono', monospace;
          text-transform: uppercase; letter-spacing: 0.06em;
        }
        .shp-status-badge {
          font-size: 0.6rem; padding: 2px 7px; border-radius: 4px;
          font-family: 'JetBrains Mono', monospace;
          text-transform: uppercase; letter-spacing: 0.06em;
        }

        /* ── Side panel ── */
        .shp-side { display: flex; flex-direction: column; gap: 1.25rem; }

        /* Fleet cards */
        .shp-fleet-wrap {
          opacity: 0; animation: fadeSlideUp 0.5s ease 0.5s forwards;
        }
        .shp-section-divider {
          display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.9rem;
        }
        .shp-divider-label {
          font-size: 0.68rem; font-family: 'JetBrains Mono', monospace;
          color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.14em;
          white-space: nowrap;
        }
        .shp-divider-line { flex: 1; height: 1px; background: var(--border); }
        .shp-truck-cards { display: flex; flex-direction: column; gap: 0.6rem; }
        .shp-truck-card {
          background: var(--card); border: 1px solid var(--border);
          border-radius: 14px; padding: 1rem 1.1rem;
          transition: border-color 0.2s, box-shadow 0.2s;
        }
        .shp-truck-card:hover {
          border-color: rgba(var(--page-glow-rgb), 0.35);
          box-shadow: 0 0 20px rgba(var(--page-glow-rgb), 0.08);
        }
        .shp-truck-header {
          display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.75rem;
        }
        .shp-truck-id {
          font-family: 'Syne', sans-serif; font-size: 0.88rem; font-weight: 700; flex: 1;
        }
        .shp-truck-util {
          font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; font-weight: 700;
        }
        .shp-truck-bar-track {
          height: 5px; border-radius: 9999px;
          background: rgba(255,255,255,0.05); overflow: hidden; margin-bottom: 0.6rem;
        }
        .shp-truck-bar-fill { height: 100%; border-radius: 9999px; }
        .shp-truck-route {
          font-size: 0.68rem; font-family: 'JetBrains Mono', monospace;
          color: var(--text-muted);
        }
        .shp-truck-shipments {
          display: flex; gap: 0.35rem; margin-top: 0.5rem; flex-wrap: wrap;
        }
        .shp-truck-ship-tag {
          font-size: 0.6rem; padding: 2px 6px; border-radius: 4px;
          font-family: 'JetBrains Mono', monospace;
        }

        /* Drawer panel */
        .shp-drawer {
          background: var(--card); border: 1px solid var(--border);
          border-radius: 16px; overflow: hidden;
          opacity: 0; animation: fadeSlideUp 0.35s ease forwards;
        }
        .shp-drawer-header {
          padding: 1.1rem 1.25rem; border-bottom: 1px solid var(--border);
          display: flex; align-items: center; justify-content: space-between;
        }
        .shp-drawer-title {
          font-family: 'Syne', sans-serif; font-size: 1rem; font-weight: 700;
        }
        .shp-drawer-close {
          background: none; border: none; cursor: pointer;
          color: var(--text-muted); font-size: 1rem; line-height: 1;
          transition: color 0.2s; padding: 0;
        }
        .shp-drawer-close:hover { color: var(--page-accent); }
        .shp-drawer-body { padding: 1.1rem 1.25rem; }
        .shp-detail-row {
          display: flex; justify-content: space-between;
          padding: 0.6rem 0; border-bottom: 1px solid rgba(255,255,255,0.04);
          font-size: 0.82rem;
        }
        .shp-detail-row:last-child { border-bottom: none; }
        .shp-detail-key {
          font-family: 'JetBrains Mono', monospace; font-size: 0.68rem;
          color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.08em;
        }
        .shp-detail-val { color: var(--text-secondary); }

        /* Map placeholder */
        .shp-map-placeholder {
          background: var(--card); border: 1px solid var(--border);
          border-radius: 18px; overflow: hidden;
          opacity: 0; animation: fadeSlideUp 0.5s ease 0.45s forwards;
        }
        .shp-map-header {
          padding: 1.1rem 1.25rem; border-bottom: 1px solid var(--border);
          display: flex; align-items: center; justify-content: space-between;
        }

        @keyframes fadeSlideUp {
          from { opacity: 0; transform: translateY(16px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        .blur-line { display: flex; flex-wrap: wrap; gap: 0.22em; }
        .blur-word {
          display: inline-block; opacity: 0;
          filter: blur(16px); transform: translateX(-14px);
          animation: blurWordIn 0.6s cubic-bezier(0.22,1,0.36,1) forwards;
        }
        @keyframes blurWordIn {
          0%   { opacity:0; filter:blur(16px); transform:translateX(-14px); }
          55%  { opacity:0.9; filter:blur(2px); transform:translateX(2px); }
          100% { opacity:1; filter:blur(0); transform:translateX(0); }
        }
      `}</style>

      <div className="shp-inner">

        {/* ════ HERO ════ */}
        <div className="shp-hero">
          <div>
            <div className="shp-hero-tag">
              <svg viewBox="0 0 24 24" width="10" height="10" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/><circle cx="12" cy="9" r="2.5"/></svg>
              Leaflet Map · Live Routes
            </div>
            <h1>
              <div className="blur-line">
                {['Shipment'].map((w, i) => (
                  <span key={w} className="blur-word" style={{ animationDelay: `${0.1 + i * 0.1}s` }}>{w}</span>
                ))}
              </div>
              <div className="blur-line" style={{ color: 'var(--page-accent)' }}>
                {['Visibility.'].map((w, i) => (
                  <span key={w} className="blur-word" style={{ animationDelay: `${0.22 + i * 0.12}s` }}>{w}</span>
                ))}
              </div>
            </h1>
            <p className="shp-hero-sub">
              Every origin–destination pair visualised with route colour-coding by consolidation group. Click any shipment for full details and truck assignment.
            </p>
          </div>
          <div className="shp-hero-right">
            <div className="shp-hero-num">6</div>
            <div className="shp-hero-lbl">Shipments</div>
          </div>
        </div>

        {/* ── Stats bar ── */}
        <div className="shp-stats">
          {[
            { val: '6',    lbl: 'Total Shipments' },
            { val: '3',    lbl: 'Trucks Assigned' },
            { val: '4100 kg', lbl: 'Total Weight' },
            { val: '76%',  lbl: 'Avg Utilization' },
          ].map(({ val, lbl }) => (
            <div key={lbl} className="shp-stat-cell">
              <div className="shp-stat-val">{val}</div>
              <div className="shp-stat-lbl">{lbl}</div>
            </div>
          ))}
        </div>

        {/* ── Toolbar ── */}
        <div className="shp-toolbar">
          {lanes.map(lane => (
            <button
              key={lane}
              className={`shp-filter-btn ${filter === lane ? 'active' : ''}`}
              onClick={() => { setFilter(lane); setSelected(null) }}
            >
              {lane}
            </button>
          ))}
          <div className="shp-view-toggle">
            {[['list', 'List'], ['map', 'Map']].map(([v, l]) => (
              <button key={v} className={`shp-view-btn ${view === v ? 'active' : ''}`} onClick={() => setView(v)}>{l}</button>
            ))}
          </div>
        </div>

        {/* ════ MAIN ════ */}
        <div className="shp-main">

          {/* ── List / Map view ── */}
          {view === 'list' ? (
            <div className="shp-table-wrap">
              <div className="shp-table-header">
                <span className="shp-table-header-label">/ shipments · {filtered.length} records</span>
                <span className="shp-count-badge">{filtered.length}</span>
              </div>
              <table className="shp-table">
                <thead>
                  <tr>
                    {['ID', 'Route', 'Weight', 'Priority', 'Window', 'Status', 'Truck'].map(h => (
                      <th key={h}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filtered.map(s => (
                    <tr
                      key={s.id}
                      className={selected === s.id ? 'row-selected' : ''}
                      onClick={() => setSelected(selected === s.id ? null : s.id)}
                    >
                      <td>
                        <span className="shp-id-cell" style={{ color: GROUP_COLORS[s.group] }}>
                          <span className="shp-group-dot" style={{ background: GROUP_COLORS[s.group] }} />
                          {s.id}
                        </span>
                      </td>
                      <td style={{ fontFamily: 'JetBrains Mono', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                        {s.origin} → {s.dest}
                      </td>
                      <td style={{ fontFamily: 'JetBrains Mono', fontSize: '0.75rem', color: 'var(--text-muted)' }}>{s.weight} kg</td>
                      <td>
                        <span className="shp-priority-badge" style={{
                          background: `${PRIORITY_COLORS[s.priority]}18`,
                          border: `1px solid ${PRIORITY_COLORS[s.priority]}30`,
                          color: PRIORITY_COLORS[s.priority],
                        }}>
                          {s.priority}
                        </span>
                      </td>
                      <td style={{ fontFamily: 'JetBrains Mono', fontSize: '0.72rem', color: 'var(--text-muted)' }}>{s.window}</td>
                      <td>
                        <span className="shp-status-badge" style={{
                          background: s.status === 'Consolidated' ? 'rgba(var(--page-glow-rgb),0.1)' : 'rgba(6,182,212,0.1)',
                          border: `1px solid ${s.status === 'Consolidated' ? 'rgba(var(--page-glow-rgb),0.3)' : 'rgba(6,182,212,0.3)'}`,
                          color: s.status === 'Consolidated' ? 'var(--page-accent)' : '#06b6d4',
                        }}>
                          {s.status}
                        </span>
                      </td>
                      <td style={{ fontFamily: 'JetBrains Mono', fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: 700 }}>{s.truck}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="shp-map-placeholder">
              <div className="shp-map-header">
                <span style={{ fontSize: '0.68rem', fontFamily: 'JetBrains Mono', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.12em' }}>/ route map · leaflet</span>
                <span style={{ fontSize: '0.65rem', fontFamily: 'JetBrains Mono', color: 'var(--page-accent)', borderRadius: 5, padding: '2px 8px', background: 'rgba(var(--page-glow-rgb),0.1)', border: '1px solid rgba(var(--page-glow-rgb),0.3)' }}>Live</span>
              </div>
              <div style={{ padding: '1rem', position: 'relative', height: '480px' }}>
                {/* SVG map mockup */}
                <svg viewBox="0 0 560 420" width="100%" height="100%" fill="none">
                  {/* Grid */}
                  {[0,1,2,3,4,5].map(i => <line key={`h${i}`} x1="0" y1={i*84} x2="560" y2={i*84} stroke="rgba(255,255,255,0.04)" strokeWidth="1"/>)}
                  {[0,1,2,3,4,5,6].map(i => <line key={`v${i}`} x1={i*93} y1="0" x2={i*93} y2="420" stroke="rgba(255,255,255,0.04)" strokeWidth="1"/>)}

                  {/* Routes */}
                  {/* G1: Mumbai→Pune (amber) */}
                  <line x1="100" y1="300" x2="220" y2="200" stroke="var(--page-accent)" strokeWidth="2.5" strokeDasharray="6,3" opacity="0.9"/>
                  <line x1="100" y1="300" x2="220" y2="200" stroke="var(--page-accent)" strokeWidth="2.5" strokeDasharray="6,3" opacity="0.4" transform="translate(6,6)"/>
                  <line x1="100" y1="300" x2="220" y2="200" stroke="var(--page-accent)" strokeWidth="2.5" strokeDasharray="6,3" opacity="0.25" transform="translate(-5,-5)"/>

                  {/* G2: Pune→Delhi (green) */}
                  <line x1="220" y1="200" x2="420" y2="80" stroke="#10b981" strokeWidth="2" strokeDasharray="5,4" opacity="0.85"/>
                  <line x1="220" y1="200" x2="420" y2="80" stroke="#10b981" strokeWidth="2" strokeDasharray="5,4" opacity="0.35" transform="translate(7,4)"/>

                  {/* G3: Mumbai→Delhi (cyan) */}
                  <line x1="100" y1="300" x2="420" y2="80" stroke="#06b6d4" strokeWidth="1.5" strokeDasharray="4,5" opacity="0.7"/>

                  {/* Glow halos */}
                  <circle cx="100" cy="300" r="16" fill="rgba(var(--page-glow-rgb),0.07)" stroke="none"/>
                  <circle cx="220" cy="200" r="16" fill="rgba(16,185,129,0.07)" stroke="none"/>
                  <circle cx="420" cy="80"  r="16" fill="rgba(6,182,212,0.07)" stroke="none"/>

                  {/* City nodes */}
                  {[
                    [100, 300, 'Mumbai'],
                    [220, 200, 'Pune'],
                    [420, 80,  'Delhi'],
                  ].map(([cx, cy, name]) => (
                    <g key={name}>
                      <circle cx={cx} cy={cy} r="9" fill="#0a0a0a" stroke="var(--page-accent)" strokeWidth="2"/>
                      <circle cx={cx} cy={cy} r="3.5" fill="var(--page-accent)"/>
                      <text x={cx} y={cy - 16} textAnchor="middle" fill="var(--text-muted)" fontSize="10" fontFamily="JetBrains Mono, monospace" letterSpacing="0.08em">{name}</text>
                    </g>
                  ))}

                  {/* Shipment dots on routes */}
                  {[[145, 260, 'S001'], [162, 248, 'S002'], [183, 233, 'S005']].map(([x,y,id]) => (
                    <g key={id}>
                      <circle cx={x} cy={y} r="5" fill="var(--page-accent)" opacity="0.8"/>
                      <text x={x+7} y={y+4} fontSize="7" fill="var(--page-accent)" fontFamily="JetBrains Mono" opacity="0.7">{id}</text>
                    </g>
                  ))}
                  {[[290, 160, 'S003'], [310, 148, 'S006']].map(([x,y,id]) => (
                    <g key={id}>
                      <circle cx={x} cy={y} r="5" fill="#10b981" opacity="0.8"/>
                      <text x={x+7} y={y+4} fontSize="7" fill="#10b981" fontFamily="JetBrains Mono" opacity="0.7">{id}</text>
                    </g>
                  ))}
                  {[[230, 215, 'S004']].map(([x,y,id]) => (
                    <g key={id}>
                      <circle cx={x} cy={y} r="5" fill="#06b6d4" opacity="0.8"/>
                      <text x={x+7} y={y+4} fontSize="7" fill="#06b6d4" fontFamily="JetBrains Mono" opacity="0.7">{id}</text>
                    </g>
                  ))}
                </svg>

                {/* Legend */}
                <div style={{ position: 'absolute', bottom: 16, left: 16, display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
                  {[['var(--page-accent)','G1 · S001+S002+S005'],['#10b981','G2 · S003+S006'],['#06b6d4','G3 · S004']].map(([c,l]) => (
                    <div key={l} style={{ display:'flex', alignItems:'center', gap:5, fontSize:'0.62rem', fontFamily:'JetBrains Mono', color:'var(--text-muted)', background:'rgba(0,0,0,0.5)', padding:'3px 8px', borderRadius:5, border:'1px solid rgba(255,255,255,0.08)' }}>
                      <span style={{ width:12, height:2, background:c, borderRadius:1, display:'inline-block' }}/>
                      {l}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* ── Side panel ── */}
          <div className="shp-side">

            {/* Shipment drawer */}
            {selShipment && (
              <div className="shp-drawer">
                <div className="shp-drawer-header">
                  <span className="shp-drawer-title" style={{ color: GROUP_COLORS[selShipment.group] }}>
                    {selShipment.id}
                  </span>
                  <button className="shp-drawer-close" onClick={() => setSelected(null)}>✕</button>
                </div>
                <div className="shp-drawer-body">
                  {[
                    ['Route',    `${selShipment.origin} → ${selShipment.dest}`],
                    ['Weight',   `${selShipment.weight} kg`],
                    ['Volume',   `${selShipment.volume} m³`],
                    ['Priority', selShipment.priority],
                    ['Window',   selShipment.window],
                    ['Status',   selShipment.status],
                    ['Truck',    selShipment.truck],
                    ['Group',    selShipment.group],
                  ].map(([k, v]) => (
                    <div key={k} className="shp-detail-row">
                      <span className="shp-detail-key">{k}</span>
                      <span className="shp-detail-val">{v}</span>
                    </div>
                  ))}
                  {selTruck && (
                    <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid var(--border)' }}>
                      <div style={{ fontSize: '0.68rem', fontFamily: 'JetBrains Mono', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '0.5rem' }}>Truck Details</div>
                      <div style={{ background: `${selTruck.color}10`, border: `1px solid ${selTruck.color}25`, borderRadius: 10, padding: '0.7rem' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
                          <span style={{ fontFamily: 'Syne, sans-serif', fontWeight: 700, fontSize: '0.88rem' }}>{selTruck.id}</span>
                          <span style={{ fontFamily: 'JetBrains Mono', fontSize: '0.75rem', fontWeight: 700, color: selTruck.color }}>{selTruck.util}%</span>
                        </div>
                        <div style={{ height: 4, borderRadius: 9999, background: 'rgba(255,255,255,0.05)', overflow: 'hidden' }}>
                          <div style={{ width: `${selTruck.util}%`, height: '100%', background: selTruck.color, borderRadius: 9999 }} />
                        </div>
                        <div style={{ fontSize: '0.65rem', fontFamily: 'JetBrains Mono', color: 'var(--text-muted)', marginTop: '0.35rem' }}>{selTruck.load} / {selTruck.cap} kg</div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Fleet utilization */}
            <div className="shp-fleet-wrap">
              <div className="shp-section-divider">
                <span className="shp-divider-label">— Fleet Utilization</span>
                <div className="shp-divider-line" />
              </div>
              <div className="shp-truck-cards">
                {TRUCKS.map(t => (
                  <div key={t.id} className="shp-truck-card">
                    <div className="shp-truck-header">
                      <div style={{ width: 8, height: 8, borderRadius: '50%', background: t.color, boxShadow: `0 0 6px ${t.color}`, flexShrink: 0 }} />
                      <div className="shp-truck-id">{t.id}</div>
                      <div className="shp-truck-util" style={{ color: t.color }}>{t.util}%</div>
                    </div>
                    <div className="shp-truck-bar-track">
                      <div className="shp-truck-bar-fill" style={{ width: `${t.util}%`, background: `linear-gradient(90deg, ${t.color}88, ${t.color})` }} />
                    </div>
                    <div className="shp-truck-route">{t.route} · {t.load}/{t.cap} kg</div>
                    <div className="shp-truck-shipments">
                      {t.shipments.map(sid => (
                        <span
                          key={sid}
                          className="shp-truck-ship-tag"
                          style={{
                            background: `${t.color}15`,
                            border: `1px solid ${t.color}30`,
                            color: t.color,
                            cursor: 'pointer',
                          }}
                          onClick={() => setSelected(sid)}
                        >
                          {sid}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}