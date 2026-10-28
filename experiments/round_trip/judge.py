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
from vivify_core import llm_call_model, LLMUnavailable, _write_usage

# gemini:  plain worker, free tier = 20 requests/day per model (14 calibration packets fit)
# groq:    the panel model already used by web_research, a second model maker
# clef:    Cloudflare's decision model, probabilities instead of text (see CLEF_URL)
JUDGES = ("gemini:gemini-3.8-flash", "groq:openai/gpt-oss-120b")

FIELD = REPO / "inferences" / "field"
FAMILY = Path.home() / "private_field" / "family" / "unclustered"
# record code: (case, slug, inference file, source shown in the packet header)
CASES = {"W": ("washington", "earl-washington-jr", FIELD / "inf_a3d99808.json", "Innocence Project"),
         "S": ("sutton", "josiah-sutton", FIELD / "inf_285ae7ab.json", "Innocence Project"),
         "C": ("cotton", "ronald-cotton", FIELD / "inf_f39647fd.json", "Innocence Project"),
         # Brown is read from the private field (NRE text kept out of the public repo)
         "B": ("brown", "anthony-t-brown", Path.home() / "private_field" / "field" / "inf_10247710.json",
               "National Registry of Exonerations"),
         # Brown again, the NRE text selected to the Innocence Project level under CASE_TELLING_STANDARD.md
         "N": ("brown", "anthony-t-brown", Path.home() / "private_field" / "field" / "inf_539d6902.json",
               "National Registry of Exonerations"),
         # the four unseen PA family cases (bond's unseen exam, 2026-10-28), private field
         "R": ("carrero", "carrero-v-lopez", FAMILY / "inf_7911d19a.json", "CourtListener"),
         "E": ("weliver", "weliver-v-ortiz", FAMILY / "inf_9a742020.json", "CourtListener"),
         "T": ("ss_v_tj", "s-s-v-t-j", FAMILY / "inf_f3ceffac.json", "CourtListener"),
         "G": ("in_re_gms", "in-re-g-m-s", FAMILY / "inf_03b28608.json", "CourtListener")}

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
    # many readings per packet: one record against all four readings, two orders per record
    "v7":  {"dir": "v7_identity", "key": "v7_identity/KEY.txt", "kind": "multi",
            "labels": ("F", "G", "H", "L"), "records": ("S", "W", "C", "B"), "expected": None},
    # v7 with each account value's definition passed to the decoder beside the value
    "v8":  {"dir": "v8_identity", "key": "v8_identity/KEY.txt", "kind": "multi",
            "labels": ("P", "Q", "R", "T"), "records": ("S", "W", "C", "B"), "expected": None},
    # v8 with Brown's telling selected like the others (record N)
    "v9":  {"dir": "v9_identity", "key": "v9_identity/KEY.txt", "kind": "multi",
            "labels": ("D", "E", "U", "V"), "records": ("S", "W", "C", "N"), "expected": None},
    # v9 plus every account element, coded into the three account values
    "v10": {"dir": "v10_identity", "key": "v10_identity/KEY.txt", "kind": "multi",
            "labels": ("K", "M", "X", "Z"), "records": ("S", "W", "C", "N"), "expected": None},
    # v10's inputs, decoder told to stay at the coordinates' level (no concrete picture)
    "v11": {"dir": "v11_identity", "key": "v11_identity/KEY.txt", "kind": "multi",
            "labels": ("B", "G", "J", "Y"), "records": ("S", "W", "C", "N"), "expected": None},
    # v10's recipe on the four unseen PA family cases; readings and verdicts stay in the private field
    "fam1": {"dir": str(Path.home() / "private_field" / "family" / "identity"),
             "key": str(Path.home() / "private_field" / "family" / "identity" / "KEY.txt"), "kind": "multi",
             "labels": ("A", "D", "H", "Q"), "records": ("R", "E", "T", "G"), "expected": None},
    # fam1 plus bond (residue.py's add_bond: coordinates and event structure, no signal text)
    "fam2": {"dir": str(Path.home() / "private_field" / "family" / "identity_bond"),
             "key": str(Path.home() / "private_field" / "family" / "identity_bond" / "KEY.txt"), "kind": "multi",
             "labels": ("F", "J", "P", "V"), "records": ("R", "E", "T", "G"), "expected": None},
    # fam2 with ages and places stripped from bond's `between` (fam2's 4/4 rode on them)
    "fam3": {"dir": str(Path.home() / "private_field" / "family" / "identity_roles"),
             "key": str(Path.home() / "private_field" / "family" / "identity_roles" / "KEY.txt"), "kind": "multi",
             "labels": ("L", "N", "U", "W"), "records": ("R", "E", "T", "G"), "expected": None},
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
MULTI_INTRO = (
    "You are judging a blind test. A system reduced real cases to coded descriptors "
    "(no text, no names). {n} readings, {labels}, were then written by a model. Each reading was "
    "written from the descriptors of ONE case, and the model never saw any case record. One reading "
    "was written from the descriptors of the case below. The others were written from the descriptors "
    "of different real cases of the same broad kind.\n\n"
    "Below are the case record and all {n} readings.\n\n"
    "Answer:\n1. Which reading was written from THIS case's descriptors: {choices}?\n")
