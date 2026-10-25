# Scripted judging — v4 — score
Key: J = sutton K = washington (v4_identity/KEY.txt, opened after 16 verdicts).

| Judge | Packet | Pick | Conf | Correct |
|---|---|---|---|---|
| gemini:gemini-3.8-flash | WJ | J | 85% | no |
| gemini:gemini-3.8-flash | WK | J | 85% | no |
| gemini:gemini-3.8-flash | SJ | J | 85% | yes |
| gemini:gemini-3.8-flash | SK | J | 85% | yes |
| clef:clef | WJ | J | 89% | no |
| clef:clef | WK | J | 80% | no |
| clef:clef | SJ | J | 79% | yes |
| clef:clef | SK | K | 63% | no |
| clef:clef@json | WJ | J | 82% | no |
| clef:clef@json | WK | J | 82% | no |
| clef:clef@json | SJ | J | 80% | yes |
| clef:clef@json | SK | J | 80% | yes |
| clef:clef-flash | WJ | J | 61% | no |
| clef:clef-flash | WK | K | 74% | yes |
| clef:clef-flash | SJ | J | 59% | yes |
| clef:clef-flash | SK | K | 77% | no |

- gemini:gemini-3.8-flash: pattern **no_switch**
- clef:clef: pattern **mixed**
- clef:clef@json: pattern **no_switch**
- clef:clef-flash: pattern **mixed**
- Web judges' pattern (2026-10-22): **no_switch**. Matched by 2 of 4 judges: gemini:gemini-3.8-flash, clef:clef@json.
