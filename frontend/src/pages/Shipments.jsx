<<<<<<< HEAD
import { useState } from 'react'

=======
import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import Navbar from '@/components/layout/Navbar'
import { MapPin } from 'lucide-react'

/* ─────────────────────────────────────────────
   ✏️ EDIT: Shipment & truck data
───────────────────────────────────────────── */
>>>>>>> d25832fc965b848f9b673c6db0faa45a90052318
const SHIPMENTS = [
  { id:'S001', origin:'Mumbai', dest:'Pune',   weight:850,  volume:12, priority:'High',   window:'08:00–14:00', status:'Consolidated', truck:'V001', group:'G1' },
  { id:'S002', origin:'Mumbai', dest:'Pune',   weight:620,  volume: 9, priority:'Medium', window:'07:30–15:00', status:'Consolidated', truck:'V001', group:'G1' },
  { id:'S003', origin:'Pune',   dest:'Delhi',  weight:1100, volume:18, priority:'High',   window:'09:00–20:00', status:'Consolidated', truck:'V004', group:'G2' },
  { id:'S004', origin:'Mumbai', dest:'Delhi',  weight:450,  volume: 7, priority:'Low',    window:'10:00–22:00', status:'Standalone',   truck:'V003', group:'G3' },
  { id:'S005', origin:'Mumbai', dest:'Pune',   weight:300,  volume: 5, priority:'Medium', window:'08:00–16:00', status:'Consolidated', truck:'V001', group:'G1' },
  { id:'S006', origin:'Pune',   dest:'Delhi',  weight:780,  volume:11, priority:'Medium', window:'10:00–21:00', status:'Consolidated', truck:'V004', group:'G2' },
]

const TRUCKS = [
<<<<<<< HEAD
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

=======
  { id:'V001', route:'Mumbai → Pune',  shipments:['S001','S002','S005'], util:91, load:1770, cap:2000, color:'#f59e0b' },
  { id:'V003', route:'Mumbai → Delhi', shipments:['S004'],               util:32, load:450,  cap:1500, color:'#06b6d4' },
  { id:'V004', route:'Pune → Delhi',   shipments:['S003','S006'],        util:97, load:1880, cap:2000, color:'#10b981' },
]

/* ✏️ EDIT: Stats bar — 4 numbers shown at the top */
const STATS = [
  { num: '6',      label: 'Total Shipments', sub: 'this batch'       },
  { num: '3',      label: 'Trucks Assigned', sub: 'MIP solution'     },
  { num: '4,100kg',label: 'Total Weight',    sub: 'all lanes'        },
  { num: '76%',    label: 'Avg Utilization', sub: 'across fleet'     },
]

/* ✏️ EDIT: Lane filter pills */
const LANES = ['All', 'Mumbai → Pune', 'Pune → Delhi', 'Mumbai → Delhi']

/* ✏️ EDIT: Arc routes for the globe */
const ARCS = [
  { startLat:19.076,  startLng:72.8777, endLat:18.5204, endLng:73.8567, color:'#f59e0b', label:'G1 · V001 · Mumbai→Pune',  ids:['S001','S002','S005'] },
  { startLat:18.5204, startLng:73.8567, endLat:28.6139, endLng:77.209,  color:'#10b981', label:'G2 · V004 · Pune→Delhi',   ids:['S003','S006'] },
  { startLat:19.076,  startLng:72.8777, endLat:28.6139, endLng:77.209,  color:'#06b6d4', label:'G3 · V003 · Mumbai→Delhi', ids:['S004'] },
]

const CITIES = {
  Mumbai: { lat: 19.076,  lng: 72.8777, color: '#f59e0b' },
  Pune:   { lat: 18.5204, lng: 73.8567, color: '#10b981' },
  Delhi:  { lat: 28.6139, lng: 77.209,  color: '#06b6d4' },
}

const GROUP_COLORS    = { G1:'#f59e0b', G2:'#10b981', G3:'#06b6d4' }
const PRIORITY_COLORS = { High:'#ef4444', Medium:'#f59e0b', Low:'#6b7280' }

function hexToRgb(hex) {
  return `${parseInt(hex.slice(1,3),16)},${parseInt(hex.slice(3,5),16)},${parseInt(hex.slice(5,7),16)}`
}

