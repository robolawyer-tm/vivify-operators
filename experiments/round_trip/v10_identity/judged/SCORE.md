# Scripted judging — v10 — score
Key: K = sutton M = brown X = washington Z = cotton (v10_identity/KEY.txt, opened after 16 verdicts).

| Judge | Packet | Pick | Conf | Correct |
|---|---|---|---|---|
| gemini:gemini-3.8-flash | Sa | K | 92% | yes |
| gemini:gemini-3.8-flash | Sb | K | 95% | yes |
| gemini:gemini-3.8-flash | Wa | X | 95% | yes |
| gemini:gemini-3.8-flash | Wb | X | 95% | yes |
| gemini:gemini-3.8-flash | Ca | Z | 95% | yes |
| gemini:gemini-3.8-flash | Cb | Z | 95% | yes |
| gemini:gemini-3.8-flash | Na | K | 95% | no |
| gemini:gemini-3.8-flash | Nb | K | 95% | no |
| clef:clef@json | Sa | K | 79% | yes |
| clef:clef@json | Sb | K | 79% | yes |
| clef:clef@json | Wa | X | 54% | yes |
| clef:clef@json | Wb | X | 54% | yes |
| clef:clef@json | Ca | Z | 79% | yes |
| clef:clef@json | Cb | Z | 79% | yes |
| clef:clef@json | Na | K | 79% | no |
| clef:clef@json | Nb | K | 79% | no |

- gemini:gemini-3.8-flash: pattern **3/4 records**
- clef:clef@json: pattern **3/4 records**

## Interpretation (2026-10-27)

v10 passes the four-case rule: both calibrated judges identify 3 of 4 records, and their 16 picks agree exactly.

- Pass rule (set before v7): each deciding judge at least 3/4, with the judges agreeing; chance is 1/4 per record.
- Both judges identify Sutton (K), Washington (X) and Cotton (Z) in both orders; Gemini at 92–95%, Clef at 54–79%.
- Clef moved for the first time in four runs: Sutton now goes to Sutton's reading, not Cotton's.
- The one change was every account element, coded into the three account values, reaching the decoder (Sutton 5, Washington 4, Cotton 5, Brown 6).
- Gemini's reasons now count elements: K has "one outside witness sincerely wrong", matching Sutton's single victim; Z has four.
- Brown is still missed by both judges, who send his record to K, Sutton's reading (Gemini 95%, Clef 79%).
- Brown's own reading (M) read his steered-witness element (manufactured, outside party, shaped by the institution) as a coerced or fed confession.
- That is the concrete-picture instruction in the decoder prompt again, the same cause as in v7–v9.
- Clef's two orders are one input: the a and b packets give identical probabilities, so Clef contributes 4 independent verdicts, not 8.
- Caveats: one decode per case, one Gemini draw per packet, and four cases; the pass is a threshold reached, not a margin.
- Next candidate (not applied): fence the concrete-picture section of the decoder prompt, which should help Brown's reading most.

<!-- llm: claude-opus-5-5 | 2026-10-27 | repos/vivify-operators/experiments/round_trip/v10_identity/judged/SCORE.md | added interpretation: PASS 3/4 for both judges with identical picks; every account element was the change; Brown still read as a confession case -->
