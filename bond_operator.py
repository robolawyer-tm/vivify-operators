#!/usr/bin/env python3
"""
bond_operator.py — logos tagging pass: the standing bonds an institution's act lands on

Reads a vivified inference and records, as far as the text shows, the bond between
people that the events in it affect most: its state before them, whether the account
the institution relies on takes it into its reasoning, what the events do to it and
who made the outcome, and whether the text records the bond itself as a danger.
Attaches logos.bond coordinates to the inference JSON.

Candidate coordinate (experiments/residue/candidate_bond.md). Theory-sourced (Bowlby;
continuing bonds; Bowen; Boss; Doka; Sbarra & Hazan), then demanded by the field: the
2026-10-26 residue test on four published family-court opinions lost family
relationships in all four, 12 of 59 items primarily about them in two blind topic
sorts (cm_v_mm-06/07/08/15, ecs_v_mcs-02/08, in_re_ejc-03/06/09/10, ss_v_kf-03/06).

- The prompt describes bonds and what happens to them only; it names no harm, no
  claim about separation and no purpose, so a pattern found is one it did not seek
- One value per coordinate, for the bond the events land on most; the others stay in
  bond_signals (decision 2026-10-26, as for account_production)
- The institution is one actor among others, not the frame (John, 2026-10-26: "the
  legal schema isn't the baseline ... participants find their better selves and create
  solutions that override judgements"). events lists every event as a record (order in
  the family's chronology, maker, whose account reports it, effect, whether the recorded
  reasoning takes it up, quote).
- effect, made_by and registered are DERIVED in code from the event that changed the
  bond most (CHANGE; ties to the later event), not asked of the model: asked for one
  summary value, it kept handing it to the last procedural act (an appeal's remand),
  the legal frame by the back door, and registered moved with prompt wording.
- Voted: standing and hazard (the events come with the modal draw); then, step 2,
  registered for each event of that fixed list, by its own majority
  (registered_votes): asked inside the event list it agreed in only 3 of 5 single
  draws on the main event, and each draw listed different events (2026-10-26)
  The residue had lost exactly these (ss_v_kf-03 an arrangement made before any court;
  ss_v_kf-09 the parents aligned against the court's own order). registered stays about
  the institution's account, which is the blind spot under study.
- Roles only in signals and `between`: never names (the court's anonymisation holds)
- Every bond is listed (bonds: id, roles, standing) and each event names the bonds it
  touched: the first acceptance run (2026-10-26) lost exactly the several-bond items
  (siblings separated, the two children's different outcomes) when only the main bond
  was kept. The main bond still carries the voted standing and hazard.
- made_by `members` = family members acting together (two parents' own arrangement
  included): in the first run a parents' informal arrangement came out `others`
- shape (hub | mesh | dyad) is deferred to its own step, so each change is measured alone
- Step 3, via: HOW each event reached the bond (distance | schedule | placement | status |
  conduct | other), voted per event from the event list alone, not the text. The decoder
  saw "reduced, made by institution" and could not tell a relocation from a cut in
  contact: ss_v_tj-14 (the friction comes from distance after a move) stayed partly
  recovered in every draw of the unseen exam (2026-10-28). The values are the mechanisms
  the 8 family cases' events show, read off their `what` lines.

_src: vivify-operators residue test on the family field (2026-10-26)
"""

import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "lib"))
from vivify_core import read_json, write_json, call_and_vote, call_and_validate, _vote_count

