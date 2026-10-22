# 01 Corpus

The coding can only be as good as the corpus. Errors in the corpus pass every automated check and reach the LLM, which codes broken input without objection. Check the corpus before coding.

## Build

- Define the population first (document type, period, languages, sources) and write the search strategy down, including synonym lists for unstandardized titles or terms.
- Give every document a stable ID and keep a provenance record: source, URL, retrieval date, the query that found it.
- Keep full texts locally if platform terms prohibit redistribution. Share IDs, links and a content hash instead (`case/data/ads_index.csv` shows the format).

## Integrity checks before coding

Run these checks per source, because each source fails differently.

| Check | Why | How |
|---|---|---|
| Duplicates and near-duplicates | reposts and aggregators inflate groups | exact hash of normalized text, then word-shingle overlap (we flag overlap of 0.9 or more) |
| Truncated or summary texts | some platforms return short machine summaries instead of the full document | minimum length per source, plus a manual look at the shortest documents |
| Category labels | a label taken from the search query instead of the document misassigns documents | compare the assigned category with the title in the document on a sample |
| Language | mixed languages affect prompts and coders | detect language, decide which languages the codebook covers |
| Completeness per group | uneven losses bias group comparisons | count documents per group after each cleaning step |

Two lessons from our case. In an earlier version of a retrieval pipeline, a large share of documents carried the category of the search query instead of the category of the document itself, and many documents held platform-generated summaries instead of full postings. Every automated check passed. Only reading samples revealed the problems.

## Record

Document each cleaning step with counts (collected, removed by reason, retained per group). Reviewers will ask how the analysis base came about.
