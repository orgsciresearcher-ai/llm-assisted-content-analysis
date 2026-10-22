# LLM content analysis toolkit

A researcher-centered workflow for LLM-assisted content analysis, with two validity tests.

Researchers own the codebook and the interpretation. A large language model (LLM) applies the codebook at scale, one document per API call. This repository turns that workflow into a toolset: a step-by-step guide, modular prompt templates, scripts for coding, sampling, blind coding and analysis, and the materials of an illustrative case.

The two validity tests answer two practical questions:

- **Theory-label test.** Does LLM coding follow the text or the codebook's theoretical framing? Code the corpus twice with the original prompt (A, A′) and once with a de-labeled copy (B) that keeps every definition, rule and example but removes code names, theoretical headings and references.
- **Confidence-calibration test.** Does the model's confidence point to its errors? Blind-code a stratified sample, compare the model with the reference coding per confidence level, and derive a **review-effort curve**: the share of segments researchers need to review, lowest confidence first, to reach a target level of agreement.

![Workflow](figures/figure1_workflow.png)

## Status

| Part | Status |
|---|---|
| Guide, prompt templates, codebook template | ready |
| Coding pipeline, de-labeling script, sampling, blind sheets, agreement statistics, review-effort calculator, cost estimate | ready, tested on the demo corpus and the case data |
| Case materials of the first full run (prompts, codebooks, coded segments, raw model output, logs, calibration coding) | shared |
| Preregistered thresholds and the drawn calibration sample | fixed before any test run |
| Results of the theory-label test and the confidence-calibration test | to follow |

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                     # add your API key; .env is ignored by git

# 1  render the case prompt for a demo document (no API call)
python tools/run_coding.py --corpus examples/demo_corpus.csv --id-col doc_id --text-col full_text \
  --system prompts/case/A_system.txt --user prompts/case/A_user.txt \
  --field ad_id=doc_id --field role_family=role \
  --codebook codebook/case/codebook_A_original.csv --run-label demo --model MODEL_ID --dry-run 1 --out-dir runs

# 2  run the whole pipeline on a stored response (no API call, no cost)
python tools/run_coding.py ... --mock-response examples/mock_response.json

# 3  plan a review budget with assumed values
python tools/review_effort_curve.py params --levels "LOW:0.004:0.60,MEDIUM:0.231:0.80,HIGH:0.765:0.85" \
  --human 0.97 --target 0.90 --out runs/curve.csv --plot runs/curve.png
```

For your own study, start with `guide/00_workflow.md`.

## Repository structure

```
guide/            step-by-step guide (00 to 08) and decisions.md with defensible options
prompts/template/ the nine modular prompt blocks with placeholders, plus the input slot
prompts/case/     prompts A and B of the case, code mapping, change log A to B (28 edits)
codebook/         template.csv and the two case codebooks with their mapping
tools/            Python scripts (see the table below)
templates/        blind coding sheet and adjudication sheet (xlsx)
examples/         three fictional documents and a stored model response for testing
case/             data, samples, results and preregistration of the illustrative case
figures/          Figure 1 and Figure 2 with the scripts that draw them
appendix/         technical appendix (PDF)
```

| Script | Purpose |
|---|---|
| `tools/assemble_prompt.py` | build system and user prompt from the nine blocks |
| `tools/run_coding.py` | code a corpus, archive raw responses, check outputs against codebook and source text |
| `tools/build_delabeled_prompt.py` | derive prompt B from prompt A through logged, counted edits |
| `tools/draw_samples.py` | calibration sample, adjudication cells, document sample, list of uncoded documents, all with fixed seeds |
| `tools/make_blind_sheets.py` | one blind Excel sheet per coder for segments, cells or whole documents, without model codes or confidence |
| `tools/agreement.py` | document × code matrices, κ, PABAK, bootstrap intervals, decision rule |
| `tools/review_effort_curve.py` | the review-effort calculator, from assumptions or from adjudicated sheets |
| `tools/estimate_cost.py` | API cost estimate from tokens or from an earlier invoice |
| `tools/redact_personal_data.py` | remove contact details before sharing coded text |

## The illustrative case

The case codes job ads for AI leadership roles (for example Chief AI Officer, Head of AI) and comparison roles (CIO, CTO, CDO) with a theory-driven codebook of 17 governance-tension codes and 3 skill codes. It serves to test the workflow; the substantive findings are reported elsewhere. See `case/README.md` for what is shared and why full ad texts are not.

## Requirements

Python 3.10 or later. `anthropic` is needed only for real API runs. Figure 1 is drawn with Playwright and Chromium (`figures/figure1_workflow.py`); all other scripts need only the packages in `requirements.txt`.

## License

Code: MIT (see `LICENSE`). Guide, prompt templates, codebook template, sheet templates and figures: CC BY 4.0 (see `LICENSE-docs.md`). Case data: see `case/README.md`.

## Anonymity

This repository is anonymized for peer review. Author names and affiliations will be added after the review.
