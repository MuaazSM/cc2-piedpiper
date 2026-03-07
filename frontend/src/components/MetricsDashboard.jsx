import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell
} from 'recharts'
import { DEMO_METRICS } from '@/data/demoData'

const CHART_DATA = [
  { label: 'Trips',        before: DEMO_METRICS.before.trips,            after: DEMO_METRICS.after.trips },
  { label: 'Utilization%', before: DEMO_METRICS.before.avg_utilization,   after: DEMO_METRICS.after.avg_utilization },
  { label: 'Cost (₹k)',    before: DEMO_METRICS.before.total_cost / 1000, after: DEMO_METRICS.after.total_cost / 1000 },
  { label: 'Carbon (kg)',  before: DEMO_METRICS.before.carbon_kg,          after: DEMO_METRICS.after.carbon_kg },
]

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: '#1a1a1a',
      border: '1px solid rgba(255,255,255,0.08)',
      borderRadius: 10,
      padding: '10px 14px',
      fontFamily: 'DM Sans',
      fontSize: 12,
    }}>
      <p style={{ color: '#a3a3a3', marginBottom: 6 }}>{label}</p>
      {payload.map(p => (
        <p key={p.name} style={{ color: p.color }}>
          {p.name}: <strong>{p.value}</strong>
        </p>
      ))}
    </div>
  )
}

export default function MetricsDashboard() {
  return (
    <div className="lorri-card p-6">
      <h4 className="font-display text-lg mb-6">Before vs After Optimization</h4>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={CHART_DATA} barGap={6} barCategoryGap="30%">
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
          <XAxis dataKey="label" tick={{ fill: '#6b6b6b', fontSize: 11 }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fill: '#6b6b6b', fontSize: 11 }} axisLine={false} tickLine={false} />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="before" name="Before" fill="#374151" radius={[6, 6, 0, 0]} />
          <Bar dataKey="after"  name="After"  fill="var(--page-accent)" radius={[6, 6, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>

      {/* Savings summary */}
      <div className="grid grid-cols-3 gap-4 mt-6 pt-5 border-t border-[var(--border)]">
        {[
          { label: 'Cost Saved',    value: `₹${(DEMO_METRICS.savings.cost_saved/1000).toFixed(1)}k`, pct: `${DEMO_METRICS.savings.cost_saved_pct}%` },
          { label: 'CO₂ Saved',     value: `${DEMO_METRICS.savings.carbon_saved_kg}kg`,              pct: `${DEMO_METRICS.savings.carbon_saved_pct}%` },
          { label: 'Trips Saved',   value: `${DEMO_METRICS.savings.trips_reduced}`,                  pct: '50% fewer' },
        ].map(item => (
          <div key={item.label} className="text-center">
            <p className="font-display text-2xl font-600" style={{ color: 'var(--page-accent)' }}>
              {item.value}
            </p>
            <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>{item.label}</p>
            <p className="text-xs font-mono mt-1 text-emerald-400">{item.pct}</p>
          </div>
        ))}
      </div>
    </div>
  )
}