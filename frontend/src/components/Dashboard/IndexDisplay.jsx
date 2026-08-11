function IndexDisplay({ idx, label }) {
  if (!idx) {
    return (
      <div className="flex items-baseline justify-between">
        <span className="font-mono text-[10px] text-ink-dim">{label}</span>
        <span className="font-mono text-[11px] text-ink-dim">-</span>
      </div>
    )
  }

  const isUp = idx.change_pct > 0
  const color = isUp ? '#ff3860' : idx.change_pct < 0 ? '#00d1b2' : '#888'

  return (
    <div className="flex items-baseline justify-between gap-1 min-w-0">
      <span className="font-mono text-[10px] text-ink-soft shrink-0">
        {idx.name || label}
      </span>
      <div className="flex items-baseline gap-1 min-w-0">
        <span className="font-mono text-[12px] font-semibold text-ink truncate">
          {idx.price?.toFixed(2)}
        </span>
        <span className="font-mono text-[10px] shrink-0" style={{ color }}>
          {isUp ? '+' : ''}
          {idx.change_pct}%
        </span>
      </div>
    </div>
  )
}

export default IndexDisplay
