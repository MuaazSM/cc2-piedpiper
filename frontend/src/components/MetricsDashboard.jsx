import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell
} from 'recharts'
import { DEMO_METRICS } from '@/data/demoData'

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

export default function MetricsDashboard({ metrics }) {
  const m = metrics || DEMO_METRICS
  const CHART_DATA = [
    { label: 'Trips',        before: m.before?.trips ?? 6,            after: m.after?.trips ?? 3 },
    { label: 'Utilization%', before: m.before?.avg_utilization ?? 62, after: m.after?.avg_utilization ?? 73 },
    { label: 'Cost (₹k)',    before: (m.before?.total_cost ?? 24000) / 1000, after: (m.after?.total_cost ?? 13500) / 1000 },
    { label: 'Carbon (kg)',  before: m.before?.carbon_kg ?? 1440,     after: m.after?.carbon_kg ?? 810 },
  ]
  const savings = m.savings || DEMO_METRICS.savings

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
          { label: 'Cost Saved',    value: `₹${((savings.cost_saved ?? 10500)/1000).toFixed(1)}k`, pct: `${savings.cost_saved_pct ?? 44}%` },
          { label: 'CO₂ Saved',     value: `${savings.carbon_saved_kg ?? 630}kg`,                  pct: `${savings.carbon_saved_pct ?? 44}%` },
          { label: 'Trips Saved',   value: `${savings.trips_reduced ?? 3}`,                        pct: `${Math.round(((savings.trips_reduced ?? 3) / (m.before?.trips ?? 6)) * 100)}% fewer` },
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