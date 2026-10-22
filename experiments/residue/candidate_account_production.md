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

## Acceptance test (2026-10-17): failed twice

- Setup: fresh residue re-runs of all four cases. The baseline arm uses the coordinates as before, and the other arms add the mode. One blind judge marked every loss from all arms, pooled and shuffled, as about how the account was made or not (`ap_acceptance.py`, `rerun/`).
- Losses about how the account was made: baseline 15/53; bare label `account_production.mode` 16/52; named label `account_the_institution_relied_on.how_it_was_made` 19/50. The judge gave the baseline 15 both times.
- Try 1, bare label: the reader applied the mode to the text itself. Washington's "manufactured" plus cooperative=honored became "a polished explainer, true line by line".
- Try 2, named label: the reader now places it right ("the falseness sits upstream: the account the institution relied on was inflated"), but the losses do not fall.
- What the remaining losses ask for is WHO produced the account and through what channel, not its kind. Examples: cotton-01, "a single private witness whose uncertain memory hardened through repeated procedures, not an institution's document"; washington-02, "police produced a confession in custody, not an institution assembling its own record"; cotton-11, "a traumatized victim rather than a bureaucrat".
- Without that, the reader fills the kind into a bureaucracy (registries, metrics, curated data). This is the July finding again: coordinates carry dynamics, not the actors' places.
- Reading: the mode word is necessary but not sufficient. The positions in the signals, who supplied the account and who shaped it, are the part the field is asking for.

## Try 3 (2026-10-17): positions added, structure carried, count flat

- Added `supplied_by` (outside_party | the_target | institution) and `shaped_by` (nobody | institution) for the main element. Tagging was 3/3 everywhere: Sutton institution/nobody, Washington the_target/institution, Cotton outside_party/nobody, Brown institution/institution, and the controls none/none.
- Losses about how the account was made: baseline 15/53, positions 15/48. The count is flat.
- The readings now carry the structure. Washington: "rests on a document the target signed. The authority drafted that document, and the target signed it under pressure". Cotton: "the falsehood came from someone else's honest mistake".
- The remaining losses are about domain. Cotton-01: "a criminal conviction from a mistaken human memory, not an administrative finding from a faulty data feed". Sutton-03: "forensic match statistics, not optimism about the institution's own performance".
- So the residue count cannot tell structure from domain: once the structure is recovered, the reader places it in tax, benefits or a regulator, and the loss is written as "not X but Y".
- Fair test, not yet run: give BOTH arms the domain (for example "criminal case"), as the keywords would in the real instrument (July finding: coordinates carry dynamics, keywords carry domain).

## Try 4 (2026-10-18): setting held, residue count still fails

- Both arms were told "criminal case". Losses about how the account was made: baseline_domain 18/58, positions_domain 23/55. The judge drifted by about ±3: it gave the baseline 18 here, after 15 three times.
- The single dominant value misleads where it leaves things out. Sutton's shaped_by=nobody became "every official, including the prosecutor, acted sincerely". Cotton's became "certainty settled from the start".

## Fixed checklist (2026-10-18): the first measure that moves

- `ap_checklist.py` scores every arm's existing blind reading against the eleven original items: yes = 1, partly = 0.5. The arms are shuffled and labelled per case, and there is one judge call per case.
- Totals out of 11: baseline 0; bare label 0.5; named 2; positions 1.5; baseline_domain 1; **positions_domain 4.5 (2 yes, 5 partly)**.
- Fair pair (setting held): 1 vs 4.5. The yes items were washington-03 (the rehearsed confession) and cotton-04 (the honest but hesitant witness).
- Still missed with everything added: sutton-03 (show-up despite mismatch), washington-07 (report rewritten), cotton-09 (weak evidence stacked), brown-02 (the hesitant picks). These are the secondary elements the one dominant value drops.
- Limits: one judge draw per case, the same model family throughout, and readings from a single decode per arm.
- Cost (usage log, tag ap_checklist): 4 calls, 42K tokens written to the cache, 2.5K out, 1.9K thinking, 37 s, list $0.39.

## Checklist repeat draws (2026-10-22): the gap holds

- Two more judge draws with new shuffles (`ap_checklist.py --seed 2` and `--seed 3`), over the same readings.
- Totals out of 11, draws 10-18 / s2 / s3, then the mean: baseline 0/0/0 (0); bare label 0.5/0/0 (0.17); named 2/1.5/1 (1.5); positions 1.5/0.5/1 (1.0); baseline_domain 1/0/0.5 (0.5); **positions_domain 4.5/4/4 (4.17)**.
- The fair pair is 0.5 vs 4.17. positions_domain is top in every draw, and the lowest positions_domain draw (4) is above the highest score of any other arm in any draw (2).
- The per-item marks barely move: washington-03 is yes in all three draws; sutton-05, washington-05, brown-03 and brown-15 are partly in all three; only cotton-04 moves (yes, then partly twice).
- The same four items are missed every time: sutton-03, washington-07, cotton-09, brown-02. These are the secondary elements.
- So the judge is stable, and the effect is not shuffle noise. Recall is still low: about 4 of 11, mostly partly.
- What this does not test: the readings come from one decode per arm, and the judge is the same model family as the writer. A second decode, or a non-Anthropic judge, is what would test those.
- Cost (usage log, tags ap_checklist_s2 and ap_checklist_s3): 8 calls, list $0.76.

<!-- llm: claude-opus-5-5 | 2026-10-17 | repos/vivify-operators/experiments/residue/candidate_account_production.md | created — sketch of the first demand-led dimension candidate: mode (mistaken/inflated/manufactured/unmarked), hardening (repetition/endorsement/none), signals, replay reading, placement, acceptance via re-run residue test -->
<!-- llm: claude-opus-5-5 | 2026-10-17 | repos/vivify-operators/experiments/residue/candidate_account_production.md | open questions replaced by John's three decisions (one dominant value, mode first, shielding goes with reopening); built files listed -->
<!-- llm: claude-opus-5-5 | 2026-10-17 | repos/vivify-operators/experiments/residue/candidate_account_production.md | acceptance section: failed with bare and named labels; remaining losses ask who supplied and shaped the account -->
<!-- llm: claude-opus-5-5 | 2026-10-17 | repos/vivify-operators/experiments/residue/candidate_account_production.md | try 3: positions carried in the reading, count flat, remaining losses are domain; domain-held test proposed -->
<!-- llm: claude-opus-5-5 | 2026-10-18 | repos/vivify-operators/experiments/residue/candidate_account_production.md | try 4 and fixed-checklist result: positions plus setting 4.5/11 vs 1/11 -->
<!-- llm: claude-opus-5-5 | 2026-10-22 | repos/vivify-operators/experiments/residue/candidate_account_production.md | checklist repeat draws s2/s3: positions_domain 4/4 (mean 4.17) vs baseline_domain 0/0.5 (mean 0.5); judge stable, same 4 items always missed -->