/* ─────────────────────────────────────────────
   Globe component — lazy loads globe.gl
   ✏️ EDIT: pointOfView lat/lng/altitude to reposition the camera
───────────────────────────────────────────── */
function GlobeMap({ filter }) {
  const containerRef = useRef(null)
  const globeRef     = useRef(null)

  useEffect(() => {
    if (!containerRef.current) return
    let cancelled = false

    import('globe.gl').then(({ default: Globe }) => {
      if (cancelled || !containerRef.current) return
      containerRef.current.innerHTML = ''

      const activeArcs = filter === 'All'
        ? ARCS
        : ARCS.filter(a => a.label.includes(filter.replace(' → ', '→')))

      const cityPoints = Object.entries(CITIES).map(([name, c]) => ({ name, ...c }))

      const g = Globe({ animateIn: true })(containerRef.current)
        /* ✏️ EDIT: swap these image URLs for different globe textures */
        .globeImageUrl('//unpkg.com/three-globe/example/img/earth-dark.jpg')
        .bumpImageUrl('//unpkg.com/three-globe/example/img/earth-topology.png')
        .backgroundImageUrl('//unpkg.com/three-globe/example/img/night-sky.png')
        .width(containerRef.current.offsetWidth || 900)
        .height(520)
        /* ✏️ EDIT: camera start position */
        .pointOfView({ lat: 22, lng: 78, altitude: 1.6 }, 0)
        /* Arc routes */
        .arcsData(activeArcs)
        .arcStartLat(d => d.startLat).arcStartLng(d => d.startLng)
        .arcEndLat(d => d.endLat).arcEndLng(d => d.endLng)
        .arcColor(d => [d.color, d.color])
        .arcAltitude(0.25)
        .arcStroke(1.2)
        .arcDashLength(0.4).arcDashGap(0.15).arcDashAnimateTime(2200)
        .arcLabel(d => `<div style="background:#0d0d12;border:1px solid ${d.color}55;border-radius:8px;padding:8px 12px;font-family:'JetBrains Mono',monospace;font-size:0.72rem;color:${d.color}">${d.label}</div>`)
        /* City dots */
        .pointsData(cityPoints)
        .pointLat(d => d.lat).pointLng(d => d.lng)
        .pointColor(d => d.color).pointAltitude(0.01).pointRadius(0.5)
        .pointLabel(d => `<div style="background:#0d0d12;border:1px solid ${d.color}55;border-radius:6px;padding:5px 10px;font-family:'JetBrains Mono',monospace;font-size:0.72rem;color:${d.color}">📍 ${d.name}</div>`)
        /* Pulse rings */
        .ringsData(cityPoints)
        .ringLat(d => d.lat).ringLng(d => d.lng)
        .ringColor(d => t => `rgba(${hexToRgb(d.color)},${1 - t})`)
        .ringMaxRadius(3).ringPropagationSpeed(1.5).ringRepeatPeriod(1500)

      /* ✏️ EDIT: auto-rotate speed (0 = off) */
      g.controls().autoRotate = true
      g.controls().autoRotateSpeed = 0.4
      g.controls().enableZoom = true

      globeRef.current = g
    }).catch(() => {})

    return () => {
      cancelled = true
    }
  }, [filter])

  return (
    <div ref={containerRef}
      style={{ width:'100%', height:'520px', background:'#060609', cursor:'grab' }}
    />
  )
}

