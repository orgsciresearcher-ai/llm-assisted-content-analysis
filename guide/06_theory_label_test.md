# 06 Theory-label test

**Question.** Does LLM coding follow the text or the theoretical framing of the codebook?

When the codebook's authors also serve as the human benchmark, high agreement may reflect shared theoretical expectations rather than a shared reading of the text. The test removes theory from the prompt on purpose and measures what changes. It differs from prompt stability scoring, which paraphrases instructions to test robustness.

## Design

| Run | Prompt | Purpose |
|---|---|---|
| A | original prompt | baseline |
| A′ | original prompt, run again | noise floor: how much two identical runs differ by chance |
| B | de-labeled prompt | test condition |

All three runs use the same model and the same input slot, close in time. B keeps every definition, rule, indicator and worked example word for word. It replaces code names with neutral IDs and drops theoretical headings and references. Derive B by script, with every edit counted (`tools/build_delabeled_prompt.py`; our case needs 28 edits, listed in `prompts/case/change_log_A_to_B.md`).

## Analysis

1. Build a document × code matrix per run (`tools/agreement.py matrix`; map B codes back with the code mapping).
2. Per code: prevalence in A, A′, B; κ and PABAK for A–A′ and A–B; bootstrap intervals over documents.
3. Decision rule (fix it before the runs, see `case/preregistration/thresholds.md`): a code shows a label effect if κ(A, A′) − κ(A, B) exceeds a threshold with a bootstrap interval above zero, and the prevalence difference B − A lies outside the noise band of A′ − A.
4. Substantive check: does the main conclusion of the study (in our case, the gap between AI leadership and comparison roles) keep its sign in B?
5. Adjudication: draw cells where A and A′ agree and B departs (`tools/draw_samples.py adjudication`), judge blind whether the text supports the code (`tools/make_blind_sheets.py adjudication`), and read the rationales of both conditions to classify errors.

With 50 adjudicated cells, the share of cells in which the text supports B is estimated within ±14 percentage points (95% confidence, worst case).

## Reading the result

- No label effect: coding follows the definitions; theory in the prompt is harmless for this codebook.
- Single codes shift: sharpen those definitions.
- The conclusion changes: code with the de-labeled prompt and keep theory for interpretation.

The test measures how framing inside the prompt shifts coding. It does not measure what the model learned in training.
