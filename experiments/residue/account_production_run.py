#!/usr/bin/env python3
"""
account_production_run.py — first run of the account_production operator.

Reads the four residue cases (the same texts the residue test used) plus two
controls with no false account (session notes), tags each with
account_production at the usual 3 votes, and writes account_production_run.json
(snapshot, overwritten). Nothing is written to the inference store.

The bar: the four cases read as the residue items say (sketch,
candidate_account_production.md), with votes unanimous; the controls read `unmarked`.

Usage:
    python3 account_production_run.py
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OPS = HERE.parent.parent
sys.path[:0] = [str(HERE), str(OPS)]

import residue                       # sets PRIVACY_GATE off; public cases
import account_production_operator as ap
from vivify_core import read_json, write_json

SESSIONS = OPS / "inferences" / "claude_code_sessions"
CONTROLS = {
    "control_backup": SESSIONS / "backup_recoverability/assertive_declaration/inf_bbe9c5e0.json",
    "control_pivot":  SESSIONS / "directory_name_preservation/backup_root_pivot/inf_24c79698.json",
}


def main():
    texts = {name: residue.load_case(name, spec)[0] for name, spec in residue.CASES.items()}
    texts.update({name: read_json(p)["raw_text"] for name, p in CONTROLS.items()})
    out = {}
    for name, text in texts.items():
        rec = ap.run({"raw_text": text})["logos"]["account_production"]
        v = rec.get("_votes") or {}
        out[name] = rec
        print(f"{name:<15} {rec['mode']:<13} votes {v.get('agreed', '?')}/{v.get('n', '?')}", flush=True)
        write_json(HERE / "account_production_run.json", out)


if __name__ == "__main__":
    main()

# llm: claude-opus-5-5 | 2026-10-17 | repos/vivify-operators/experiments/residue/account_production_run.py | created — first run of account_production on the four residue cases plus two no-false-account controls, 3 votes, snapshot to account_production_run.json
