# Landing-Page Judge Audit

A paired-mutation evaluation study of whether browser-grounded observations
(Playwright) improve an LLM judge's accuracy on landing-page acceptance
criteria. Same judge (Claude Sonnet 4.5), one manipulated variable:
**evidence grounding** (static packet = raw HTML; grounded packet = HTML +
Playwright observations). Pre-registered expectations, four pre-accepted
outcomes, n=144 judgments at temperature 0 with full reproducibility check.

**This project, at small scale, aims to:
design what to measure, isolate the manipulated variable, interpret what the
data says, and when anomalies appear, determine whether the cause is the
model, the harness, the data, or the criteria themselves.

Project 2 in a two-project sequence on eval-harness design, following
[`growth-copy-harness`](https://github.com/dywcmu24/growth-copy-harness).

---

## Headline finding

Grounding did not deliver the predicted net positive. In one of four cases
the judge **flipped from a correct FAIL to an incorrect PASS** when given
Playwright observations — and the judge's own rationale showed it had
re-interpreted the acceptance criterion more leniently in light of finer
signals. This is a reasoning-level finding, not a noise artifact: identical
verdicts reproduced across two independent runs.

| Base | Mutation | static | grounded |
|------|----------|--------|----------|
| 01 Kards | testimonial parent `height:0;overflow:hidden` | FAIL ✓ | FAIL ✓ |
| 03 Maser | roster `max-height:200px;overflow:hidden` | FAIL ✓ | FAIL ✓ |
| 07 Variety | press badge `transform:scale(0)` | FAIL ✓ | **PASS ✗** |
| 08 Idea | empty `<div class="credential">` blocks | FAIL ✓ | FAIL ✓ |

### The reverse case (verbatim model rationale)

**Static (FAIL, correct):** *"...the scaled-to-zero press badge violates
['actually VISIBLE'] for at least part of the trust content."*

**Grounded (PASS, incorrect):** *"...the testimonial section is actually
visible to normal visitors, while the press badge is correctly identified
as hidden..."*

With HTML alone, the judge applied a strict reading: *any* hidden trust
content = violation. With higher-resolution grounded signals, it applied
a permissive reading: *bulk* visible = satisfied. **The grounding didn't
just inform — it licensed a different interpretation of the criterion.**
Connects to Tian et al. 2025 (overconfidence under additional evidence)
and arXiv 2508.12358 (verification accuracy under heavier context).

---

## Four root-cause categories the study surfaced

Anthropic's evals JD asks engineers to "determine whether the cause is a
model change, harness, data, or infrastructure issue." I hit one of each:

1. **Model-level finding** — the reverse case above. Sonnet 4.5 re-reasons
   over criteria when given fine-grained evidence.
2. **Harness blind spots** — `ground.py` was upgraded four times mid-study.
   Each new mutation exposed a layer the tool was missing (ancestor-chain
   clipping, partial occlusion via multi-point sampling, horizontal
   off-viewport, low-contrast text). Grounding is a multi-dimensional
   resolution problem, not a boolean.
3. **Data-generation pathologies** — the LLM generator exhibited
   "semantic gravity": when asked to mutate a CTA into a position where a
   sticky header would occlude it, the generator repeatedly relocated the
   CTA *inside* the header (a natural design choice) rather than producing
   the intended bug. The mutation had to be reimplemented as a deterministic
   Python edit. Documented under `base-04` (excluded from main analysis).
4. **Criteria-coverage gap** — two base pairs had mutations grounding clearly
   observed (broken `<img src>`, dead `onclick`) but the six pre-registered
   criteria did not ask the judge to check for either pattern. Both judges
   returned PASS. **Designing what to measure is itself harness work, easy
   to underdo, invisible to accuracy metrics.**

---

## Experimental design

- **Dataset:** 8 hypothetical landing pages for real Shadyside small
  businesses, each a `(clean, mutated)` pair via surgical mutation
  (validated by per-base diff-budget gate). 4 used in main analysis.
- **6 acceptance criteria, 3 ownership classes** (mechanical / semantic /
  hybrid), each with a pre-registered expectation of whether grounding
  should help. This yields a *differential prediction* — flat on
  mechanical/semantic, gap on hybrid — and makes the result harder to
  p-hack than a binary "does grounding help."
- **Four outcomes accepted pre-collection:** main scissor / overconfidence
  bonus / null / reverse. Outcomes 3 and 4 were observed.

## Pipeline
generate_pair.py     two-call LLM surgical mutation

check_pair.py        per-base diff-budget gate

ground.py            Playwright observation pipeline (mobile viewport, 9-pt
occlusion sampling, ancestor-chain visibility, broken
image and empty container detection)

judge.py             the LLM judge under audit; captures verdict, confidence,
rationale across both packets

summarize_grounding.py            One-liner summary of `ground.py` output. 
Used to verify each mutation surfaces a Playwright-observable signal before spending API calls on judge.py.

collect_verdicts.py  pandas aggregation; false-pass rate restricted to each
base's target criterionAll judgments via the native Anthropic Python SDK with per-script spend caps.

## Limitations

n=4 is too small for paired statistical tests; results are descriptive,
anchored on verbatim rationale. Single judge (Sonnet 4.5); cross-family
replication is the natural next step. Generator-induced baseline noise on
mobile responsiveness. Two-of-eight attempted mutations excluded from main
analysis. Hypothetical pages, real businesses — no claim about these
businesses' actual websites.

*5-day sprint experiment, May 27 – June 1, 2026.*
