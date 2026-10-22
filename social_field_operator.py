#!/usr/bin/env python3
"""
social_field_operator.py — logos tagging pass: Douglas grid/group axes

Reads a vivified inference, scores it on Douglas's grid/group axes,
attaches logos.social_field coordinates to the inference JSON.

Two levels: the field the described acts take place in (events, the top-level
grid/group) and the field the text itself circulates in (telling). A case summary
is about its events, so a single score had to pick one, and each draw picked
silently (round_trip v4, 2026-10-22).

_src: Douglas (Purity and Danger, 1966; Natural Symbols, 1970)
Schema: pillars/logos/logos_schema_v01.json#dimensions.social_field
"""

import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "lib"))
from vivify_core import read_json, write_json, resolve_model, call_and_vote

PROMPT = """You are applying Mary Douglas's grid/group framework to score a text unit.
Researcher context: Douglas (Purity and Danger 1966, Natural Symbols 1970).

Two independent axes, each 0.0 to 1.0:

  grid  — degree to which behavior is constrained by explicit rules and classifications
          0.0 = unconstrained, personal, negotiable, improvised
          1.0 = rigid, rule-bound, role-defined, hierarchically prescribed

  group — degree to which individual identity is defined by group membership
          0.0 = individual, autonomous, weak boundary between self and outside
          1.0 = collective, strong boundary, identity inseparable from group

The four quadrants this produces:
  low grid / low group   — individualist, competitive, negotiated order
  high grid / low group  — isolated, role-defined but not group-belonging
  low grid / high group  — egalitarian, strong boundary, internal negotiation
  high grid / high group — hierarchical, role and group together, most institutionalized

Score TWO fields, each on both axes:

  events  — the social constraint field in which the acts the text describes take
            place: the people who act in it, and the rules and roles they act under.
  telling — the social constraint field in which this text itself is communicated:
            who it is written for, and under what rules it circulates.

For a text that is itself a move inside its events (a ruling, a demand, a message
to the other party), the two are the same field: give both the same scores. For a
text that reports events from outside (a case summary, a news account, notes), score
each on its own. Score the fields, not the content of the communication.

Text:
{text}

Return ONLY valid JSON:
{{
  "grid":      <0.0-1.0>,
  "group":     <0.0-1.0>,
  "quadrant":  "<individualist|isolate|egalitarian|hierarchical>",
  "rationale": "<one sentence — what social field the described acts take place in>",
  "telling_grid":      <0.0-1.0>,
  "telling_group":     <0.0-1.0>,
  "telling_quadrant":  "<individualist|isolate|egalitarian|hierarchical>",
  "telling_rationale": "<one sentence — what social field this text is communicated in>",
  "confidence": <0.0-1.0>
}}
"""


QUADRANT_THRESHOLD = 0.5


def derive_quadrant(grid, group, threshold=QUADRANT_THRESHOLD):
    """Douglas's quadrant is a POSITION on the two axes, not a separate judgement.

    The prompt above documents the mapping, but the drawn label contradicted its own
    grid/group in 2 of the 4 stored field inferences (both at grid 0.85 / group 0.4,
    labelled "hierarchical" where high-grid/low-group is "isolate") — the model reaches
    for the everyday sense of "hierarchical" whenever the setting is institutional.
    Deriving it makes that contradiction impossible. The drawn label is kept as
    quadrant_drawn so how often the model disagrees with its own axes stays measurable.
    Boundary: >= threshold counts as high.
    """
    if not isinstance(grid, (int, float)) or not isinstance(group, (int, float)):
        return None
    return {(False, False): "individualist",
            (True,  False): "isolate",
            (False, True):  "egalitarian",
            (True,  True):  "hierarchical"}[(grid >= threshold, group >= threshold)]


def run(inference: dict) -> dict:
    """Attach logos.social_field coordinates to an inference."""
    text = inference.get("raw_text", "")
    if not text:
        return inference

    result = call_and_vote(PROMPT.format(text=text), "social_field",
                           capability="logos_operator", sensitive=True)
    return parse(result, inference)


