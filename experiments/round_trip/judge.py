#!/usr/bin/env python3
"""
judge.py — the blind round-trip judging, done by script instead of web chats.

Until 2026-10-22 every verdict was a packet John pasted into ChatGPT or Gemini and a
reply pasted back. This sends the same packets to non-Anthropic judges through the
existing transports, writes each reply to its own file, and opens the key only when
every expected verdict file is present.

- packets are rebuilt from the committed readings and the stored case records, with the
  text of the 2026-10-22 judging pages, plus two closing lines asking for a machine-read
  PICK and CONFIDENCE
- packets are built in memory and never written into the repo: they carry the full case
  record (Innocence Project text)
- run   skips any verdict already on disk, so a run that hits a quota resumes where it stopped
- score refuses while any verdict is missing; only then is the key file read
- for the four 2026-10-22 experiments, score also checks the pattern the web judges gave
  (EXPECTED below); that is the calibration: the script is trusted only if it reproduces them

Usage:
    source <(unseal_it -o - ~/.secrets/keys.env.age)      # with set -a
    python3 judge.py packets v5B                  # list packet ids and sizes, no calls
    python3 judge.py run v5B [--judge MODEL ...]  # judge every packet, write judged/
    python3 judge.py score v5B [--judge MODEL ...]
"""

import os
import re
import sys
import json
import time
import argparse
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "lib"))
os.environ.setdefault("PRIVACY_GATE", "off")          # public Innocence Project cases
os.environ.setdefault("GEMINI_TIMEOUT", "300")        # 120s timed out on these packets
os.environ.setdefault("GEMINI_503_RETRIES", "1")      # retried 503s spend the free quota
from vivify_core import llm_call_model, LLMUnavailable

# gemini:  plain worker, free tier = 20 requests/day per model (14 calibration packets fit)
# groq:    the panel model already used by web_research, a second model maker
JUDGES = ("gemini:gemini-3.8-flash", "groq:openai/gpt-oss-120b")

FIELD = REPO / "inferences" / "field"
CASES = {"W": ("washington", "earl-washington-jr", FIELD / "inf_a3d99808.json"),
         "S": ("sutton", "josiah-sutton", FIELD / "inf_285ae7ab.json")}

# expected = what the web judges gave on 2026-10-22
#   real       every pick is the real reading
#   no_switch  each judge picks the same reading on both records (choosing on quality)
#   switch     each judge's pick follows the record, and every pick is correct
EXPERIMENTS = {
    "v3":  {"dir": "v3_washington", "key": "v3_washington/KEY.txt", "kind": "shuffle",
            "labels": ("M", "N"), "expected": "real"},
    "v4":  {"dir": "v4_identity", "key": "v4_identity/KEY.txt", "kind": "identity",
            "labels": ("J", "K"), "expected": "no_switch"},
    "v5A": {"dir": "v5_identity/arm_A", "key": "v5_identity/KEY_A.txt", "kind": "identity",
            "labels": ("J", "K"), "expected": "no_switch"},
    "v5B": {"dir": "v5_identity/arm_B", "key": "v5_identity/KEY_B.txt", "kind": "identity",
            "labels": ("J", "K"), "expected": "switch"},
    "v6":  {"dir": "v6_identity", "key": "v6_identity/KEY.txt", "kind": "identity",
            "labels": ("X", "Y"), "expected": None},
}

SHUFFLE_INTRO = (
    "You are judging a blind test. A system reduced one real case to coded descriptors "
    "(no text, no names). Two readings, {a} and {b}, were then written by a model that saw only the "
    "descriptors and never the case. One reading was written from this case's real descriptors. "
    "The other was written from descriptors that had been shuffled, so they no longer fit the case.\n\n"
    "Below are the case record and both readings.\n\n"
    "Answer:\n1. Which reading was written from the real descriptors: {a} or {b}?\n")
IDENTITY_INTRO = (
    "You are judging a blind test. A system reduced real cases to coded descriptors "
    "(no text, no names). Two readings, {a} and {b}, were then written by a model. Each reading was "
    "written from the descriptors of ONE case, and the model never saw any case record. One reading "
    "was written from the descriptors of the case below. The other was written from the descriptors "
    "of a different real case of the same broad kind.\n\n"
    "Below are the case record and both readings.\n\n"
    "Answer:\n1. Which reading was written from THIS case's descriptors: {a} or {b}?\n")
COMMON = (
    "2. Your confidence, from 50% (a guess) to 100% (certain).\n"
    "3. Your reasons in 3 to 5 bullets. Point to specific places in the case record where each "
    "reading fits or contradicts it.\n"
    "4. If anything other than fit to the case influenced your decision, say what.\n\n"
    "Pick one; do not hedge between them.\n\n")
