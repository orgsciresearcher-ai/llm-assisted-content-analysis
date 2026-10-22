"""Draw the validation samples with fixed seeds.

Four samples, one subcommand each:

  calibration   stratified sample of coded segments by model confidence
                (confidence-calibration test, guide/07_calibration_and_curve.md)
  adjudication  random ad-code cells where runs A and A' agree and run B departs
                (theory-label test, guide/06_theory_label_test.md)
  documents     random sample of documents for document-level blind coding
  uncoded       all documents to which the model assigned no code (recall check)

The output lists IDs and strata only. It never contains model codes, confidence,
or rationales, so coders can open it without seeing what the model decided.

Examples
  python tools/draw_samples.py calibration --segments case/data/coded_segments.csv \
      --exclude-ads case/data/calibration_ads.csv --out case/samples/calibration_test_sample.csv
  python tools/draw_samples.py adjudication --run-a runs/A1_matrix.csv --run-a2 runs/A2_matrix.csv \
      --run-b runs/B1_matrix.csv --n 50 --out samples/adjudication_cells.csv
  python tools/draw_samples.py documents --index case/data/ads_index.csv --share 0.10 --out samples/documents.csv
  python tools/draw_samples.py uncoded --segments case/data/coded_segments.csv --index case/data/ads_index.csv \
      --out case/samples/recall_check_uncoded_ads.csv
"""
import argparse
import re
import sys

import numpy as np
import pandas as pd

DEFAULT_SEED = 20261101
NONE_VALUES = {"", "none", "nan", "null"}


def is_coded(row, code_cols):
    return any(str(row[c]).strip().lower() not in NONE_VALUES for c in code_cols)


def cmd_calibration(a):
    seg = pd.read_csv(a.segments)
    code_cols = [c for c in seg.columns if c.lower().endswith("_code") and not c.lower().startswith("inductive")]
    seg = seg[seg.apply(is_coded, axis=1, code_cols=code_cols)].copy()
    if a.exclude_ads:
        excl = set(pd.read_csv(a.exclude_ads)["ad_id"].astype(str))
        seg = seg[~seg["ad_id"].astype(str).isin(excl)]
    conf = seg["confidence"].astype(str).str.upper().str.strip()
    contextual = seg["rationale"].astype(str).str.contains(a.contextual_pattern, flags=re.I, regex=True)
    seg["stratum"] = np.select(
        [conf.eq("LOW"), conf.eq("MEDIUM") & contextual, conf.eq("MEDIUM"), conf.eq("HIGH")],
        ["LOW", "MEDIUM_contextual", "MEDIUM_lexical", "HIGH"], default="OTHER")
    plan = {"LOW": a.n_low, "MEDIUM_contextual": a.n_medium_contextual,
            "MEDIUM_lexical": a.n_medium_lexical, "HIGH": a.n_high}
    rng = np.random.default_rng(a.seed)
    parts = []
    for stratum, n in plan.items():
        pop = seg[seg["stratum"] == stratum]
        take = len(pop) if n is None or n < 0 or n >= len(pop) else n
        idx = rng.choice(len(pop), size=take, replace=False)
        part = pop.iloc[np.sort(idx)][["seg_id", "ad_id", "stratum"]].copy()
        part["population_size"] = len(pop)
        part["sample_size"] = take
        part["inclusion_probability"] = take / len(pop) if len(pop) else np.nan
        parts.append(part)
        print(f"{stratum:20s} population {len(pop):5d}  sample {take:4d}")
    out = pd.concat(parts, ignore_index=True)
    out["seed"] = a.seed
    out.to_csv(a.out, index=False)
    print(f"wrote {len(out)} segments to {a.out}")


def cmd_adjudication(a):
    A, A2, B = (pd.read_csv(p, index_col=0) for p in (a.run_a, a.run_a2, a.run_b))
    common_rows = A.index.intersection(A2.index).intersection(B.index)
    common_cols = A.columns.intersection(A2.columns).intersection(B.columns)
    A, A2, B = (m.loc[common_rows, common_cols].astype(int) for m in (A, A2, B))
    mask = (A == A2) & (B != A)
    rows, cols = np.where(mask.values)
    cells = [(A.index[r], A.columns[c], int(A.iat[r, c]), int(B.iat[r, c])) for r, c in zip(rows, cols)]
    if not cells:
        sys.exit("no cells where A and A' agree and B departs")
    rng = np.random.default_rng(a.seed)
    take = min(a.n, len(cells))
    pick = rng.choice(len(cells), size=take, replace=False)
    out = pd.DataFrame([cells[i] for i in sorted(pick)], columns=["doc_id", "code", "code_in_A", "code_in_B"])
    out["population_size"] = len(cells)
    out["seed"] = a.seed
    # the blind sheet must not show which run assigned the code; keep these columns out of coder files
    out.to_csv(a.out, index=False)
    print(f"{len(cells)} eligible cells, drew {take} -> {a.out}")