/* ═══════════════════════════════════════════
   Main page — structure mirrors Home exactly
═══════════════════════════════════════════ */
export default function Shipments() {
  const nav = useNavigate()
  const [filter,   setFilter]   = useState('All')
  const [selected, setSelected] = useState(null)

  const filtered    = filter === 'All' ? SHIPMENTS : SHIPMENTS.filter(s => `${s.origin} → ${s.dest}` === filter)
>>>>>>> d25832fc965b848f9b673c6db0faa45a90052318
  const selShipment = SHIPMENTS.find(s => s.id === selected)
  const selTruck    = selShipment ? TRUCKS.find(t => t.id === selShipment.truck) : null

  return (
<<<<<<< HEAD
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
=======
    <div className="lorri-page">
      <style>{`
        /* ─── Base (same as Home) ─── */
        .lorri-page {
          min-height: 100vh;
          display: flex;
          flex-direction: column;
          position: relative;
          overflow-x: clip;
        }

        /* ─── Dot grid texture (identical to Home) ─── */
        .lorri-page::before {
          content: '';
          position: fixed;
          inset: 0;
          z-index: 0;
          background-image: radial-gradient(circle, rgba(var(--page-glow-rgb), 0.18) 1px, transparent 1px);
          background-size: 32px 32px;
          pointer-events: none;
          mask-image: radial-gradient(ellipse 80% 80% at 50% 50%, black 30%, transparent 100%);
        }

        /* ─── Hero (identical classes to Home) ─── */
        .hero-wrap {
          min-height: 55vh;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          text-align: center;
          padding: 8rem 2rem 5rem;
          position: relative;
          z-index: 1;
        }
        .hero-tag {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 5px 14px;
          border-radius: 9999px;
          border: 1px solid rgba(var(--page-glow-rgb), 0.45);
          background: rgba(var(--page-glow-rgb), 0.1);
          font-size: 0.7rem;
          font-family: 'JetBrains Mono', monospace;
          color: var(--page-accent);
          letter-spacing: 0.12em;
          text-transform: uppercase;
          margin-bottom: 2.2rem;
          cursor: default;
          transition: all 0.3s ease;
          opacity: 0;
          animation: fadeSlideUp 0.5s ease 0.1s forwards;
        }
        .hero-tag:hover {
          background: rgba(var(--page-glow-rgb), 0.28);
          border-color: var(--page-accent);
          box-shadow: 0 0 20px rgba(var(--page-glow-rgb), 0.45), 0 0 50px rgba(var(--page-glow-rgb), 0.15);
          transform: scale(1.05);
        }
        .hero-h1 {
          font-family: 'Syne', sans-serif;
          font-size: clamp(2.8rem, 5.5vw, 5.2rem);
          font-weight: 800;
          line-height: 1.02;
          letter-spacing: -0.03em;
          margin-bottom: 1.4rem;
        }
        .hero-sub {
          font-size: 1.05rem;
          color: var(--text-secondary);
          max-width: 520px;
          line-height: 1.75;
          margin-bottom: 2.8rem;
        }

        /* ─── Marquee (identical to Home) ─── */
        .marquee-wrap {
          overflow: hidden;
          border-top: 1px solid var(--border);
          border-bottom: 1px solid var(--border);
          padding: 0.9rem 0;
          position: relative;
          z-index: 1;
        }
        .marquee-track {
          display: flex;
          gap: 0;
          animation: marquee 22s linear infinite;
          width: max-content;
        }
        .marquee-item {
          font-family: 'Syne', sans-serif;
          font-size: 0.75rem;
          font-weight: 600;
          color: var(--text-muted);
          white-space: nowrap;
          letter-spacing: 0.14em;
          text-transform: uppercase;
          padding: 0 2rem;
        }
        .marquee-dot { color: var(--page-accent); padding: 0 0.2rem; }
        @keyframes marquee {
          from { transform: translateX(0); }
          to   { transform: translateX(-50%); }
        }

        /* ─── Stats grid (identical to Home) ─── */
        .stats-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          border-bottom: 1px solid var(--border);
          position: relative;
          z-index: 1;
        }
        .stat-cell {
          padding: 2.5rem 3rem;
          border-right: 1px solid var(--border);
          position: relative;
          overflow: hidden;
          transition: background 0.3s;
        }
        .stat-cell:last-child { border-right: none; }
        .stat-cell:hover { background: rgba(var(--page-glow-rgb), 0.06); }
        .stat-cell::before {
          content: '';
          position: absolute;
          bottom: 0; left: 0; right: 0;
          height: 2px;
          background: linear-gradient(90deg, transparent, var(--page-accent), transparent);
          transform: scaleX(0);
          transition: transform 0.4s ease;
        }
        .stat-cell:hover::before { transform: scaleX(1); }
        .stat-num {
          font-family: 'Syne', sans-serif;
          font-size: 3rem;
          font-weight: 800;
          color: var(--page-accent);
          line-height: 1;
          margin-bottom: 0.4rem;
          letter-spacing: -0.02em;
        }
        .stat-label {
          font-size: 0.8rem;
          color: var(--text-secondary);
          margin-bottom: 2px;
          font-weight: 500;
        }
        .stat-sub {
          font-size: 0.68rem;
          color: var(--text-muted);
          font-family: 'JetBrains Mono', monospace;
        }

        /* ─── Section divider (identical to Home) ─── */
        .section-divider {
          display: flex;
          align-items: center;
          gap: 1rem;
          padding: 3.5rem 3rem 2rem;
        }
        .section-divider-label {
          font-size: 0.68rem;
          font-family: 'JetBrains Mono', monospace;
          color: var(--text-muted);
          text-transform: uppercase;
          letter-spacing: 0.14em;
          white-space: nowrap;
        }
        .section-divider-line { flex: 1; height: 1px; background: var(--border); }

        /* ─── Main content area ─── */
        .page-body {
          position: relative;
          z-index: 1;
          padding: 0 3rem 5rem;
        }

        /* ─── Globe card ─── */
        .globe-card {
          background: var(--card);
          border: 1px solid var(--border);
          border-radius: 18px;
          overflow: hidden;
          margin-bottom: 2rem;
          transition: border-color 0.3s, box-shadow 0.3s;
        }
        .globe-card:hover {
          border-color: rgba(var(--page-glow-rgb), 0.4);
          box-shadow: 0 0 40px rgba(var(--page-glow-rgb), 0.1);
        }
        .globe-header {
          padding: 1.2rem 1.5rem;
          border-bottom: 1px solid var(--border);
          display: flex;
          align-items: center;
          justify-content: space-between;
        }
        .globe-legend {
          padding: 1rem 1.5rem;
          border-top: 1px solid var(--border);
          display: flex;
          gap: 1.5rem;
          flex-wrap: wrap;
          background: rgba(0,0,0,0.2);
        }

        /* ─── Filter pills ─── */
        .filter-pill {
          padding: 7px 18px;
          border-radius: 9999px;
          font-size: 0.72rem;
          font-family: 'JetBrains Mono', monospace;
          letter-spacing: 0.08em;
          cursor: pointer;
          transition: all 0.2s;
          border: 1px solid rgba(var(--page-glow-rgb), 0.25);
          background: rgba(var(--page-glow-rgb), 0.06);
          color: var(--text-muted);
        }
        .filter-pill:hover {
          border-color: var(--page-accent);
          color: var(--page-accent);
        }
        .filter-pill.active {
          border: none;
          background: var(--page-accent);
          color: #0a0a0a;
          font-weight: 700;
          box-shadow: 0 0 16px rgba(var(--page-glow-rgb), 0.4);
        }

        /* ─── Two-col layout: table + sidebar ─── */
        .content-grid {
          display: grid;
          grid-template-columns: 1fr 340px;
          gap: 1.5rem;
        }

        /* ─── Table card ─── */
        .table-card {
          background: var(--card);
          border: 1px solid var(--border);
          border-radius: 18px;
          overflow: hidden;
        }
        .table-card table { width: 100%; border-collapse: collapse; }
        .table-card th {
          padding: 0.75rem 1.25rem;
          font-size: 0.62rem;
          font-family: 'JetBrains Mono', monospace;
          text-transform: uppercase;
          letter-spacing: 0.1em;
          color: var(--text-muted);
          text-align: left;
          border-bottom: 1px solid var(--border);
          white-space: nowrap;
        }
        .table-card td {
          padding: 0.9rem 1.25rem;
          border-bottom: 1px solid rgba(255,255,255,0.04);
          font-size: 0.82rem;
        }
        .table-card tr { cursor: pointer; transition: background 0.15s; }
        .table-card tr:hover td { background: rgba(var(--page-glow-rgb), 0.05); }
        .table-card tr.sel td { background: rgba(var(--page-glow-rgb), 0.08); }

        /* ─── Sidebar cards ─── */
        .sidebar-card {
          background: var(--card);
          border: 1px solid var(--border);
          border-radius: 16px;
          overflow: hidden;
          margin-bottom: 1.25rem;
          transition: border-color 0.3s, box-shadow 0.3s;
        }
        .sidebar-card:hover {
          border-color: rgba(var(--page-glow-rgb), 0.3);
        }
        .sidebar-card-header {
          padding: 1rem 1.25rem;
          border-bottom: 1px solid var(--border);
          display: flex;
          align-items: center;
          justify-content: space-between;
        }
        .sidebar-card-body { padding: 1rem 1.25rem; }

        /* ─── Util bar ─── */
        .util-bar-wrap {
          height: 4px;
          border-radius: 9999px;
          background: rgba(255,255,255,0.05);
          overflow: hidden;
        }
        .util-bar {
          height: 100%;
          border-radius: 9999px;
        }

        /* ─── Tag badge ─── */
        .badge {
          font-size: 0.6rem;
          padding: 2px 7px;
          border-radius: 4px;
          font-family: 'JetBrains Mono', monospace;
          text-transform: uppercase;
          letter-spacing: 0.06em;
        }

        /* ─── Footer (identical to Home) ─── */
        .lorri-footer {
          border-top: 1px solid var(--border);
          position: relative;
          z-index: 1;
        }
        .footer-grid {
          padding: 3.5rem 3rem 2rem;
          display: grid;
          grid-template-columns: 2fr 1fr 1fr;
          gap: 3rem;
        }
        .footer-brand {
          font-family: 'Syne', sans-serif;
          font-size: 1.15rem;
          font-weight: 800;
          color: var(--page-accent);
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 0.6rem;
        }
        .footer-desc {
          font-size: 0.82rem;
          color: var(--text-muted);
          line-height: 1.7;
          max-width: 230px;
          margin-bottom: 1.2rem;
        }
        .footer-badges { display: flex; flex-wrap: wrap; gap: 0.4rem; }
        .footer-badge {
          font-size: 0.65rem;
          font-family: 'JetBrains Mono', monospace;
          padding: 3px 8px;
          border-radius: 5px;
          border: 1px solid var(--border);
          color: var(--text-muted);
          cursor: default;
          transition: all 0.2s;
        }
        .footer-badge:hover { border-color: var(--page-accent); color: var(--page-accent); }
        .footer-col-title {
          font-family: 'Syne', sans-serif;
          font-size: 0.72rem;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.12em;
          color: var(--text-secondary);
          margin-bottom: 1.1rem;
        }
        .footer-link {
          display: block;
          font-size: 0.82rem;
          color: var(--text-muted);
          margin-bottom: 0.55rem;
          cursor: pointer;
          text-decoration: none;
          transition: all 0.2s ease;
          width: fit-content;
        }
        .footer-link:hover {
          color: var(--page-accent);
          transform: translateX(3px);
          text-shadow: 0 0 10px rgba(var(--page-glow-rgb), 0.5);
        }
        .footer-bottom {
          border-top: 1px solid var(--border);
          padding: 1.2rem 3rem;
          display: flex;
          align-items: center;
          justify-content: space-between;
        }
        .footer-bottom-l { font-size: 0.72rem; color: var(--text-muted); font-family: 'JetBrains Mono', monospace; }
        .footer-bottom-r { display: flex; gap: 1.5rem; }
        .footer-bottom-link { font-size: 0.72rem; color: var(--text-muted); cursor: pointer; transition: color 0.2s; }
        .footer-bottom-link:hover { color: var(--page-accent); }

        /* ─── Animations (identical to Home) ─── */
        @keyframes fadeSlideUp {
          from { opacity: 0; transform: translateY(18px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        .blur-line { display: flex; flex-wrap: wrap; justify-content: center; gap: 0.22em; }
>>>>>>> d25832fc965b848f9b673c6db0faa45a90052318
        .blur-word {
          display: inline-block; opacity: 0;
          filter: blur(16px); transform: translateX(-14px);
          animation: blurWordIn 0.6s cubic-bezier(0.22,1,0.36,1) forwards;
        }
        @keyframes blurWordIn {
<<<<<<< HEAD
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
=======
          0%   { opacity:0;   filter:blur(16px); transform:translateX(-14px); }
          55%  { opacity:0.9; filter:blur(2px);  transform:translateX(2px);  }
          100% { opacity:1;   filter:blur(0);    transform:translateX(0);    }
        }
        .blur-word-sub {
          display: inline-block; opacity: 0;
          filter: blur(8px); transform: translateX(-8px);
          animation: blurWordSub 0.5s cubic-bezier(0.22,1,0.36,1) forwards;
        }
        @keyframes blurWordSub {
          from { opacity:0; filter:blur(8px); transform:translateX(-8px); }
          to   { opacity:1; filter:blur(0);   transform:translateX(0);    }
        }
      `}</style>

      {/* ── Navbar (identical to Home) ── */}
      <Navbar />

      {/* ════ HERO ════ */}
      {/* ✏️ EDIT: hero-tag text, h1 words, subtitle words */}
      <section style={{ position:'relative', zIndex:1, width:'100%' }}>
        <div className="hero-wrap">
          <div className="hero-tag">
            <MapPin size={10} /> Live Route Visibility
          </div>

          <h1 className="hero-h1">
            <div className="blur-line">
              {/* ✏️ EDIT: change these words */}
              {['Every', 'Route.'].map((w, i) => (
                <span key={w} className="blur-word" style={{ animationDelay:`${0.12 + i*0.09}s` }}>{w}</span>
              ))}
            </div>
            <div className="blur-line" style={{ color:'var(--page-accent)' }}>
              {/* ✏️ EDIT: change these accent words */}
              {['Every', 'Shipment.'].map((w, i) => (
                <span key={w} className="blur-word" style={{ animationDelay:`${0.3 + i*0.11}s` }}>{w}</span>
              ))}
            </div>
          </h1>

          <p className="hero-sub">
            {/* ✏️ EDIT: change subtitle words */}
            {['6 shipments', 'across', '3 lanes', '—', 'visualised', 'on', 'an', 'interactive', '3D', 'globe', 'with', 'live', 'arc', 'routes.'].map((w, i) => (
              <span key={i} className="blur-word-sub" style={{ animationDelay:`${0.5 + i*0.04}s`, marginRight:'0.3em' }}>{w}</span>
            ))}
          </p>
        </div>
      </section>

      {/* ════ MARQUEE ════ */}
      {/* ✏️ EDIT: change the marquee words */}
      <div className="marquee-wrap">
        <div className="marquee-track">
          {['Route Visibility','Mumbai · Pune · Delhi','Load Consolidation','3 Active Trucks','OR-Tools MIP','6 Shipments','4,100 kg Load','76% Utilization','Colour-Coded Groups','LangChain Agents','Live Globe Map','Time Windows'].flatMap((t,i) => [
            <span key={`a${i}`} className="marquee-item">{t}</span>,
            <span key={`d${i}`} className="marquee-item marquee-dot">·</span>,
          ]).concat(
            ['Route Visibility','Mumbai · Pune · Delhi','Load Consolidation','3 Active Trucks','OR-Tools MIP','6 Shipments','4,100 kg Load','76% Utilization','Colour-Coded Groups','LangChain Agents','Live Globe Map','Time Windows'].flatMap((t,i) => [
              <span key={`b${i}`} className="marquee-item">{t}</span>,
              <span key={`e${i}`} className="marquee-item marquee-dot">·</span>,
            ])
          )}
        </div>
      </div>

      {/* ════ STATS ════ */}
      {/* ✏️ EDIT: stat values are in the STATS array at the top of the file */}
      <div className="stats-grid">
        {STATS.map(({ num, label, sub }) => (
          <div key={label} className="stat-cell">
            <div className="stat-num">{num}</div>
            <div className="stat-label">{label}</div>
            <div className="stat-sub">{sub}</div>
          </div>
        ))}
      </div>

      {/* ════ MAIN CONTENT ════ */}
      <div style={{ position:'relative', zIndex:1 }}>

        {/* Section divider */}
        {/* ✏️ EDIT: section label */}
        <div className="section-divider">
          <span className="section-divider-label">— Route map · shipment table</span>
          <div className="section-divider-line" />
        </div>

        <div className="page-body">

          {/* ── Lane filter pills ── */}
          {/* ✏️ EDIT: LANES array at the top controls these */}
          <div style={{ display:'flex', gap:'0.6rem', flexWrap:'wrap', marginBottom:'1.5rem' }}>
            {LANES.map(lane => (
              <button key={lane} className={`filter-pill${filter === lane ? ' active' : ''}`}
                onClick={() => { setFilter(lane); setSelected(null) }}
              >{lane}</button>
            ))}
          </div>

          {/* ════ GLOBE MAP ════ */}
          {/* ✏️ EDIT: globe config is inside the GlobeMap component above (camera, rotate speed, textures) */}
          <div className="globe-card">
            <div className="globe-header">
              <span style={{ fontSize:'0.68rem', fontFamily:"'JetBrains Mono',monospace", color:'var(--text-muted)', textTransform:'uppercase', letterSpacing:'0.12em' }}>
                / 3d globe · globe.gl · india shipment lanes
              </span>
              <div style={{ display:'flex', alignItems:'center', gap:'0.75rem' }}>
                <span style={{ fontSize:'0.65rem', fontFamily:"'JetBrains Mono',monospace", color:'var(--page-accent)' }}>
                  ● Drag to rotate · Scroll to zoom
                </span>
                {/* ✏️ EDIT: change this badge label */}
                <span style={{ fontSize:'0.65rem', padding:'2px 8px', borderRadius:5, fontFamily:"'JetBrains Mono',monospace", background:'rgba(var(--page-glow-rgb),0.1)', border:'1px solid rgba(var(--page-glow-rgb),0.3)', color:'var(--page-accent)' }}>Live</span>
              </div>
            </div>

            <GlobeMap filter={filter} />

            {/* ✏️ EDIT: legend entries match ARCS array */}
            <div className="globe-legend">
              {ARCS.map(a => (
                <div key={a.label} style={{ display:'flex', alignItems:'center', gap:8, fontSize:'0.65rem', fontFamily:"'JetBrains Mono',monospace", color:'var(--text-muted)' }}>
                  <div style={{ width:24, height:2, background:a.color, borderRadius:1, boxShadow:`0 0 6px ${a.color}` }}/>
                  {a.label}
                </div>
              ))}
            </div>
          </div>

          {/* ════ TABLE + SIDEBAR ════ */}
          <div className="content-grid">

            {/* TABLE */}
            {/* ✏️ EDIT: columns in <thead>, rows driven by SHIPMENTS array above */}
            <div className="table-card">
              <div style={{ padding:'1.1rem 1.5rem', borderBottom:'1px solid var(--border)', display:'flex', alignItems:'center', justifyContent:'space-between' }}>
                <span style={{ fontSize:'0.68rem', fontFamily:"'JetBrains Mono',monospace", color:'var(--text-muted)', textTransform:'uppercase', letterSpacing:'0.12em' }}>
                  / shipments · {filtered.length} records
                </span>
                <span style={{ fontSize:'0.65rem', padding:'2px 8px', borderRadius:5, fontFamily:"'JetBrains Mono',monospace", background:'rgba(var(--page-glow-rgb),0.1)', border:'1px solid rgba(var(--page-glow-rgb),0.3)', color:'var(--page-accent)' }}>{filtered.length}</span>
              </div>
              <table>
                <thead>
                  <tr>
                    {/* ✏️ EDIT: table column headers */}
                    {['ID','Route','Weight','Priority','Window','Status','Truck'].map(h => (
>>>>>>> d25832fc965b848f9b673c6db0faa45a90052318
                      <th key={h}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filtered.map(s => (
<<<<<<< HEAD
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
=======
                    <tr key={s.id} className={selected === s.id ? 'sel' : ''} onClick={() => setSelected(selected === s.id ? null : s.id)}>
                      <td>
                        <span style={{ fontFamily:"'JetBrains Mono',monospace", fontWeight:700, color:GROUP_COLORS[s.group], display:'flex', alignItems:'center', gap:6 }}>
                          <span style={{ width:7, height:7, borderRadius:'50%', background:GROUP_COLORS[s.group], display:'inline-block', boxShadow:`0 0 6px ${GROUP_COLORS[s.group]}` }}/>
                          {s.id}
                        </span>
                      </td>
                      <td style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:'0.75rem', color:'var(--text-secondary)' }}>{s.origin} → {s.dest}</td>
                      <td style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:'0.75rem', color:'var(--text-muted)' }}>{s.weight} kg</td>
                      <td>
                        <span className="badge" style={{ background:`${PRIORITY_COLORS[s.priority]}18`, border:`1px solid ${PRIORITY_COLORS[s.priority]}30`, color:PRIORITY_COLORS[s.priority] }}>{s.priority}</span>
                      </td>
                      <td style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:'0.72rem', color:'var(--text-muted)' }}>{s.window}</td>
                      <td>
                        <span className="badge" style={{
                          background: s.status==='Consolidated' ? 'rgba(var(--page-glow-rgb),0.1)' : 'rgba(6,182,212,0.1)',
                          border: `1px solid ${s.status==='Consolidated' ? 'rgba(var(--page-glow-rgb),0.3)' : 'rgba(6,182,212,0.3)'}`,
                          color: s.status==='Consolidated' ? 'var(--page-accent)' : '#06b6d4',
                        }}>{s.status}</span>
                      </td>
                      <td style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:'0.75rem', color:'var(--text-secondary)', fontWeight:700 }}>{s.truck}</td>
