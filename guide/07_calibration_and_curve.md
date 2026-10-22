# 07 Confidence-calibration test and review-effort curve

**Question.** Does model confidence point to errors, and how much human review does a coded dataset need to reach a target level of agreement?

## Sample

Draw a stratified sample of coded segments by confidence level (`tools/draw_samples.py calibration`). Exclude documents used for calibration or worked examples. Our case: all 27 LOW segments, 100 MEDIUM (50 coded via the contextual rule, 50 via explicit terms, to see whether MEDIUM records uncertainty or only the rule) and 100 HIGH, 227 in total, seed 20261101.

## Blind coding

Two researchers code each sampled segment independently with the full codebook (`tools/make_blind_sheets.py segments`). They see the segment, the text just before it with its heading, and a link to the document. They do not see the model's codes, confidence or rationale, because wrong model labels can lower human accuracy. Afterwards they resolve disagreements into a reference coding.

## Unit of agreement

A segment agrees only if its **full set of codes** matches. Agreement per segment-code cell would be inflated by the many codes that do not apply (in our first run it was about 98%), and the curve would say nothing.

## The curve

For each confidence level l:

- p_l = percent agreement between model and reference (strata pooled by population weights)
- h_l = percent agreement between the two coders before adjudication
- w_l = share of level l among all coded segments

Review proceeds from the lowest to the highest level, in random order within a level. With s the share of all segments reviewed and r_l(s) the reviewed fraction of level l:

PA(s) = Σ_l w_l [ r_l(s) h_l + (1 − r_l(s)) p_l ]

Random order within a level makes the expected curve linear inside each level. `tools/review_effort_curve.py` computes it, with a bootstrap band, and reports the smallest s that reaches the target. Our target is 90% (Lombard et al., 2002, consider intercoder agreement of .90 or greater nearly always acceptable).

## Shapes and what they mean

| Shape | Meaning | Review rule |
|---|---|---|
| early flattening | errors cluster at low confidence | review by confidence |
| linear | confidence carries no signal about errors | confidence-based review is no better than a random sample |
| late jump | errors hide among confident segments | review more, or route by run stability; look for a class of confident errors |

## Recall check

The sample contains only passages the model extracted, so it cannot show what the model missed. List all documents without any code (`tools/draw_samples.py uncoded`) and have both researchers read them in full and code them blind with the full codebook (`tools/make_blind_sheets.py documents`). A missed code is one the reference coding assigns after adjudication. Report the share of uncoded documents with at least one missed code, by group. In our case, 86 of 794 ads received no code, 78 of them from comparison roles.

## Run stability

Runs A and A′ of the theory-label test give a second, behavioral measure of uncertainty: the rate at which document-code decisions flip between identical runs. Compare it with the model's self-reported confidence. With three verbal levels the curve has only three segments; run stability allows a finer curve.

## Precision of the estimates (95% confidence, worst case p = 0.5)

| n | half-width |
|---|---|
| 27 (LOW) | ±19 percentage points |
| 50 (adjudicated cells) | ±14 |
| 100 (MEDIUM or HIGH) | ±10 |
