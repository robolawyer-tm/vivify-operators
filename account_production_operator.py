#!/usr/bin/env python3
"""
account_production_operator.py — logos tagging pass: how the account the institution acts on was made

Reads a vivified inference and records, as far as the text shows, how the account
of events that the institution relies on was produced: by a sincere source who
got it wrong (mistaken), by a real but weak element stated as stronger than it is
(inflated), or by the institution's own agents building or altering it
(manufactured). Attaches logos.account_production coordinates to the inference JSON.

Emergent coordinate: forced by the 2026-10-17 residue test (experiments/residue),
where the blind readings of all four cases lost HOW the false account was produced
(11 items: sutton-03/05, washington-03/05/07, cotton-04/05/09, brown-02/03/15) and
none of the ten literature candidates matched them. The values come from those items.

- The value never asserts that the account is false: in a replay an early step
  cannot know that. It reads how the account was made as far as the text shows.
- One value, the element the institution's case rests on most; the others stay in
  mode_signals (decision 2026-10-17: per-coordinate voting needs one answer).
- Second part, hardening (repetition | endorsement | none), is deferred to its own
  step so each change can be measured alone (sketch: experiments/residue/
  candidate_account_production.md).

_src: vivify-operators residue test (2026-10-17, experiments/residue, 201d7d8)
"""

import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "lib"))
from vivify_core import read_json, write_json, call_and_vote

PROMPT = """You are reading how an account of events was produced.

Find the account that the institution in this text acts on: the version of events
it relies on to decide, accuse, rule or act. Then say how that account was made,
as far as the text shows. Do not judge whether the account is true; judge only
how it came to be.

The modes:
  unmarked     — the text shows nothing about how the account was made, or no
                 institution acts on an account at all.
  mistaken     — a sincere source gets it wrong: someone honestly reports what
                 they believe they saw, heard or remember, and errs. No one is
                 shown shaping it.
  inflated     — a real but weak element is stated as stronger than it is: a
                 figure, an expert's claim, or several weak pieces stacked into
                 apparent certainty.
  manufactured — the institution's own agents build or alter the account:
                 coaching or rehearsing a statement, steering a witness or
                 suspect, rewriting a report, claiming a step was done that was not.

If several modes appear, choose the one the institution's account rests on most,
and list every element in mode_signals. When the account comes from one person but
is shaped by another, the shaper decides the mode.

Text:
{text}

Return ONLY valid JSON:
{{
  "mode": "<unmarked|mistaken|inflated|manufactured>",
  "mode_signals": ["<element> (from <whom>, shaped by <whom or nobody>): <words from the text>"],
  "rationale": "<one sentence: why this mode is the one the account rests on most>",
  "confidence": <0.0-1.0>
}}
"""


def run(inference: dict) -> dict:
    """Attach logos.account_production coordinates to an inference."""
    text = inference.get("raw_text", "")
    if not text:
        return inference

    result = call_and_vote(PROMPT.format(text=text), "account_production",
                           capability="logos_operator", sensitive=True)
    return parse(result, inference)


def parse(result: dict, inference: dict) -> dict:
    """Map a validated account_production result into inference['logos']['account_production'].

    Split out from run() so a fused pass or a replay can reuse the mapping with a
    pre-fetched sub-result, without re-calling the LLM (act_position pattern)."""
    logos = inference.setdefault("logos", {})
    logos["account_production"] = {
        "mode":         result["mode"],
        "mode_signals": result.get("mode_signals", []),
        "rationale":    result.get("rationale"),
        "confidence":   result.get("confidence"),
        "_model":       result.get("_model"),
        "_votes":       result.get("_votes"),
        "_src":         ["residue test 2026-10-17"],
        "_operator":    "account_production_operator.py"
    }
    return inference


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Tag an inference with how the account the institution acts on was made"
    )
    parser.add_argument("file", nargs="?", help="inference JSON file to tag")
    parser.add_argument("--dry-run", action="store_true", help="print result, do not write")
    args = parser.parse_args()

    path = Path(args.file) if args.file else None
    inference = read_json(path) if path else json.load(sys.stdin)

    tagged = run(inference)

    if args.dry_run or not path:
        print(json.dumps(tagged, indent=2))
    else:
        write_json(path, tagged)
        print(f"logos.account_production tagged: {tagged['logos']['account_production']['mode']}")

# llm: claude-opus-5-5 | 2026-10-17 | repos/vivify-operators/account_production_operator.py | created — mode coordinate (unmarked|mistaken|inflated|manufactured + signals), forced by the residue test; one dominant value, hardening deferred
