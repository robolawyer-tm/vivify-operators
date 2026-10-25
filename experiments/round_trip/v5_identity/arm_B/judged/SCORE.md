# Scripted judging — v5B — score
Key: J = sutton K = washington (v5_identity/KEY_B.txt, opened after 16 verdicts).

| Judge | Packet | Pick | Conf | Correct |
|---|---|---|---|---|
| gemini:gemini-3.8-flash | WJ | K | 95% | yes |
| gemini:gemini-3.8-flash | WK | K | 95% | yes |
| gemini:gemini-3.8-flash | SJ | J | 95% | yes |
| gemini:gemini-3.8-flash | SK | J | 95% | yes |
| clef:clef | WJ | K | 95% | yes |
| clef:clef | WK | K | 96% | yes |
| clef:clef | SJ | J | 86% | yes |
| clef:clef | SK | K | 78% | no |
| clef:clef@json | WJ | K | 95% | yes |
| clef:clef@json | WK | K | 95% | yes |
| clef:clef@json | SJ | J | 91% | yes |
| clef:clef@json | SK | J | 91% | yes |
| clef:clef-flash | WJ | K | 60% | yes |
| clef:clef-flash | WK | K | 83% | yes |
| clef:clef-flash | SJ | J | 89% | yes |
| clef:clef-flash | SK | J | 61% | yes |

- gemini:gemini-3.8-flash: pattern **switch**
- clef:clef: pattern **mixed**
- clef:clef@json: pattern **switch**
- clef:clef-flash: pattern **switch**
- Web judges' pattern (2026-10-22): **switch**. Matched by 3 of 4 judges: gemini:gemini-3.8-flash, clef:clef@json, clef:clef-flash.