def parse(result: dict, inference: dict) -> dict:
    """Map a validated social_field result into inference['logos']['social_field'].

    Split out from run() so the fused logos pass (logos_fused.py) can reuse this
    mapping with a pre-fetched sub-result, without re-calling the LLM.

    The top-level grid/group/quadrant are the EVENTS level, so every reader of
    social_field (conflict, cross_scale, narrative) gets the case, not the page it
    was reported on. The telling level sits under "telling", quadrant derived the
    same way; it is None when a result predates the two-level prompt."""
    logos = inference.setdefault("logos", {})
    grid, group = result["grid"], result["group"]
    drawn = result.get("quadrant")
    derived = derive_quadrant(grid, group)
    t_grid, t_group = result.get("telling_grid"), result.get("telling_group")
    telling = None
    if t_grid is not None or t_group is not None:
        t_drawn = result.get("telling_quadrant")
        t_derived = derive_quadrant(t_grid, t_group)
        telling = {
            "grid":      t_grid,
            "group":     t_group,
            "quadrant":  t_derived if t_derived is not None else t_drawn,
            "quadrant_drawn": t_drawn,
            "rationale": result.get("telling_rationale"),
        }
    logos["social_field"] = {
        "grid":       grid,
        "group":      group,
        "quadrant":   derived if derived is not None else drawn,
        "quadrant_drawn":  drawn,
        "quadrant_agrees": (derived == drawn) if derived is not None else None,
        "rationale":  result.get("rationale"),
        "level":      "events" if telling is not None else None,
        "telling":    telling,
        "confidence": result.get("confidence"),
        "_model":     result.get("_model"),
        "_votes":     result.get("_votes"),
        "_src":       ["Douglas"],
        "_operator":  "social_field_operator.py"
    }
    return inference


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Tag an inference with Douglas grid/group social field scores"
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
        print(f"logos.social_field tagged: grid={tagged['logos']['social_field']['grid']} group={tagged['logos']['social_field']['group']}")
# llm: claude-sonnet-4-6 | 2026-05-22 | repos/vivify-inferences/social_field_operator.py | created — Douglas grid/group social field logos tagging operator
# llm: claude-opus-4-8 | 2026-06-20 | repos/vivify-operators/social_field_operator.py | wired inbound validation gate: validate_coordinates() on extract_json output
# llm: claude-opus-4-8 | 2026-06-20 | repos/vivify-operators/social_field_operator.py | wired sensitive=True into llm_call so the privacy gate protects field data
# llm: claude-opus-4-8 | 2026-06-24 | repos/vivify-operators/social_field_operator.py | retry-on-invalid: run() uses call_and_validate() so a recoverable small-model miss is re-asked, not dropped as a missing dimension
# llm: claude-opus-4-8 | 2026-06-24 | repos/vivify-operators/social_field_operator.py | split result->logos mapping into parse() so logos_fused.py reuses it without re-calling the LLM (run = call_and_validate + parse); behavior unchanged
# llm: claude-opus-5 | 2026-08-13 | repos/vivify-operators/social_field_operator.py | parse() records _model beside _operator — which model produced the coordinate

# llm: claude-opus-5 | 2026-09-07 | repos/vivify-operators/social_field_operator.py | quadrant is now DERIVED from grid/group (it contradicted its own axes in 2 of 4 stored inferences); drawn label kept as quadrant_drawn + quadrant_agrees so the disagreement stays measurable; parse() is shared so the fused pass gets the fix too
# llm: claude-opus-5-5 | 2026-10-22 | repos/vivify-operators/social_field_operator.py | two levels: grid/group/quadrant now score the EVENTS, telling_* the field the text itself circulates in (same scores for a within text); parse() stores the telling under social_field.telling with a derived quadrant; forced by the round_trip v4 case-identity fail
