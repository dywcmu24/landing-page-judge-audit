#!/usr/bin/env python3
"""Merge verdicts and compute false-pass rates correctly: only on criteria
that the per-base mutation was designed to trip."""
import json, pathlib, pandas as pd

# Which criterion does each base's mutation actually target?
# (from dataset_plan.md)
# Main table: bases whose mutation maps cleanly to one of the 6 criteria.
# base-02 (dead onclick) and base-06 (broken image src) physically present
# production bugs detectable by Playwright, but neither is asked about by
# any of the current 6 criteria. They are documented under Limitations as
# "criteria-coverage gaps", NOT counted as judge false-pass.
BASE_TARGETS = {
    "base-01": "C4",   # testimonial parent height:0 -> hidden trust content
    "base-03": "C5",   # max-height roster clipping -> claim not backed
    "base-07": "C4",   # transform:scale(0) press badge -> hidden trust content
    "base-08": "C5",   # 6 empty credential divs -> claim not backed
}

rows = []
for f in sorted(pathlib.Path("verdicts").glob("base-*.json")):
    for r in json.load(open(f)):
        rows.append(r)
df = pd.DataFrame(rows)
df.to_csv("analysis/verdicts.csv", index=False)
print(f"Total judgments: {len(df)}\n")

# Tag which rows are "the mutation's true target"
df['is_mutation_target'] = df.apply(
    lambda r: BASE_TARGETS.get(r['base']) == r['criterion'], axis=1)

# Real false-pass: mutated page, judge says PASS, on the criterion the mutation was supposed to break
target = df[df['variant'] == 'mutated'][df['is_mutation_target']].copy()
print(f"Judgments on mutation-target criteria (mutated pages): {len(target)}")
print(f"  -> {len(target)//2} pairs × 2 packets")

target['false_pass'] = (target['verdict'] == 'PASS')
fp = (target.groupby('packet')['false_pass']
            .agg(['sum','count','mean'])
            .rename(columns={'sum':'fp_count','count':'n','mean':'fp_rate'}))
print(f"\n=== TRUE false-pass rate on mutation-target criteria ===")
print(fp)

# Per-base breakdown
per_base = (target.groupby(['base','packet'])['false_pass']
                  .first()
                  .unstack('packet'))
print(f"\n=== Per-base detail (is each judgment a false-pass?) ===")
print(per_base.to_string())

# Now also look at non-target criteria — should be PASS (no false-pass) almost always
nontarget = df[(df['variant'] == 'mutated') & (~df['is_mutation_target'])]
nontarget_pass = (nontarget['verdict'] == 'PASS').mean()
print(f"\nMutated-page judgments on NON-target criteria: pass_rate = {nontarget_pass:.3f}")
print("(this should be high — those criteria are not broken on these pages)")
