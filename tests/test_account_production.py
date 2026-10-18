#!/usr/bin/env python3
"""Focused test: account_production validates its vocabulary, votes on its three enums, and parses.

- the four modes pass the gate; an out-of-set mode is rejected
- the vote signature is the three enums (signals, rationale, confidence are not voted on)
- parse() stores mode, signals and provenance under logos.account_production
- a text-less inference is returned untouched, with no call

No real LLM calls — call_and_vote is stubbed.

Run standalone: python3 tests/test_account_production.py  (exit 0 = pass)
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "lib"))

import account_production_operator as ap
from vivify_core import validate_coordinates, categorical_signature, CoordinateValidationError

CONFIG = str(ROOT / "config")
failures = []


def check(label, condition, detail=""):
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}  {detail}")
        failures.append(label)


def draw(mode):
    return {"mode": mode, "supplied_by": "the_target", "shaped_by": "institution", "mode_signals": ["confession (from the accused, shaped by police): fourth attempt"],
            "rationale": "r", "confidence": 0.8}


for mode in ("unmarked", "mistaken", "inflated", "manufactured"):
    try:
        validate_coordinates(draw(mode), "account_production", CONFIG)
        check(f"mode {mode} passes the gate", True)
    except CoordinateValidationError as e:
        check(f"mode {mode} passes the gate", False, str(e))

try:
    validate_coordinates(draw("coerced"), "account_production", CONFIG)
    check("out-of-set mode rejected", False, "accepted")
except CoordinateValidationError:
    check("out-of-set mode rejected", True)

a, b = draw("manufactured"), draw("manufactured")
b.update(mode_signals=[], rationale="other", confidence=0.3)
check("vote signature is the three enums",
      categorical_signature(a, "account_production", CONFIG)
      == categorical_signature(b, "account_production", CONFIG)
      == (("mode", "manufactured"), ("shaped_by", "institution"), ("supplied_by", "the_target")))

bad = draw("manufactured"); bad["supplied_by"] = "police"
try:
    validate_coordinates(bad, "account_production", CONFIG)
    check("out-of-set supplied_by rejected", False, "accepted")
except CoordinateValidationError:
    check("out-of-set supplied_by rejected", True)

calls = []
orig = ap.call_and_vote
ap.call_and_vote = lambda prompt, op, **kw: calls.append(op) or {**draw("inflated"), "_model": "m", "_votes": {"n": 3}}
try:
    out = ap.run({"raw_text": "The statistic overstated the match."})
    rec = out["logos"]["account_production"]
    check("parse stores mode and signals", rec["mode"] == "inflated" and len(rec["mode_signals"]) == 1, rec)
    check("parse stores the positions",
          rec["supplied_by"] == "the_target" and rec["shaped_by"] == "institution", rec)
    check("parse records provenance",
          rec["_model"] == "m" and rec["_votes"] == {"n": 3}
          and rec["_operator"] == "account_production_operator.py", rec)
    check("prompt went to the account_production vocabulary", calls == ["account_production"], calls)
    calls.clear()
    empty = ap.run({"raw_text": ""})
    check("no text: untouched, no call", calls == [] and "logos" not in empty, empty)
finally:
    ap.call_and_vote = orig

print()
if failures:
    print(f"FAILED: {len(failures)} check(s) — {', '.join(failures)}")
    sys.exit(1)
print("All account-production checks passed.")

# llm: claude-opus-5-5 | 2026-10-17 | repos/vivify-operators/tests/test_account_production.py | created — vocabulary gate, mode-only vote signature, parse provenance, no-text path; call_and_vote stubbed
# llm: claude-opus-5-5 | 2026-10-17 | repos/vivify-operators/tests/test_account_production.py | supplied_by/shaped_by: gate, signature and parse checks
