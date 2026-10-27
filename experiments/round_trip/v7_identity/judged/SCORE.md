# Scripted judging — v7 — score
Key: F = washington G = cotton H = sutton L = brown (v7_identity/KEY.txt, opened after 16 verdicts).

| Judge | Packet | Pick | Conf | Correct |
|---|---|---|---|---|
| gemini:gemini-3.8-flash | Sa | G | 95% | no |
| gemini:gemini-3.8-flash | Sb | G | 95% | no |
| gemini:gemini-3.8-flash | Wa | F | 94% | yes |
| gemini:gemini-3.8-flash | Wb | F | 95% | yes |
| gemini:gemini-3.8-flash | Ca | G | 90% | yes |
| gemini:gemini-3.8-flash | Cb | G | 90% | yes |
| gemini:gemini-3.8-flash | Ba | G | 95% | no |
| gemini:gemini-3.8-flash | Bb | G | 92% | no |
| clef:clef@json | Sa | G | 92% | no |
| clef:clef@json | Sb | G | 92% | no |
| clef:clef@json | Wa | F | 91% | yes |
| clef:clef@json | Wb | F | 91% | yes |
| clef:clef@json | Ca | G | 73% | yes |
| clef:clef@json | Cb | G | 73% | yes |
| clef:clef@json | Ba | G | 78% | no |
| clef:clef@json | Bb | G | 78% | no |

- gemini:gemini-3.8-flash: pattern **2/4 records**
- clef:clef@json: pattern **2/4 records**

## Interpretation (2026-10-27)

v7 fails: both calibrated judges identify 2 of 4 records (pass = 3 of 4), and they fail identically.

- Washington (F) and Cotton (G) are identified by both judges in both orders, at 73–95% confidence.
- The Sutton and Brown records both go to G, Cotton's reading, in all 8 verdicts from the two judges.
- Panel (informational): gpt-oss and qwen also send Sutton to G; Brown packets exceed Groq's size limit (413); two Ca replies carry no PICK line.
- Every judge's reason is the same: G says the account came from "a contractor, a technical vendor, a laboratory", and Sutton's and Brown's records turn on crime-lab evidence.
- The coding is right: Cotton's `supplied_by` is `outside_party`, which account_production defines as "a witness, a victim, an informant, a member of the public".
- The decoder is wrong: it received the value without its definition and glossed `outside_party` as a contractor or lab.
- So the failure is a decoding leak, the same class as v4's telling leak: the reading invents a concrete picture the coordinate does not hold.
- H (Sutton) and L (Brown) both say the institution supplied its own figures; the judges read them as administrative self-certification, not forensic work.
- Candidate fix (not applied): pass each enum value's definition to the decoder with its value, then regenerate the four readings and re-judge as v8.
- Caveats carried from the design: Brown is model- and source-confounded; Sutton and Brown share their account values, so they may stay hard to separate even after the fix.

<!-- llm: claude-opus-5-5 | 2026-10-27 | repos/vivify-operators/experiments/round_trip/v7_identity/judged/SCORE.md | added interpretation: 2/4 fail for both calibrated judges, outside_party glossed as a lab by the decoder -->
