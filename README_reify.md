# reify

**FABRIC inverse pass: JSON inference → regenerated text**

The vivify pipeline moves from language to structure: raw text enters, keywords
and clumps emerge, the inference is filed into a category tree, and tension is scored
over the operator coordinates. reify runs that process in reverse. It takes a stored
inference — already compressed into left_keywords, clumps, category_paths, and its
tension block — and asks the Claude API to reconstruct the analog original: the felt
thought the structure was built from.

This is not summarization or paraphrase. The model is instructed to speak from
inside the meaning, not about it.

## What tension does to the output

Tension shapes the reconstruction, but not as this file claimed until 2026-09-19.
The old text described the score as left/right keyword divergence and said a score of 1.0 meant the two keyword sets shared nothing. That was the lexical score,
dead since 2026-07-13. The number now means something else entirely:

| field | meaning |
|---|---|
| `predicted` | the operators' judgment of **un-truth** — the resonance surface↔underlying gap (illusion) blended with conflict alarms. High means the text presented one thing while something else sat underneath. |
| `confirmed` | the same distance measured against the record, from claimed-vs-actual discrepancies. Only present on calibration material, where it is established fact rather than inference. |
| absent / `null` | **unmeasured**. Not low, not sincere. |

So a high-tension reconstruction keeps the doubleness the original had — surface
intact, the underneath showing through — instead of leaning into a keyword-overlap
gap that no longer exists.

`calibration_delta` is deliberately **not** sent to the model. It is `predicted`
minus `confirmed`: a measure of how far the operators were off, which is a fact
about the instrument and not about the felt thought. Sending it would invite the
model to dramatise the pipeline's own error as something the original text carried.

---

## Modes

### single

Reconstructs prose from one inference. The model receives left_keywords, clumps,
and a slice of category_paths, plus the tension block. Output is 3-6 dense
sentences in first person. Use this to test whether vivify actually captured
what was meant — if the reconstruction feels foreign, the keywords drifted.

```
python3 reify.py inferences/autovivification/analogical_religion/inf_c8e1ac73.json
```

### synthesize

Takes two inference files and generates a single passage that holds both
simultaneously. Not alternating, not summarizing — finding the place where they
are the same thought. If the two inferences pull in different directions the
model writes from that tension. Use this to discover connections the corpus
has not yet made explicit.

```
python3 reify.py --synthesize inferences/.../inf_A.json inferences/.../inf_B.json
```

### voice

Walks an entire category directory and generates a passage that speaks for the
whole category — a distillation of what all its inferences are reaching toward
together. This is the most generative mode: the emergent category tree, built
by co-occurrence across the full corpus, becomes the source material for new
prose that could not have come from any single inference.

```
python3 reify.py --voice autovivification/analogical_religion
```

---

## Options

| Flag | Description |
|------|-------------|
| `--dry-run` | Print the full prompt without calling the API. No billing. Use this to inspect what the model will receive before committing to a call. |
| `--dir <path>` | Inferences directory (default: `inferences`). Used with `--voice`. |

---

## Requirements

```
pip install anthropic
export ANTHROPIC_API_KEY=your_key_here
```

Each call to reify bills against your Anthropic API account. Use `--dry-run` first.

<!-- llm: claude-opus-5 | 2026-09-19 | repos/vivify-operators/README_reify.md | tension was still described as left/right keyword divergence, two months after the rewire and in the file documenting a generative prompt; replaced with predicted/confirmed and the reason calibration_delta is withheld -->
