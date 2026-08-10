import React from 'react'
import MainlineMap from './MainlineMap'
import PortfolioMap from './PortfolioMap'
import SignalPanel from './SignalPanel'

// ============================================================
// Battlefield - 第二层：主线作战室
// 三栏布局：左 30% / 中 40% / 右 30%
// ============================================================

export default function Battlefield({
  mainlines,
  portfolio,
  signals,
  onSelectStock,
  onMoveToWatch,
}) {
  return (
    <div className="flex-1 grid grid-cols-[30%_1fr_30%] gap-3 min-h-0">
      <MainlineMap mainlines={mainlines} onSelectStock={onSelectStock} />
      <PortfolioMap
        items={portfolio}
        onSelectStock={onSelectStock}
        onMoveToWatch={onMoveToWatch}
      />
      <SignalPanel signals={signals} onSelectStock={onSelectStock} />
    </div>
  )
}