PROMPT = """You are reading the bonds between people, and the events that land on them.

A bond is a standing relationship of care or attachment between particular people:
parent and child, siblings, a grandparent and a grandchild, partners, or others the
text shows as bound to each other. List EVERY bond the text shows (each parent with
each child, siblings with each other, grandparents, others), give each an id, and say
which one the events affect most: the main bond. Events can be made by anyone: an institution's decision, an arrangement the
people make themselves (including one made before any institution was involved), a
move, an agreement, a refusal, an act by other family. Count only what happened to
the bond in fact; a request, proposal or argument is not an event until it is acted on.
Then describe the bonds as far as the text shows. Refer to people by
role only (mother, father, child aged 7, older sibling), never by name or initials.

standing — a bond's state before the events the text is about:
  secure    — an established bond with ongoing care or contact.
  strained  — the bond is present but interrupted, limited or in conflict.
  ruptured  — the bond was already broken before those events.
  unmarked  — the text shows no bond between particular people.

events — every event that happened to any of the bonds, in the order it happened in
the family's life (not the order the text tells it), each as a record:
  order       — 1, 2, 3 ... in the family's own chronology
  bonds       — the ids of the bonds the event touched
  what        — the event, in a few plain words
  made_by     — who made the event:
                institution — a court, agency or other institution, by its decision
                members     — members of the family acting together: an agreement or an
                              arrangement between them, including one between two parents
                              about their child, made before or outside any institution;
                              an order the court makes on their agreement is still theirs
                one_member  — one member of the family, on their own
                others      — people outside the family and outside the institution
  reported_by — whose account the text gives it from:
                institution — the institution's own finding, order or record
                member      — the words or claim of a family member
                others      — another person's account (a witness, an assessor)
                unclear     — the text does not say
  effect      — what the event did to the bond:
                preserved — the bond and its contact continue as they were
                reduced   — contact or care is cut back, but the bond continues
                severed   — the bond's contact or legal tie is ended
                restored  — contact or care is given back or increased
  words       — a short quote from the text

hazard — whether the text records the main bond itself as a danger to one of its members:
  none        — no such danger is recorded.
  alleged     — a danger is claimed but not found.
  established — a danger is found by the institution or shown in the text.

Text:
{text}

Return ONLY valid JSON:
{{
  "bonds": [{{"id": "B1", "between": "<roles, e.g. 'father and son aged 9'>",
             "standing": "<secure|strained|ruptured>"}}],
  "main_bond": "<id of the bond the events affect most, or none>",
  "between": "<the roles in the main bond>",
  "standing": "<the main bond's standing: secure|strained|ruptured|unmarked>",
  "hazard": "<none|alleged|established>",
  "bond_signals": ["<bond> (between <roles>): <words from the text>"],
  "events": [{{"order": <n>, "bonds": ["<id>"], "what": "<event>", "made_by": "<institution|members|one_member|others>",
              "reported_by": "<institution|member|others|unclear>",
              "effect": "<preserved|reduced|severed|restored>", "words": "<quote>"}}],
  "rationale": "<one sentence: why this bond is the one the events land on most>",
  "confidence": <0.0-1.0>
}}
"""


EVENT_ENUMS = {
    "made_by":     ("institution", "members", "one_member", "others"),
    "reported_by": ("institution", "member", "others", "unclear"),
    "effect":      ("preserved", "reduced", "severed", "restored"),
    "registered":  ("weighed", "mentioned", "absent"),
    "via":         ("distance", "schedule", "placement", "status", "conduct", "other"),
}
# How much an event changes the bond, for choosing the main event: a cut or a return
# counts more than continuity; ties go to the EARLIER event, the original change the
# family lived under (a later equal change usually confirms or undoes it, as an appeal
# does; ties to the later event handed every main value to the appeal, 2026-10-26)
CHANGE = {"severed": 3, "reduced": 2, "restored": 2, "preserved": 0}


def events(raw: list) -> list:
    """Event records in the family's chronology. A value outside its set is kept and
    named in _off_vocabulary rather than dropped (record, don't forbid); a plain-string
    event from an older run becomes a record with only `what`."""
    out = []
    for e in raw or []:
        if isinstance(e, str):
            e = {"what": e}
        rec = {k: e.get(k) for k in ("order", "bonds", "what", "made_by", "reported_by", "effect", "registered", "via", "words")}
        if isinstance(rec["bonds"], str):
            rec["bonds"] = [rec["bonds"]]
        for k in ("_registered_votes", "_via_votes"):
            if k in e:
                rec[k] = e[k]
        off = [k for k, allowed in EVENT_ENUMS.items() if rec.get(k) is not None and rec[k] not in allowed]
        if off:
            rec["_off_vocabulary"] = off
        out.append(rec)
    return sorted(out, key=lambda r: r["order"] if isinstance(r.get("order"), int) else 10**6)


BOND_STANDING = ("secure", "strained", "ruptured")


def bonds(raw: list) -> list:
    """Every bond the text shows: id, roles, standing (off-vocabulary standing kept and named)."""
    out = []
    for b in raw or []:
        if not isinstance(b, dict):
            continue
        rec = {k: b.get(k) for k in ("id", "between", "standing")}
        if rec["standing"] is not None and rec["standing"] not in BOND_STANDING:
            rec["_off_vocabulary"] = ["standing"]
        out.append(rec)
    return out


def main_event(evs: list):
    """The event that changed the bond most, by CHANGE; ties go to the earlier event.
    Events with an off-vocabulary effect are skipped. None when no event changed it."""
    best = None
    for e in evs:
        rank = CHANGE.get(e.get("effect"), -1)
        if rank <= 0:
            continue
        if best is None or rank > CHANGE[best["effect"]]:
            best = e
    return best


