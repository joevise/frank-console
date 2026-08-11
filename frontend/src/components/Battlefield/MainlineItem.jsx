export default function MainlineItem({ name, days, isBear }) {
  const color = isBear
    ? '#00d1b2'
    : days >= 7
      ? '#FFD700'
      : days >= 4
        ? '#ffdd57'
        : '#666'
  const widthPct = Math.min(100, ((days || 0) / 20) * 100)
  const label = isBear ? '空' : days >= 7 ? '强' : days >= 4 ? '中' : '新'

  return (
    <div className="flex items-center gap-2 px-3 py-2 rounded-lg transition hover:bg-[#1c1c1c]">
      <span
        className="w-2 h-2 rounded-full shrink-0"
        style={{ backgroundColor: color }}
      />
      <span className="text-[13px] font-medium text-ink flex-1 truncate">
        {name}
      </span>
      <span
        className="font-mono text-[10px] px-1.5 py-0.5 rounded"
        style={{ backgroundColor: `${color}1a`, color }}
      >
        {label}
      </span>
      <div className="w-10 h-1.5 bg-[#222] rounded-full overflow-hidden">
        <div
          className="h-full rounded-full"
          style={{ width: `${widthPct}%`, backgroundColor: color }}
        />
      </div>
      <span className="font-mono text-[10px] text-ink-soft w-8 text-right">
        {days}d
      </span>
    </div>
  )
}
