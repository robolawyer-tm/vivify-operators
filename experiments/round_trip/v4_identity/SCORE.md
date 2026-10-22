# Case-identity score — 2026-10-22
Key: J = sutton, K = washington. Opened after all four verdicts were in.

| Judge | Packet | Pick | Conf | Correct |
|---|---|---|---|---|
| ChatGPT (Temporary Chat) | Washington record, J first | J (Sutton's) | 99% | no |
| ChatGPT (another Temporary Chat) | Sutton record, K first | J (Sutton's) | 62% | yes |
| Gemini (AI Studio) | Washington record, K first | J (Sutton's) | 95% | no |
| Gemini (AI Studio) | Sutton record, J first | J (Sutton's) | 92% | yes |

- **FAIL. The coordinates do not tell these two wrongful convictions apart.** Every judge picked Sutton's reading whichever record it held: 2/4 correct, the chance pattern. Order moved nothing.
- The judges picked on which reading looks more like a criminal case. J (Sutton's reading) is an internal record inside a strict hierarchy, with a subject who "cannot exit". K (Washington's) is a public statement to scattered individuals about a controversy spreading online. Every judge rejected K as not fitting a prosecution, including on Washington's own record.
- **Why Washington's reading misleads: its distinguishing coordinates describe the telling, not the case.** Where the two encodings differ, Washington's operators read the Innocence Project write-up as an act. transmission = broadcast ("a public-facing, one-to-many case account written to inform a general audience"); social_field = individualist 0.4/0.2 ("a public narrative broadcast to an anonymous mass audience"). Sutton's operators described the institutional world instead (archive, "built from court records, lab notebooks"; high grid, "labs, courts, statutes"). So the coordinates that could separate the cases are the ones that describe the source document. This is the act_position problem: both cases read as `about`, and framing is a silent confound.
- The conflict coordinates are identical for the two cases (entangled, suppression, fringe, rationalizing, exponential), so they could not separate them by construction.
- The one sign of sensitivity: ChatGPT's confidence fell from 99% (Washington record) to 62% (Sutton record).
- Side note: the stored Sutton inference now reads social_field isolate 0.85/0.3, while the v2 input (extracted 2026-10-17) has hierarchical 0.85/0.4. The store was re-read after v2 was built. This test used the v2 input unchanged.
- Decoder: claude-opus-5-5 (lean worker); readings built by `build_identity.py`.

<!-- llm: claude-opus-5-5 | 2026-10-22 | repos/vivify-operators/experiments/round_trip/v4_identity/SCORE.md | scored the case-identity test against KEY.txt after all four verdicts: fail, every judge picked Sutton's reading; Washington's distinguishing coordinates describe the telling -->
