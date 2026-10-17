#!/usr/bin/env python3
"""
probe_providers.py — ask each LLM provider directly what works right now.

Web research answers "is model X still available?" from web pages, and on
2026-10-17 it got both test questions wrong: it called a retired Groq model
"still offered", and it put the Gemini free tier at 1,500 requests a day when
the quota error itself said 20. The provider's own API is the ground truth, so
this script asks it:

  1. KEY     — is the provider's key in the environment (name only, never value)
  2. MODELS  — the provider's live model list, diffed against the last snapshot,
               so a retired model shows up as `removed`
  3. CALLS   — a one-word call ("Reply with the single word ok") to each model the
               pipeline routes to that provider (config/model_map.json), plus any
               --call extras and the DEFAULT_CALLS below
  4. QUOTA   — what a refusal says about limits (Gemini's quotaId/value, the
               OpenRouter credit balance)

Writes one snapshot, probes/providers.json, overwritten each run (the previous
one is read first for the diff). Key values are scrubbed from every stored string.
Model lists and statuses are public facts, so the snapshot may be published.

Costs: one models-list request per provider, one tiny call per probed model,
one Tavily search (of 1,000/month). On a free Gemini key each call is one of
20 per day per model.

Usage:
    source <(unseal_it -o - ~/.secrets/keys.env.age)    # with set -a, or export
    ./probe_providers.py                      # probe all, write snapshot
    ./probe_providers.py --only groq,gemini   # some providers
    ./probe_providers.py --call nvidia:moonshotai/kimi-k2.6
    ./probe_providers.py --no-calls           # model lists only, no LLM calls
    ./probe_providers.py --dry-run            # probe, print, write nothing
"""

import os
import sys
import json
import time
import argparse
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "lib"))
from vivify_core import (llm_call_model, read_json, write_json, add_dry_run_arg,
                         split_backend, LLMUnavailable)

SNAPSHOT = ROOT / "probes" / "providers.json"
PROBE_PROMPT = "Reply with the single word ok"
UA = {"User-Agent": "vivify-operators/1.0"}   # Cloudflare 403s the urllib default

# Bespoke backends, outside config/providers.json: their key and models endpoint.
BESPOKE = {
    "gemini": {"env_key": "GEMINI_API_KEY",
               "models_url": "https://generativelanguage.googleapis.com/v1beta/models?pageSize=1000"},
}
# A model worth one call even when nothing routes to it yet.
DEFAULT_CALLS = ["gemini:gemini-flash-latest"]


def scrub(text, secrets):
    """Remove every key value from a string before it is printed or stored."""
    text = str(text)
    for s in secrets:
        if s:
            text = text.replace(s, "<redacted>")
    return text


def models_url(base_url):
    """OpenAI-compatible chat URL -> its models-list URL."""
    return base_url.rsplit("/chat/completions", 1)[0] + "/models"


def load_providers():
    """{name: {env_key, models_url}} for every provider the pipeline can route to."""
    cfg = read_json(ROOT / "config" / "providers.json")
    out = {name: {"env_key": c["env_key"], "models_url": models_url(c["base_url"])}
           for name, c in cfg.items() if not name.startswith("_")}
    out.update(BESPOKE)
    return out


def http_get(url, headers):
    """(status, parsed JSON or short error text). Never raises."""
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={**UA, **headers}),
                                    timeout=30) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:300]
    except (OSError, json.JSONDecodeError) as e:
        return "error", str(e)[:300]


def list_models(name, cfg, key):
    """Live model ids for one provider, or an error record."""
    if name == "gemini":
        status, body = http_get(cfg["models_url"], {"x-goog-api-key": key})
        if status == 200:
            ids = [m["name"].split("/", 1)[1] for m in body.get("models", [])
                   if "generateContent" in m.get("supportedGenerationMethods", [])]
            return {"status": 200, "ids": sorted(ids)}
    else:
        status, body = http_get(cfg["models_url"], {"Authorization": f"Bearer {key}"})
        if status == 200:
            return {"status": 200, "ids": sorted(m["id"] for m in body.get("data", []))}
    return {"status": status, "error": body if isinstance(body, str) else str(body)[:300]}


def diff_models(prev_ids, ids):
    """What appeared and disappeared since the last snapshot (None = no baseline)."""
    if prev_ids is None:
        return None
    return {"added": sorted(set(ids) - set(prev_ids)),
            "removed": sorted(set(prev_ids) - set(ids))}


def gemini_quota(error_text):
    """The limit a Gemini refusal hit, from vivify_core's ' quota=<id>:<value>' tag."""
    marker = " quota="
    if marker not in error_text:
        return None
    quota_id, _, limit = error_text.split(marker, 1)[1].split()[0].rpartition(":")
    return {"quota_id": quota_id, "limit": limit}


def probe_call(model_id):
    """One tiny call through the pipeline's own transport."""
    t = time.time()
    try:
        out = llm_call_model(PROBE_PROMPT, model_id, sensitive=False)
        return {"ok": out.strip().lower().rstrip(".") == "ok", "reply": out[:40],
                "seconds": round(time.time() - t, 1)}
    except Exception as e:      # LLMUnavailable, ValueError for an unknown backend, …
        return {"ok": False, "error": f"{type(e).__name__}: {str(e)[:300]}",
                "seconds": round(time.time() - t, 1)}


def routed_models():
    """backend -> model ids that config/model_map.json routes to it (claude excluded)."""
    routes = {}
    for cap, model in read_json(ROOT / "config" / "model_map.json").items():
        if cap.startswith("_") or ":" not in str(model):
            continue
        backend, _ = split_backend(model)
        routes.setdefault(backend, set()).add(model)
    return routes


