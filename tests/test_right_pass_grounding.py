#!/usr/bin/env python3
"""Focused test: right_pass keeps a quote the model re-punctuated, drops one it reworded.

The grounding check once compared after lowercasing and collapsing spaces only, so a
quote copied with a straight apostrophe where the text had a curly one was dropped
as ungrounded, silently lowering confirmed tension. It now folds the same glyph
differences claim_check does, and nothing else.

No LLM calls. Run standalone: python3 tests/test_right_pass_grounding.py  (exit 0 = pass)
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "lib"))

from right_pass import _grounded

TEXT = "He was 5\u20198\u2033 and weighed 130 pounds \u2014 the lab\u2019s report said \u201cno match\u201d.\u00a0It was 1994\u20131995."

failures = []


def check(label, condition):
    print(f"  {'ok  ' if condition else 'FAIL'} {label}")
    if not condition:
        failures.append(label)


check("straight apostrophe and inch mark match curly and prime", _grounded("He was 5'8\" and weighed 130 pounds", TEXT))
check("hyphen matches an em dash", _grounded("130 pounds - the lab's report", TEXT))
check("straight double quotes match curly ones", _grounded('said "no match"', TEXT))
check("ordinary space matches a non-breaking space", _grounded('"no match". It was 1994-1995', TEXT))
check("case and extra spaces still do not matter", _grounded("HE   WAS 5'8", TEXT))
check("a reworded quote is still dropped", not _grounded("He was 5'8\" and weighed 140 pounds", TEXT))
check("an empty quote is not grounded", not _grounded("", TEXT))

print()
if failures:
    print(f"FAILED: {len(failures)} check(s)")
    sys.exit(1)
print("All right_pass grounding checks passed.")

# llm: claude-fable-5-2 | 2026-11-16 | repos/vivify-operators/tests/test_right_pass_grounding.py | created: grounding folds glyph differences only
