#!/usr/bin/env python3
"""Verdict matrix for the 4-pair main table.
4 base pairs × 2 packets × 1 target criterion each = 8 cells.
Each cell shows whether judge correctly caught the mutation (PASS=missed, FAIL=caught).
The base-07 cell is the reverse case: static caught, grounded missed."""
import json, matplotlib.pyplot as plt, matplotlib.patches as patches

BASE_TARGETS = {"base-01":"C4","base-03":"C5","base-07":"C4","base-08":"C5"}
BASE_LABELS = {
    "base-01": "Kards Unlimited\n(testimonial height:0)",
    "base-03": "Maser Galleries\n(roster max-height)",
    "base-07": "Shadyside Variety\n(transform:scale(0))",
    "base-08": "Idea Shops\n(empty credential divs)",
}

# Load verdicts and pick the target-criterion judgment for each (base, packet)
cells = {}  # (base, packet) -> verdict
for b in BASE_TARGETS:
    data = json.load(open(f"verdicts/{b}.json"))
    target = BASE_TARGETS[b]
    for r in data:
        if r['variant']=='mutated' and r['criterion']==target:
            cells[(b, r['packet'])] = r['verdict']

fig, ax = plt.subplots(figsize=(8, 5))
ax.set_xlim(0, 2); ax.set_ylim(0, 4)
ax.set_xticks([0.5, 1.5]); ax.set_xticklabels(['STATIC packet', 'GROUNDED packet'], fontsize=12)
ax.set_yticks([0.5, 1.5, 2.5, 3.5])
ax.set_yticklabels([BASE_LABELS[b] for b in reversed(list(BASE_TARGETS.keys()))], fontsize=10)
ax.set_title('Judge verdict on mutation-target criterion\n(FAIL = mutation caught = correct; PASS = false-pass)', fontsize=11)

for i, b in enumerate(reversed(list(BASE_TARGETS.keys()))):
    for j, pkt in enumerate(['static', 'grounded']):
        v = cells.get((b, pkt), '?')
        correct = (v == 'FAIL')  # mutation should trip the criterion
        color = '#a8d5a8' if correct else '#f4a8a8'  # green if caught, red if missed
        rect = patches.Rectangle((j, i), 1, 1, facecolor=color, edgecolor='black', linewidth=1)
        ax.add_patch(rect)
        ax.text(j+0.5, i+0.5, v, ha='center', va='center',
                fontsize=14, fontweight='bold')
        # mark the reverse cell
        if b == 'base-07' and pkt == 'grounded':
            ax.text(j+0.5, i+0.18, '★ reverse', ha='center', va='center',
                    fontsize=9, fontstyle='italic')

plt.tight_layout()
plt.savefig('analysis/verdict_matrix.png', dpi=150, bbox_inches='tight')
plt.savefig('analysis/verdict_matrix.svg', bbox_inches='tight')
print('wrote analysis/verdict_matrix.png and .svg')
