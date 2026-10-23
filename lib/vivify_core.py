"""
vivify_core — autovivification engine

Perl-style hash-of-hashes in Python. Builds nested JSON structures from
key paths without requiring a predefined schema. Structure emerges from data.
"""

import json
from collections import Counter, defaultdict
from pathlib import Path


def autovivify():
    """Return a deeply nestable defaultdict — the core autovivification primitive."""
    return defaultdict(autovivify)


def deep_update(base, update):
    """Merge update into base recursively, creating nested keys as needed.

    - Existing keys are updated in place, not overwritten at the top level
    - New keys are created at any depth without prior declaration
    - Leaf values (non-dict) are replaced by the incoming value
    """
    for key, value in update.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            deep_update(base[key], value)
        else:
            base[key] = value
    return base


def to_dict(obj):
    """Recursively convert autovivified defaultdicts to plain dicts for serialization.

    - Required before JSON serialization — defaultdict is not JSON-serializable
    - Safe to call on plain dicts (no-op)
    - Handles arbitrary nesting depth
    """
    if isinstance(obj, defaultdict):
        return {k: to_dict(v) for k, v in obj.items()}
    elif isinstance(obj, dict):
        return {k: to_dict(v) for k, v in obj.items()}
    return obj


def write_json(path, data, indent=2, dry_run=False):
    """Write data to a JSON file, creating parent directories as needed.

    - path: str or Path
    - data: dict (will be serialized via to_dict first)
    - indent: pretty-print indent level
    - dry_run: if True, print what would be written without touching the filesystem
    """
    path = Path(path)
    if dry_run:
        print(f"[DRY RUN] would write to {path}:")
        print(json.dumps(to_dict(data), indent=indent))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(to_dict(data), f, indent=indent)


def add_dry_run_arg(parser):
    """Add --dry-run to an argparse parser — standard facility for scripts with side effects.

    Usage:
        add_dry_run_arg(parser)
        args = parser.parse_args()
        write_json(path, data, dry_run=args.dry_run)
    """
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be written or published without committing any changes"
    )


def read_json(path):
    """Read a JSON file and return as a plain dict.

    - Returns empty dict if file does not exist
    - Raises JSONDecodeError if file is malformed
    """
    path = Path(path)
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


class LLMUnavailable(RuntimeError):
    """The claude CLI itself failed — quota exhausted, auth lost, or not installed.

    - Distinct from a per-inference content error (bad/missing JSON in a good response)
    - Signals that retrying further operators or inferences is futile until resolved
    - Callers running batches should catch this and abort rather than burn calls
    """


class PrivacyGateError(RuntimeError):
    """A sensitivity-tagged call was routed to a non-local backend while the
    privacy gate is on — data would leave the box. Blocked before any send.

    - Raised when sensitive=True AND backend not local AND the gate is not
      explicitly relaxed (PRIVACY_GATE is anything but 'off' — including unset)
    - Fail-closed by default: an unset gate BLOCKS sensitive off-box calls. The dev
      relaxation is the explicit opt-out PRIVACY_GATE=off, not the absence of a value
    - See project_model_routing.md
    """


class CoordinateValidationError(ValueError):
    """An operator's LLM output failed the inbound validation gate — an unknown
    enum value, an out-of-range number, a wrong type, or an over-long string
    (the injection guard). The counterpart to PrivacyGateError: that one guards
    what LEAVES the box, this one guards what a (possibly distal, untrusted) model
    is allowed to put INTO the inference store.

    - Fail-closed: a rejected result must NOT be merged; the caller quarantines it
    - Distinct from LLMUnavailable (transport down) — here the response arrived
      but its content is not a legal coordinate
    - Raised by validate_coordinates() against config/coordinates.json
    """


# The lean worker: a claude -p call stripped of the Claude Code harness. Without
# these flags every call carried ~24K tokens of agent system prompt, tool
# definitions and project memory around a ~1-2K classification, and the memory
# primed the instrument with the project's own notes. `--bare` would go further
# but needs ANTHROPIC_API_KEY, and these calls run on Claude Code's OAuth login.
WORKER_SYSTEM_PROMPT = ("You read texts and answer exactly in the format the "
                        "user's message asks for. Use only what the message contains.")
LEAN_WORKER_FLAGS = [
    "--tools", "",                                   # no tools at all
    "--system-prompt", WORKER_SYSTEM_PROMPT,         # replaces the agent prompt
    "--setting-sources", "",                         # no user/project/local settings
    "--settings", '{"autoMemoryEnabled": false}',    # no MEMORY.md in context
    "--strict-mcp-config",                           # no MCP servers
    "--disable-slash-commands",                      # no skills
    "--no-session-persistence",                      # no session file per call
]


def claude_worker_mode():
    """'lean' (default) or 'full' — VIVIFY_CLAUDE_WORKER=full restores the old
    harnessed call, kept for parity checks against readings made before the switch."""
    import os
    mode = os.environ.get("VIVIFY_CLAUDE_WORKER", "lean").strip().lower()
    if mode not in ("lean", "full"):
        raise ValueError(f"VIVIFY_CLAUDE_WORKER must be 'lean' or 'full', not {mode!r}")
    return mode


def claude_cmd(prompt, model, *extra):
    """The claude CLI argv for one call, lean unless VIVIFY_CLAUDE_WORKER=full."""
    cmd = ["claude", "-p", prompt, "--model", model, *extra]
    if claude_worker_mode() == "lean":
        cmd += LEAN_WORKER_FLAGS
    return cmd


# --- usage log -----------------------------------------------------------------
# One JSON line per LLM call, the same shape for every backend, so runs and
# providers can be compared by one ruler: tokens in / out / cached, seconds, ok.
# Transports report what their provider says (_note_usage); llm_call_model times
# the call and writes the line. VIVIFY_USAGE_LOG=off turns it off; VIVIFY_RUN_TAG
# labels the calls of one run (e.g. "residue_try5").
USAGE_FIELDS = ("input", "output", "cache_write", "cache_read", "thinking", "cost_usd")
_last_usage = {}


