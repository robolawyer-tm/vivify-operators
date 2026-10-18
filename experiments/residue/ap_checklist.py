#!/usr/bin/env python3
"""
ap_checklist.py — fixed-checklist recall: does each reading recover the eleven items?

Open-ended residue always finds 11-19 losses per case whatever the encoding
carries (tries 1-4), so its count cannot move. This scores against a FIXED list
instead: the eleven "how the account was made" items from the first residue run
(sutton-03/05, washington-03/05/07, cotton-04/05/09, brown-02/03/15).

For each case, one call gets that case's items and the blind readings of every arm,
shuffled and labelled R1..Rn, so the judge cannot tell which arm wrote which. For
each item and reading it answers yes (the reading recovers it), partly (recovers
the structure but not where or by whom), or no. yes = 1, partly = 0.5.

Arms compared: baseline, with_ap, with_ap_named, with_positions (no domain), and
baseline_domain, positions_domain (both told "criminal case"). Writes
rerun/checklist.json (snapshot).

Usage:
    VIVIFY_RUN_TAG=ap_checklist python3 ap_checklist.py
"""

import sys
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE)]

import residue                       # sets PRIVACY_GATE off; public cases
from vivify_core import llm_call, extract_json, read_json, write_json

ARMS = ["baseline", "with_ap", "with_ap_named", "with_positions",
        "baseline_domain", "positions_domain"]
CHECKLIST = {"sutton": [3, 5], "washington": [3, 5, 7], "cotton": [4, 5, 9], "brown": [2, 3, 15]}
SCORE = {"yes": 1.0, "partly": 0.5, "no": 0.0}

PROMPT = """Below are FACTS from the record of one real case, and several READINGS. Each
reading was written blind, from abstract descriptors of the case, without the record.

For every fact and every reading, say whether the reading recovers the fact:
  yes    — the reading states this fact's mechanism and who did it, in substance
           (exact names, numbers and places are not needed)
  partly — the reading has the right kind of mechanism but places it with the wrong
           actor or setting, or states it only vaguely
  no     — the reading does not have it, or says something contrary

Judge each reading on its own. Return JSON only:
{"scores": {"<fact id>": {"<reading id>": "yes|partly|no", ...}, ...}}

FACTS:
%s

READINGS:
%s
"""


def main():
    rng = random.Random(20261018)
    out = {"by_case": {}, "totals": {a: 0.0 for a in ARMS}, "max_per_arm": 0}
    for case, nums in CHECKLIST.items():
        items = {it["id"]: it for it in read_json(HERE / f"{case}_residue.json")["items"]}
        facts = [items[f"{case}-{n:02d}"] for n in nums]
        arms = ARMS[:]
        rng.shuffle(arms)
        label = {arm: f"R{i}" for i, arm in enumerate(arms, 1)}
        readings = "\n\n".join(f"=== {label[a]} ===\n{(HERE / 'rerun' / a / f'{case}_reading.md').read_text().strip()}"
                               for a in arms)
        fact_text = "\n".join(f"[{f['id']}] {f['record']}" for f in facts)
        scores = extract_json(llm_call(PROMPT % (fact_text, readings),
                                       capability=residue.MODEL_CAPABILITY, sensitive=False))["scores"]
        by_arm = {}
        for a in ARMS:
            marks = {f["id"]: scores.get(f["id"], {}).get(label[a], "no") for f in facts}
            by_arm[a] = {"marks": marks, "score": sum(SCORE.get(m, 0.0) for m in marks.values())}
            out["totals"][a] += by_arm[a]["score"]
        out["by_case"][case] = {"labels": label, "arms": by_arm}
        out["max_per_arm"] += len(facts)
        print(f"{case:<11}" + "".join(f"{a}={by_arm[a]['score']:g} " for a in ARMS), flush=True)
    write_json(HERE / "rerun" / "checklist.json", out)
    print(f"\ntotal (of {out['max_per_arm']}): " + "  ".join(f"{a}={out['totals'][a]:g}" for a in ARMS))


if __name__ == "__main__":
    main()

# llm: claude-opus-5-5 | 2026-10-18 | repos/vivify-operators/experiments/residue/ap_checklist.py | created — fixed-checklist recall of the eleven production items against every arm's blind reading, arms shuffled and labelled per case, yes/partly/no
