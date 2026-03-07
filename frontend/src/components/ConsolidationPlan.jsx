import { Truck, Package } from 'lucide-react'

function UtilBar({ pct }) {
  const color = pct >= 85 ? '#10b981' : pct >= 60 ? '#f59e0b' : '#f43f5e'
  return (
    <div>
      <div className="flex justify-between text-xs mb-1.5" style={{ color: 'var(--text-muted)' }}>
        <span>Utilization</span>
        <span style={{ color }}>{pct}%</span>
      </div>
      <div className="util-bar-bg h-2">
        <div className="util-bar-fill h-full" style={{ width: `${pct}%`, background: `linear-gradient(90deg, ${color}88, ${color})` }} />
      </div>
    </div>
  )
}

export default function ConsolidationPlan({ plan }) {
  return (
    <div>
      <h3 className="font-display text-lg mb-4 flex items-center gap-2">
        <Truck size={16} style={{ color: 'var(--page-accent)' }} />
        Consolidation Plan
        <span className="text-sm font-normal font-mono ml-2" style={{ color: 'var(--text-muted)' }}>
          #{plan.id}
        </span>
      </h3>

      <div className="grid grid-cols-1 gap-4">
        {plan.trucks.map((truck, i) => (
          <div key={truck.vehicle_id} className="lorri-card p-5">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl flex items-center justify-center font-mono text-sm font-600"
                  style={{ background: 'rgba(var(--page-glow-rgb),0.2)', color: 'var(--page-accent)' }}>
                  {i + 1}
                </div>
                <div>
                  <p className="font-medium text-sm">{truck.vehicle_type}</p>
                  <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                    {truck.vehicle_id} · {truck.route}
                  </p>
                </div>
              </div>
              <p className="text-sm font-mono" style={{ color: 'var(--page-accent)' }}>
                ₹{truck.cost.toLocaleString()}
              </p>
            </div>

            {/* Shipments */}
            <div className="flex gap-2 mb-4 flex-wrap">
              {truck.shipments.map(sid => (
                <span key={sid}
                  className="px-2 py-0.5 rounded-md text-xs border font-mono"
                  style={{
                    color: 'var(--page-accent)',
                    borderColor: 'rgba(var(--page-glow-rgb),0.3)',
                    background: 'rgba(var(--page-glow-rgb),0.1)',
                  }}>
                  <Package size={10} className="inline mr-1" />{sid}
                </span>
              ))}
            </div>

            {/* Weight + Util */}
            <div className="flex items-center gap-4 text-xs mb-3" style={{ color: 'var(--text-muted)' }}>
              <span>{truck.total_weight.toLocaleString()} / {truck.capacity_weight.toLocaleString()} kg</span>
            </div>
            <UtilBar pct={truck.utilization} />
          </div>
        ))}
      </div>
    </div>
  )
}