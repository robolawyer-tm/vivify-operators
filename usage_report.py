#!/usr/bin/env python3
"""
usage_report.py — what the LLM calls cost, summed from the usage log.

Reads the one-line-per-call log that vivify_core writes (default
~/.local/state/vivify-operators/usage.jsonl, or VIVIFY_USAGE_LOG, or a file
argument, or stdin) and prints, per run tag, backend and model: calls, failures,
tokens in / out / cache written / cache read, thinking tokens, seconds, and the
list-price cost the provider reports (claude only; a subscription is not billed it).

Usage:
    ./usage_report.py                      # the whole log
    ./usage_report.py --tag residue_try5   # one run
    ./usage_report.py --since 2026-10-18   # calls on or after a date
    tail -50 usage.jsonl | ./usage_report.py
"""

import os
import sys
import stat
import json
import argparse
import fileinput
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
from vivify_core import usage_log_path, USAGE_FIELDS


def summarise(records):
    groups = {}
    for r in records:
        key = (r.get("tag") or "-", r.get("backend"), r.get("model"))
        g = groups.setdefault(key, {"calls": 0, "failed": 0, "seconds": 0.0,
                                    **{f: 0 for f in USAGE_FIELDS}})
        g["calls"] += 1
        g["failed"] += 0 if r.get("ok") else 1
        g["seconds"] += r.get("seconds") or 0
        for f in USAGE_FIELDS:
            g[f] += r.get(f) or 0
    return groups


def table(groups):
    head = f"{'tag':<18} {'model':<34} {'calls':>5} {'fail':>4} {'in':>8} {'out':>8} {'c.write':>8} {'c.read':>8} {'think':>7} {'secs':>7} {'list $':>7}"
    rows = [head, "-" * len(head)]
    for (tag, backend, model), g in sorted(groups.items(), key=lambda kv: (kv[0][0], str(kv[0][1]), str(kv[0][2]))):
        rows.append(f"{tag[:18]:<18} {(str(backend) + ':' + str(model))[:34]:<34} {g['calls']:>5} {g['failed']:>4} "
                    f"{g['input']:>8} {g['output']:>8} {g['cache_write']:>8} {g['cache_read']:>8} "
                    f"{g['thinking']:>7} {g['seconds']:>7.0f} {g['cost_usd']:>7.3f}")
    return "\n".join(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("file", nargs="?", help="usage log (default: VIVIFY_USAGE_LOG or ~/.local/state/...)")
    ap.add_argument("--tag", help="only this run tag")
    ap.add_argument("--since", help="only calls at or after this ISO date/time")
    args = ap.parse_args()
    piped = stat.S_ISFIFO(os.fstat(sys.stdin.fileno()).st_mode)   # house pipe-detect
    if args.file or piped:
        source = fileinput.input(files=[args.file] if args.file else ["-"])
    else:
        path = usage_log_path()
        if not path or not path.exists():
            sys.exit(f"no usage log at {path}")
        source = path.open()
    records = []
    for line in source:
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        if args.tag and r.get("tag") != args.tag:
            continue
        if args.since and r.get("at", "") < args.since:
            continue
        records.append(r)
    print(table(summarise(records)))


if __name__ == "__main__":
    main()

# llm: claude-opus-5-5 | 2026-10-18 | repos/vivify-operators/usage_report.py | created — sums the per-call usage log by run tag, backend and model (calls, failures, tokens in/out/cache, thinking, seconds, list cost)
