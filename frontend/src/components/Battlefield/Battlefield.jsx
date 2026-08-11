import MainlineMap from './MainlineMap'
import PortfolioMap from './PortfolioMap'
import SignalPanel from './SignalPanel'

export default function Battlefield({
  mainlines,
  portfolio,
  signals,
  onSelectStock,
  onMoveToWatch,
  onSignalAction,
}) {
  return (
    <div className="flex flex-col md:grid md:grid-cols-[30%_1fr_30%] gap-3 min-h-0">
      <MainlineMap mainlines={mainlines} onSelectStock={onSelectStock} />
      <PortfolioMap
        items={portfolio}
        onSelectStock={onSelectStock}
        onMoveToWatch={onMoveToWatch}
      />
      <SignalPanel
        signals={signals}
        onSelectStock={onSelectStock}
        onAction={onSignalAction}
      />
    </div>
  )
}
