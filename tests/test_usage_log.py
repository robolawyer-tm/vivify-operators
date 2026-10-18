#!/usr/bin/env python3
"""Focused test: every LLM call writes one usage line, the same shape for every backend.

- claude: the lean worker asks for --output-format json and reads tokens and cost
  from it; the reply text is still returned as before
- an OpenAI-compatible provider and Gemini report their own usage fields, mapped
  to the same names (input, output, cache_read, thinking)
- a failed call is logged with ok=false and the error, and still raises
- VIVIFY_RUN_TAG labels lines; VIVIFY_USAGE_LOG=off writes nothing

No real calls — subprocess.run and urlopen are stubbed.

Run standalone: python3 tests/test_usage_log.py  (exit 0 = pass)
"""
import io
import os
import sys
import json
import tempfile
import subprocess
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "lib"))

import vivify_core
from vivify_core import llm_call_model, LLMUnavailable

failures = []


def check(label, condition, detail=""):
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}  {detail}")
        failures.append(label)


log = Path(tempfile.mkdtemp()) / "usage.jsonl"
saved = {k: os.environ.get(k) for k in ("VIVIFY_USAGE_LOG", "VIVIFY_RUN_TAG", "GEMINI_API_KEY", "PRIVACY_GATE")}
os.environ.update(VIVIFY_USAGE_LOG=str(log), VIVIFY_RUN_TAG="t1", GEMINI_API_KEY="k", PRIVACY_GATE="off")


def lines():
    return [json.loads(l) for l in log.read_text().splitlines()] if log.exists() else []


CLAUDE_OUT = json.dumps({"result": "ok", "is_error": False, "total_cost_usd": 0.0047,
                         "usage": {"input_tokens": 2, "output_tokens": 4,
                                   "cache_creation_input_tokens": 574, "cache_read_input_tokens": 0,
                                   "output_tokens_details": {"thinking_tokens": 0}}})
argv_seen = []
orig_run, orig_open = subprocess.run, urllib.request.urlopen
try:
    def fake_run(cmd, **kw):
        argv_seen.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, stdout=CLAUDE_OUT, stderr="")
    subprocess.run = fake_run
    reply = llm_call_model("PROMPT", "claude:claude-opus-5-5")
    rec = lines()[-1]
    check("claude reply text unchanged", reply == "ok", reply)
    check("claude asks for JSON output", "--output-format" in argv_seen[-1] and "json" in argv_seen[-1])
    check("claude usage mapped",
          (rec["input"], rec["output"], rec["cache_write"], rec["cache_read"], rec["cost_usd"])
          == (2, 4, 574, 0, 0.0047), rec)
    check("line carries tag, backend, model, worker, ok",
          (rec["tag"], rec["backend"], rec["model"], rec["worker"], rec["ok"])
          == ("t1", "claude", "claude-opus-5-5", "lean", True), rec)

    subprocess.run = lambda cmd, **kw: subprocess.CompletedProcess(cmd, 1, stdout="", stderr="boom")
    try:
        llm_call_model("PROMPT", "claude:claude-opus-5-5")
        check("failed call still raises", False, "no error")
    except LLMUnavailable:
        rec = lines()[-1]
        check("failed call logged ok=false with error", rec["ok"] is False and "boom" in rec["error"], rec)
        check("failed call carries no stale usage", rec["input"] is None, rec)

    vivify_core.TRANSPORTS["fakeprov"] = vivify_core._make_openai_transport("fakeprov", "https://x", "GEMINI_API_KEY")
    urllib.request.urlopen = lambda req, timeout=None: io.BytesIO(json.dumps(
        {"choices": [{"message": {"content": "ok"}}],
         "usage": {"prompt_tokens": 11, "completion_tokens": 3,
                   "prompt_tokens_details": {"cached_tokens": 5}}}).encode())
    llm_call_model("PROMPT", "fakeprov:some-model")
    rec = lines()[-1]
    check("openai-compatible usage mapped",
          (rec["backend"], rec["input"], rec["output"], rec["cache_read"]) == ("fakeprov", 11, 3, 5), rec)

    urllib.request.urlopen = lambda req, timeout=None: io.BytesIO(json.dumps(
        {"candidates": [{"content": {"parts": [{"text": "ok"}]}}],
         "usageMetadata": {"promptTokenCount": 9, "candidatesTokenCount": 2, "thoughtsTokenCount": 7}}).encode())
    llm_call_model("PROMPT", "gemini:gemini-3.8-flash")
    rec = lines()[-1]
    check("gemini usage mapped",
          (rec["input"], rec["output"], rec["thinking"]) == (9, 2, 7), rec)

    n = len(lines())
    os.environ["VIVIFY_USAGE_LOG"] = "off"
    llm_call_model("PROMPT", "gemini:gemini-3.8-flash")
    os.environ["VIVIFY_USAGE_LOG"] = str(log)
    check("VIVIFY_USAGE_LOG=off writes nothing", len(lines()) == n)
finally:
    subprocess.run, urllib.request.urlopen = orig_run, orig_open
    vivify_core.TRANSPORTS.pop("fakeprov", None)
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v

print()
if failures:
    print(f"FAILED: {len(failures)} check(s) — {', '.join(failures)}")
    sys.exit(1)
print("All usage-log checks passed.")

# llm: claude-opus-5-5 | 2026-10-18 | repos/vivify-operators/tests/test_usage_log.py | created — one usage line per call, same shape across claude (JSON output), openai-compatible and gemini; failures logged; tag and off switch; subprocess and urlopen stubbed
