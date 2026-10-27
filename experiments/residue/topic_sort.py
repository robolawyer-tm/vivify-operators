#!/usr/bin/env python3
"""
topic_sort.py — sort residue items into plain topics, blind to which topic is under test.

A candidate's demand is the share of residue items about its subject. Picking those
items by eye is the experimenter's judgement; this hands it to a judge that sees six
topics, one of which is the candidate's, so it cannot tell which one matters.

- Input: the <case>_residue.json files in --dir (from residue.py); items shuffled with
  --seed, case names hidden behind their item ids' position only
- Each item gets every topic that applies, and one primary topic
- Output: topic_sort.json in --dir (labels per item, counts per topic, per case)

Usage:
    python3 topic_sort.py --dir ~/private_field/family/residue [--seed 1]
"""

import os
import sys
import json
import random
import argparse
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent.parent / "lib")]
os.environ["PRIVACY_GATE"] = "off"           # published, anonymised court opinions
from vivify_core import llm_call, extract_json, read_json, write_json

TOPICS = {
    "A": "the act or institution itself: what kind of act it is, who issues it, by what authority",
    "B": "procedure and law: review between courts, rules, legal categories, arguments, results",
    "C": "money and resources: costs, means, payments, economic pressure",
    "D": "relationships between family members: their state, history, contact, separation, "
         "or what a decision does to them",
    "E": "a person's conduct or the harm done to a person",
    "F": "a person's voice: their wishes, preferences, or being heard",
}

PROMPT = """Below are short descriptions of information that was lost when court records were
summarised. Sort each one by topic.

TOPICS:
%s

For each item give every topic letter that applies, and the one primary letter that fits
best. Judge each item only by what it describes.

Return JSON only:
{"items": [{"n": <item number>, "topics": ["<letter>", ...], "primary": "<letter>"}]}

ITEMS:
%s
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--dir", required=True)
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()
    d = Path(args.dir).expanduser()
    items = []
    for f in sorted(d.glob("*_residue.json")):
        items += read_json(f).get("items", [])
    order = list(range(len(items)))
    random.Random(args.seed).shuffle(order)
    lines = "\n".join(f"[{k}] {items[i]['loss']} (record: {items[i]['record'][:300]})"
                      for k, i in enumerate(order, 1))
    topics = "\n".join(f"  {l} — {t}" for l, t in TOPICS.items())
    out = extract_json(llm_call(PROMPT % (topics, lines), capability="prose_reconstruction", sensitive=False))
    labels = {}
    for row in out.get("items", []):
        it = items[order[int(row["n"]) - 1]]
        labels[it["id"]] = {"topics": row.get("topics", []), "primary": row.get("primary")}
    counts = {l: sum(l in v["topics"] for v in labels.values()) for l in TOPICS}
    primary = {l: sum(v["primary"] == l for v in labels.values()) for l in TOPICS}
    by_case = {}
    for iid, v in labels.items():
        by_case.setdefault(iid.rsplit("-", 1)[0], []).append(iid) if "D" in v["topics"] else None
    write_json(d / "topic_sort.json", {"seed": args.seed, "topics": TOPICS, "n_items": len(items),
                                       "labelled": len(labels), "any": counts, "primary": primary,
                                       "labels": labels})
    print(f"{len(labels)}/{len(items)} items labelled (seed {args.seed})")
    for l, t in TOPICS.items():
        print(f"  {l} any {counts[l]:2d}  primary {primary[l]:2d}  {t[:60]}")
    for c, ids in sorted(by_case.items()):
        print(f"  D in {c}: {', '.join(sorted(ids))}")


if __name__ == "__main__":
    main()

# llm: claude-opus-5-5 | 2026-10-26 | repos/vivify-operators/experiments/residue/topic_sort.py | created — blind topic sort of residue items (six topics, candidate's hidden among them) to measure a candidate's demand without picking items by eye
