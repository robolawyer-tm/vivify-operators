# Scripted judging — v11 — score
Key: B = cotton G = sutton J = washington Y = brown (v11_identity/KEY.txt, opened after 16 verdicts).

| Judge | Packet | Pick | Conf | Correct |
|---|---|---|---|---|
| gemini:gemini-3.8-flash | Sa | G | 95% | yes |
| gemini:gemini-3.8-flash | Sb | G | 95% | yes |
| gemini:gemini-3.8-flash | Wa | J | 98% | yes |
| gemini:gemini-3.8-flash | Wb | J | 95% | yes |
| gemini:gemini-3.8-flash | Ca | Y | 92% | no |
| gemini:gemini-3.8-flash | Cb | Y | 92% | no |
| gemini:gemini-3.8-flash | Na | Y | 95% | yes |
| gemini:gemini-3.8-flash | Nb | Y | 95% | yes |
| clef:clef@json | Sa | B | 94% | no |
| clef:clef@json | Sb | B | 94% | no |
| clef:clef@json | Wa | B | 51% | no |
| clef:clef@json | Wb | B | 51% | no |
| clef:clef@json | Ca | B | 93% | yes |
| clef:clef@json | Cb | B | 93% | yes |
| clef:clef@json | Na | B | 87% | no |
| clef:clef@json | Nb | B | 87% | no |

- gemini:gemini-3.8-flash: pattern **3/4 records**
- clef:clef@json: pattern **1/4 records**

## Interpretation (2026-10-27)

v11 fails the rule: Gemini stays at 3/4 but on a different three, and Clef falls to 1/4.

- The fence worked on the readings: none names a confession, laboratory, jail or country.
- Gemini finds Brown's own reading (Y) for the first time, in both orders at 95%, along with Sutton (G) and Washington (J).
- Gemini now loses Cotton to Y, Brown's reading, and its reasons read the record more finely than the coding did.
- It counts two inflated items (flashlight, shoe rubber), which the coding merged into one element, and sees lineup steering, which the coding put as shaped by nobody.
- So Gemini's one miss is now a coding question about Cotton's elements, not a decoder invention.
- Clef sends all four records to B, Cotton's reading (51–94%): with the vivid details gone, it has nothing on the surface to match.
- Reading: the concrete picture was both the leak and what Clef matched on; fencing it helps a reasoning judge and blinds a matching one.
- v10 remains the configuration that passes the two-judge rule.
- For the family work: keep definitions and every element (v8, v10); treat the fence as a choice of judge, not a fix, until it is tested on family readings.

<!-- llm: claude-opus-5-5 | 2026-10-27 | repos/vivify-operators/experiments/round_trip/v11_identity/judged/SCORE.md | added interpretation: Gemini 3/4 (Brown found, Cotton lost on coding), Clef 1/4 (collapses on abstract readings); v10 stays the passing configuration -->
