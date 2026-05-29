#!/usr/bin/env python3
"""Sanity check: a clean/mutated pair should differ by only the planned
mutation. Most mutations are single-point (<=4 line diff). A few are
intentionally multi-point (e.g. patching every accordion button or every
portfolio image src). The expected diff size is declared per base."""
import sys, difflib, pathlib

# Expected ceiling of (added + removed) diff lines per base.
# - Single-point mutations: <=4
# - Multi-point mutations (intentionally repeated): higher, justified below.
LIMITS = {
    "base-01": 4,      # 1 inline style on testimonial section
    "base-02": 16,     # ~6 accordion buttons * 2 lines each
    "base-03": 4,      # 1 inline style on roster container
    "base-04": 4,      # excluded from main analysis, see Limitations
    "base-05": 4,      # 1 inline style on trust badge
    "base-06": 16,     # ~6 portfolio images * 2 lines each
    "base-07": 4,      # 1 inline style on press badge
    "base-08": 40,     # destructive replace of 6 credential blocks; see README note
}

base_id = sys.argv[1] if len(sys.argv) > 1 else "base-01"
limit = LIMITS.get(base_id, 4)

clean = pathlib.Path(f"pages/clean/{base_id}/index.html").read_text(encoding="utf-8")
mutated = pathlib.Path(f"pages/mutated/{base_id}/index.html").read_text(encoding="utf-8")

clean_lines = clean.splitlines()
mutated_lines = mutated.splitlines()
diff = list(difflib.unified_diff(clean_lines, mutated_lines, lineterm=""))
changed = [l for l in diff if (l.startswith("+") or l.startswith("-"))
           and not l.startswith("+++") and not l.startswith("---")]

print(f"=== {base_id} ===")
print(f"clean: {len(clean_lines)} lines | mutated: {len(mutated_lines)} lines")
print(f"changed lines: {len(changed)} (ceiling for {base_id}: {limit})")

if len(changed) <= limit:
    print(f"\n✅ CLEAN PAIR — within expected diff budget for this mutation type.")
else:
    print(f"\n⚠️  CONTAMINATED — diff exceeds the budget for this base.")
    print(f"    Re-run generate for this base, or inspect manually.")
