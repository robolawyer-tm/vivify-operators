# candidate: bond — the standing bonds an institution's act lands on

A new coordinate, `bond`, would record the parent–child and family bonds a text describes, whether the account the institution acts on weighs them, and what its act does to them.

## Where this comes from, and why that matters

- This is a SUPPLY-PUSH candidate: it comes from theory and from the project's purpose, not yet from a residue loss. account_production and act_position came the other way, from observed losses, and arrived pre-assured.
- Purpose (John, 2026-10-26): evidence for parliamentary reform of Canadian family and divorce law, that the separation of parent and child is a harm courts do not see, and that these bonds should be the key concern.
- Theory: Bowlby (separation distress), continuing bonds (Klass, Silverman & Nickman), Bowen (the family as one emotional unit; emotional cutoff), Boss (ambiguous loss), Doka (disenfranchised grief), and Sbarra & Hazan (co-regulation, so separation brings dysregulation).
- The bond, not the grief, is the unit; harm is one outcome of what happens to the bond (~/new_material/13_hypothetical_quantum_analog_dyads.md).
- Converting move, before anything is built: run the residue test on the first family texts with the CURRENT coordinates. If the blind readings lose the bonds, that loss is the demand, and the candidate stops being supply-push.
- Name: `bond`, not `entangled`, which is already a conflict-schema value with another meaning (`conflict_operator.py:134`).

## The prompt stays blind to the purpose

- The operator prompt describes bonds and what happens to them. It never mentions harm, self-harm, reform, or the claim that separation is damaging.
- If the pattern appears, it then appears from coding that did not look for it. A committee, or a critic, can be shown the prompt.

## First coordinate: standing — the bond before the act

- `secure`: an established bond with ongoing care or contact, as the text shows it.
- `strained`: the bond is present but interrupted or in conflict.
- `ruptured`: the bond was already broken before the institution acted.
- `unmarked`: the text shows no bond. Needed so that texts without families are not forced into one of the three.
- One value: the bond the act lands on most, as with account_production's mode. The signals keep the other bonds.

## Second coordinate: registered — does the institution's account see it

- `weighed`: the bond is named in the account the institution relies on, and given weight in its reasoning.
- `mentioned`: named, but no weight is given to it in the reasoning.
- `absent`: the bond appears in the text but not in the institution's account.
- `unmarked`: no bond in the text.
- This is where "courts do not see it" becomes a measurement. Compared with an after-harm review of the same family, the court record's value can be read against the review's.
- Placed as account_production's positions are: the account the institution relied on, not the text as a whole.

## Third coordinate: effect — the outcome for the bond, and who made it

