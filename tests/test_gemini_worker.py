#!/usr/bin/env python3
"""Focused test: the Gemini worker is plain, and it waits out rate limits.

- gemini: sends no tools, so an operator routed there cannot search the web (a
  replay reads steps 1..N only; a search could find how the case ended).
  gemini_search: is the only route that turns Google Search on.
- A 429 (too many requests this minute) or 503 (servers busy) waits and retries,
  using Google's own retryDelay when given; a per-day quota, any other error, or
  running out of retries raises LLMUnavailable so a run still stops cleanly.

No real calls — urlopen and sleep are stubbed.

Run standalone: python3 tests/test_gemini_worker.py  (exit 0 = pass)
"""
import io
import os
import sys
import json
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "lib"))

import vivify_core
from vivify_core import LLMUnavailable, _gemini_wait_seconds, _gemini_request_with_wait

failures = []


def check(label, condition, detail=""):
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}  {detail}")
        failures.append(label)


def http_error(code, body):
    return urllib.error.HTTPError("https://x", code, "err", {}, io.BytesIO(body.encode()))


OK = json.dumps({"candidates": [{"content": {"parts": [{"text": "ok"}]}}]})
RETRY_27 = json.dumps({"error": {"details": [{"retryDelay": "27s"}]}})
PER_DAY = json.dumps({"error": {"details": [{"violations": [
    {"quotaId": "GenerateRequestsPerDayPerProjectPerModel-FreeTier"}]}]}})


class FakeOpen:
    """Plays a script of responses: an HTTPError to raise, or a JSON string to return."""
    def __init__(self, script):
        self.script = list(script)
        self.requests = []

    def __call__(self, req, timeout=None):
        self.requests.append(req)
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return io.BytesIO(item.encode())


# --- wait rules ---------------------------------------------------------------
check("429 uses Google's retryDelay (+1s)", _gemini_wait_seconds(429, RETRY_27, 0) == 28)
check("503 without a delay waits 30s, then 60s",
      _gemini_wait_seconds(503, "", 0) == 30 and _gemini_wait_seconds(503, "", 1) == 60)
check("a per-day quota gives up at once", _gemini_wait_seconds(429, PER_DAY, 0) is None)
check("other errors give up at once", _gemini_wait_seconds(400, "", 0) is None)
import os
os.environ["GEMINI_503_RETRIES"] = "1"
check("GEMINI_503_RETRIES=1: one 503 retry, then give up; 429 unaffected",
      _gemini_wait_seconds(503, "", 0) == 30 and _gemini_wait_seconds(503, "", 1) is None
      and _gemini_wait_seconds(429, "", 1) == 60)
del os.environ["GEMINI_503_RETRIES"]
check("gives up after the last retry",
      _gemini_wait_seconds(429, "", vivify_core.GEMINI_RETRIES) is None)
check("never waits longer than the cap",
      _gemini_wait_seconds(429, json.dumps({"error": {"details": [{"retryDelay": "900s"}]}}), 0)
      == vivify_core.GEMINI_MAX_WAIT)

# --- request loop -------------------------------------------------------------
original = urllib.request.urlopen
try:
    waits = []
    urllib.request.urlopen = FakeOpen([http_error(429, RETRY_27), http_error(503, ""), OK])
    payload = _gemini_request_with_wait("REQ", sleep=waits.append)
    check("recovers after a 429 and a 503", payload["candidates"][0]["content"]["parts"][0]["text"] == "ok")
    check("waited 28s then 60s", waits == [28, 60], waits)

    urllib.request.urlopen = FakeOpen([http_error(429, "")] * (vivify_core.GEMINI_RETRIES + 1))
    try:
        _gemini_request_with_wait("REQ", sleep=lambda s: None)
        check("raises LLMUnavailable when retries run out", False, "no error")
    except LLMUnavailable as e:
        check("raises LLMUnavailable when retries run out", "429" in str(e), str(e))

    urllib.request.urlopen = FakeOpen([http_error(429, PER_DAY)])
    waits = []
    try:
        _gemini_request_with_wait("REQ", sleep=waits.append)
        check("per-day quota stops without waiting", False, "no error")
    except LLMUnavailable as e:
        check("per-day quota stops without waiting", waits == [], waits)
        check("the error names the quota it hit",
              "quota=GenerateRequestsPerDayPerProjectPerModel-FreeTier" in str(e), str(e))

    # --- plain vs search route ------------------------------------------------
    os.environ.setdefault("GEMINI_API_KEY", "test-key")
    fake = FakeOpen([OK, OK])
    urllib.request.urlopen = fake
    vivify_core.TRANSPORTS["gemini"]("PROMPT", "gemini-3.8-flash")
    vivify_core.TRANSPORTS["gemini_search"]("PROMPT", "gemini-3.8-flash")
    plain, search = (json.loads(r.data) for r in fake.requests)
    check("gemini: sends no tools", "tools" not in plain, plain)
    check("gemini_search: turns Google Search on", search.get("tools") == [{"google_search": {}}], search)
finally:
    urllib.request.urlopen = original

print()
if failures:
    print(f"FAILED: {len(failures)} check(s) — {', '.join(failures)}")
    sys.exit(1)
print("All gemini-worker checks passed.")

# llm: claude-opus-5-5 | 2026-10-17 | repos/vivify-operators/tests/test_gemini_worker.py | created — gemini: plain vs gemini_search: grounded, wait-and-retry on 429/503 (retryDelay, per-day quota, cap, give-up), urlopen and sleep stubbed
# llm: claude-opus-5-5 | 2026-10-17 | repos/vivify-operators/tests/test_gemini_worker.py | per-day refusal must name its quota in the error
# llm: claude-opus-5-5 | 2026-10-25 | repos/vivify-operators/tests/test_gemini_worker.py | GEMINI_503_RETRIES check
