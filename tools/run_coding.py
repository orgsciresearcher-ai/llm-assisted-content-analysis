"""Code a corpus with an LLM, one document per API call, and archive every raw response.

One pipeline serves all conditions (A, A', B): only the prompt files differ.

What the script does
  - fills the user prompt template with each document's fields and sends one request per document
  - appends the raw response, stop reason and token counts to raw_<run>.jsonl (the run can resume)
  - retries once with a doubled token limit if a response stops at max_tokens
  - with --rerun-unparsable, sends documents again whose archived response is not valid JSON
    (earlier attempts stay in the archive; parsing uses the last attempt per document)
  - stops at once on structural API errors (400, 401, 403, 404) and retries transient ones
  - parses the JSON array, assigns deterministic segment IDs, maps de-labeled codes back if a
    mapping is given, flags codes outside the codebook, and checks that each quoted segment
    appears verbatim in the document
  - writes segments_<run>.csv, log_<run>.csv and run_info_<run>.json (model, prompt hash, settings),
    and with --group-col reports failures by group (e.g. role), because failures are rarely random

No temperature is sent unless you pass --temperature, because some current models reject it.
Report test-retest stability across repeated runs instead (guide/08_reporting.md).

Examples
  # render prompts only, no API call
  python tools/run_coding.py --corpus examples/demo_corpus.csv --id-col doc_id --text-col full_text \
      --system prompts/case/A_system.txt --user prompts/case/A_user.txt \
      --field ad_id=doc_id --field role_family=role --field language=language --field full_text=full_text \
      --codebook codebook/case/codebook_A_original.csv --run-label A1 --model MODEL_ID --dry-run 2

  # pipeline test with a stored response instead of the API
  ... --mock-response examples/mock_response.json

  # real run (needs: pip install anthropic, and ANTHROPIC_API_KEY in the environment or a .env file)
  ... --model <same model ID for A1, A2 and B1> --out-dir runs
"""
import argparse
import hashlib
import json
import os
import re
import string
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

NONE_VALUES = {"", "none", "nan", "null"}
STRUCTURAL = {400, 401, 403, 404}


def load_env(path=".env"):
    p = Path(path)
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def load_corpus(path, sheets=None):
    path = Path(path)
    if path.suffix.lower() in (".xlsx", ".xlsm"):
        xl = pd.ExcelFile(path)
        names = sheets or xl.sheet_names
        return pd.concat([xl.parse(s).assign(sheet=s) for s in names], ignore_index=True)
    return pd.read_csv(path)


def norm_ws(t):
    return re.sub(r"\s+", " ", str(t)).strip().casefold()


def split_codes(v):
    return [c.strip() for c in re.split(r"[;,]", str(v)) if c.strip() and c.strip().lower() not in NONE_VALUES]


def parse_json_array(raw):
    t = raw.strip()
    t = re.sub(r"^```(?:json)?\s*", "", t)
    t = re.sub(r"\s*```$", "", t)
    data = json.loads(t)
    return [data] if isinstance(data, dict) else data


