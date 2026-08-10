import React from 'react'
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts'

// ============================================================
// PortfolioHealth - 持仓健康度（饼图：主线内/主线外/观察池）
// ============================================================

const SEGMENT = [
  { key: 'in_mainline', label: '主线内', color: '#00d1b2' },
  { key: 'out_mainline', label: '主线外', color: '#ffdd57' },
  { key: 'watch', label: '观察池', color: '#6b6b63' },
]

export default function PortfolioHealth({ data }) {
  const counts = data?.counts || { in_mainline: 0, out_mainline: 0, watch: 0 }
  const total = SEGMENT.reduce((sum, s) => sum + (counts[s.key] || 0), 0)

  const pieData = SEGMENT
    .map((s) => ({ name: s.label, value: counts[s.key] || 0, color: s.color }))
    .filter((d) => d.value > 0)

  const score = data?.score ?? (total > 0 ? Math.round((counts.in_mainline / total) * 100) : 0)

  return (
    <div className="bg-surface-2 border border-surface-border rounded-xl p-3 h-full flex flex-col">
      <div className="flex items-center justify-between mb-1">
        <span className="font-mono text-[10px] text-on-surface-soft uppercase tracking-widest">持仓健康度</span>
        <span
          className="font-mono text-[10px] font-semibold"
          style={{ color: score >= 70 ? '#00d1b2' : score >= 40 ? '#ffdd57' : '#ff3860' }}
        >
          {score}/100
        </span>
      </div>
      <div className="flex-1 flex items-center gap-2">
        <div className="w-20 h-20 relative">
          {total === 0 ? (
            <div className="w-full h-full rounded-full border-2 border-surface-border flex items-center justify-center">
              <span className="font-mono text-[10px] text-on-surface-soft">空仓</span>
            </div>
          ) : (
            <>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={20}
                    outerRadius={32}
                    paddingAngle={2}
                    dataKey="value"
                    stroke="none"
                  >
                    {pieData.map((entry, i) => (
                      <Cell key={i} fill={entry.color} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="font-mono text-xs font-semibold text-on-surface">{total}</span>
              </div>
            </>
          )}
        </div>
        <div className="flex-1 flex flex-col gap-1">
          {SEGMENT.map((s) => (
            <div key={s.key} className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-sm" style={{ backgroundColor: s.color }} />
              <span className="text-[10px] text-on-surface-soft flex-1">{s.label}</span>
              <span className="font-mono text-[11px] text-on-surface">{counts[s.key] || 0}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}