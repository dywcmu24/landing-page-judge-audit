#!/usr/bin/env python3
"""
judge.py — the LLM judge under audit.
For one base pair, runs 6 criteria x 2 packets (static / grounded) through
Claude Sonnet 4.5 and records verdict + confidence + rationale.

Usage: python3 judge.py base-01
"""
import sys, json, subprocess, pathlib, re
from anthropic import Anthropic

MODEL = "claude-sonnet-4-5"
TEMP = 0.0
PRICE_IN, PRICE_OUT = 3.0/1e6, 15.0/1e6
SPEND_CAP = 5.0

base_id = sys.argv[1] if len(sys.argv) > 1 else "base-01"
criteria = json.load(open("specs/feature_list.json"))["criteria"]
client = Anthropic()
spent = 0.0

PROMPT = """You are a strict QA reviewer auditing a marketing landing page
against ONE acceptance criterion. Decide PASS or FAIL.

CRITERION ({cid}, ownership={own}):
{ctext}

{packet}

Reply with EXACTLY this format, nothing else:
VERDICT: PASS or FAIL
CONFIDENCE: an integer 0-100
REASON: one sentence."""

def make_packet(html, ground, grounded):
    p = f"--- PAGE HTML ---\n{html}\n--- END HTML ---"
    if grounded:
        p += ("\n\n--- BROWSER OBSERVATIONS (Playwright, rendered) ---\n"
              f"{json.dumps(ground, indent=2)}\n--- END OBSERVATIONS ---")
    return p

def ask(html, crit, ground, grounded):
    global spent
    if spent > SPEND_CAP:
        sys.exit("!! spend cap reached")
    prompt = PROMPT.format(cid=crit["id"], own=crit["ownership"],
                           ctext=crit["text"],
                           packet=make_packet(html, ground, grounded))
    msg = client.messages.create(model=MODEL, max_tokens=200, temperature=TEMP,
                                 messages=[{"role":"user","content":prompt}])
    spent += msg.usage.input_tokens*PRICE_IN + msg.usage.output_tokens*PRICE_OUT
    text = "".join(b.text for b in msg.content if hasattr(b,"text"))
    verdict = "PASS" if re.search(r"VERDICT:\s*PASS", text, re.I) else "FAIL"
    conf = re.search(r"CONFIDENCE:\s*(\d+)", text)
    return verdict, int(conf.group(1)) if conf else None, text.strip()

def ground_facts(page_path):
    out = subprocess.run(["python3","ground.py",page_path],
                         capture_output=True, text=True)
    return json.loads(out.stdout)

rows = []
for variant in ["clean", "mutated"]:
    page = f"pages/{variant}/{base_id}/index.html"
    html = pathlib.Path(page).read_text(encoding="utf-8")
    g = ground_facts(page)
    for crit in criteria:
        for grounded in [False, True]:
            v, c, raw = ask(html, crit, g, grounded)
            rows.append({"base":base_id,"variant":variant,"criterion":crit["id"],
                         "ownership":crit["ownership"],
                         "packet":"grounded" if grounded else "static",
                         "verdict":v,"confidence":c,
                         "rationale":raw})
            print(f"{variant:8} {crit['id']} {crit['ownership']:10} "
                  f"{'grounded' if grounded else 'static  '} -> {v} ({c})")

pathlib.Path("verdicts").mkdir(exist_ok=True)
json.dump(rows, open(f"verdicts/{base_id}.json","w"), indent=2)
print(f"\nspend ${spent:.4f} | wrote verdicts/{base_id}.json")

print("\n=== C4 scissor check (the money result) ===")
for r in rows:
    if r["criterion"]=="C4":
        print(f"  {r['variant']:8} {r['packet']:8} -> {r['verdict']} (conf {r['confidence']})")
