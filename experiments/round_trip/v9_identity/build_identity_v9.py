#!/usr/bin/env python3
"""
build_identity_v9.py — v8 with Brown's telling selected like the other three.

v8 failed 2/4; Brown's own reading was never picked, because his coordinates (global,
archival) came from the full, unselected NRE text and decoded as a state-to-state dispute.
v9 changes one thing: Brown is read from inf_539d6902, the NRE text cut by whole-sentence
selection to the Innocence Project tellings' level (CASE_TELLING_STANDARD.md,
~/private_field/field/tools/select_brown.py). Everything else is v8's builder.

(v8's notes follow.)
build_identity_v8.py — v7's four-case identity test, with the account values decoded alongside their definitions.

v7 failed 2/4: the decoder saw supplied_by = outside_party with no definition and wrote
"a contractor, a technical vendor, a laboratory", so both crime-lab records (Sutton,
Brown) matched Cotton's reading. account_production defines outside_party as a witness,
victim, informant or member of the public. v8 changes one thing: each account value is
passed as {"value", "means"}, the meaning quoted from account_production_operator.py.
Everything else is v7's builder unchanged.

v5 arm B showed two wrongful convictions told apart once the decoder input carried the
account the institution relied on (how it was made, who supplied it, who shaped it).
v7 asks the same of four cases at once, with every input read from the current
instrument: Sutton, Washington and Cotton (the longest of its three tellings) from the
field store, and Brown read fresh on 2026-10-26 from his full NRE record (kept in
~/private_field/field, out of the public repo).

- coordinates as in v3 (build_blind.coordinates), structural.transmission dropped as in
  v6 (it still describes the telling), plus the account values now stored in
  logos.account_production, named as in v5 arm B
- one blind decode per case; four random labels from F/G/H/L; padding to equal size;
  one key file (KEY.txt; do not open until every verdict is in)
- the hard pair: Washington and Brown are both 'manufactured'; they differ in who
  supplied the account (the target vs the institution)

Judge with ../judge.py (experiment v7): each record against all four readings.
Chance is 1 in 4 per record.

Usage:
    VIVIFY_RUN_TAG=blind_identity_v9 python3 build_identity_v9.py
"""

import os
import sys
import json
import secrets
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path[:0] = [str(REPO / "lib"), str(HERE.parent / "v3_washington"), str(HERE.parent)]
os.environ["PRIVACY_GATE"] = "off"           # public Innocence Project / NRE cases
from vivify_core import llm_call, read_json, write_json
from build_blind import coordinates          # the v2/v3 stripping, unchanged
from judge import CASES as JUDGE_CASES, EXPERIMENTS

CASES = {JUDGE_CASES[c][0]: JUDGE_CASES[c][2] for c in EXPERIMENTS["v9"]["records"]}
PROMPT = HERE.parent / "v2" / "decoder_prompt_v2.txt"
LABELS = EXPERIMENTS["v9"]["labels"]
DROP = [("logos", "structural", "transmission")]   # still describes the telling (v6)

# account_production_operator.py's own definitions, in its words
MEANS = {
    "how_it_was_made": {
        "unmarked": "the text shows nothing about how the account was made",
        "mistaken": "a sincere source gets it wrong: someone honestly reports what they believe they saw, "
                    "heard or remember, and errs; no one is shown shaping it",
        "inflated": "a real but weak element is stated as stronger than it is: a figure, an expert's claim, "
                    "or several weak pieces stacked into apparent certainty",
        "manufactured": "the institution's own agents build or alter the account: coaching or rehearsing a "
                        "statement, steering a witness or suspect, rewriting a report, claiming a step was "
                        "done that was not"},
    "supplied_by": {
        "outside_party": "someone outside the institution who is not its target: a witness, a victim, "
                         "an informant, a member of the public",
        "the_target": "the person or group the account is acted on against",
        "institution": "the institution's own staff, officials or experts",
        "none": "mode is unmarked"},
    "shaped_by": {
        "nobody": "it was relied on much as its supplier gave it",
        "institution": "the institution's own agents formed, steered or altered it",
        "none": "mode is unmarked"},
}


def defined(field, value):
    return {"value": value, "means": MEANS[field][value]}


def inputs():
    out = {}
    for case, path in CASES.items():
        inf = read_json(path)
        coords = coordinates(inf)
        for *parent, key in DROP:
            d = coords
            for p in parent:
                d = d[p]
            d.pop(key, None)
        ap = inf["logos"]["account_production"]
        coords["logos"]["account_the_institution_relied_on"] = {
            "how_it_was_made": defined("how_it_was_made", ap["mode"]),
            "supplied_by": defined("supplied_by", ap["supplied_by"]),
            "shaped_by": defined("shaped_by", ap["shaped_by"])}
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

# llm: claude-opus-5-5 | 2026-10-27 | repos/vivify-operators/experiments/round_trip/v9_identity/build_identity_v9.py | created from build_identity_v8.py — Brown read from the selected telling (record N); D/E/U/V labels
