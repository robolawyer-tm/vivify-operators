#!/usr/bin/env python3
"""Focused test: VIVIFY_BUDGET_USD refuses calls once logged spend since VIVIFY_BUDGET_SINCE reaches it.

- under the cap the call goes through and its cost is logged
- at or over the cap the next call raises BudgetExceeded before the transport runs
- lines before SINCE do not count; no cap set = no check
- BudgetExceeded is an LLMUnavailable, so batch callers abort as on quota loss

No real calls — the claude transport is stubbed.

Run standalone: python3 tests/test_budget_cap.py  (exit 0 = pass)
"""
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lib"))

import vivify_core
from vivify_core import llm_call_model, BudgetExceeded, LLMUnavailable

failures, sent = [], []


def check(label, condition, detail=""):
    print(f"  {'ok  ' if condition else 'FAIL'} {label}  {detail if not condition else ''}")
    if not condition:
        failures.append(label)


def fake(prompt, model, params=None):
    sent.append(prompt)
    vivify_core._note_usage(cost_usd=0.40)
    return "ok"


def main():
    vivify_core.TRANSPORTS["claude"] = fake
    with tempfile.TemporaryDirectory() as d:
        log = Path(d) / "usage.jsonl"
        log.write_text(json.dumps({"at": "2026-01-01T00:00:00+00:00", "cost_usd": 99}) + "\n")
        os.environ.update(VIVIFY_USAGE_LOG=str(log), VIVIFY_BUDGET_USD="1.00",
                          VIVIFY_BUDGET_SINCE="2026-06-01T00:00:00+00:00")
        check("old lines before SINCE do not count", llm_call_model("a", "claude:x") == "ok")
        llm_call_model("b", "claude:x")
        llm_call_model("c", "claude:x")                     # spent now 1.20
        try:
            llm_call_model("d", "claude:x")
            check("over the cap raises BudgetExceeded", False)
        except BudgetExceeded as e:
            check("over the cap raises BudgetExceeded", "cap $1.00" in str(e), str(e))
        check("refused call never reached the transport", "d" not in sent)
        check("BudgetExceeded is an LLMUnavailable", issubclass(BudgetExceeded, LLMUnavailable))
        check("budget_spent sums since SINCE", abs(vivify_core.budget_spent(os.environ["VIVIFY_BUDGET_SINCE"]) - 1.20) < 1e-9)
        del os.environ["VIVIFY_BUDGET_SINCE"]
        try:
            llm_call_model("e", "claude:x")
            check("cap without SINCE refuses", False)
        except BudgetExceeded:
            check("cap without SINCE refuses", True)
        del os.environ["VIVIFY_BUDGET_USD"]
        check("no cap set = no check", llm_call_model("f", "claude:x") == "ok")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()

# llm: claude-opus-5-5 | 2026-11-07 | repos/vivify-operators/tests/test_budget_cap.py | created — spend cap refuses calls at VIVIFY_BUDGET_USD
