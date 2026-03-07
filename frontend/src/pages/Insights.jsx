import { useState } from 'react'
import { Loader2 } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import Navbar from '@/components/layout/Navbar'
import FoxMascot from '@/components/FoxMascot'
import { DEMO_PLAN } from '@/data/demoData'

const AGENTS = [
  {
    id: 'validator',
    num: '01',
    tag: 'Validation',
    label: 'Validation Agent',
    color: '#06b6d4',
    icon: (
      <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
      </svg>
    ),
    insight: 'All 6 shipments passed constraint validation. Weight and volume bounds satisfied. Time windows are feasible for proposed consolidations.',
    metric: { val: '6/6', lbl: 'Valid' },
  },
  {
    id: 'insight',
    num: '02',
    tag: 'Insight',
    label: 'Insight Agent',
    color: 'var(--page-accent)',
    icon: (
      <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="8" r="5"/>
        <path d="M9 13v2a3 3 0 0 0 6 0v-2"/>
        <line x1="9" y1="17" x2="15" y2="17"/>
        <line x1="12" y1="19" x2="12" y2="21"/>
      </svg>
    ),
    insight: '91% utilisation on the Mumbai–Pune lane achieved by grouping S001, S002, and S005. ₹10.5k saved versus individual dispatch. V003 on the Delhi run is under-utilized at 32% — consider demand buffering.',
    metric: { val: '₹10.5k', lbl: 'Saved' },
  },
  {
    id: 'relaxation',
    num: '03',
    tag: 'Relaxation',
    label: 'Constraint Relaxation Agent',
    color: '#10b981',
    icon: (
      <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10"/>
        <line x1="12" y1="8" x2="12" y2="12"/>
        <line x1="12" y1="16" x2="12.01" y2="16"/>
      </svg>
    ),
    insight: 'Relaxing S003\'s delivery window by 45 minutes enables consolidation with S006 on the Pune–Delhi lane. Estimated additional saving: ₹2.1k. No SLA breach if customer notified.',
    metric: { val: '+45m', lbl: 'Window' },
  },
  {
    id: 'recommender',
    num: '04',
    tag: 'Recommender',
    label: 'Scenario Recommender',
    color: '#8b5cf6',
    icon: (
      <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <line x1="18" y1="20" x2="18" y2="10"/>
        <line x1="12" y1="20" x2="12" y2="4"/>
        <line x1="6" y1="20" x2="6" y2="14"/>
        <line x1="2" y1="20" x2="22" y2="20"/>
      </svg>
    ),
    insight: 'Flexible SLA scenario delivers the best cost outcome at ₹13.5k with 76% avg utilization. Strict SLA is recommended only when compliance is contractually mandated. Vehicle Shortage hits 91% utilization — ideal for peak season planning.',
    metric: { val: 'Flex', lbl: 'Recommended' },
  },
]

