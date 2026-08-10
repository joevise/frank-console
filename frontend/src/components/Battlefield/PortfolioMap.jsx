import React, { useState } from 'react'

// ============================================================
// PortfolioMap - 中栏：持仓映射
// 表格：股票 | 主线 | 健康度 | 操作建议
// 点击股票 → 触发回调（弹抽屉）
// ============================================================

const HEALTH_DOT = {
  green: { color: '#00d1b2', label: '🟢' },
  yellow: { color: '#ffdd57', label: '🟡' },
  red: { color: '#ff3860', label: '🔴' },
}

function healthOf(score) {
  if (score >= 70) return 'green'
  if (score >= 40) return 'yellow'
  return 'red'
}

const ACTION_STYLE = {
  hold: { text: '持有', color: 'text-ink-soft' },
  add: { text: '加仓', color: 'text-up' },
  reduce: { text: '减仓', color: 'text-warn' },
  cut: { text: '止损', color: 'text-down' },
  watch: { text: '观察', color: 'text-ink-soft' },
}

function PortfolioRow({ item, onClick, onDragStart }) {
  const h = HEALTH_DOT[healthOf(item.health_score)]
  const a = ACTION_STYLE[item.action] || ACTION_STYLE.hold

  return (
    <div
      onClick={() => onClick?.(item)}
      draggable
      onDragStart={(e) => onDragStart?.(e, item)}
      className="grid grid-cols-[1fr_auto_auto_auto] items-center gap-2 px-3 py-2 rounded-lg hover:bg-code cursor-pointer transition border-b border-border last:border-0"
    >
      <div className="min-w-0">
        <div className="text-[13px] font-medium text-ink truncate">{item.stock_name || item.name}</div>
        <div className="font-mono text-[10px] text-ink-soft">{item.stock_code}</div>
      </div>
      <span className="font-mono text-[10px] text-ink-soft px-1.5 py-0.5 bg-code rounded truncate max-w-[80px]">
        {item.mainline || '主线外'}
      </span>
      <span
        className="flex items-center gap-1 font-mono text-[10px]"
        style={{ color: h.color }}
        title={`健康度 ${item.health_score}`}
      >
        {h.label} {item.health_score}
      </span>
      <span className={`font-mono text-[10px] font-semibold ${a.color} w-10 text-right`}>
        {a.text}
      </span>
    </div>
  )
}

export default function PortfolioMap({ items = [], onSelectStock, onMoveToWatch }) {
  const [filter, setFilter] = useState('all')

  const filtered = items.filter((it) => {
    if (filter === 'all') return true
    if (filter === 'mainline') return !!it.mainline
    if (filter === 'unhealthy') return healthOf(it.health_score) !== 'green'
    return true
  })

  return (
    <div className="bg-panel border border-border rounded-xl p-4 h-full flex flex-col">
      <div className="flex items-center gap-2 mb-2">
        <span className="font-mono text-[10px] text-ink-soft uppercase tracking-widest">持仓映射</span>
        <span className="font-mono text-[10px] bg-code text-ink-soft px-1.5 rounded">{filtered.length}</span>
        <div className="flex-1 h-px bg-border" />
        <div className="flex gap-1 font-mono text-[10px]">
          {[
            { k: 'all', l: '全部' },
            { k: 'mainline', l: '主线' },
            { k: 'unhealthy', l: '异常' },
          ].map((t) => (
            <button
              key={t.k}
              onClick={() => setFilter(t.k)}
              className={`px-2 py-0.5 rounded ${
                filter === t.k ? 'bg-ink text-white' : 'text-ink-soft hover:bg-code'
              }`}
            >
              {t.l}
            </button>
          ))}
        </div>
      </div>
      <div
        className="flex-1 overflow-y-auto"
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault()
          const data = e.dataTransfer.getData('application/json')
          if (data) {
            try { onMoveToWatch?.(JSON.parse(data)) } catch {}
          }
        }}
      >
        {filtered.length === 0 ? (
          <div className="text-sm text-ink-soft py-8 text-center">
            {items.length === 0 ? '暂无持仓，点击右上角添加' : '当前筛选下无持仓'}
          </div>
        ) : (
          filtered.map((it) => (
            <PortfolioRow
              key={it.id || it.stock_code}
              item={it}
              onClick={onSelectStock}
              onDragStart={(e, item) => {
                e.dataTransfer.setData('application/json', JSON.stringify(item))
                e.dataTransfer.effectAllowed = 'move'
              }}
            />
          ))
        )}
      </div>
    </div>
  )
}