REGISTERED_PROMPT = """Below is a text and a numbered list of events in it that affected
bonds between people in it (the main bond: {between}).

For each event, say whether the reasoning the text records for its decisions takes what
that event did to the bond into account:
  weighed   — the reasoning names what the event did to the bond and gives it weight
  mentioned — the reasoning names it but gives it no weight
  absent    — the reasoning does not take it up

Judge only from the reasoning in the text, not from the event's importance.

Events:
{events}

Text:
{text}

Return ONLY valid JSON: {{"registered": {{"<event number>": "<weighed|mentioned|absent>", ...}}}}
"""
REGISTERED = ("weighed", "mentioned", "absent")


class ShortVotes(RuntimeError):
    """Fewer per-event draws came back than were asked for."""


def per_event_votes(prompt: str, operator: str, key: str, allowed: tuple, evs: list, votes=None) -> list:
    """Judge `key` for each event of the FIXED list, by majority over independent draws,
    so every event gets its own vote and spread.

    A value outside the set is not counted; an event with no majority keeps
    `key` None and its distribution in _<key>_votes (record, don't forbid).
    A failed draw is retried, up to n extra attempts; if fewer than n draws come
    back, ShortVotes is raised so no record is written with missing votes (a usage
    limit once saved five records whose events had 0 of 3 votes)."""
    n = _vote_count() if votes is None else max(1, votes)
    draws, model, last_err = [], None, None
    for _ in range(2 * n):
        if len(draws) == n:
            break
        try:
            r = call_and_validate(prompt, operator, capability="logos_operator", sensitive=True)
        except Exception as err:
            last_err = err
            continue
        model = r.get("_model", model)
        draws.append(r.get(key) or {})
    if len(draws) < n:
        raise ShortVotes(f"{operator}: {len(draws)} of {n} draws came back ({last_err})")
    for i, e in enumerate(evs, 1):
        dist = {}
        for d in draws:
            v = d.get(str(i), d.get(i))
            if v in allowed:
                dist[v] = dist.get(v, 0) + 1
        top = max(dist.items(), key=lambda kv: kv[1]) if dist else (None, 0)
        e[key] = top[0] if top[1] * 2 > len(draws) else None
        e[f"_{key}_votes"] = {"n": len(draws), "distribution": dist, "_model": model}
    return evs


def registered_votes(text: str, between: str, evs: list, votes=None) -> list:
    """Step 2: judge `registered` for each event of the fixed list (per_event_votes)."""
    if not evs:
        return evs
    listing = "\n".join(f"{i}. {e.get('what')} (made by {e.get('made_by')}; {e.get('effect')} "
                        f"bond {', '.join(e.get('bonds') or []) or '?'})"
                        for i, e in enumerate(evs, 1))
    prompt = REGISTERED_PROMPT.format(between=between or "the main bond", events=listing, text=text)
    return per_event_votes(prompt, "bond_registered", "registered", REGISTERED, evs, votes)


VIA_PROMPT = """Below is a numbered list of events that affected bonds between people
(parent and child, siblings, grandparent and grandchild, and the like).

For each event, say how it reached the bond, that is, what about the people's lives
together it changed:
  distance  — where people live: someone moves, or is moved, nearer or farther away
  schedule  — the time or contact people have with each other: custody time, visits,
              calls, supervision of contact, a bar on contact
  placement — whose household a child lives in: removal, a foster or kin placement,
              a return home
  status    — a legal standing in the relationship: rights granted, ended or confirmed,
              jurisdiction, an order made or vacated without changing time or place
  conduct   — something a person did or failed to do within the relationship: kept to
              or broke an order, used or skipped their time, an act or a report against
              another member
  other     — none of these

Judge only from the event as described.

Events:
{events}

Return ONLY valid JSON: {{"via": {{"<event number>": "<distance|schedule|placement|status|conduct|other>", ...}}}}
"""
VIA = EVENT_ENUMS["via"]


def via_votes(evs: list, votes=None) -> list:
    """Step 3: judge `via` for each event of the fixed list, from the event descriptions
    alone (no text), so a stored inference can take it without re-reading its case."""
    if not evs:
        return evs
    listing = "\n".join(f"{i}. {e.get('what')}" for i, e in enumerate(evs, 1))
    return per_event_votes(VIA_PROMPT.format(events=listing), "bond_via", "via", VIA, evs, votes)


def run(inference: dict) -> dict:
    """Attach logos.bond coordinates to an inference, in three steps: the bond and its
    events (voted on standing and hazard), then `registered` and `via` per event."""
    text = inference.get("raw_text", "")
    if not text:
        return inference

    result = call_and_vote(PROMPT.format(text=text), "bond",
                           capability="logos_operator", sensitive=True)
    if result.get("standing") != "unmarked":
        result["events"] = via_votes(registered_votes(text, result.get("between"),
                                                      events(result.get("events", []))))
    return parse(result, inference)