COMMON = (
    "2. Your confidence, from 50% (a guess) to 100% (certain).\n"
    "3. Your reasons in 3 to 5 bullets. Point to specific places in the case record where each "
    "reading fits or contradicts it.\n"
    "4. If anything other than fit to the case influenced your decision, say what.\n\n"
    "Pick one; do not hedge between them.\n\n")
CLOSING = ("\nEnd your answer with exactly these two lines:\n"
           "PICK: <the letter of the reading you chose>\nCONFIDENCE: <a number from 50 to 100>%\n")


def record(case):
    path = CASES[case][2]
    paras = [p.strip() for p in json.loads(path.read_text())["raw_text"].split("\n\n") if p.strip()]
    return "\n\n".join(paras)


def multi_packets(exp):
    """{packet id: text} for one record against every reading. Ids are the record code
    then the order: 'a' rotates the labels by the record's position, 'b' reverses that
    order, so each reading appears in a different place across the records."""
    spec = EXPERIMENTS[exp]
    labels = list(spec["labels"])
    exp_dir = HERE / spec["dir"]
    reading = {l: (exp_dir / f"reading_{l}.md").read_text().rstrip("\n") for l in labels}
    intro = MULTI_INTRO.format(n=len(labels), labels=", ".join(labels),
                               choices=", ".join(labels[:-1]) + " or " + labels[-1]) + COMMON
    out = {}
    for i, case in enumerate(spec["records"]):
        rotated = labels[i % len(labels):] + labels[:i % len(labels)]
        for tag, order in (("a", rotated), ("b", rotated[::-1])):
            body = "".join(f"\n\n=== READING {l} ===\n\n{reading[l]}" for l in order)
            out[case + tag] = (intro + f"=== THE CASE ({CASES[case][3]}, {CASES[case][1]}) ===\n\n"
                               + record(case) + body + "\n" + CLOSING)
    return out


def packets(exp):
    """{packet id: text}. Shuffle ids are the first label (M, N); identity ids are the
    record then the first label (WJ, WK, SJ, SK), as on the judging pages."""
    spec = EXPERIMENTS[exp]
    if spec["kind"] == "multi":
        return multi_packets(exp)
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


# clef: Cloudflare's decision model (Workers AI). Not a chat model: it takes a state and
# typed questions and returns a probability for every allowed option, with no reasons.
#   clef:clef        options offered in label order (X, Y)
#   clef:clef@swap   options offered in reverse order, to measure option-order bias
#   clef:clef@rep    the same call as clef:clef again, to measure determinism
#   clef:clef@json   the state as labelled JSON fields (case_record, reading_X, ...)
# clef-flash works in place of clef. Reads CLOUDFLARE_ACCOUNT_ID / CLOUDFLARE_API_TOKEN.
CLEF_URL = "https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/@cf/cloudflare/{model}"


def clef_request(packet, labels, swap=False, structured=False):
    """The Clef body for one packet: the blind-test framing and question go in the
    instructions, the case record and both readings in the state, one choice question.

    structured=True (@json) passes the state as labelled JSON fields instead of one
    flat string, keeping the packet's reading order: Cloudflare's suggestion for the
    two calibration misses, which both picked the reading placed first."""
    head, rest = packet.split("=== THE CASE", 1)
    state = "=== THE CASE" + (rest[:-len(CLOSING)] if rest.endswith(CLOSING) else rest)
    if structured:
        parts = re.split(r"\n*=== READING ([A-Z]) ===\n*", state)
        record = parts[0].split("===\n", 1)[1].strip()
        state = {"case_record": record}
        for label, text in zip(parts[1::2], parts[2::2]):
            state[f"reading_{label}"] = text.strip()
    framing = head.split("Below are the case record")[0].strip()
    question = next(l for l in head.splitlines() if l.startswith("1. "))[3:]
    order = list(reversed(labels)) if swap else list(labels)
    return {"model": None, "state": state,
            "questions": {"pick": {"type": "choice", "instructions": framing + "\n\n" + question,
                                   "criteria": {l: (f"reading_{l}" if structured else f"Reading {l}")
                                                for l in order}}}}


