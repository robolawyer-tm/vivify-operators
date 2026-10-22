#!/usr/bin/env python3
"""
build_identity_v5.py — the case-identity test again, after the social_field fix.

v4 (2026-10-22) failed: every judge picked Sutton's reading on both records, because
Washington's social_field had scored the Innocence Project page's audience, not the
case. social_field now scores two levels, and the top level is the events. This
rebuilds the two inputs from the CURRENT store and decodes them blind, in two arms:

  A  coordinates only: what the social_field fix does on its own
  B  A plus the account the institution relied on: how it was made, who supplied it,
     who shaped it (account_production positions, from the residue run, named as in
     acceptance try 3 because a bare label was read as describing the text)

Each arm gets its own random J/K labels, its own padding, and its own key file
(KEY_A.txt, KEY_B.txt; do not open until every verdict is in). Judging is as in v4:
each record against the same pair, so a judge who picks the same reading for both
records is choosing on quality, not fit.

Usage:
    VIVIFY_RUN_TAG=blind_identity_v5 python3 build_identity_v5.py
"""

import os
import sys
import json
import secrets
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path[:0] = [str(REPO / "lib"), str(HERE.parent / "v3_washington")]
os.environ["PRIVACY_GATE"] = "off"           # public Innocence Project cases
from vivify_core import llm_call, read_json, write_json
from build_blind import coordinates          # the v2/v3 stripping, unchanged

CASES = {"sutton": REPO / "inferences" / "field" / "inf_285ae7ab.json",
         "washington": REPO / "inferences" / "field" / "inf_a3d99808.json"}
AP_RUN = REPO / "experiments" / "residue" / "account_production_run.json"
PROMPT = HERE.parent / "v2" / "decoder_prompt_v2.txt"
LABELS = ("J", "K")


def inputs(arm):
    ap = read_json(AP_RUN)
    out = {}
    for case, path in CASES.items():
        coords = coordinates(read_json(path))
        if arm == "B":
            rec = ap[case]
            coords["logos"]["account_the_institution_relied_on"] = {
                "how_it_was_made": rec["mode"], "supplied_by": rec["supplied_by"],
                "shaped_by": rec["shaped_by"]}
        out[case] = coords
    return out


def build(arm, prompt):
    arm_dir = HERE / f"arm_{arm}"
    arm_dir.mkdir(exist_ok=True)
    regen = {}
    for case, coords in inputs(arm).items():
        write_json(arm_dir / f"input_{case}.json", coords)
        regen[case] = llm_call(prompt + "\n" + json.dumps(coords, indent=2),
                               capability="prose_reconstruction", sensitive=False).strip() + "\n"
        (arm_dir / f"regen_{case}.md").write_text(regen[case])
        print(f"arm {arm} regen_{case}.md: {len(regen[case].encode())} bytes", flush=True)
    first = secrets.choice(sorted(CASES))
    order = {LABELS[0]: first, LABELS[1]: next(c for c in CASES if c != first)}
    size = max(len(t.encode()) for t in regen.values())
    for label, case in order.items():
        text = regen[case]
        (arm_dir / f"reading_{label}.md").write_text(text + "\n" * (size - len(text.encode())))
    (HERE / f"KEY_{arm}.txt").write_text(" ".join(f"{l} = {c}" for l, c in order.items()) + "\n")
    print(f"arm {arm}: reading_J.md / reading_K.md {size} bytes each; key in KEY_{arm}.txt (not shown)")


def main():
    prompt = PROMPT.read_text()
    for arm in ("A", "B"):
        build(arm, prompt)


if __name__ == "__main__":
    main()

# llm: claude-opus-5-5 | 2026-10-22 | repos/vivify-operators/experiments/round_trip/v5_identity/build_identity_v5.py | created — case-identity rerun after the two-level social_field fix: inputs from the current store, arm A coordinates only, arm B plus account_production positions (named), separate labels, padding and keys per arm
