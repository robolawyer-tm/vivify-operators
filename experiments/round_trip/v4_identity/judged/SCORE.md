# Scripted judging — v4 — score
Key: J = sutton K = washington (v4_identity/KEY.txt, opened after 24 verdicts).

| Judge | Packet | Pick | Conf | Correct |
|---|---|---|---|---|
| gemini:gemini-3.8-flash | WJ | J | 85% | no |
| gemini:gemini-3.8-flash | WK | J | 85% | no |
| gemini:gemini-3.8-flash | SJ | J | 85% | yes |
| gemini:gemini-3.8-flash | SK | J | 85% | yes |
| groq:openai/gpt-oss-120b | WJ | J | 75% | no |
| groq:openai/gpt-oss-120b | WK | J | 70% | no |
| groq:openai/gpt-oss-120b | SJ | J | 70% | yes |
| groq:openai/gpt-oss-120b | SK | K | 75% | no |
| groq:qwen/qwen3.8-27b | WJ | J | 80% | no |
| groq:qwen/qwen3.8-27b | WK | J | 90% | no |
| groq:qwen/qwen3.8-27b | SJ | K | 60% | no |
| groq:qwen/qwen3.8-27b | SK | K | 55% | no |
| clef:clef | WJ | J | 89% | no |
| clef:clef | WK | J | 80% | no |
| clef:clef | SJ | J | 79% | yes |
| clef:clef | SK | K | 63% | no |
| clef:clef@swap | WJ | J | 89% | no |
| clef:clef@swap | WK | J | 80% | no |
| clef:clef@swap | SJ | J | 79% | yes |
| clef:clef@swap | SK | K | 63% | no |
| clef:clef@rep | WJ | J | 89% | no |
| clef:clef@rep | WK | J | 80% | no |
| clef:clef@rep | SJ | J | 79% | yes |
| clef:clef@rep | SK | K | 63% | no |

- gemini:gemini-3.8-flash: pattern **no_switch**
- groq:openai/gpt-oss-120b: pattern **mixed**
- groq:qwen/qwen3.8-27b: pattern **mixed**
- clef:clef: pattern **mixed**
- clef:clef@swap: pattern **mixed**
- clef:clef@rep: pattern **mixed**
- Web judges' pattern (2026-10-22): **no_switch**. Matched by 1 of 6 judges: gemini:gemini-3.8-flash.
