import { useState } from 'react'
import { Zap, Loader2 } from 'lucide-react'
import FoxMascot from '@/components/FoxMascot'
import ConsolidationPlan from '@/components/ConsolidationPlan'
import MetricsDashboard from '@/components/MetricsDashboard'
import { DEMO_PLAN } from '@/data/demoData'

const SOLVE_STEPS = [
  { label: 'Building compatibility graph', detail: 'Checking weight, volume & time windows' },
  { label: 'Running OR-Tools MIP solver',  detail: 'Binary decision variables assigned' },
  { label: 'Generating AI insights',        detail: 'LangChain agents analysing output' },
]

export default function Optimize() {
  const [status, setStatus] = useState('idle')
  const [plan,   setPlan]   = useState(null)
  const [activeStep, setActiveStep] = useState(-1)

  const runOptimizer = async () => {
    setStatus('running')
    setPlan(null)
    setActiveStep(0)
    await new Promise(r => setTimeout(r, 900))
    setActiveStep(1)
    await new Promise(r => setTimeout(r, 800))
    setActiveStep(2)
    await new Promise(r => setTimeout(r, 600))
    setPlan(DEMO_PLAN)
    setStatus('done')
    setActiveStep(-1)
  }

  return (
    <div className="lorri-optimize">
      <style>{`
        /* ── Base ── */
        .lorri-optimize {
          min-height: 100vh;
          display: flex;
          flex-direction: column;
          position: relative;
          overflow-x: clip;
        }

        /* ── Dot grid (same as Home) ── */
        .lorri-optimize::before {
          content: '';
          position: fixed;
          inset: 0;
          z-index: 0;
          background-image: radial-gradient(circle, rgba(var(--page-glow-rgb), 0.18) 1px, transparent 1px);
          background-size: 32px 32px;
          pointer-events: none;
          mask-image: radial-gradient(ellipse 80% 80% at 50% 50%, black 30%, transparent 100%);
        }

        /* ── Inner layout ── */
        .opt-inner {
          position: relative;
          z-index: 1;
          max-width: 1160px;
          margin: 0 auto;
          padding: 5rem 3rem 6rem;
          width: 100%;
        }

        /* ── Page hero ── */
        .opt-hero {
          display: grid;
          grid-template-columns: 1fr auto;
          align-items: flex-end;
          gap: 2rem;
          margin-bottom: 3.5rem;
          padding-bottom: 2.5rem;
          border-bottom: 1px solid var(--border);
        }
        .opt-hero-tag {
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
          margin-bottom: 1rem;
          opacity: 0;
          animation: fadeSlideUp 0.45s ease 0.05s forwards;
        }
        .opt-hero h1 {
          font-family: 'Syne', sans-serif;
          font-size: clamp(2.2rem, 4vw, 3.8rem);
          font-weight: 800;
          line-height: 1.04;
          letter-spacing: -0.025em;
          margin-bottom: 0.8rem;
        }
        .opt-hero-sub {
          font-size: 0.95rem;
          color: var(--text-secondary);
          line-height: 1.7;
          opacity: 0;
          animation: fadeSlideUp 0.45s ease 0.55s forwards;
        }
        .opt-hero-badge-row {
          display: flex;
          gap: 0.4rem;
          flex-wrap: wrap;
          margin-top: 1.2rem;
          opacity: 0;
          animation: fadeSlideUp 0.45s ease 0.7s forwards;
        }
        .opt-badge {
          font-size: 0.65rem;
          font-family: 'JetBrains Mono', monospace;
          padding: 3px 8px;
          border-radius: 5px;
          border: 1px solid var(--border);
          color: var(--text-muted);
        }
        .opt-hero-meta {
          text-align: right;
          opacity: 0;
          animation: fadeSlideUp 0.45s ease 0.65s forwards;
        }
        .opt-hero-meta-num {
          font-family: 'Syne', sans-serif;
          font-size: 2.8rem;
          font-weight: 800;
          color: var(--page-accent);
          line-height: 1;
        }
        .opt-hero-meta-lbl {
          font-size: 0.72rem;
          color: var(--text-muted);
          font-family: 'JetBrains Mono', monospace;
          text-transform: uppercase;
          letter-spacing: 0.1em;
          margin-top: 4px;
        }

        /* ── Two-column layout ── */
        .opt-grid {
          display: grid;
          grid-template-columns: 1fr 1.6fr;
          gap: 1.5rem;
          align-items: start;
        }

        /* ── Trigger card ── */
        .opt-trigger-card {
          background: var(--card);
          border: 1px solid var(--border);
          border-radius: 18px;
          overflow: hidden;
          opacity: 0;
          animation: fadeSlideUp 0.5s ease 0.3s forwards;
          position: sticky;
          top: 2rem;
        }
        .opt-trigger-header {
          padding: 1.2rem 1.5rem;
          border-bottom: 1px solid var(--border);
          display: flex;
          align-items: center;
          justify-content: space-between;
        }
        .opt-trigger-header-label {
          font-size: 0.68rem;
          font-family: 'JetBrains Mono', monospace;
          color: var(--text-muted);
          text-transform: uppercase;
          letter-spacing: 0.12em;
        }
        .opt-status-dot {
          width: 7px; height: 7px;
          border-radius: 50%;
          background: var(--page-accent);
          box-shadow: 0 0 8px var(--page-accent);
          animation: pulse 2s ease-in-out infinite;
        }
        @keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.5;transform:scale(0.8)} }

        .opt-trigger-body {
          padding: 2rem 1.5rem;
          text-align: center;
        }

        /* ── Shipment summary mini-list ── */
        .opt-shipment-list {
          margin-bottom: 1.5rem;
          display: flex;
          flex-direction: column;
          gap: 0.4rem;
        }
        .opt-ship-row {
          display: flex;
          align-items: center;
          gap: 0.6rem;
          padding: 0.45rem 0.75rem;
          border-radius: 8px;
          background: rgba(var(--page-glow-rgb), 0.04);
          border: 1px solid rgba(var(--page-glow-rgb), 0.1);
          font-size: 0.72rem;
          font-family: 'JetBrains Mono', monospace;
          color: var(--text-muted);
          text-align: left;
        }
        .opt-ship-id {
          color: var(--page-accent);
          min-width: 36px;
        }
        .opt-ship-route { flex: 1; }
        .opt-ship-weight { color: var(--text-secondary); }

        /* ── Run button ── */
        .opt-run-btn {
          display: inline-flex; align-items: center; gap: 8px;
          width: 100%;
          justify-content: center;
          padding: 0.85rem 2rem; border-radius: 12px; border: none;
          background: var(--page-accent); color: #0a0a0a;
          font-weight: 700; font-size: 0.9rem; cursor: pointer;
          font-family: 'DM Sans', sans-serif;
          box-shadow: 0 0 28px rgba(var(--page-glow-rgb), 0.45);
          transition: all 0.22s ease;
        }
        .opt-run-btn:hover {
          transform: translateY(-2px);
          box-shadow: 0 0 48px rgba(var(--page-glow-rgb), 0.65);
        }
        .opt-run-btn:disabled {
          opacity: 0.6; cursor: not-allowed; transform: none;
        }

        /* ── Solve progress ── */
        .opt-progress-wrap {
          padding: 1.5rem;
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }
        .opt-progress-step {
          display: flex;
          align-items: flex-start;
          gap: 0.75rem;
          padding: 0.7rem 0.9rem;
          border-radius: 10px;
          border: 1px solid transparent;
          transition: all 0.3s ease;
        }
        .opt-progress-step.active {
          background: rgba(var(--page-glow-rgb), 0.08);
          border-color: rgba(var(--page-glow-rgb), 0.3);
        }
        .opt-progress-step.done-step {
          border-color: rgba(var(--page-glow-rgb), 0.15);
        }
        .opt-step-icon {
          width: 20px; height: 20px;
          border-radius: 50%;
          display: flex; align-items: center; justify-content: center;
          flex-shrink: 0;
          font-size: 0.65rem;
          font-family: 'JetBrains Mono', monospace;
          margin-top: 1px;
        }
        .opt-step-icon.pending {
          border: 1px solid var(--border);
          color: var(--text-muted);
        }
        .opt-step-icon.running {
          border: 1px solid var(--page-accent);
          color: var(--page-accent);
          animation: spinIcon 1s linear infinite;
        }
        @keyframes spinIcon { to { transform: rotate(360deg); } }
        .opt-step-icon.complete {
          background: rgba(var(--page-glow-rgb), 0.15);
          border: 1px solid var(--page-accent);
          color: var(--page-accent);
        }
        .opt-step-lbl {
          font-size: 0.8rem;
          font-weight: 500;
          color: var(--text-secondary);
        }
        .opt-step-detail {
          font-size: 0.68rem;
          font-family: 'JetBrains Mono', monospace;
          color: var(--text-muted);
          margin-top: 2px;
        }

        /* ── Results panel ── */
        .opt-results-wrap {
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
          opacity: 0;
          animation: fadeSlideUp 0.5s ease 0.4s forwards;
        }

        /* ── Section divider (matches Home) ── */
        .opt-divider {
          display: flex;
          align-items: center;
          gap: 1rem;
          margin-bottom: 1.2rem;
        }
        .opt-divider-label {
          font-size: 0.68rem;
          font-family: 'JetBrains Mono', monospace;
          color: var(--text-muted);
          text-transform: uppercase;
          letter-spacing: 0.14em;
          white-space: nowrap;
        }
        .opt-divider-line {
          flex: 1; height: 1px;
          background: var(--border);
        }

        /* ── Empty state ── */
        .opt-empty {
          background: var(--card);
          border: 1px solid var(--border);
          border-radius: 18px;
          padding: 4rem 2rem;
          text-align: center;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 0.75rem;
          min-height: 320px;
          opacity: 0;
          animation: fadeSlideUp 0.5s ease 0.45s forwards;
        }
        .opt-empty-icon {
          width: 48px; height: 48px;
          border-radius: 14px;
          border: 1px solid rgba(var(--page-glow-rgb), 0.3);
          background: rgba(var(--page-glow-rgb), 0.06);
          display: flex; align-items: center; justify-content: center;
          margin-bottom: 0.5rem;
        }
        .opt-empty-title {
          font-family: 'Syne', sans-serif;
          font-size: 1rem;
          font-weight: 700;
          color: var(--text-secondary);
        }
        .opt-empty-sub {
          font-size: 0.78rem;
          color: var(--text-muted);
          font-family: 'JetBrains Mono', monospace;
        }

        /* ── Success banner ── */
        .opt-success-banner {
          background: rgba(var(--page-glow-rgb), 0.06);
          border: 1px solid rgba(var(--page-glow-rgb), 0.3);
          border-radius: 14px;
          padding: 1rem 1.5rem;
          display: flex;
          align-items: center;
          gap: 1.2rem;
        }
        .opt-success-banner-icon {
          width: 36px; height: 36px;
          border-radius: 10px;
          background: rgba(var(--page-glow-rgb), 0.12);
          border: 1px solid rgba(var(--page-glow-rgb), 0.35);
          display: flex; align-items: center; justify-content: center;
          flex-shrink: 0;
          color: var(--page-accent);
        }
        .opt-success-banner-title {
          font-family: 'Syne', sans-serif;
          font-size: 1rem;
          font-weight: 700;
          color: var(--page-accent);
          margin-bottom: 2px;
        }
        .opt-success-banner-sub {
          font-size: 0.75rem;
          color: var(--text-muted);
          font-family: 'JetBrains Mono', monospace;
        }
        .opt-success-stats {
          margin-left: auto;
          display: flex;
          gap: 1.5rem;
        }
        .opt-success-stat-num {
          font-family: 'Syne', sans-serif;
          font-size: 1.4rem;
          font-weight: 800;
          color: var(--page-accent);
          line-height: 1;
        }
        .opt-success-stat-lbl {
          font-size: 0.62rem;
          color: var(--text-muted);
          font-family: 'JetBrains Mono', monospace;
          text-transform: uppercase;
          letter-spacing: 0.08em;
        }

        /* ── Animations ── */
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
          0%   { opacity:0;   filter:blur(16px); transform:translateX(-14px); }
          55%  { opacity:0.9; filter:blur(2px);  transform:translateX(2px); }
          100% { opacity:1;   filter:blur(0);    transform:translateX(0); }
        }
      `}</style>

      <div className="opt-inner">

        {/* ════ PAGE HERO ════ */}
        <div className="opt-hero">
          <div>
            <div className="opt-hero-tag">
              <Zap size={10} /> MIP Solver · OR-Tools
            </div>
            <h1>
              <div className="blur-line">
                {['Consolidate.'].map((w, i) => (
                  <span key={w} className="blur-word" style={{ animationDelay: `${0.1 + i * 0.1}s` }}>{w}</span>
                ))}
              </div>
              <div className="blur-line" style={{ color: 'var(--page-accent)' }}>
                {['Optimize.', 'Save.'].map((w, i) => (
                  <span key={w} className="blur-word" style={{ animationDelay: `${0.2 + i * 0.12}s` }}>{w}</span>
                ))}
              </div>
            </h1>
            <p className="opt-hero-sub">
              Run the binary MIP solver on your shipment batch — get the best truck assignments, cost savings, and AI-powered insights in seconds.
            </p>
            <div className="opt-hero-badge-row">
              {['6 Shipments', '4 Vehicles', 'Demo Mode', 'LangChain Agents'].map(b => (
                <span key={b} className="opt-badge">{b}</span>
              ))}
            </div>
          </div>

          <div className="opt-hero-meta">
            <div className="opt-hero-meta-num">44%</div>
            <div className="opt-hero-meta-lbl">Avg Cost Reduction</div>
          </div>
        </div>

        {/* ════ MAIN GRID ════ */}
        <div className="opt-grid">

          {/* ── LEFT: Trigger card ── */}
          <div className="opt-trigger-card">
            <div className="opt-trigger-header">
              <span className="opt-trigger-header-label">/ optimizer · v2.1</span>
              <div className="opt-status-dot" />
            </div>

            <div className="opt-trigger-body">
              <FoxMascot
                size={status === 'running' ? 'lg' : 'md'}
                variant={status === 'idle' ? 'idle' : status === 'running' ? 'thinking' : 'happy'}
                style={{ margin: '0 auto 1.5rem' }}
              />
              <div style={{ marginBottom: '1.5rem', textAlign: 'left' }}>
                <p style={{ fontSize: '0.68rem', fontFamily: 'JetBrains Mono, monospace', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: '0.75rem' }}>
                  Shipment Batch
                </p>
                <div className="opt-shipment-list">
                  {[
                    { id:'S001', route:'Mumbai → Pune',  wt:'850 kg' },
                    { id:'S002', route:'Mumbai → Pune',  wt:'620 kg' },
                    { id:'S003', route:'Pune → Delhi',   wt:'1100 kg' },
                    { id:'S004', route:'Mumbai → Delhi', wt:'450 kg' },
                    { id:'S005', route:'Mumbai → Pune',  wt:'300 kg' },
                    { id:'S006', route:'Pune → Delhi',   wt:'780 kg' },
                  ].map(s => (
                    <div key={s.id} className="opt-ship-row">
                      <span className="opt-ship-id">{s.id}</span>
                      <span className="opt-ship-route">{s.route}</span>
                      <span className="opt-ship-weight">{s.wt}</span>
                    </div>
                  ))}
                </div>
              </div>

              <button
                className="opt-run-btn"
                onClick={runOptimizer}
                disabled={status === 'running'}
              >
                {status === 'running'
                  ? <><Loader2 size={15} style={{ animation: 'spinIcon 1s linear infinite' }} /> Solving…</>
                  : <><Zap size={15} /> {status === 'done' ? 'Re-run Optimizer' : 'Run Optimizer'}</>
                }
              </button>
            </div>

            {/* Solve progress steps */}
            {status === 'running' && (
              <div className="opt-progress-wrap">
                <div style={{ height: '1px', background: 'var(--border)', marginBottom: '0.5rem' }} />
                {SOLVE_STEPS.map((step, i) => {
                  const state = i < activeStep ? 'complete' : i === activeStep ? 'running' : 'pending'
                  return (
                    <div key={step.label} className={`opt-progress-step ${state === 'running' ? 'active' : state === 'complete' ? 'done-step' : ''}`}>
                      <div className={`opt-step-icon ${state}`}>
                        {state === 'complete' ? '✓' : state === 'running' ? '↻' : String(i + 1)}
                      </div>
                      <div>
                        <div className="opt-step-lbl">{step.label}</div>
                        {state !== 'pending' && <div className="opt-step-detail">{step.detail}</div>}
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>

          {/* ── RIGHT: Results ── */}
          <div className="opt-results-wrap">

            {/* Success banner */}
            {status === 'done' && (
              <div className="opt-success-banner" style={{ opacity: 0, animation: 'fadeSlideUp 0.4s ease 0.1s forwards' }}>
                <div className="opt-success-banner-icon">
                  <Zap size={18} />
                </div>
                <div>
                  <div className="opt-success-banner-title">✓ Optimization complete</div>
                  <div className="opt-success-banner-sub">3 trucks assigned · heuristic solver · 2.1s</div>
                </div>
                <div className="opt-success-stats">
                  {[['₹13.5k','Cost Total'],['44%','Saved'],['91%','Max Util']].map(([n,l]) => (
                    <div key={l} style={{ textAlign: 'center' }}>
                      <div className="opt-success-stat-num">{n}</div>
                      <div className="opt-success-stat-lbl">{l}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Plan + Metrics */}
            {plan ? (
              <>
                <div style={{ opacity: 0, animation: 'fadeSlideUp 0.5s ease 0.2s forwards' }}>
                  <div className="opt-divider">
                    <span className="opt-divider-label">— Consolidation Plan</span>
                    <div className="opt-divider-line" />
                  </div>
                  <ConsolidationPlan plan={plan} />
                </div>

                <div style={{ opacity: 0, animation: 'fadeSlideUp 0.5s ease 0.35s forwards' }}>
                  <div className="opt-divider">
                    <span className="opt-divider-label">— Performance Metrics</span>
                    <div className="opt-divider-line" />
                  </div>
                  <MetricsDashboard />
                </div>
              </>
            ) : (
              <div className="opt-empty">
                <div className="opt-empty-icon">
                  <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="var(--page-accent)" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
                  </svg>
                </div>
                <div className="opt-empty-title">
                  {status === 'running' ? 'Solving…' : 'Results will appear here'}
                </div>
                <div className="opt-empty-sub">
                  {status === 'running'
                    ? 'Running MIP solver · assigning shipments to trucks'
                    : 'Run the optimizer to see the consolidation plan'}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}