# First full run: descriptive results

Results of the theory-label test and the confidence-calibration test will be added here once the Phase 1 runs and the blind coding are complete. The thresholds were fixed beforehand (`../preregistration/thresholds.md`).

## Setup

| Item | Value |
|---|---|
| Model | Claude Sonnet 4.6 (`claude-sonnet-4-6`), via API |
| Calls | one ad per call, 1.5 s between calls |
| Settings | maximum 4,000 output tokens; no temperature parameter sent; ads under 100 characters skipped (none) |
| Prompt | system prompt and user template as in `prompts/case/A_*.txt` |
| Output | JSON array per ad: segment, codes per layer, inductive label, confidence (HIGH, MEDIUM, LOW), rationale |
| Human review | all LOW segments and all inductive suggestions; changes recorded as "Edit: ..." in 32 rationales |
| Cost | about USD 50 for the whole run, including repeated calls (provider invoice) |
| Tokens | first pass, 706 ads with valid output: 3,492,827 input and 1,331,896 output tokens (mean 4,947 and 1,887 per ad) |

## Output by role

| Role | Ads | Coded segments | Segments per ad | Failed first-pass responses | Ads without any code |
|---|---|---|---|---|---|
| AI Manager | 154 | 1,484 | 9.6 | 16 (10%) | 4 (3%) |
| Head of AI | 298 | 3,441 | 11.5 | 48 (16%) | 3 (1%) |
| Chief AI Officer | 55 | 646 | 11.7 | 9 (16%) | 0 (0%) |
| AI Lead | 102 | 1,062 | 10.4 | 13 (13%) | 1 (1%) |
| CTO | 89 | 304 | 3.4 | 1 (1%) | 32 (36%) |
| CIO | 79 | 154 | 1.9 | 1 (1%) | 37 (47%) |
| CDO | 17 | 35 | 2.1 | 0 (0%) | 9 (53%) |
| Total | 794 | 7,126 | 9.0 | 88 (11%) | 86 (11%) |

Failed responses were JSON that could not be parsed: 42 were cut off (unterminated strings, typical of output that reaches the token limit) and 46 were otherwise malformed. All 88 were re-run. 86 of the 88 came from AI leadership roles, which yield three to six times more segments per ad than the comparison roles. Dropping instead of re-running them would have biased every comparison between role groups.

## Confidence

| Confidence | Coded segments | Share |
|---|---|---|
| HIGH | 5,452 | 76.5% |
| MEDIUM | 1,647 | 23.1% |
| LOW | 27 | 0.4% |
| Total | 7,126 | 100% |

In addition, 168 rows record ads or passages without any code (NONE rows). 1,289 of the 1,647 MEDIUM segments (78%) have a rationale that cites contextual specificity, i.e. the rule that passages referring to AI only through their section heading must receive MEDIUM or LOW confidence. MEDIUM therefore records which rule applied more than the model's uncertainty. Excluding the 32 calibration ads, the population for the calibration sample is 6,773 coded segments: 27 LOW, 1,238 MEDIUM via the contextual rule, 347 MEDIUM via explicit terms, and 5,161 HIGH.

## Inductive suggestions

The model proposed an inductive label for 118 segments in 61 ads, using 117 distinct labels; only one label occurred twice. Examples: "AI agent lifecycle management", "AI research prioritization authority", "Cross-functional AI embedding". With one ad per call, the model cannot check the codebook rule that a new code must recur across ads. We pooled all suggestions and kept none as a new code after a relevancy and frequency analysis. All suggestions are listed in `../data/inductive_suggestions.csv`.

## Agreement on the calibration ads

The prior study compared the model's codes for the 32 calibration ads with our consensus coding, using the same prompt as the main run, including codebook, coding rules and worked examples: percent agreement 98.5% and Cohen's κ = 0.880 across 277 code segments ("almost perfect" in the terms of Landis & Koch, 1977). Our consensus coding is in `../data/calibration_coding.csv`.
