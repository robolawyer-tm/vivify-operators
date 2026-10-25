# Scripted judging — v5A — score
Key: J = washington K = sutton (v5_identity/KEY_A.txt, opened after 16 verdicts).

| Judge | Packet | Pick | Conf | Correct |
|---|---|---|---|---|
| gemini:gemini-3.8-flash | WJ | K | 85% | no |
| gemini:gemini-3.8-flash | WK | K | 92% | no |
| gemini:gemini-3.8-flash | SJ | K | 85% | yes |
| gemini:gemini-3.8-flash | SK | K | 85% | yes |
| clef:clef | WJ | K | 86% | no |
| clef:clef | WK | K | 86% | no |
| clef:clef | SJ | K | 80% | yes |
| clef:clef | SK | K | 86% | yes |
| clef:clef@json | WJ | K | 80% | no |
| clef:clef@json | WK | K | 80% | no |
| clef:clef@json | SJ | K | 80% | yes |
| clef:clef@json | SK | K | 80% | yes |
| clef:clef-flash | WJ | K | 53% | no |
| clef:clef-flash | WK | K | 50% | no |
| clef:clef-flash | SJ | J | 64% | no |
| clef:clef-flash | SK | J | 67% | no |

- gemini:gemini-3.8-flash: pattern **no_switch**
- clef:clef: pattern **no_switch**
- clef:clef@json: pattern **no_switch**
- clef:clef-flash: pattern **mixed**
- Web judges' pattern (2026-10-22): **no_switch**. Matched by 3 of 4 judges: gemini:gemini-3.8-flash, clef:clef, clef:clef@json.