export default function Insights() {
  const [status, setStatus]         = useState('idle')
  const [revealed, setRevealed]     = useState([])
  const [activeAgent, setActiveAgent] = useState(null)
  const nav = useNavigate()

  const runPipeline = async () => {
    setStatus('running')
    setRevealed([])
    for (let i = 0; i < AGENTS.length; i++) {
      setActiveAgent(AGENTS[i].id)
      await new Promise(r => setTimeout(r, 900 + i * 150))
      setRevealed(prev => [...prev, AGENTS[i].id])
    }
    setActiveAgent(null)
    setStatus('done')
  }

  return (
    <div className="lorri-insights">
      <Navbar />
      <style>{`
        .lorri-insights {
          min-height: 100vh;
          display: flex;
          flex-direction: column;
          position: relative;
          overflow-x: clip;
        }
        .lorri-insights::before {
          content: '';
          position: fixed;
          inset: 0;
          z-index: 0;
          background-image: radial-gradient(circle, rgba(var(--page-glow-rgb), 0.18) 1px, transparent 1px);
          background-size: 32px 32px;
          pointer-events: none;
          mask-image: radial-gradient(ellipse 80% 80% at 50% 50%, black 30%, transparent 100%);
        }
        .ins-inner {
          position: relative; z-index: 1;
          padding: 5rem 3rem 6rem;
          width: 100%;
        }

        /* ── Hero ── */
        .ins-hero {
          display: grid;
          grid-template-columns: 1fr auto;
          align-items: flex-end;
          gap: 2rem;
          margin-bottom: 3.5rem;
          padding-bottom: 2.5rem;
          border-bottom: 1px solid var(--border);
        }
        .ins-hero-tag {
          display: inline-flex;
          align-items: center; gap: 6px;
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
        .ins-hero h1 {
          font-family: 'Syne', sans-serif;
          font-size: clamp(2.2rem, 4vw, 3.8rem);
          font-weight: 800;
          line-height: 1.04;
          letter-spacing: -0.025em;
          margin-bottom: 0.8rem;
        }
        .ins-hero-sub {
          font-size: 0.95rem;
          color: var(--text-secondary);
          line-height: 1.7;
          opacity: 0;
          animation: fadeSlideUp 0.45s ease 0.55s forwards;
        }
        .ins-pipeline-badge {
          display: flex;
          align-items: center;
          gap: 0;
          opacity: 0;
          animation: fadeSlideUp 0.45s ease 0.7s forwards;
          margin-top: 1.2rem;
        }
        .ins-pipeline-step {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 0.65rem;
          font-family: 'JetBrains Mono', monospace;
          color: var(--text-muted);
          padding: 3px 10px;
          border: 1px solid var(--border);
          border-radius: 5px;
          white-space: nowrap;
        }
        .ins-pipeline-arrow {
          width: 20px; height: 1px;
          background: var(--border);
          position: relative;
        }
        .ins-pipeline-arrow::after {
          content: '›';
          position: absolute;
          right: -4px; top: -7px;
          color: var(--text-muted);
          font-size: 0.7rem;
        }
        .ins-hero-agent-count {
          text-align: right;
          opacity: 0;
          animation: fadeSlideUp 0.45s ease 0.65s forwards;
        }
        .ins-hero-num {
          font-family: 'Syne', sans-serif;
          font-size: 2.8rem;
          font-weight: 800;
          color: var(--page-accent);
          line-height: 1;
        }
        .ins-hero-lbl {
          font-size: 0.72rem;
          color: var(--text-muted);
          font-family: 'JetBrains Mono', monospace;
          text-transform: uppercase;
          letter-spacing: 0.1em;
          margin-top: 4px;
        }

        /* ── Main grid ── */
        .ins-grid {
          display: grid;
          grid-template-columns: 1fr 1.6fr;
          gap: 1.5rem;
          align-items: start;
        }

        /* ── Control card ── */
        .ins-control-card {
          background: var(--card);
          border: 1px solid var(--border);
          border-radius: 18px;
          overflow: hidden;
          opacity: 0;
          animation: fadeSlideUp 0.5s ease 0.3s forwards;
          position: sticky;
          top: 2rem;
        }
        .ins-ctrl-header {
          padding: 1.2rem 1.5rem;
          border-bottom: 1px solid var(--border);
          display: flex;
          align-items: center;
          justify-content: space-between;
        }
        .ins-ctrl-header-label {
          font-size: 0.68rem;
          font-family: 'JetBrains Mono', monospace;
          color: var(--text-muted);
          text-transform: uppercase;
          letter-spacing: 0.12em;
        }
        .ins-status-dot {
          width: 7px; height: 7px;
          border-radius: 50%;
          background: var(--page-accent);
          box-shadow: 0 0 8px var(--page-accent);
          animation: pulse 2s ease-in-out infinite;
        }
        @keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.5;transform:scale(0.8)} }

        .ins-ctrl-body { padding: 1.5rem; }

        /* Agent mini-list */
        .ins-agent-list {
          display: flex;
          flex-direction: column;
          gap: 0.4rem;
          margin-bottom: 1.5rem;
        }
        .ins-agent-row {
          display: flex;
          align-items: center;
          gap: 0.7rem;
          padding: 0.6rem 0.9rem;
          border-radius: 10px;
          border: 1px solid var(--border);
          transition: all 0.25s;
        }
        .ins-agent-row.active-agent {
          border-color: rgba(var(--page-glow-rgb), 0.5);
          background: rgba(var(--page-glow-rgb), 0.06);
        }
        .ins-agent-row.done-agent {
          border-color: rgba(var(--page-glow-rgb), 0.2);
          background: rgba(var(--page-glow-rgb), 0.03);
        }
        .ins-agent-dot {
          width: 7px; height: 7px;
          border-radius: 50%;
          flex-shrink: 0;
        }
        .ins-agent-name {
          flex: 1;
          font-size: 0.78rem;
          color: var(--text-secondary);
        }
        .ins-agent-check {
          font-size: 0.72rem;
          color: var(--page-accent);
          font-family: 'JetBrains Mono', monospace;
        }

        .ins-run-btn {
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
        .ins-run-btn:hover { transform: translateY(-2px); box-shadow: 0 0 48px rgba(var(--page-glow-rgb), 0.65); }
        .ins-run-btn:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }

        /* ── Right: insight cards ── */
        .ins-results { display: flex; flex-direction: column; gap: 1rem; }
        .ins-results-header {
          opacity: 0;
          animation: fadeSlideUp 0.45s ease 0.45s forwards;
        }

        .ins-divider {
          display: flex; align-items: center; gap: 1rem; margin-bottom: 1.2rem;
        }
        .ins-divider-label {
          font-size: 0.68rem;
          font-family: 'JetBrains Mono', monospace;
          color: var(--text-muted);
          text-transform: uppercase;
          letter-spacing: 0.14em;
          white-space: nowrap;
        }
        .ins-divider-line { flex: 1; height: 1px; background: var(--border); }

        /* Agent card */
        .ins-agent-card {
          background: var(--card);
          border: 1px solid var(--border);
          border-radius: 16px;
          overflow: hidden;
          transition: border-color 0.3s, box-shadow 0.3s;
          opacity: 0;
          transform: translateY(12px);
          animation: fadeSlideUp 0.4s ease forwards;
        }
        .ins-agent-card:hover {
          box-shadow: 0 0 32px rgba(var(--page-glow-rgb), 0.1);
        }
        .ins-card-header {
          padding: 1rem 1.25rem;
          border-bottom: 1px solid var(--border);
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }
        .ins-card-icon {
          width: 32px; height: 32px;
          border-radius: 9px;
          display: flex; align-items: center; justify-content: center;
          flex-shrink: 0;
        }
        .ins-card-num {
          font-family: 'JetBrains Mono', monospace;
          font-size: 0.65rem;
          color: var(--text-muted);
          letter-spacing: 0.1em;
        }
        .ins-card-name {
          font-family: 'Syne', sans-serif;
          font-size: 0.9rem;
          font-weight: 700;
          flex: 1;
        }
        .ins-card-tag {
          font-size: 0.62rem;
          padding: 2px 7px;
          border-radius: 5px;
          font-family: 'JetBrains Mono', monospace;
          text-transform: uppercase;
          letter-spacing: 0.08em;
        }
        .ins-card-body {
          padding: 1.1rem 1.25rem;
          display: flex;
          gap: 1.25rem;
          align-items: flex-start;
        }
        .ins-card-text {
          flex: 1;
          font-size: 0.85rem;
          color: var(--text-secondary);
          line-height: 1.7;
        }
        .ins-card-metric {
          text-align: center;
          padding: 0.7rem 1rem;
          border-radius: 10px;
          background: rgba(var(--page-glow-rgb), 0.06);
          border: 1px solid rgba(var(--page-glow-rgb), 0.15);
          flex-shrink: 0;
          min-width: 64px;
        }
        .ins-card-metric-val {
          font-family: 'Syne', sans-serif;
          font-size: 1.25rem;
          font-weight: 800;
          line-height: 1;
        }
        .ins-card-metric-lbl {
          font-size: 0.6rem;
          font-family: 'JetBrains Mono', monospace;
          text-transform: uppercase;
          letter-spacing: 0.08em;
          margin-top: 3px;
          color: var(--text-muted);
        }

        /* Empty state */
        .ins-empty {
          background: var(--card);
          border: 1px solid var(--border);
          border-radius: 16px;
          padding: 4rem 2rem;
          text-align: center;
          min-height: 300px;
          display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 0.75rem;
        }
        .ins-empty-title {
          font-family: 'Syne', sans-serif;
          font-size: 1rem; font-weight: 700;
          color: var(--text-secondary);
        }
        .ins-empty-sub {
          font-size: 0.78rem; color: var(--text-muted);
          font-family: 'JetBrains Mono', monospace;
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
          0%   { opacity:0;   filter:blur(16px); transform:translateX(-14px); }
          55%  { opacity:0.9; filter:blur(2px);  transform:translateX(2px); }
          100% { opacity:1;   filter:blur(0);    transform:translateX(0); }
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

      <div className="ins-inner">

        {/* ════ HERO ════ */}
        <div className="ins-hero">
          <div>
            <div className="ins-hero-tag">
              <svg viewBox="0 0 24 24" width="10" height="10" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="8" r="5"/><path d="M9 13v2a3 3 0 0 0 6 0v-2"/></svg>
              LangChain · 4-Agent Pipeline
            </div>
            <h1>
              <div className="blur-line">
                {['AI-Powered'].map((w, i) => (
                  <span key={w} className="blur-word" style={{ animationDelay: `${0.1 + i * 0.1}s` }}>{w}</span>
                ))}
              </div>
              <div className="blur-line" style={{ color: 'var(--page-accent)' }}>
                {['Insights.'].map((w, i) => (
                  <span key={w} className="blur-word" style={{ animationDelay: `${0.22 + i * 0.12}s` }}>{w}</span>
                ))}
              </div>
            </h1>
            <p className="ins-hero-sub">
              A sequential LangChain pipeline validates your batch, explains the solver's output, suggests constraint relaxations, and recommends the best scenario — all in plain language.
            </p>
            <div className="ins-pipeline-badge">
              {['Validator', 'Insight', 'Relaxation', 'Recommender'].map((step, i, arr) => (
                <>
                  <span key={step} className="ins-pipeline-step">{step}</span>
                  {i < arr.length - 1 && <div key={`arrow-${i}`} className="ins-pipeline-arrow" />}
                </>
              ))}
            </div>
          </div>
          <div className="ins-hero-agent-count">
            <div className="ins-hero-num">4</div>
            <div className="ins-hero-lbl">AI Agents</div>
          </div>
        </div>

        {/* ════ MAIN GRID ════ */}
        <div className="ins-grid">

          {/* ── LEFT: Control ── */}
          <div className="ins-control-card">
            <div className="ins-ctrl-header">
              <span className="ins-ctrl-header-label">/ pipeline · langchain</span>
              <div className="ins-status-dot" />
            </div>
            <div className="ins-ctrl-body">
              <FoxMascot
                size="md"
                variant={status === 'idle' ? 'idle' : status === 'running' ? 'thinking' : 'happy'}
                style={{ margin: '0 auto 1.5rem' }}
              />

              <p style={{ fontSize: '0.68rem', fontFamily: 'JetBrains Mono, monospace', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: '0.75rem' }}>
                Agent Pipeline
              </p>
              <div className="ins-agent-list">
                {AGENTS.map(agent => {
                  const isDone = revealed.includes(agent.id)
                  const isActive = activeAgent === agent.id
                  return (
                    <div key={agent.id} className={`ins-agent-row ${isActive ? 'active-agent' : isDone ? 'done-agent' : ''}`}>
                      <div className="ins-agent-dot" style={{ background: agent.color, boxShadow: isDone ? `0 0 6px ${agent.color}` : 'none' }} />
                      <span className="ins-agent-name" style={{ color: isActive || isDone ? 'var(--text-primary)' : undefined }}>
                        {agent.label}
                      </span>
                      {isDone && <span className="ins-agent-check">✓</span>}
                      {isActive && <Loader2 size={12} style={{ color: 'var(--page-accent)', animation: 'spinIcon 1s linear infinite' }} />}
                    </div>
                  )
                })}
              </div>

              <button
                className="ins-run-btn"
                onClick={runPipeline}
                disabled={status === 'running'}
              >
                {status === 'running'
                  ? <><Loader2 size={15} style={{ animation: 'spinIcon 1s linear infinite' }} /> Running Pipeline…</>
                  : <>
                      <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="8" r="5"/><path d="M9 13v2a3 3 0 0 0 6 0v-2"/></svg>
                      {status === 'done' ? 'Re-run Pipeline' : 'Run AI Pipeline'}
                    </>
                }
              </button>
            </div>
          </div>

          {/* ── RIGHT: Agent cards ── */}
          <div className="ins-results">
            <div className="ins-results-header">
              <div className="ins-divider">
                <span className="ins-divider-label">— Agent Outputs</span>
                <div className="ins-divider-line" />
              </div>
            </div>

            {revealed.length > 0 ? (
              revealed.map((id, idx) => {
                const agent = AGENTS.find(a => a.id === id)
                return (
                  <div
                    key={id}
                    className="ins-agent-card"
                    style={{ animationDelay: `${idx * 0.07}s`, borderColor: `${agent.color}28` }}
                  >
                    <div className="ins-card-header">
                      <div className="ins-card-icon" style={{ background: `${agent.color}18`, border: `1px solid ${agent.color}30`, color: agent.color }}>
                        {agent.icon}
                      </div>
                      <div style={{ flex: 1 }}>
                        <div className="ins-card-num">No. {agent.num}</div>
                        <div className="ins-card-name">{agent.label}</div>
                      </div>
                      <span className="ins-card-tag" style={{ background: `${agent.color}18`, border: `1px solid ${agent.color}30`, color: agent.color }}>
                        {agent.tag}
                      </span>
                    </div>
                    <div className="ins-card-body">
                      <p className="ins-card-text">{agent.insight}</p>
                      <div className="ins-card-metric">
                        <div className="ins-card-metric-val" style={{ color: agent.color }}>{agent.metric.val}</div>
                        <div className="ins-card-metric-lbl">{agent.metric.lbl}</div>
                      </div>
                    </div>
                  </div>
                )
              })
            ) : (
              <div className="ins-empty">
                <div style={{ width:48, height:48, borderRadius:14, border:'1px solid rgba(var(--page-glow-rgb),0.3)', background:'rgba(var(--page-glow-rgb),0.06)', display:'flex', alignItems:'center', justifyContent:'center', marginBottom:'0.5rem', color:'var(--page-accent)' }}>
                  <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="8" r="5"/><path d="M9 13v2a3 3 0 0 0 6 0v-2"/></svg>
                </div>
                <div className="ins-empty-title">
                  {status === 'running' ? `Running ${AGENTS.find(a => a.id === activeAgent)?.label ?? 'pipeline'}…` : 'Agent insights appear here'}
                </div>
                <div className="ins-empty-sub">
                  {status === 'running' ? 'LangChain agents processing batch' : 'Run the pipeline to generate AI insights'}
                </div>
              </div>
            )}
          </div>
        </div>
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