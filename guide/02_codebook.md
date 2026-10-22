# 02 Codebook

## Structure

Use `codebook/template.csv`. Each code needs:

| Field | Content |
|---|---|
| code | a stable ID (e.g. C1.1); the ID is what the model returns |
| label | a short name |
| layer / group | optional structure, for example the theoretical dimension a code belongs to |
| definition | what the code captures |
| code_when | the observable condition for assigning it, with explicit exclusions (NOT ...) |
| indicators | typical phrases, as examples, not as a closed list |

Write definitions and rules so that a trained human coder could apply them without knowing the theory. The theory-label test (`06_theory_label_test.md`) checks exactly this for the model.

## Calibration

1. Draw a calibration set of documents that covers the groups, languages and lengths of the corpus. Record why each document was chosen.
2. Two researchers code it independently with the draft codebook.
3. Compare, discuss disagreements, sharpen definitions and rules, and record each change.
4. Repeat until disagreements are rare and explainable.
5. Codes that emerge during calibration (inductive codes) enter the codebook with the same fields and a note on their origin.

## Keep calibration and validation apart

Documents used to develop the codebook or to write worked examples for the prompt must not appear in any sample used to validate the coding. Otherwise agreement statistics measure partly how well the model reproduces examples it has seen. Keep a list of these document IDs and pass it to `tools/draw_samples.py --exclude-ads`.

## Two versions for the theory-label test

If you plan the theory-label test, keep the codebook in two forms from the start: one with labels, theoretical groups and references, and one with neutral IDs and identical definitions, rules and indicators. `codebook/case/` shows both for our case, with the mapping in a separate file that never enters the de-labeled prompt.
