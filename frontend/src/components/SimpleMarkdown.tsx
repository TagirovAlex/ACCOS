import { useCallback, useState } from "react";

interface Props {
  text: string | null | undefined;
}

function CodeBlock({ code, language }: { code: string; language: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(() => {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(code).then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      }).catch(() => {
        fallbackCopy(code);
      });
    } else {
      fallbackCopy(code);
    }
  }, [code]);

  function fallbackCopy(text: string) {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    try {
      document.execCommand("copy");
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
    document.body.removeChild(ta);
  }

  return (
    <div style={{ position: "relative", margin: "8px 0" }}>
      <pre style={{
        padding: "28px 12px 12px", position: "relative",
        overflow: "auto", borderRadius: 8,
        backgroundColor: "rgba(0,0,0,0.06)",
        fontSize: 13, lineHeight: 1.5,
        fontFamily: "'Cascadia Code', 'Fira Code', 'Consolas', monospace",
        whiteSpace: "pre-wrap", wordBreak: "break-word",
      }}>
        <button
          onClick={handleCopy}
          style={{
            position: "absolute", top: 4, right: 8,
            fontSize: 11, padding: "2px 8px", cursor: "pointer",
            border: "1px solid", borderRadius: 4,
            background: "transparent", color: "inherit", opacity: 0.6,
            transition: "opacity 0.2s",
          }}
          onMouseEnter={e => { (e.target as HTMLElement).style.opacity = "1"; }}
          onMouseLeave={e => { (e.target as HTMLElement).style.opacity = "0.6"; }}
          title="Скопировать код"
        >
          {copied ? "✓ Скопировано" : "Копировать"}
        </button>
        <code className={language ? `language-${language}` : ""}>{code}</code>
      </pre>
    </div>
  );
}

function parseDocLinks(text: string): string {
  return text.replace(
    /\[doc:\s*([a-f0-9\-]+)\]/gi,
    '<span style="text-decoration:underline;font-weight:600;cursor:pointer;color:inherit" onclick="var w=Math.round(screen.width*0.85);var h=Math.round(screen.height*0.85);window.open(\'/api/v1/knowledge/$1/preview\',\'preview\',\'width=\'+w+\',height=\'+h+\',scrollbars=yes,resizable=yes\')">📄 [документ]</span>'
  );
}

export const SimpleMarkdown = ({ text }: Props) => {
  const content = text || "";
  const parts: { type: "code" | "text"; content: string; language?: string }[] = [];
  const codeBlockRegex = /```(\w*)\n?([\s\S]*?)```/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = codeBlockRegex.exec(content)) !== null) {
    if (match.index > lastIndex) {
      parts.push({ type: "text", content: content.slice(lastIndex, match.index) });
    }
    parts.push({ type: "code", content: match[2], language: match[1] });
    lastIndex = match.index + match[0].length;
  }
  if (lastIndex < content.length) {
    parts.push({ type: "text", content: content.slice(lastIndex) });
  }

  return (
    <span>
      {parts.map((part, i) => {
        if (part.type === "code") {
          return <CodeBlock key={i} code={part.content} language={part.language || ""} />;
        }
        const html = part.content
          .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
          .replace(/`([^`]+)`/g, "<code>$1</code>")
          .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
          .replace(/\*([^*]+)\*/g, "<em>$1</em>")
          .replace(/\n/g, "<br/>");
        const withLinks = parseDocLinks(html);
        return <span key={i} dangerouslySetInnerHTML={{ __html: withLinks }} />;
      })}
    </span>
  );
};
