#!/usr/bin/env python3
"""Focused test: social_field scores two levels, the events and the telling.

- a two-level result passes the gate; an out-of-range telling_grid is rejected
- the vote signature carries both quadrants, so a draw that flips only the telling level is a different draw
- parse() keeps the events level at the top (what conflict, cross_scale and narrative read) and stores the telling under social_field.telling, quadrant derived from its own axes
- a result without telling_* (the pre-2026-10-22 shape) still parses, with telling = None
- the fused pass now requires the telling fields, so a block without them is retried

No real LLM calls.

Run standalone: python3 tests/test_social_field_levels.py  (exit 0 = pass)
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "lib"))

import social_field_operator as sf
import logos_fused
from vivify_core import validate_coordinates, categorical_signature, CoordinateValidationError

CONFIG = str(ROOT / "config")
failures = []


def check(label, condition, detail=""):
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}  {detail}")
        failures.append(label)


def draw(t_grid=0.3, t_group=0.2, t_quadrant="individualist"):
    # a case summary: courts at the events level, a public page at the telling level
    return {"grid": 0.9, "group": 0.45, "quadrant": "hierarchical", "rationale": "courts and a lab",
            "telling_grid": t_grid, "telling_group": t_group, "telling_quadrant": t_quadrant,
            "telling_rationale": "a public case page", "confidence": 0.8}


try:
    validate_coordinates(draw(), "social_field", CONFIG)
    check("two-level result passes the gate", True)
except CoordinateValidationError as e:
    check("two-level result passes the gate", False, str(e))

try:
    validate_coordinates(draw(t_grid=1.4), "social_field", CONFIG)
    check("telling_grid out of range is rejected", False)
except CoordinateValidationError:
    check("telling_grid out of range is rejected", True)

sig_a = categorical_signature(draw(), "social_field", CONFIG)
sig_b = categorical_signature(draw(t_quadrant="hierarchical"), "social_field", CONFIG)
check("vote signature carries both quadrants", dict(sig_a).keys() == {"quadrant", "telling_quadrant"}, sig_a)
check("a telling-only flip is a different draw", sig_a != sig_b)

out = sf.parse(dict(draw(), _model="m"), {})["logos"]["social_field"]
check("top level is the events level", (out["grid"], out["group"], out["level"]) == (0.9, 0.45, "events"), out)
check("events quadrant derived from its axes", out["quadrant"] == "isolate", out["quadrant"])
check("telling stored with its own axes", (out["telling"]["grid"], out["telling"]["group"]) == (0.3, 0.2), out["telling"])
check("telling quadrant derived from its axes", out["telling"]["quadrant"] == "individualist", out["telling"])

old = {"grid": 0.4, "group": 0.2, "quadrant": "individualist", "rationale": "r", "confidence": 0.7}
out_old = sf.parse(old, {})["logos"]["social_field"]
check("old one-level result still parses", out_old["telling"] is None and out_old["level"] is None, out_old)

required = logos_fused._required_fields("social_field")
check("fused pass requires the telling fields",
      {"telling_grid", "telling_group", "telling_quadrant"} <= set(required), required)
check("fused prompt asks for the telling fields", '"telling_grid"' in logos_fused.PROMPT_TEMPLATE)

print()
print("PASS" if not failures else f"FAIL: {len(failures)} check(s): {failures}")
sys.exit(1 if failures else 0)

# llm: claude-opus-5-5 | 2026-10-22 | repos/vivify-operators/tests/test_social_field_levels.py | created — social_field two levels: gate, vote signature, parse mapping (events on top, telling nested), old-shape compatibility, fused required fields
