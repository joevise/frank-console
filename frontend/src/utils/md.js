// ============================================================
// md.js — 极简 Markdown → HTML 渲染（零依赖）
// 支持：标题、粗体、斜体、行内代码、代码块、表格、列表、引用、分隔线、链接
// ============================================================

function escapeHtml(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
}

function inlineMd(text) {
  return text
    // 行内代码
    .replace(/`([^`]+)`/g, '<code class="md-code">$1</code>')
    // 粗体
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    // 斜体
    .replace(/\*([^*]+)\*/g, '<em>$1</em>')
    // 链接
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
}

export function mdToHtml(md) {
  if (!md) return ""
  const lines = escapeHtml(md).split("\n")
  let html = []
  let inTable = false
  let inList = false
  let inCode = false
  let tableHeader = false

  for (let i = 0; i < lines.length; i++) {
    let line = lines[i]

    // 代码块
    if (line.trim().startsWith("```")) {
      if (inCode) {
        html.push("</code></pre>")
        inCode = false
      } else {
        html.push('<pre class="md-pre"><code>')
        inCode = true
      }
      continue
    }
    if (inCode) {
      html.push(line)
      continue
    }

    // 表格
    if (line.trim().startsWith("|") && line.trim().endsWith("|")) {
      const cells = line.split("|").filter((_, j, a) => j > 0 && j < a.length - 1).map(c => c.trim())
      // 检查是不是分隔行 |---|---|
      if (cells.every(c => /^[-:]+$/.test(c))) {
        tableHeader = false
        continue
      }
      if (!inTable) {
        html.push('<table class="md-table">')
        inTable = true
        tableHeader = true
      }
      const tag = tableHeader ? "th" : "td"
      const trClass = tableHeader ? ' class="md-th-row"' : ""
      html.push(`<tr${trClass}>${cells.map(c => `<${tag}>${inlineMd(c)}</${tag}>`).join("")}</tr>`)
      if (tableHeader) tableHeader = false
      continue
    } else if (inTable) {
      html.push("</table>")
      inTable = false
    }

    // 标题
    const hMatch = line.match(/^(#{1,4})\s+(.+)/)
    if (hMatch) {
      const level = hMatch[1].length
      html.push(`<h${level} class="md-h${level}">${inlineMd(hMatch[2])}</h${level}>`)
      continue
    }

    // 分隔线
    if (/^---+\s*$/.test(line)) {
      html.push('<hr class="md-hr"/>')
      continue
    }

    // 引用
    if (line.startsWith("&gt; ")) {
      html.push(`<blockquote class="md-quote">${inlineMd(line.slice(5))}</blockquote>`)
      continue
    }

    // 无序列表
    if (/^[-*]\s+/.test(line)) {
      if (!inList) { html.push('<ul class="md-ul">'); inList = true }
      html.push(`<li>${inlineMd(line.replace(/^[-*]\s+/, ""))}</li>`)
      continue
    } else if (inList) {
      html.push("</ul>")
      inList = false
    }

    // 有序列表
    if (/^\d+\.\s+/.test(line)) {
      html.push(`<div class="md-ol-item">${inlineMd(line)}</div>`)
      continue
    }

    // 空行
    if (!line.trim()) {
      html.push("")
      continue
    }

    // 普通段落
    html.push(`<p class="md-p">${inlineMd(line)}</p>`)
  }

  // 收尾
  if (inTable) html.push("</table>")
  if (inList) html.push("</ul>")
  if (inCode) html.push("</code></pre>")

  return html.join("\n")
}
