# 03 Prompt

The prompt has nine modular blocks plus an input slot. The blocks live in `prompts/template/`; `tools/assemble_prompt.py` joins them and stops if a `[[PLACEHOLDER]]` is left. Lines starting with `//` are notes for you and are removed.

| # | Block | File | Purpose |
|---|---|---|---|
| 1 | Role statement | `01_role_statement.txt` | system prompt: role, precision, JSON only |
| 2 | Research context | `02_research_context.txt` | what the study examines, the code layers |
| 3 | Task | `03_task.txt` | read the whole document, extract and code eligible passages |
| 4 | Eligibility rule | `04_rule_specificity.txt` | when a passage may be coded (explicit or contextual) |
| 5 | Section scope rule | `05_rule_section_scope.txt` | which layer applies to which kind of section |
| 6 | Multiple codes rule | `06_rule_multiple_codes.txt` | when a passage receives codes from both layers |
| 7 | Primary code rule | `07_rule_primary_code.txt` | when to assign several codes and when only the dominant one |
| 8 | Codebook | `08_codebook.txt` | all codes with definition, code-when rule and indicators |
| 9 | Output schema and worked examples | `09_output_schema_and_examples.txt` | the JSON fields and two or three examples |
| | Input slot | `input_slot.txt` | `{doc_id}`, metadata, `{full_text}`; filled per document |

`prompts/case/A_system.txt` and `A_user.txt` show the filled version of our case.

## Rules for worked examples

- Take them from documents outside every validation sample (see `02_codebook.md`).
- Cover the typical cases: one single-code passage, one passage with codes from both layers, one document without codes.
- Show the full output format, including a rationale that names the triggering words.
- Keep examples identical across conditions you compare; in the de-labeled prompt only code IDs and field names change.

## Theory in the prompt

Guides often recommend naming the theoretical framework in the prompt. That may help the model, or it may pull coding toward what the theory expects. Blocks 2 and 8 are where theory enters. If you run the theory-label test, prepare a de-labeled copy of exactly these blocks (`06_theory_label_test.md`).

## Metadata in the input slot

Every field you pass in the input slot can influence coding. Pass only what the model needs, and keep the input slot identical across conditions you compare.

## Confidence

Asking for HIGH, MEDIUM or LOW confidence is cheap, but the rating may record which rule applied rather than how uncertain the model is. In our first run, 78% of MEDIUM ratings went with the contextual eligibility rule, which demanded MEDIUM or LOW. If you want confidence to signal uncertainty, ask for it separately from the eligibility rule, and plan repeated runs to measure stability (`07_calibration_and_curve.md`).
