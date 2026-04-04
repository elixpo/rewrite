"""Central configuration — loads from .env and provides defaults."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root
_env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(_env_path)


# --- API ---
POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY", "")
POLLINATIONS_BASE_URL = "https://gen.pollinations.ai/v1"
DEFAULT_MODEL = "kimi"

# --- LLM ---
LLM_TIMEOUT = 60
LLM_MAX_RETRIES = 3
LLM_RETRY_BASE_DELAY = 1.0  # seconds, exponential backoff

# --- Redis ---
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
SESSION_TTL = 3600  # 1 hour

# --- Embeddings ---
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384
SIMILARITY_THRESHOLD = 0.85

# --- Detection thresholds ---
SCORE_GREEN = 20
SCORE_YELLOW = 60
SCORE_RED = 60  # above this = red

# --- Ensemble weights (with LLM judge) ---
ENSEMBLE_WEIGHTS = {
    "llm_judge": 0.35,
    "burstiness": 0.20,
    "vocabulary_markers": 0.15,
    "type_token_ratio": 0.10,
    "sentence_starters": 0.10,
    "paragraph_structure": 0.05,
    "punctuation_diversity": 0.05,
}

# --- Fallback weights (heuristics only, when LLM judge unavailable) ---
HEURISTIC_WEIGHTS = {
    "burstiness": 0.22,
    "vocabulary_markers": 0.25,
    "type_token_ratio": 0.15,
    "sentence_starters": 0.15,
    "paragraph_structure": 0.10,
    "punctuation_diversity": 0.13,
}

# --- Paraphrase ---
PARAPHRASE_TARGET_SCORE = 20  # rewrite segments above this
PARAPHRASE_MAX_RETRIES = 3
PARAPHRASE_INTENSITIES = {
    "light": 0.8,
    "medium": 1.0,
    "aggressive": 1.2,
}

# --- Segmentation ---
SEGMENT_TARGET_WORDS = 150
