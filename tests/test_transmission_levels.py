#!/usr/bin/env python3
"""Focused test: transmission classifies two channels, the events and the telling.

- a two-level result passes the gate; an out-of-set telling_transmission is rejected
- the vote signature carries both channels, so a telling-only flip is a different draw
- parse() keeps the events channel as the top-level value (what conflict and narrative read) and nests the telling
- a one-level result (the pre-2026-10-22 shape) still parses, with telling = None
- the fused pass requires telling_transmission, so a block without it is retried

No real LLM calls.

Run standalone: python3 tests/test_transmission_levels.py  (exit 0 = pass)
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "lib"))

import transmission_operator as tx
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


def draw(telling="broadcast"):
    # a case summary: filed lab reports at the events level, a public page at the telling level
    return {"transmission": "archive", "rationale": "filed lab reports and court records",
            "telling_transmission": telling, "telling_rationale": "a public case page",
            "confidence": 0.8}


try:
    validate_coordinates(draw(), "transmission", CONFIG)
    check("two-level result passes the gate", True)
except CoordinateValidationError as e:
    check("two-level result passes the gate", False, str(e))

try:
    validate_coordinates(draw(telling="rumour"), "transmission", CONFIG)
    check("out-of-set telling_transmission is rejected", False)
except CoordinateValidationError:
    check("out-of-set telling_transmission is rejected", True)

sig_a = categorical_signature(draw(), "transmission", CONFIG)
sig_b = categorical_signature(draw(telling="archive"), "transmission", CONFIG)
check("vote signature carries both channels", dict(sig_a).keys() == {"transmission", "telling_transmission"}, sig_a)
check("a telling-only flip is a different draw", sig_a != sig_b)

out = tx.parse(dict(draw(), _model="m"), {})["logos"]["transmission"]
check("top level is the events channel", (out["value"], out["level"]) == ("archive", "events"), out)
check("telling nested", out["telling"] == {"value": "broadcast", "rationale": "a public case page"}, out["telling"])

old = tx.parse({"transmission": "broadcast", "rationale": "r", "confidence": 0.7}, {})["logos"]["transmission"]
check("old one-level result still parses", old["telling"] is None and old["level"] is None, old)

check("fused pass requires telling_transmission", "telling_transmission" in logos_fused._required_fields("transmission"))
check("fused prompt asks for telling_transmission", '"telling_transmission"' in logos_fused.PROMPT_TEMPLATE)

print()
print("PASS" if not failures else f"FAIL: {len(failures)} check(s): {failures}")
sys.exit(1 if failures else 0)

# llm: claude-opus-5-5 | 2026-10-22 | repos/vivify-operators/tests/test_transmission_levels.py | created — transmission two levels: gate, vote signature, parse mapping (events on top, telling nested), old-shape compatibility, fused required fields
