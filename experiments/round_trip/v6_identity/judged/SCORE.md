# Scripted judging — v6 — score
Key: X = washington Y = sutton (v6_identity/KEY.txt, opened after 20 verdicts).

| Judge | Packet | Pick | Conf | Correct |
|---|---|---|---|---|
| gemini:gemini-3.8-flash | WX | X | 85% | yes |
| gemini:gemini-3.8-flash | WY | Y | 85% | no |
| gemini:gemini-3.8-flash | SX | X | 85% | no |
| gemini:gemini-3.8-flash | SY | X | 85% | no |
| groq:openai/gpt-oss-120b | WX | X | 78% | yes |
| groq:openai/gpt-oss-120b | WY | X | 85% | yes |
| groq:openai/gpt-oss-120b | SX | X | 85% | no |
| groq:openai/gpt-oss-120b | SY | X | 82% | no |
| groq:qwen/qwen3.8-27b | WX | X | 85% | yes |
| groq:qwen/qwen3.8-27b | WY | X | 90% | yes |
| groq:qwen/qwen3.8-27b | SX | X | 75% | no |
| groq:qwen/qwen3.8-27b | SY | X | 85% | no |
| clef:clef | WX | X | 86% | yes |
| clef:clef | WY | X | 76% | yes |
| clef:clef | SX | X | 81% | no |
| clef:clef | SY | X | 69% | no |
| clef:clef@json | WX | X | 88% | yes |
| clef:clef@json | WY | X | 88% | yes |
| clef:clef@json | SX | X | 88% | no |
| clef:clef@json | SY | X | 88% | no |

- gemini:gemini-3.8-flash: pattern **mixed**
- groq:openai/gpt-oss-120b: pattern **no_switch**
- groq:qwen/qwen3.8-27b: pattern **no_switch**
- clef:clef: pattern **no_switch**
- clef:clef@json: pattern **no_switch**
