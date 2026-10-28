#!/usr/bin/env python3
"""
bond_checklist.py — fixed-checklist recall for the bond candidate: does each arm's
blind reading recover the family-relationship items?

The account_production acceptance (ap_checklist.py) showed that an open residue count
cannot move, so this scores against a FIXED list: the residue items that two blind
topic sorts both put primarily under family relationships (topic_sort.py, 2026-10-26).

For each case, one call gets that case's items and every arm's blind reading, shuffled
and labelled R1..Rn, so the judge cannot tell which arm wrote which. yes = 1,
partly = 0.5, no = 0 (the ap_checklist prompt, unchanged).

Usage:
    python3 bond_checklist.py --items ~/private_field/family/residue \
        --arms ~/private_field/family/rerun/baseline_domain ~/private_field/family/rerun/bond_domain [--seed N]
        [--checklist FILE]   # {"<case>": [item numbers]}, for cases other than the first four
Writes checklist[_sN].json beside the arms' parent folder.
"""

import argparse
import random
from pathlib import Path

import residue                       # sets PRIVACY_GATE off
from ap_checklist import PROMPT, SCORE
from vivify_core import llm_call, extract_json, read_json, write_json

# Primary "relationships between family members" in both topic-sort draws (seeds 1, 2)
CHECKLIST = {"cm_v_mm": [6, 7, 8, 15], "ecs_v_mcs": [2, 8],
             "in_re_ejc": [3, 6, 9, 10], "ss_v_kf": [3, 6]}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--items", required=True, help="folder holding the original <case>_residue.json files")
    ap.add_argument("--arms", nargs="+", required=True, help="one folder per arm, each with <case>_reading.md")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--checklist", help="JSON {case: [item numbers]}; default the first four cases' list")
    args = ap.parse_args()
    items_dir = Path(args.items).expanduser()
    arm_dirs = {Path(a).expanduser().name: Path(a).expanduser() for a in args.arms}
    rng = random.Random(20261026 if args.seed is None else args.seed)
    checklist = read_json(Path(args.checklist).expanduser()) if args.checklist else CHECKLIST
    out = {"checklist": checklist, "by_case": {}, "totals": {a: 0.0 for a in arm_dirs}, "max_per_arm": 0}
    for case, nums in checklist.items():
        items = {it["id"]: it for it in read_json(items_dir / f"{case}_residue.json")["items"]}
        facts = [items[f"{case}-{n:02d}"] for n in nums]
        arms = list(arm_dirs)
        rng.shuffle(arms)
        label = {arm: f"R{i}" for i, arm in enumerate(arms, 1)}
        readings = "\n\n".join(f"=== {label[a]} ===\n{(arm_dirs[a] / f'{case}_reading.md').read_text().strip()}"
                               for a in arms)
        fact_text = "\n".join(f"[{f['id']}] {f['record']}" for f in facts)
        scores = extract_json(llm_call(PROMPT % (fact_text, readings),
                                       capability=residue.MODEL_CAPABILITY, sensitive=False))["scores"]
        by_arm = {}
        for a in arm_dirs:
            marks = {f["id"]: scores.get(f["id"], {}).get(label[a], "no") for f in facts}
            by_arm[a] = {"marks": marks, "score": sum(SCORE.get(m, 0.0) for m in marks.values())}
            out["totals"][a] += by_arm[a]["score"]
        out["by_case"][case] = {"labels": label, "arms": by_arm}
        out["max_per_arm"] += len(facts)
        print(f"{case:<10} " + "  ".join(f"{a}={by_arm[a]['score']:g}" for a in arm_dirs), flush=True)
    name = "checklist.json" if args.seed is None else f"checklist_s{args.seed}.json"
    write_json(next(iter(arm_dirs.values())).parent / name, out)
    print(f"\ntotal (of {out['max_per_arm']}): " + "  ".join(f"{a}={out['totals'][a]:g}" for a in arm_dirs))


if __name__ == "__main__":
    main()

# llm: claude-opus-5-5 | 2026-10-26 | repos/vivify-operators/experiments/residue/bond_checklist.py | created — fixed-checklist recall of the 12 family-relationship items per arm, shuffled and labelled, ap_checklist prompt reused
# llm: claude-opus-5-5 | 2026-10-27 | repos/vivify-operators/experiments/residue/bond_checklist.py | --checklist FILE, so unseen cases bring their own item list
