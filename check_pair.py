#!/usr/bin/env python3
"""Sanity check: a clean/mutated pair should differ by only a few lines."""
import sys, difflib, pathlib

base_id = sys.argv[1] if len(sys.argv) > 1 else "base-01"
clean = pathlib.Path(f"pages/clean/{base_id}/index.html").read_text(encoding="utf-8")
mutated = pathlib.Path(f"pages/mutated/{base_id}/index.html").read_text(encoding="utf-8")

clean_lines = clean.splitlines()
mutated_lines = mutated.splitlines()
diff = list(difflib.unified_diff(clean_lines, mutated_lines, lineterm=""))

# count changed lines (ignore the +++/---/@@ headers)
changed = [l for l in diff if (l.startswith("+") or l.startswith("-"))
           and not l.startswith("+++") and not l.startswith("---")]

print(f"=== {base_id} ===")
print(f"clean: {len(clean_lines)} lines | mutated: {len(mutated_lines)} lines")
print(f"changed lines: {len(changed)}")
for l in changed:
    print("  " + l)

if len(changed) <= 4:
    print("\n✅ CLEAN PAIR — differs by <=4 lines, pairing is valid.")
else:
    print("\n⚠️  CONTAMINATED — too many changed lines. Mutation leaked into other content.")
    print("    Re-run generate for this base, or fall back to Python surgical edit.")