def cmd_documents(a):
    idx = pd.read_csv(a.index)
    id_col = a.id_col
    rng = np.random.default_rng(a.seed)
    if a.stratify_by:
        share = a.share if a.n is None else a.n / len(idx)
        parts = []
        for _, grp in idx.groupby(a.stratify_by):
            n = min(len(grp), max(1, int(round(len(grp) * share))))
            parts.append(grp.iloc[np.sort(rng.choice(len(grp), size=n, replace=False))])
        out = pd.concat(parts)
    else:
        n = a.n if a.n is not None else int(round(len(idx) * a.share))
        out = idx.iloc[np.sort(rng.choice(len(idx), size=n, replace=False))]
    out = out[[id_col] + ([a.stratify_by] if a.stratify_by else [])].copy()
    out["seed"] = a.seed
    out.to_csv(a.out, index=False)
    print(f"drew {len(out)} of {len(idx)} documents -> {a.out}")


def cmd_uncoded(a):
    seg = pd.read_csv(a.segments)
    code_cols = [c for c in seg.columns if c.lower().endswith("_code") and not c.lower().startswith("inductive")]
    coded = set(seg[seg.apply(is_coded, axis=1, code_cols=code_cols)][a.id_col].astype(str))
    idx = pd.read_csv(a.index)
    out = idx[~idx[a.id_col].astype(str).isin(coded)]
    keep = [a.id_col] + [c for c in ("role",) if c in out.columns]
    out = out[keep].copy()
    out.to_csv(a.out, index=False)
    by = out["role"].value_counts().to_dict() if "role" in out.columns else {}
    print(f"{len(out)} of {len(idx)} documents without any code -> {a.out} {by}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("calibration")
    c.add_argument("--segments", required=True, help="coded segments CSV (seg_id, ad_id, *_code, confidence, rationale)")
    c.add_argument("--exclude-ads", help="CSV with column ad_id, e.g. the calibration ads")
    c.add_argument("--contextual-pattern", default=r"contextual",
                   help="regex on the rationale that marks MEDIUM segments coded via the context rule")
    c.add_argument("--n-low", type=int, default=-1, help="-1 = all LOW segments")
    c.add_argument("--n-medium-contextual", type=int, default=50)
    c.add_argument("--n-medium-lexical", type=int, default=50)
    c.add_argument("--n-high", type=int, default=100)
    c.add_argument("--seed", type=int, default=DEFAULT_SEED)
    c.add_argument("--out", required=True)
    c.set_defaults(func=cmd_calibration)

    d = sub.add_parser("adjudication")
    d.add_argument("--run-a", required=True, help="document x code 0/1 matrix of run A (first column = doc id)")
    d.add_argument("--run-a2", required=True, help="matrix of the repeated run A'")
    d.add_argument("--run-b", required=True, help="matrix of the de-labeled run B")
    d.add_argument("--n", type=int, default=50)
    d.add_argument("--seed", type=int, default=DEFAULT_SEED)
    d.add_argument("--out", required=True)
    d.set_defaults(func=cmd_adjudication)

    e = sub.add_parser("documents")
    e.add_argument("--index", required=True, help="CSV with one row per document")
    e.add_argument("--id-col", default="ad_id")
    e.add_argument("--share", type=float, default=0.10)
    e.add_argument("--n", type=int, default=None)
    e.add_argument("--stratify-by", default=None, help="optional column, e.g. role")
    e.add_argument("--seed", type=int, default=DEFAULT_SEED)
    e.add_argument("--out", required=True)
    e.set_defaults(func=cmd_documents)

    u = sub.add_parser("uncoded")
    u.add_argument("--segments", required=True, help="coded segments CSV of the run")
    u.add_argument("--index", required=True, help="CSV with one row per document")
    u.add_argument("--id-col", default="ad_id")
    u.add_argument("--out", required=True)
    u.set_defaults(func=cmd_uncoded)

    a = p.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
