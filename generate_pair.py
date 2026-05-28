#!/usr/bin/env python3
"""
generate_pair.py  —  Project 2
Produces ONE paired (clean, mutated) landing page.

Design:
  call 1: brief -> clean HTML (satisfies all acceptance criteria)
  call 2: clean HTML + ONE surgical mutation instruction -> mutated HTML
          (everything else copied verbatim, so the pair differs by exactly
           one variable — the mutation)

Mutation type for this first pair: Hidden / offscreen evidence
  (testimonial exists in DOM but display:none -> invisible when rendered)
"""

import sys, pathlib
from anthropic import Anthropic

MODEL = "claude-sonnet-4-5"
PRICE_IN  = 3.0  / 1_000_000
PRICE_OUT = 15.0 / 1_000_000
SPEND_CAP_USD = 5.0
BASE_ID = "base-01"

PRODUCT = """Product: "Stacksift" — an error-monitoring and log-analysis tool
for backend engineering teams. It groups noisy production errors into a small
number of root-cause clusters, links each cluster to the exact deploy that
introduced it, and alerts the on-call engineer in Slack.
Audience: engineering managers and senior backend engineers at 50-500 person
SaaS companies. Tone: precise, technical, no fluff."""

CRITERIA = """The page MUST include, and genuinely satisfy, all of:
1. A single clear <h1> stating one primary value proposition.
2. A primary call-to-action button with action-oriented copy, above the fold.
3. A features section with at least 3 concrete capabilities.
4. A customer TESTIMONIAL section with at least one named quote that is
   VISIBLE to a normal visitor (not hidden, not collapsed).
5. A pricing section with at least two named tiers and visible prices.
6. Every information-bearing image has a non-empty, meaningful alt attribute.
7. A viewport meta tag for mobile responsiveness."""

CLEAN_PROMPT = f"""Generate a single self-contained marketing landing page as ONE HTML file
for this product:
{PRODUCT}

{CRITERIA}

Use inline CSS only. No external files, no build step, no JavaScript frameworks.
Keep it self-contained so the full HTML fits in one response.
Respond with ONLY the raw HTML, no explanation, no markdown fences."""

MUTATION_INSTRUCTION = """Apply EXACTLY ONE change to the HTML below and return the FULL document.

THE ONE CHANGE: take the existing testimonial section (the customer quote block)
and add `display:none` to its outermost container's inline style, so the
testimonial is present in the DOM but NOT rendered to a visitor.

Hard rules:
- Change NOTHING else. Every other character, attribute, and line stays byte-for-byte identical.
- Do not reword, reformat, reindent, or "improve" anything.
- Do not add comments explaining the change.
- Return ONLY the raw HTML, no explanation, no markdown fences.

HERE IS THE HTML TO MUTATE:
"""

client = Anthropic()
spent = 0.0

def call(prompt, label):
    global spent
    if spent > SPEND_CAP_USD:
        sys.exit(f"!! Spend cap ${SPEND_CAP_USD} reached. Stopping before {label}.")
    msg = client.messages.create(
        model=MODEL, max_tokens=8192,
        messages=[{"role": "user", "content": prompt}],
    )
    cost = msg.usage.input_tokens * PRICE_IN + msg.usage.output_tokens * PRICE_OUT
    spent += cost
    html = "".join(b.text for b in msg.content if hasattr(b, "text"))
    html = html.strip()
    if html.startswith("```"):
        html = html.split("\n", 1)[1] if "\n" in html else html
        if html.endswith("```"):
            html = html.rsplit("```", 1)[0]
    print(f"  [{label}] in={msg.usage.input_tokens} out={msg.usage.output_tokens} "
          f"stop={msg.stop_reason} running_cost=${spent:.4f}")
    return html.strip()

def write(rel_path, content):
    p = pathlib.Path(rel_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    print(f"  wrote {rel_path} ({len(content)} chars)")

if __name__ == "__main__":
    print(f"=== Generating pair {BASE_ID} ===")
    print("Call 1: clean version")
    clean_html = call(CLEAN_PROMPT, "clean")
    write(f"pages/clean/{BASE_ID}/index.html", clean_html)

    print("Call 2: surgical mutation (testimonial display:none)")
    mutated_html = call(MUTATION_INSTRUCTION + clean_html, "mutated")
    write(f"pages/mutated/{BASE_ID}/index.html", mutated_html)

    print(f"\nDone. Total spend: ${spent:.4f}")
    print("Next: diff the two files — they should differ by only the mutation.")
