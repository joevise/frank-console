import React from 'react'

// ============================================================
// MarketPulse - 市场脉搏（上证/深证/创业板 涨跌幅 + 红绿灯色块）
// ============================================================

function IndexCell({ label, value, change }) {
  const up = change >= 0
  const color = up ? 'text-up' : 'text-down'
  const bg = up ? 'bg-up' : 'bg-down'
  return (
    <div className="flex items-center gap-1.5">
      <span className="w-2 h-2 rounded-full" style={{ backgroundColor: up ? '#00d1b2' : '#ff3860', boxShadow: up ? '0 0 6px #00d1b2' : '0 0 6px #ff3860' }} />
      <span className="font-mono text-[10px] text-on-surface-soft uppercase tracking-wider">{label}</span>
      <span className={`font-mono text-sm font-semibold ${color}`}>
        {value != null ? value.toFixed(2) : '--'}
      </span>
      <span className={`font-mono text-[10px] ${color}`}>
        {change != null ? `${up ? '+' : ''}${change.toFixed(2)}%` : '--'}
      </span>
    </div>
  )
}

export default function MarketPulse({ data }) {
  const { indexes = {}, turnover, vix } = data || {}
  const { sh, sz, cyb } = indexes

  // 整体市场情绪：红绿比例
  const allUp = [sh, sz, cyb].every((x) => x?.change >= 0)
  const allDown = [sh, sz, cyb].every((x) => x?.change < 0)
  const mood = allUp ? 'risk-on' : allDown ? 'risk-off' : 'mixed'

  const moodLabel = {
    'risk-on': { text: 'Risk On', color: 'text-up', dot: 'bg-up' },
    'risk-off': { text: 'Risk Off', color: 'text-down', dot: 'bg-down' },
    mixed: { text: '震荡', color: 'text-warn', dot: 'bg-warn' },
  }[mood]

  return (
    <div className="bg-surface-2 border border-surface-border rounded-xl p-3 h-full flex flex-col">
      <div className="flex items-center justify-between mb-2">
        <span className="font-mono text-[10px] text-on-surface-soft uppercase tracking-widest">市场脉搏</span>
        <span className={`flex items-center gap-1 font-mono text-[10px] ${moodLabel.color}`}>
          <span className={`w-1.5 h-1.5 rounded-full ${moodLabel.dot} pulse-dot`} />
          {moodLabel.text}
        </span>
      </div>
      <div className="flex-1 flex flex-col justify-around gap-1">
        <IndexCell label="上证" value={sh?.value} change={sh?.change} />
        <IndexCell label="深证" value={sz?.value} change={sz?.change} />
        <IndexCell label="创业板" value={cyb?.value} change={cyb?.change} />
      </div>
      <div className="flex justify-between mt-2 pt-2 border-t border-surface-border font-mono text-[10px] text-on-surface-soft">
        <span>成交 {(turnover / 10000)?.toFixed(0) || '--'} 亿</span>
        <span>VIX {vix?.toFixed(1) || '--'}</span>
      </div>
    </div>
  )
}