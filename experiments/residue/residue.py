#!/usr/bin/env python3
"""
residue.py — what the coordinates cannot carry, read from the field, then matched.

The demand-pull test for new dimensions (project memory: dimension candidates).
Supply-push asks "where could this theory's distinction be used?"; this asks the
cases what the current coordinates drop, and only afterwards looks at the ten
candidates (C-01..C-10). It can return nothing: an item may match no candidate,
and a candidate may match no item.

Three steps per case, each one lean-worker call (vivify_core, no harness):
  1. DECODE  — coordinates only (no signals, rationales or text) -> a blind reading
               (the round-trip v2 decoder prompt)
  2. RESIDUE — case record + blind reading -> what the record holds that the reading
               missed or got wrong. Particulars (names, numbers, dates) are summarised
               in one line, since dropping them is by design; the items are STRUCTURAL
               losses. This step never sees the candidates.
  3. MATCH   — once all cases are done: every structural item against the ten
               candidates' own opening descriptions, NONE allowed.

Outputs (experiments/residue/, snapshots, overwritten): <case>_encoding.json,
<case>_reading.md, <case>_residue.json, match.json.

Usage:
    python3 residue.py                 # all cases, all steps
    python3 residue.py --cases sutton  # some cases (steps 1-2)
    python3 residue.py --match-only    # step 3 on the residue files present
    python3 residue.py --out rerun/with_ap --with-account-production   # acceptance arm
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path

HERE = Path(__file__).resolve().parent
OPS = HERE.parent.parent
REPLAY = Path.home() / "private_field" / "replay"
CANDIDATES_DOC = Path.home() / "new_material" / "new_operator_dimension_ideas_aug27-026"
sys.path[:0] = [str(OPS), str(OPS / "lib"), str(REPLAY)]

os.environ["PRIVACY_GATE"] = "off"           # public Innocence Project / NRE cases
from vivify_core import llm_call, extract_json, read_json, write_json

MODEL_CAPABILITY = "prose_reconstruction"
DECODER_PROMPT = OPS / "experiments" / "round_trip" / "v2" / "decoder_prompt_v2.txt"

# Which logos keys survive encoding: the round-trip v2 template (values, axes,
# confidences; no rationale, surface/underlying, implicature, source or _fields).
TEMPLATE = read_json(OPS / "experiments" / "round_trip" / "v2" / "input_real.json")
CONFLICT_KEYS = ["schema", "behavior", "terrain", "window", "escalation_phase",
                 "counter_force", "confidence"]

STORE = OPS / "inferences" / "field"
CASES = {
    "sutton":     {"store": "inf_285ae7ab.json"},
    "washington": {"store": "inf_a3d99808.json"},
    "cotton":     {"store": "inf_f39647fd.json"},   # the longest of the three Cotton tellings
    "brown":      {"replay": "brown", "slice": 15},
}

RESIDUE_PROMPT = """Below are two texts about the same real case.

CASE RECORD: the original record.
BLIND READING: written by a model that never saw the record, only a set of abstract
social-structural descriptors derived from it.

List what the CASE RECORD contains that the BLIND READING does not recover, or gets
wrong.

- Names, dates, places, numbers and other particulars were dropped on purpose. Do not
  list them one by one; summarise them in a single line.
- Every other loss is an ITEM: a relation, process, mechanism, position, sequence or
  dynamic in the record that the reading misses or misdescribes.
- Describe each item in plain words of your own. Do not name theories, schools or
  frameworks, and do not sort items into categories.
- If the reading recovered something well, do not list it.

Return JSON only:
{"particulars": "<one line>",
 "items": [{"record": "<what the record shows, with a short quote from it>",
            "reading": "<what the reading says instead, or 'absent'>",
            "loss": "<one sentence: what kind of information this is>"}]}

CASE RECORD:
<<<
%s
>>>

BLIND READING:
<<<
%s
>>>
"""

MATCH_PROMPT = """Below are STRUCTURAL LOSSES found when real cases were reduced to abstract
descriptors and rebuilt blind, and TEN CANDIDATE DIMENSIONS from the research
literature, each given by its own opening text.

For each loss, decide whether one candidate would capture it if it were added as a
descriptor: the candidate's id, or NONE. Use NONE whenever the fit is loose; a
weak match is worse than none. Then, for each candidate, count how many losses it
captures.

Return JSON only:
{"items": [{"id": "<loss id>", "match": "<C-0n or NONE>", "why": "<one sentence>"}],
 "by_candidate": {"C-01": <n>, ..., "C-10": <n>, "NONE": <n>}}

LOSSES:
%s

