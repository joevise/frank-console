import { useState } from 'react'

const SIGNAL_TABS = [
  { key: 'buy', label: '买入', dot: '🔴', color: '#ff3860' },
  { key: 'sell', label: '卖出', dot: '🟢', color: '#00d1b2' },
  { key: 'watch', label: '观察', dot: '🟡', color: '#ffdd57' },
]

function SignalDetail({ detail }) {
  if (!detail) return null

  const rows = []
  if (detail.trend_days) rows.push(['持续天数', `${detail.trend_days}天`])
  if (detail.start_date) rows.push(['开始日期', detail.start_date])
  if (detail.end_date) rows.push(['结束日期', detail.end_date])
  if (detail.signal) rows.push(['当前信号', detail.signal])
  if (detail.prev_signal) rows.push(['前一日', detail.prev_signal])
  if (detail.ratio) rows.push(['转强比例', detail.ratio])
  if (detail.strong_count != null && detail.total_count != null) {
    rows.push(['转强/总数', `${detail.strong_count}/${detail.total_count}`])
  }

  return (
    <div className="mt-1.5 pt-1.5 border-t border-border/50 space-y-1">
      {rows.map(([label, value], idx) => (
        <div key={idx} className="flex items-center justify-between">
          <span className="text-[10px] text-ink-dim">{label}</span>
          <span className="font-mono text-[10px] text-ink">{value}</span>
        </div>
      ))}

      {Array.isArray(detail.industries) && detail.industries.length > 0 && (
        <div className="flex flex-wrap gap-1 pt-1">
          {detail.industries.map((industry, idx) => (
            <span
              key={idx}
              className="font-mono text-[9px] text-gold px-1 rounded"
              style={{ backgroundColor: 'rgba(255,215,0,0.1)' }}
            >
              {industry}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

function SignalItem({ signal, expanded, onClick, onAction }) {
  return (
    <div
      onClick={onClick}
      className={`px-2 py-1.5 rounded cursor-pointer transition ${
        expanded ? 'bg-[#1c1c1c]' : 'hover:bg-[#1c1c1c]/50'
      }`}
    >
      <div className="flex items-center gap-1.5">
        <span className="text-[12px] font-medium text-ink truncate flex-1">
          {signal.stock || signal.stock_name || signal.name}
        </span>
      </div>

      <div className="text-[11px] text-ink-soft mt-0.5 leading-snug">
        {signal.reason || signal.summary}
      </div>

      {expanded && <SignalDetail detail={signal.detail} />}

      {expanded && (
        <div className="flex gap-1 mt-2" onClick={(e) => e.stopPropagation()}>
          {onAction && (
            <>
              <button
                onClick={() => onAction('ask_frank', signal)}
                className="font-mono text-[9px] text-gold bg-gold/10 border border-gold/20 rounded px-1.5 py-0.5 hover:bg-gold/20 transition"
              >
                问Frank
              </button>
              <button
                onClick={() => onAction('ask_dsa', signal)}
                className="font-mono text-[9px] text-ink-soft bg-[#1c1c1c] border border-border rounded px-1.5 py-0.5 hover:text-gold hover:border-gold/30 transition"
              >
                @DSA
              </button>
              <button
                onClick={() => onAction('add_watch', signal)}
                className="font-mono text-[9px] text-ink-soft bg-[#1c1c1c] border border-border rounded px-1.5 py-0.5 hover:text-gold hover:border-gold/30 transition"
              >
                +自选
              </button>
            </>
          )}
        </div>
      )}
    </div>
  )
}

export default function SignalPanel({ signals = { buy: [], sell: [], watch: [] }, onSelectStock, onAction }) {
  const [expandedKey, setExpandedKey] = useState(null)

  return (
    <div className="bg-panel border border-border rounded-xl p-4 h-full flex flex-col">
      <div className="flex items-center gap-2 mb-2">
        <span className="font-mono text-[10px] text-gold uppercase tracking-widest">
          买卖信号
        </span>
        <div className="flex-1 h-px bg-border" />
      </div>

      <div className="flex-1 overflow-y-auto space-y-3">
        {SIGNAL_TABS.map((tab) => {
          const items = signals[tab.key] || []
          return (
            <div key={tab.key}>
              <div className="flex items-center gap-1.5 mb-1">
                <span className="text-[11px]">{tab.dot}</span>
                <span
                  className="font-mono text-[10px] uppercase tracking-wider"
                  style={{ color: tab.color }}
                >
                  {tab.label}
                </span>
                <span className="font-mono text-[10px] text-ink-dim">
                  {items.length}
                </span>
              </div>

              <div className="space-y-0.5">
                {items.length === 0 ? (
                  <div className="text-[11px] text-ink-dim px-2 py-1 italic">
                    暂无
                  </div>
                ) : (
                  items
                    .slice(0, 8)
                    .map((signal, idx) => (
                      <SignalItem
                        key={idx}
                        signal={signal}
                        expanded={expandedKey === `${tab.key}-${idx}`}
                        onClick={() =>
                          setExpandedKey(
                            expandedKey === `${tab.key}-${idx}`
                              ? null
                              : `${tab.key}-${idx}`
                          )
                        }
                        onAction={onAction}
                      />
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
