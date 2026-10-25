# Scripted judging — v3 — score
Key: M = real N = shuffled (v3_washington/KEY.txt, opened after 8 verdicts).

| Judge | Packet | Pick | Conf | Correct |
|---|---|---|---|---|
| gemini:gemini-3.8-flash | M | M | 90% | yes |
| gemini:gemini-3.8-flash | N | M | 95% | yes |
| clef:clef | M | M | 86% | yes |
| clef:clef | N | M | 57% | yes |
| clef:clef@json | M | M | 74% | yes |
| clef:clef@json | N | M | 74% | yes |
| clef:clef-flash | M | M | 75% | yes |
| clef:clef-flash | N | M | 73% | yes |

- gemini:gemini-3.8-flash: pattern **real**
- clef:clef: pattern **real**
- clef:clef@json: pattern **real**
- clef:clef-flash: pattern **real**
- Web judges' pattern (2026-10-22): **real**. Matched by 4 of 4 judges: gemini:gemini-3.8-flash, clef:clef, clef:clef@json, clef:clef-flash.