def call_clef(packet, model_id, labels):
    """One Clef verdict, written as text with the same PICK/CONFIDENCE lines as the chat judges,
    plus the full per-option probabilities."""
    import urllib.request
    import urllib.error
    model, _, variant = model_id.split(":", 1)[1].partition("@")
    key, account = os.environ.get("CLOUDFLARE_API_TOKEN"), os.environ.get("CLOUDFLARE_ACCOUNT_ID")
    if not key or not account:
        raise LLMUnavailable("CLOUDFLARE_API_TOKEN / CLOUDFLARE_ACCOUNT_ID not set — source the sealed keys.env first")
    body = clef_request(packet, labels, swap=(variant == "swap"), structured=(variant == "json"))
    body["model"] = model
    req = urllib.request.Request(CLEF_URL.format(account=account, model=model), method="POST",
                                 data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                                          "User-Agent": "vivify-operators/1.0"})
    t = time.time()
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            ans = json.loads(resp.read())["result"]["answers"]["pick"]
    except urllib.error.HTTPError as e:
        err = f"clef request failed: HTTP {e.code}: {e.read().decode(errors='replace')[:200]}"
        _write_usage("clef", model, time.time() - t, len(packet), False, err)
        raise LLMUnavailable(err)
    except (OSError, KeyError, ValueError) as e:
        _write_usage("clef", model, time.time() - t, len(packet), False, e)
        raise LLMUnavailable(f"clef request failed: {e}")
    _write_usage("clef", model, time.time() - t, len(packet), True)
    p = ans["probabilities"]
    return (f"Options offered in the order {', '.join(body['questions']['pick']['criteria'])}.\n"
            f"Probabilities: {json.dumps(p)}; Clef confidence {ans.get('confidence')}.\n\n"
            f"PICK: {ans['choice']}\nCONFIDENCE: {round(100 * p[ans['choice']])}%\n")


def call_judge(text, model_id, sleep=time.sleep, labels=("J", "K")):
    """One verdict. A per-minute 429 (groq's token-per-minute limit on long packets) waits
    65s and retries, up to 4 tries; a per-day quota raises at once, so run() can stop that judge."""
    for attempt in range(4):
        try:
            if model_id.startswith("clef:"):
                return call_clef(text, model_id, labels)
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
                reply = call_judge(text, model_id, labels=EXPERIMENTS[exp]["labels"])
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
    if spec["kind"] == "multi":                  # a record counts only if every order picked right
        right = {c for c in spec["records"]
                 if all(r["correct"] for r in rows if r["pid"][0] == c)}
        stable = all(len({r["pick"] for r in rows if r["pid"][0] == c}) == 1 for c in spec["records"])
        return f"{len(right)}/{len(spec['records'])} records{'' if stable else ', order moved a pick'}"
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
# llm: claude-opus-5-5 | 2026-10-25 | repos/vivify-operators/experiments/round_trip/judge.py | clef: judges (Cloudflare decision model): one choice question per packet, per-option probabilities in the verdict, @swap (reversed option order) and @rep (repeat) variants
# llm: claude-opus-5-5 | 2026-10-25 | repos/vivify-operators/experiments/round_trip/judge.py | clef @json variant: state as labelled JSON fields (Cloudflare's suggestion for the position-sensitive misses)
# llm: claude-opus-5-5 | 2026-10-26 | repos/vivify-operators/experiments/round_trip/judge.py | multi kind (one record against every reading, two orders per record) for the four-case v7; CASES gains Cotton, Brown (private field) and a per-case source label
# llm: claude-opus-5-5 | 2026-10-27 | repos/vivify-operators/experiments/round_trip/judge.py | v8 experiment: v7's four cases, account values decoded with their definitions
# llm: claude-opus-5-5 | 2026-10-27 | repos/vivify-operators/experiments/round_trip/judge.py | v9 experiment and record N: Brown's NRE text selected under the telling standard
# llm: claude-opus-5-5 | 2026-10-27 | repos/vivify-operators/experiments/round_trip/judge.py | v10 experiment: v9 plus every account element
# llm: claude-opus-5-5 | 2026-10-27 | repos/vivify-operators/experiments/round_trip/judge.py | v11 experiment: v10's inputs, concrete-picture instruction fenced
# llm: claude-opus-5-5 | 2026-10-28 | repos/vivify-operators/experiments/round_trip/judge.py | fam1 experiment: v10's identity recipe on the four unseen PA family cases (records R/E/T/G from the private family field)
# llm: claude-opus-5-5 | 2026-10-28 | repos/vivify-operators/experiments/round_trip/judge.py | fam2 experiment: fam1 with bond in the decoder input
# llm: claude-opus-5-5 | 2026-10-28 | repos/vivify-operators/experiments/round_trip/judge.py | fam3 experiment: fam2 with ages and places stripped from bond roles
