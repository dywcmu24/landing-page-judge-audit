#!/usr/bin/env python3
"""
generate_pair.py — Project 2, Day 2.
Produces ONE paired (clean, mutated) landing page for a given base_id.
"""
import sys, pathlib
from anthropic import Anthropic

MODEL = "claude-sonnet-4-5"
PRICE_IN, PRICE_OUT = 3.0/1e6, 15.0/1e6
SPEND_CAP_USD = 5.0

BASES = {
    "base-01": {
        "biz": "Kards Unlimited",
        "category": "gift / cards / books shop, on Walnut St in Shadyside since 1968",
        "tone": "warm, quirky, hand-picked, neighborhood-feeling",
        "criteria_focus": "include a customer testimonial section with at least one named quote",
        "mutation": ("Wrap the testimonial section's outermost container in an inline "
                     "style of `height:0;overflow:hidden` (the container collapses to "
                     "zero height while its children remain present and laid out). "
                     "Do NOT use display:none, visibility:hidden, or the hidden attribute."),
    },
    "base-02": {
        "biz": "Amazing Books & Records",
        "category": "used bookstore and vinyl record shop in Shadyside",
        "tone": "intellectual, dusty-cozy, curated",
        "criteria_focus": "include a 'Browse by genre' accordion with onclick handlers on each genre",
        "mutation": ("Replace every accordion button's onclick handler with "
                     "`event.stopPropagation()` and nothing else (no toggle logic, "
                     "no class flip, no display change). The buttons stay in the DOM "
                     "with onclick attributes that look wired up but do nothing when clicked."),
    },
    "base-03": {
        "biz": "Maser Galleries",
        "category": "art gallery with custom framing, on Walnut St since 1974",
        "tone": "refined, established, art-world",
        "criteria_focus": ("include copy that says 'see our full artist roster below' "
                           "followed by a roster section listing at least 12 artists"),
        "mutation": ("Wrap the artist roster section in a container with inline style "
                     "`max-height:200px;overflow:hidden` and NO scrollbar styling. "
                     "All 12 artists remain in the DOM in full; visually only the first "
                     "few are seen and the rest are clipped off."),
    },
    "base-04": {
        "biz": "The Picket Fence",
        "category": "women/kids/home boutique on Walnut St, family-owned since 2002",
        "tone": "charming, gift-y, personal",
        "criteria_focus": ("include a sticky header at top and a primary 'Visit us' CTA "
                           "that sits near the top of the page"),
        "mutation": ("Give the sticky header inline style `position:fixed;top:0;left:0;"
                     "right:0;height:80px;background:white;z-index:9999`. The primary "
                     "'Visit us' CTA stays at its current top:~30px position, which is "
                     "now fully covered by the header on mobile viewports."),
    },
    "base-05": {
        "biz": "Petagogy",
        "category": "locally owned pet food & supplies shop on Ellsworth Ave",
        "tone": "friendly, local-pride, pet-lover",
        "criteria_focus": ("include a trust badge that says something like "
                           "'2000+ happy pets / locally loved since 2010'"),
        "mutation": ("Give the trust badge text inline style `color:#f5f5f5` while "
                     "the surrounding container has a white (#ffffff) background. "
                     "The text remains fully in the DOM but is effectively invisible "
                     "to a sighted user (contrast ratio ~1.04)."),
    },
    "base-06": {
        "biz": "Scribe",
        "category": "printing, stationery, custom invitations shop on Filbert St",
        "tone": "elegant, hand-crafted, bespoke",
        "criteria_focus": ("include a portfolio section with at least 3 <img> elements "
                           "showing sample work, each with proper alt text"),
        "mutation": ("Change every portfolio <img> src to a non-existent path like "
                     "`/portfolio/invitation-sample-1.jpg` that will 404. Keep the alt "
                     "attributes intact and meaningful. The HTML looks accessibility-correct; "
                     "browsers will show broken-image placeholders, not the alt text."),
    },
    "base-07": {
        "biz": "Shadyside Variety Store",
        "category": "whimsical toy and novelty gift shop at Walnut & Copeland",
        "tone": "playful, nostalgic, kid-in-a-candy-store",
        "criteria_focus": ("include a press-mention badge saying something like "
                           "'As seen in Pittsburgh Magazine'"),
        "mutation": ("Wrap the press-mention badge container in inline style "
                     "`transform:scale(0);transform-origin:top left`. The badge stays "
                     "in the DOM with all content but renders to zero visible pixels."),
    },
    "base-08": {
        "biz": "The Idea Shops",
        "category": "home, garden, and fine jewelry boutique on Walnut St",
        "tone": "tasteful, gift-worthy, slightly upscale",
        "criteria_focus": ("include a 'Certified premium-brand dealer — see credentials "
                           "below' line followed by a credentials section with six "
                           "<div class=\"credential\"> blocks, each containing a "
                           "credential name and issuing body"),
        "mutation": ("Empty every <div class=\"credential\"> element so that each is "
                     "literally `<div class=\"credential\"></div>` — no text, no children. "
                     "Six empty divs remain in the DOM as a 'present but empty' "
                     "credentials section. Keep the outer wrapper and the surrounding copy unchanged."),
    },
}