def probe_tavily(key):
    body = json.dumps({"query": "LLM API free tier", "max_results": 1}).encode()
    req = urllib.request.Request("https://api.tavily.com/search", data=body,
                                 headers={**UA, "Content-Type": "application/json",
                                          "Authorization": f"Bearer {key}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return {"ok": True, "results": len(json.load(r).get("results", []))}
    except urllib.error.HTTPError as e:
        return {"ok": False, "error": f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:200]}"}
    except OSError as e:
        return {"ok": False, "error": str(e)[:200]}


def run(only=None, extra_calls=(), calls=True, previous=None):
    providers = load_providers()
    secrets = [os.environ.get(c["env_key"], "") for c in providers.values()]
    secrets.append(os.environ.get("TAVILY_API_KEY", ""))
    previous = previous or {}
    routes = routed_models()
    wanted = {}
    for m in list(DEFAULT_CALLS) + list(extra_calls):
        wanted.setdefault(split_backend(m)[0], set()).add(m)
    for backend, models in routes.items():
        wanted.setdefault(backend, set()).update(models)

    snap = {"probed": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "prompt": PROBE_PROMPT, "providers": {}}
    for name, cfg in sorted(providers.items()):
        if only and name not in only:
            continue
        key = os.environ.get(cfg["env_key"])
        rec = {"key": cfg["env_key"] + (" present" if key else " missing")}
        if key:
            models = list_models(name, cfg, key)
            if "ids" in models:
                prev = previous.get("providers", {}).get(name, {}).get("models", {}).get("ids")
                models["count"] = len(models["ids"])
                models["changes"] = diff_models(prev, models["ids"])
            rec["models"] = models
            if calls:
                rec["calls"] = {}
                for m in sorted(wanted.get(name, ())):
                    result = probe_call(m)
                    if name == "gemini" and "error" in result:
                        quota = gemini_quota(result["error"])
                        if quota:
                            result["quota"] = quota
                    rec["calls"][m] = result
            if name == "openrouter":
                status, body = http_get("https://openrouter.ai/api/v1/credits",
                                        {"Authorization": f"Bearer {key}"})
                if status == 200:
                    rec["credits"] = body.get("data")
                if "ids" in models:
                    rec["free_models"] = [i for i in models["ids"] if i.endswith(":free")]
        rec["probed"] = snap["probed"]      # kept per provider: --only merges into older snapshots
        snap["providers"][name] = rec
    if not only or "tavily" in only:
        key = os.environ.get("TAVILY_API_KEY")
        snap["providers"]["tavily"] = ({"key": "TAVILY_API_KEY present", "search": probe_tavily(key),
                                        "probed": snap["probed"]}
                                       if key else {"key": "TAVILY_API_KEY missing"})
    return json.loads(scrub(json.dumps(snap), secrets))


def summary(snap):
    lines = [f"probed {snap['probed']}"]
    for name, rec in snap["providers"].items():
        if "missing" in rec["key"]:
            lines.append(f"  {name:<11} no key")
            continue
        if name == "tavily":
            s = rec["search"]
            lines.append(f"  {name:<11} search {'ok' if s['ok'] else 'FAIL ' + s['error'][:80]}")
            continue
        m = rec.get("models", {})
        line = f"  {name:<11} models: {m.get('count', 'FAIL ' + str(m.get('status')))}"
        ch = m.get("changes")
        if ch and (ch["added"] or ch["removed"]):
            line += f"  (+{len(ch['added'])} / -{len(ch['removed'])} since last probe)"
        if "credits" in rec:
            line += f"  credits {rec['credits']}"
        if "free_models" in rec:
            line += f"  free: {len(rec['free_models'])}"
        lines.append(line)
        for model, r in rec.get("calls", {}).items():
            state = "ok" if r["ok"] else "FAIL " + " ".join(r.get("error", repr(r.get("reply"))).split())[:90]
            quota = f"  quota {r['quota']}" if "quota" in r else ""
            lines.append(f"      call {model}: {state} ({r['seconds']}s){quota}")
        for model in (ch or {}).get("removed", []):
            lines.append(f"      removed: {model}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--only", help="comma-separated providers (e.g. groq,gemini,tavily)")
    ap.add_argument("--call", action="append", default=[],
                    help="extra backend:model to call once (repeatable)")
    ap.add_argument("--no-calls", action="store_true", help="model lists only, no LLM calls")
    ap.add_argument("--out", default=str(SNAPSHOT), help="snapshot path")
    add_dry_run_arg(ap)
    args = ap.parse_args()
    out = Path(args.out)
    previous = read_json(out) if out.exists() else {}
    only = set(args.only.split(",")) if args.only else None
    snap = run(only=only, extra_calls=args.call, calls=not args.no_calls, previous=previous)
    print(summary(snap))
    if only and previous:
        # a partial probe keeps the providers it did not touch
        merged = dict(previous.get("providers", {}))
        merged.update(snap["providers"])
        snap["providers"] = merged
    write_json(out, snap, dry_run=args.dry_run)
    if not args.dry_run:
        print(f"wrote {out}")


if __name__ == "__main__":
    main()

# llm: claude-opus-5-5 | 2026-10-17 | repos/vivify-operators/probe_providers.py | created — asks each provider's own API which keys, models, calls and quotas work now; diffs model lists against the last snapshot to catch retirements; scrubs key values; writes probes/providers.json
# llm: claude-opus-5-5 | 2026-10-17 | repos/vivify-operators/probe_providers.py | quota read from vivify_core's one-line quota= tag; summary collapses whitespace in errors
