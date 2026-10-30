#!/usr/bin/env python3
"""Focused test: claude calls run as the lean worker unless told otherwise.

The lean worker strips the Claude Code harness from each `claude -p` call: no
tools, a one-line system prompt in place of the agent prompt, no settings, no
auto-memory, no MCP servers, no skills, no session file. Measured 2026-10-17, a
trivial prompt went from ~24K input tokens to 607, and project memory stopped
reaching the instrument. VIVIFY_CLAUDE_WORKER=full restores the old call for
parity checks.

No real LLM calls — subprocess.run is monkeypatched.

Run standalone: python3 tests/test_lean_worker.py  (exit 0 = pass)
"""
import os
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "lib"))

import vivify_core
from vivify_core import claude_cmd, claude_worker_mode, LEAN_WORKER_FLAGS

failures = []


def check(label, condition, detail=""):
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}  {detail}")
        failures.append(label)


def set_mode(value):
    if value is None:
        os.environ.pop("VIVIFY_CLAUDE_WORKER", None)
    else:
        os.environ["VIVIFY_CLAUDE_WORKER"] = value


class FakeRun:
    """Records the argv of each subprocess.run and answers like the CLI."""
    def __init__(self, stdout="ok"):
        self.cmds = []
        self.inputs = []
        self.stdout = stdout

    def __call__(self, cmd, **kwargs):
        self.cmds.append(cmd)
        self.inputs.append(kwargs.get("input"))
        return subprocess.CompletedProcess(cmd, 0, stdout=self.stdout, stderr="")


def flag_value(cmd, flag):
    return cmd[cmd.index(flag) + 1] if flag in cmd else None


# --- mode switch -------------------------------------------------------------
set_mode(None)
check("default mode is lean", claude_worker_mode() == "lean")
set_mode("FULL")
check("full mode is case-insensitive", claude_worker_mode() == "full")
set_mode("nonsense")
try:
    claude_worker_mode()
    check("unknown mode is refused", False, "no error raised")
except ValueError:
    check("unknown mode is refused", True)

# --- argv shape --------------------------------------------------------------
set_mode(None)
cmd = claude_cmd("PROMPT", "claude-opus-5-5")
check("lean argv keeps prompt and model first",
      cmd[:5] == ["claude", "-p", "PROMPT", "--model", "claude-opus-5-5"], cmd[:5])
check("lean argv disables all tools", flag_value(cmd, "--tools") == "", cmd)
check("lean argv replaces the system prompt",
      flag_value(cmd, "--system-prompt") == vivify_core.WORKER_SYSTEM_PROMPT)
check("lean argv loads no setting sources", flag_value(cmd, "--setting-sources") == "")
check("lean argv turns auto-memory off",
      '"autoMemoryEnabled": false' in (flag_value(cmd, "--settings") or ""))
for flag in ("--strict-mcp-config", "--disable-slash-commands", "--no-session-persistence"):
    check(f"lean argv has {flag}", flag in cmd)
check("lean argv never uses --bare (needs an API key, we run on OAuth)", "--bare" not in cmd)

set_mode("full")
cmd = claude_cmd("PROMPT", "claude-opus-5-5")
check("full argv is the old harnessed call",
      cmd == ["claude", "-p", "PROMPT", "--model", "claude-opus-5-5"], cmd)

# --- both claude entry points go through claude_cmd ---------------------------
original = subprocess.run
fake = FakeRun()
subprocess.run = fake
try:
    set_mode(None)
    out = vivify_core._claude_transport("PROMPT", "claude-opus-5-5")
    check("transport returns the CLI's stdout", out == "ok", out)
    check("transport call is lean",
          all(f in fake.cmds[-1] for f in LEAN_WORKER_FLAGS if f.startswith("--")), fake.cmds[-1])

    fake.stdout = '{"modelUsage": {"claude-opus-5-5": {}}}'
    pinned = vivify_core._probe_alias("opus")
    check("alias probe still pins", pinned == "claude-opus-5-5", pinned)
    check("alias probe is lean and keeps --output-format json",
          "--tools" in fake.cmds[-1] and flag_value(fake.cmds[-1], "--output-format") == "json",
          fake.cmds[-1])

    fake.stdout = "ok"
    long_prompt = "x" * (vivify_core.CLAUDE_ARG_MAX + 1)
    vivify_core._claude_transport(long_prompt, "claude-opus-5-5")
    check("long prompt goes on stdin, not argv",
          fake.inputs[-1] == long_prompt and long_prompt not in fake.cmds[-1]
          and fake.cmds[-1][:2] == ["claude", "-p"] and "--tools" in fake.cmds[-1], fake.cmds[-1][:4])
    vivify_core._claude_transport("PROMPT", "claude-opus-5-5")
    check("short prompt stays in argv", fake.inputs[-1] is None and "PROMPT" in fake.cmds[-1], fake.cmds[-1][:4])

    set_mode("full")
    vivify_core._claude_transport("PROMPT", "claude-opus-5-5")
    check("full mode reaches the transport", "--tools" not in fake.cmds[-1], fake.cmds[-1])
finally:
    subprocess.run = original
    set_mode(None)

print()
if failures:
    print(f"FAILED: {len(failures)} check(s) — {', '.join(failures)}")
    sys.exit(1)
print("All lean-worker checks passed.")

# llm: claude-opus-5-5 | 2026-10-17 | repos/vivify-operators/tests/test_lean_worker.py | created — lean worker is the default claude call, full mode restores the old argv, transport and alias probe both route through claude_cmd (subprocess stubbed, no live calls)
# llm: claude-opus-5-5 | 2026-10-30 | repos/vivify-operators/tests/test_lean_worker.py | long prompts (> CLAUDE_ARG_MAX) reach claude -p on stdin, short ones stay in argv
