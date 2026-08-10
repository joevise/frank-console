import React, { useState } from 'react'

// ============================================================
// MainlineMap - 左栏：主线地图
// 显示：主线 + 进度条 + 状态；展开子行业
// ============================================================

const STATUS_STYLE = {
  strong: { color: '#00d1b2', label: '强' },
  normal: { color: '#ffdd57', label: '中' },
  weak: { color: '#ff3860', label: '弱' },
  forming: { color: '#8a8a8a', label: '新' },
}

function MainlineRow({ mainline, expanded, onToggle, onSelectSub }) {
  const s = STATUS_STYLE[mainline.status] || STATUS_STYLE.normal
  const pct = Math.min(100, ((mainline.days || 0) / 30) * 100)
  return (
    <>
      <div
        onClick={onToggle}
        className={`flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition ${
          expanded ? 'bg-accent-soft' : 'hover:bg-code'
        }`}
      >
        <span
          className="w-2 h-2 rounded-full shrink-0"
          style={{ backgroundColor: s.color, boxShadow: expanded ? `0 0 6px ${s.color}` : 'none' }}
        />
        <span className="text-[13px] font-medium text-ink flex-1 truncate">{mainline.name}</span>
        <span
          className="font-mono text-[10px] px-1.5 py-0.5 rounded"
          style={{ backgroundColor: `${s.color}22`, color: s.color }}
        >
          {s.label}
        </span>
        <div className="w-12 h-1.5 bg-border rounded-full overflow-hidden">
          <div className="h-full rounded-full" style={{ width: `${pct}%`, backgroundColor: s.color }} />
        </div>
        <span className="font-mono text-[10px] text-ink-soft w-8 text-right">
          {mainline.days}d
        </span>
        <span className="text-ink-soft text-xs w-3 text-right">
          {expanded ? '▾' : '▸'}
        </span>
      </div>
      {expanded && mainline.sub_industries && mainline.sub_industries.length > 0 && (
        <div className="ml-5 mt-1 mb-2 space-y-0.5">
          {mainline.sub_industries.map((sub, i) => {
            const dev = sub.deviation || 0
            const isNew = sub.is_new
            const isHot = sub.is_overheated
            const devColor = dev > 0 ? 'text-up' : dev < 0 ? 'text-down' : 'text-ink-soft'
            return (
              <div
                key={i}
                onClick={() => onSelectSub?.(sub)}
                className="flex items-center gap-2 px-2 py-1 rounded text-[12px] hover:bg-code cursor-pointer"
              >
                <span className="text-ink-soft">·</span>
                <span className="text-ink-soft flex-1 truncate">{sub.name}</span>
                {isNew && <span className="text-[10px]">🆕</span>}
                {isHot && <span className="text-[10px]">⚠️</span>}
                <span className={`font-mono text-[10px] ${devColor}`}>
                  {dev > 0 ? '+' : ''}{dev.toFixed(1)}σ
                </span>
              </div>
            )
          })}
        </div>
      )}
    </>
  )
}

export default function MainlineMap({ mainlines = [], onSelectStock }) {
  const [expanded, setExpanded] = useState(() => new Set(mainlines.length > 0 ? [mainlines[0].name] : []))

  const toggle = (name) => {
    setExpanded((prev) => {
      const next = new Set(prev)
      if (next.has(name)) next.delete(name)
      else next.add(name)
      return next
    })
  }

  if (mainlines.length === 0) {
    return (
      <div className="bg-panel border border-border rounded-xl p-5 h-full flex flex-col">
        <SectionHeader title="主线地图" badge="0" />
        <div className="flex-1 flex items-center justify-center text-ink-soft text-sm">
          暂无活跃主线
        </div>
      </div>
    )
  }

  return (
    <div className="bg-panel border border-border rounded-xl p-4 h-full flex flex-col">
      <SectionHeader title="主线地图" badge={mainlines.length} />
      <div className="flex-1 overflow-y-auto mt-2 space-y-0.5">
        {mainlines.map((m) => (
          <MainlineRow
            key={m.name}
            mainline={m}
            expanded={expanded.has(m.name)}
            onToggle={() => toggle(m.name)}
          />
        ))}
      </div>
    </div>
  )
}

function SectionHeader({ title, badge }) {
  return (
    <div className="flex items-center gap-2 mb-1">
      <span className="font-mono text-[10px] text-ink-soft uppercase tracking-widest">{title}</span>
      <span className="font-mono text-[10px] bg-code text-ink-soft px-1.5 rounded">{badge}</span>
      <div className="flex-1 h-px bg-border" />
    </div>
  )
}