- `effect`: `preserved`, `reduced`, `severed`, `restored`, or `none` — the outcome for the bond as the text leaves it, whoever made it.
- `made_by`: `institution`, `members` (the people in the bond, together), `one_member`, `others` (other family or outside people), or `none`.
- `events`: each event in the text with its maker and what it did to the bond.
- Why not the institution's act (John, 2026-10-26): "the legal schema isn't the baseline - courts think they are but in better cases the participants find their better selves and create solutions that override judgements - so I think that the mapping is events and outcomes environmentally structured." Making the court's act the frame would be an imposed taxonomy.
- The field had already shown it: ss_v_kf-03 (a long informal arrangement before any court) and ss_v_kf-09 (the two parents aligned against the court's own order) were lost by the blind readings.
- `registered` stays about the institution's account: that is the blind spot under study.
- Sentencing, a custody order, a protection order, a removal, and a family's own agreement all sort the same way; this is social structure, not family law.

## Fourth coordinate: hazard — is the bond itself a danger

- `none`, `alleged`, or `established`, as the text records it.
- This keeps both directions coded. The 2021 Divorce Act puts the child's safety first because some contact is the danger (the Ontario DVDRC child-homicide road map is about those cases).
- Evidence that codes these cases too, and still shows a pattern of unseen bond loss, survives a hearing. Evidence that leaves them out will be set aside.

## Fifth coordinate, second step: shape — how the bonds are distributed

- `hub`: the family's bonds run through one member.
- `mesh`: bonds run between every pair.
- `dyad`: two people only.
- `unmarked`.
- From the W/GHZ section of document 13: how bonds are distributed decides what survives losing one member. Honest limit: ordinary network theory predicts the same, so the quantum frame supplies the idea, not the proof.
- Ships after the first four, by itself, so each change is measured alone (as hardening followed mode).

## Signals, as account_production does

- One entry per bond: `<bond> (between <whom>): <words from the text>`.
- Roles only (mother, father, child aged 9, grandmother), never names. The court's anonymisation is never undone.
- Several bonds per case are normal. The coordinate takes the one the act lands on most; the signals keep the rest.

## Reading in a replay (streaming)

- The values are "as far as the text shows so far". `registered` can move from `absent` to `weighed` when an appeal court takes up what the trial court left out; that movement is the reversal, the same shape as an exoneration.
- Hindsight guard as for every replay operator: steps 1..N only, no search (feedback_no_search_workers).

## Placement

- Its own operator file, `bond_operator.py`, built like account_production_operator.py (call_and_vote, parse(), `_src` naming this candidate). Vocabulary in `config/coordinates.json`, tests in `tests/test_bond.py`.
- Family texts go in their own store, `~/private_field/family/` (outside the repo: CanLII terms bar redistribution, and the repo store's shared vocabulary and cross-scale weights read everything under `inferences/`). The repo store is tagged `pre-family-2026-10-26`.
- Cost: one lean call per vote per inference, about an account_production call.

## How it would be judged

- Demand first: the residue test on 3–5 family texts with the current coordinates. Bond losses must appear in the blind readings, or the candidate waits.
- Then acceptance, as account_production's was: a fixed checklist of the bond items found, scored over three judge draws, coordinates with `bond` against without.
- Then the case-identity test (round_trip, as v5 arm B): two family cases whose other coordinates match, told apart by the bond values or not.
- Reliability: 3-vote unanimity on every case, the same bar as counter_force.
- Negative control: a text with no family (a claude_code_sessions text) must come out `unmarked` throughout.
- Cross-field check: the exoneration cases also separate families for decades (Brown, Washington). `bond` should code them too, and would show whether their courts weighed the families any more than family courts do.
- Watch: `mentioned` vs `weighed` is the boundary most likely to split votes. If it persists, record it as data rather than adding a prompt rule (feedback_record_dont_forbid).

## What a finding would look like, later

- Across many decisions: how often `registered` is `absent` or `mentioned` while `effect` is `reduced` or `severed`, with `hazard` held at `none`.
- Against after-harm reviews (Alberta OCYA, Ontario DVDRC, coroners' inquests): whether the bond the review names was registered in the court's account.
- Post-2021 Divorce Act decisions specifically, since the Act now ranks the child's emotional and psychological well-being first.
- This is a pattern claim and needs dozens of cases per kind; the first texts only test whether the coordinate works.

## Decisions (John, 2026-10-26)

- Step 1 ships standing, registered, effect and hazard together; shape follows as step 2, by itself.
- One value per coordinate: the bond the act lands on most; the signals keep the rest.
- The demand check runs first: the residue test on the first family texts with the current coordinates, before anything is built.

## Demand check (2026-10-26): passed

- Residue on four Pennsylvania Superior Court opinions (custody modification, relocation, termination, school choice), current coordinates: 59 structural items.
- Every case's first loss was the family itself: a ruling on one family read as policy for a population (in_re_ejc-15: "harm to particular children, not mild bureaucratic discomfort across a population").
- Blind topic sort (topic_sort.py, six topics, two shuffles): 12 of 59 items primarily about relationships between family members, the same 12 in both draws, in all four cases.

## Build notes (2026-10-26)

- effect is not asked of the model: it came back as the last procedural act (an appeal's remand) every time. It is derived in code from the event that changed the bond most; ties go to the earlier event (ties to the later one handed every main value to the appeal).
- registered is judged in a second step, per event of a fixed list, by its own majority: asked inside the event list it agreed on the main event in 3 of 5 draws. Two-step, 5 votes: 30 of 30 events reached a majority, 23 unanimous.
- Every bond is listed (bonds, main_bond), and each event names the bonds it touched.
- made_by `members` = family members acting together, two parents' own arrangement included.
- Control (a session text with no family): unmarked throughout, unanimous, in every run.

## Acceptance (2026-10-27): fixed checklist, 12 family-relationship items

- Arms told the same setting ("family court case"); bond adds coordinates and each event's structure, never event wording or quotes. Two blind decodes per arm; three judge draws, arms shuffled and hidden (bond_checklist.py).

| Arm | Draw 1 | Draw 2 | Draw 3 | Mean |
|---|---|---|---|---|
| baseline, decode 1 | 1 | 1 | 1 | 1.0 |
| baseline, decode 2 | 1 | 1 | 1 | 1.0 |
| bond v1 (main bond only) | 3.5 | 3 | 3.5 | 3.33 |
| bond v2 (every bond), decode 1 | 6 | 6 | 5.5 | 5.83 |
| bond v2 (every bond), decode 2 | 6 | 6.5 | 5 | 5.83 |

- bond v2 recovers about half the items (5.83 of 12) against 1 for the baseline, in every draw and both decodes; the two decodes give the same mean. account_production was accepted at 4.17 of 11 against 0.5.
- What the fixes bought: in_re_ejc-03 (siblings removed and separated) no → yes in all six marks; ss_v_kf-03 (the parents' informal arrangement before any court) no → yes in 4 of 6; in_re_ejc-10 (the two children's different outcomes) no → partly in 4 of 6.
- Still missed: cm_v_mm-08 (one parent acting as monitor of the other's contact) and, mostly, ecs_v_mcs-08 (the family's back-and-forth moves): a role and a geography no coordinate carries.
- Limits: four cases from one court; the checklist items come from these same cases, and the two fixes were made after seeing the first run's misses (as Clef's labelled state was), so the next unseen family cases are the real exam. The coder, decoder and judge are one model family.
- Recommendation: accept as a coordinate, on the same terms account_production was accepted; confirm on new cases before relying on registered's per-event pattern.

<!-- llm: claude-opus-5-5 | 2026-10-26 | repos/vivify-operators/experiments/residue/candidate_bond.md | created — supply-push candidate `bond` (standing, registered, effect, hazard; shape second), purpose-blind prompt, demand check first, acceptance as account_production -->
<!-- llm: claude-opus-5-5 | 2026-10-26 | repos/vivify-operators/experiments/residue/candidate_bond.md | John's three decisions recorded; family store placed in ~/private_field/family -->
<!-- llm: claude-opus-5-5 | 2026-10-26 | repos/vivify-operators/experiments/residue/candidate_bond.md | effect = outcome from any actor's events, made_by and events added (the legal schema is not the baseline) -->
<!-- llm: claude-opus-5-5 | 2026-10-27 | repos/vivify-operators/experiments/residue/candidate_bond.md | demand check, build notes, acceptance result (v2 5.83/12 vs baseline 1.0, two decodes, three draws), recommendation -->

**Decision (2026-10-27):** ACCEPTED by John.
