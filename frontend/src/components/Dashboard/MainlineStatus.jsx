export default function MainlineStatus({ mainlines }) {
  const bull = mainlines?.bull || []
  const topBull = bull.slice(0, 4)
  const maxDays = Math.max(10, ...bull.map((item) => item?.持续天数 || 0))

  if (topBull.length === 0) {
    return (
      <div className="bg-panel border border-border rounded-xl p-3 h-full flex flex-col">
        <span className="font-mono text-[10px] text-gold uppercase tracking-widest">
          主线多头
        </span>
        <div className="flex-1 flex items-center justify-center font-mono text-[11px] text-ink-dim">
          加载中…
        </div>
      </div>
    )
  }

  return (
    <div className="bg-panel border border-border rounded-xl p-3 h-full flex flex-col">
      <div className="flex items-center justify-between mb-2">
        <span className="font-mono text-[10px] text-gold uppercase tracking-widest">
          主线多头
        </span>
        <span className="font-mono text-[10px] text-ink-soft">
          {bull.length}行业
        </span>
      </div>

      <div className="flex-1 flex flex-col gap-1.5 justify-center">
        {topBull.map((item, idx) => {
          const days = item?.持续天数 || 0
          const industry = item?.行业 || '?'
          const widthPct = Math.min(100, (days / maxDays) * 100)
          const color = days >= 7 ? '#FFD700' : days >= 4 ? '#ffdd57' : '#666'

          return (
            <div key={idx} className="flex items-center gap-2">
              <span className="font-mono text-[10px] text-ink-dim w-3 shrink-0">
                {idx + 1}
              </span>
              <span className="text-xs text-ink flex-1 truncate">{industry}</span>
              <div className="w-12 h-1.5 bg-[#222] rounded-full overflow-hidden shrink-0">
                <div
                  className="h-full rounded-full transition-all"
                  style={{ width: `${widthPct}%`, backgroundColor: color }}
                />
              </div>
              <span
                className="font-mono text-[10px] shrink-0"
                style={{ color }}
              >
                {days}d
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
