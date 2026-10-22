# 08 Reporting

Report enough for a reader to judge and repeat the coding. Many published studies report no model parameters at all.

## Checklist

**Model and settings**
- exact model ID, access route (API), dates of the runs
- maximum output tokens, temperature (or that none was set, and why), other parameters
- one document per call or batching

**Prompt and codebook**
- full prompt text, including worked examples and input slot, with a hash
- codebook with definitions, rules and indicators; origin of inductive codes

**Corpus**
- population, sources, period, cleaning steps with counts, documents excluded and why

**Validation**
- agreement on the calibration set: percent agreement, Cohen's κ, and PABAK per code, with the number of units
- document whether calibration documents were also used to build the prompt
- confidence calibration: percent agreement per confidence level, coder-coder agreement, the review-effort curve and the review share chosen
- theory-label test: per-code κ and PABAK for A–A′ and A–B, prevalence differences with intervals, the decision per code, the substantive check
- test-retest stability between identical runs (share of document-code decisions that flip)

**Failures and review**
- failed or malformed responses by group, and how they were handled
- number of outputs flagged (codes outside the codebook, non-verbatim segments)
- number of segments reviewed and changed

**Costs and data**
- API cost and tokens
- what data are shared, what is withheld and why (platform terms, personal data)

## Statistics

`tools/agreement.py` computes per-code κ (Cohen) and PABAK (2 × percent agreement − 1). Report both: κ drops for rare codes even when agreement is high, and PABAK adjusts for prevalence. Bootstrap intervals resample documents, not cells, because cells within a document are not independent.
