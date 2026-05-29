#!/usr/bin/env python3
"""Summarize ground.py output for one mutated page in one line per signal.
Uses sys.executable + explicit anaconda PATH to ensure subprocess uses the
same python that imports playwright correctly."""
import sys, os, json, subprocess, pathlib

base_id = sys.argv[1]
page = f"pages/mutated/{base_id}/index.html"
if not pathlib.Path(page).exists():
    sys.exit(f"page not found: {page}")

# Force subprocess to use the same python interpreter AND prepend anaconda
# to PATH so child shell utilities also resolve correctly.
env = os.environ.copy()
env["PATH"] = "/Users/danyangw/opt/anaconda3/bin:" + env.get("PATH", "")
result = subprocess.run([sys.executable, "ground.py", page],
                        capture_output=True, text=True, env=env)
if result.returncode != 0:
    print(f"  ground.py failed: {result.stderr.strip()[:200]}")
    sys.exit(1)

try:
    d = json.loads(result.stdout)
except json.JSONDecodeError as e:
    print(f"  could not parse ground.py output: {e}")
    print(f"  first 300 chars of output: {result.stdout[:300]}")
    sys.exit(1)

print(f"=== {base_id} ===")

# C4 trust content
c4 = d.get('C4_trust_content', [])
if isinstance(c4, list):
    invisible = sum(1 for c in c4 if not c.get('user_visible', True))
    same_color = sum(1 for c in c4
                     if c.get('style', {}).get('color') == c.get('style', {}).get('background')
                     and c.get('style', {}).get('color'))
    print(f"  C4: {len(c4)} trust blocks | {invisible} user-invisible | {same_color} same-color text/bg")
else:
    print(f"  C4: (no blocks matched — {c4})")

# C5 affordance / claims
c5 = d.get('C5_affordance_and_claims', {})
dead = len(c5.get('dead_onclicks', []))
clipped = len(c5.get('max_height_clipped', []))
empty = len(c5.get('empty_structural_divs', []))
print(f"  C5: dead_onclicks={dead} | max_height_clipped={clipped} | empty_structural_divs={empty}")

# C6 CTA mobile
c6 = d.get('C6_cta_mobile', [])
if isinstance(c6, list):
    print(f"  C6: {len(c6)} CTAs found")
    for cta in c6[:3]:
        text = cta.get('text', '')[:30]
        top = cta.get('top', 0)
        off = cta.get('horizontally_off_viewport', False)
        occ = cta.get('occluded_points', 0)
        print(f"     '{text}' top={top:.0f} off_vp={off} occluded={occ}/9")
else:
    print(f"  C6: {c6}")

# broken images
bi = d.get('broken_images', [])
print(f"  broken_images: {len(bi)}")
