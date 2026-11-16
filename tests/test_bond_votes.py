#!/usr/bin/env python3
"""Focused test: bond's per-event votes never save an event with missing votes.

per_event_votes once swallowed failed draws: a usage limit left five Canadian
records (2026-10-30) whose events had 0 of 3 votes, saved as if complete. Now a
failed draw is retried (up to n extra attempts) and ShortVotes is raised when
fewer than n draws come back, so the operator exits before writing the record.

No real LLM calls — bond_operator.call_and_validate is monkeypatched.
Run standalone: python3 tests/test_bond_votes.py  (exit 0 = pass)
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "lib"))

import bond_operator
from bond_operator import per_event_votes, ShortVotes, REGISTERED

failures = []


def check(label, condition, detail=""):
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}  {detail}")
        failures.append(label)


class FakeCall:
    """Answers each draw from a script: a value dict, or an exception to raise."""
    def __init__(self, script):
        self.script = list(script)
        self.calls = 0
        self.capabilities = []

    def __call__(self, prompt, operator, **kwargs):
        self.calls += 1
        self.capabilities.append(kwargs.get("capability"))
        step = self.script.pop(0) if self.script else RuntimeError("claude exited 1")
        if isinstance(step, Exception):
            raise step
        return {"registered": step, "_model": "claude-opus-5-5"}


def events():
    return [{"what": "father moves away"}, {"what": "sibling placed elsewhere"}]


VOTE = {"1": "weighed", "2": "absent"}
original = bond_operator.call_and_validate
try:
    bond_operator.call_and_validate = fake = FakeCall([VOTE, VOTE, VOTE])
    evs = per_event_votes("P", "bond_registered", "registered", REGISTERED, events(), votes=3)
    check("all draws back: 3 votes per event", all(e["_registered_votes"]["n"] == 3 for e in evs), evs)
    check("all draws back: majority kept", [e["registered"] for e in evs] == ["weighed", "absent"], evs)
    check("all draws back: no extra calls", fake.calls == 3, fake.calls)

    bond_operator.call_and_validate = fake = FakeCall([RuntimeError("claude exited 1"), VOTE, VOTE, VOTE])
    evs = per_event_votes("P", "bond_registered", "registered", REGISTERED, events(), votes=3)
    check("one failed draw is retried", fake.calls == 4 and evs[0]["_registered_votes"]["n"] == 3, fake.calls)

    bond_operator.call_and_validate = fake = FakeCall([VOTE])
    try:
        per_event_votes("P", "bond_registered", "registered", REGISTERED, events(), votes=3)
        check("short votes raise ShortVotes", False, "no exception")
    except ShortVotes as err:
        check("short votes raise ShortVotes", "1 of 3" in str(err), str(err))
    check("retries are bounded at 2n attempts", fake.calls == 6, fake.calls)

    bond_operator.call_and_validate = fake = FakeCall([VOTE, VOTE, VOTE])
    bond_operator.registered_votes("TEXT", "father and son", events(), votes=3)
    check("registered votes go out as bond_registered", set(fake.capabilities) == {"bond_registered"},
          fake.capabilities)
    bond_operator.call_and_validate = fake = FakeCall([{"1": "distance", "2": "placement"}] * 3)
    bond_operator.via_votes(events(), votes=3)
    check("via votes stay on logos_operator", set(fake.capabilities) == {"logos_operator"}, fake.capabilities)
finally:
    bond_operator.call_and_validate = original

# the three sub-pass names are in config/coordinates.json, so the gate applies to them
import json
from vivify_core import validate_coordinates, CoordinateValidationError
CONFIG = str(ROOT / "config")
ops = json.load(open(ROOT / "config" / "coordinates.json"))["operators"]
check("config carries the registered vocabulary", ops["bond_registered"]["enum_maps"]["registered"] == list(REGISTERED))
check("config carries the via vocabulary", ops["bond_via"]["enum_maps"]["via"] == list(bond_operator.VIA))
check("config carries the tie-effect vocabulary", ops["bond_tie"]["enum_maps"]["effect"] == list(bond_operator.TIE_EFFECT))


def rejected(result, operator):
    try:
        validate_coordinates(result, operator, CONFIG)
        return False
    except CoordinateValidationError:
        return True


check("a well-formed answer passes the gate", not rejected({"registered": {"1": "weighed", "2": "absent"}}, "bond_registered"))
check("a list where a map is expected is rejected", rejected({"registered": ["weighed", "absent"]}, "bond_registered"))
check("a paragraph smuggled in as a value is rejected", rejected({"via": {"1": "distance " * 40}}, "bond_via"))
check("a nested object as a value is rejected", rejected({"effect": {"1": {"x": "severed"}}}, "bond_tie"))
check("an off-vocabulary word passes the gate (the vote leaves it uncounted)",
      not rejected({"registered": {"1": "noted"}}, "bond_registered"))

print()
if failures:
    print(f"FAILED: {len(failures)} check(s) — {', '.join(failures)}")
    sys.exit(1)
print("All bond-vote checks passed.")

# llm: claude-opus-5-5 | 2026-10-30 | repos/vivify-operators/tests/test_bond_votes.py | created — per_event_votes retries failed draws, raises ShortVotes when fewer than n come back (call_and_validate stubbed, no live calls)
# llm: claude-opus-5-5 | 2026-10-31 | repos/vivify-operators/tests/test_bond_votes.py | registered votes use capability bond_registered, via stays on logos_operator
# llm: claude-fable-5-2 | 2026-11-16 | repos/vivify-operators/tests/test_bond_votes.py | bond sub-pass names are in coordinates.json and gated on shape and size (enum_maps); vocabulary in config must equal the code's constants
