"use client";

import { useRef, useCallback, useMemo } from "react";

export interface DiffChunk {
  paraIndex: number;
  originalText: string;
  rewrittenText: string;
  startLine: number;
  endLine: number;
}

interface TexEditorProps {
  value: string;
  onChange: (value: string) => void;
  readOnly?: boolean;
  paragraphScores?: Array<{ startLine: number; score: number }>;
  activeParagraph?: number;
  diffs?: DiffChunk[];
  lockMessage?: string;
}

const LINE_HEIGHT = 22;
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

  const lines = useMemo(() => value.split("\n"), [value]);

  const handleScroll = useCallback(() => {
    if (textareaRef.current && gutterRef.current) {
      gutterRef.current.scrollTop = textareaRef.current.scrollTop;
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

  const diffLines = useMemo(() => {
    const set = new Set<number>();
    if (!diffs) return set;
    for (const d of diffs) {
      for (let l = d.startLine; l <= d.endLine; l++) set.add(l);
    }
    return set;
  }, [diffs]);

  const hasDiffs = diffs && diffs.length > 0;

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
            {diffs.length} changed
          </span>
        )}
        <span className="text-text-subtle text-xs">{lines.length} lines</span>
      </div>

      {/* Editor body */}
      <div className="flex flex-1 min-h-[400px] relative" style={{ maxHeight: "calc(100vh - 110px)" }}>
        {/* Gutter */}
        <div
          ref={gutterRef}
          className="shrink-0 overflow-hidden select-none bg-editor-gutter text-text-subtle"
          style={{ width: GUTTER_WIDTH }}
        >
          <div className="py-3">
            {lines.map((_, i) => {
              const score = lineScores.get(i);
              const isActive = activeParagraph !== undefined && activeParagraph === i;
              const isDiff = diffLines.has(i);
              return (
                <div
                  key={i}
                  className={`px-2 text-right text-xs ${
                    isActive ? "bg-lime-dim text-lime" :
                    isDiff ? "bg-[rgba(163,230,53,0.08)]" : ""
                  }`}
                  style={{ lineHeight: `${LINE_HEIGHT}px`, minHeight: LINE_HEIGHT }}
                >
                  {score !== undefined ? (
                    <span className={`text-[10px] font-bold ${
                      score >= 60 ? "text-error" : score >= 20 ? "text-warning" : "text-success"
                    }`}>
                      {score.toFixed(0)}%
                    </span>
                  ) : isDiff ? (
                    <span className="text-lime text-[10px]">~</span>
                  ) : (
                    i + 1
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Textarea — direct editing, no overlay */}
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onScroll={handleScroll}
          onKeyDown={handleKeyDown}
          readOnly={readOnly || !!lockMessage}
          spellCheck={false}
          className="flex-1 bg-transparent text-text-primary font-mono text-[13px] py-3 px-4 resize-none outline-none overflow-auto caret-lime"
          style={{
            lineHeight: `${LINE_HEIGHT}px`,
            tabSize: 2,
            whiteSpace: "pre-wrap",
            wordWrap: "break-word",
            overflowWrap: "break-word",
          }}
          placeholder={"% Paste your LaTeX document here...\n\\documentclass{article}\n\\begin{document}\n\nYour text goes here.\n\n\\end{document}"}
        />
      </div>
    </div>
  );
}
