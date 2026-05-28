# Dataset Plan — Landing-Page Judge Audit

## What this experiment manipulates

**The one manipulated variable is evidence grounding: a static packet
(raw HTML + criterion) vs a grounded packet (same, plus Playwright
browser observations). NOT model family.** Main judge: Claude Sonnet 4.5.
Cross-family sanity check (GPT-5, Gemini 2.5 Pro): appendix only, 6 pairs.

## Base pages: 8 hypothetical landing pages for REAL Shadyside businesses

These are real small businesses on/near Walnut Street, Shadyside, Pittsburgh.
The landing pages are HYPOTHETICAL — generated for this study, NOT scraped
from any real site. No claim is made about these businesses' actual web presence.

| base | business | category | mutation class | injected defect |
|------|----------|----------|----------------|-----------------|
| base-01 | Kards Unlimited | gift / cards / books | 4 Hidden evidence | customer testimonial set to display:none |
| base-02 | Amazing Books & Records | used books + vinyl | 1 Visual affordance w/o behavior | "Browse by genre" accordion does not expand on click |
| base-03 | Maser Galleries | art gallery + framing | 3 Semantic claim w/o DOM backing | "See full artist roster below" but roster section is missing half the artists |
| base-04 | The Picket Fence | women/kids/home boutique | 6 CTA placement mismatch | "Visit us" CTA above fold on desktop, hidden behind sticky header on mobile |
| base-05 | Petagogy | pet food & supplies | 2 Trust signal w/o support | "Locally loved since 2010 - 2000+ happy pets" badge with no source or link |
| base-06 | Scribe | printing / stationery | 5 A11y / metadata mirage | portfolio images have empty alt; schema.org LocalBusiness missing address |
| base-07 | Shadyside Variety Store | toys / novelty gifts | 4 Hidden evidence | "As seen in Pittsburgh Magazine" press badge set to visibility:hidden |
| base-08 | The Idea Shops | home / garden / jewelry | 3 Semantic claim w/o DOM backing | "Certified premium-brand dealer - verify below" but no actual credential fields in DOM |

Coverage: all 6 mutation classes; classes 3 (Semantic) and 4 (Hidden)
each appear twice for robustness. Total: 8 pairs = 16 pages.

## Why these mutations are "production bugs," not adversarial probes

Each defect is placed where that business category would *naturally* surface it:
a gallery talks about its artist roster, a pet store leans on trust badges, a
toy store cites press. The defects mirror real QA-caught bugs (invisible content,
dead affordances, unsupported claims), not contrived attacks. The point is to
test whether an LLM judge catches the kind of thing a human QA reviewer catches.

## Pairing discipline

Each (clean, mutated) pair is produced by surgical mutation: generate clean HTML,
then apply EXACTLY ONE change to it. check_pair.py gates every pair — a pair with
more than ~4 changed lines is rejected and regenerated. This keeps the pair
differing by exactly one variable.

## Sample size

8 base pages x 6 acceptance criteria = 48 paired judgments per packet condition.
Paired (McNemar) design. Locked at 8 for Saturday hard-freeze; base-09/10 only
if Day 2 finishes with margin. Quality over quantity — buffer goes to validation,
not more pages.

## Ownership labels (the experiment's target)

Each acceptance criterion is labeled mechanical-owned / semantic-owned /
hybrid-owned. The 6 mutation classes are designed to trip HYBRID-owned criteria —
those that need BOTH semantic understanding AND physical/rendered backing.
(Detailed criterion-by-criterion ownership table: see feature_list.json.)
