export default function PortfolioHealth({ data }) {
  const counts = data?.counts || {}
  const inMainline = counts.in_mainline || 0
  const outMainline = counts.out_mainline || 0
  const watch = counts.watch || 0
  const total = inMainline + outMainline

  return (
    <div className="bg-panel border border-border rounded-xl p-3 h-full flex flex-col">
      <div className="flex items-center justify-between mb-2">
        <span className="font-mono text-[10px] text-gold uppercase tracking-widest">
          持仓健康
        </span>
        <span className="font-mono text-[10px] text-ink-soft">{total}只</span>
      </div>

      <div className="flex-1 flex flex-col justify-center gap-2">
        <div className="flex items-center gap-2">
          <span
            className="w-2 h-2 rounded-full shrink-0"
            style={{ backgroundColor: '#FFD700' }}
          />
          <span className="text-[11px] text-ink-soft flex-1">在主线</span>
          <span className="font-mono text-sm font-semibold text-gold">
            {inMainline}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full shrink-0 bg-[#555]" />
          <span className="text-[11px] text-ink-soft flex-1">主线外</span>
          <span className="font-mono text-sm font-semibold text-ink-soft">
            {outMainline}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span
            className="w-2 h-2 rounded-full shrink-0"
            style={{ backgroundColor: '#ffdd57' }}
          />
          <span className="text-[11px] text-ink-soft flex-1">观察中</span>
          <span className="font-mono text-sm font-semibold text-warn">
            {watch}
          </span>
        </div>
      </div>
    </div>
  )
}
