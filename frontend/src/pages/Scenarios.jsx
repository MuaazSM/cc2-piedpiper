import { useState } from 'react'
import { Loader2 } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import Navbar from '@/components/layout/Navbar'
import { DEMO_METRICS } from '@/data/demoData'

const SCENARIOS = [
  {
    id: 'flexible',
    num: '01',
    label: 'Flexible SLA',
    tag: 'Recommended',
    color: 'var(--page-accent)',
    colorRaw: 'var(--page-glow-rgb)',
    icon: (
      <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10"/>
        <path d="M12 8v4l3 3"/>
      </svg>
    ),
    desc: 'Delivery windows are relaxed by up to 2 hours. Enables maximum consolidation and cost savings — ideal for non-urgent B2B shipments.',
    metrics: { trucks: 3, cost: '₹13.5k', util: '76%', carbon: '42 kg', saved: '44%' },
    bars: [['V001 · Mumbai→Pune', 91], ['V003 · Mumbai→Delhi', 32], ['V004 · Pune→Delhi', 97]],
  },
  {
    id: 'strict',
    num: '02',
    label: 'Strict SLA',
    tag: 'Compliance',
    color: '#06b6d4',
    colorRaw: '6,182,212',
    icon: (
      <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
      </svg>
    ),
    desc: 'All delivery time windows respected exactly. Fewer consolidations are possible — choose this for contractually bound SLA customers.',
    metrics: { trucks: 4, cost: '₹15.5k', util: '68%', carbon: '58 kg', saved: '22%' },
    bars: [['V001 · Mumbai→Pune', 74], ['V003 · Mumbai→Delhi', 61], ['V004 · Pune→Delhi', 82], ['V005 · Mumbai→Pune', 55]],
  },
  {
    id: 'shortage',
    num: '03',
    label: 'Vehicle Shortage',
    tag: 'Peak Mode',
    color: '#10b981',
    colorRaw: '16,185,129',
    icon: (
      <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <rect x="1" y="3" width="15" height="13"/><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/>
      </svg>
    ),
    desc: 'Fleet is reduced to 2 available vehicles. The solver maximises utilisation above all — best for peak season fleet crunches.',
    metrics: { trucks: 2, cost: '₹12.0k', util: '91%', carbon: '35 kg', saved: '52%' },
    bars: [['V001 · Mumbai→Pune', 95], ['V003 · Full Circuit', 91]],
  },
  {
    id: 'surge',
    num: '04',
    label: 'Demand Surge',
    tag: 'Stress Test',
    color: '#8b5cf6',
    colorRaw: '139,92,246',
    icon: (
      <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>
      </svg>
    ),
    desc: 'Shipment volume doubled to simulate Q4 demand spike. All 4 trucks deployed with heuristic solver fallback for >50 shipments.',
    metrics: { trucks: 4, cost: '₹19.0k', util: '82%', carbon: '71 kg', saved: '18%' },
    bars: [['V001', 88], ['V003', 92], ['V004', 79], ['V005', 82]],
  },
]

