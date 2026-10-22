# Illustrative case: job ads for AI leadership roles

The case tests the workflow on job ads for four AI leadership roles (AI Manager, Head of AI, Chief AI Officer, AI Lead) and three comparison roles (CIO, CTO, CDO), collected from LinkedIn and Adzuna in 2026 and coded with a theory-driven codebook of 17 governance-tension codes and 3 skill codes. The substantive study is reported elsewhere (reference blinded for review).

## Files

| File | Content | Rows |
|---|---|---|
| `data/ads_index.csv` | one row per ad: ID, role, source, URL without tracking parameters, posting month, language, text length, SHA-256 of the full text (first 12 characters) | 794 |
| `data/coded_segments.csv` | coded segments after human review (final first-run output) | 7,294 |
| `data/raw_outputs/first_pass_output.csv` | parsed model output before human review | 7,014 |
| `data/raw_outputs/processing_log.csv` | per ad: status of the first pass, segments found, input and output tokens, error message | 794 |
| `data/inductive_suggestions.csv` | all segments for which the model proposed an inductive label | 118 |
| `data/calibration_ads.csv` | the 32 calibration ads with sampling rationale | 32 |
| `data/calibration_coding.csv` | our consensus coding of the calibration ads (segments, codes, rationale) | 341 |
| `samples/calibration_test_sample.csv` | the 227 segments of the confidence-calibration test, drawn before any blind coding | 227 |
| `samples/recall_check_uncoded_ads.csv` | all ads to which the model assigned no code, for the recall check | 86 |
| `preregistration/thresholds.md`, `thresholds.json` | thresholds, samples and seeds fixed before the Phase 1 runs | |
| `results/first_run.md` | descriptive results of the first run; test results will follow | |

## Notes on the data

**SK4.** Seven assignments of SK4 remain in `coded_segments.csv`; SK4 was an inductive code that was added provisionally and later dropped.

**Review notes.** In `coded_segments.csv`, 32 rationales end with "Edit: ...". These notes record changes made during human review.

**Calibration coding.** `calibration_coding.csv` has rows for 31 of the 32 calibration ads; our coding file holds no rows for JOB_0944 (CTO).

**NONE rows.** Ads or passages without any code appear as rows with GT_code and SK_code = NONE (168 rows). Coded segments are the remaining 7,126 rows.

## What is not shared, and why

- **Full ad texts.** Platform terms may prohibit redistribution. The index gives the URL and a hash of each text as we stored it, so others can check whether a text they retrieve matches. Coded segments are short verbatim passages needed to check the coding.
- **Personal data.** The ads describe roles, not persons. We scanned all shared text fields for e-mail addresses, phone numbers and profile links and found none.
- **Collection scripts.** Not part of this repository.

## License of the case data

Our calibration coding, review notes, samples, preregistration and results, as well as the model outputs, are shared under CC BY 4.0. Quoted passages from job ads remain subject to the rights of their authors and the terms of the platforms; they are shared for the purpose of verifying the research.
