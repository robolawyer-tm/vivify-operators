#!/usr/bin/env python3
"""
ap_acceptance.py — did adding account_production remove the loss it was built for?

Two residue re-runs, same code, same day: rerun/baseline (the coordinates as
before) and rerun/with_ap (plus logos.account_production.mode). The items of both
arms are pooled, shuffled, and given neutral ids, so the judge cannot tell which
arm an item came from; one call then marks each item:

  production — the loss is about HOW the account the institution relied on was
               made (who supplied it, how it was shaped, inflated or altered)
  other      — anything else

The acceptance bar (sketch, candidate_account_production.md): production items
fall in the with_ap arm, other items do not. Writes rerun/acceptance_<arms>.json.

Usage:
    python3 ap_acceptance.py                               # baseline vs with_ap
    python3 ap_acceptance.py baseline with_ap with_ap_named  # any arms, judged in one call
"""

import sys
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE)]

import residue                       # sets PRIVACY_GATE off; public cases
from vivify_core import llm_call, extract_json, read_json, write_json

ARMS = sys.argv[1:] or ["baseline", "with_ap"]

JUDGE_PROMPT = """Below are losses found when real cases were reduced to abstract descriptors
and rebuilt blind. Each loss says what the original record held that the rebuilt
reading missed.

Mark each loss:
  production — it is about HOW the account of events that the institution relied on
               was made: who supplied it, how it was shaped, coached, inflated,
               altered, or how a sincere source came to err.
  other      — anything else (what happened afterwards, who reopened the case, how
               the institution responded, who the people were, particulars, ...).

Return JSON only: {"marks": {"<id>": "production|other", ...}}

LOSSES:
%s
"""


def main():
    pool = []
    for arm in ARMS:
        for f in sorted((HERE / "rerun" / arm).glob("*_residue.json")):
            case = f.name.split("_")[0]
            for it in read_json(f).get("items", []):
                pool.append({"arm": arm, "case": case, "item": it})
    random.Random(20261017).shuffle(pool)
    for i, p in enumerate(pool, 1):
        p["blind_id"] = f"L{i:03d}"
    losses = "\n".join(f"[{p['blind_id']}] {p['item']['loss']} (record: {p['item']['record']})"
                       for p in pool)
    marks = extract_json(llm_call(JUDGE_PROMPT % losses,
                                  capability=residue.MODEL_CAPABILITY, sensitive=False))["marks"]

    table = {}
    for p in pool:
        mark = marks.get(p["blind_id"], "unmarked")
        cell = table.setdefault(p["case"], {}).setdefault(p["arm"], {"items": 0, "production": 0, "ids": []})
        cell["items"] += 1
        if mark == "production":
            cell["production"] += 1
            cell["ids"].append(p["item"]["id"])
    write_json(HERE / "rerun" / f"acceptance_{'_'.join(ARMS)}.json",
               {"marks": {p["blind_id"]: {"arm": p["arm"], "id": p["item"]["id"],
                                          "mark": marks.get(p["blind_id"])} for p in pool},
                "table": table})
    print(f"{'case':<12}" + "".join(f"{a + ' prod/items':>22}" for a in ARMS))
    for case in residue.CASES:
        row = table.get(case, {})
        print(f"{case:<12}" + "".join(
            f"{row.get(a, {}).get('production', 0):>14}/{row.get(a, {}).get('items', 0):<7}" for a in ARMS))


if __name__ == "__main__":
    main()

# llm: claude-opus-5-5 | 2026-10-17 | repos/vivify-operators/experiments/residue/ap_acceptance.py | created — blind acceptance check: pooled, shuffled residue items from baseline and with_ap arms, one judge call marks production vs other, counts per case and arm
# llm: claude-opus-5-5 | 2026-10-17 | repos/vivify-operators/experiments/residue/ap_acceptance.py | arms from the command line, all judged in one blind call; output named by arms
