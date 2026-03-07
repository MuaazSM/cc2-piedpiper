import { X, Package, Clock, Scale, Boxes } from 'lucide-react'

export default function ShipmentDrawer({ shipment: s, onClose }) {
  if (!s) return null
  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/50 z-40 backdrop-blur-sm"
        onClick={onClose} />

      {/* Drawer */}
      <div className="fixed top-0 right-0 h-full w-80 z-50
                      bg-[#111] border-l border-[var(--border)]
                      flex flex-col"
        style={{ animation: 'slideIn 0.25s ease forwards' }}>
        <style>{`
          @keyframes slideIn {
            from { transform: translateX(100%); }
            to   { transform: translateX(0); }
          }
        `}</style>

        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4
                        border-b border-[var(--border)]">
          <div className="flex items-center gap-2">
            <Package size={14} style={{ color: 'var(--page-accent)' }} />
            <span className="font-mono text-sm" style={{ color: 'var(--page-accent)' }}>
              {s.id}
            </span>
          </div>
          <button onClick={onClose} className="p-1 rounded-lg hover:bg-white/5 transition-colors">
            <X size={16} style={{ color: 'var(--text-muted)' }} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-5">

          {/* Route */}
          <div>
            <p className="text-xs mb-2 uppercase tracking-wide" style={{ color: 'var(--text-muted)' }}>Route</p>
            <div className="lorri-card p-4 flex items-center gap-3 text-sm font-medium">
              <span>{s.origin}</span>
              <span style={{ color: 'var(--page-accent)' }}>→</span>
              <span>{s.destination}</span>
            </div>
          </div>

          {/* Time windows */}
          <div>
            <p className="text-xs mb-2 uppercase tracking-wide" style={{ color: 'var(--text-muted)' }}>
              <Clock size={10} className="inline mr-1" />Time Window
            </p>
            <div className="lorri-card p-4 space-y-2 text-sm">
              <div className="flex justify-between">
                <span style={{ color: 'var(--text-muted)' }}>Pickup</span>
                <span className="font-mono text-xs">
                  {new Date(s.pickup_time).toLocaleString()}
                </span>
              </div>
              <div className="flex justify-between">
                <span style={{ color: 'var(--text-muted)' }}>Delivery</span>
                <span className="font-mono text-xs">
                  {new Date(s.delivery_time).toLocaleString()}
                </span>
              </div>
            </div>
          </div>

          {/* Cargo */}
          <div>
            <p className="text-xs mb-2 uppercase tracking-wide" style={{ color: 'var(--text-muted)' }}>Cargo</p>
            <div className="lorri-card p-4 grid grid-cols-2 gap-3 text-sm">
              <div>
                <p className="text-xs mb-1 flex items-center gap-1" style={{ color: 'var(--text-muted)' }}>
                  <Scale size={10} /> Weight
                </p>
                <p className="font-mono">{s.weight.toLocaleString()} kg</p>
              </div>
              <div>
                <p className="text-xs mb-1 flex items-center gap-1" style={{ color: 'var(--text-muted)' }}>
                  <Boxes size={10} /> Volume
                </p>
                <p className="font-mono">{s.volume} m³</p>
              </div>
            </div>
          </div>

          {/* Priority */}
          <div>
            <p className="text-xs mb-2 uppercase tracking-wide" style={{ color: 'var(--text-muted)' }}>Priority</p>
            <span className={`px-3 py-1 rounded-lg text-xs border font-medium
                              ${s.priority === 'high'   ? 'text-red-400 border-red-400/30 bg-red-400/10'   : ''}
                              ${s.priority === 'medium' ? 'text-amber-400 border-amber-400/30 bg-amber-400/10' : ''}
                              ${s.priority === 'low'    ? 'text-slate-400 border-slate-400/30 bg-slate-400/10' : ''}`}>
              {s.priority}
            </span>
          </div>
        </div>
      </div>
    </>
  )
}