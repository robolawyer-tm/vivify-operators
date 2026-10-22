#!/usr/bin/env python3
"""
build_blind.py — the round-two blind round trip, rebuilt for a second case (Washington).

Same method as v2 (Sutton), written down this time so it can be rerun:
- input_real.json: the case's stored logos + conflict coordinates, values and
  confidences only. No rationales, signal lists, surface/underlying, sources,
  votes, _model/_src/_operator, or the *_drawn/*_agrees bookkeeping.
- input_shuffled.json: the same, with the 18 fields v2 swapped each replaced by a
  REAL value of that field taken from another stored inference (seeded). Marginals
  kept, joint structure destroyed. shuffled_swaps.txt lists every swap.
- Both inputs are decoded blind with v2's decoder prompt (no comment on the inputs).
- The two readings get the labels M and N at random (secrets), are padded with
  trailing newlines to equal size, and the key goes to KEY.txt. Do not open KEY.txt
  until every verdict is in.

Usage:
    VIVIFY_RUN_TAG=blind_washington python3 build_blind.py            # build and decode
    python3 build_blind.py --inputs-only                              # inputs + swaps, no LLM calls
"""

import os
import sys
import json
import random
import secrets
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "lib"))
os.environ["PRIVACY_GATE"] = "off"           # public Innocence Project case
from vivify_core import llm_call, read_json, write_json

CASE = REPO / "inferences" / "field" / "inf_a3d99808.json"     # Earl Washington Jr.
PROMPT = HERE.parent / "v2" / "decoder_prompt_v2.txt"
SEED = 20261022
LABELS = ("M", "N")

KEEP = {
    "act_type": ["value", "authority_mismatch", "confidence"],
    "cooperative": ["status", "maxim_violated", "confidence"],
    "transmission": ["value", "confidence"],
    "resonance": ["value", "confidence"],
    "authority": ["value", "confidence"],
    "utility": ["value", "secondary", "confidence"],
    "social_field": ["grid", "group", "quadrant", "confidence"],
    "structural": ["layer", "scale", "_coerced", "density", "persistence", "authority",
                   "transmission", "memory_channel", "language_mode", "overlays", "confidence"],
}
CONFLICT_KEEP = ["schema", "behavior", "terrain", "window", "escalation_phase", "confidence"]

# the fields v2 swapped (experiments/round_trip/shuffled_swaps.txt)
SWAP = [("logos", "transmission", "value"), ("logos", "resonance", "value"),
        ("logos", "authority", "value"), ("logos", "social_field", "grid"),
        ("logos", "social_field", "group"), ("logos", "social_field", "quadrant"),
        ("logos", "structural", "layer"), ("logos", "structural", "scale"),
        ("logos", "structural", "persistence"), ("logos", "structural", "authority"),
        ("logos", "structural", "transmission"), ("logos", "structural", "memory_channel"),
        ("logos", "structural", "language_mode"),
        ("conflict", "schema"), ("conflict", "behavior"), ("conflict", "terrain"),
        ("conflict", "window"), ("conflict", "escalation_phase")]


def coordinates(inf):
    logos = {op: {k: inf["logos"][op].get(k) for k in keys} for op, keys in KEEP.items()}
    return {"logos": logos, "conflict": {k: inf["conflict"].get(k) for k in CONFLICT_KEEP}}


def get(d, path):
    for p in path:
        if not isinstance(d, dict) or p not in d:
            return None
        d = d[p]
    return d


def shuffle(real, case_id):
    rng = random.Random(SEED)
    pool = []
    for f in sorted((REPO / "inferences").rglob("inf_*.json")):
        inf = read_json(f)
        if inf.get("id") != case_id and isinstance(inf.get("logos"), dict):
            pool.append(inf)
    out = json.loads(json.dumps(real))
    lines = []
    for path in SWAP:
        have = get(real, path)
        cands = sorted({(json.dumps(get(i, path)), i["id"]) for i in pool
                        if get(i, path) is not None and get(i, path) != have})
        if not cands:
            lines.append(f"{'.'.join(path)}: {have} kept (no other value in the store)")
            continue
        value, src = rng.choice(cands)
        node = out
        for p in path[:-1]:
            node = node[p]
        node[path[-1]] = json.loads(value)
        lines.append(f"{'.'.join(path)}: {have} -> {json.loads(value)}  ({src})")
    return out, lines, len(pool)


def main():
    inf = read_json(CASE)
    real = coordinates(inf)
    fake, swaps, n_pool = shuffle(real, inf["id"])
    write_json(HERE / "input_real.json", real)
    write_json(HERE / "input_shuffled.json", fake)
    (HERE / "shuffled_swaps.txt").write_text(
        f"# Permutation control, seed {SEED}, pool = {n_pool} other stored inferences.\n"
        f"# Every value below is a REAL value for that field, taken from a different inference.\n\n"
        + "\n".join(swaps) + "\n")
    print("\n".join(swaps))
    if "--inputs-only" in sys.argv:
        return

    prompt = PROMPT.read_text()
    regen = {}
    for name, coords in (("real", real), ("shuffled", fake)):
        regen[name] = llm_call(prompt + "\n" + json.dumps(coords, indent=2),
                               capability="prose_reconstruction", sensitive=False).strip() + "\n"
        (HERE / f"regen_{name}.md").write_text(regen[name])
        print(f"regen_{name}.md: {len(regen[name].encode())} bytes", flush=True)

    first = secrets.choice(["real", "shuffled"])
    order = {LABELS[0]: first, LABELS[1]: "shuffled" if first == "real" else "real"}
    size = max(len(t.encode()) for t in regen.values())
    for label, name in order.items():
        text = regen[name]
        (HERE / f"reading_{label}.md").write_text(text + "\n" * (size - len(text.encode())))
    (HERE / "KEY.txt").write_text(" ".join(f"{l} = {n}" for l, n in order.items()) + "\n")
    print(f"reading_{LABELS[0]}.md / reading_{LABELS[1]}.md: {size} bytes each; key in KEY.txt (not shown)")


if __name__ == "__main__":
    main()

# llm: claude-opus-5-5 | 2026-10-22 | repos/vivify-operators/experiments/round_trip/v3_washington/build_blind.py | created — v2 blind round-trip method as a rerunnable builder, for the Washington case: stripped inputs, seeded 18-field permutation from the store, v2 decoder prompt, random M/N labels, equal padding, hidden key
