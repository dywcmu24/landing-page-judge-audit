# Landing-Page Judge Audit

## What this project is

This is an EXPERIMENT, not a generator. It audits whether a single LLM judge
(Claude Sonnet 4.5) can distinguish "genuinely satisfied" from "looks satisfied
but isn't" acceptance criteria — and whether giving the judge grounded browser
observations (Playwright) closes that gap.

It is the follow-up to growth-copy-harness (project 1). In project 1 an
independent evaluator sub-agent judged copy quality. Here we put that very
evaluator under audit: an LLM judge is still a model judging another model's
output. We test whether grounding fixes its blind spots.

## The one manipulated variable

evidence grounding ONLY:
- static packet  = raw HTML + criterion text
- grounded packet = same, PLUS Playwright browser observations
Same judge, same prompt template, same temperature. NOT model family.
Cross-family (GPT-5, Gemini 2.5 Pro) is APPENDIX ONLY, 6 pairs, never main.

## Project structure (do not deviate)

- specs/feature_list.json : 6 acceptance criteria + ownership labels. Read-only spec.
- dataset_plan.md         : the 8 real-business base pages + mutation assignment.
- pages/clean/<base>/index.html   : clean version of each pair.
- pages/mutated/<base>/index.html : mutated version (surgical, one defect).
- generate_pair.py        : produces a clean page then a surgically mutated twin.
- check_pair.py           : gate — a pair differing by >~4 lines is rejected.
- verify.py               : Playwright structural sensor (from project 1).
- judge.py                : (to build) the Python judge — runs each
                            page x criterion x packet through the API, records
                            verdict + confidence + rationale.
- verdicts/               : one row per judgment, written by judge.py.
- analysis/               : McNemar test, ownership scissor plot, case cards.
- appendix/               : cross-family sanity check (GPT-5, Gemini), 6 pairs.

## Working agreement (each rule guards one failure mode)

# Failure mode: contaminated pairing
- A (clean, mutated) pair MUST differ by exactly one injected defect.
  check_pair.py gates every pair. Never hand-wave a noisy diff through.

# Failure mode: the manipulated variable creeping
- The ONLY thing that changes between the two packets is grounding.
  Do NOT also vary model, temperature, prompt wording, or criterion text.
  If you find yourself adding a judge or a criterion mid-run, STOP.

# Failure mode: p-hacking a null result
- feature_list.json records each criterion's static_expectation BEFORE any run.
  These are pre-registered. A null result (grounding doesn't help) is an
  ACCEPTED, publishable outcome. Do NOT retry mutations, swap judges, or add
  samples to chase a significant gap.

# Failure mode: judge non-reproducibility
- All main judgments go through judge.py via the Anthropic Python SDK with a
  fixed model string and fixed temperature, NOT through ad-hoc chat or the
  sub-agent. Every judgment must be reproducible from the script alone.

# Failure mode: pretending generated pages are real sites
- The 8 businesses are real Shadyside shops, but every page here is a
  HYPOTHETICAL page generated for this study. Never imply these are the
  businesses' actual websites.

## Tech constraints (stability over novelty)
- Plain static HTML + inline CSS for all pages. No frameworks, no build step.
- Main judge: claude-sonnet-4-5 via native Anthropic API. No OpenAI-compat layer.
- Cost: every script that calls the API carries a spend cap, like project 1.
