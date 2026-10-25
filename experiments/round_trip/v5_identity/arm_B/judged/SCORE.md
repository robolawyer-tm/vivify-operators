# Scripted judging — v5B — score
Key: J = sutton K = washington (v5_identity/KEY_B.txt, opened after 24 verdicts).

| Judge | Packet | Pick | Conf | Correct |
|---|---|---|---|---|
| gemini:gemini-3.8-flash | WJ | K | 95% | yes |
| gemini:gemini-3.8-flash | WK | K | 95% | yes |
| gemini:gemini-3.8-flash | SJ | J | 95% | yes |
| gemini:gemini-3.8-flash | SK | J | 95% | yes |
| groq:openai/gpt-oss-120b | WJ | K | 85% | yes |
| groq:openai/gpt-oss-120b | WK | K | 90% | yes |
| groq:openai/gpt-oss-120b | SJ | J | 85% | yes |
| groq:openai/gpt-oss-120b | SK | J | 90% | yes |
| groq:qwen/qwen3.8-27b | WJ | K | 95% | yes |
| groq:qwen/qwen3.8-27b | WK | K | 90% | yes |
| groq:qwen/qwen3.8-27b | SJ | J | 75% | yes |
| groq:qwen/qwen3.8-27b | SK | J | 95% | yes |
| clef:clef | WJ | K | 95% | yes |
| clef:clef | WK | K | 96% | yes |
| clef:clef | SJ | J | 86% | yes |
| clef:clef | SK | K | 78% | no |
| clef:clef@swap | WJ | K | 95% | yes |
| clef:clef@swap | WK | K | 96% | yes |
| clef:clef@swap | SJ | J | 86% | yes |
| clef:clef@swap | SK | K | 78% | no |
| clef:clef@rep | WJ | K | 95% | yes |
| clef:clef@rep | WK | K | 96% | yes |
| clef:clef@rep | SJ | J | 86% | yes |
| clef:clef@rep | SK | K | 78% | no |

- gemini:gemini-3.8-flash: pattern **switch**
- groq:openai/gpt-oss-120b: pattern **switch**
- groq:qwen/qwen3.8-27b: pattern **switch**
- clef:clef: pattern **mixed**
- clef:clef@swap: pattern **mixed**
- clef:clef@rep: pattern **mixed**
- Web judges' pattern (2026-10-22): **switch**. Matched by 3 of 6 judges: gemini:gemini-3.8-flash, groq:openai/gpt-oss-120b, groq:qwen/qwen3.8-27b.