>>>>>>> d25832fc965b848f9b673c6db0faa45a90052318
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
<<<<<<< HEAD
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
=======

            {/* SIDEBAR */}
            <div>

              {/* Shipment detail drawer — appears on row click */}
              {selShipment && (
                <div className="sidebar-card" style={{ borderColor:`${GROUP_COLORS[selShipment.group]}44`, animation:'fadeSlideUp 0.3s ease forwards' }}>
                  <div className="sidebar-card-header">
                    <span style={{ fontFamily:"'Syne',sans-serif", fontSize:'1rem', fontWeight:700, color:GROUP_COLORS[selShipment.group] }}>{selShipment.id}</span>
                    <button onClick={() => setSelected(null)} style={{ background:'none', border:'none', cursor:'pointer', color:'var(--text-muted)', fontSize:'1rem', lineHeight:1, transition:'color 0.2s' }}
                      onMouseEnter={e=>e.currentTarget.style.color='var(--page-accent)'}
                      onMouseLeave={e=>e.currentTarget.style.color='var(--text-muted)'}
                    >✕</button>
                  </div>
                  <div className="sidebar-card-body">
                    {/* ✏️ EDIT: detail rows — add/remove as needed */}
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
                      <div key={k} style={{ display:'flex', justifyContent:'space-between', padding:'0.6rem 0', borderBottom:'1px solid rgba(255,255,255,0.04)', fontSize:'0.82rem' }}>
                        <span style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:'0.68rem', color:'var(--text-muted)', textTransform:'uppercase', letterSpacing:'0.08em' }}>{k}</span>
                        <span style={{ color:'var(--text-secondary)' }}>{v}</span>
                      </div>
                    ))}

                    {selTruck && (
                      <div style={{ marginTop:'1rem', paddingTop:'1rem', borderTop:'1px solid var(--border)' }}>
                        <div style={{ fontSize:'0.68rem', fontFamily:"'JetBrains Mono',monospace", color:'var(--text-muted)', textTransform:'uppercase', letterSpacing:'0.1em', marginBottom:'0.5rem' }}>Truck util</div>
                        <div style={{ background:`${selTruck.color}10`, border:`1px solid ${selTruck.color}25`, borderRadius:10, padding:'0.7rem' }}>
                          <div style={{ display:'flex', justifyContent:'space-between', marginBottom:'0.4rem' }}>
                            <span style={{ fontFamily:"'Syne',sans-serif", fontWeight:700, fontSize:'0.88rem' }}>{selTruck.id}</span>
                            <span style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:'0.75rem', fontWeight:700, color:selTruck.color }}>{selTruck.util}%</span>
                          </div>
                          <div className="util-bar-wrap">
                            <div className="util-bar" style={{ width:`${selTruck.util}%`, background:`linear-gradient(90deg,${selTruck.color}88,${selTruck.color})` }}/>
                          </div>
                          <div style={{ fontSize:'0.65rem', fontFamily:"'JetBrains Mono',monospace", color:'var(--text-muted)', marginTop:'0.35rem' }}>{selTruck.load}/{selTruck.cap} kg</div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Fleet utilization cards */}
              {/* ✏️ EDIT: driven by TRUCKS array at the top */}
              <div className="sidebar-card">
                <div className="sidebar-card-header">
                  <span style={{ fontSize:'0.68rem', fontFamily:"'JetBrains Mono',monospace", color:'var(--text-muted)', textTransform:'uppercase', letterSpacing:'0.12em' }}>/ fleet utilization</span>
                </div>
                <div className="sidebar-card-body" style={{ display:'flex', flexDirection:'column', gap:'0.75rem' }}>
                  {TRUCKS.map(t => (
                    <div key={t.id} onClick={() => setSelected(t.shipments[0])}
                      style={{ background:'rgba(255,255,255,0.02)', border:'1px solid var(--border)', borderRadius:12, padding:'0.9rem 1rem', cursor:'pointer', transition:'all 0.2s' }}
                      onMouseEnter={e=>{ e.currentTarget.style.borderColor=`${t.color}55`; e.currentTarget.style.boxShadow=`0 0 16px ${t.color}18` }}
                      onMouseLeave={e=>{ e.currentTarget.style.borderColor='var(--border)'; e.currentTarget.style.boxShadow='none' }}
                    >
                      <div style={{ display:'flex', alignItems:'center', gap:'0.6rem', marginBottom:'0.6rem' }}>
                        <div style={{ width:8, height:8, borderRadius:'50%', background:t.color, boxShadow:`0 0 6px ${t.color}`, flexShrink:0 }}/>
                        <div style={{ fontFamily:"'Syne',sans-serif", fontSize:'0.88rem', fontWeight:700, flex:1 }}>{t.id}</div>
                        <div style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:'0.75rem', fontWeight:700, color:t.color }}>{t.util}%</div>
                      </div>
                      <div className="util-bar-wrap" style={{ marginBottom:'0.5rem' }}>
                        <div className="util-bar" style={{ width:`${t.util}%`, background:`linear-gradient(90deg,${t.color}88,${t.color})` }}/>
                      </div>
                      <div style={{ fontSize:'0.68rem', fontFamily:"'JetBrains Mono',monospace", color:'var(--text-muted)', marginBottom:'0.5rem' }}>{t.route} · {t.load}/{t.cap} kg</div>
                      <div style={{ display:'flex', gap:'0.35rem', flexWrap:'wrap' }}>
                        {t.shipments.map(sid => (
                          <span key={sid} onClick={e=>{ e.stopPropagation(); setSelected(sid) }}
                            style={{ fontSize:'0.6rem', padding:'2px 6px', borderRadius:4, fontFamily:"'JetBrains Mono',monospace", background:`${t.color}15`, border:`1px solid ${t.color}30`, color:t.color, cursor:'pointer' }}
                          >{sid}</span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

>>>>>>> d25832fc965b848f9b673c6db0faa45a90052318
            </div>
          </div>
        </div>
      </div>
<<<<<<< HEAD
=======

      {/* ════ FOOTER (identical to Home) ════ */}
      {/* ✏️ EDIT: footer badge list, team names */}
      <footer className="lorri-footer">
        <div className="footer-grid">
          <div>
            <div className="footer-brand">
              <svg viewBox="0 0 120 140" width="20" height="23" fill="none">
                <path stroke="var(--page-accent)" strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" d="M28 42 L18 10 L44 30 Z"/>
                <path stroke="var(--page-accent)" strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" d="M92 42 L102 10 L76 30 Z"/>
                <path stroke="var(--page-accent)" strokeWidth="2.2" strokeLinejoin="round" strokeLinecap="round" d="M22 70 Q18 50 28 42 Q44 30 60 28 Q76 30 92 42 Q102 50 98 70 Q96 90 80 100 Q70 108 60 110 Q50 108 40 100 Q24 90 22 70 Z"/>
                <ellipse stroke="var(--page-accent)" strokeWidth="2" cx="42" cy="62" rx="7" ry="8"/>
                <ellipse stroke="var(--page-accent)" strokeWidth="2" cx="78" cy="62" rx="7" ry="8"/>
              </svg>
              Lorri
            </div>
            <p className="footer-desc">AI-powered load consolidation. Fewer trucks, lower costs, less carbon — optimized in seconds using OR-Tools and LangChain.</p>
            <div className="footer-badges">
              {['OR-Tools','LangChain','FastAPI','React','Globe.gl','Recharts'].map(t => (
                <span key={t} className="footer-badge">{t}</span>
              ))}
            </div>
          </div>
          <div>
            <div className="footer-col-title">Product</div>
            {[['Shipments','/shipments'],['Optimizer','/optimize'],['Scenarios','/scenarios'],['AI Insights','/insights']].map(([l,t]) => (
              <span key={l} className="footer-link" onClick={() => nav(t)}>{l}</span>
            ))}
          </div>
          <div>
            <div className="footer-col-title">Stack</div>
            {['OR-Tools MIP','LangChain Agents','scikit-learn','Globe.gl','Recharts','SQLite / PG'].map(t => (
              <span key={t} className="footer-link">{t}</span>
            ))}
          </div>

        </div>
        <div className="footer-bottom">
          <span className="footer-bottom-l">© 2025 Lorri · Load Consolidation Intelligence · Hackathon Build</span>
          <div className="footer-bottom-r">
            <span className="footer-bottom-link">Privacy</span>
            <span className="footer-bottom-link">Terms</span>
            <span className="footer-bottom-link">GitHub</span>
          </div>
        </div>
      </footer>
>>>>>>> d25832fc965b848f9b673c6db0faa45a90052318
    </div>
  )
}