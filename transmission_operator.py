#!/usr/bin/env python3
"""
transmission_operator.py — logos tagging pass: transmission channel

Reads a vivified inference, classifies how the communication moves through the
social field, attaches logos.transmission coordinates to the inference JSON.

Two levels, as social_field: the channel the described events' communications moved
through (the top-level value) and the channel the text itself moves through (telling).
In all five field cases the single value had described the case page (2026-10-22).

_src: Logos Core Tree synthesis (project)
Schema: pillars/logos/logos_schema_v01.json#dimensions.transmission
"""

import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "lib"))
from vivify_core import read_json, write_json, resolve_model, call_and_vote

PROMPT = """You are classifying the transmission channel of a text unit — how the
communication moves through the social field, not what it says.

The three transmission types:
  broadcast — one-to-many, public, low fidelity to source (news, rulings, announcements)
  leak      — restricted recipients, high emotional charge, unofficial, not meant to travel further
  archive   — past-to-future, preserved, institutional, resistant to revision (records, filed documents)

Classify TWO channels:

  events  — how the communications inside the events the text describes moved: the
            reports, statements, records and messages the actors produced and acted on.
  telling — how this text itself moves to its readers.

For a text that is itself a move inside its events (a ruling, a demand, a message to
the other party), the two are the same channel: give the same value. For a text that
reports events from outside (a case summary, a news account, notes), classify each on
its own. Classify the channels as they appear, not how they could be used.

Text:
{text}

Return ONLY valid JSON:
{{
  "transmission": "<broadcast|leak|archive>",
  "rationale": "<one sentence — how the communications inside the described events moved>",
  "telling_transmission": "<broadcast|leak|archive>",
  "telling_rationale": "<one sentence — how this text itself moves>",
  "confidence": <0.0-1.0>
}}
"""


def run(inference: dict) -> dict:
    """Attach logos.transmission coordinates to an inference."""
    text = inference.get("raw_text", "")
    if not text:
        return inference

    result = call_and_vote(PROMPT.format(text=text), "transmission",
                           capability="logos_operator", sensitive=True)
    return parse(result, inference)


def parse(result: dict, inference: dict) -> dict:
    """Map a validated transmission result into inference['logos']['transmission'].

    Split out from run() so the fused logos pass (logos_fused.py) can reuse this
    mapping with a pre-fetched sub-result, without re-calling the LLM.

    The top-level value is the EVENTS channel, so conflict and narrative read the
    case, not the page it was reported on. The telling sits under "telling"; it is
    None when a result predates the two-level prompt."""
    logos = inference.setdefault("logos", {})
    t_value = result.get("telling_transmission")
    telling = None if t_value is None else {"value": t_value,
                                             "rationale": result.get("telling_rationale")}
    logos["transmission"] = {
        "value":      result["transmission"],
        "rationale":  result.get("rationale"),
        "level":      "events" if telling is not None else None,
        "telling":    telling,
        "confidence": result.get("confidence"),
        "_model":     result.get("_model"),
        "_votes":     result.get("_votes"),
        "_src":       ["Logos Core Tree"],
        "_operator":  "transmission_operator.py"
    }
    return inference


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Tag an inference with transmission channel"
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
        print(f"logos.transmission tagged: {tagged['logos']['transmission']['value']}")
# llm: claude-sonnet-4-6 | 2026-05-22 | repos/vivify-inferences/transmission_operator.py | created — transmission channel logos tagging operator
# llm: claude-opus-4-8 | 2026-06-20 | repos/vivify-operators/transmission_operator.py | wired inbound validation gate: validate_coordinates() on extract_json output
# llm: claude-opus-4-8 | 2026-06-20 | repos/vivify-operators/transmission_operator.py | wired sensitive=True into llm_call so the privacy gate protects field data
# llm: claude-opus-4-8 | 2026-06-24 | repos/vivify-operators/transmission_operator.py | retry-on-invalid: run() uses call_and_validate() so a recoverable small-model miss is re-asked, not dropped as a missing dimension
# llm: claude-opus-4-8 | 2026-06-24 | repos/vivify-operators/transmission_operator.py | split result->logos mapping into parse() so logos_fused.py reuses it without re-calling the LLM (run = call_and_validate + parse); behavior unchanged
# llm: claude-opus-5 | 2026-08-13 | repos/vivify-operators/transmission_operator.py | parse() records _model beside _operator — which model produced the coordinate
# llm: claude-opus-5-5 | 2026-10-22 | repos/vivify-operators/transmission_operator.py | two levels: transmission now classifies the EVENTS' channel, telling_* the channel the text itself moves through (same value for a within text); parse() nests the telling; the remaining telling leak after round_trip v5 arm A
