# Case-identity rerun, arm A — score — 2026-10-22
Key: J = washington, K = sutton (KEY_A.txt, opened after all four arm A verdicts).
Arm A input = the current store's coordinates only: social_field now scores the events (Washington hierarchical 0.85/0.6, Sutton isolate 0.85/0.4), and there are no account values.

| Judge | Packet | Pick | Conf | Correct |
|---|---|---|---|---|
| ChatGPT (Temporary Chat) | Washington record, J first | K (Sutton's) | 96% | no |
| Gemini (AI Studio) | Washington record, K first (order unconfirmed; John's label said Sutton, the text is Washington) | K (Sutton's) | 95% | no |
| Gemini (AI Studio, new chat) | Sutton record, J first | K (Sutton's) | 95% | yes |
| ChatGPT (Temporary Chat) | Sutton record, K first | K (Sutton's) | 78% | yes |

- **FAIL, 2/4: the chance pattern, the same as v4.** Every judge picked Sutton's reading on both records. ChatGPT's confidence fell on the second record (96% → 78%), as in v4.
- **The social_field fix alone does not separate the cases.** It made the coordinates honest: both now read the criminal justice system. But an honest match is still a match.
- **A second telling-level leak remains: transmission.** Washington's input still has transmission = broadcast (logos and structural), while Sutton's has archive. Both describe the Innocence Project page, the same genre judged two ways (Washington's vote was 2-1). Washington's reading became "a public statement during a spreading crisis", and every judge rejected it as not a criminal case, including on Washington's own record. This is the v4 failure, now through transmission rather than social_field.
- With arm B (SCORE_B.md, 4/4, both judges switching), the attribution is clear: **the account values (how the account the institution relied on was made, who supplied it, who shaped it) are what tell the two cases apart.** The conflict coordinates are identical, and the remaining logos difference points the wrong way.
- Next candidate (not built): give transmission the same two levels as social_field, or treat it as telling-level only, since in all five field cases it described the page.

<!-- llm: claude-opus-5-5 | 2026-10-22 | repos/vivify-operators/experiments/round_trip/v5_identity/SCORE_A.md | scored arm A against KEY_A: 2/4, every judge picks Sutton's reading; transmission is the remaining telling-level leak; arm B's pass is attributable to the account values -->
