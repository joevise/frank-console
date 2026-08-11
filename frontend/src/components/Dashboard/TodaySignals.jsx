export default function TodaySignals({ data }) {
  const buy = data?.buy || []
  const sell = data?.sell || []
  const topBuy = buy.slice(0, 2)
  const topSell = sell.slice(0, 2)

  return (
    <div className="bg-panel border border-border rounded-xl p-3 h-full flex flex-col">
      <div className="flex items-center justify-between mb-2">
        <span className="font-mono text-[10px] text-gold uppercase tracking-widest">
          今日信号
        </span>
        <span className="font-mono text-[10px] text-ink-soft">🆕 实时</span>
      </div>

      <div className="flex-1 flex flex-col justify-center gap-1.5">
        {/* Buy signals */}
        <div className="flex items-baseline justify-between">
          <span className="text-xs" style={{ color: '#ff3860' }}>
            新转多
          </span>
          <span
            className="font-mono text-lg font-semibold"
            style={{ color: '#ff3860' }}
          >
            {buy.length}
          </span>
        </div>
        <div className="flex flex-wrap gap-1 min-h-[14px]">
          {topBuy.map((item, idx) => (
            <span
              key={idx}
              className="font-mono text-[10px] px-1 rounded truncate max-w-[60px]"
              style={{ color: '#ff3860', backgroundColor: 'rgba(255,56,96,0.1)' }}
            >
              {item.stock}
            </span>
          ))}
        </div>

        {/* Sell signals */}
        <div className="flex items-baseline justify-between mt-1">
          <span className="text-xs" style={{ color: '#00d1b2' }}>
            空头/转空
          </span>
          <span
            className="font-mono text-lg font-semibold"
            style={{ color: '#00d1b2' }}
          >
            {sell.length}
          </span>
        </div>
        <div className="flex flex-wrap gap-1 min-h-[14px]">
          {topSell.map((item, idx) => (
            <span
              key={idx}
              className="font-mono text-[10px] px-1 rounded truncate max-w-[60px]"
              style={{ color: '#00d1b2', backgroundColor: 'rgba(0,209,178,0.1)' }}
            >
              {item.stock}
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}
