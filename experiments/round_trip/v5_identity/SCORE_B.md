# Case-identity rerun, arm B — score — 2026-10-22
Key: J = sutton, K = washington (KEY_B.txt, opened after all four arm B verdicts; KEY_A.txt still closed).
Arm B input = the current store's coordinates (social_field now scores the events) plus account_the_institution_relied_on: Sutton inflated / institution / nobody; Washington manufactured / the_target / institution.

| Judge | Packet | Pick | Conf | Correct |
|---|---|---|---|---|
| Gemini (AI Studio) | Washington record, J first | K (Washington's) | 98% | yes |
| ChatGPT | Washington record, J first | K (Washington's) | 99% | yes |
| Gemini (AI Studio, new chat) | Sutton record, K first | J (Sutton's) | 96% | yes |
| ChatGPT (Temporary Chat) | Sutton record, J first | J (Sutton's) | 99% | yes |

- **PASS, 4/4. Both models switched their pick with the record,** which v4 never did: there every judge picked the same reading for both records.
- Every reason is about the mechanism. Washington: a confession the target supplied under conditions the institution created, against the rehearsed fourth confession and his deference to authority. Sutton: an inflated institutional account that nobody outside tested, against the 1-in-694,000 statistic, Sample #1, the missing defence expert, and KHOU and Thompson's exposure. Each judge also rejected the other reading because it names a mechanism the record lacks: "Sutton never confessed"; Horizon-style dispersed operators do not fit "one wrongly convicted man".
- Facts: every cited fact is in the packet records; one loose phrase (ChatGPT SJ) and one mild gloss (Gemini SK), neither load-bearing.
- Order: Washington was judged J-first twice (the K-first packet was not run); Sutton was judged in both orders.
- What this shows: with the account coordinates, two wrongful convictions with IDENTICAL conflict coordinates are told apart by every judge. What it does not yet show: how much of this comes from the social_field fix. Arm A (the fix alone) is built but not judged.
- Limits: two cases, one decode per case, two judge model makers; the account values come from the residue run (account_production_run.json), not from the store.
- Decoder: claude-opus-5-5 (lean worker); readings built by `build_identity_v5.py`.

<!-- llm: claude-opus-5-5 | 2026-10-22 | repos/vivify-operators/experiments/round_trip/v5_identity/SCORE_B.md | scored arm B of the case-identity rerun against KEY_B: 4/4, both judges switch with the record -->
