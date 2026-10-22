#!/usr/bin/env python3
"""
build_identity.py — can the coordinates tell two wrongful convictions apart?

Rounds two and three asked real against shuffled, a coarse contrast: the shuffled
input lands far from any criminal case. This asks the finer question. Two REAL
encodings of two cases of the same broad kind (Sutton, Washington) are decoded blind
with the v2 decoder prompt. The two readings get the labels J and K at random. A
judge then sees ONE case record and both readings, and picks the reading written
from that case's own descriptors.

Each record is judged against the same pair: Washington's record and Sutton's record.
If the coordinates carry case identity, the pick switches with the record. If a
judge picks the same reading for both, it is choosing the better reading in
general, not the one that fits.

Inputs are the stripped real inputs from v2 (Sutton) and v3 (Washington), unchanged.
Both are decoded fresh, because the earlier readings are public in the repo.

Usage:
    VIVIFY_RUN_TAG=blind_identity python3 build_identity.py
Writes regen_<case>.md, reading_J.md, reading_K.md (padded to equal size), KEY.txt
(do not open until every verdict is in).
"""

import os
import sys
import secrets
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "lib"))
os.environ["PRIVACY_GATE"] = "off"           # public Innocence Project cases
from vivify_core import llm_call

ROUND_TRIP = HERE.parent
INPUTS = {"sutton": ROUND_TRIP / "v2" / "input_real.json",
          "washington": ROUND_TRIP / "v3_washington" / "input_real.json"}
PROMPT = ROUND_TRIP / "v2" / "decoder_prompt_v2.txt"
LABELS = ("J", "K")


def main():
    prompt = PROMPT.read_text()
    regen = {}
    for case, path in INPUTS.items():
        regen[case] = llm_call(prompt + "\n" + path.read_text().strip(),
                               capability="prose_reconstruction", sensitive=False).strip() + "\n"
        (HERE / f"regen_{case}.md").write_text(regen[case])
        print(f"regen_{case}.md: {len(regen[case].encode())} bytes", flush=True)

    first = secrets.choice(sorted(INPUTS))
    order = {LABELS[0]: first, LABELS[1]: next(c for c in INPUTS if c != first)}
    size = max(len(t.encode()) for t in regen.values())
    for label, case in order.items():
        text = regen[case]
        (HERE / f"reading_{label}.md").write_text(text + "\n" * (size - len(text.encode())))
    (HERE / "KEY.txt").write_text(" ".join(f"{l} = {c}" for l, c in order.items()) + "\n")
    print(f"reading_J.md / reading_K.md: {size} bytes each; key in KEY.txt (not shown)")


if __name__ == "__main__":
    main()

# llm: claude-opus-5-5 | 2026-10-22 | repos/vivify-operators/experiments/round_trip/v4_identity/build_identity.py | created — case-identity blind test: fresh blind decodes of Sutton's and Washington's real inputs, random J/K labels, equal padding, hidden key; each record is judged against the same pair
