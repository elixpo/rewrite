"""Post-processing pipeline — marker removal, burstiness injection, starter dedup."""

import re
import random

import nltk

try:
    nltk.data.find("tokenizers/punkt_tab")
except LookupError:
    nltk.download("punkt_tab", quiet=True)

from nltk.tokenize import sent_tokenize

# Expanded marker word substitutions
MARKER_REPLACEMENTS = {
    "delve": "explore",
    "crucial": "key",
    "moreover": "also",
    "furthermore": "and",
    "utilize": "use",
    "leveraging": "using",
    "comprehensive": "thorough",
    "facilitate": "help",
    "robust": "strong",
    "seamless": "smooth",
    "groundbreaking": "new",
    "paradigm": "model",
    "pivotal": "central",
    "intricate": "complex",
    "multifaceted": "varied",
    "endeavor": "effort",
    "streamline": "simplify",
    "harness": "use",
    "foster": "encourage",
    "bolster": "support",
    "meticulous": "careful",
    "commendable": "impressive",
    "tapestry": "mix",
    "realm": "area",
    "embark": "start",
    "holistic": "overall",
    "synergy": "combination",
    "overarching": "broad",
    "underscores": "highlights",
    "underpin": "support",
    "testament": "proof",
    "navigating": "working through",
    "ever-evolving": "changing",
    "notably": "especially",
    "landscape": "field",
    "cutting-edge": "latest",
}

# Phrases to strip or replace
PHRASE_REPLACEMENTS = {
    "it is important to note": "note that",
    "it is worth noting": "worth noting:",
    "in today's world": "today",
    "in the realm of": "in",
    "plays a crucial role": "matters a lot",
    "a myriad of": "many",
    "shed light on": "clarify",
    "in light of": "given",
    "a testament to": "proof of",
    "serves as a": "is a",
    "it should be noted": "note that",
    "this is particularly": "this is especially",
}


def replace_markers(text: str) -> str:
    """Replace AI marker words with human alternatives."""
    result = text

    # Replace phrases first (longer matches)
    for old, new in PHRASE_REPLACEMENTS.items():
        pattern = re.compile(re.escape(old), re.IGNORECASE)
        result = pattern.sub(
            lambda m: new.capitalize() if m.group(0)[0].isupper() else new,
            result,
        )

    # Replace single words
    for old, new in MARKER_REPLACEMENTS.items():
        def _replace(match, replacement=new):
            word = match.group(0)
            if word[0].isupper():
                return replacement.capitalize()
            return replacement
        result = re.sub(rf"\b{re.escape(old)}\b", _replace, result, flags=re.IGNORECASE)

    return result


def inject_burstiness(text: str, target_cv: float = 0.5) -> str:
    """Adjust sentence lengths to increase burstiness if too uniform.

    Splits long uniform sequences and occasionally merges short sentences.
    """
    sentences = sent_tokenize(text)
    if len(sentences) < 4:
        return text

    lengths = [len(s.split()) for s in sentences]
    mean_len = sum(lengths) / len(lengths)
    if mean_len == 0:
        return text

    import math
    variance = sum((l - mean_len) ** 2 for l in lengths) / len(lengths)
    cv = math.sqrt(variance) / mean_len

    if cv >= target_cv:
        return text  # already bursty enough

    result = []
    i = 0
    while i < len(sentences):
        s = sentences[i]
        words = s.split()

        # Split long sentences (>25 words) at natural breakpoints
        if len(words) > 25 and random.random() < 0.4:
            mid = len(words) // 2
            # Find a comma or conjunction near the middle
            split_at = mid
            for j in range(max(mid - 5, 0), min(mid + 5, len(words))):
                if words[j].rstrip(",") in ("and", "but", "or", "which", "where", "while"):
                    split_at = j
                    break
                if words[j].endswith(","):
                    split_at = j + 1
                    break

            part1 = " ".join(words[:split_at]).rstrip(",")
            part2 = " ".join(words[split_at:])
            if part2 and not part2[0].isupper():
                part2 = part2[0].upper() + part2[1:]
            result.append(part1 + ".")
            result.append(part2)
        # Merge short consecutive sentences (<8 words each)
        elif (
            len(words) < 8
            and i + 1 < len(sentences)
            and len(sentences[i + 1].split()) < 8
            and random.random() < 0.3
        ):
            merged = s.rstrip(".!?") + " — " + sentences[i + 1]
            result.append(merged)
            i += 1
        else:
            result.append(s)
        i += 1

    return " ".join(result)


def deduplicate_starters(text: str) -> str:
    """Vary sentence starters if consecutive sentences begin with the same word."""
    sentences = sent_tokenize(text)
    if len(sentences) < 2:
        return text

    alternatives = {
        "the": ["This", "That", "A", "One"],
        "this": ["The", "That", "Such a", "One"],
        "it": ["That", "The result", "What we see"],
        "there": ["We find", "One sees", "What exists"],
        "however": ["Still,", "Yet,", "But", "That said,"],
        "additionally": ["Also,", "On top of that,", "Plus,", "Beyond that,"],
        "furthermore": ["Also,", "And", "Plus,", "What's more,"],
        "moreover": ["Also,", "And", "On top of that,", "Plus,"],
    }

    result = [sentences[0]]
    for i in range(1, len(sentences)):
        current_start = sentences[i].strip().split()[0].lower() if sentences[i].strip() else ""
        prev_start = result[-1].strip().split()[0].lower() if result[-1].strip() else ""

        if current_start == prev_start and current_start in alternatives:
            alt = random.choice(alternatives[current_start])
            words = sentences[i].strip().split()
            words[0] = alt
            # Fix capitalization of second word if needed
            if len(words) > 1 and words[1][0].isupper() and current_start in ("however", "additionally", "furthermore", "moreover"):
                words[1] = words[1][0].lower() + words[1][1:]
            result.append(" ".join(words))
        else:
            result.append(sentences[i])

    return " ".join(result)


def postprocess(text: str) -> str:
    """Full post-processing pipeline."""
    text = replace_markers(text)
    text = inject_burstiness(text)
    text = deduplicate_starters(text)
    return text
