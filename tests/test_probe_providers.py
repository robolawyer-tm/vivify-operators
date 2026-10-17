#!/usr/bin/env python3
"""Focused test: probe_providers reports what providers say, and never stores a key.

- models URL is derived from each provider's chat URL
- a model missing since the last snapshot shows as removed (the retirement check)
- Gemini's quota error yields quota_id + limit
- key values are scrubbed from every stored string, even when an error echoes one
- a missing key is reported by name and nothing is called

No network — http_get, probe_call and probe_tavily are stubbed.

Run standalone: python3 tests/test_probe_providers.py  (exit 0 = pass)
"""
import os
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "lib"))

import probe_providers as pp

failures = []


def check(label, condition, detail=""):
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}  {detail}")
        failures.append(label)


# --- pure helpers -------------------------------------------------------------
check("models URL from chat URL",
      pp.models_url("https://api.groq.com/openai/v1/chat/completions")
      == "https://api.groq.com/openai/v1/models")
check("no baseline -> no diff", pp.diff_models(None, ["a"]) is None)
check("retired model shows as removed",
      pp.diff_models(["a", "llama-3.3"], ["a", "gpt-oss"]) == {"added": ["gpt-oss"], "removed": ["llama-3.3"]})
err = "LLMUnavailable: gemini request failed: HTTP 429: You exceeded your current quota quota=GenerateRequestsPerDayPerProjectPerModel-FreeTier:20"
check("gemini quota read from the error body",
      pp.gemini_quota(err) == {"quota_id": "GenerateRequestsPerDayPerProjectPerModel-FreeTier", "limit": "20"},
      pp.gemini_quota(err))
check("scrub removes key values", pp.scrub("bad key sk-SECRET123 rejected", ["sk-SECRET123"]) == "bad key <redacted> rejected")

# --- one full run, stubbed ----------------------------------------------------
SECRET = "gsk_TEST_SECRET_VALUE"
saved_env = {k: os.environ.get(k) for k in ("GROQ_API_KEY", "GEMINI_API_KEY", "TAVILY_API_KEY")}
os.environ["GROQ_API_KEY"] = SECRET
os.environ.pop("GEMINI_API_KEY", None)
os.environ.pop("TAVILY_API_KEY", None)

calls = []
orig = (pp.http_get, pp.probe_call, pp.load_providers, pp.routed_models)
pp.load_providers = lambda: {"groq": {"env_key": "GROQ_API_KEY", "models_url": "https://x/models"},
                             "gemini": pp.BESPOKE["gemini"]}
pp.routed_models = lambda: {"groq": {"groq:openai/gpt-oss-120b"}}
pp.http_get = lambda url, headers: (200, {"data": [{"id": "openai/gpt-oss-120b"}, {"id": "qwen/qwen3.8-27b"}]})


def fake_call(model):
    calls.append(model)
    return {"ok": False, "error": f"LLMUnavailable: key {SECRET} invalid", "seconds": 0.1}


pp.probe_call = fake_call
try:
    previous = {"providers": {"groq": {"models": {"ids": ["llama-3.3-70b-versatile", "openai/gpt-oss-120b"]}}}}
    snap = pp.run(previous=previous)
    groq = snap["providers"]["groq"]
    check("routed model was called", calls == ["groq:openai/gpt-oss-120b"], calls)
    check("model count recorded", groq["models"]["count"] == 2, groq["models"])
    check("retirement caught against the previous snapshot",
          groq["models"]["changes"]["removed"] == ["llama-3.3-70b-versatile"], groq["models"]["changes"])
    check("key value never stored", SECRET not in json.dumps(snap))
    check("echoed key scrubbed in the call error",
          "<redacted>" in groq["calls"]["groq:openai/gpt-oss-120b"]["error"])
    check("missing gemini key reported by name, nothing called",
          snap["providers"]["gemini"] == {"key": "GEMINI_API_KEY missing", "probed": snap["probed"]}
          and not any(c.startswith("gemini:") for c in calls), snap["providers"]["gemini"])
    check("missing tavily key reported", snap["providers"]["tavily"]["key"] == "TAVILY_API_KEY missing")
    check("summary prints the removed model", "removed: llama-3.3-70b-versatile" in pp.summary(snap))

    calls.clear()
    snap = pp.run(calls=False, previous=previous)
    check("--no-calls makes no LLM calls", calls == [] and "calls" not in snap["providers"]["groq"])
finally:
    pp.http_get, pp.probe_call, pp.load_providers, pp.routed_models = orig
    for k, v in saved_env.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v

print()
if failures:
    print(f"FAILED: {len(failures)} check(s) — {', '.join(failures)}")
    sys.exit(1)
print("All probe-providers checks passed.")

# llm: claude-opus-5-5 | 2026-10-17 | repos/vivify-operators/tests/test_probe_providers.py | created — models URL, retirement diff, gemini quota parse, key scrubbing (incl. echoed in errors), missing keys, --no-calls; network stubbed
