# Scripted judging — v8 — score
Key: P = brown Q = cotton R = washington T = sutton (v8_identity/KEY.txt, opened after 16 verdicts).

| Judge | Packet | Pick | Conf | Correct |
|---|---|---|---|---|
| gemini:gemini-3.8-flash | Sa | T | 92% | yes |
| gemini:gemini-3.8-flash | Sb | Q | 95% | no |
| gemini:gemini-3.8-flash | Wa | R | 100% | yes |
| gemini:gemini-3.8-flash | Wb | R | 98% | yes |
| gemini:gemini-3.8-flash | Ca | Q | 100% | yes |
| gemini:gemini-3.8-flash | Cb | Q | 100% | yes |
| gemini:gemini-3.8-flash | Ba | T | 92% | no |
| gemini:gemini-3.8-flash | Bb | Q | 95% | no |
| clef:clef@json | Sa | Q | 95% | no |
| clef:clef@json | Sb | Q | 95% | no |
| clef:clef@json | Wa | R | 92% | yes |
| clef:clef@json | Wb | R | 92% | yes |
| clef:clef@json | Ca | Q | 97% | yes |
| clef:clef@json | Cb | Q | 97% | yes |
| clef:clef@json | Ba | Q | 96% | no |
| clef:clef@json | Bb | Q | 96% | no |

- gemini:gemini-3.8-flash: pattern **2/4 records, order moved a pick**
- clef:clef@json: pattern **2/4 records**

## Interpretation (2026-10-27)

v8 fails at 2/4 for both calibrated judges, but the failure has moved: the v7 lab leak is fixed and two different leaks remain.

- Washington (R) and Cotton (Q) are identified by both judges in both orders, as in v7.
- The definitions worked where they were aimed: no reading says laboratory or vendor, and Cotton's says witness and victim.
- Gemini now finds Sutton's own reading (T) in one order, citing "the body's own experts or officials" and the statistical figure; in the other order it picks Q.
- Gemini's Sutton-to-Q reasons are the shared conflict coordinates (entangled, rationalizing, exponential pressure), which Sutton, Washington and Cotton all share.
- Brown's own reading (P) is never picked: its coordinates (layer, scale and memory channel global, archival) made the decoder write an international, state-to-state dispute.
- That is the known Brown confound: his values were read fresh from a different source (the NRE record) and describe that source's telling, not the case.
- Brown then goes to T (Sutton's reading) or Q: Sutton and Brown share their account values, so T is the expected near-miss.
- Clef sends Sutton, Cotton and Brown all to Q, so it has not moved from v7's pattern.
- Gemini ran on the paid tier (credits added by John); all 8 verdicts arrived in minutes.
- Next candidates (not applied): read Brown from the same kind of source as the others, or test with three cases (drop Brown) to separate the Brown confound from the conflict-coordinate pull.

<!-- llm: claude-opus-5-5 | 2026-10-27 | repos/vivify-operators/experiments/round_trip/v8_identity/judged/SCORE.md | added interpretation: 2/4 for both judges; lab leak fixed, Brown's global/archival coordinates and the shared conflict values remain -->