def usage_log_path():
    import os
    p = os.environ.get("VIVIFY_USAGE_LOG", "")
    if p.lower() == "off":
        return None
    return Path(p) if p else Path.home() / ".local" / "state" / "vivify-operators" / "usage.jsonl"


def _note_usage(**fields):
    """Called by a transport with what its provider reported (missing = unknown)."""
    _last_usage.update({k: v for k, v in fields.items() if v is not None})


def _write_usage(backend, model, seconds, prompt_chars, ok, error=None):
    import os
    path = usage_log_path()
    if path is None:
        return
    from datetime import datetime, timezone
    rec = {"at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "tag": os.environ.get("VIVIFY_RUN_TAG"), "backend": backend, "model": model,
           "ok": ok, "seconds": round(seconds, 2), "prompt_chars": prompt_chars}
    rec.update({k: _last_usage.get(k) for k in USAGE_FIELDS})
    if backend == "claude":
        rec["worker"] = claude_worker_mode()
    if error:
        rec["error"] = str(error)[:200]
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a") as f:
            f.write(json.dumps(rec) + "\n")
    except OSError:
        pass                    # the log must never stop a run


def _claude_transport(prompt, model, params=None):
    """Transport for the claude: backend — the claude CLI subprocess.

    No API key — uses Claude Code's own authentication. The original (and default)
    transport; bare model ids with no backend prefix route here. `params` (sampling
    knobs like temperature) are ignored — the `claude -p` CLI exposes no per-call
    sampling, so claude is not used as a diversity source in the quorum. Runs as
    the lean worker (claude_cmd) unless VIVIFY_CLAUDE_WORKER=full.
    """
    import subprocess
    result = subprocess.run(
        claude_cmd(prompt, model, "--output-format", "json"),
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        raise LLMUnavailable(result.stderr.strip() or f"claude exited {result.returncode}")
    try:
        out = json.loads(result.stdout)
    except json.JSONDecodeError:
        return result.stdout.strip()        # an older CLI without JSON output
    u = out.get("usage") or {}
    _note_usage(input=u.get("input_tokens"), output=u.get("output_tokens"),
                cache_write=u.get("cache_creation_input_tokens"),
                cache_read=u.get("cache_read_input_tokens"),
                thinking=(u.get("output_tokens_details") or {}).get("thinking_tokens"),
                cost_usd=out.get("total_cost_usd"))
    if out.get("is_error"):
        raise LLMUnavailable(f"claude error: {str(out.get('result'))[:200]}")
    return str(out.get("result", "")).strip()


def _make_openai_transport(provider, base_url, env_key, extra_headers=None):
    """Build a transport for ANY OpenAI-compatible chat-completions endpoint.

    The whole distal team (deepseek, nvidia, openrouter, groq, mistral, …) is just
    instances of this — only base_url and env_key differ. Defined once, registered
    per provider from config/providers.json (see _load_providers).

    - Reads the key from `env_key` in the environment (sourced from the sealed
      keys.env.age — see project secrets seam). Key rides in the Authorization
      header, never in the prompt body.
    - Remote backend: excluded from LOCAL_BACKENDS, so the privacy gate blocks
      sensitivity-tagged data from reaching it when PRIVACY_GATE is on.
    - Raises LLMUnavailable on missing key, network failure, or malformed response.
    """
    def _transport(prompt, model, params=None):
        import os
        import urllib.request
        import urllib.error
        key = os.environ.get(env_key)
        if not key:
            raise LLMUnavailable(f"{env_key} not set — source the sealed keys.env first")
        payload_obj = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }
        # OpenAI-compatible sampling knobs go straight in the body (temperature,
        # top_p, seed, max_tokens) — this is how the quorum gets its diversity.
        for k in ("temperature", "top_p", "seed", "max_tokens"):
            if params and params.get(k) is not None:
                payload_obj[k] = params[k]
        body = json.dumps(payload_obj).encode()
        # Explicit User-Agent: some providers (e.g. Groq) sit behind Cloudflare, which
        # blocks the default 'Python-urllib/x' UA with a 403 (error 1010). Any real UA passes.
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                   "User-Agent": "vivify-operators/1.0"}
        if extra_headers:
            headers.update(extra_headers)
        req = urllib.request.Request(base_url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                payload = json.loads(resp.read())
        except OSError as e:
            # URLError, read TimeoutError, and socket errors are all OSError —
            # a slow free-tier model that times out must fail-soft, not crash.
            raise LLMUnavailable(f"{provider} request failed: {e}")
        u = payload.get("usage") or {}
        _note_usage(input=u.get("prompt_tokens"), output=u.get("completion_tokens"),
                    cache_read=(u.get("prompt_tokens_details") or {}).get("cached_tokens"),
                    thinking=(u.get("completion_tokens_details") or {}).get("reasoning_tokens"))
        try:
            return payload["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError) as e:
            raise LLMUnavailable(f"{provider} response malformed: {e}")
    return _transport


def _ollama_transport(prompt, model, params=None):
    """Transport for the ollama: backend — a LOCAL Ollama server. Data never leaves the box.

    - Talks to the Ollama HTTP API (default http://localhost:11434, override via
      OLLAMA_HOST; a host without scheme is assumed http). No API key — local service.
    - This is the privacy-safe tier: 'ollama' is in LOCAL_BACKENDS, so sensitivity-
      tagged data may route here even when the privacy gate is on.
    - `params` sampling knobs go in Ollama's "options" (temperature/top_p/seed,
      max_tokens -> num_predict) — this is what gives a single local model spread
      across quorum members.
    - Raises LLMUnavailable when the server is unreachable or the response is
      malformed (fail-fast, consistent with the other transports).
    """
    import os
    import urllib.request
    import urllib.error
    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    if not host.startswith(("http://", "https://")):
        host = "http://" + host
    host = host.rstrip("/")
    body_obj = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
    }
    options = {}
    if params:
        for k in ("temperature", "top_p", "seed"):
            if params.get(k) is not None:
                options[k] = params[k]
        if params.get("max_tokens") is not None:
            options["num_predict"] = params["max_tokens"]
    if options:
        body_obj["options"] = options
    body = json.dumps(body_obj).encode()
    req = urllib.request.Request(
        f"{host}/api/chat",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            payload = json.loads(resp.read())
    except OSError as e:  # URLError / TimeoutError / socket errors are all OSError
        raise LLMUnavailable(f"ollama request failed (is the server running at {host}?): {e}")
    _note_usage(input=payload.get("prompt_eval_count"), output=payload.get("eval_count"))
    try:
        return payload["message"]["content"].strip()
    except (KeyError, TypeError) as e:
        raise LLMUnavailable(f"ollama response malformed: {e}")


GEMINI_RETRIES = 3          # extra attempts after a 429 / 503
GEMINI_MAX_WAIT = 120       # seconds; never sleep longer than this for one retry


def _gemini_wait_seconds(status, body, attempt):
    """How long to wait before retrying a refused Gemini call, or None to give up.

    429 = too many requests this minute; 503 = Google's servers busy. Both pass, so
    the call waits and tries again instead of stopping the run. A 429 that names a
    per-day quota will not pass within a run, so it gives up at once. The wait is
    Google's own retryDelay when the error carries one, else 30s, 60s, 90s.
    """
    if status not in (429, 503) or attempt >= GEMINI_RETRIES:
        return None
    try:
        details = json.loads(body).get("error", {}).get("details", [])
    except (json.JSONDecodeError, AttributeError):
        details = []
    for d in details:
        for v in d.get("violations", []):
            if "PerDay" in v.get("quotaId", ""):
                return None
    for d in details:
        delay = d.get("retryDelay")             # e.g. "27s"
        if isinstance(delay, str) and delay.endswith("s"):
            try:
                return min(GEMINI_MAX_WAIT, float(delay[:-1]) + 1)
            except ValueError:
                pass
    return min(GEMINI_MAX_WAIT, 30 * (attempt + 1))


def _gemini_error_summary(body):
    """One line from a Gemini error body: its message, plus the quota it hit
    (quota=<quotaId>:<quotaValue>) — the part a 200-character cut used to lose."""
    try:
        err = json.loads(body).get("error", {})
    except (json.JSONDecodeError, AttributeError):
        return " ".join(body.split())[:200]
    text = " ".join(str(err.get("message", "")).split())[:200]
    for d in err.get("details", []):
        for v in d.get("violations", []):
            text += f" quota={v.get('quotaId')}:{v.get('quotaValue')}"
    return text


def _gemini_request_with_wait(req, sleep=None):
    """Send a Gemini request, waiting and retrying on 429 / 503 (_gemini_wait_seconds).
    Any other failure, or running out of retries, raises LLMUnavailable as before."""
    import time
    import urllib.error
    import urllib.request
    import os
    sleep = sleep or time.sleep
    timeout = float(os.environ.get("GEMINI_TIMEOUT", 120))   # long judging packets need more
    attempt = 0
    while True:
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")
            wait = _gemini_wait_seconds(e.code, body, attempt)
            if wait is None:
                raise LLMUnavailable(f"gemini request failed: HTTP {e.code}: "
                                     f"{_gemini_error_summary(body)}")
            sleep(wait)
            attempt += 1
        except OSError as e:  # URLError / TimeoutError / socket errors are all OSError
            raise LLMUnavailable(f"gemini request failed: {e}")


def _gemini_transport(prompt, model, params=None, grounded=False):
    """Transport for the gemini: and gemini_search: backends — Google Gemini's NATIVE
    generateContent API.

    - gemini: is a PLAIN worker, no tools. It is the one an operator may route to: a
      replay reads steps 1..N only, and a search-enabled reader could look up how the
      case ended.
    - gemini_search: turns Google Search grounding ON (grounded=True). This is the
      freshness channel: a query is answered against live web results, covering for
      any model's training cutoff (e.g. 'which free LLM tiers exist / got cancelled
      now?'). Never route an operator here.

    - Native API (not the OpenAI-compat shim): the shim rejects the grounding tool
      ('Unknown name google_search') and drops the source URLs. Native returns
      groundingMetadata, so we can hand back the citations — the valuable part.
    - Grounding needs Gemini 3+ (e.g. gemini_search:gemini-3.8-flash). Free tier
      gives 5,000 grounded prompts/month, so keep this for occasional research, not bulk.
    - REMOTE backend (not in LOCAL_BACKENDS): the privacy gate blocks sensitivity-tagged
      data from reaching it when PRIVACY_GATE is on. A freshness probe is public info —
      callers leave sensitive=False (the default).
    - params sampling knobs map into generationConfig; LLMUnavailable on failure/empty.
    """
    import os
    import urllib.request
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise LLMUnavailable("GEMINI_API_KEY not set — source the sealed keys.env first")
    body_obj = {"contents": [{"parts": [{"text": prompt}]}]}
    if grounded:
        body_obj["tools"] = [{"google_search": {}}]
    gen = {}
    if params:
        if params.get("temperature") is not None:
            gen["temperature"] = params["temperature"]
        if params.get("top_p") is not None:
            gen["topP"] = params["top_p"]
        if params.get("seed") is not None:
            gen["seed"] = params["seed"]
        if params.get("max_tokens") is not None:
            gen["maxOutputTokens"] = params["max_tokens"]
    if gen:
        body_obj["generationConfig"] = gen
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    req = urllib.request.Request(
        url,
        data=json.dumps(body_obj).encode(),
        headers={"Content-Type": "application/json", "x-goog-api-key": key,
                 "User-Agent": "vivify-operators/1.0"},
        method="POST",
    )
    payload = _gemini_request_with_wait(req)
    u = payload.get("usageMetadata") or {}
    _note_usage(input=u.get("promptTokenCount"), output=u.get("candidatesTokenCount"),
                cache_read=u.get("cachedContentTokenCount"), thinking=u.get("thoughtsTokenCount"))
    try:
        cand = payload["candidates"][0]
        text = "".join(p.get("text", "") for p in cand["content"]["parts"]).strip()
    except (KeyError, IndexError, TypeError) as e:
        # empty candidates also happens on a safety block — surface, don't crash
        raise LLMUnavailable(f"gemini response malformed or blocked: {e}; {str(payload)[:200]}")
    if not text:
        raise LLMUnavailable("gemini returned no text (likely safety-blocked)")
    # Append grounding citations — the point of using the grounded channel.
    sources = []
    for chunk in cand.get("groundingMetadata", {}).get("groundingChunks", []):
        web = chunk.get("web", {})
        uri = web.get("uri")
        if uri:
            sources.append(f"- {web.get('title', uri)} ({uri})")
    if sources:
        text += "\n\nSources:\n" + "\n".join(sources[:8])
    return text


# Transport registry: backend prefix -> callable(prompt, model) -> response text.
# claude (CLI), ollama (local, no key) and gemini (native API, plain or grounded) are bespoke —
# each has its own auth and response shape. Every hosted OpenAI-compatible provider is
# added from config/providers.json by _load_providers() below — a JSON line, no code.
TRANSPORTS = {
    "claude": _claude_transport,
    "ollama": _ollama_transport,
    "gemini": _gemini_transport,
    "gemini_search": lambda prompt, model, params=None: _gemini_transport(
        prompt, model, params, grounded=True),
}


def _load_providers():
    """Register every OpenAI-compatible provider in config/providers.json as a
    transport. The path is module-relative (cwd-independent). A missing or empty
    file is fine — claude + ollama still work; the distal team just isn't wired yet.
    """
    cfg_path = Path(__file__).resolve().parent.parent / "config" / "providers.json"
    if not cfg_path.exists():
        return
    for name, cfg in read_json(cfg_path).items():
        # Underscore-prefixed keys are metadata, not providers — the convention
        # coordinates.json already uses for _doc and _max_string_len. Without this
        # guard, documenting this file crashes the import: cfg["base_url"] on a
        # string raises TypeError before any transport is registered.
        if name.startswith("_"):
            continue
        if name in TRANSPORTS:
            # a bespoke transport already owns this backend (e.g. gemini's native
            # grounding transport) — don't silently clobber it with the generic shim
            continue
        TRANSPORTS[name] = _make_openai_transport(
            name, cfg["base_url"], cfg["env_key"], cfg.get("extra_headers"))


_load_providers()

# Backends where data never leaves the box. Sensitivity-tagged calls may go ONLY
# to these when the privacy gate is on. All OpenAI-compatible providers are remote
# and excluded; only local services belong here.
LOCAL_BACKENDS = {"ollama", "lok"}


def _privacy_gate_state():
    """Read PRIVACY_GATE as an explicit tristate: 'on', 'off', or None (unset).

    None (unset or an unrecognized value) is deliberately distinct from 'off'. The
    old silent 'off by default' meant one forgotten env var could leak real field
    data off-box; now only an EXPLICIT 'off' relaxes the gate, so forgetting it
    fails closed instead. See project_model_routing.md.
    """
    import os
    raw = os.environ.get("PRIVACY_GATE")
    if raw is None:
        return None
    v = raw.strip().lower()
    if v in ("on", "1", "true", "yes"):
        return "on"
    if v in ("off", "0", "false", "no"):
        return "off"
    return None  # unrecognized -> treat as unset, fail closed


def _enforce_privacy_gate(backend, sensitive):
    """Block sensitivity-tagged work from leaving the box unless the gate is
    EXPLICITLY relaxed. The single enforcement point for non-negotiables #1/#2.

    No-op when the call is not sensitive, or the backend is local. Otherwise the
    sensitive-data-leaving-the-box path is fail-closed: allowed ONLY when
    PRIVACY_GATE is explicitly 'off'. 'on', unset, and any unrecognized value all
    block — so forgetting to set the gate protects the data instead of leaking it.
    """
    if not sensitive or backend in LOCAL_BACKENDS:
        return
    state = _privacy_gate_state()
    if state == "off":
        return  # explicit development relaxation — the only path sensitive data leaves
    reason = ("PRIVACY_GATE is on" if state == "on"
              else "PRIVACY_GATE is unset — refusing to route sensitive data off-box "
                   "without an explicit decision (set PRIVACY_GATE=off to allow in dev)")
    raise PrivacyGateError(
        f"sensitivity-tagged call blocked: backend {backend!r} is not local "
        f"(local = {sorted(LOCAL_BACKENDS)}); {reason}"
    )


def split_backend(model_id):
    """Split a model id into (backend, model).

    The token before the first ':' selects a transport (e.g. 'deepseek:deepseek-chat',
    'ollama:qwen2.5:7b' -> split on the FIRST colon, so the model keeps its own tag
    colon). A bare id with no colon ('claude-sonnet-4-6') routes to claude, so existing
    model_map entries keep working unchanged. A colon-prefixed id whose prefix is NOT a
    registered backend is an error (typo or unregistered backend) — raised here rather
    than silently misrouted to claude, since no real model id contains a colon.
    """
    if ":" in model_id:
        prefix, rest = model_id.split(":", 1)
        if prefix in TRANSPORTS:
            return prefix, rest
        raise ValueError(
            f"unknown backend prefix {prefix!r} in model id {model_id!r}; "
            f"registered backends: {sorted(TRANSPORTS)}"
        )
    return "claude", model_id


def llm_call_model(prompt, model_id, params=None, sensitive=False):
    """Dispatch to an explicit backend-prefixed model id, bypassing capability
    routing. Used by quorum.py to address debate members directly (e.g.
    'ollama:llama3:8b', 'nvidia:meta/llama-3.1-70b-instruct') without needing a
    model_map entry. Same gate, transport, and fence-stripping as llm_call.

    - params: optional sampling knobs ({temperature, top_p, seed, max_tokens}) —
      how the quorum gets spread/divergence; ignored by transports that can't honor
      them (claude CLI).
    - Raises LLMUnavailable (model down) / PrivacyGateError (sensitive call leaving box).
    """
    import re
    import time
    backend, model = split_backend(model_id)
    _enforce_privacy_gate(backend, sensitive)
    _last_usage.clear()
    t = time.time()
    try:
        text = TRANSPORTS[backend](prompt, model, params)
    except Exception as e:
        _write_usage(backend, model, time.time() - t, len(prompt), False, e)
        raise
    _write_usage(backend, model, time.time() - t, len(prompt), True)
    # strip markdown code fences (```json ... ``` or ``` ... ```)
    text = re.sub(r"^```[a-z]*\n?", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n?```$", "", text, flags=re.MULTILINE)
    return text.strip()


def llm_call(prompt, capability="default", config_dir="config", sensitive=False, params=None):
    """Call an LLM for a capability and return the response text.

    - resolve_model() picks the model id; dispatch + gate + fence-strip via
      llm_call_model() (which split_backend()s and routes to the transport)
    - sensitive=True marks private field data; with PRIVACY_GATE on it may route
      only to a local backend (see _enforce_privacy_gate). Default False — callers
      handling private legal data pass sensitive=True so the gate can protect it.
    - params: optional sampling knobs passed through to the transport
    - Raises LLMUnavailable when a transport reports the model is down (not the data)
    - Raises PrivacyGateError when a sensitive call would leave the box (gate on)
    """
    return llm_call_model(prompt, resolve_model(capability, config_dir), params, sensitive)


def extract_json(text):
    """Extract the first valid JSON object from a string.

    Handles responses where the LLM adds explanation before or after the JSON.
    Raises json.JSONDecodeError if no valid JSON object is found.
    """
    start = text.find("{")
    if start == -1:
        raise json.JSONDecodeError("No JSON object found", text, 0)
    depth = 0
    for i, ch in enumerate(text[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start:i + 1])
    raise json.JSONDecodeError("Unterminated JSON object", text, start)


_coordinates_cache = {}

# The repo root — lib/vivify_core.py sits one level below it. Relative config_dir
# values are anchored here, never to the cwd.
_REPO_ROOT = Path(__file__).resolve().parent.parent


def _config_path(config_dir, filename):
    """Resolve a config file, anchoring a relative config_dir to the repo root.

    Previously these were read as Path("config")/... — relative to the CWD — so
    running an operator from any other directory found nothing, and read_json's
    empty-dict-for-missing-file turned that into two silent failures rather than an
    error: model_map fell through to the hardcoded default model, and the
    coordinates spec went empty, disabling the enum gate entirely (out-of-enum
    values then validated clean). Both were invisible in the store.

    An absolute config_dir is honored as given, so callers can still point at a
    different config set deliberately.
    """
    base = Path(config_dir)
    if not base.is_absolute():
        base = _REPO_ROOT / base
    return base / filename


def _load_coordinates(config_dir="config"):
    """Read config/coordinates.json (the allowed-value spec), cached per path.
    Cwd-independent: a relative config_dir resolves against the repo root, not the
    cwd. Cached because operators call the gate once per inference in bulk runs."""
    path = _config_path(config_dir, "coordinates.json")
    key = str(path.resolve())
    if key not in _coordinates_cache:
        _coordinates_cache[key] = read_json(path)
    return _coordinates_cache[key]


def validate_coordinates(result, operator, config_dir="config"):
    """The inbound validation gate: check an operator's parsed LLM output against
    the allowed values in config/coordinates.json before it may enter the store.

    Returns the same dict on success, so callers write:
        result = validate_coordinates(extract_json(raw), "conflict")
    Raises CoordinateValidationError on the FIRST failure — fail-closed; a rejected
    result must NOT be merged. An operator with no spec entry still gets the global
    string-length guard, so a new operator is never silently blocked — only its
    declared fields are enforced, and only when present (presence of required keys
    is still enforced by the operator's own result[...] access).

    Checks, cheapest first:
      - global: every string value (declared or not) under _max_string_len — the
        injection guard, so a coordinate can't smuggle a paragraph or a command in
      - enums:  value in the operator's allowed set (or null if field is nullable)
      - floats: numeric (not bool) and within [lo, hi]
      - bools:  an actual bool
      - lists:  a list whose string elements obey the length cap
    """
    spec = _load_coordinates(config_dir)
    max_len = spec.get("_max_string_len", 600)
    op_spec = spec.get("operators", {}).get(operator, {})
    nullable = set(op_spec.get("nullable", []))

    def fail(field, why):
        raise CoordinateValidationError(
            f"{operator}.{field}: {why} (got {result.get(field)!r})")

    # global injection guard — cap every string the model returned, declared or not
    for field, val in result.items():
        if isinstance(val, str) and len(val) > max_len:
            fail(field, f"string exceeds {max_len} chars (injection guard)")

    for field, allowed in op_spec.get("enums", {}).items():
        if field not in result:
            continue
        val = result[field]
        # nullable fields accept JSON null and the common string stand-ins a small
        # model emits instead ("null"/"none"/empty) — don't reject those as enums
        if field in nullable and (val is None or
                (isinstance(val, str) and val.strip().lower() in ("null", "none", ""))):
            continue
        if val not in allowed:
            fail(field, f"not in {allowed}")

    for field, bounds in op_spec.get("floats", {}).items():
        if field not in result or result[field] is None:
            continue
        val = result[field]
        if isinstance(val, bool) or not isinstance(val, (int, float)):
            fail(field, "not a number")
        lo, hi = bounds
        if not (lo <= val <= hi):
            fail(field, f"outside [{lo}, {hi}]")

    for field in op_spec.get("bools", []):
        if field in result and not isinstance(result[field], bool):
            fail(field, "not a boolean")

    for field in op_spec.get("lists", []):
        if field not in result or result[field] is None:
            continue
        val = result[field]
        if not isinstance(val, list):
            fail(field, "not a list")
        for el in val:
            if isinstance(el, str) and len(el) > max_len:
                fail(field, f"list element exceeds {max_len} chars")

    return result


def _vote_count():
    """How many draws a voted call takes. VIVIFY_VOTES, default 3; 1 disables voting.

    Three is the smallest count that can produce a majority. Measured on the legal
    corpus (inferences/session_stability.md): single draws gave predicted_tension a
    0.607 spread on one case; majority-of-three collapses it to 0.034.
    """
    import os
    raw = os.environ.get("VIVIFY_VOTES", "3")
    try:
        return max(1, int(raw))
    except ValueError:
        return 3


def categorical_signature(result, operator, config_dir="config"):
    """A draw's categorical identity: its declared enum fields, as a sortable tuple.

    Only enum fields count. Prose and confidence churn on every call (measured: free
    text never repeats across identical-input runs) and would make every draw unique,
    so voting on them would be voting on noise.
    """
    spec = _load_coordinates(config_dir).get("operators", {}).get(operator, {})
    return tuple(sorted((f, result.get(f)) for f in spec.get("enums", {})))


def modal_choice(draws, signature_of):
    """Pick the most typical draw. Returns (index, vote record).

    The winner is a draw that ACTUALLY OCCURRED, chosen by modal signature — not a
    field-wise assembly of the most popular value for each field independently.
    Field-wise assembly can synthesise a combination no draw produced: the legal
    re-read caught `cooperative` returning status=honored with a maxim named, which
    is individually legal and jointly incoherent, and assembly would manufacture
    exactly that class of result. Choosing a real draw keeps each block internally
    consistent.

    Ties, and the case where no signature repeats at all, fall back to the draw that
    agrees most often with the field-wise plurality — still a real draw, just the
    most central one.
    """
    sigs = [signature_of(d) for d in draws]
    counts = Counter(sigs)
    top, agreed = counts.most_common(1)[0]
    if agreed == 1 and len(draws) > 1:
        fields = {f for s in sigs for f, _ in s}
        modes = {f: Counter(dict(s).get(f) for s in sigs).most_common(1)[0][0]
                 for f in fields}
        scores = [sum(1 for f, v in s if modes.get(f) == v) for s in sigs]
        idx = scores.index(max(scores))
        top, agreed = sigs[idx], counts[sigs[idx]]
    # str() the distribution keys: a value may be None, which JSON cannot use as a key
    distribution = {f: dict(Counter(str(dict(s).get(f)) for s in sigs))
                    for f in {f for s in sigs for f, _ in s}}
    return sigs.index(top), {"n": len(draws), "agreed": agreed,
                             "unanimous": agreed == len(draws),
                             "distribution": distribution}


def call_and_vote(prompt, operator, capability="default", sensitive=False,
                  params=None, retries=2, config_dir="config", votes=None):
    """Take several independent draws and store the modal one, with the spread.

    The operator entry point. Sits ON TOP of call_and_validate, which keeps its own
    job: retrying output that is INVALID. This handles the different problem of
    output that is valid but not reproducible — measured across two sessions of the
    legal corpus, where 4 of 36 stored coordinates flipped outright and 6 more split
    within a single session, all between legal enum values that no gate can reject.

    - votes defaults to VIVIFY_VOTES (3); votes=1 is exactly call_and_validate.
    - A draw that fails validation after its own retries is dropped, not fatal —
      the vote proceeds on the draws that survived. Only if EVERY draw fails does
      the last error propagate, so the caller still quarantines as before.
    - The winner carries `_votes`: n, agreed, unanimous, and the per-field
      distribution. A coordinate is now stored WITH its spread, so a later reader
      can see whether it was 3/3 or 2/1 rather than inferring stability from a
      point value.
    """
    votes = _vote_count() if votes is None else max(1, votes)
    if votes == 1:
        return call_and_validate(prompt, operator, capability, sensitive,
                                 params, retries, config_dir)

    draws, last_err = [], None
    for _ in range(votes):
        try:
            draws.append(call_and_validate(prompt, operator, capability, sensitive,
                                           params, retries, config_dir))
        except (CoordinateValidationError, json.JSONDecodeError) as e:
            last_err = e
    if not draws:
        raise last_err

    idx, record = modal_choice(
        draws, lambda d: categorical_signature(d, operator, config_dir))
    record["quarantined"] = votes - len(draws)
    winner = draws[idx]
    winner["_votes"] = record
    return winner


def call_and_validate(prompt, operator, capability="default", sensitive=False,
                      params=None, retries=2, config_dir="config"):
    """Call an LLM, parse and validate its output, retrying on invalid/malformed
    output before giving up. The standard operator entry point — replaces the bare
    validate_coordinates(extract_json(llm_call(...))) so a RECOVERABLE miss isn't
    silently dropped as a missing dimension.

    The privacy-safe tier (a small local model, e.g. ollama:llama3:8b) emits an
    out-of-enum value or broken JSON more often than a frontier model; one or two
    re-asks recover most of these. Retries re-issue the same prompt with a small
    temperature bump (on backends that honor it) to break out of a stuck wrong
    answer; the caller's prompt and validation rules are unchanged.

    - Retries CoordinateValidationError and json.JSONDecodeError only.
    - Does NOT retry LLMUnavailable — transport-down is fatal; it propagates so the
      batch can fail fast (re-asking a dead CLI just burns quota).
    - After `retries` extra attempts all fail, the last validation/parse error is
      raised, so the caller still quarantines exactly as before (fail-closed).
    - The validated result carries `_model`: the model id this call actually used,
      resolved ONCE up front rather than re-derived later, so an operator's parse()
      records what produced the coordinate instead of what the config says now.
    """
    model = resolve_model(capability, config_dir)
    last_err = None
    for attempt in range(retries + 1):
        call_params = dict(params or {})
        if attempt > 0 and "temperature" not in call_params:
            # nudge diversity only on retries; the first attempt honors caller intent
            call_params["temperature"] = round(0.3 * attempt, 2)
        raw = llm_call_model(prompt, model, call_params or None, sensitive=sensitive)
        try:
            result = validate_coordinates(extract_json(raw), operator, config_dir)
            result["_model"] = model
            return result
        except (CoordinateValidationError, json.JSONDecodeError) as e:
            last_err = e
    raise last_err


def model_override(capability):
    """Read VIVIFY_MODEL_OVERRIDE — the model-comparison arm switch, env-scoped.

    Swapping models by editing config/model_map.json is the wrong mechanism for an
    experiment: a forgotten revert silently re-models every later run, and nothing
    in the store would say so. An env var dies with the shell.

    Two forms:
      VIVIFY_MODEL_OVERRIDE=claude-fable-5
          every capability, including web_research — the blunt whole-pipeline arm
      VIVIFY_MODEL_OVERRIDE=logos_operator=claude-fable-5,conflict_operator=claude-fable-5
          named capabilities only; everything else keeps its mapped model. This is
          the form that isolates one variable — swap the coordinate producers and
          hold semantic_extraction fixed, so left keywords stay comparable.

    - Returns the override model id for this capability, or None
    - Malformed entries are skipped rather than raising: a typo'd arm must not
      take down a run, and _model in the store records what was ACTUALLY used
    """
    import os
    raw = os.environ.get("VIVIFY_MODEL_OVERRIDE", "").strip()
    if not raw:
        return None
    if "=" not in raw:
        return raw
    for entry in raw.split(","):
        cap, _, model = entry.partition("=")
        if cap.strip() == capability and model.strip():
            return model.strip()
    return None


# Family aliases the claude CLI resolves to the newest model of that family.
# model_map names these so the pipeline tracks the current release without edits;
# pin_model() turns one into the concrete id before anything is recorded.
CLAUDE_ALIASES = {"opus", "sonnet", "haiku", "fable"}
_PINNED = {}


def _probe_alias(alias):
    """Ask the claude CLI which concrete model an alias resolves to right now.

    One tiny call; its JSON output names the model that answered in modelUsage.
    Background helper models (e.g. haiku) can appear there too, so the key that
    contains the alias family wins. Raises LLMUnavailable if the CLI is down or
    the answer names no model of that family — the real call would fail anyway.
    """
    import subprocess
    result = subprocess.run(
        claude_cmd("Reply with the single word ok", alias, "--output-format", "json"),
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise LLMUnavailable(result.stderr.strip() or f"claude exited {result.returncode}")
    try:
        used = list(json.loads(result.stdout).get("modelUsage", {}))
    except json.JSONDecodeError as e:
        raise LLMUnavailable(f"alias probe for {alias!r}: unreadable output: {e}")
    matches = [m for m in used if alias in m]
    if not matches:
        raise LLMUnavailable(f"alias probe for {alias!r} named no {alias} model: {used}")
    return matches[0]


def pin_model(model_id):
    """Return the concrete model id for a family alias; any other id unchanged.

    - 'opus' -> e.g. 'claude-opus-5-5', resolved once per process and cached, so
      every call in a run uses (and stamps) the same model
    - Concrete ids and backend-prefixed ids ('groq:...') pass through untouched
    - The pinned id, never the alias, is what reaches _model: an alias stamp would
      make runs before and after a release indistinguishable in the store
    """
    if model_id not in CLAUDE_ALIASES:
        return model_id
    if model_id not in _PINNED:
        _PINNED[model_id] = _probe_alias(model_id)
    return _PINNED[model_id]


def resolve_model(capability, config_dir="config"):
    """Return the concrete model ID for a named capability from config/model_map.json.

    - VIVIFY_MODEL_OVERRIDE wins over the map when it names this capability
      (see model_override) — the experiment switch, never a config edit
    - Falls back to 'default' if capability not found
    - Falls back to 'opus' if config missing. A relative config_dir is anchored to
      the repo root (see _config_path), so this fallback now means the map is
      genuinely absent — not merely that the caller ran from elsewhere.
    - A family alias ('opus') is pinned to the current concrete id (see pin_model)
    """
    override = model_override(capability)
    if override:
        return pin_model(override)
    model_map = read_json(_config_path(config_dir, "model_map.json"))
    return pin_model(model_map.get(capability) or model_map.get("default", "opus"))


if __name__ == "__main__":
    import sys
    import fileinput

    print("vivify_core — autovivification engine self-test")
    print()

    # Demo: build a nested structure from scratch
    store = autovivify()
    store["conflict"]["legal"]["perjury"] = "detected"
    store["conflict"]["legal"]["timeline"] = ["2024-01", "2024-03"]
    store["outcome"]["prediction"] = "adverse"

    result = to_dict(store)
    print(json.dumps(result, indent=2))

# llm: claude-sonnet-4-6 | 2026-04-15 | repos/vivify-inferences/lib/vivify_core.py | created — autovivification engine, deep_update, JSON I/O
# llm: claude-sonnet-4-6 | 2026-04-27 | repos/vivify-inferences/lib/vivify_core.py | added resolve_model() — capability-to-model routing via config/model_map.json
# llm: claude-sonnet-4-6 | 2026-05-18 | repos/vivify-inferences/lib/vivify_core.py | added dry_run param to write_json(); add_dry_run_arg() helper for argparse
# llm: claude-opus-4-8 | 2026-06-20 | repos/vivify-operators/lib/vivify_core.py | added inbound validation gate: CoordinateValidationError, _load_coordinates(), validate_coordinates() against config/coordinates.json
# llm: claude-sonnet-4-6 | 2026-05-22 | repos/vivify-inferences/lib/vivify_core.py | added llm_call() — claude CLI subprocess, no API key required, strips markdown fences
# llm: claude-opus-4-8 | 2026-06-15 | repos/vivify-operators/lib/vivify_core.py | added LLMUnavailable exception — llm_call raises it on CLI failure (quota/auth) so batches can fail-fast
# llm: claude-opus-4-8 | 2026-06-17 | repos/vivify-operators/lib/vivify_core.py | step 1 multi-backend dispatch — TRANSPORTS registry + split_backend(); claude is a transport, bare ids backward-compatible; gate seam left for step 2
# llm: claude-opus-4-8 | 2026-06-17 | repos/vivify-operators/lib/vivify_core.py | step 2 privacy gate — PrivacyGateError + LOCAL_BACKENDS + _enforce_privacy_gate(); llm_call gains sensitive flag; gated behind PRIVACY_GATE env (off by default, one-flip to reinstate)
# llm: claude-opus-4-8 | 2026-06-17 | repos/vivify-operators/lib/vivify_core.py | step 3 deepseek transport — stdlib urllib, key from DEEPSEEK_API_KEY (header not prompt), LLMUnavailable on failure; split_backend now raises on unregistered colon-prefix instead of misrouting to claude
# llm: claude-opus-4-8 | 2026-06-17 | repos/vivify-operators/lib/vivify_core.py | step 4 ollama transport — local HTTP /api/chat (OLLAMA_HOST override), no key, in LOCAL_BACKENDS so privacy-gate-safe for sensitive data; LLMUnavailable when server down
# llm: claude-opus-4-8 | 2026-06-19 | repos/vivify-operators/lib/vivify_core.py | generalized deepseek into _make_openai_transport factory + config/providers.json loader (_load_providers); distal team (deepseek/nvidia/openrouter/groq/mistral/cerebras/gemini) now data-driven — adding a provider is one JSON line
# llm: claude-opus-4-8 | 2026-06-19 | repos/vivify-operators/lib/vivify_core.py | threaded params (temperature/top_p/seed/max_tokens) through all transports (openai body, ollama options, claude ignores); added llm_call_model() direct-model entry for quorum.py
# llm: claude-opus-4-8 | 2026-06-19 | repos/vivify-operators/lib/vivify_core.py | broadened transport network except URLError->OSError so read TimeoutError fails-soft as LLMUnavailable (was crashing the quorum on a slow free-tier member)
# llm: claude-opus-4-8 | 2026-06-21 | repos/vivify-operators/lib/vivify_core.py | added native Gemini grounding transport (_gemini_transport, Google Search always-on + citations) as the web-research freshness channel; _load_providers no longer clobbers bespoke transports
# llm: claude-opus-4-8 | 2026-06-21 | repos/vivify-operators/lib/vivify_core.py | send explicit User-Agent on OpenAI-compat + gemini transports — Groq is behind Cloudflare which 403s (error 1010) the default Python-urllib UA
# llm: claude-opus-4-8 | 2026-06-24 | repos/vivify-operators/lib/vivify_core.py | safe-default privacy gate: _privacy_gate_state() tristate, unset/unrecognized now fails CLOSED for sensitive off-box calls (only explicit PRIVACY_GATE=off relaxes) — forgetting the env protects data instead of leaking it
# llm: claude-opus-4-8 | 2026-06-24 | repos/vivify-operators/lib/vivify_core.py | added call_and_validate() — retries CoordinateValidationError/JSONDecodeError (temp bump on retry) before fail-closing, so a recoverable small-model miss isn't dropped as a missing dimension; LLMUnavailable still propagates
# llm: claude-opus-5 | 2026-08-13 | repos/vivify-operators/lib/vivify_core.py | VIVIFY_MODEL_OVERRIDE (bare = all capabilities, scoped = capability=model pairs) via model_override(); call_and_validate resolves the model once, calls llm_call_model directly, stamps result["_model"]
# llm: claude-opus-5 | 2026-08-27 | repos/vivify-operators/lib/vivify_core.py | _config_path(): relative config_dir now anchors to the repo root, not the cwd — fixes silent model downgrade to the hardcoded default AND a silently disabled coordinate enum gate when run from any other directory
# llm: claude-opus-5 | 2026-09-03 | repos/vivify-operators/lib/vivify_core.py | repeat-and-vote: call_and_vote() takes VIVIFY_VOTES draws (default 3) and stores the MODAL one plus its per-field spread in _votes; modal-signature not field-wise assembly, so the stored block is always a draw that really occurred; call_and_validate unchanged underneath (it still owns retry-on-invalid)
# llm: claude-opus-5 | 2026-09-21 | repos/vivify-operators/lib/vivify_core.py | _load_providers skips _-prefixed metadata keys — adding a _doc to providers.json would otherwise raise TypeError at import and take the whole library with it
# llm: claude-opus-5-5 | 2026-09-29 | repos/vivify-operators/lib/vivify_core.py | pin_model(): model_map may name a family alias (opus) that tracks the newest release; resolve_model pins it to the concrete id once per run via a claude -p JSON probe, so _model never records a bare alias; fallback default sonnet-4-6 -> opus
# llm: claude-opus-5-5 | 2026-10-17 | repos/vivify-operators/lib/vivify_core.py | lean worker — claude -p calls drop the Claude Code harness (no tools, own system prompt, no settings/memory/MCP/skills/session file); VIVIFY_CLAUDE_WORKER=full restores the old call; alias probe routes through claude_cmd too
# llm: claude-opus-5-5 | 2026-10-17 | repos/vivify-operators/lib/vivify_core.py | gemini: is now a plain worker (no tools) and gemini_search: the grounded route; Gemini calls wait and retry on 429/503 (Google's retryDelay, else 30/60/90s, cap 120s, per-day quota gives up)
# llm: claude-opus-5-5 | 2026-10-17 | repos/vivify-operators/lib/vivify_core.py | Gemini give-up errors are one line and keep the quota hit (quota=<id>:<value>) instead of a 200-char cut of pretty-printed JSON
# llm: claude-opus-5-5 | 2026-10-18 | repos/vivify-operators/lib/vivify_core.py | usage log: one JSON line per LLM call, same shape for every backend (tokens in/out/cache, thinking, cost, seconds, ok); claude worker reads --output-format json; VIVIFY_USAGE_LOG, VIVIFY_RUN_TAG
# llm: claude-opus-5-5 | 2026-10-23 | repos/vivify-operators/lib/vivify_core.py | Gemini read timeout configurable via GEMINI_TIMEOUT (default 120s unchanged); long judging packets timed out at 120s and the timed-out calls still spent free quota
