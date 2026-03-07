import { useNavigate } from 'react-router-dom'
import { useEffect, useRef, useState } from 'react'
import Navbar from '@/components/layout/Navbar'
import { Zap } from 'lucide-react'
import { DEMO_METRICS } from '@/data/demoData'

/* ── Animated counter hook ── */
function useCounter(target, duration = 1800, start = false) {
  const [val, setVal] = useState(0)
  useEffect(() => {
    if (!start) return
    let startTime = null
    const step = (ts) => {
      if (!startTime) startTime = ts
      const p = Math.min((ts - startTime) / duration, 1)
      const ease = 1 - Math.pow(1 - p, 3)
      setVal(Math.floor(ease * target))
      if (p < 1) requestAnimationFrame(step)
    }
    requestAnimationFrame(step)
  }, [start, target, duration])
  return val
}

const STATS = [
  { label: 'Trips Reduced',  raw: DEMO_METRICS.savings.trips_reduced,    suffix: '',   prefix: '' },
  { label: 'Cost Saved',     raw: DEMO_METRICS.savings.cost_saved / 1000, suffix: 'k', prefix: '₹' },
  { label: 'CO₂ Saved',      raw: DEMO_METRICS.savings.carbon_saved_kg,   suffix: 'kg', prefix: '' },
  { label: 'Avg Utilization',raw: DEMO_METRICS.after.avg_utilization,     suffix: '%',  prefix: '' },
]

const FEATURE_ICONS = [
  /* Engine — lightning bolt */
  <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="var(--page-accent)" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>,
  /* Intelligence — brain/bulb */
  <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="var(--page-accent)" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="8" r="5"/><path d="M9 13v2a3 3 0 0 0 6 0v-2"/><line x1="9" y1="17" x2="15" y2="17"/><line x1="12" y1="19" x2="12" y2="21"/><path d="M7 8a5 5 0 0 1 5-5"/><path d="M12 3a5 5 0 0 1 5 5"/></svg>,
  /* Scenarios — bar chart */
  <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="var(--page-accent)" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/><line x1="2" y1="20" x2="22" y2="20"/></svg>,
  /* Visibility — map pin */
  <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="var(--page-accent)" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/><circle cx="12" cy="9" r="2.5"/></svg>,
]

const FEATURES = [
  {
    num: '01',
    tag: 'Engine',
    title: 'OR-Tools MIP Solver',
    desc: 'Binary decision variables assign each shipment to exactly one truck. The solver minimises total trips while maximising utilisation — constrained by weight, volume, time windows and compatibility.',
    bullets: ['Weight & volume capacity', 'Time window feasibility', 'Heuristic fallback >50 shipments'],
    to: '/optimize',
  },
  {
    num: '02',
    tag: 'Intelligence',
    title: 'Four-Agent LangChain Pipeline',
    desc: 'A sequential AI pipeline validates inputs, explains outputs in plain language, relaxes blocking constraints, and recommends the best plan across all scenarios.',
    bullets: ['Validation before solve', 'Human-readable insights', 'Constraint relaxation suggestions'],
    to: '/insights',
  },
  {
    num: '03',
    tag: 'Scenarios',
    title: 'What-If Scenario Engine',
    desc: 'Run the same batch under four different business conditions — strict SLAs, flexible windows, reduced fleet, or demand surge — and compare cost, carbon, and utilisation side by side.',
    bullets: ['Strict vs Flexible SLA', 'Vehicle Shortage mode', 'Demand Surge simulation'],
    to: '/scenarios',
  },
  {
    num: '04',
    tag: 'Visibility',
    title: 'Live Route Map',
    desc: 'Every origin–destination pair visualised on an interactive Leaflet map. Routes colour-coded by consolidation group, clickable for full shipment details.',
    bullets: ['Mumbai · Pune · Delhi lanes', 'Colour-coded groups', 'Click for shipment drawer'],
    to: '/shipments',
  },
]

