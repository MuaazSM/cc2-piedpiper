import { useNavigate, useLocation } from 'react-router-dom'
import FoxMascot from '@/components/FoxMascot'

const LINKS = [
  { to: '/',          label: 'Home'      },
  { to: '/shipments', label: 'Shipments' },
  { to: '/optimize',  label: 'Optimize'  },
  { to: '/scenarios', label: 'Scenarios' },
  { to: '/insights',  label: 'Insights'  },
]

export default function Navbar() {
  const nav = useNavigate()
  const { pathname } = useLocation()

  return (
    <>
      <style>{`
        .lorri-nav {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 1.2rem 2.5rem;
          border-bottom: 1px solid var(--border);
          position: sticky;
          top: 0;
          z-index: 50;
          background: rgba(10,10,10,0.72);
          backdrop-filter: blur(20px);
          -webkit-backdrop-filter: blur(20px);
        }
        .lorri-nav-logo {
          display: flex;
          align-items: center;
          gap: 10px;
          font-family: 'Syne', sans-serif;
          font-weight: 700;
          font-size: 1.9rem;
          color: var(--page-accent);
          cursor: pointer;
          transition: all 0.25s ease;
          text-shadow: 0 0 0px rgba(var(--page-glow-rgb), 0);
        }
        .lorri-nav-logo:hover {
          opacity: 0.85;
          text-shadow: 0 0 16px rgba(var(--page-glow-rgb), 0.7);
        }

        /* ── Nav pill container ── */
        .lorri-nav-links {
          display: flex;
          gap: 0.15rem;
          background: rgba(255,255,255,0.03);
          border: 1px solid var(--border);
          border-radius: 12px;
          padding: 5px;
        }

        /* ── Each nav button ── */
        .lorri-nav-link {
          position: relative;
          padding: 0.8rem 1.5rem;
          border-radius: 12px;
          font-size: 1rem;
          cursor: pointer;
          border: none;
          background: transparent;
          font-family: 'DM Sans', sans-serif;
          font-weight: 500;
          letter-spacing: 0.01em;
          transition: all 0.22s cubic-bezier(0.4, 0, 0.2, 1);
          outline: none;
        }

        /* Active state */
        .lorri-nav-link.active {
          background: rgba(var(--page-glow-rgb), 0.22);
          color: var(--page-accent);
          box-shadow: 0 0 12px rgba(var(--page-glow-rgb), 0.25),
                      inset 0 1px 0 rgba(255,255,255,0.06);
        }

        /* Idle state */
        .lorri-nav-link:not(.active) {
          color: var(--text-muted);
        }

        /* Hover on non-active */
        .lorri-nav-link:not(.active):hover {
          background: rgba(255,255,255,0.06);
          color: var(--text-primary);
          transform: translateY(-1px);
        }

        /* Active dot */
        .nav-dot {
          display: inline-block;
          width: 5px;
          height: 5px;
          border-radius: 50%;
          background: var(--page-accent);
          margin-right: 5px;
          vertical-align: middle;
          animation: navpulse 2s ease-in-out infinite;
          box-shadow: 0 0 6px var(--page-accent);
        }
        @keyframes navpulse {
          0%,100% { opacity: 1;  transform: scale(1);    }
          50%      { opacity: 0.4; transform: scale(0.8); }
        }

        /* Right spacer */
        .lorri-nav-right {
          width: 120px;
          display: flex;
          justify-content: flex-end;
        }
      `}</style>

      <nav className="lorri-nav">
        {/* Logo */}
        <div className="lorri-nav-logo" onClick={() => nav('/')}>
          <FoxMascot size="lg" variant="idle" />
          Lorri
        </div>

        {/* Pill nav */}
        <div className="lorri-nav-links">
          {LINKS.map(({ to, label }) => {
            const isActive = pathname === to
            return (
              <button
                key={to}
                className={`lorri-nav-link ${isActive ? 'active' : ''}`}
                onClick={() => nav(to)}
              >
                {isActive && <span className="nav-dot" />}
                {label}
              </button>
            )
          })}
        </div>

        <div className="lorri-nav-right" />
      </nav>
    </>
  )
}