# Scripted judging — v3 — score
Key: M = real N = shuffled (v3_washington/KEY.txt, opened after 12 verdicts).

| Judge | Packet | Pick | Conf | Correct |
|---|---|---|---|---|
| gemini:gemini-3.8-flash | M | M | 90% | yes |
| gemini:gemini-3.8-flash | N | M | 95% | yes |
| groq:openai/gpt-oss-120b | M | M | 78% | yes |
| groq:openai/gpt-oss-120b | N | N | 71% | no |
| groq:qwen/qwen3.8-27b | M | M | 75% | yes |
| groq:qwen/qwen3.8-27b | N | N | 95% | no |
| clef:clef | M | M | 86% | yes |
| clef:clef | N | M | 57% | yes |
| clef:clef@swap | M | M | 86% | yes |
| clef:clef@swap | N | M | 57% | yes |
| clef:clef@rep | M | M | 86% | yes |
| clef:clef@rep | N | M | 57% | yes |

- gemini:gemini-3.8-flash: pattern **real**
- groq:openai/gpt-oss-120b: pattern **mixed**
- groq:qwen/qwen3.8-27b: pattern **mixed**
- clef:clef: pattern **real**
- clef:clef@swap: pattern **real**
- clef:clef@rep: pattern **real**
- Web judges' pattern (2026-10-22): **real**. Matched by 4 of 6 judges: gemini:gemini-3.8-flash, clef:clef, clef:clef@swap, clef:clef@rep.
