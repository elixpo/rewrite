# ReWrite — Production Build TODO

## Phase 1: Core Infrastructure (Current — Local)

- [x] Project scaffold + venv
- [x] Pollinations API wrapper (llm.py)
- [x] Basic heuristic detector
- [x] Basic paraphraser with engineered prompts
- [x] CLI interface
- [ ] Restructure into modular architecture
  - [ ] `core/` — config, llm, embeddings
  - [ ] `detection/` — heuristics, llm_judge, ensemble, segment
  - [ ] `paraphrase/` — prompts, rewriter, postprocess, targeted
  - [ ] `document/` — parser, report, structure
  - [ ] `session/` — store (file-based placeholder), compression
- [ ] Central config module (API keys, thresholds, model selection)
- [ ] Enhanced LLM wrapper (retries, timeout handling, streaming)

## Phase 2: Detection Engine

- [ ] Refine heuristic scorers (tune weights against known AI/human samples)
- [ ] LLM-as-judge detector
  - Calibrated prompt asking LLM to rate AI likelihood per paragraph
  - Returns 0-100 score + reasoning
- [ ] Segment-level analysis
  - Break document into ~150-word chunks preserving sentence boundaries
  - Score each chunk independently
  - Track per-sentence and per-paragraph scores
- [ ] Ensemble scorer
  - Weighted combination: 0.35 LLM judge + 0.20 burstiness + 0.15 vocab + 0.10 TTR + 0.10 starters + 0.05 paragraph + 0.05 punctuation
  - Per-segment and whole-document rollup

## Phase 3: Document Pipeline

- [ ] PDF text extraction (preserve section structure, headings, citations)
- [ ] DOCX text extraction
- [ ] Document structure model (sections → paragraphs → sentences hierarchy)
- [ ] Annotated PDF report generation
  - Color-coded highlights: red (>60%), yellow (20-60%), green (<20%)
  - Per-paragraph score annotations in margin
  - Summary page with overall score + feature breakdown
- [ ] Clean rewritten PDF output (rewritten text in original formatting)

## Phase 4: Smart Paraphraser

- [ ] Domain-aware prompt templates (CS, medicine, law, humanities, general)
- [ ] Targeted rewriting pipeline
  - Only rewrite segments scoring >20% AI
  - Feed surrounding context (previous + next paragraph) for coherence
  - Context compression: summarize prior sections to fit context window
- [ ] Semantic similarity verification via LLM
  - Compare original vs rewritten paragraph meaning
  - Reject rewrites with similarity <0.85
  - Retry with adjusted prompt if rejected
- [ ] Iterative refinement loop
  - Rewrite → re-score → if still >20%, retry (max 3 attempts)
  - Escalate intensity on each retry (light → medium → aggressive)
  - Mark segments still >20% after 3 attempts for manual review
- [ ] Post-processing pipeline
  - AI marker word substitution (existing, expanded)
  - Burstiness injection (split/merge sentences if variance too low)
  - Sentence starter deduplication

## Phase 5: Session & Context Management (VPS)

- [ ] Redis session store
  - Document state (parsed structure, segment scores, rewrite history)
  - Job queue for long paper processing
  - TTL-based expiry for completed jobs
- [ ] Context compression for long papers
  - Sliding window: full text for current section, summaries for rest
  - Use LLM to generate section summaries for context
  - Track token budget per LLM call
- [ ] Semantic similarity via sentence-transformers (VPS only)
  - Replace LLM-based similarity with proper embedding cosine similarity
  - Model: all-MiniLM-L6-v2 (fast, 80MB) or all-mpnet-base-v2 (better, 420MB)

## Phase 6: API & Deployment (VPS)

- [ ] FastAPI REST API
  - POST /api/detect — text or file upload, returns segment-level scores
  - POST /api/paraphrase — text or file, returns rewritten + scores
  - GET /api/job/{id} — poll long-running jobs
  - GET /api/report/{id}/pdf — download annotated PDF
- [ ] Background job processing (Celery or asyncio tasks)
- [ ] Rate limiting and API key management
- [ ] Docker compose (app + Redis)
- [ ] Nginx reverse proxy + SSL

## Architecture Reference

```
app/
├── core/
│   ├── config.py            # Thresholds, API keys, model IDs
│   ├── llm.py               # Pollinations wrapper (retries, streaming)
│   └── embeddings.py        # Semantic similarity (LLM now, sentence-transformers on VPS)
├── detection/
│   ├── heuristics.py        # Statistical scorers (burstiness, vocab, TTR, etc.)
│   ├── llm_judge.py         # LLM evaluates AI likelihood per segment
│   ├── ensemble.py          # Weighted combination of all signals
│   └── segment.py           # Chunk text, score each segment
├── paraphrase/
│   ├── prompts.py           # Prompt templates by domain and intensity
│   ├── rewriter.py          # Core LLM rewriting
│   ├── postprocess.py       # Marker removal, burstiness injection
│   └── targeted.py          # Only rewrite flagged segments with context
├── document/
│   ├── parser.py            # PDF/DOCX → structured text
│   ├── report.py            # Generate annotated + clean PDFs
│   └── structure.py         # Document hierarchy model
├── session/
│   ├── store.py             # Redis (VPS) / file-based (local) session store
│   └── compression.py       # Summarize sections for context window management
└── cli.py                   # CLI with file I/O support
```

## Detection Ensemble Weights

```
Final Score = 0.35 × LLM_judge
            + 0.20 × burstiness
            + 0.15 × vocab_markers
            + 0.10 × TTR
            + 0.10 × sentence_starters
            + 0.05 × paragraph_structure
            + 0.05 × punctuation_diversity
```

## Paraphrase Pipeline (Full Paper)

```
1. Parse PDF/DOCX → structured text (sections, paragraphs)
2. Score each paragraph (ensemble detector)
3. Flag paragraphs >20% AI
4. For each flagged paragraph:
   a. Build context: [section summary] + [prev paragraph] + [target] + [next paragraph]
   b. Rewrite with domain-aware prompt
   c. Verify semantic similarity ≥ 0.85
   d. Re-score — if still >20%, retry with higher intensity (max 3)
   e. If still failing after 3 attempts → mark for manual review
5. Reassemble document
6. Output:
   - Detection report PDF (color-coded highlights + scores)
   - Clean rewritten PDF
```

## Thresholds

| Metric | Green | Yellow | Red |
|--------|-------|--------|-----|
| AI score per segment | <20% | 20-60% | >60% |
| Semantic similarity | ≥0.85 | 0.70-0.85 | <0.70 |
| Max rewrite attempts | — | — | 3 |

## Notes

- Pollinations API requires auth — need API key in config
- Redis deferred until VPS transfer
- Sentence-transformers deferred until VPS (too heavy for Pi)
- LLM-based similarity and file-based sessions used as placeholders locally
