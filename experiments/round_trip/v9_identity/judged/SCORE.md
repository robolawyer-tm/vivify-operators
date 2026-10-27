# Scripted judging — v9 — score
Key: D = cotton E = sutton U = washington V = brown (v9_identity/KEY.txt, opened after 16 verdicts).

| Judge | Packet | Pick | Conf | Correct |
|---|---|---|---|---|
| gemini:gemini-3.8-flash | Sa | E | 95% | yes |
| gemini:gemini-3.8-flash | Sb | E | 92% | yes |
| gemini:gemini-3.8-flash | Wa | U | 98% | yes |
| gemini:gemini-3.8-flash | Wb | U | 98% | yes |
| gemini:gemini-3.8-flash | Ca | D | 100% | yes |
| gemini:gemini-3.8-flash | Cb | D | 100% | yes |
| gemini:gemini-3.8-flash | Na | E | 92% | no |
| gemini:gemini-3.8-flash | Nb | E | 85% | no |
| clef:clef@json | Sa | D | 95% | no |
| clef:clef@json | Sb | D | 95% | no |
| clef:clef@json | Wa | U | 94% | yes |
| clef:clef@json | Wb | U | 94% | yes |
| clef:clef@json | Ca | D | 97% | yes |
| clef:clef@json | Cb | D | 97% | yes |
| clef:clef@json | Na | D | 90% | no |
| clef:clef@json | Nb | D | 90% | no |

- gemini:gemini-3.8-flash: pattern **3/4 records**
- clef:clef@json: pattern **2/4 records**

## Interpretation (2026-10-27)

v9 fails the two-judge rule, but Gemini, the deciding judge, reaches the pass mark (3/4) for the first time in the four-case test.

- Gemini identifies Sutton (E), Washington (U) and Cotton (D) in both orders, at 92–100%.
- The one change worked: Brown's selected telling moved layer, scale and memory channel from global to institution, and no reading decodes as an international dispute.
- Brown's record still misses: Gemini sends it to E, Sutton's reading, in both orders (85–92%).
- Brown's account was re-coded from inflated to manufactured, supplied and shaped by the institution, after the selection kept the false report of a SAFIS search.
- His reading V turned that into a custodial setting with falsified records about the institution's own conduct (cell checks), which no judge matched to a fingerprint case.
- So the decoder again filled a value with an invented concrete picture, now for `manufactured` with an institutional shaper.
- Gemini's reasons for E (an official expert's weak figure stated as certain) also describe the print examiner, so E is a defensible near-miss: Sutton and Brown are both expert-evidence cases.
- Clef stays at 2/4: it sends Sutton, Cotton and Brown all to D (Cotton's reading), its v7 and v8 pattern unchanged.
- Clef has not moved in three runs while Gemini has; Clef may be reading something other than the account values, which needs its own check.
- Root cause across v7–v9: the decoder prompt (v2/decoder_prompt_v2.txt) asks for a committed concrete picture, so every reading guesses a setting the coordinates do not hold.
- Next candidates (not applied): drop or fence the concrete-picture section of the decoder prompt, or check whether `manufactured` or `inflated` is the right coding for Brown.s main element.

<!-- llm: claude-opus-5-5 | 2026-10-27 | repos/vivify-operators/experiments/round_trip/v9_identity/judged/SCORE.md | added interpretation: Gemini 3/4 (first pass mark), Clef 2/4; Brown's reading decoded as a custodial records case; Clef unchanged across v7-v9 -->
