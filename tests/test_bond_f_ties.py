#!/usr/bin/env python3
"""Focused test: bond --f-ties runs steps 1 and 5 only.

run_f_ties must make the voted bond call (step 1) and the per-tie registered votes
(step 5), and never the event steps 2-4 (registered per event, via, tie effect).
Per-tie registered must come out as a full run would give it, and logos.bond._steps
must record [1, 5]. An unmarked result skips step 5.

No real LLM calls — bond_operator.call_and_vote / call_and_validate are monkeypatched.
Run standalone: python3 tests/test_bond_f_ties.py  (exit 0 = pass)
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "lib"))

import bond_operator

failures = []


def check(label, condition, detail=""):
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}  {detail}")
        failures.append(label)


def bond_result(standing="threatened"):
    return {"standing": standing, "between": "mother and son", "main_bond": "B1", "hazard": "alleged",
            "bonds": [{"id": "B1", "between": "mother and son", "standing": "threatened"},
                      {"id": "B2", "between": "brothers", "standing": "secure"}],
            "events": [{"order": 1, "what": "order moves son", "effect": "reduced", "made_by": "institution",
                        "bonds": ["B1"]}],
            "_model": "claude-opus-5-5", "_votes": {"n": 3, "agreed": 3, "unanimous": True}}


operators = []


def fake_vote(prompt, operator, **kwargs):
    operators.append(("vote", operator))
    return dict(STEP1)


def fake_validate(prompt, operator, **kwargs):
    operators.append(("validate", operator))
    return {"registered": {"1": "weighed", "2": "absent"}, "_model": "claude-opus-5-5"}


orig_vote, orig_validate = bond_operator.call_and_vote, bond_operator.call_and_validate
try:
    bond_operator.call_and_vote, bond_operator.call_and_validate = fake_vote, fake_validate
    STEP1 = bond_result()
    inf = bond_operator.run_f_ties({"raw_text": "some decision text"})
    b = inf["logos"]["bond"]
    ops = [o for _, o in operators]
    check("step 1 ran once", ops.count("bond") == 1, ops)
    check("only step 5 votes after step 1", set(ops) - {"bond"} == {"bond_registered"}, ops)
    check("step 5 voted 3 draws", ops.count("bond_registered") == 3, ops)
    check("per-tie registered by majority", [t.get("registered") for t in b["bonds"]] == ["weighed", "absent"], b["bonds"])
    check("no event votes stored", not any(k.startswith("_") and k.endswith("_votes") for e in b["events"] for k in e), b["events"])
    check("_steps recorded", b.get("_steps") == [1, 5], b.get("_steps"))

    operators.clear()
    STEP1 = bond_result("unmarked")
    inf = bond_operator.run_f_ties({"raw_text": "some decision text"})
    check("unmarked: step 5 skipped", [o for _, o in operators] == ["bond"], operators)
    check("unmarked: _steps still recorded", inf["logos"]["bond"].get("_steps") == [1, 5])

    operators.clear()
    check("empty text: no calls", bond_operator.run_f_ties({"raw_text": ""}) == {"raw_text": ""} and not operators)
finally:
    bond_operator.call_and_vote, bond_operator.call_and_validate = orig_vote, orig_validate

print("PASS" if not failures else f"FAIL ({len(failures)})")
sys.exit(1 if failures else 0)

# llm: claude-opus-5-5 | 2026-11-06 | repos/vivify-operators/tests/test_bond_f_ties.py | created — --f-ties runs steps 1 and 5 only (calls stubbed, no live calls)