def make_client(mock):
    if mock:
        payload = Path(mock).read_text(encoding="utf-8")

        class Mock:
            def call(self, model, system, user, max_tokens, temperature):
                return payload, "end_turn", len(user) // 4, len(payload) // 4
        return Mock()
    try:
        import anthropic
    except ImportError:
        sys.exit("pip install anthropic (see requirements.txt)")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY is not set (environment variable or .env file)")
    client = anthropic.Anthropic()

    class Live:
        def call(self, model, system, user, max_tokens, temperature):
            kwargs = dict(model=model, max_tokens=max_tokens, system=system,
                          messages=[{"role": "user", "content": user}])
            if temperature is not None:
                kwargs["temperature"] = temperature
            r = client.messages.create(**kwargs)
            text = "".join(getattr(b, "text", "") for b in r.content)
            return text, r.stop_reason, r.usage.input_tokens, r.usage.output_tokens
    return Live()


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--corpus", required=True, help="CSV or XLSX with one document per row")
    p.add_argument("--sheets", help="comma-separated sheet names for XLSX input (default: all)")
    p.add_argument("--id-col", required=True)
    p.add_argument("--text-col", required=True)
    p.add_argument("--min-chars", type=int, default=100, help="skip documents with shorter text")
    p.add_argument("--system", required=True, help="system prompt file")
    p.add_argument("--user", required=True, help="user prompt template ({placeholders}, literal braces doubled)")
    p.add_argument("--field", action="append", default=[],
                   help="placeholder=column, e.g. ad_id=doc_id; unmapped placeholders use the column of the same name")
    p.add_argument("--codebook", required=True, help="CSV with column 'code'")
    p.add_argument("--code-fields", default="GT_Code,SK_Code", help="JSON fields that hold codes")
    p.add_argument("--mapping", help="JSON with code mapping, e.g. prompts/case/code_mapping.json")
    p.add_argument("--map-direction", default="to_A")
    p.add_argument("--run-label", required=True)
    p.add_argument("--model", required=True, help="model ID; use the identical ID for all runs you compare")
    p.add_argument("--max-tokens", type=int, default=8000)
    p.add_argument("--temperature", type=float, default=None)
    p.add_argument("--delay", type=float, default=1.5, help="seconds between calls")
    p.add_argument("--out-dir", default="runs")
    p.add_argument("--dry-run", type=int, default=0, help="render prompts for the first N documents, no API call")
    p.add_argument("--mock-response", help="file whose content is returned instead of an API response")
    p.add_argument("--rerun-unparsable", action="store_true",
                   help="send documents again whose archived response cannot be parsed")
    p.add_argument("--group-col", help="corpus column for reporting failures by group, e.g. role")
    a = p.parse_args()
    load_env()

    system = Path(a.system).read_text(encoding="utf-8")
    template = Path(a.user).read_text(encoding="utf-8")
    prompt_hash = hashlib.sha256((system + "\n" + template).encode("utf-8")).hexdigest()[:12]
    fieldmap = dict(f.split("=", 1) for f in a.field)
    placeholders = {name for _, name, _, _ in string.Formatter().parse(template) if name}
    corpus = load_corpus(a.corpus, a.sheets.split(",") if a.sheets else None)
    for ph in placeholders:
        col = fieldmap.get(ph, ph)
        if col not in corpus.columns:
            sys.exit(f"placeholder {{{ph}}} has no column '{col}' (use --field {ph}=<column>)")
    corpus = corpus[corpus[a.text_col].astype(str).str.len() >= a.min_chars]
    codes_valid = set(pd.read_csv(a.codebook)["code"].astype(str))
    mapping = json.loads(Path(a.mapping).read_text())[a.map_direction] if a.mapping else {}
    code_fields = [c.strip() for c in a.code_fields.split(",")]

    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    if a.dry_run:
        for _, row in corpus.head(a.dry_run).iterrows():
            user = template.format(**{ph: row[fieldmap.get(ph, ph)] for ph in placeholders})
            f = out / f"dry_run_{a.run_label}_{row[a.id_col]}.txt"
            f.write_text(f"=== SYSTEM ===\n{system}\n\n=== USER ===\n{user}", encoding="utf-8")
            print(f"rendered {f}")
        return

    raw_path = out / f"raw_{a.run_label}.jsonl"
    done = set()
    if raw_path.exists():
        last = {}
        for line in raw_path.read_text(encoding="utf-8").splitlines():
            rec = json.loads(line)
            last[str(rec["doc_id"])] = rec
        for doc_id, rec in last.items():
            if rec.get("status") != "ok":
                continue
            if a.rerun_unparsable:
                try:
                    parse_json_array(rec["raw_response"])
                except Exception:  # noqa: BLE001
                    continue
            done.add(doc_id)
    client = make_client(a.mock_response)
    info = {"run_label": a.run_label, "model": a.model, "prompt_hash": prompt_hash, "max_tokens": a.max_tokens,
            "temperature": a.temperature, "corpus": Path(a.corpus).name, "n_documents": int(len(corpus)),
            "started_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "mock": bool(a.mock_response)}
    (out / f"run_info_{a.run_label}.json").write_text(json.dumps(info, indent=2), encoding="utf-8")

    with raw_path.open("a", encoding="utf-8") as fh:
        for i, (_, row) in enumerate(corpus.iterrows(), 1):
            doc_id = str(row[a.id_col])
            if doc_id in done:
                continue
            user = template.format(**{ph: row[fieldmap.get(ph, ph)] for ph in placeholders})
            rec = {"doc_id": doc_id, "run": a.run_label, "model": a.model, "prompt_hash": prompt_hash,
                   "time_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
            max_tokens, attempt = a.max_tokens, 0
            while True:
                attempt += 1
                try:
                    raw, stop, tin, tout = client.call(a.model, system, user, max_tokens, a.temperature)
                except Exception as e:  # noqa: BLE001
                    status = getattr(e, "status_code", None)
                    if status in STRUCTURAL:
                        sys.exit(f"structural API error {status} at {doc_id}: {e}")
                    if attempt < 4:
                        time.sleep(5 * attempt)
                        continue
                    rec.update(status="error", error=str(e)[:500])
                    break
                if stop == "max_tokens" and attempt == 1:
                    max_tokens *= 2
                    continue
                rec.update(status="ok", stop_reason=stop, input_tokens=tin, output_tokens=tout,
                           max_tokens=max_tokens, raw_response=raw)
                break
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            print(f"[{i}/{len(corpus)}] {doc_id}: {rec['status']}")
            if not a.mock_response:
                time.sleep(a.delay)

    # parse all archived responses
    texts = dict(zip(corpus[a.id_col].astype(str), corpus[a.text_col].astype(str)))
    groups = dict(zip(corpus[a.id_col].astype(str), corpus[a.group_col].astype(str))) if a.group_col else {}
    last, attempts = {}, {}
    for line in raw_path.read_text(encoding="utf-8").splitlines():
        rec = json.loads(line)
        d = str(rec["doc_id"])
        last[d] = rec
        attempts[d] = attempts.get(d, 0) + 1
    seg_rows, log_rows = [], []
    for d, rec in last.items():
        log = {k: rec.get(k) for k in ("doc_id", "status", "stop_reason", "input_tokens", "output_tokens", "error")}
        log["attempts"] = attempts[d]
        if a.group_col:
            log["group"] = groups.get(d)
        if rec.get("status") != "ok":
            log_rows.append(log)
            continue
        try:
            items = parse_json_array(rec["raw_response"])
        except Exception as e:  # noqa: BLE001
            log.update(status="parse_error", error=str(e)[:300])
            log_rows.append(log)
            continue
        doc_text = norm_ws(texts.get(rec["doc_id"], ""))
        for k, it in enumerate(items, 1):
            row = {"seg_id": f"{rec['doc_id']}_S{k:02d}", "doc_id": rec["doc_id"], "run": rec["run"],
                   "model_seg_id": it.get("Seg_ID"), "text_segment": it.get("Text_Segment"),
                   "inductive_code": it.get("Inductive_Code"), "confidence": it.get("Confidence"),
                   "rationale": it.get("Rationale")}
            outside = []
            for f in code_fields:
                raw_codes = split_codes(it.get(f, ""))
                mapped = [mapping.get(c, c) for c in raw_codes]
                row[f"raw_{f}"] = ";".join(raw_codes)
                row[f] = ";".join(mapped) if mapped else "NONE"
                outside += [c for c in mapped if c not in codes_valid]
            row["codes_outside_codebook"] = ";".join(outside)
            seg = it.get("Text_Segment")
            row["verbatim_in_document"] = (norm_ws(seg) in doc_text) if seg else None
            seg_rows.append(row)
        log["segments"] = len(items)
        log_rows.append(log)
    pd.DataFrame(seg_rows).to_csv(out / f"segments_{a.run_label}.csv", index=False)
    lg = pd.DataFrame(log_rows)
    lg.to_csv(out / f"log_{a.run_label}.csv", index=False)
    s = pd.DataFrame(seg_rows)
    print(f"documents {len(lg)}, ok {int((lg.status == 'ok').sum())}, segments {len(s)}, "
          f"codes outside codebook {int((s.get('codes_outside_codebook', pd.Series(dtype=str)) != '').sum()) if len(s) else 0}, "
          f"non-verbatim segments {int((s.get('verbatim_in_document') == False).sum()) if len(s) else 0}")  # noqa: E712
    if a.group_col and len(lg):
        fail = lg.assign(failed=lg.status != "ok").groupby("group")["failed"].agg(["sum", "count"])
        print("failed documents by group:")
        for g, r in fail.iterrows():
            print(f"  {g}: {int(r['sum'])} of {int(r['count'])}")


if __name__ == "__main__":
    main()