CLOSING = ("\nEnd your answer with exactly these two lines:\n"
           "PICK: <the letter of the reading you chose>\nCONFIDENCE: <a number from 50 to 100>%\n")


def record(case):
    _, _, path = CASES[case]
    paras = [p.strip() for p in json.loads(path.read_text())["raw_text"].split("\n\n") if p.strip()]
    return "\n\n".join(paras)


def packets(exp):
    """{packet id: text}. Shuffle ids are the first label (M, N); identity ids are the
    record then the first label (WJ, WK, SJ, SK), as on the judging pages."""
    spec = EXPERIMENTS[exp]
    a, b = spec["labels"]
    exp_dir = HERE / spec["dir"]
    reading = {l: (exp_dir / f"reading_{l}.md").read_text().rstrip("\n") for l in (a, b)}
    intro = (SHUFFLE_INTRO if spec["kind"] == "shuffle" else IDENTITY_INTRO).format(a=a, b=b) + COMMON
    records = ("W",) if spec["kind"] == "shuffle" else ("W", "S")
    out = {}
    for case in records:
        for first in (a, b):
            second = b if first == a else a
            pid = first if spec["kind"] == "shuffle" else case + first
            out[pid] = (intro + f"=== THE CASE (Innocence Project, {CASES[case][1]}) ===\n\n" + record(case)
                        + f"\n\n=== READING {first} ===\n\n{reading[first]}\n\n=== READING {second} ===\n\n"
                        + f"{reading[second]}\n" + CLOSING)
    return out


def judge_slug(model_id):
    return re.sub(r"[^A-Za-z0-9.-]+", "_", model_id)


def verdict_path(exp, model_id, pid):
    return HERE / EXPERIMENTS[exp]["dir"] / "judged" / f"{judge_slug(model_id)}_{pid}.md"


def parse_verdict(text, labels):
    """(pick, confidence) from the closing lines; the last PICK line wins.

    Fallback when a judge drops the closing lines (gpt-oss did, 2026-10-23): the pick is
    the bold label on the answer-1 line (or on the next line when
    that line only restates the question), else its single label; the confidence is the first
    percentage. None when nothing is found."""
    picks = re.findall(r"PICK:\s*\**\s*([A-Z])\b", text)
    confs = re.findall(r"CONFIDENCE:\**\s*\**\s*(\d{2,3})\s*%?", text, flags=re.IGNORECASE)
    pick = picks[-1] if picks and picks[-1] in labels else None
    if pick is None and not picks:
        lines = text.splitlines()
        i = next((n for n, l in enumerate(lines) if re.match(r"\W*1\b", l)), None)
        line = "" if i is None else lines[i]
        if i is not None and re.search(r"\?\W*$", line):          # question restated, answer below
            line = next((l for l in lines[i + 1:] if l.strip()), "")
        bold = [x for x in re.findall(r"\*\*([A-Z])\*\*", line) if x in labels]
        plain = [x for x in re.findall(r"\b([A-Z])\b", line) if x in labels]
        pick = (bold or plain or [None])[-1] if bold or len(set(plain)) == 1 else None
    if not confs:
        confs = re.findall(r"(\d{2,3})\s*%", text)[:1]
    return pick, (int(confs[-1]) if confs else None)


def parse_key(text):
    """'J = sutton K = washington' -> {'J': 'sutton', 'K': 'washington'}"""
    return dict(re.findall(r"\b([A-Z])\s*=\s*(\w+)", text))


def call_judge(text, model_id, sleep=time.sleep):
    """One verdict. A per-minute 429 (groq's token-per-minute limit on long packets) waits
    65s and retries, up to 4 tries; a per-day quota raises at once, so run() can stop that judge."""
    for attempt in range(4):
        try:
            return llm_call_model(text, model_id, sensitive=False)
        except LLMUnavailable as e:
            msg = str(e)
            if "PerDay" in msg or "429" not in msg or attempt == 3:
                raise
            sleep(65)


def run(exp, judges):
    for model_id in judges:
        for pid, text in packets(exp).items():
            out = verdict_path(exp, model_id, pid)
            if out.exists():
                print(f"{exp} {model_id} {pid}: on disk, skipped")
                continue
            try:
                reply = call_judge(text, model_id)
            except LLMUnavailable as e:
                print(f"{exp} {model_id} {pid}: UNAVAILABLE {e}", flush=True)
                if "PerDay" in str(e):
                    print(f"{exp} {model_id}: daily quota spent, judge stopped for this run", flush=True)
                    break
                continue
            out.parent.mkdir(exist_ok=True)
            out.write_text(f"# Verdict — {exp} — {model_id} — packet {pid}\n\n{reply.strip()}\n")
            pick, conf = parse_verdict(reply, EXPERIMENTS[exp]["labels"])
            print(f"{exp} {model_id} {pid}: written ({pick or '?'} {conf or '?'}%)", flush=True)


