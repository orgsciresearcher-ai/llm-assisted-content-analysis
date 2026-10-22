# Decision points

Decisions that stay with researchers, with defensible options. Record which option you chose and why.

| Decision | Options | Consider | Our case |
|---|---|---|---|
| Unit of coding | segments (passages) / whole documents | segments make errors traceable and allow segment-level validation; documents are cheaper and match document-level analysis | segments, aggregated to documents for analysis |
| Documents per call | one / several | one keeps calls independent and outputs traceable; several let the model compare, which helps inductive work but couples errors | one |
| Theory in the prompt | named / de-labeled | named may help the model, but may pull coding toward expectations; test it (`06`) | named in A, removed in B |
| Worked examples | none / from calibration documents / from documents outside every validation sample | examples help format and borderline cases; they must not overlap with validation samples | three worked examples |
| Confidence | verbal levels / run stability / both | verbal is free but may record rules; stability costs repeated runs | verbal in the first run; run stability in Phase 2 |
| Temperature | set / not set | some models reject the parameter; report test-retest stability either way | not set |
| Review rule | all / random sample / by confidence / by run stability | depends on the review-effort curve | decided after the calibration test |
| Target agreement | e.g. 80%, 90% | conventions in content analysis; Lombard et al. (2002) consider .90 or greater nearly always acceptable | 90% |
| Unit of agreement | segment-code cell / full code set per segment / document | cells inflate agreement through absent codes | full code set per segment |
| Inductive codes | not allowed / suggested by the model, decided by researchers | one document per call cannot detect recurrence | suggestions pooled and decided by written criteria |
| Model | proprietary / open-weights | cost, access, data terms, archiving; keep prompts in plain text so you can switch | one current proprietary model for all Phase 1 runs |
| Data sharing | full texts / IDs, links, hashes and coded segments | platform terms, personal data | IDs, links, hashes, coded segments, raw outputs |