export default function Home() {
  const nav = useNavigate()
  const statsRef = useRef(null)
  const [statsVisible, setStatsVisible] = useState(false)

  useEffect(() => {
    const obs = new IntersectionObserver(([e]) => { if (e.isIntersecting) setStatsVisible(true) }, { threshold: 0.3 })
    if (statsRef.current) obs.observe(statsRef.current)
    return () => obs.disconnect()
  }, [])

  const c0 = useCounter(STATS[0].raw, 1400, statsVisible)
  const c1 = useCounter(STATS[1].raw, 1600, statsVisible)
  const c2 = useCounter(STATS[2].raw, 1800, statsVisible)
  const c3 = useCounter(STATS[3].raw, 1500, statsVisible)
  const counters = [c0, c1, c2, c3]

  return (
    <div className="lorri-home">
      <style>{`
        /* ─── Base ─── */
        .lorri-home {
          min-height: 100vh;
          display: flex;
          flex-direction: column;
          position: relative;
          overflow-x: clip;
        }

        /* ─── Dot grid texture ─── */
        .lorri-home::before {
          content: '';
          position: fixed;
          inset: 0;
          z-index: 0;
          background-image: radial-gradient(circle, rgba(var(--page-glow-rgb), 0.18) 1px, transparent 1px);
          background-size: 32px 32px;
          pointer-events: none;
          mask-image: radial-gradient(ellipse 80% 80% at 50% 50%, black 30%, transparent 100%);
        }

        /* ─── Sections ─── */
        .home-section {
          position: relative;
          z-index: 1;
          width: 100%;
        }
        .home-inner {
          max-width: 1160px;
          margin: 0 auto;
          padding: 0 3rem;
        }

        /* ─── HERO ─── CHANGE 1: min-height 100vh, padding bigger, sticky ── */
        .hero-wrap {
          min-height: 100vh;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          text-align: center;
          padding: 8rem 2rem 6rem;
          position: sticky;
          top: 0;
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
          box-shadow: 0 0 20px rgba(var(--page-glow-rgb), 0.45),
                      0 0 50px rgba(var(--page-glow-rgb), 0.15);
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
          max-width: 500px;
          line-height: 1.75;
          margin-bottom: 2.8rem;
        }
        .hero-cta-row {
          display: flex;
          gap: 12px;
          justify-content: center;
          flex-wrap: wrap;
          opacity: 0;
          animation: fadeSlideUp 0.5s ease 1.7s forwards;
        }
        /* ─── CHANGE 2: both buttons same design ─── */
        .btn-primary {
          display: inline-flex; align-items: center; gap: 8px;
          padding: 13px 30px; border-radius: 12px; border: none;
          background: var(--page-accent); color: #0a0a0a;
          font-weight: 700; font-size: 0.9rem; cursor: pointer;
          font-family: 'DM Sans', sans-serif;
          box-shadow: 0 0 28px rgba(var(--page-glow-rgb), 0.45);
          transition: all 0.22s ease;
        }
        .btn-primary:hover {
          transform: translateY(-2px);
          box-shadow: 0 0 48px rgba(var(--page-glow-rgb), 0.65);
        }
        .btn-outline {
          display: inline-flex; align-items: center; gap: 8px;
          padding: 13px 30px; border-radius: 12px; border: none;
          background: var(--page-accent); color: #0a0a0a;
          font-weight: 700; font-size: 0.9rem; cursor: pointer;
          font-family: 'DM Sans', sans-serif;
          box-shadow: 0 0 28px rgba(var(--page-glow-rgb), 0.45);
          transition: all 0.22s ease;
        }
        .btn-outline:hover {
          transform: translateY(-2px);
          box-shadow: 0 0 48px rgba(var(--page-glow-rgb), 0.65);
        }

        /* ─── Scroll hint ─── */
        .scroll-hint {
          position: absolute;
          bottom: 2.5rem;
          left: calc(50% - 25px);
          transform: translateX(-50%);
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 6px;
          opacity: 0;
          animation: fadeSlideUp 0.5s ease 2s forwards;
        }
        .scroll-hint span {
          font-size: 0.65rem;
          font-family: 'JetBrains Mono', monospace;
          color: var(--text-muted);
          letter-spacing: 0.1em;
          text-transform: uppercase;
        }
        .scroll-line {
          width: 1px;
          height: 40px;
          background: linear-gradient(to bottom, var(--page-accent), transparent);
          animation: scrollPulse 2s ease-in-out infinite;
        }
        @keyframes scrollPulse {
          0%,100% { opacity: 0.4; transform: scaleY(1); }
          50%      { opacity: 1;   transform: scaleY(1.15); }
        }

        /* ─── Marquee ─── */
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
        .marquee-dot {
          color: var(--page-accent);
          padding: 0 0.2rem;
        }
        @keyframes marquee {
          from { transform: translateX(0); }
          to   { transform: translateX(-50%); }
        }

        /* ─── Stats ─── */
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

        /* ─── Section divider ─── */
        .section-divider {
          display: flex;
          align-items: center;
          gap: 1rem;
          padding: 3.5rem 3rem 0;
        }
        .section-divider-label {
          font-size: 0.68rem;
          font-family: 'JetBrains Mono', monospace;
          color: var(--text-muted);
          text-transform: uppercase;
          letter-spacing: 0.14em;
          white-space: nowrap;
        }
        .section-divider-line {
          flex: 1;
          height: 1px;
          background: var(--border);
        }

        /* ─── Features alternating ─── */
        .features-wrap {
          padding: 0 3rem 5rem;
          display: flex;
          flex-direction: column;
          gap: 0;
        }
        .feature-row {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 4rem;
          padding: 4rem 0;
          border-bottom: 1px solid var(--border);
          align-items: center;
        }
        .feature-row:last-child { border-bottom: none; }
        .feature-row.reverse .feature-text { order: 2; }
        .feature-row.reverse .feature-visual { order: 1; }
        .feature-num {
          font-family: 'JetBrains Mono', monospace;
          font-size: 0.68rem;
          color: var(--page-accent);
          letter-spacing: 0.12em;
          margin-bottom: 0.5rem;
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }
        .feature-num::after {
          content: '';
          flex: 0 0 40px;
          height: 1px;
          background: var(--page-accent);
          opacity: 0.4;
        }
        .feature-tag {
          font-size: 0.68rem;
          padding: 2px 8px;
          border-radius: 5px;
          border: 1px solid rgba(var(--page-glow-rgb), 0.35);
          color: var(--page-accent);
          background: rgba(var(--page-glow-rgb), 0.1);
          font-family: 'JetBrains Mono', monospace;
          text-transform: uppercase;
          letter-spacing: 0.08em;
          display: inline-block;
          margin-bottom: 1rem;
        }
        /* ─── CHANGE 4: bigger text in features section ─── */
        .feature-title {
          font-family: 'Syne', sans-serif;
          font-size: 2rem;
          font-weight: 800;
          line-height: 1.15;
          letter-spacing: -0.02em;
          margin-bottom: 1rem;
        }
        .feature-desc {
          font-size: 1rem;
          color: var(--text-secondary);
          line-height: 1.75;
          margin-bottom: 1.5rem;
        }
        .feature-bullets {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
          margin-bottom: 1.8rem;
        }
        .feature-bullet {
          display: flex;
          align-items: center;
          gap: 0.6rem;
          font-size: 0.92rem;
          color: var(--text-muted);
        }
        .feature-bullet::before {
          content: '';
          width: 5px; height: 5px;
          border-radius: 50%;
          background: var(--page-accent);
          flex-shrink: 0;
          box-shadow: 0 0 6px var(--page-accent);
        }
        .feature-link {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          font-size: 0.9rem;
          font-weight: 600;
          color: var(--page-accent);
          cursor: pointer;
          padding: 5px 14px;
          border-radius: 9999px;
          border: 1px solid rgba(var(--page-glow-rgb), 0.45);
          background: rgba(var(--page-glow-rgb), 0.1);
          font-family: 'JetBrains Mono', monospace;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          font-size: 0.72rem;
          transition: all 0.3s ease;
        }
        .feature-link:hover {
          background: rgba(var(--page-glow-rgb), 0.28);
          border-color: var(--page-accent);
          box-shadow: 0 0 20px rgba(var(--page-glow-rgb), 0.45),
                      0 0 50px rgba(var(--page-glow-rgb), 0.15);
          transform: scale(1.05);
        }

        /* ─── Feature visual card ─── */
        .feature-visual {
          background: var(--card);
          border: 1px solid var(--border);
          border-radius: 18px;
          padding: 2rem;
          min-height: 260px;
          display: flex;
          flex-direction: column;
          justify-content: space-between;
          position: relative;
          overflow: hidden;
          transition: border-color 0.3s, box-shadow 0.3s;
        }
        .feature-row:hover .feature-visual {
          border-color: rgba(var(--page-glow-rgb), 0.4);
          box-shadow: 0 0 40px rgba(var(--page-glow-rgb), 0.1);
        }
        .feature-visual::before {
          content: '';
          position: absolute;
          top: -40%; right: -20%;
          width: 200px; height: 200px;
          border-radius: 50%;
          background: radial-gradient(circle, rgba(var(--page-glow-rgb), 0.2), transparent 70%);
          pointer-events: none;
        }
        .visual-label {
          font-size: 0.65rem;
          font-family: 'JetBrains Mono', monospace;
          color: var(--text-muted);
          text-transform: uppercase;
          letter-spacing: 0.12em;
          margin-bottom: 1.2rem;
        }
        .visual-metric-row {
          display: flex;
          gap: 1rem;
          margin-bottom: 1rem;
        }
        .visual-metric {
          flex: 1;
          background: rgba(var(--page-glow-rgb), 0.08);
          border: 1px solid rgba(var(--page-glow-rgb), 0.15);
          border-radius: 10px;
          padding: 0.75rem 1rem;
        }
        .visual-metric-val {
          font-family: 'Syne', sans-serif;
          font-size: 1.4rem;
          font-weight: 800;
          color: var(--page-accent);
          line-height: 1;
        }
        .visual-metric-lbl {
          font-size: 0.65rem;
          color: var(--text-muted);
          font-family: 'JetBrains Mono', monospace;
          margin-top: 3px;
          text-transform: uppercase;
          letter-spacing: 0.08em;
        }
        .visual-bar-wrap {
          background: rgba(255,255,255,0.05);
          border-radius: 9999px;
          height: 6px;
          overflow: hidden;
          margin-top: 0.5rem;
        }
        .visual-bar {
          height: 100%;
          border-radius: 9999px;
          background: linear-gradient(90deg, rgba(var(--page-glow-rgb),1), var(--page-accent));
        }

        /* ─── Bottom CTA ─── */
        .cta-section {
          border-top: 1px solid var(--border);
          position: relative;
          z-index: 1;
          overflow: hidden;
        }
        .cta-inner {
          padding: 6rem 3rem;
          text-align: center;
          position: relative;
        }
        .cta-glow {
          position: absolute;
          top: 50%; left: 50%;
          transform: translate(-50%, -50%);
          width: 600px; height: 300px;
          border-radius: 50%;
          background: radial-gradient(ellipse, rgba(var(--page-glow-rgb), 0.25) 0%, transparent 70%);
          pointer-events: none;
        }
        .cta-h2 {
          font-family: 'Syne', sans-serif;
          font-size: clamp(2rem, 4vw, 3.5rem);
          font-weight: 800;
          letter-spacing: -0.025em;
          line-height: 1.1;
          margin-bottom: 1rem;
          position: relative;
        }
        .cta-sub {
          font-size: 1rem;
          color: var(--text-secondary);
          margin-bottom: 2.5rem;
          position: relative;
        }

        /* ─── Footer ─── */
        .lorri-footer {
          border-top: 1px solid var(--border);
          position: relative;
          z-index: 1;
        }
        .footer-grid {
          padding: 3.5rem 3rem 2rem;
          display: grid;
          grid-template-columns: 2fr 1fr 1fr 1fr;
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
        .footer-badges {
          display: flex;
          flex-wrap: wrap;
          gap: 0.4rem;
        }
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
        .footer-badge:hover {
          border-color: var(--page-accent);
          color: var(--page-accent);
        }
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
          max-width: 100%;
          border-top: 1px solid var(--border);
          padding: 1.2rem 3rem;
          display: flex;
          align-items: center;
          justify-content: space-between;
        }
        .footer-bottom-l {
          font-size: 0.72rem;
          color: var(--text-muted);
          font-family: 'JetBrains Mono', monospace;
        }
        .footer-bottom-r {
          display: flex;
          gap: 1.5rem;
        }
        .footer-bottom-link {
          font-size: 0.72rem;
          color: var(--text-muted);
          cursor: pointer;
          transition: color 0.2s;
        }
        .footer-bottom-link:hover { color: var(--page-accent); }

        /* ─── Animations ─── */
        @keyframes fadeSlideUp {
          from { opacity: 0; transform: translateY(18px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        .blur-line { display: flex; flex-wrap: wrap; justify-content: center; gap: 0.22em; }
        .blur-word {
          display: inline-block; opacity: 0;
          filter: blur(16px); transform: translateX(-14px);
          animation: blurWordIn 0.6s cubic-bezier(0.22,1,0.36,1) forwards;
        }
        @keyframes blurWordIn {
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

      {/* ── Navbar ── */}
      <Navbar />

      {/* ════ HERO ════ */}
      <section className="home-section">
        <div className="hero-wrap">

          <div className="hero-tag">
            <Zap size={10} /> AI-Powered Load Consolidation
          </div>

          <h1 className="hero-h1">
            <div className="blur-line">
              {['Ship', 'Less', 'Trucks.'].map((w, i) => (
                <span key={w} className="blur-word" style={{ animationDelay: `${0.12 + i * 0.09}s` }}>{w}</span>
              ))}
            </div>
            <div className="blur-line" style={{ color: 'var(--page-accent)' }}>
              {['Save', 'More.'].map((w, i) => (
                <span key={w} className="blur-word" style={{ animationDelay: `${0.4 + i * 0.11}s` }}>{w}</span>
              ))}
            </div>
          </h1>

          <p className="hero-sub">
            {['Lorri','uses','OR-Tools','+','LangChain','agents','to','consolidate','your','shipments','—','cutting','trips,','costs,','and','carbon','in','seconds.'].map((w, i) => (
              <span key={i} className="blur-word-sub" style={{ animationDelay: `${0.65 + i * 0.042}s`, marginRight: '0.3em' }}>{w}</span>
            ))}
          </p>

          <div className="hero-cta-row">
            <button className="btn-primary" onClick={() => nav('/optimize')}>
              <Zap size={15} /> Run Optimizer
            </button>
            <button className="btn-outline" onClick={() => nav('/shipments')}>
              <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/><circle cx="12" cy="9" r="2.5"/></svg>
              View Shipments
            </button>
          </div>

          <div className="scroll-hint">
            <span>Scroll</span>
            <div className="scroll-line" />
          </div>
        </div>
      </section>

      {/* ════ MARQUEE ════ */}
      <div className="marquee-wrap">
        <div className="marquee-track">
          {['Load Consolidation','Fewer Trucks','Lower Costs','Less Carbon','OR-Tools Solver','AI Insights','Smart Routing','Max Utilization','Time Windows','Heuristic Fallback','LangChain Agents','Scenario Engine'].flatMap((t,i) => [
            <span key={`a${i}`} className="marquee-item">{t}</span>,
            <span key={`d${i}`} className="marquee-item marquee-dot">·</span>,
          ]).concat(
            ['Load Consolidation','Fewer Trucks','Lower Costs','Less Carbon','OR-Tools Solver','AI Insights','Smart Routing','Max Utilization','Time Windows','Heuristic Fallback','LangChain Agents','Scenario Engine'].flatMap((t,i) => [
              <span key={`b${i}`} className="marquee-item">{t}</span>,
              <span key={`e${i}`} className="marquee-item marquee-dot">·</span>,
            ])
          )}
        </div>
      </div>

      {/* ════ STATS ════ */}
      <div className="stats-grid" ref={statsRef}>
        {STATS.map(({ label, raw, suffix, prefix }, i) => (
          <div key={label} className="stat-cell">
            <div className="stat-num">
              {prefix}{counters[i]}{suffix}
            </div>
            <div className="stat-label">{label}</div>
            <div className="stat-sub">per optimized batch</div>
          </div>
        ))}
      </div>

      {/* ════ FEATURES — alternating rows ════ */}
      <div className="home-section">
        <div className="section-divider">
          <span className="section-divider-label">— How it works</span>
          <div className="section-divider-line" />
        </div>

        <div className="features-wrap">
          {FEATURES.map((f, idx) => (
            <div key={f.num} className={`feature-row${idx % 2 === 1 ? ' reverse' : ''}`}>

              {/* Text side */}
              <div className="feature-text">
                <div className="feature-num">No. {f.num}</div>
                <div style={{ display:'flex', alignItems:'center', gap:'0.6rem', marginBottom:'1rem' }}>
                  <span className="feature-tag" style={{ marginBottom:0 }}>{f.tag}</span>
                  <span style={{ opacity:0.85 }}>{FEATURE_ICONS[idx]}</span>
                </div>
                <h3 className="feature-title">{f.title}</h3>
                <p className="feature-desc">{f.desc}</p>
                <div className="feature-bullets">
                  {f.bullets.map(b => (
                    <div key={b} className="feature-bullet">{b}</div>
                  ))}
                </div>
                {/* CHANGE 3: text matches navbar order */}
                <span className="feature-link" onClick={() => nav(f.to)}>
                  <span style={{ display:'flex', alignItems:'center' }}>{FEATURE_ICONS[idx]}</span>
                  {['Optimize','Insights','Scenarios','Shipments'][idx]} →
                </span>
              </div>

              {/* Visual side */}
              <div className="feature-visual">
                <div className="visual-label">/ {f.tag.toLowerCase()} · preview</div>

                {idx === 0 && (
                  <>
                    <div className="visual-metric-row">
                      <div className="visual-metric">
                        <div className="visual-metric-val">3</div>
                        <div className="visual-metric-lbl">Trucks Used</div>
                      </div>
                      <div className="visual-metric">
                        <div className="visual-metric-val">₹13.5k</div>
                        <div className="visual-metric-lbl">Total Cost</div>
                      </div>
                      <div className="visual-metric">
                        <div className="visual-metric-val">44%</div>
                        <div className="visual-metric-lbl">Saved</div>
                      </div>
                    </div>
                    <div>
                      {[['V001 · Mumbai→Pune', 91], ['V003 · Mumbai→Delhi', 32], ['V004 · Pune→Delhi', 97]].map(([lbl, pct]) => (
                        <div key={lbl} style={{ marginBottom: '0.6rem' }}>
                          <div style={{ display:'flex', justifyContent:'space-between', fontSize:'0.7rem', color:'var(--text-muted)', marginBottom:'4px', fontFamily:'JetBrains Mono' }}>
                            <span>{lbl}</span><span style={{ color:'var(--page-accent)' }}>{pct}%</span>
                          </div>
                          <div className="visual-bar-wrap">
                            <div className="visual-bar" style={{ width:`${pct}%` }} />
                          </div>
                        </div>
                      ))}
                    </div>
                  </>
                )}

                {idx === 1 && (
                  <div style={{ display:'flex', flexDirection:'column', gap:'0.65rem' }}>
                    {[
                      { agent:'Insight Agent',     color:'#06b6d4', msg:'91% utilisation on Mumbai–Pune lane. ₹10.5k saved vs individual dispatch.' },
                      { agent:'Relaxation Agent',  color:'#10b981', msg:'Relax S003 window by 45 min → consolidation with S006 feasible.' },
                      { agent:'Scenario Recommender', color:'var(--page-accent)', msg:'Flexible SLA = best cost. Strict SLA = best compliance.' },
                    ].map(({ agent, color, msg }) => (
                      <div key={agent} style={{ background:'rgba(255,255,255,0.03)', border:`1px solid ${color}28`, borderRadius:'10px', padding:'0.75rem 1rem' }}>
                        <div style={{ fontSize:'0.65rem', color, fontFamily:'JetBrains Mono', marginBottom:'4px', textTransform:'uppercase', letterSpacing:'0.08em' }}>{agent}</div>
                        <div style={{ fontSize:'0.78rem', color:'var(--text-secondary)', lineHeight:1.5 }}>{msg}</div>
                      </div>
                    ))}
                  </div>
                )}

                {idx === 2 && (
                  <div style={{ display:'flex', flexDirection:'column', gap:'0.6rem' }}>
                    {[
                      { label:'Flexible SLA',    cost:'₹13.5k', util:'76%', color:'var(--page-accent)' },
                      { label:'Strict SLA',      cost:'₹15.5k', util:'68%', color:'#06b6d4' },
                      { label:'Vehicle Shortage',cost:'₹12.0k', util:'91%', color:'#10b981' },
                      { label:'Demand Surge',    cost:'₹19.0k', util:'82%', color:'#8b5cf6' },
                    ].map(({ label, cost, util, color }) => (
                      <div key={label} style={{ display:'flex', alignItems:'center', gap:'0.75rem', background:'rgba(255,255,255,0.02)', borderRadius:'8px', padding:'0.6rem 0.9rem' }}>
                        <div style={{ width:8, height:8, borderRadius:'50%', background:color, flexShrink:0, boxShadow:`0 0 6px ${color}` }} />
                        <span style={{ flex:1, fontSize:'0.78rem', color:'var(--text-secondary)' }}>{label}</span>
                        <span style={{ fontSize:'0.78rem', fontFamily:'JetBrains Mono', color }}>{cost}</span>
                        <span style={{ fontSize:'0.72rem', color:'var(--text-muted)', fontFamily:'JetBrains Mono' }}>{util}</span>
                      </div>
                    ))}
                  </div>
                )}

                {idx === 3 && (
                  <div>
                    <div style={{ background:'rgba(255,255,255,0.03)', borderRadius:'12px', padding:'1rem', height:'160px', display:'flex', alignItems:'center', justifyContent:'center', border:'1px solid var(--border)', position:'relative', overflow:'hidden' }}>
                      <svg viewBox="0 0 300 140" width="100%" height="100%" fill="none">
                        {[0,1,2,3].map(i => <line key={i} x1="0" y1={i*40+20} x2="300" y2={i*40+20} stroke="rgba(255,255,255,0.05)" strokeWidth="1"/>)}
                        <line x1="40" y1="110" x2="150" y2="70" stroke="#f59e0b" strokeWidth="2" strokeDasharray="5,3" opacity="0.8"/>
                        <line x1="40" y1="110" x2="150" y2="70" stroke="#f59e0b" strokeWidth="2" strokeDasharray="5,3" opacity="0.5" transform="translate(10,5)"/>
                        <line x1="150" y1="70" x2="260" y2="30" stroke="#06b6d4" strokeWidth="2" strokeDasharray="5,3" opacity="0.8"/>
                        <line x1="40" y1="110" x2="260" y2="30" stroke="#10b981" strokeWidth="1.5" strokeDasharray="3,4" opacity="0.5"/>
                        {[[40,110,'Mumbai'],[150,70,'Pune'],[260,30,'Delhi']].map(([cx,cy,name]) => (
                          <g key={name}>
                            <circle cx={cx} cy={cy} r="6" fill="#0a0a0a" stroke="var(--page-accent)" strokeWidth="2"/>
                            <circle cx={cx} cy={cy} r="2" fill="var(--page-accent)"/>
                            <text x={cx} y={cy-12} textAnchor="middle" fill="var(--text-muted)" fontSize="9" fontFamily="JetBrains Mono">{name}</text>
                          </g>
                        ))}
                      </svg>
                    </div>
                    <div style={{ display:'flex', gap:'0.75rem', marginTop:'0.75rem' }}>
                      {[['#f59e0b','S001+S002+S005'],['#06b6d4','S003'],['#10b981','S004']].map(([c,l]) => (
                        <div key={l} style={{ display:'flex', alignItems:'center', gap:'4px', fontSize:'0.65rem', color:'var(--text-muted)', fontFamily:'JetBrains Mono' }}>
                          <span style={{ width:8, height:2, background:c, borderRadius:1, display:'inline-block' }}/>
                          {l}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ════ BOTTOM CTA ════ */}
      <div className="cta-section">
        <div className="cta-inner">
          <div className="cta-glow" />
          <h2 className="cta-h2">
            Ready to consolidate?
          </h2>
          <p className="cta-sub">
            Load your shipments, run the solver, watch the savings appear.
          </p>
          <div style={{ display:'flex', gap:'12px', justifyContent:'center', flexWrap:'wrap' }}>
            <button className="btn-outline" onClick={() => nav('/scenarios')}>
              <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/><line x1="2" y1="20" x2="22" y2="20"/></svg>
              Scenarios
            </button>
            <button className="btn-outline" onClick={() => nav('/insights')}>
              <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="8" r="5"/><path d="M9 13v2a3 3 0 0 0 6 0v-2"/><line x1="9" y1="17" x2="15" y2="17"/><line x1="12" y1="19" x2="12" y2="21"/></svg>
              Insights
            </button>
          </div>
        </div>
      </div>

      {/* ════ FOOTER ════ */}
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
            <p className="footer-desc">
              AI-powered load consolidation. Fewer trucks, lower costs, less carbon — optimized in seconds using OR-Tools and LangChain.
            </p>
            <div className="footer-badges">
              {['OR-Tools','LangChain','FastAPI','React','Leaflet','Recharts'].map(t => (
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
            {['OR-Tools MIP','LangChain Agents','scikit-learn','Leaflet Maps','Recharts','SQLite / PG'].map(t => (
              <span key={t} className="footer-link">{t}</span>
            ))}
          </div>
          <div>
            <div className="footer-col-title">Team</div>
            {['Manikya — Frontend','Muaaz — AI & Backend','Vaishnavi — OR Engine','Rajkumar — OR Engine'].map(t => (
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
    </div>
  )
}