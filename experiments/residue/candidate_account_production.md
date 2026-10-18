# candidate: account_production — how the account the institution acts on was made

A new coordinate, `account_production`, would record how the account the institution acts on was made, using values taken from the eleven residue items that asked for it.

## Where the demand came from

- The residue test (report.md, 201d7d8) found this loss in all four cases. It is the most frequent group that matches none of C-01..C-10.
- The items are sutton-03/05, washington-03/05/07, cotton-04/05/09 and brown-02/03/15. Each record quote is in `<case>_residue.json`.
- The current coordinates do mark that a false account exists: `resonance: illusion`, and `cooperative` with a quality maxim. They do not say how it was made, so the blind reading guessed "bureaucratic framing" (cotton-04) or left it out.
- This is the act_position route: an observed loss forces an axis, and its values come from the items, not from a theory list.

## First coordinate: mode — what made the account

- `mistaken`: a sincere source gets it wrong. Sutton's show-up despite a 6-inch, 60-pound mismatch; Cotton's "between number four and number five"; Brown's "80 percent".
- `inflated`: a real but weak element is stated as stronger than it is. Sutton's DNA statistic; Brown's claim that prints cannot survive Windex; Cotton's insole and flashlight stacked into corroboration.
- `manufactured`: the institution's own agents build or alter the account. Washington's fourth rehearsed confession, the three trips to the scene, and the amended report "without additional testing"; Brown's database "loaded but never searched, although his report said they had been".
- `unmarked`: the text shows nothing about how the account was made. This value is needed so that non-exoneration texts are not forced into one of the three above.
- The three values are an ordering of institutional agency: none, then amplifying, then authoring. That is a social-structural distinction, not a legal one; a rumour, a citation cascade or a smear campaign sorts the same way.

## Second coordinate: hardening — how it gained certainty

- `repetition`: each pass through procedure fixes the account further. Cotton went from photo array to lineup to courtroom; Brown's pick came on a second viewing; Washington's was the fourth take.
- `endorsement`: an expert or official form lends the account certainty it lacks. Sutton's statistic, Brown's examiner and his report.
- `none`: the account stands as first given.
- This coordinate carries what C-05 (timing) only partly touched: the same false account grows stronger with each step, with no new evidence.

## Signals, as counter_force does

- One entry per element, in the form `<element> (from <whom>, shaped by <whom>): <words from the text>`.
- "From whom" and "shaped by whom" keep the producer apart from the source. In Washington the words came from the accused, but the police shaped them; that split is what `manufactured` means.
- The cases mix modes: Brown has all three. The coordinate takes the value the institution's case rests on most, and the signals keep the rest. The alternative, a set-valued coordinate, would break per-coordinate voting.

## Reading in a replay (streaming)

- The value is "how the account was made, as far as the text shows so far". It never asserts that the account is false, because an early step cannot know that.
- So the value can move from `mistaken` to `manufactured` once the record exposes the alteration (Brown's database search). That movement is itself an early signal, like contesting before the turn.
- Hindsight guard: the same as every replay operator. Steps 1..N only, and no search (feedback_no_search_workers).

## Placement

- Recommended: its own operator file, `account_production_operator.py`, built like act_position (call_and_vote, parse(), `_src` naming the residue test).
- Why not inside conflict_operator: changing conflict's prompt again would mix with the schema shift still being watched at Sutton steps 8-10. A separate operator changes one thing.
- Cost: one lean call per vote per inference, about the size of an act_position call.

## How it would be judged

- Acceptance is the residue test itself. Add the coordinate to the encoding, re-run residue.py, and the eleven items should drop out of the residue or be recovered in the blind reading, while the other groups stay.
- Reliability: 3-vote unanimity on the four cases plus Brown replay steps 1-15, the same bar as counter_force.
- Negative control: every field case is an exoneration, so `unmarked` would hardly ever be seen. One or two texts with no false account (a session text from claude_code_sessions) must come out `unmarked`, or the coordinate is just restating the field.
- Watch: `inflated` vs `mistaken` is the boundary most likely to split votes (Brown's "80 percent" is a sincere witness made stronger by procedure). If the split persists, record it as data rather than adding a prompt rule (feedback_record_dont_forbid).

## Decisions (John, 2026-10-17)

- One value: `mode` records the element the institution's case rests on most, and the signals keep the rest. If mixed modes recur across cases, the signals will show it, and a set-valued coordinate can come later.
- `mode` ships first, alone. `hardening` follows as its own step, so each change is measured by itself, as counter_force was.
- "The error shielding itself from review" (sutton-08, washington-10, brown-08) goes with the reopening route, as the obstacle a reopening must get past, not here.
- Built: `account_production_operator.py`, its vocabulary in `config/coordinates.json`, and `tests/test_account_production.py`. The first run is `account_production_run.py`.

<!-- llm: claude-opus-5-5 | 2026-10-17 | repos/vivify-operators/experiments/residue/candidate_account_production.md | created — sketch of the first demand-led dimension candidate: mode (mistaken/inflated/manufactured/unmarked), hardening (repetition/endorsement/none), signals, replay reading, placement, acceptance via re-run residue test -->
<!-- llm: claude-opus-5-5 | 2026-10-17 | repos/vivify-operators/experiments/residue/candidate_account_production.md | open questions replaced by John's three decisions (one dominant value, mode first, shielding goes with reopening); built files listed -->
