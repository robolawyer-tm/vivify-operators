#!/usr/bin/env python3
"""Focused test: bond validates its vocabulary, votes on standing and hazard, derives its main values from events, and parses.

- every value of the four enums passes the gate; out-of-set values are rejected
- the vote signature is standing and hazard; effect, made_by and registered are derived from the events
- parse() stores the coordinates, signals and provenance under logos.bond
- the prompt names no harm or purpose (it describes bonds only)
- a text-less inference is returned untouched, with no call

No real LLM calls — call_and_vote is stubbed.

Run standalone: python3 tests/test_bond.py  (exit 0 = pass)
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "lib"))

import bond_operator as bo
from vivify_core import validate_coordinates, categorical_signature, CoordinateValidationError

CONFIG = str(ROOT / "config")
failures = []


def check(label, condition, detail=""):
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}  {detail}")
        failures.append(label)


def draw(**kw):
    d = {"between": "mother and child aged 7", "standing": "secure", "hazard": "none",
         "bond_signals": ["mother and child (between mother and child aged 7): primary caregiver since birth"],
         "events": [{"order": 2, "what": "custody order", "made_by": "institution", "reported_by": "institution",
                     "effect": "reduced", "registered": "absent", "words": "every other weekend"},
                    {"order": 1, "what": "shared care arranged by the parents", "made_by": "members",
                     "reported_by": "member", "effect": "preserved", "registered": "mentioned", "words": "they agreed"}],
         "rationale": "r", "confidence": 0.8}
    d.update(kw)
    return d


VALUES = {"standing": ("unmarked", "secure", "strained", "ruptured"),
          "hazard": ("none", "alleged", "established")}
for field, values in VALUES.items():
    ok = []
    for v in values:
        try:
            validate_coordinates(draw(**{field: v}), "bond", CONFIG)
            ok.append(v)
        except CoordinateValidationError:
            pass
    check(f"every {field} value passes the gate", ok == list(values), ok)
    try:
        validate_coordinates(draw(**{field: "harmed"}), "bond", CONFIG)
        check(f"out-of-set {field} rejected", False, "accepted")
    except CoordinateValidationError:
        check(f"out-of-set {field} rejected", True)

a, b = draw(), draw(between="father and son", bond_signals=[], events=[], rationale="other", confidence=0.3)
check("vote signature is standing and hazard",
      categorical_signature(a, "bond", CONFIG) == categorical_signature(b, "bond", CONFIG)
      == (("hazard", "none"), ("standing", "secure")))

prompt = bo.PROMPT.lower()
check("prompt names no harm or purpose",
      not any(w in prompt for w in ("harm", "damage", "suffer", "self-harm", "reform", "wrong")),
      [w for w in ("harm", "damage", "suffer", "self-harm", "reform", "wrong") if w in prompt])

# step 2: registered per event, majority per event over stubbed draws
seq = iter([{"registered": {"1": "weighed", "2": "absent"}},
            {"registered": {"1": "weighed", "2": "mentioned"}},
            {"registered": {"1": "mentioned", "2": "maybe"}}])
orig_cv = bo.call_and_validate
bo.call_and_validate = lambda *a, **k: {**next(seq), "_model": "m"}
try:
    evs = bo.registered_votes("text", "father and child", [{"what": "a"}, {"what": "b"}], votes=3)
    check("registered: majority per event", evs[0]["registered"] == "weighed"
          and evs[0]["_registered_votes"]["distribution"] == {"weighed": 2, "mentioned": 1}, evs[0])
    check("registered: no majority stays None, spread kept, off-set value not counted",
          evs[1]["registered"] is None and evs[1]["_registered_votes"]["distribution"] == {"absent": 1, "mentioned": 1}, evs[1])
    kept = bo.events(evs)
    check("events() keeps the per-event vote record", "_registered_votes" in kept[0], kept[0])
finally:
    bo.call_and_validate = orig_cv

calls = []
orig = bo.call_and_vote
bo.call_and_vote = lambda prompt, op, **kw: calls.append(op) or {**draw(), "_model": "m", "_votes": {"n": 3}}
orig_rv = bo.registered_votes
bo.registered_votes = lambda text, between, evs, votes=None: calls.append("registered") or evs
try:
    out = bo.run({"raw_text": "The order ended the father's contact with the child."})
    rec = out["logos"]["bond"]
    check("main values come from the event that changed the bond most",
          (rec["standing"], rec["effect"], rec["made_by"], rec["registered"], rec["main_event"], rec["hazard"])
          == ("secure", "reduced", "institution", "absent", 2, "none"), rec)
    check("parse stores the events", len(rec["events"]) == 2, rec)
    check("events are sorted into the family's chronology",
          [e["order"] for e in rec["events"]] == [1, 2], rec["events"])
    check("parse stores between and signals", rec["between"] == "mother and child aged 7" and len(rec["bond_signals"]) == 1, rec)
    check("parse records provenance",
          rec["_model"] == "m" and rec["_votes"] == {"n": 3} and rec["_operator"] == "bond_operator.py", rec)
    check("two steps: the bond vocabulary, then registered per event", calls == ["bond", "registered"], calls)
    calls.clear()
    empty = bo.run({"raw_text": ""})
    check("no text: untouched, no call", calls == [] and "logos" not in empty, empty)
finally:
    bo.call_and_vote = orig
    bo.registered_votes = orig_rv

ev = bo.events([{"order": 1, "what": "x", "made_by": "court", "effect": "reduced"},
                "an older plain-string event",
                {"what": "no order", "made_by": "members", "reported_by": "member", "effect": "restored"}])
check("off-vocabulary event values are kept and named", ev[0].get("_off_vocabulary") == ["made_by"], ev)
check("a plain-string event becomes a record", any(e["what"] == "an older plain-string event" for e in ev), ev)
check("events without an order sort last", ev[-1]["order"] is None and ev[0]["order"] == 1, ev)

E = lambda o, eff: {"order": o, "effect": eff}
bs = bo.bonds([{"id": "B1", "between": "father and son", "standing": "secure"},
                {"id": "B2", "between": "two sisters", "standing": "close"}, "junk"])
check("bonds: every bond kept with id and roles, off-vocabulary standing named, junk dropped",
      len(bs) == 2 and bs[1]["_off_vocabulary"] == ["standing"] and bs[0]["id"] == "B1", bs)
rec2 = bo.parse({"standing": "secure", "hazard": "none", "main_bond": "B1",
                 "bonds": [{"id": "B1", "between": "father and son", "standing": "secure"}],
                 "events": [{"order": 1, "bonds": ["B1"], "effect": "reduced", "made_by": "members"}]}, {})["logos"]["bond"]
check("parse stores bonds, the main bond, and each event's bonds",
      rec2["main_bond"] == "B1" and len(rec2["bonds"]) == 1 and rec2["events"][0]["bonds"] == ["B1"], rec2)
check("main event: a severing outranks a reduction", bo.main_event([E(1, "severed"), E(2, "reduced")])["order"] == 1)
check("main event: ties go to the earlier event", bo.main_event([E(1, "reduced"), E(2, "restored")])["order"] == 1)
check("main event: continuity alone is no main event", bo.main_event([E(1, "preserved")]) is None)
only_kept = bo.parse({"standing": "secure", "hazard": "none", "events": [E(1, "preserved")]}, {})["logos"]["bond"]
check("only continuity: effect preserved, no maker", (only_kept["effect"], only_kept["made_by"]) == ("preserved", "none"), only_kept)
nobond = bo.parse({"standing": "unmarked", "hazard": "none", "events": []}, {})["logos"]["bond"]
check("no bond: effect none, registered unmarked", (nobond["effect"], nobond["registered"]) == ("none", "unmarked"), nobond)

print()
if failures:
    print(f"FAILED: {len(failures)} check(s) — {', '.join(failures)}")
    sys.exit(1)
print("All bond checks passed.")

# llm: claude-opus-5-5 | 2026-10-26 | repos/vivify-operators/tests/test_bond.py | created — bond vocabulary gate, four-enum vote signature, purpose-blind prompt, parse provenance, no-text path; call_and_vote stubbed
# llm: claude-opus-5-5 | 2026-10-26 | repos/vivify-operators/tests/test_bond.py | made_by enum in gate and signature; events and made_by in parse
# llm: claude-opus-5-5 | 2026-10-26 | repos/vivify-operators/tests/test_bond.py | structured event records: chronology sort, off-vocabulary kept and named, plain-string upgrade
# llm: claude-opus-5-5 | 2026-10-26 | repos/vivify-operators/tests/test_bond.py | vote on standing+hazard only; main values derived from events (main_event rank and ties, continuity, no bond)
# llm: claude-opus-5-5 | 2026-10-26 | repos/vivify-operators/tests/test_bond.py | ties to the earlier event; two-step registered: per-event majority, no-majority None, vote record kept, run() makes both calls
# llm: claude-opus-5-5 | 2026-10-26 | repos/vivify-operators/tests/test_bond.py | every bond listed: bonds() normalisation, main_bond, event bond ids