def add_via(inference: dict) -> dict:
    """Step 3 alone on an inference already tagged: `via` per stored event, the main
    via re-derived. Nothing else in logos.bond changes."""
    b = inference.get("logos", {}).get("bond")
    if not b or not b.get("events"):
        return inference
    b["events"] = events(via_votes(b["events"]))
    main = next((e for e in b["events"] if e.get("order") == b.get("main_event")), None)
    b["via"] = main.get("via") if main else None
    return inference


def parse(result: dict, inference: dict) -> dict:
    """Map a validated bond result into inference['logos']['bond'].

    Split out from run() so a fused pass or a replay can reuse the mapping with a
    pre-fetched sub-result, without re-calling the LLM (act_position pattern)."""
    evs = events(result.get("events", []))
    main = main_event(evs)
    if result["standing"] == "unmarked":
        effect, made_by, registered = "none", "none", "unmarked"
    elif main is None:
        effect, made_by, registered = ("preserved", "none", "unmarked") if evs else ("none", "none", "unmarked")
    else:
        effect, made_by, registered = main["effect"], main.get("made_by"), main.get("registered")
    via = main.get("via") if main else None
    logos = inference.setdefault("logos", {})
    logos["bond"] = {
        "bonds":        bonds(result.get("bonds", [])),
        "main_bond":    result.get("main_bond"),
        "between":      result.get("between"),
        "standing":     result["standing"],
        "registered":   registered,
        "effect":       effect,
        "made_by":      made_by,
        "via":          via,
        "main_event":   main.get("order") if main else None,
        "hazard":       result.get("hazard"),
        "bond_signals": result.get("bond_signals", []),
        "events":       evs,
        "rationale":    result.get("rationale"),
        "confidence":   result.get("confidence"),
        "_model":       result.get("_model"),
        "_votes":       result.get("_votes"),
        "_src":         ["residue test on the family field 2026-10-26"],
        "_operator":    "bond_operator.py"
    }
    return inference


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Tag an inference with the bond the events land on, and who made the outcome"
    )
    parser.add_argument("file", nargs="?", help="inference JSON file to tag")
    parser.add_argument("--dry-run", action="store_true", help="print result, do not write")
    parser.add_argument("--via-only", action="store_true",
                        help="step 3 only: add via to the stored events of an inference already tagged")
    args = parser.parse_args()

    path = Path(args.file) if args.file else None
    inference = read_json(path) if path else json.load(sys.stdin)

    tagged = add_via(inference) if args.via_only else run(inference)

    if args.dry_run or not path:
        print(json.dumps(tagged, indent=2))
    else:
        write_json(path, tagged)
        b = tagged["logos"]["bond"]
        print(f"logos.bond tagged: {b['standing']}/{b['registered']}/{b['effect']} by {b['made_by']} via {b.get('via')}/{b['hazard']}")

# llm: claude-opus-5-5 | 2026-10-26 | repos/vivify-operators/bond_operator.py | created — bond coordinate step 1 (standing|registered|effect|hazard + between, signals), purpose-blind prompt, one value per coordinate; shape deferred
# llm: claude-opus-5-5 | 2026-10-26 | repos/vivify-operators/bond_operator.py | effect = outcome from any actor's events (not the institution's act); made_by (institution|members|one_member|others) voted; events list with makers
# llm: claude-opus-5-5 | 2026-10-26 | repos/vivify-operators/bond_operator.py | events are structured records (order, what, made_by, reported_by, effect, words) in the family's chronology; effect/made_by = the event that changed the bond most, not the last act; requests are not events
# llm: claude-opus-5-5 | 2026-10-26 | repos/vivify-operators/bond_operator.py | registered asked per event; main effect/made_by/registered derived in code from the event that changed the bond most (main_event); only standing and hazard voted
# llm: claude-opus-5-5 | 2026-10-26 | repos/vivify-operators/bond_operator.py | ties go to the earlier event; registered moved to step 2: judged per event of the fixed list, majority per event (registered_votes)
# llm: claude-opus-5-5 | 2026-10-26 | repos/vivify-operators/bond_operator.py | every bond listed (bonds, main_bond) and events name the bonds they touch; made_by members = family members acting together, others = outside the family
# llm: claude-opus-5-5 | 2026-10-28 | repos/vivify-operators/bond_operator.py | step 3 via (distance|schedule|placement|status|conduct|other) per event from the event list; per_event_votes shared with registered; --via-only backfill
# llm: claude-opus-5-5 | 2026-10-30 | repos/vivify-operators/bond_operator.py | per_event_votes retries failed draws and raises ShortVotes instead of saving events with missing votes