function MetricPill({ val, lbl, color }) {
  return (
    <div style={{ flex: 1, background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 10, padding: '0.65rem 0.8rem' }}>
      <div style={{ fontFamily: "'Syne', sans-serif", fontSize: '1.2rem', fontWeight: 800, color, lineHeight: 1, marginBottom: 2 }}>{val}</div>
      <div style={{ fontSize: '0.62rem', fontFamily: "'JetBrains Mono', monospace", color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>{lbl}</div>
    </div>
  )
}

export default function Scenarios() {
  const [running, setRunning]   = useState(null)
  const [results, setResults]   = useState({})
  const [selected, setSelected] = useState(null)

  const runScenario = async (id) => {
    setRunning(id)
    await new Promise(r => setTimeout(r, 1400))
    setResults(prev => ({ ...prev, [id]: true }))
    setRunning(null)
    setSelected(id)
  }

  const runAll = async () => {
    for (const s of SCENARIOS) {
      await runScenario(s.id)
      await new Promise(r => setTimeout(r, 200))
    }
  }

  const allDone = SCENARIOS.every(s => results[s.id])
  const sel = SCENARIOS.find(s => s.id === selected)
  const nav = useNavigate()

  return (
    <div className="lorri-scenarios">
      <Navbar />
      <style>{`
        .lorri-scenarios {
          min-height: 100vh;
          display: flex; flex-direction: column;
          position: relative; overflow-x: clip;
        }
        .lorri-scenarios::before {
          content: '';
          position: fixed; inset: 0; z-index: 0;
          background-image: radial-gradient(circle, rgba(var(--page-glow-rgb), 0.18) 1px, transparent 1px);
          background-size: 32px 32px;
          pointer-events: none;
          mask-image: radial-gradient(ellipse 80% 80% at 50% 50%, black 30%, transparent 100%);
        }
        .scn-inner {
          position: relative; z-index: 1;
          padding: 5rem 3rem 6rem;
          width: 100%;
        }

        /* ── Hero ── */
        .scn-hero {
          display: grid;
          grid-template-columns: 1fr auto;
          align-items: flex-end;
          gap: 2rem;
          margin-bottom: 3.5rem;
          padding-bottom: 2.5rem;
          border-bottom: 1px solid var(--border);
        }
        .scn-hero-tag {
          display: inline-flex; align-items: center; gap: 6px;
          padding: 5px 14px; border-radius: 9999px;
          border: 1px solid rgba(var(--page-glow-rgb), 0.45);
          background: rgba(var(--page-glow-rgb), 0.1);
          font-size: 0.7rem; font-family: 'JetBrains Mono', monospace;
          color: var(--page-accent); letter-spacing: 0.12em; text-transform: uppercase;
          margin-bottom: 1rem;
          opacity: 0; animation: fadeSlideUp 0.45s ease 0.05s forwards;
        }
        .scn-hero h1 {
          font-family: 'Syne', sans-serif;
          font-size: clamp(2.2rem, 4vw, 3.8rem);
          font-weight: 800; line-height: 1.04; letter-spacing: -0.025em;
          margin-bottom: 0.8rem;
        }
        .scn-hero-sub {
          font-size: 0.95rem; color: var(--text-secondary); line-height: 1.7;
          opacity: 0; animation: fadeSlideUp 0.45s ease 0.55s forwards;
        }
        .scn-hero-right {
          text-align: right;
          opacity: 0; animation: fadeSlideUp 0.45s ease 0.65s forwards;
        }
        .scn-hero-num {
          font-family: 'Syne', sans-serif;
          font-size: 2.8rem; font-weight: 800;
          color: var(--page-accent); line-height: 1;
        }
        .scn-hero-lbl {
          font-size: 0.72rem; color: var(--text-muted);
          font-family: 'JetBrains Mono', monospace;
          text-transform: uppercase; letter-spacing: 0.1em; margin-top: 4px;
        }

        /* ── Run All bar ── */
        .scn-toolbar {
          display: flex; align-items: center; gap: 1rem;
          margin-bottom: 2rem;
          opacity: 0; animation: fadeSlideUp 0.45s ease 0.7s forwards;
        }
        .scn-run-all-btn {
          display: inline-flex; align-items: center; gap: 8px;
          padding: 10px 22px; border-radius: 12px; border: none;
          background: var(--page-accent); color: #0a0a0a;
          font-weight: 700; font-size: 0.85rem; cursor: pointer;
          font-family: 'DM Sans', sans-serif;
          box-shadow: 0 0 24px rgba(var(--page-glow-rgb), 0.4);
          transition: all 0.22s;
        }
        .scn-run-all-btn:hover { transform: translateY(-2px); box-shadow: 0 0 42px rgba(var(--page-glow-rgb), 0.6); }
        .scn-run-all-btn:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
        .scn-toolbar-info {
          font-size: 0.72rem; font-family: 'JetBrains Mono', monospace;
          color: var(--text-muted);
        }

        /* ── Grid of scenario cards ── */
        .scn-cards-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 1.25rem;
          margin-bottom: 2.5rem;
        }
        .scn-card {
          background: var(--card);
          border: 1px solid var(--border);
          border-radius: 18px;
          overflow: hidden;
          cursor: pointer;
          transition: border-color 0.25s, box-shadow 0.25s;
          opacity: 0;
          animation: fadeSlideUp 0.5s ease forwards;
        }
        .scn-card.selected {
          box-shadow: 0 0 0 1px var(--page-accent), 0 0 32px rgba(var(--page-glow-rgb), 0.18);
        }
        .scn-card:hover { border-color: rgba(var(--page-glow-rgb), 0.4); }
        .scn-card-header {
          padding: 1.1rem 1.25rem;
          border-bottom: 1px solid var(--border);
          display: flex; align-items: center; gap: 0.75rem;
        }
        .scn-card-icon {
          width: 34px; height: 34px;
          border-radius: 10px;
          display: flex; align-items: center; justify-content: center;
          flex-shrink: 0;
        }
        .scn-card-num {
          font-family: 'JetBrains Mono', monospace;
          font-size: 0.62rem; color: var(--text-muted);
        }
        .scn-card-title {
          font-family: 'Syne', sans-serif;
          font-size: 1rem; font-weight: 700;
        }
        .scn-card-tag {
          margin-left: auto;
          font-size: 0.62rem; padding: 2px 7px;
          border-radius: 5px;
          font-family: 'JetBrains Mono', monospace;
          text-transform: uppercase; letter-spacing: 0.08em;
        }
        .scn-card-body { padding: 1.1rem 1.25rem; }
        .scn-card-desc {
          font-size: 0.82rem; color: var(--text-secondary);
          line-height: 1.65; margin-bottom: 1rem;
        }
        .scn-metric-row {
          display: flex; gap: 0.5rem; margin-bottom: 1rem;
        }
        .scn-bars { display: flex; flex-direction: column; gap: 0.45rem; }
        .scn-bar-lbl {
          display: flex; justify-content: space-between;
          font-size: 0.65rem; font-family: 'JetBrains Mono', monospace;
          color: var(--text-muted); margin-bottom: 3px;
        }
        .scn-bar-track {
          height: 5px; border-radius: 9999px;
          background: rgba(255,255,255,0.05); overflow: hidden;
        }
        .scn-bar-fill {
          height: 100%; border-radius: 9999px;
          transition: width 0.8s cubic-bezier(0.22,1,0.36,1);
        }
        .scn-card-footer {
          padding: 0.9rem 1.25rem;
          border-top: 1px solid var(--border);
          display: flex; align-items: center; justify-content: space-between;
        }
        .scn-run-btn {
          display: inline-flex; align-items: center; gap: 6px;
          padding: 7px 16px; border-radius: 9999px; border: none;
          font-size: 0.72rem; font-weight: 600;
          font-family: 'JetBrains Mono', monospace;
          letter-spacing: 0.06em; text-transform: uppercase;
          cursor: pointer; transition: all 0.2s;
        }
        .scn-run-btn:disabled { cursor: not-allowed; opacity: 0.6; }

        /* ── Compare table ── */
        .scn-compare {
          background: var(--card);
          border: 1px solid var(--border);
          border-radius: 18px;
          overflow: hidden;
          opacity: 0;
          animation: fadeSlideUp 0.5s ease 0.5s forwards;
        }
        .scn-compare-header {
          padding: 1.2rem 1.5rem;
          border-bottom: 1px solid var(--border);
        }
        .scn-compare-title {
          font-family: 'Syne', sans-serif;
          font-size: 1rem; font-weight: 700; margin-bottom: 2px;
        }
        .scn-compare-sub {
          font-size: 0.68rem; font-family: 'JetBrains Mono', monospace;
          color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.1em;
        }
        .scn-table { width: 100%; border-collapse: collapse; }
        .scn-table th {
          padding: 0.75rem 1.25rem;
          font-size: 0.65rem; font-family: 'JetBrains Mono', monospace;
          text-transform: uppercase; letter-spacing: 0.1em;
          color: var(--text-muted); text-align: left;
          border-bottom: 1px solid var(--border);
        }
        .scn-table td {
          padding: 0.9rem 1.25rem;
          font-size: 0.82rem;
          border-bottom: 1px solid rgba(255,255,255,0.04);
        }
        .scn-table tr:last-child td { border-bottom: none; }
        .scn-table tr:hover td { background: rgba(var(--page-glow-rgb), 0.03); }
        .scn-best-badge {
          font-size: 0.6rem;
          font-family: 'JetBrains Mono', monospace;
          padding: 2px 6px; border-radius: 4px;
          text-transform: uppercase; letter-spacing: 0.08em;
          margin-left: 6px;
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
        @keyframes spinIcon { to { transform: rotate(360deg); } }
        .lorri-footer { border-top: 1px solid var(--border); position: relative; z-index: 1; }
        .footer-grid { padding: 3.5rem 3rem 2rem; display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 3rem; }
        .footer-brand { font-family: 'Syne', sans-serif; font-size: 1.15rem; font-weight: 800; color: var(--page-accent); display: flex; align-items: center; gap: 8px; margin-bottom: 0.6rem; }
        .footer-desc { font-size: 0.82rem; color: var(--text-muted); line-height: 1.7; max-width: 230px; margin-bottom: 1.2rem; }
        .footer-badges { display: flex; flex-wrap: wrap; gap: 0.4rem; }
        .footer-badge { font-size: 0.65rem; font-family: 'JetBrains Mono', monospace; padding: 3px 8px; border-radius: 5px; border: 1px solid var(--border); color: var(--text-muted); cursor: default; transition: all 0.2s; }
        .footer-badge:hover { border-color: var(--page-accent); color: var(--page-accent); }
        .footer-col-title { font-family: 'Syne', sans-serif; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.12em; color: var(--text-secondary); margin-bottom: 1.1rem; }
        .footer-link { display: block; font-size: 0.82rem; color: var(--text-muted); margin-bottom: 0.55rem; cursor: pointer; text-decoration: none; transition: all 0.2s ease; width: fit-content; }
        .footer-link:hover { color: var(--page-accent); transform: translateX(3px); text-shadow: 0 0 10px rgba(var(--page-glow-rgb), 0.5); }
        .footer-bottom { border-top: 1px solid var(--border); padding: 1.2rem 3rem; display: flex; align-items: center; justify-content: space-between; }
        .footer-bottom-l { font-size: 0.72rem; color: var(--text-muted); font-family: 'JetBrains Mono', monospace; }
        .footer-bottom-r { display: flex; gap: 1.5rem; }
        .footer-bottom-link { font-size: 0.72rem; color: var(--text-muted); cursor: pointer; transition: color 0.2s; }
        .footer-bottom-link:hover { color: var(--page-accent); }
      `}</style>

      <div className="scn-inner">

        {/* ════ HERO ════ */}
        <div className="scn-hero">
          <div>
            <div className="scn-hero-tag">
              <svg viewBox="0 0 24 24" width="10" height="10" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
              What-If Engine
            </div>
            <h1>
              <div className="blur-line">
                {['What-If'].map((w, i) => (
                  <span key={w} className="blur-word" style={{ animationDelay: `${0.1 + i * 0.1}s` }}>{w}</span>
                ))}
              </div>
              <div className="blur-line" style={{ color: 'var(--page-accent)' }}>
                {['Scenarios.'].map((w, i) => (
                  <span key={w} className="blur-word" style={{ animationDelay: `${0.22 + i * 0.12}s` }}>{w}</span>
                ))}
              </div>
            </h1>
            <p className="scn-hero-sub">
              Run the same shipment batch under four different business conditions. Compare cost, carbon, and utilisation side-by-side to pick the plan that fits your operation.
            </p>
          </div>
          <div className="scn-hero-right">
            <div className="scn-hero-num">4</div>
            <div className="scn-hero-lbl">Scenarios</div>
          </div>
        </div>

        {/* ── Toolbar ── */}
        <div className="scn-toolbar">
          <button
            className="scn-run-all-btn"
            onClick={runAll}
            disabled={running !== null}
          >
            {running
              ? <><Loader2 size={14} style={{ animation: 'spinIcon 1s linear infinite' }} /> Running…</>
              : <><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="5 3 19 12 5 21 5 3"/></svg> Run All Scenarios</>
            }
          </button>
          <span className="scn-toolbar-info">
            {allDone ? `All 4 scenarios complete — ${SCENARIOS.find(s => s.id === 'shortage')?.metrics.cost} best cost` : `${Object.keys(results).length}/4 complete`}
          </span>
        </div>

        {/* ── Cards grid ── */}
        <div className="scn-cards-grid">
          {SCENARIOS.map((s, idx) => {
            const isDone    = !!results[s.id]
            const isRunning = running === s.id
            const isSel     = selected === s.id
            return (
              <div
                key={s.id}
                className={`scn-card ${isSel ? 'selected' : ''}`}
                style={{
                  animationDelay: `${0.1 + idx * 0.08}s`,
                  borderColor: isSel ? s.color : undefined,
                }}
                onClick={() => isDone && setSelected(s.id)}
              >
                <div className="scn-card-header">
                  <div className="scn-card-icon" style={{ background: `${s.color}18`, border: `1px solid ${s.color}28`, color: s.color }}>
                    {s.icon}
                  </div>
                  <div>
                    <div className="scn-card-num">No. {s.num}</div>
                    <div className="scn-card-title">{s.label}</div>
                  </div>
                  <span className="scn-card-tag" style={{ background: `${s.color}18`, border: `1px solid ${s.color}28`, color: s.color }}>
                    {s.tag}
                  </span>
                </div>

                <div className="scn-card-body">
                  <p className="scn-card-desc">{s.desc}</p>

                  {isDone ? (
                    <>
                      <div className="scn-metric-row">
                        <MetricPill val={s.metrics.trucks + ' trucks'} lbl="Fleet Used" color={s.color} />
                        <MetricPill val={s.metrics.cost} lbl="Total Cost" color={s.color} />
                        <MetricPill val={s.metrics.util} lbl="Avg Util" color={s.color} />
                      </div>
                      <div className="scn-bars">
                        {s.bars.map(([lbl, pct]) => (
                          <div key={lbl}>
                            <div className="scn-bar-lbl"><span>{lbl}</span><span style={{ color: s.color }}>{pct}%</span></div>
                            <div className="scn-bar-track">
                              <div className="scn-bar-fill" style={{ width: `${pct}%`, background: `linear-gradient(90deg, ${s.color}88, ${s.color})` }} />
                            </div>
                          </div>
                        ))}
                      </div>
                    </>
                  ) : (
                    <div style={{ height: 80, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(255,255,255,0.02)', borderRadius: 10, border: '1px dashed var(--border)' }}>
                      <span style={{ fontSize: '0.72rem', fontFamily: 'JetBrains Mono', color: 'var(--text-muted)' }}>
                        {isRunning ? 'Solving…' : 'Not run yet'}
                      </span>
                    </div>
                  )}
                </div>

                <div className="scn-card-footer">
                  <span style={{ fontSize: '0.68rem', fontFamily: 'JetBrains Mono', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
                    {isDone ? `✓ Saved ${s.metrics.saved}` : isRunning ? 'Running MIP…' : 'Ready'}
                  </span>
                  <button
                    className="scn-run-btn"
                    style={{
                      background: `${s.color}18`,
                      border: `1px solid ${s.color}40`,
                      color: s.color,
                    }}
                    onClick={(e) => { e.stopPropagation(); runScenario(s.id) }}
                    disabled={running !== null}
                  >
                    {isRunning
                      ? <><Loader2 size={12} style={{ animation: 'spinIcon 1s linear infinite' }} /> Running</>
                      : isDone ? 'Re-run' : 'Run →'
                    }
                  </button>
                </div>
              </div>
            )
          })}
        </div>

        {/* ── Compare table (visible when 2+ done) ── */}
        {Object.keys(results).length >= 2 && (
          <div className="scn-compare">
            <div className="scn-compare-header">
              <div className="scn-compare-title">Side-by-Side Comparison</div>
              <div className="scn-compare-sub">/ scenarios · cost · util · carbon</div>
            </div>
            <table className="scn-table">
              <thead>
                <tr>
                  {['Scenario', 'Trucks', 'Total Cost', 'Avg Util', 'CO₂ Saved', 'Cost Saving'].map(h => (
                    <th key={h}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {SCENARIOS.filter(s => results[s.id]).map(s => {
                  const isBestCost = s.id === 'shortage'
                  const isBestUtil = s.id === 'shortage'
                  return (
                    <tr key={s.id} style={{ cursor: 'pointer' }} onClick={() => setSelected(s.id)}>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <div style={{ width: 8, height: 8, borderRadius: '50%', background: s.color, boxShadow: `0 0 6px ${s.color}` }} />
                          <span style={{ fontFamily: 'Syne, sans-serif', fontWeight: 700 }}>{s.label}</span>
                        </div>
                      </td>
                      <td style={{ fontFamily: 'JetBrains Mono', color: 'var(--text-secondary)' }}>{s.metrics.trucks}</td>
                      <td style={{ fontFamily: 'JetBrains Mono', color: s.color, fontWeight: 700 }}>
                        {s.metrics.cost}
                        {isBestCost && <span className="scn-best-badge" style={{ background: `${s.color}18`, color: s.color }}>Best</span>}
                      </td>
                      <td style={{ fontFamily: 'JetBrains Mono', color: 'var(--text-secondary)' }}>
                        {s.metrics.util}
                        {isBestUtil && <span className="scn-best-badge" style={{ background: `${s.color}18`, color: s.color }}>Best</span>}
                      </td>
                      <td style={{ fontFamily: 'JetBrains Mono', color: 'var(--text-muted)' }}>{s.metrics.carbon}</td>
                      <td style={{ fontFamily: 'JetBrains Mono', color: s.color }}>{s.metrics.saved}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
        </div>

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