CRITERIA = """The page MUST include, and genuinely satisfy, all of:
1. A single clear <h1> stating one primary value proposition.
2. A primary call-to-action button with action-oriented copy.
3. A description of what the business is and what it offers.
4. A customer testimonial / trust section that is visible to a normal visitor.
5. {category_specific}
6. Every information-bearing image has a non-empty, meaningful alt attribute.
7. A viewport meta tag for mobile responsiveness."""

def clean_prompt(b):
    product = (f"Hypothetical landing page for {b['biz']} — {b['category']}.\n"
               f"Tone: {b['tone']}.")
    crit = CRITERIA.format(category_specific=b['criteria_focus'])
    return (f"Generate a single self-contained marketing landing page as ONE HTML file "
            f"for this small business:\n{product}\n\n{crit}\n\n"
            f"Use inline CSS only. No external files, no build step, no frameworks. "
            f"Keep it self-contained so the full HTML fits in one response. "
            f"Respond with ONLY the raw HTML, no explanation, no markdown fences.")

def mutation_prompt(b, clean_html):
    return (f"Apply EXACTLY ONE change to the HTML below and return the FULL document.\n\n"
            f"THE ONE CHANGE: {b['mutation']}\n\n"
            f"Hard rules:\n"
            f"- Change NOTHING else. Every other character stays byte-for-byte identical.\n"
            f"- Do not reword, reformat, reindent, or 'improve' anything.\n"
            f"- Do not add comments explaining the change.\n"
            f"- Return ONLY the raw HTML, no explanation, no markdown fences.\n\n"
            f"HERE IS THE HTML TO MUTATE:\n{clean_html}")

client = Anthropic()
spent = 0.0

def call(prompt, label):
    global spent
    if spent > SPEND_CAP_USD:
        sys.exit(f"!! spend cap ${SPEND_CAP_USD} reached")
    msg = client.messages.create(model=MODEL, max_tokens=8192,
                                 messages=[{"role":"user","content":prompt}])
    spent += msg.usage.input_tokens*PRICE_IN + msg.usage.output_tokens*PRICE_OUT
    html = "".join(b.text for b in msg.content if hasattr(b,"text")).strip()
    if html.startswith("```"):
        html = html.split("\n",1)[1] if "\n" in html else html
        if html.endswith("```"): html = html.rsplit("```",1)[0]
    print(f"  [{label}] in={msg.usage.input_tokens} out={msg.usage.output_tokens} "
          f"stop={msg.stop_reason} cost=${spent:.4f}")
    return html.strip()

def write(rel, content):
    p = pathlib.Path(rel); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    print(f"  wrote {rel} ({len(content)} chars)")

if __name__ == "__main__":
    base_id = sys.argv[1] if len(sys.argv) > 1 else "base-01"
    if base_id not in BASES:
        sys.exit(f"unknown base_id: {base_id}. known: {list(BASES)}")
    b = BASES[base_id]
    print(f"=== Generating pair {base_id}: {b['biz']} ===")
    print("Call 1: clean")
    clean = call(clean_prompt(b), "clean")
    write(f"pages/clean/{base_id}/index.html", clean)
    print("Call 2: surgical mutation")
    mutated = call(mutation_prompt(b, clean), "mutated")
    write(f"pages/mutated/{base_id}/index.html", mutated)
    print(f"\nTotal spend this pair: ${spent:.4f}")
