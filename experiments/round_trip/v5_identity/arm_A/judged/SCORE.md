# Scripted judging — v5A — score
Key: J = washington K = sutton (v5_identity/KEY_A.txt, opened after 12 verdicts).

| Judge | Packet | Pick | Conf | Correct |
|---|---|---|---|---|
| gemini:gemini-3.8-flash | WJ | K | 85% | no |
| gemini:gemini-3.8-flash | WK | K | 92% | no |
| gemini:gemini-3.8-flash | SJ | K | 85% | yes |
| gemini:gemini-3.8-flash | SK | K | 85% | yes |
| groq:openai/gpt-oss-120b | WJ | K | 80% | no |
| groq:openai/gpt-oss-120b | WK | K | 70% | no |
| groq:openai/gpt-oss-120b | SJ | K | 82% | yes |
| groq:openai/gpt-oss-120b | SK | K | 85% | yes |
| groq:qwen/qwen3.8-27b | WJ | K | 60% | no |
| groq:qwen/qwen3.8-27b | WK | J | 75% | yes |
| groq:qwen/qwen3.8-27b | SJ | K | 85% | yes |
| groq:qwen/qwen3.8-27b | SK | K | 85% | yes |

- gemini:gemini-3.8-flash: pattern **no_switch**
- groq:openai/gpt-oss-120b: pattern **no_switch**
- groq:qwen/qwen3.8-27b: pattern **mixed**
- Web judges' pattern (2026-10-22): **no_switch**. Matched by 2 of 3 judges: gemini:gemini-3.8-flash, groq:openai/gpt-oss-120b.
