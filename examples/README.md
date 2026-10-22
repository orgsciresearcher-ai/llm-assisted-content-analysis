# Examples for testing

- `demo_corpus.csv`: three fictional job ads (invented text, invented companies) with the columns `doc_id`, `role`, `language`, `full_text`.
- `mock_response.json`: a stored model response. With `--mock-response`, `tools/run_coding.py` runs parsing and all output checks without an API call. One code in it (GT9.9) is not in the codebook, and because the same stored response is returned for every document, the segments are flagged as not verbatim for the other two documents. Both show the checks at work.

```bash
python tools/run_coding.py --corpus examples/demo_corpus.csv --id-col doc_id --text-col full_text \
  --system prompts/case/A_system.txt --user prompts/case/A_user.txt --field ad_id=doc_id --field role_family=role \
  --codebook codebook/case/codebook_A_original.csv --run-label demo --model MODEL_ID \
  --mock-response examples/mock_response.json --out-dir runs
```
