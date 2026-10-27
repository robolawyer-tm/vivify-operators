# Family field design — mapping what the record cannot show

The family field maps what records cannot show but measured dimensions lead us to expect: bonds, the events on them, and whose account reports each.

- Premise (John, 2026-10-26): the narrative a record presents is pollution, and this field will vary widely from the theoretical baseline.
- The legal schema is not the frame; a court is one actor in the family's environment, beside the people themselves.
- Target layout, defined before more process code: `~/private_field/family/cases/<case>/` holds one case, outside the repo for licence and store isolation.
- Inside a case: `docs/NN_<kind>_<date>.txt`, one per decision, report or review, numbered in the family's chronology.
- Inside a case: `inferences/` with one inference per document, and `case.json` linking them with order and kind.
- An event is a record, not a sentence: order, what, made_by, reported_by, effect on the bond, and a quote.
- `made_by` (institution, members, one_member, others) keeps families' own arrangements visible beside institutional orders.
- `reported_by` (institution, member, others, unclear) separates an event from the account that reports it.
- Requests, proposals and arguments are not events until acted on; they are claims within an account.
- The same event reported by several accounts stays several records, so their disagreement remains measurable.
- Joint read: the parents' accounts are also read together, since some relational structure appears only in the pair.
- Replay reads a case document by document, so the bond's state moves with each event, not only at the end.
- Baselines: `baselines/<theory>.md` states what one theory expects for a bond under each kind of event.
- Each baseline is written in plain words from the theory's own sources, and reviewed by John before use.
- Theories first written up: attachment (Bowlby), co-regulation (Sbarra and Hazan), family systems and cutoff (Bowen), ambiguous loss (Boss).
- A baseline is a reference to measure against, never a label imposed on the coding.
- Variance is the gap between a baseline's expectation and the coded case; it is the signal, read as tension.
- Variance measures wait for enough cases per kind; on four cases any measure would be a guess.
- `registered` measures the court's blind spot directly: bonds present in the field, absent from the court's account.
- The important material is often what no account states; the dimensions let it be expected, located and then sought.
- Every coding prompt stays blind to the purpose: no harm, no thesis, no reform language.
- People appear by role only; the court's anonymisation is never undone, and pseudonyms are never linked to people.
- Now: structured events in bond_operator.py, then the acceptance rerun of the residue test with bond added.
- Next: the case layout for one multi-document family, and the first baseline (attachment) for review.
- Not yet: variance measures, shape (hub, mesh, dyad), the `entanglement` naming (parked), and John's own case.

<!-- llm: claude-opus-5-5 | 2026-10-26 | repos/vivify-operators/FAMILY_FIELD_DESIGN.md | created — design for the family field: case layout, structured events with maker and reporting account, joint read, replay, theory baselines and variance, phasing -->
