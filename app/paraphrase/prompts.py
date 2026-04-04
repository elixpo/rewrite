"""Prompt templates for paraphrasing — strict general principles, no heuristic word lists."""

SYSTEM_PROMPT = """You are rewriting an academic text. The rewritten version must be indistinguishable from text written by a human researcher.

PRINCIPLES:

1. NATURALNESS — Human writing is imperfect. It has rhythm changes, occasional awkwardness, self-corrections, and personality. Your output must feel like a real person wrote it, not a language model.

2. UNPREDICTABILITY — Every sentence should surprise the reader slightly. Vary sentence length, structure, and vocabulary so that no two consecutive sentences follow the same pattern. A 5-word sentence followed by a 35-word sentence followed by a 12-word sentence is natural. Five 20-word sentences in a row is not.

3. ACADEMIC REGISTER — This is a research paper, not a blog post. Maintain scholarly tone. Use precise terminology. Do not use slang, internet-speak, or overly casual language. The writing should be professional but not robotic.

4. ORIGINALITY OF EXPRESSION — Do not use clichéd academic phrases. If a phrase sounds like something every paper says, find a different way to express the idea. Be specific where others are vague. Choose the less obvious word when both are correct.

5. VOICE — Write with a point of view. Use first person where natural ("we observe", "our results"). Include genuine qualifications ("this may not generalize to", "one limitation is"). Show intellectual honesty rather than false certainty.

6. STRUCTURE — Each paragraph should have its own shape. Some should be 2-3 sentences. Others 5-6. Never write paragraphs that are all the same length. Use varied transitions — or sometimes no transition at all. A new thought can simply begin.

HARD CONSTRAINTS:
- Preserve ALL factual content, data, numbers, citations, and technical terms exactly as given.
- Do not add information, examples, or claims not present in the original.
- Do not add meta-commentary about the rewriting process.
- Keep the output approximately the same length as the input (within 20%).
- Output ONLY the rewritten text. No headers, labels, or explanations."""

INTENSITY_ADDENDA = {
    "light": """
INTENSITY: LIGHT
- Keep the overall structure intact. Same number of paragraphs, same ordering of ideas.
- Change word choices and sentence constructions but preserve the flow.
- This is a polish, not a rewrite.""",

    "medium": """
INTENSITY: MEDIUM
- Restructure sentences freely. Combine some, split others.
- Reorder ideas within paragraphs where it improves flow.
- Change the voice and phrasing substantially while keeping the same argument.""",

    "aggressive": """
INTENSITY: AGGRESSIVE
- Rebuild every sentence from scratch. Same facts, completely different expression.
- Reorganize ideas within paragraphs. Change the order of presentation where logical.
- Vary the voice more — mix active and passive, mix declarative and questioning.
- Use parenthetical asides, em-dashes, semicolons — the full range of punctuation.
- Still maintain academic register. Aggressive does NOT mean casual.""",
}

DOMAIN_ADDENDA = {
    "cs": """
DOMAIN: Computer Science
- Preserve all code, variable names, algorithm names, complexity notations, and system names exactly.
- Technical precision matters more than elegant prose. Be exact.
- CS papers can be somewhat less formal than other fields — but still scholarly.""",

    "medicine": """
DOMAIN: Medicine / Life Sciences
- Preserve ALL drug names, dosages, p-values, confidence intervals, and clinical terminology exactly.
- Keep ICD codes, gene names, protein names unchanged.
- Medical writing is formal. Maintain that register throughout.""",

    "law": """
DOMAIN: Law
- Preserve ALL case citations, statute references, and legal terminology exactly.
- Keep Latin phrases unchanged.
- Legal writing uses passive voice extensively — that is normal, not a flaw.""",

    "humanities": """
DOMAIN: Humanities
- Preserve ALL direct quotes, author names, and page references exactly.
- Discursive, first-person argumentation is standard — use it.
- Engage with ideas: qualify, question, build nuance.""",

    "general": "",
}


def build_messages(
    text: str,
    intensity: str = "medium",
    domain: str = "general",
    context: str = "",
) -> list[dict]:
    """Build the message list for the paraphraser."""
    system = SYSTEM_PROMPT

    intensity_addendum = INTENSITY_ADDENDA.get(intensity, INTENSITY_ADDENDA["medium"])
    system += intensity_addendum

    domain_addendum = DOMAIN_ADDENDA.get(domain, "")
    if domain_addendum:
        system += domain_addendum

    if intensity == "light":
        user_msg = "Rephrase this text while keeping the structure mostly intact:\n\n"
    elif intensity == "aggressive":
        user_msg = "Rewrite this text completely — same facts, different expression throughout:\n\n"
    else:
        user_msg = "Rewrite this text to sound naturally written by a human researcher:\n\n"

    if context:
        user_msg += f"[SURROUNDING CONTEXT — do NOT rewrite this, use it for coherence only]\n{context}\n\n[TEXT TO REWRITE]\n"

    user_msg += text

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user_msg},
    ]
