import { useState, useEffect } from "react";
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
} from "recharts";

/* ------------------------------------------------------------------ */
/*  RadarChart sub-component                                          */
/* ------------------------------------------------------------------ */

const RADAR_COLOR = "#FFD700";

function StockRadar({ radar }) {
  const data = [
    { dim: "技术面", value: radar?.tech ?? 0 },
    { dim: "基本面", value: radar?.fundamental ?? 0 },
    { dim: "行业", value: radar?.industry ?? 0 },
    { dim: "铁律", value: radar?.rules ?? 0 },
  ];
  return (
    <div className="h-48 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={data} cx="50%" cy="50%" outerRadius="75%">
          <PolarGrid stroke="#2a2a2a" />
          <PolarAngleAxis
            dataKey="dim"
            tick={{
              fill: "#8a8a8a",
              fontSize: 11,
              fontFamily: "IBM Plex Mono",
            }}
          />
          <PolarRadiusAxis
            angle={90}
            domain={[0, 100]}
            tick={{ fill: "#444", fontSize: 9 }}
            stroke="#2a2a2a"
          />
          <Radar
            name="评分"
            dataKey="value"
            stroke={RADAR_COLOR}
            fill={RADAR_COLOR}
            fillOpacity={0.35}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  ScoreBar sub-component                                            */
/* ------------------------------------------------------------------ */

function ScoreBar({ label, value, hint }) {
  const v = value ?? 0;
  const color = v >= 70 ? "#00d1b2" : v >= 40 ? "#ffdd57" : "#ff3860";
  return (
    <div className="flex items-center justify-between py-1.5 border-b border-[#262626] last:border-0">
      <span className="text-[12px] text-[#888]">{label}</span>
      <div className="flex items-center gap-2">
        {hint && (
          <span className="font-mono text-[10px] text-[#888]/70">{hint}</span>
        )}
        <div className="w-16 h-1.5 bg-[#1c1c1c] rounded-full overflow-hidden">
          <div
            className="h-full rounded-full"
            style={{ width: `${v}%`, backgroundColor: color }}
          />
        </div>
        <span
          className="font-mono text-xs font-semibold w-6 text-right"
          style={{ color }}
        >
          {v}
        </span>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  StockDrawer (main export)                                         */
/* ------------------------------------------------------------------ */

export default function StockDrawer({
  stock,
  analysis,
  loading,
  steps,
  onClose,
  onChatWithDSA,
}) {
  const [closing, setClosing] = useState(false);

  useEffect(() => {
    const handler = (e) => e.key === "Escape" && handleClose();
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  const handleClose = () => {
    setClosing(true);
    setTimeout(onClose, 200);
  };

  if (!stock) return null;

  return (
    <>
      <div
        onClick={handleClose}
        className={`fixed inset-0 bg-black/40 z-40 transition-opacity ${
          closing ? "opacity-0" : "opacity-100"
        }`}
      />
      <aside
        className={`fixed top-0 right-0 h-full w-full md:w-[420px] max-w-none md:max-w-[90vw] bg-[#161616] border-l border-[#262626] z-50 flex flex-col shadow-2xl ${
          closing
            ? "animate-fade-in opacity-0"
            : "animate-slide-in-right"
        }`}
      >
        {/* Header */}
        <div className="px-5 py-4 border-b border-[#262626] flex items-center gap-3">
          <button
            onClick={handleClose}
            className="w-11 h-11 md:w-7 md:h-7 rounded-md hover:bg-[#161616] text-[#888] hover:text-[#f5f5f5] flex items-center justify-center"
          >
            ✕
          </button>
          <div className="flex-1 min-w-0">
            <div className="text-base font-semibold text-[#f5f5f5] truncate">
              {stock.stock_name || stock.name}
            </div>
            <div className="font-mono text-[10px] text-[#888]">
              {stock.stock_code}
            </div>
          </div>
          {stock.mainline && (
            <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-[#1c1c1c] text-[#888]">
              {stock.mainline}
            </span>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-5">
          {loading ? (
            <div className="text-[#888] text-sm text-center py-12">
              <div className="font-mono text-[11px] animate-pulse text-[#FFD700] mb-3">
                DSA 分析师诊断中…
              </div>
              {(steps || []).length > 0 && (
                <div className="space-y-1 text-left max-w-[300px] mx-auto">
                  {(steps || []).map((s, i) => (
                    <div
                      key={i}
                      className="flex items-center gap-1.5 font-mono text-[10px] animate-fade-in-up"
                      style={{ animationDelay: `${i * 100}ms` }}
                    >
                      <span className="text-[#FFD700]">✓</span>
                      <span className="text-[#888]">{s}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : analysis ? (
            <>
              {/* Quote */}
              <section>
                <div className="font-mono text-[10px] text-[#888] uppercase tracking-widest mb-2">
                  实时行情
                </div>
                {analysis.quote ? (
                  <div className="grid grid-cols-3 gap-2 text-center">
                    <div className="bg-[#161616] border border-[#262626] rounded-lg p-2">
                      <div className="font-mono text-sm font-semibold text-[#f5f5f5]">
                        {analysis.quote.price}
                      </div>
                      <div className="font-mono text-[9px] text-[#888]">
                        现价
                      </div>
                    </div>
                    <div className="bg-[#161616] border border-[#262626] rounded-lg p-2">
                      <div
                        className="font-mono text-sm font-semibold"
                        style={{
                          color:
                            analysis.quote.change_pct > 0
                              ? "#ff3860"
                              : analysis.quote.change_pct < 0
                              ? "#00d1b2"
                              : "#8a8a8a",
                        }}
                      >
                        {analysis.quote.change_pct > 0 ? "+" : ""}
                        {analysis.quote.change_pct}%
                      </div>
                      <div className="font-mono text-[9px] text-[#888]">
                        涨跌
                      </div>
                    </div>
                    <div className="bg-[#161616] border border-[#262626] rounded-lg p-2">
                      <div className="font-mono text-sm font-semibold text-[#f5f5f5]">
                        {analysis.quote.amount_yi}亿
                      </div>
                      <div className="font-mono text-[9px] text-[#888]">
                        成交额
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-[11px] text-[#888] italic">
                    行情数据暂不可用
                  </div>
                )}
              </section>

              {/* Radar */}
              <section>
                <div className="font-mono text-[10px] text-[#888] uppercase tracking-widest mb-2">
                  四维雷达
                </div>
                <StockRadar radar={analysis.radar} />
              </section>

              {/* Scores */}
              <section>
                <div className="font-mono text-[10px] text-[#888] uppercase tracking-widest mb-2">
                  分项评分
                </div>
                <ScoreBar
                  label="技术面"
                  value={analysis.radar?.tech}
                />
                <ScoreBar
                  label="基本面"
                  value={analysis.radar?.fundamental}
                />
                <ScoreBar
                  label="行业面"
                  value={analysis.radar?.industry}
                />
                <ScoreBar
                  label="铁律"
                  value={analysis.radar?.rules}
                />
              </section>

              {/* DSA Steps */}
              {(analysis.dsa_steps || []).length > 0 && (
                <section>
                  <div className="font-mono text-[10px] text-[#FFD700] uppercase tracking-widest mb-2">
                    DSA 分析步骤
                  </div>
                  <div className="space-y-1 bg-[#161616] border border-[#262626] rounded-lg p-3">
                    {analysis.dsa_steps.map((s, i) => (
                      <div
                        key={i}
                        className="flex items-center gap-1.5 font-mono text-[10px]"
                      >
                        <span className="text-[#FFD700]">✓</span>
                        <span className="text-[#888]">{s}</span>
                      </div>
                    ))}
                  </div>
                </section>
              )}

              {/* Opinion */}
              <section>
                <div className="font-mono text-[10px] text-[#888] uppercase tracking-widest mb-2">
                  DSA 观点
                </div>
                <div className="bg-[#161616] border border-[#262626] rounded-lg p-3 text-[13px] text-[#f5f5f5] leading-relaxed">
                  {analysis.summary || analysis.dsa_opinion || "暂无观点"}
                </div>
              </section>

              {/* Action */}
              {analysis.action && (
                <section>
                  <div className="font-mono text-[10px] text-[#888] uppercase tracking-widest mb-2">
                    操作建议
                  </div>
                  <div className="bg-[#161616] border border-[#262626] rounded-lg p-3 text-[13px] text-[#f5f5f5]">
                    {analysis.action}
                  </div>
                </section>
              )}
            </>
          ) : (
            <div className="text-[#888] text-sm text-center py-12">
              暂无论断数据
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-5 py-4 border-t border-[#262626]">
          <button
            onClick={() => onChatWithDSA?.(stock)}
            className="w-full bg-[#FFD700] text-ink font-semibold rounded-lg py-2.5 text-sm hover:bg-[#FFD700]/90 transition flex items-center justify-center gap-2"
          >
            <span>跟 DSA 深入聊</span>
            <span>→</span>
          </button>
        </div>
      </aside>
    </>
  );
}
