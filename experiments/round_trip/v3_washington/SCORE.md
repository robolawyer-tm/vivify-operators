# Second case score — Washington — 2026-10-22
Key: M = real, N = shuffled. Opened after all four verdicts were in.

| Judge | Order | Pick | Conf | Correct |
|---|---|---|---|---|
| ChatGPT | M first | M | 99% | yes |
| ChatGPT (new Temporary Chat) | N first | M | 98% | yes |
| Gemini (AI Studio) | M first | M | 95% | yes |
| Gemini (AI Studio, new chat) | N first | M | 100% | yes |

- 4/4 correct, two model makers, both orders each; order did not move any pick.
- No judge cited self-commentary, shuffling, length or style. Every reason ties the reading to the record: state institution vs vulnerable individual, the rehearsed confession and the serology report amended to "inconclusive" (after-the-fact rationalising), the death sentence and decades to pardon (escalation), against N's two equals at global scale, early in a contest.
- Facts checked against the packet: ChatGPT used only packet facts. Gemini added two details not in the record (Washington "impoverished"; Washington's race, which the record gives only for the attacker), neither of them load-bearing.
- With Sutton (rounds one and two), two cases now pass with ChatGPT and Gemini as judges, and Sutton also with Sonnet.
- Caveat, and it is the main one: the contrast is coarse again. Washington's stored conflict coordinates are identical to Sutton's, and logos is close, so the real reading is the "institution suppresses a marginal party" picture both times, while the shuffled one lands far away. This replicates round two on a second case; it does not show that the coordinates tell one wrongful conviction from another.
- Decoder: claude-opus-5-5 (lean worker); readings built by `build_blind.py`, seed 20261022.

<!-- llm: claude-opus-5-5 | 2026-10-22 | repos/vivify-operators/experiments/round_trip/v3_washington/SCORE.md | scored the second blind case against KEY.txt after all four verdicts -->
