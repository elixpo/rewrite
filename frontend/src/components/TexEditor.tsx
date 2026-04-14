"use client";

import { useRef, useCallback, useMemo, useState } from "react";

export interface DiffChunk {
  /** Paragraph index in the original document */
  paraIndex: number;
  originalText: string;
  rewrittenText: string;
  /** Start line number in the original */
  startLine: number;
  endLine: number;
}

interface TexEditorProps {
  value: string;
  onChange: (value: string) => void;
  readOnly?: boolean;
  paragraphScores?: Array<{ startLine: number; score: number }>;
  activeParagraph?: number;
  /** Diff chunks to overlay on the editor during paraphrase */
  diffs?: DiffChunk[];
  /** Lock message shown when editor is locked */
  lockMessage?: string;
}

const LINE_HEIGHT = 22;
const FONT_SIZE = 13;
const PAD_TOP = 12;
const PAD_LEFT = 16;
const PAD_RIGHT = 16;
const GUTTER_WIDTH = 48;

export function TexEditor({
  value,
  onChange,
  readOnly = false,
  paragraphScores,
  activeParagraph,
  diffs,
  lockMessage,
}: TexEditorProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const gutterRef = useRef<HTMLDivElement>(null);
  const highlightRef = useRef<HTMLPreElement>(null);

  const lines = useMemo(() => value.split("\n"), [value]);

  const handleScroll = useCallback(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    if (gutterRef.current) gutterRef.current.scrollTop = ta.scrollTop;
    if (highlightRef.current) {
      highlightRef.current.scrollTop = ta.scrollTop;
      highlightRef.current.scrollLeft = ta.scrollLeft;
    }
  }, []);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Tab") {
        e.preventDefault();
        const ta = e.currentTarget;
        const start = ta.selectionStart;
        const end = ta.selectionEnd;
        const newVal = value.substring(0, start) + "  " + value.substring(end);
        onChange(newVal);
        requestAnimationFrame(() => {
          ta.selectionStart = ta.selectionEnd = start + 2;
        });
      }
    },
    [value, onChange]
  );

  const lineScores = useMemo(() => {
    const map = new Map<number, number>();
    if (!paragraphScores) return map;
    for (const ps of paragraphScores) map.set(ps.startLine, ps.score);
    return map;
  }, [paragraphScores]);

  // Build diff line markers: which lines have diffs
  const diffLineMap = useMemo(() => {
    const map = new Map<number, "removed" | "changed">();
    if (!diffs) return map;
    for (const d of diffs) {
      for (let l = d.startLine; l <= d.endLine; l++) {
        map.set(l, "changed");
      }
    }
    return map;
  }, [diffs]);

  const hasDiffs = diffs && diffs.length > 0;

  // Word-wrap style — always on
  const textStyle: React.CSSProperties = {
    fontFamily: "var(--font-mono)",
    fontSize: FONT_SIZE,
    lineHeight: `${LINE_HEIGHT}px`,
    tabSize: 2,
    whiteSpace: "pre-wrap",
    wordWrap: "break-word",
    overflowWrap: "break-word",
    padding: `${PAD_TOP}px ${PAD_RIGHT}px ${PAD_TOP}px ${PAD_LEFT}px`,
    margin: 0,
    border: "none",
    outline: "none",
  };

  return (
    <div className="editor-container flex flex-col relative">
      {/* Lock overlay */}
      {lockMessage && (
        <div className="absolute inset-0 z-20 bg-[rgba(20,25,22,0.6)] backdrop-blur-[2px] flex items-start justify-center pt-20 pointer-events-none">
          <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-editor-bg border border-lime-border text-lime text-xs font-medium">
            <span className="w-3 h-3 rounded-full border-2 border-lime border-t-transparent animate-spin" />
            {lockMessage}
          </div>
        </div>
      )}

      {/* Toolbar */}
      <div className="editor-toolbar shrink-0">
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-[#ff5f57]" />
          <span className="w-3 h-3 rounded-full bg-[#febc2e]" />
          <span className="w-3 h-3 rounded-full bg-[#28c840]" />
        </div>
        <span className="text-text-subtle text-xs font-mono ml-2">document.tex</span>
        <div className="flex-1" />
        {hasDiffs && (
          <span className="text-lime text-[10px] font-mono mr-2">
            {diffs.length} paragraph{diffs.length !== 1 ? "s" : ""} changed
          </span>
        )}
        <span className="text-text-subtle text-xs">
          {lines.length} lines
        </span>
      </div>

      {/* Editor body */}
      <div className="flex flex-1 min-h-[400px] relative" style={{ maxHeight: "calc(100vh - 110px)" }}>
        {/* Gutter */}
        <div
          ref={gutterRef}
          className="shrink-0 overflow-hidden select-none bg-editor-gutter text-text-subtle"
          style={{ width: GUTTER_WIDTH }}
        >
          <div style={{ paddingTop: PAD_TOP }}>
            {lines.map((_, i) => {
              const score = lineScores.get(i);
              const isActive = activeParagraph !== undefined && activeParagraph === i;
              const diffType = diffLineMap.get(i);
              return (
                <div
                  key={i}
                  className={`px-2 text-right text-xs ${
                    isActive ? "bg-lime-dim text-lime" :
                    diffType === "changed" ? "bg-[rgba(163,230,53,0.08)]" : ""
                  }`}
                  style={{ lineHeight: `${LINE_HEIGHT}px`, minHeight: LINE_HEIGHT }}
                >
                  {score !== undefined ? (
                    <span className={`text-[10px] font-bold ${
                      score >= 60 ? "text-error" : score >= 20 ? "text-warning" : "text-success"
                    }`}>
                      {score.toFixed(0)}%
                    </span>
                  ) : diffType === "changed" ? (
                    <span className="text-lime text-[10px]">~</span>
                  ) : (
                    i + 1
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Highlight layer */}
        <pre
          ref={highlightRef}
          className="absolute inset-0 overflow-hidden pointer-events-none"
          style={{
            ...textStyle,
            left: GUTTER_WIDTH,
            right: 0,
            top: 0,
            bottom: 0,
            color: "transparent",
            background: "transparent",
          }}
          aria-hidden="true"
        >
          {hasDiffs ? highlightWithDiffs(value, diffs) : highlightTex(value)}
        </pre>

        {/* Textarea */}
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onScroll={handleScroll}
          onKeyDown={handleKeyDown}
          readOnly={readOnly || !!lockMessage}
          spellCheck={false}
          className="flex-1 bg-transparent resize-none caret-lime"
          style={{
            ...textStyle,
            color: "transparent",
            caretColor: "var(--color-lime)",
            WebkitTextFillColor: "transparent",
            overflow: "auto",
          }}
          placeholder={"% Paste your LaTeX document here...\n\\documentclass{article}\n\\begin{document}\n\nYour text goes here.\n\n\\end{document}"}
        />
      </div>
    </div>
  );
}

// ====================================================================
// Diff-aware highlighting
// ====================================================================

function highlightWithDiffs(source: string, diffs: DiffChunk[]): React.ReactNode[] {
  const result: React.ReactNode[] = [];
  const lines = source.split("\n");

  // Build a set of changed line ranges
  const changedLines = new Set<number>();
  for (const d of diffs) {
    for (let l = d.startLine; l <= d.endLine; l++) changedLines.add(l);
  }

  for (let li = 0; li < lines.length; li++) {
    if (li > 0) result.push("\n");
    if (changedLines.has(li)) {
      // This line was rewritten — show in green with background
      result.push(
        <span key={`diff-${li}`} className="diff-added">{lines[li]}</span>
      );
    } else {
      // Normal syntax highlighting
      const tokens = tokenizeLine(lines[li]);
      for (let ti = 0; ti < tokens.length; ti++) {
        const t = tokens[ti];
        result.push(<span key={`${li}-${ti}`} className={TOKEN_CLASSES[t.type]}>{t.value}</span>);
      }
    }
  }

  return result;
}

// ====================================================================
// LaTeX syntax highlighter
// ====================================================================

type TokenType =
  | "comment" | "command" | "section" | "env" | "math-delim"
  | "math-body" | "brace" | "bracket" | "argument" | "text";

interface Token { type: TokenType; value: string; }

const SECTION_COMMANDS = new Set([
  "documentclass", "usepackage", "title", "author", "date",
  "chapter", "section", "subsection", "subsubsection",
  "paragraph", "subparagraph", "part", "tableofcontents", "maketitle",
]);

const ENV_COMMANDS = new Set(["begin", "end"]);

function tokenizeLine(line: string): Token[] {
  const tokens: Token[] = [];
  let i = 0;
  while (i < line.length) {
    if (line[i] === "%" && (i === 0 || line[i - 1] !== "\\")) {
      tokens.push({ type: "comment", value: line.slice(i) }); break;
    }
    if (line[i] === "$") {
      const double = line[i + 1] === "$";
      const delim = double ? "$$" : "$";
      i += delim.length;
      tokens.push({ type: "math-delim", value: delim });
      let body = "";
      while (i < line.length) {
        if (line[i] === "$") { if (double && line[i + 1] === "$") break; else if (!double) break; }
        body += line[i]; i++;
      }
      if (body) tokens.push({ type: "math-body", value: body });
      if (i < line.length) { tokens.push({ type: "math-delim", value: delim }); i += delim.length; }
      continue;
    }
    if (line[i] === "\\") {
      i++;
      if (i < line.length && /[\\{}$%&#_~^,;!| ]/.test(line[i])) {
        tokens.push({ type: "command", value: "\\" + line[i] }); i++; continue;
      }
      let name = "";
      while (i < line.length && /[a-zA-Z@*]/.test(line[i])) { name += line[i]; i++; }
      if (!name) { tokens.push({ type: "text", value: "\\" }); continue; }
      const fullCmd = "\\" + name;
      if (ENV_COMMANDS.has(name)) {
        tokens.push({ type: "env", value: fullCmd });
        if (i < line.length && line[i] === "{") {
          const s = i; let d = 0;
          while (i < line.length) { if (line[i] === "{") d++; else if (line[i] === "}") { d--; if (d === 0) { i++; break; } } i++; }
          tokens.push({ type: "env", value: line.slice(s, i) });
        }
      } else if (SECTION_COMMANDS.has(name)) {
        tokens.push({ type: "section", value: fullCmd });
      } else {
        tokens.push({ type: "command", value: fullCmd });
      }
      if (i < line.length && line[i] === "[") {
        const s = i; let d = 0;
        while (i < line.length) { if (line[i] === "[") d++; else if (line[i] === "]") { d--; if (d === 0) { i++; break; } } i++; }
        tokens.push({ type: "bracket", value: line.slice(s, i) });
      }
      if (i < line.length && line[i] === "{") {
        const s = i; let d = 0;
        while (i < line.length) { if (line[i] === "{") d++; else if (line[i] === "}") { d--; if (d === 0) { i++; break; } } i++; }
        tokens.push({ type: "argument", value: line.slice(s, i) });
      }
      continue;
    }
    if (line[i] === "{" || line[i] === "}") { tokens.push({ type: "brace", value: line[i] }); i++; continue; }
    let text = "";
    while (i < line.length && !["\\", "$", "%", "{", "}"].includes(line[i])) { text += line[i]; i++; }
    if (text) tokens.push({ type: "text", value: text });
  }
  return tokens;
}

const TOKEN_CLASSES: Record<TokenType, string> = {
  comment: "tex-comment", command: "tex-command", section: "tex-section",
  env: "tex-env", "math-delim": "tex-math", "math-body": "tex-math",
  brace: "tex-brace", bracket: "tex-bracket", argument: "tex-argument", text: "tex-text",
};

function highlightTex(source: string): React.ReactNode[] {
  const result: React.ReactNode[] = [];
  const lines = source.split("\n");
  for (let li = 0; li < lines.length; li++) {
    if (li > 0) result.push("\n");
    const tokens = tokenizeLine(lines[li]);
    for (let ti = 0; ti < tokens.length; ti++) {
      const t = tokens[ti];
      result.push(<span key={`${li}-${ti}`} className={TOKEN_CLASSES[t.type]}>{t.value}</span>);
    }
  }
  return result;
}
