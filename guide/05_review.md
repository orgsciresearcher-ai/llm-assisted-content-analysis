# 05 Human review

## What to review

- every segment the model marks LOW, and as many further segments as the review-effort curve requires for your target (`07_calibration_and_curve.md`)
- every flagged output (codes outside the codebook, non-verbatim segments)
- every inductive suggestion
- use the error typology (`06` and `07`) as a checklist: over-extraction from context, definition stretching, cue-word coding, theory filling

Record each change in the data, for example as "Edit: ..." appended to the rationale, so the reviewed dataset documents itself. Our case shares the coded segments with these notes (`case/data/coded_segments.csv`).

## Inductive suggestions

With one document per call, the model cannot check whether a pattern recurs across documents, so it tends to coin a new label for every passage. In our first run it proposed 117 distinct labels for 118 segments. Treat suggestions as raw material:

1. Pool all suggestions across documents (`case/data/inductive_suggestions.csv` shows the format).
2. Group them by meaning, not by wording.
3. Apply written criteria before adding a code: it recurs across documents, it is distinct from existing codes, and it matters for the research question.
4. If a new code enters the codebook, re-code all documents, not only those where it was suggested.

## Use the templates

`templates/blind_coding_sheet.xlsx` and `templates/adjudication_sheet.xlsx` give the column layout; `tools/make_blind_sheets.py` fills them from a sample.
