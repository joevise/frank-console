import IndexDisplay from './IndexDisplay'

export default function MarketPulse({ data }) {
  const indexes = data?.indexes || {}
  const sh = indexes.sh
  const sz = indexes.sz
  const cyb = indexes.cyb
  const turnoverYi = data?.turnover_yi
  const status = data?.status

  return (
    <div className="bg-panel border border-border rounded-xl p-3 h-full flex flex-col">
      <div className="flex items-center justify-between mb-2">
        <span className="font-mono text-[10px] text-gold uppercase tracking-widest">
          市场脉搏
        </span>
        {status && (
          <span className="flex items-center gap-1">
            <span
              className="w-1.5 h-1.5 rounded-full pulse-dot"
              style={{ backgroundColor: '#FFD700' }}
            />
            <span className="font-mono text-[9px] text-ink-soft">
              {status === 'trading' ? '盘中' : '休市'}
            </span>
          </span>
        )}
      </div>

      <div className="flex-1 flex flex-col justify-center gap-1.5">
        <IndexDisplay idx={sh} label="上证" />
        <IndexDisplay idx={sz} label="深证" />
        <IndexDisplay idx={cyb} label="创业板" />
      </div>

      {turnoverYi != null && (
        <div className="mt-1.5 pt-1.5 border-t border-border flex items-center justify-between">
          <span className="font-mono text-[9px] text-ink-soft">成交额</span>
          <span className="font-mono text-[11px] text-gold font-semibold">
            {Math.round(turnoverYi).toLocaleString()}亿
          </span>
        </div>
      )}
    </div>
  )
}
