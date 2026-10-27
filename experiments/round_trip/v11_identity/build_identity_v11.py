#!/usr/bin/env python3
"""
build_identity_v11.py — v10 with the decoder's concrete-picture instruction fenced.

v10 passed 3/4 for both judges; Brown was still missed because his steered-witness
element decoded as a coerced confession. Across v7-v10 every leak traced to one sentence
of v2/decoder_prompt_v2.txt: "Commit to the most plausible concrete picture the
coordinates support". v11 changes one thing: decoder_prompt_v11.txt replaces it with an
instruction to stay at the coordinates' level and say what is open. The inputs are v10's
input_<case>.json files, read unchanged (no re-coding), so only the prompt differs.

Judge with ../judge.py (experiment v11).

Usage:
    VIVIFY_RUN_TAG=blind_identity_v11 python3 build_identity_v11.py
"""

import os
import sys
import json
import secrets
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path[:0] = [str(REPO / "lib"), str(HERE.parent)]
os.environ["PRIVACY_GATE"] = "off"           # public Innocence Project / NRE cases
from vivify_core import llm_call, read_json
from judge import CASES as JUDGE_CASES, EXPERIMENTS

CASES = [JUDGE_CASES[c][0] for c in EXPERIMENTS["v11"]["records"]]
PROMPT = HERE / "decoder_prompt_v11.txt"
INPUTS = HERE.parent / "v10_identity"
LABELS = EXPERIMENTS["v11"]["labels"]


def main():
    prompt = PROMPT.read_text()
    regen = {}
    for case in CASES:
        coords = read_json(INPUTS / f"input_{case}.json")
        regen[case] = llm_call(prompt + "\n" + json.dumps(coords, indent=2),
                               capability="prose_reconstruction", sensitive=False).strip() + "\n"
        (HERE / f"regen_{case}.md").write_text(regen[case])
        print(f"regen_{case}.md: {len(regen[case].encode())} bytes", flush=True)
    cases = list(CASES)
    order = {}
    for label in LABELS:
        order[label] = cases.pop(secrets.randbelow(len(cases)))
    size = max(len(t.encode()) for t in regen.values())
    for label, case in order.items():
        text = regen[case]
        (HERE / f"reading_{label}.md").write_text(text + "\n" * (size - len(text.encode())))
    (HERE / "KEY.txt").write_text(" ".join(f"{l} = {c}" for l, c in order.items()) + "\n")
    print(f"reading_{'/'.join(LABELS)}.md {size} bytes each; key in KEY.txt (not shown)")


if __name__ == "__main__":
    main()

# llm: claude-opus-5-5 | 2026-10-27 | repos/vivify-operators/experiments/round_trip/v11_identity/build_identity_v11.py | created — v10's inputs decoded with the concrete-picture sentence fenced (decoder_prompt_v11.txt); B/G/J/Y labels
