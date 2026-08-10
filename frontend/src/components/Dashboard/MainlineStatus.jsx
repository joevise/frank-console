import React from 'react'

// ============================================================
// MainlineStatus - 主线状态（当前主线 + 持续天数 + 进度条）
// ============================================================

const STATUS_STYLE = {
  strong: { color: '#00d1b2', label: '强' },
  normal: { color: '#ffdd57', label: '中' },
  weak: { color: '#ff3860', label: '弱' },
  forming: { color: '#8a8a8a', label: '新' },
}

export default function MainlineStatus({ mainlines = [] }) {
  const top = mainlines.slice(0, 3)
  const max = Math.max(30, ...mainlines.map((m) => m.days || 0))

  if (top.length === 0) {
    return (
      <div className="bg-surface-2 border border-surface-border rounded-xl p-3 h-full flex flex-col">
        <span className="font-mono text-[10px] text-on-surface-soft uppercase tracking-widest">主线状态</span>
        <div className="flex-1 flex items-center justify-center font-mono text-[11px] text-on-surface-soft">
          暂无主线
        </div>
      </div>
    )
  }

  return (
    <div className="bg-surface-2 border border-surface-border rounded-xl p-3 h-full flex flex-col">
      <div className="flex items-center justify-between mb-2">
        <span className="font-mono text-[10px] text-on-surface-soft uppercase tracking-widest">主线状态</span>
        <span className="font-mono text-[10px] text-on-surface-soft">活跃 {mainlines.length}</span>
      </div>
      <div className="flex-1 flex flex-col gap-1.5 justify-center">
        {top.map((m, i) => {
          const s = STATUS_STYLE[m.status] || STATUS_STYLE.normal
          const pct = Math.min(100, ((m.days || 0) / max) * 100)
          return (
            <div key={i} className="flex items-center gap-2">
              <span className="font-mono text-[10px] text-on-surface-soft w-3">{i + 1}</span>
              <span className="text-xs text-on-surface flex-1 truncate">{m.name}</span>
              <span className="font-mono text-[10px]" style={{ color: s.color }}>
                {s.label}
              </span>
              <div className="w-16 h-1.5 bg-surface-3 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all"
                  style={{ width: `${pct}%`, backgroundColor: s.color }}
                />
              </div>
              <span className="font-mono text-[10px] text-on-surface-soft w-8 text-right">
                {m.days}d
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}