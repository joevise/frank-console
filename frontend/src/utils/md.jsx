import React from "react";

/**
 * Enhanced Markdown renderer — zero dependency.
 * Supports: headings, bold, italic, inline code, code blocks,
 * ordered/unordered lists, blockquotes, hr, links, paragraphs.
 */
export function renderInline(text) {
  if (!text) return null;

  const tokens = [];
  const regex =
    /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\[[^\]]+\]\([^)]+\))/g;
  let lastIndex = 0;
  let match;
  let keyIdx = 0;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      tokens.push(
        <span key={keyIdx++}>{text.slice(lastIndex, match.index)}</span>
      );
    }
    const m = match[0];
    if (m.startsWith("**") && m.endsWith("**")) {
      tokens.push(
        <strong key={keyIdx++} className="font-semibold text-ink">
          {m.slice(2, -2)}
        </strong>
      );
    } else if (m.startsWith("`") && m.endsWith("`")) {
      tokens.push(
        <code
          key={keyIdx++}
          className="bg-[#0a0a0a] border border-border rounded px-1.5 py-0.5 text-[12px] font-mono text-[#FFD700]"
        >
          {m.slice(1, -1)}
        </code>
      );
    } else {
      // link
      const linkMatch = m.match(/\[([^\]]+)\]\(([^)]+)\)/);
      if (linkMatch) {
        tokens.push(
          <a
            key={keyIdx++}
            href={linkMatch[2]}
            target="_blank"
            rel="noreferrer"
            className="text-[#FFD700] hover:underline"
          >
            {linkMatch[1]}
          </a>
        );
      }
    }
    lastIndex = regex.lastIndex;
  }
  if (lastIndex < text.length) {
    tokens.push(<span key={keyIdx++}>{text.slice(lastIndex)}</span>);
  }
  return tokens;
}

export function MarkdownContent({ content, className }) {
  if (!content) return null;

  const lines = content.split("\n");
  const blocks = [];
  let paragraphs = [];
  let listItems = [];
  let codeBlock = null;
  let quoteLines = [];

  const flushParagraphs = () => {
    if (paragraphs.length > 0) {
      blocks.push(
        <p
          key={`p-${blocks.length}`}
          className="text-[14px] text-ink-soft leading-[1.85] mb-3"
        >
          {paragraphs.map((line, i) => (
            <React.Fragment key={i}>
              {i > 0 && <br />}
              {renderInline(line)}
            </React.Fragment>
          ))}
        </p>
      );
      paragraphs = [];
    }
  };

  const flushList = () => {
    if (listItems.length > 0) {
      blocks.push(
        <div key={`list-${blocks.length}`} className="mb-3 space-y-1">
          {listItems.map((item, i) => (
            <div
              key={i}
              className="text-[14px] text-ink-soft leading-[1.8] flex gap-2 pl-2"
            >
              <span className="text-[#FFD700] shrink-0 font-mono">
                {item.marker}
              </span>
              <span>{renderInline(item.text)}</span>
            </div>
          ))}
        </div>
      );
      listItems = [];
    }
  };

  const flushQuote = () => {
    if (quoteLines.length > 0) {
      blocks.push(
        <blockquote
          key={`q-${blocks.length}`}
          className="border-l-2 border-[#FFD700]/40 pl-4 my-3 text-[13px] text-ink-soft italic space-y-1"
        >
          {quoteLines.map((line, i) => (
            <div key={i}>{renderInline(line)}</div>
          ))}
        </blockquote>
      );
      quoteLines = [];
    }
  };

  const flushCodeBlock = () => {
    if (codeBlock !== null) {
      blocks.push(
        <pre
          key={`code-${blocks.length}`}
          className="bg-[#0a0a0a] border border-border rounded-lg p-3 mb-3 overflow-x-auto"
        >
          <code className="text-[12px] font-mono text-ink leading-relaxed whitespace-pre">
            {codeBlock}
          </code>
        </pre>
      );
      codeBlock = null;
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();

    // Code block
    if (trimmed.startsWith("```")) {
      if (codeBlock !== null) {
        flushCodeBlock();
      } else {
        flushParagraphs();
        flushList();
        flushQuote();
        codeBlock = "";
      }
      continue;
    }
    if (codeBlock !== null) {
      codeBlock += (codeBlock ? "\n" : "") + line;
      continue;
    }

    // Empty line
    if (!trimmed) {
      flushParagraphs();
      flushList();
      flushQuote();
      continue;
    }

    // Horizontal rule
    if (/^---+$/.test(trimmed) || /^\*\*\*+$/.test(trimmed)) {
      flushParagraphs();
      flushList();
      flushQuote();
      blocks.push(<hr key={`hr-${i}`} className="border-border my-4" />);
      continue;
    }

    // Headings
    const h1 = trimmed.match(/^#\s+(.+)/);
    const h2 = trimmed.match(/^##\s+(.+)/);
    const h3 = trimmed.match(/^###\s+(.+)/);
    if (h1 || h2 || h3) {
      flushParagraphs();
      flushList();
      flushQuote();
      const text = (h1 || h2 || h3)[1];
      const cls = h1
        ? "text-[16px] font-bold text-ink mt-5 mb-2"
        : h2
          ? "text-[15px] font-bold text-ink mt-4 mb-2"
          : "text-[14px] font-semibold text-ink mt-3 mb-1";
      blocks.push(
        <div key={`h-${i}`} className={cls}>
          {renderInline(text)}
        </div>
      );
      continue;
    }

    // Blockquote
    if (trimmed.startsWith(">")) {
      flushParagraphs();
      flushList();
      quoteLines.push(trimmed.replace(/^>\s?/, ""));
      continue;
    } else if (quoteLines.length > 0) {
      flushQuote();
    }

    // Ordered list
    const ordered = trimmed.match(/^(\d+)\.\s+(.+)/);
    if (ordered) {
      flushParagraphs();
      listItems.push({ marker: `${ordered[1]}.`, text: ordered[2] });
      continue;
    }

    // Unordered list
    const unordered = trimmed.match(/^[-•·]\s+(.+)/);
    if (unordered) {
      flushParagraphs();
      listItems.push({ marker: "·", text: unordered[1] });
      continue;
    }

    // Regular text
    flushList();
    if (quoteLines.length > 0) flushQuote();
    paragraphs.push(trimmed);
  }

  // Flush remaining
  flushParagraphs();
  flushList();
  flushQuote();
  flushCodeBlock();

  return <div className={className}>{blocks}</div>;
}

export default MarkdownContent;
