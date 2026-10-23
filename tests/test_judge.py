#!/usr/bin/env python3
"""Focused test: the scripted blind judge (experiments/round_trip/judge.py).

- every experiment's packets build, end with the PICK/CONFIDENCE lines, and carry no key text
- parse_verdict reads the last PICK and CONFIDENCE lines, tolerates bold, rejects an unknown letter
- parse_key reads the key files' 'J = sutton K = washington' form
- pattern() tells real / switch / no_switch / mixed apart
- score refuses, with the key unread, while any verdict is missing
- a per-minute 429 is retried; a per-day quota is not
- the fallback parse reads a bold pick on the answer-1 line, and not a restated question

No real LLM calls.

Run standalone: python3 tests/test_judge.py  (exit 0 = pass)
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "experiments" / "round_trip"))

import judge

failures = []


def check(label, condition, detail=""):
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}  {detail}")
        failures.append(label)


for exp, spec in judge.EXPERIMENTS.items():
    ps = judge.packets(exp)
    want = {"shuffle": 2, "identity": 4}[spec["kind"]]
    check(f"{exp}: {want} packets", len(ps) == want, sorted(ps))
    check(f"{exp}: packets end with the closing lines", all(p.endswith(judge.CLOSING) for p in ps.values()))
    check(f"{exp}: no key words in packets",
          not any(w in p for p in ps.values() for w in ("= real", "= shuffled", "= sutton", "= washington")))

check("parse: plain", judge.parse_verdict("...\nPICK: K\nCONFIDENCE: 96%\n", ("J", "K")) == ("K", 96))
check("parse: bold, last line wins",
      judge.parse_verdict("PICK: J\n...\n**PICK:** K\n**CONFIDENCE:** 78%", ("J", "K")) == ("K", 78))
check("parse: unknown letter", judge.parse_verdict("PICK: Q\nCONFIDENCE: 90%", ("J", "K")) == (None, 90))
check("parse: absent", judge.parse_verdict("I pick J.", ("J", "K")) == (None, None))
check("parse fallback: bold answer line", judge.parse_verdict("**1.** Reading **M** was written.\n**2.** **CONFIDENCE:** 78 %", ("M", "N")) == ("M", 78))
check("parse fallback: answer on the line below the question",
      judge.parse_verdict("**1.  Which reading?**  \n**K**\n\n**CONFIDENCE: 82 %**", ("J", "K")) == ("K", 82))
check("parse fallback: question restated is not a pick",
      judge.parse_verdict("1. Which reading, M or N?\nI think 80%", ("M", "N")) == (None, 80))


def flaky(errors):
    def call(text, model_id, sensitive=False):
        if errors:
            raise judge.LLMUnavailable(errors.pop(0))
        return "PICK: J"
    return call


judge.llm_call_model, real_call = flaky(["HTTP Error 429: Too Many Requests"]), judge.llm_call_model
check("retry: per-minute 429 waits and retries", judge.call_judge("x", "groq:m", sleep=lambda s: None) == "PICK: J")
judge.llm_call_model = flaky(["HTTP 429 quota=GenerateRequestsPerDayPerProjectPerModel-FreeTier:20", "x"])
try:
    judge.call_judge("x", "gemini:m", sleep=lambda s: None)
    check("retry: per-day quota raises at once", False, "returned")
except judge.LLMUnavailable:
    check("retry: per-day quota raises at once", True)
judge.llm_call_model = real_call
check("key", judge.parse_key("J = sutton K = washington\n") == {"J": "sutton", "K": "washington"})


def rows(picks, key):
    return [{"pid": pid, "pick": p, "correct": p == judge.truth("v4", pid, key)} for pid, p in picks.items()]


KEY = {"J": "sutton", "K": "washington"}
check("pattern: switch", judge.pattern("v4", rows({"WJ": "K", "WK": "K", "SJ": "J", "SK": "J"}, KEY)) == "switch")
check("pattern: no_switch", judge.pattern("v4", rows({"WJ": "J", "WK": "J", "SJ": "J", "SK": "J"}, KEY)) == "no_switch")
check("pattern: wrong both ways is mixed",
      judge.pattern("v4", rows({"WJ": "J", "WK": "J", "SJ": "K", "SK": "K"}, KEY)) == "mixed")
check("pattern: order moved a pick", judge.pattern("v4", rows({"WJ": "K", "WK": "J", "SJ": "J", "SK": "J"}, KEY)) == "mixed")
check("pattern: shuffle real",
      judge.pattern("v3", [{"pid": "M", "pick": "M", "correct": True}, {"pid": "N", "pick": "M", "correct": True}]) == "real")

try:
    judge.score("v5B", ["nobackend:never-run"])
    check("score refuses with verdicts missing", False, "returned")
except SystemExit as e:
    check("score refuses with verdicts missing", "key stays closed" in str(e), str(e))

print()
print("PASS" if not failures else f"FAIL: {len(failures)} check(s): {failures}")
sys.exit(1 if failures else 0)

# llm: claude-opus-5-5 | 2026-10-23 | repos/vivify-operators/tests/test_judge.py | created — scripted judge: packet build, verdict and key parsing, pattern classes, score refuses while verdicts are missing
# llm: claude-opus-5-5 | 2026-10-23 | repos/vivify-operators/tests/test_judge.py | fallback parse and 429 retry checks
