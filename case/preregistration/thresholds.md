# Preregistered thresholds and sampling decisions

Fixed on 2026-10-19, before any Phase 1 run (A, A′, B) and before any blind coding.
The machine-readable copy is `thresholds.json`; `tools/agreement.py` and `tools/draw_samples.py` read these values.
The commit history of this file documents that it predates the runs.

## Theory-label test (runs A, A′, B)

Unit: document × code, binary (the code appears in at least one segment of the document). One matrix per run, 794 documents × 20 codes.

A code shows a **label effect** only if both conditions hold:

1. κ(A, A′) − κ(A, B) > **0.10**, and the 95% bootstrap interval of this difference excludes zero
   (2,000 resamples of documents with replacement, seed 20261101).
2. The prevalence difference B − A lies outside the 95% bootstrap interval of the prevalence difference A′ − A (the noise band).

The **substantive conclusion holds** if, for every code whose prevalence gap between AI leadership roles and comparison roles is at least **10 percentage points** in run A, the gap has the same sign in run B.

Interpretation fixed in advance (as stated in the proposal): if only single codes shift, sharper code definitions suffice; if the substantive conclusion changes, we recommend coding with a de-labeled prompt.

**Adjudication:** 50 cells drawn at random (seed 20261101) from all cells in which A and A′ agree and B departs. Both authors judge blind, without knowing which prompt assigned the code, whether the text supports the code. With 50 cells, the share of cells in which the text supports B is estimated within ±14 percentage points (95% confidence, worst case p = 0.5).

## Confidence-calibration test

**Sample:** 227 coded segments from the first run, calibration ads excluded (`case/samples/calibration_test_sample.csv`, seed 20261101):
all 27 LOW, 50 MEDIUM coded via the contextual rule, 50 MEDIUM coded via explicit terms, and 100 HIGH.

**Unit of agreement:** a segment agrees only if its full set of codes matches the reference coding.

**Curve:** levels reviewed from LOW to HIGH, in random order within a level; weights = shares of the levels in the first run (LOW 0.4%, MEDIUM 23.1%, HIGH 76.5%); reviewed segments take the coder-coder agreement before adjudication. The target is **90%** percent agreement (Lombard et al., 2002).

## Phase 2

Document-level blind coding of 10% of the second corpus (about 170 documents), drawn with seed 20261101.

## Changes

Any change after this date will be recorded below with date and reason.

| Date | Change | Reason |
|---|---|---|