CANDIDATES:
%s
"""


def encode(logos, conflict):
    """Coordinates only, in the round-trip v2 shape."""
    out = {"logos": {}, "conflict": {}}
    for dim, keys in TEMPLATE["logos"].items():
        if dim in logos:
            out["logos"][dim] = {k: logos[dim].get(k) for k in keys if k in logos[dim]}
    out["conflict"] = {k: conflict[k] for k in CONFLICT_KEYS if k in conflict}
    return out


def load_case(name, spec):
    """(record text, encoding) for one case."""
    if "store" in spec:
        inf = read_json(STORE / spec["store"])
        return inf["raw_text"], encode(inf["logos"], inf["conflict"])
    from run_replay import cumulative_text
    case = REPLAY / spec["replay"]
    stream = read_json(case / "slices_v1.json")
    n = spec["slice"]
    logos = read_json(case / "runs" / f"slice_{n:02d}.json")["logos"]
    conflict = read_json(case / "runs_cf" / f"slice_{n:02d}.json")["conflict"]
    return cumulative_text(stream["slices"], n), encode(logos, conflict)


def candidate_openings():
    """C-01..C-10 by their own opening text (first ~700 chars of each section)."""
    text = CANDIDATES_DOC.read_text()
    parts = re.split(r"\n### (C-\d\d[^\n]*)\n", text)
    out = []
    for i in range(1, len(parts), 2):
        body = parts[i + 1].split("\n## ")[0].strip()
        out.append(f"{parts[i]}\n{' '.join(body[:700].split())}")
    return "\n\n".join(out)


def add_account_production(name, encoding, named=False, positions=False):
    """The mode alone, from account_production_run.json; signals carry particulars.

    named: label the value with WHOSE account it describes. The bare label was read
    as describing the text itself (acceptance try 1, 2026-10-17).
    positions: also who supplied and who shaped it (try 3; try 2 lost WHO)."""
    rec = read_json(HERE / "account_production_run.json")[name]
    mode = rec["mode"]
    if positions:
        encoding["logos"]["account_the_institution_relied_on"] = {
            "how_it_was_made": mode, "supplied_by": rec["supplied_by"], "shaped_by": rec["shaped_by"]}
    elif named:
        encoding["logos"]["account_the_institution_relied_on"] = {"how_it_was_made": mode}
    else:
        encoding["logos"]["account_production"] = {"mode": mode}
    return encoding


def run_case(name, spec, out=HERE, with_ap=False, named=False, positions=False, domain=None):
    record, encoding = load_case(name, spec)
    if with_ap:
        encoding = add_account_production(name, encoding, named, positions)
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / f"{name}_encoding.json", encoding)
    decoder = DECODER_PROMPT.read_text()
    domain_line = f"Domain: {domain}\n\n" if domain else ""
    reading = llm_call(decoder + "\n\n" + domain_line + json.dumps(encoding, indent=2),
                       capability=MODEL_CAPABILITY, sensitive=False)
    (out / f"{name}_reading.md").write_text(reading + "\n")
    raw = llm_call(RESIDUE_PROMPT % (record, reading),
                   capability=MODEL_CAPABILITY, sensitive=False)
    residue = extract_json(raw)
    for i, item in enumerate(residue.get("items", []), 1):
        item["id"] = f"{name}-{i:02d}"
    write_json(out / f"{name}_residue.json", residue)
    print(f"{name}: {len(residue.get('items', []))} structural items")


def run_match():
    items = []
    for f in sorted(HERE.glob("*_residue.json")):
        items += read_json(f).get("items", [])
    losses = "\n".join(f"[{it['id']}] {it['loss']} (record: {it['record']})" for it in items)
    raw = llm_call(MATCH_PROMPT % (losses, candidate_openings()),
                   capability=MODEL_CAPABILITY, sensitive=False)
    match = extract_json(raw)
    write_json(HERE / "match.json", match)
    print("by candidate:", match.get("by_candidate"))


def main():
    ap = argparse.ArgumentParser(description="residue reading: what the coordinates drop")
    ap.add_argument("--cases", help="comma-separated subset of " + ",".join(CASES))
    ap.add_argument("--match-only", action="store_true")
    ap.add_argument("--out", help="write case files here instead (a re-run arm); no match step")
    ap.add_argument("--with-account-production", action="store_true",
                    help="add logos.account_production.mode to each encoding")
    ap.add_argument("--named", action="store_true",
                    help="with --with-account-production: label it as the account the institution relied on")
    ap.add_argument("--domain", help="tell the decoder the domain (e.g. 'criminal case'), as keywords would")
    ap.add_argument("--positions", action="store_true",
                    help="with --with-account-production: named label plus supplied_by and shaped_by")
    args = ap.parse_args()
    out = Path(args.out) if args.out else HERE
    if not args.match_only:
        names = args.cases.split(",") if args.cases else list(CASES)
        for name in names:
            run_case(name, CASES[name], out, args.with_account_production, args.named, args.positions, args.domain)
    if not args.out and (args.match_only or not args.cases):
        run_match()


if __name__ == "__main__":
    main()

# llm: claude-opus-5-5 | 2026-10-17 | repos/vivify-operators/experiments/residue/residue.py | created — demand-pull residue test: blind decode, residue vs case record (candidates unseen), then match against C-01..C-10 with NONE allowed
# llm: claude-opus-5-5 | 2026-10-17 | repos/vivify-operators/experiments/residue/residue.py | --out (re-run arm, no match step) and --with-account-production (adds the mode alone to each encoding) for the account_production acceptance test
# llm: claude-opus-5-5 | 2026-10-17 | repos/vivify-operators/experiments/residue/residue.py | --named: label the mode as the account the institution relied on (try 1 was read as describing the text itself)
# llm: claude-opus-5-5 | 2026-10-17 | repos/vivify-operators/experiments/residue/residue.py | --positions: named label plus supplied_by and shaped_by (acceptance try 3)
# llm: claude-opus-5-5 | 2026-10-18 | repos/vivify-operators/experiments/residue/residue.py | --domain: one line naming the domain before the coordinates, so structure can be tested apart from domain (acceptance try 4)
