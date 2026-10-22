# 04 Coding

## Before the run

1. **Model.** Pick one model ID and use it for every run you want to compare. Record the exact ID.
2. **Cost.** Estimate with `tools/estimate_cost.py` (token means from a pilot, current prices from the provider's price list). Our first run of 794 documents cost about USD 50 including repeated calls.
3. **Dry run.** `tools/run_coding.py ... --dry-run 3` renders the full prompt for three documents without calling the API. Read them.
4. **Pipeline test.** `--mock-response examples/mock_response.json` runs parsing and checks without cost.
5. **Data protection.** Check the provider's terms for the use of submitted data and record what applied at the time of coding.

## The run

```bash
python tools/run_coding.py --corpus local/corpus.csv --id-col doc_id --text-col full_text \
  --system prompt/system.txt --user prompt/user.txt --codebook codebook.csv \
  --code-fields L1_Code,L2_Code --run-label A1 --model <model-id> --out-dir runs
```

The script sends one document per call and appends each raw response to `runs/raw_A1.jsonl` as soon as it arrives. An interrupted run resumes where it stopped. It retries once with a doubled token limit if a response stops at the limit, retries transient errors, and stops at once on structural errors (bad request, authentication, permission, unknown model).

## Output checks

| Check | Column in `segments_<run>.csv` | What to do |
|---|---|---|
| JSON parsing | status `parse_error` in `log_<run>.csv` | re-run these documents (`--rerun-unparsable`); never drop them silently |
| Codes outside the codebook | `codes_outside_codebook` | correct or discard, and count them |
| Segment not found verbatim in the document | `verbatim_in_document` = False | read the passage; paraphrased or invented quotes are a known failure |
| Failures by group | column `group` in `log_<run>.csv` (`--group-col`) | compare failure rates across groups before any comparison |

Failures are rarely random. In our first run, 88 of 794 responses came back malformed or truncated, 86 of them from the longer documents of one group. Dropping them would have biased every comparison between groups.

## Keep

`raw_<run>.jsonl`, `segments_<run>.csv`, `log_<run>.csv` and `run_info_<run>.json` (model, prompt hash, settings, start time). Share them with the results.
