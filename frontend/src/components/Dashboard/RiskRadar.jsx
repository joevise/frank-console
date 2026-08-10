import React from 'react'

// ============================================================
// RiskRadar - 风险雷达（转空行业 + 过热信号 + 红灯）
// ============================================================

export default function RiskRadar({ data }) {
  const { rotating_down = 0, overheated = 0, level = 'low' } = data || {}

  const levelStyle = {
    low: { bg: 'bg-up', text: 'Risk On', color: '#00d1b2' },
    mid: { bg: 'bg-warn', text: '留意', color: '#ffdd57' },
    high: { bg: 'bg-down', text: 'Risk Off', color: '#ff3860' },
  }[level]

  const total = rotating_down + overheated

  return (
    <div className="bg-surface-2 border border-surface-border rounded-xl p-3 h-full flex flex-col">
      <div className="flex items-center justify-between mb-2">
        <span className="font-mono text-[10px] text-on-surface-soft uppercase tracking-widest">风险雷达</span>
        <span
          className="font-mono text-[10px] px-1.5 py-0.5 rounded font-semibold"
          style={{ backgroundColor: `${levelStyle.color}22`, color: levelStyle.color }}
        >
          {levelStyle.text}
        </span>
      </div>
      <div className="flex-1 flex flex-col justify-center gap-1.5">
        <div className="flex items-center justify-between">
          <span className="text-xs text-on-surface-soft">转空行业</span>
          <div className="flex items-center gap-1.5">
            <span className="font-mono text-lg font-semibold text-down">{rotating_down}</span>
            <span className="font-mono text-[10px] text-on-surface-soft">个</span>
          </div>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-xs text-on-surface-soft">过热信号</span>
          <div className="flex items-center gap-1.5">
            <span className="font-mono text-lg font-semibold text-warn">{overheated}</span>
            <span className="font-mono text-[10px] text-on-surface-soft">个</span>
          </div>
        </div>
      </div>
      <div className="mt-2 pt-2 border-t border-surface-border flex items-center justify-between">
        <span className="font-mono text-[10px] text-on-surface-soft">合计告警</span>
        <span
          className="font-mono text-sm font-semibold"
          style={{ color: total > 5 ? '#ff3860' : total > 2 ? '#ffdd57' : '#00d1b2' }}
        >
          {total}
        </span>
      </div>
    </div>
  )
}