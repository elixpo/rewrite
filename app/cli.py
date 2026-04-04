"""CLI interface for ReWrite — AI Detector & Paraphraser."""

import argparse
import sys
import textwrap

from app.detector import detect
from app.paraphraser import paraphrase


COLORS = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "dim": "\033[2m",
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "cyan": "\033[96m",
    "magenta": "\033[95m",
}


def c(text, color):
    return f"{COLORS[color]}{text}{COLORS['reset']}"


def score_color(score):
    if score >= 65:
        return "red"
    if score >= 40:
        return "yellow"
    return "green"


def print_bar(label, value, width=30):
    """Print a colored progress bar."""
    filled = int(value / 100 * width)
    color = score_color(value)
    bar = c("█" * filled, color) + c("░" * (width - filled), "dim")
    print(f"  {label:<24} {bar} {c(f'{value}%', color)}")


def print_header(text):
    print(f"\n{c('─' * 50, 'dim')}")
    print(f"  {c(text, 'bold')}")
    print(c("─" * 50, "dim"))


def read_input(args_text=None):
    """Read text from argument, file, or stdin."""
    if args_text:
        return args_text

    if not sys.stdin.isatty():
        return sys.stdin.read()

    print(c("\nPaste your text below (press Ctrl+D or Ctrl+Z when done):\n", "dim"))
    lines = []
    try:
        while True:
            lines.append(input())
    except EOFError:
        pass
    return "\n".join(lines)


def cmd_detect(args):
    """Run the detector."""
    text = read_input(args.text)
    if not text or not text.strip():
        print(c("Error: No text provided.", "red"))
        return

    if len(text.strip()) < 50:
        print(c("Error: Text too short — need at least 50 characters.", "red"))
        return

    print_header("AI DETECTION ANALYSIS")
    result = detect(text)

    score = result["score"]
    color = score_color(score)

    print(f"\n  {'Overall Score:':<24} {c(f'{score}%', color)} {c('AI likelihood', 'dim')}")
    print(f"  {'Verdict:':<24} {c(result['verdict'], color)}\n")

    print(f"  {c('Feature Breakdown:', 'bold')}\n")
    labels = {
        "burstiness": "Burstiness",
        "vocabulary_markers": "AI Vocabulary",
        "type_token_ratio": "Lexical Diversity",
        "sentence_starters": "Sentence Starters",
        "paragraph_structure": "Paragraph Uniformity",
        "punctuation_diversity": "Punctuation Variety",
    }
    for key, value in result["features"].items():
        print_bar(labels.get(key, key), value)

    print()


def cmd_paraphrase(args):
    """Run the paraphraser."""
    text = read_input(args.text)
    if not text or not text.strip():
        print(c("Error: No text provided.", "red"))
        return

    intensity = args.intensity
    model = args.model

    print_header("PARAPHRASING")
    print(f"  Intensity: {c(intensity, 'cyan')}  |  Model: {c(model, 'cyan')}")
    print(f"  {c('Rewriting text... this may take a moment.', 'dim')}\n")

    result = paraphrase(text, intensity=intensity, model=model)

    before = result["original_score"]
    after = result["final_score"]

    print_header("RESULTS")
    print(f"\n  Score: {c(f'{before}%', score_color(before))} → {c(f'{after}%', score_color(after))}  ({result['attempts']} pass{'es' if result['attempts'] > 1 else ''})")
    print(f"  Verdict: {c(result['final_verdict'], score_color(after))}\n")

    print(f"  {c('Feature Breakdown:', 'bold')}\n")
    labels = {
        "burstiness": "Burstiness",
        "vocabulary_markers": "AI Vocabulary",
        "type_token_ratio": "Lexical Diversity",
        "sentence_starters": "Sentence Starters",
        "paragraph_structure": "Paragraph Uniformity",
        "punctuation_diversity": "Punctuation Variety",
    }
    for key, value in result["final_features"].items():
        print_bar(labels.get(key, key), value)

    print_header("REWRITTEN TEXT")
    print()
    # Wrap output nicely
    for paragraph in result["rewritten"].split("\n"):
        if paragraph.strip():
            wrapped = textwrap.fill(paragraph.strip(), width=78)
            print(f"  {wrapped}")
        else:
            print()
    print()

    # Offer to copy to file
    if args.output:
        with open(args.output, "w") as f:
            f.write(result["rewritten"])
        print(c(f"  Output saved to {args.output}", "green"))
        print()


def cmd_interactive(args):
    """Interactive mode — loop between detect and paraphrase."""
    print(c("\n  ReWrite — Interactive Mode", "bold"))
    print(c("  Type 'detect', 'rewrite', or 'quit'\n", "dim"))

    while True:
        try:
            cmd = input(c("rewrite> ", "magenta")).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if cmd in ("quit", "exit", "q"):
            break
        elif cmd in ("detect", "d", "scan"):
            print(c("  Paste text (Ctrl+D when done):", "dim"))
            lines = []
            try:
                while True:
                    lines.append(input())
            except EOFError:
                pass
            text = "\n".join(lines)
            if text.strip() and len(text.strip()) >= 50:
                args.text = text
                cmd_detect(args)
            else:
                print(c("  Need at least 50 characters.", "red"))
        elif cmd in ("rewrite", "r", "paraphrase", "p"):
            print(c("  Paste text (Ctrl+D when done):", "dim"))
            lines = []
            try:
                while True:
                    lines.append(input())
            except EOFError:
                pass
            text = "\n".join(lines)
            if text.strip():
                args.text = text
                args.intensity = input(c("  Intensity [light/medium/aggressive]: ", "dim")).strip() or "medium"
                cmd_paraphrase(args)
            else:
                print(c("  No text provided.", "red"))
        elif cmd == "help":
            print("  detect  — Analyze text for AI signals")
            print("  rewrite — Paraphrase text to bypass detection")
            print("  quit    — Exit")
        else:
            print(c("  Unknown command. Type 'help' for options.", "dim"))


def main():
    parser = argparse.ArgumentParser(
        prog="rewrite",
        description="ReWrite — AI Text Detector & Paraphraser",
    )
    sub = parser.add_subparsers(dest="command")

    # detect
    p_detect = sub.add_parser("detect", help="Analyze text for AI-generated content")
    p_detect.add_argument("text", nargs="?", help="Text to analyze (or pipe via stdin)")
    p_detect.set_defaults(func=cmd_detect)

    # paraphrase
    p_para = sub.add_parser("rewrite", help="Paraphrase text to bypass AI detection")
    p_para.add_argument("text", nargs="?", help="Text to rewrite (or pipe via stdin)")
    p_para.add_argument("-i", "--intensity", choices=["light", "medium", "aggressive"], default="medium")
    p_para.add_argument("-m", "--model", default="openai", help="Pollinations model ID")
    p_para.add_argument("-o", "--output", help="Save output to file")
    p_para.set_defaults(func=cmd_paraphrase)

    # interactive
    p_inter = sub.add_parser("interactive", help="Interactive mode")
    p_inter.set_defaults(func=cmd_interactive, text=None, intensity="medium", model="openai", output=None)

    args = parser.parse_args()
    if args.command is None:
        # Default to interactive
        args.text = None
        args.intensity = "medium"
        args.model = "openai"
        args.output = None
        cmd_interactive(args)
    else:
        args.func(args)


if __name__ == "__main__":
    main()
