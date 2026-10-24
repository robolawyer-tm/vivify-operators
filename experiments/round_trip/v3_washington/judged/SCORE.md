# Scripted judging — v3 — score
Key: M = real N = shuffled (v3_washington/KEY.txt, opened after 6 verdicts).

| Judge | Packet | Pick | Conf | Correct |
|---|---|---|---|---|
| gemini:gemini-3.8-flash | M | M | 90% | yes |
| gemini:gemini-3.8-flash | N | M | 95% | yes |
| groq:openai/gpt-oss-120b | M | M | 78% | yes |
| groq:openai/gpt-oss-120b | N | N | 71% | no |
| groq:qwen/qwen3.8-27b | M | M | 75% | yes |
| groq:qwen/qwen3.8-27b | N | N | 95% | no |

- gemini:gemini-3.8-flash: pattern **real**
- groq:openai/gpt-oss-120b: pattern **mixed**
- groq:qwen/qwen3.8-27b: pattern **mixed**
- Web judges' pattern (2026-10-22): **real**. Matched by 1 of 3 judges: gemini:gemini-3.8-flash.
