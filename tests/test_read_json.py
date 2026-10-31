#!/usr/bin/env python3
"""Focused test: read_json fails loudly on a missing file unless missing_ok.

It used to return {} for any missing path, so an operator given a wrong
relative path tagged an empty record and wrote it out as a new file
(recall test, 2026-10-30). Optional files (indexes, synonyms) pass
missing_ok=True and still read as empty.

Run standalone: python3 tests/test_read_json.py  (exit 0 = pass)
"""

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lib"))

from vivify_core import read_json

failures = []


def check(label, condition, detail=""):
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}  {detail}")
        failures.append(label)


with tempfile.TemporaryDirectory() as d:
    missing = Path(d) / "nope.json"
    try:
        read_json(missing)
        check("missing file raises", False, "no exception")
    except FileNotFoundError:
        check("missing file raises", True)
    check("missing_ok returns {}", read_json(missing, missing_ok=True) == {})
    present = Path(d) / "yes.json"
    present.write_text('{"a": 1}')
    check("present file reads", read_json(present) == {"a": 1})

    r = subprocess.run([sys.executable, str(ROOT / "bond_operator.py"), str(missing)],
                       capture_output=True, text=True, cwd=d)
    check("operator CLI on a missing path exits non-zero", r.returncode != 0, r.returncode)
    check("operator CLI writes nothing", not missing.exists())

print()
if failures:
    print(f"FAILED: {len(failures)} check(s) — {', '.join(failures)}")
    sys.exit(1)
print("All read_json checks passed.")

# llm: claude-opus-5-5 | 2026-10-30 | repos/vivify-operators/tests/test_read_json.py | created — read_json raises on a missing file unless missing_ok; operator CLI on a wrong path exits and writes nothing
