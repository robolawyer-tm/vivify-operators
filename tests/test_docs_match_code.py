#!/usr/bin/env python3
"""Focused test: no document may restate the superseded lexical tension formula,
and no document may cite a path that has gone away.

Regression guard, written after the failure it guards against. tension_score.py
was rewired on 2026-07-13 to three numbers — predicted / confirmed /
calibration_delta — because the original lexical score,

    1.0 - (shared_keywords / total_unique_keywords)

pinned at 1.0 storewide: the left and right vocabularies are disjoint by design,
so their intersection is empty by construction and the score carried no
information.

The code changed. Four documents did not. On 2026-09-15 an ingest bundle went to
three outside models; two of them read the stale documents rather than the
docstring and handed the dead formula back. One spent its longest section
re-deriving, correctly, why a formula that no longer exists cannot work. The
other quoted it approvingly as the project's "Core Insight". The instrument was
right and every description of it was wrong, and nothing in the repo noticed.

Instances found and closed on 2026-09-16:
  - README.md:14 and :98-109   (intro claim + the full formula section)
  - lib/keyword_graph.py:80    (orphaned implementation, imported by nothing)
  - FLOW.md                    (untracked May-8 copy of the retired repo's; deleted)
  - pillars/FLOW.md:17,41,51   (the declared source of truth the others derived from)

Two deliberate mentions survive, each required to carry its own marker on the same
line: README.md's "Superseded — do not reintroduce" note, and AUTHORING_BRIEF.md's
account of the episode. Keeping the dead formula visible with the reason it died is
what stops the next reader re-deriving it — which is what a reader did.

What check 5 does and does not catch. It verifies that every repo-local path a
document cites still exists, and that a cited line number is within that file. It
catches a deleted or renamed file — FLOW.md is the worked example — and a citation
that points past the end of a truncated one. It does NOT catch semantic drift: when
lib/keyword_graph.py:80 stopped being the tension implementation, the file still
existed and still had eighty lines. Verifying that a cited line still means what the
citing document claims is not attempted here.

Scope limit, stated rather than hidden: this scans THIS repo only. pillars/FLOW.md
was the root instance and lives in a sibling repo, so it is not covered here — a
test that reached across repos would fail for anyone who cloned only this one.
Citations beginning "pillars/" are skipped for the same reason.

No LLM calls. No network. Pure filesystem scan.

Run standalone: python3 tests/test_docs_match_code.py  (exit 0 = pass)
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SELF = Path(__file__).resolve()

# The dead SEMANTICS, separate from the dead formula. reify.py and
# README_reify.md carried no formula at all — they described tension as left/right
# keyword divergence in prose, and reify's copy was an executable instruction to a
# generating model, not a doc. The formula check could never have caught either.
# "left and right keyword sets" on its own is a TRUE statement — README.md states
# the duality invariant that way, and that invariant is exactly WHY the lexical
# score carried no information. What is dead is tying those sets to tension. So the
# phrase only counts when a tension word sits near it, and "near" has to span lines
# because the original wording wrapped: "The tension_score shapes the output — a
# score of\n1.0 means left and right keyword sets share nothing".
SEM_PHRASE = re.compile(
    r"(left[ -]and[ -]right|left/right)\s+keyword\s+(sets?|divergence|overlap)",
    re.IGNORECASE,
)
SEM_NEARBY = re.compile(r"tension|diverg|share nothing|resists its", re.IGNORECASE)
SEM_WINDOW = 220

# The formula in every spelling it has actually appeared in: with and without
# the _keywords suffix, with and without parens, spaces or underscores as the
# word separator. Anchored on "1.0 -" followed by a shared/total ratio.
DEAD_FORMULA = re.compile(
    r"1\.0\s*[-−]\s*\(?\s*shared[ _]?(?:keywords)?\s*/\s*total[ _]?unique",
    re.IGNORECASE,
)

# The only sanctioned mentions: file -> marker that must sit on the same line.
# Anywhere else, in any file, is a regression.
# file -> markers that may sit on a line naming the dead formula or semantics.
# A line carrying any of its file's markers is a deliberate historical reference.
SANCTIONED = {
    "README.md":          ("Superseded — do not reintroduce",),
    "AUTHORING_BRIEF.md": ("the formula it replaced",),
    "reify.py":           ("The old prompt described",),
    "README_reify.md":    ("The old text described",),
    # The authoritative statement of what was replaced. If this stops naming the
    # thing it superseded, the repo has lost its own record of the change.
    "tension_score.py":   ("replacing the dead lexical",),
}

# A provenance footer's entire job is to say what changed, so it will name the
# thing that was removed. Excluding them by shape rather than listing each one
# keeps the exemption from needing maintenance every time a file is signed.
PROVENANCE = re.compile(r"^\s*(#|<!--)\s*llm:\s")

# Files that carry the formula as a TEST FIXTURE rather than as a claim. A test
# needs the real strings — test_claim_check's whole point is that U+2212 MINUS
# and ASCII hyphen must normalise together, and obfuscating the fixture would
# destroy the check. The exemption is per-file, named here, and itself guarded:
# each listed file must still declare why, so the exemption cannot outlive its
# reason the way the formula outlived the code.
FIXTURE_FILES = {
    "tests/test_claim_check.py": "FIXTURE: known-false formula strings",
}

# A backticked repo path, with an optional :line or :line-line suffix.
CITATION = re.compile(r"`([A-Za-z0-9_][A-Za-z0-9_./-]*\.(?:py|md|json))(?::(\d+)(?:-(\d+))?)?`")

SKIP_DIRS = {".git", "__pycache__", "inferences", "experiments", ".claude"}
SCAN_SUFFIXES = {".md", ".py", ".json", ".txt"}

failures = []


def check(label, condition, detail=""):
    if condition:
        print(f"  ok   {label}")
    else:
        failures.append(label)
        print(f"  FAIL {label}{(' — ' + detail) if detail else ''}")


def scan_files():
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path.suffix not in SCAN_SUFFIXES:
            continue
        if path.resolve() == SELF:
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts):
            continue
        yield path


print("no document restates the superseded lexical tension formula:")

# 1. the formula appears nowhere except its sanctioned, marked lines
offenders = []
sanctioned_hits = {name: 0 for name in SANCTIONED}
for path in scan_files():
    rel = str(path.relative_to(ROOT))
    try:
        lines = path.read_text(errors="replace").splitlines()
    except OSError:
        continue
    marker = SANCTIONED.get(rel)
    for n, line in enumerate(lines, 1):
        if not DEAD_FORMULA.search(line):
            continue
        if PROVENANCE.match(line):
            continue          # a signing footer describing its own change
        if marker and any(m in line for m in marker):
            sanctioned_hits[rel] += 1
        elif rel in FIXTURE_FILES:
            continue          # a fixture is not a document making a claim
        else:
            offenders.append(f"{rel}:{n}")

    # Semantics: whole-file with a proximity window, because the dead wording wraps.
    # Provenance footers are blanked first, keeping line numbers intact: they name
    # the superseded tension by design, and a footer sitting within the window of an
    # innocent sentence would otherwise convict it. That is not hypothetical — the
    # duality invariant near the end of a signed file reads as an offence without this.
    whole = "\n".join("" if PROVENANCE.match(ln) else ln for ln in lines)
    for m in SEM_PHRASE.finditer(whole):
        lo = max(0, m.start() - SEM_WINDOW)
        window = whole[lo:m.end() + SEM_WINDOW]
        if not SEM_NEARBY.search(window):
            continue          # the duality invariant, stated truthfully
        n = whole.count("\n", 0, m.start()) + 1
        if PROVENANCE.match(lines[n - 1]):
            continue
        if marker and any(m2 in window for m2 in marker):
            sanctioned_hits[rel] += 1
        elif rel in FIXTURE_FILES:
            continue
        else:
            offenders.append(f"{rel}:{n}")

check("dead formula and semantics absent outside sanctioned lines",
      not offenders,
      f"found in {', '.join(offenders)}" if offenders else "")

# 2. each sanctioned mention is still there, exactly once. A repo that passed
#    check 1 by quietly deleting the "why it died" notes is worse, not better.
for name in SANCTIONED:
    check(f"{name} still records what the dead tension meant",
          sanctioned_hits[name] >= 1,
          f"expected a marked historical mention, found {sanctioned_hits[name]}")

# 2b. every fixture exemption still declares its reason. An exemption whose
#     justification has been deleted is how a guard quietly stops guarding.
for rel, declaration in FIXTURE_FILES.items():
    path = ROOT / rel
    check(f"{rel} still declares its fixture exemption",
          path.is_file() and declaration in path.read_text(errors="replace"),
          f"expected the marker {declaration!r}")

# 3. no second tension implementation. keyword_graph.tension_score() was the
#    orphan; nothing must define one outside tension_score.py again.
second_impls = []
for path in scan_files():
    if path.suffix != ".py" or path.name == "tension_score.py":
        continue
    try:
        text = path.read_text(errors="replace")
    except OSError:
        continue
    if re.search(r"^def tension_score\s*\(", text, re.MULTILINE):
        second_impls.append(str(path.relative_to(ROOT)))

check("exactly one tension implementation in the repo",
      not second_impls,
      f"also defined in {', '.join(second_impls)}" if second_impls else "")

# 4. the live vocabulary is what the docs actually describe. A repo that passed
#    1-3 by deleting every mention of tension would be worse, not better.
readme = (ROOT / "README.md").read_text(errors="replace")
for name in ("predicted", "confirmed", "calibration_delta"):
    check(f"README documents `{name}`", name in readme)

# 5. every repo-local path the reading instructions cite still resolves. FLOW.md
#    sat in the bundle for months naming a pipeline that no longer existed.
brief = ROOT / "AUTHORING_BRIEF.md"
check("AUTHORING_BRIEF.md is present", brief.is_file(),
      "the bundle would ship with no reading instructions")

if brief.is_file():
    text = brief.read_text(errors="replace")
    dangling = []
    for cited, start, end in CITATION.findall(text):
        if cited.startswith("pillars/"):      # sibling repo, deliberately unscanned
            continue
        target = ROOT / cited
        if not target.is_file():
            # a bare filename may legitimately live in a subdirectory
            matches = [p for p in ROOT.rglob(Path(cited).name)
                       if p.is_file()
                       and not any(part in SKIP_DIRS for part in p.relative_to(ROOT).parts)]
            if not matches:
                dangling.append(f"{cited} (no such file)")
                continue
            target = matches[0]
        last = max(int(start or 0), int(end or 0))
        if last:
            n_lines = len(target.read_text(errors="replace").splitlines())
            if last > n_lines:
                dangling.append(f"{cited} (cites line {last}, file has {n_lines})")

    check("every path AUTHORING_BRIEF.md cites still resolves",
          not dangling,
          "; ".join(dangling) if dangling else "")

print()
if failures:
    print(f"FAILED: {len(failures)} check(s) — {', '.join(failures)}")
    sys.exit(1)
print("All docs-match-code checks passed.")

# llm: claude-opus-5 | 2026-09-16 | repos/vivify-operators/tests/test_docs_match_code.py | created — regression guard: the superseded lexical tension formula must not reappear in any document, and no second tension implementation may be defined
# llm: claude-opus-5 | 2026-09-16 | repos/vivify-operators/tests/test_docs_match_code.py | two sanctioned formula mentions (README + AUTHORING_BRIEF), each marker-gated; added check 5 — every repo-local path the brief cites must resolve and cited line numbers must be in range
# llm: claude-opus-5 | 2026-09-16 | repos/vivify-operators/tests/test_docs_match_code.py | added FIXTURE_FILES — a test may hold the formula as a known-false fixture, but the exemption must be named here and the file must declare why
# llm: claude-opus-5 | 2026-09-19 | repos/vivify-operators/tests/test_docs_match_code.py | added DEAD_SEMANTICS — reify.py and README_reify.md described tension as left/right keyword divergence with no formula present, so the formula check could never have caught them, and reify's copy was a live prompt rather than a doc
# llm: claude-opus-5 | 2026-09-19 | repos/vivify-operators/tests/test_docs_match_code.py | exempt llm: provenance footers by shape and sanction tension_score.py's own docstring — both name the superseded tension because that is precisely their job
# llm: claude-opus-5 | 2026-09-19 | repos/vivify-operators/tests/test_docs_match_code.py | the semantics check now needs a tension word near the phrase, matched across lines — 'left and right keyword sets stay separate' is the duality invariant and true, and flagging it would have taught the next reader to ignore this test
# llm: claude-opus-5 | 2026-09-19 | repos/vivify-operators/tests/test_docs_match_code.py | blank provenance footers before proximity matching — a footer inside the window made a true statement of the duality invariant read as a reintroduction
