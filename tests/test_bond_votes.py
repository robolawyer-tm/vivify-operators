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

    def __call__(self, prompt, operator, **kwargs):
        self.calls += 1
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
finally:
    bond_operator.call_and_validate = original

print()
if failures:
    print(f"FAILED: {len(failures)} check(s) — {', '.join(failures)}")
    sys.exit(1)
print("All bond-vote checks passed.")

# llm: claude-opus-5-5 | 2026-10-30 | repos/vivify-operators/tests/test_bond_votes.py | created — per_event_votes retries failed draws, raises ShortVotes when fewer than n come back (call_and_validate stubbed, no live calls)
