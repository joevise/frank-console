import React from 'react'

// ============================================================
// MorningBrief - 晨报抽屉（从右侧滑出，由左侧边栏按钮控制）
// 不悬浮于顶部栏，不遮挡其他内容
// ============================================================

export default function MorningBrief({ open, brief, generating, onGenerate, onClose }) {
  return (
    <>
      {/* 遮罩 */}
      <div
        onClick={onClose}
        className={`fixed inset-0 bg-black/20 z-20 transition-opacity ${
          open ? 'opacity-100' : 'opacity-0 pointer-events-none'
        }`}
      />
      {/* 抽屉本体：顶栏之下、聊天框收起条之上 */}
      <div
        className={`fixed top-14 bottom-12 right-0 z-30 w-[400px] max-w-[92vw] bg-panel border-l border-border shadow-2xl flex flex-col transform transition-transform duration-300 ${
          open ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        <div className="h-12 px-4 flex items-center gap-2 border-b border-border shrink-0">
          <span className="text-base">📰</span>
          <span className="font-semibold text-sm">今日晨报</span>
          {brief && (
            <span className="font-mono text-[10px] text-ink-soft">{brief.date}</span>
          )}
          <div className="ml-auto flex items-center gap-2">
            <button
              onClick={onGenerate}
              disabled={generating}
              className="bg-ink text-accent text-xs px-2.5 py-1 rounded font-mono disabled:opacity-50"
            >
              {generating ? '生成中…' : '一键生成'}
            </button>
            <button
              onClick={onClose}
              className="text-ink-soft hover:text-ink text-sm px-1"
              aria-label="关闭"
            >
              ✕
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-4 py-4">
          {brief ? (
            <div className="space-y-3">
              <div className="font-mono text-[10px] text-ink-soft uppercase tracking-widest">
                关键观点
              </div>
              {brief.views.map((v, i) => (
                <div key={i} className="bg-code rounded-lg p-3">
                  <div className="text-[13px] font-semibold text-ink mb-1">{v.title}</div>
                  <div className="text-[12px] text-ink-soft leading-relaxed">{v.detail}</div>
                  {v.links && v.links.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {v.links.map((l, j) => (
                        <a
                          key={j}
                          href={l.url}
                          target="_blank"
                          rel="noreferrer"
                          className="font-mono text-[10px] text-accent hover:underline"
                        >
                          🔗 {l.label}
                        </a>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-sm text-ink-soft text-center py-10">
              暂无晨报，点击「一键生成」
            </div>
          )}
        </div>
      </div>
    </>
  )
}
