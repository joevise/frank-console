import React, { useState } from 'react'

// ============================================================
// SignalPanel - 右栏：买卖信号
// 三个区块：🟢 买入 / 🔴 卖出 / 🟡 观察
// 每条信号：股票名 + 理由（一句话）+ 点击展开
// ============================================================

const SEGMENTS = [
  { key: 'buy', label: '买入', dot: '🟢', color: '#00d1b2' },
  { key: 'sell', label: '卖出', dot: '🔴', color: '#ff3860' },
  { key: 'watch', label: '观察', dot: '🟡', color: '#ffdd57' },
]

function SignalItem({ signal, expanded, onClick }) {
  return (
    <div
      onClick={onClick}
      className={`px-2 py-1.5 rounded cursor-pointer transition ${
        expanded ? 'bg-code' : 'hover:bg-code/50'
      }`}
    >
      <div className="flex items-center gap-1.5">
        <span className="text-[12px] font-medium text-ink truncate flex-1">
          {signal.stock_name || signal.name}
        </span>
        <span className="font-mono text-[10px] text-ink-soft">{signal.stock_code}</span>
      </div>
      <div className="text-[11px] text-ink-soft mt-0.5 leading-snug">
        {expanded && signal.detail ? signal.detail : signal.reason || signal.summary}
      </div>
    </div>
  )
}

export default function SignalPanel({ signals = { buy: [], sell: [], watch: [] }, onSelectStock }) {
  const [expanded, setExpanded] = useState(null)

  return (
    <div className="bg-panel border border-border rounded-xl p-4 h-full flex flex-col">
      <div className="flex items-center gap-2 mb-2">
        <span className="font-mono text-[10px] text-ink-soft uppercase tracking-widest">买卖信号</span>
        <div className="flex-1 h-px bg-border" />
      </div>
      <div className="flex-1 overflow-y-auto space-y-3">
        {SEGMENTS.map((seg) => {
          const list = signals[seg.key] || []
          return (
            <div key={seg.key}>
              <div className="flex items-center gap-1.5 mb-1">
                <span className="text-[11px]">{seg.dot}</span>
                <span className="font-mono text-[10px] text-ink-soft uppercase tracking-wider">
                  {seg.label}
                </span>
                <span className="font-mono text-[10px] text-ink-soft">{list.length}</span>
              </div>
              <div className="space-y-0.5">
                {list.length === 0 ? (
                  <div className="text-[11px] text-ink-soft/60 px-2 py-1 italic">暂无</div>
                ) : (
                  list.slice(0, 8).map((sig, i) => (
                    <div key={i} onClick={() => onSelectStock?.(sig)}>
                      <SignalItem
                        signal={sig}
                        expanded={expanded === `${seg.key}-${i}`}
                        onClick={() => setExpanded(expanded === `${seg.key}-${i}` ? null : `${seg.key}-${i}`)}
                      />
                    </div>
                  ))
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}