#!/usr/bin/env python3
"""
build_identity_v6.py — the case-identity test, coordinates only, with the telling leaks closed.

v5 arm A (coordinates only) failed 2/4: every judge picked Sutton's reading on both
records. Two coordinates still described the Innocence Project page rather than the case:
logos.transmission (fixed in 17dbc09, the store now reads the events channel) and
structural.transmission, which still reads Washington as broadcast. structural is not
re-read, because a re-read would re-vote the unstable scale, so v6 drops
structural.transmission from the decoder input instead. No account values: this is
arm A again, with both leaks closed.

The prediction (2026-10-22): the readings come out near-identical, and judges split
instead of all picking Sutton's.

One pair of random X/Y labels, padding to equal size, one key file (KEY.txt; do not open
until every verdict is in). Judge with ../judge.py (experiment v6).

Usage:
    VIVIFY_RUN_TAG=blind_identity_v6 python3 build_identity_v6.py
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
PROMPT = HERE.parent / "v2" / "decoder_prompt_v2.txt"
LABELS = ("X", "Y")
DROP = [("logos", "structural", "transmission")]   # still describes the telling, see above


def inputs():
    out = {}
    for case, path in CASES.items():
        coords = coordinates(read_json(path))
        for *parent, key in DROP:
            d = coords
            for p in parent:
                d = d[p]
            d.pop(key, None)
        out[case] = coords
    return out


def main():
    prompt = PROMPT.read_text()
    regen = {}
    for case, coords in inputs().items():
        write_json(HERE / f"input_{case}.json", coords)
        regen[case] = llm_call(prompt + "\n" + json.dumps(coords, indent=2),
                               capability="prose_reconstruction", sensitive=False).strip() + "\n"
        (HERE / f"regen_{case}.md").write_text(regen[case])
        print(f"regen_{case}.md: {len(regen[case].encode())} bytes", flush=True)
    first = secrets.choice(sorted(CASES))
    order = {LABELS[0]: first, LABELS[1]: next(c for c in CASES if c != first)}
    size = max(len(t.encode()) for t in regen.values())
    for label, case in order.items():
        text = regen[case]
        (HERE / f"reading_{label}.md").write_text(text + "\n" * (size - len(text.encode())))
    (HERE / "KEY.txt").write_text(" ".join(f"{l} = {c}" for l, c in order.items()) + "\n")
    print(f"reading_X.md / reading_Y.md {size} bytes each; key in KEY.txt (not shown)")


if __name__ == "__main__":
    main()

# llm: claude-opus-5-5 | 2026-10-24 | repos/vivify-operators/experiments/round_trip/v6_identity/build_identity_v6.py | created — case-identity, coordinates only, from the current store (logos.transmission now the events level), structural.transmission dropped from the decoder input; X/Y labels, padding, one key