def truth(exp, pid, key):
    """The label that is correct for packet pid."""
    spec = EXPERIMENTS[exp]
    if spec["kind"] == "shuffle":
        return next(l for l, v in key.items() if v == "real")
    case = CASES[pid[0]][0]
    return next(l for l, v in key.items() if v == case)


def pattern(exp, rows):
    """Each judge's pattern: real / switch / no_switch / mixed, from its rows."""
    spec = EXPERIMENTS[exp]
    if spec["kind"] == "shuffle":
        return "real" if all(r["correct"] for r in rows) else "mixed"
    by_record = {}
    for r in rows:
        by_record.setdefault(r["pid"][0], set()).add(r["pick"])
    if any(len(p) != 1 for p in by_record.values()):
        return "mixed"                           # the order changed the pick on one record
    if by_record["W"] == by_record["S"]:
        return "no_switch"
    return "switch" if all(r["correct"] for r in rows) else "mixed"


def score(exp, judges):
    spec = EXPERIMENTS[exp]
    ids = list(packets(exp))
    missing = [verdict_path(exp, m, p).name for m in judges for p in ids
               if not verdict_path(exp, m, p).exists()]
    if missing:
        sys.exit(f"{exp}: {len(missing)} verdict(s) missing, key stays closed: {', '.join(missing)}")
    key = parse_key((HERE / spec["key"]).read_text())      # read only once every verdict is in
    lines = [f"# Scripted judging — {exp} — score",
             f"Key: {' '.join(f'{l} = {v}' for l, v in key.items())} ({spec['key']}, opened after "
             f"{len(judges) * len(ids)} verdicts).", "",
             "| Judge | Packet | Pick | Conf | Correct |", "|---|---|---|---|---|"]
    patterns = {}
    for model_id in judges:
        rows = []
        for pid in ids:
            pick, conf = parse_verdict(verdict_path(exp, model_id, pid).read_text(), spec["labels"])
            rows.append({"pid": pid, "pick": pick, "correct": pick == truth(exp, pid, key)})
            lines.append(f"| {model_id} | {pid} | {pick or '?'} | {conf if conf is not None else '?'}% "
                         f"| {'yes' if pick == truth(exp, pid, key) else 'no'} |")
        patterns[model_id] = pattern(exp, rows)
    lines.append("")
    for model_id, p in patterns.items():
        lines.append(f"- {model_id}: pattern **{p}**")
    if spec.get("expected"):
        match = [m for m, p in patterns.items() if p == spec["expected"]]
        lines.append(f"- Web judges' pattern (2026-10-22): **{spec['expected']}**. "
                     f"Matched by {len(match)} of {len(patterns)} judges: {', '.join(match) or 'none'}.")
    text = "\n".join(lines) + "\n"
    (HERE / spec["dir"] / "judged" / "SCORE.md").write_text(text)
    print(text)
    return patterns


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=("packets", "run", "score"))
    ap.add_argument("experiment", choices=sorted(EXPERIMENTS))
    ap.add_argument("--judge", action="append", help=f"model id (repeatable); default {', '.join(JUDGES)}")
    args = ap.parse_args()
    judges = args.judge or list(JUDGES)
    if args.command == "packets":
        for pid, text in packets(args.experiment).items():
            print(f"{pid}: {len(text.encode())} bytes")
    elif args.command == "run":
        run(args.experiment, judges)
    else:
        score(args.experiment, judges)


if __name__ == "__main__":
    main()

# llm: claude-opus-5-5 | 2026-10-23 | repos/vivify-operators/experiments/round_trip/judge.py | created — scripted blind judging: packets rebuilt from committed readings (web-page text + PICK/CONFIDENCE lines), one verdict file per judge and packet, key read only when every verdict is in, calibration against the 2026-10-22 web pattern
# llm: claude-opus-5-5 | 2026-10-23 | repos/vivify-operators/experiments/round_trip/judge.py | after the first calibration run: fallback pick/confidence parse when the closing lines are dropped, 65s retry on per-minute 429, judge stopped on a per-day quota, Gemini timeout 300s
# llm: claude-opus-5-5 | 2026-10-24 | repos/vivify-operators/experiments/round_trip/judge.py | score names which judges matched the web pattern, instead of one all-judges verdict
# llm: claude-opus-5-5 | 2026-10-24 | repos/vivify-operators/experiments/round_trip/judge.py | added experiment v6 (case identity, X/Y, no web pattern to match)
# llm: claude-opus-5-5 | 2026-10-25 | repos/vivify-operators/experiments/round_trip/judge.py | GEMINI_503_RETRIES=1, so an overloaded Gemini gives up early and keeps the quota
