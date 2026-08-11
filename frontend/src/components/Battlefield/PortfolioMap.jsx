import { useState } from 'react'

const ACTION_CONFIG = {
  hold: { text: '持有', color: '#888' },
  add: { text: '加仓', color: '#ff3860' },
  reduce: { text: '减仓', color: '#ffdd57' },
  cut: { text: '止损', color: '#00d1b2' },
  watch: { text: '观察', color: '#888' },
}

function getHealthColor(score) {
  if (score == null) return 'gray'
  if (score >= 70) return 'green'
  if (score >= 45) return 'yellow'
  return 'red'
}

const HEALTH_DOT = {
  green: { color: '#ff3860', label: '●' },
  yellow: { color: '#ffdd57', label: '●' },
  red: { color: '#00d1b2', label: '●' },
  gray: { color: '#555', label: '○' },
}

function PortfolioItem({ item, onClick, onDragStart }) {
  const healthDot = HEALTH_DOT[getHealthColor(item.health_score)]
  const action = ACTION_CONFIG[item.action] || ACTION_CONFIG.hold
  const quote = item.quote
  const changePct = quote?.change_pct
  const changeColor = changePct > 0 ? '#ff3860' : changePct < 0 ? '#00d1b2' : '#888'

  return (
    <div
      onClick={() => onClick?.(item)}
      draggable
      onDragStart={(e) => onDragStart?.(e, item)}
      className="grid grid-cols-[1fr_auto_auto_auto] items-center gap-2 px-3 py-2 rounded-lg hover:bg-[#1c1c1c] cursor-pointer transition border-b border-border last:border-0"
    >
      <div className="min-w-0">
        <div className="text-[13px] font-medium text-ink truncate">
          {item.stock_name || item.stock_code}
        </div>
        <div className="flex items-center gap-1.5">
          <span className="font-mono text-[10px] text-ink-soft">
            {item.stock_code}
          </span>
          {quote && (
            <>
              <span className="font-mono text-[10px] text-ink">{quote.price}</span>
              <span className="font-mono text-[10px]" style={{ color: changeColor }}>
                {changePct > 0 ? '+' : ''}
                {changePct}%
              </span>
            </>
          )}
        </div>
      </div>

      <span className="font-mono text-[10px] text-ink-soft px-1.5 py-0.5 bg-[#1c1c1c] rounded truncate max-w-[70px]">
        {item.mainline || '主线外'}
      </span>

      <span
        className="flex items-center gap-1 font-mono text-[10px]"
        style={{ color: healthDot.color }}
      >
        {healthDot.label} {item.health_score ?? '-'}
      </span>

      <span
        className="font-mono text-[10px] font-semibold w-10 text-right"
        style={{ color: action.color }}
      >
        {action.text}
      </span>
    </div>
  )
}

export default function PortfolioMap({ items = [], onSelectStock, onMoveToWatch }) {
  const [filter, setFilter] = useState('all')

  const filtered = items.filter((item) => {
    if (filter === 'all') return true
    if (filter === 'mainline') return !!item.mainline
    if (filter === 'unhealthy')
      return getHealthColor(item.health_score) !== 'green' && item.health_score != null
    return true
  })

  const filterTabs = [
    { k: 'all', l: '全部' },
    { k: 'mainline', l: '主线' },
    { k: 'unhealthy', l: '异常' },
  ]

  return (
    <div className="bg-panel border border-border rounded-xl p-4 h-full flex flex-col">
      <div className="flex items-center gap-2 mb-2">
        <span className="font-mono text-[10px] text-gold uppercase tracking-widest">
          持仓映射
        </span>
        <span className="font-mono text-[10px] text-ink-soft">{filtered.length}</span>
        <div className="flex-1 h-px bg-border" />
        <div className="flex gap-1 font-mono text-[10px]">
          {filterTabs.map((tab) => (
            <button
              key={tab.k}
              onClick={() => setFilter(tab.k)}
              className={`px-2 py-0.5 rounded transition ${
                filter === tab.k
                  ? 'bg-gold/10 text-gold'
                  : 'text-ink-soft hover:text-ink'
              }`}
            >
              {tab.l}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {filtered.length === 0 ? (
          <div className="text-sm text-ink-dim py-8 text-center">
            {items.length === 0 ? '暂无持仓' : '当前筛选无结果'}
          </div>
        ) : (
          filtered.map((item) => (
            <PortfolioItem
              key={item.id || item.stock_code}
              item={item}
              onClick={onSelectStock}
              onDragStart={(e, itemData) => {
                e.dataTransfer.setData('application/json', JSON.stringify(itemData))
                e.dataTransfer.effectAllowed = 'move'
              }}
            />
          ))
        )}
      </div>
    </div>
  )
}
