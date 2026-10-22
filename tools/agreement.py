"""Agreement statistics and the theory-label decision rule.

Subcommands

  matrix   turn a segments file into a document x code 0/1 matrix
  compare  compare runs A, A' and B code by code and apply the preregistered decision rule

Statistics per code
  prevalence       share of documents with the code
  Cohen's kappa    (p_o - p_e) / (1 - p_e) for two binary ratings
  PABAK            2 * p_o - 1 (prevalence- and bias-adjusted kappa)
  bootstrap        percentile intervals from resampling documents with replacement

Decision rule (thresholds read from a JSON file, see case/preregistration/thresholds.json)
  A code shows a label effect if BOTH hold:
  (1) kappa(A, A') - kappa(A, B) > kappa_drop, and the bootstrap interval of this
      difference excludes zero;
  (2) the prevalence difference B - A lies outside the bootstrap interval of the
      prevalence difference A' - A (the noise band).
  The substantive conclusion holds if, for every code whose gap between two document
  groups is at least gap_min in run A, the gap has the same sign in run B.

Examples
  python tools/agreement.py matrix --segments runs/segments_A1.csv --codebook codebook/case/codebook_A_original.csv \
      --index case/data/ads_index.csv --out runs/A1_matrix.csv
  python tools/agreement.py compare --a runs/A1_matrix.csv --a2 runs/A2_matrix.csv --b runs/B1_matrix.csv \
      --thresholds case/preregistration/thresholds.json --groups case/data/ads_index.csv --group-col role \
      --group-a "AI Manager,Head of AI,Chief AI Officer,AI Lead" --out results/theory_label_test.csv
"""
import argparse
import json
import re

import numpy as np
import pandas as pd

NONE_VALUES = {"", "none", "nan", "null"}


def split_codes(value):
    return [c.strip() for c in re.split(r"[;,]", str(value)) if c.strip() and c.strip().lower() not in NONE_VALUES]


def to_matrix(segments, codes, doc_col="ad_id", code_cols=None, mapping=None, docs=None, prefix_map=None):
    if code_cols is None:
        code_cols = [c for c in segments.columns if c.lower().endswith("_code") and not c.lower().startswith("inductive")]
    docs = list(docs) if docs is not None else sorted(segments[doc_col].astype(str).unique())
    m = pd.DataFrame(0, index=pd.Index(docs, name="doc_id"), columns=codes)
    for _, row in segments.iterrows():
        d = str(row[doc_col])
        if d not in m.index:
            continue
        for col in code_cols:
            for c in split_codes(row[col]):
                c = mapping.get(c, c) if mapping else c
                if prefix_map and c.startswith(prefix_map[0]):
                    c = prefix_map[1] + c[len(prefix_map[0]):]
                if c in m.columns:
                    m.at[d, c] = 1
    return m


def kappa(x, y):
    x, y = np.asarray(x, int), np.asarray(y, int)
    po = np.mean(x == y)
    px, py = x.mean(), y.mean()
    pe = px * py + (1 - px) * (1 - py)
    return np.nan if pe >= 1 else (po - pe) / (1 - pe)


def pabak(x, y):
    return 2 * np.mean(np.asarray(x) == np.asarray(y)) - 1


def percent_agreement(x, y):
    return float(np.mean(np.asarray(x) == np.asarray(y)))


def cmd_matrix(a):
    seg = pd.read_csv(a.segments)
    codes = pd.read_csv(a.codebook)["code"].astype(str).tolist()
    mapping = json.load(open(a.mapping))[a.map_direction] if a.mapping else None
    docs = pd.read_csv(a.index)[a.index_id_col].astype(str) if a.index else None
    pm = tuple(a.rename_prefix.split(":")) if a.rename_prefix else None
    m = to_matrix(seg, codes, doc_col=a.doc_col, mapping=mapping, docs=docs, prefix_map=pm)
    m.to_csv(a.out)
    print(f"matrix {m.shape[0]} documents x {m.shape[1]} codes -> {a.out}")


def cmd_compare(a):
    th = json.load(open(a.thresholds))
    A, A2, B = (pd.read_csv(p, index_col=0) for p in (a.a, a.a2, a.b))
    rows = A.index.intersection(A2.index).intersection(B.index)
    cols = A.columns.intersection(A2.columns).intersection(B.columns)
    A, A2, B = (m.loc[rows, cols].astype(int).values for m in (A, A2, B))
    n = len(rows)
    rng = np.random.default_rng(th.get("seed", 20261101))
    nb = int(th.get("n_boot", 2000))
    lo_q, hi_q = (1 - th.get("ci_level", 0.95)) / 2, 1 - (1 - th.get("ci_level", 0.95)) / 2
    boots = rng.integers(0, n, size=(nb, n))

    groups = None
    if a.groups:
        g = pd.read_csv(a.groups).set_index(a.group_id_col)[a.group_col].astype(str)
        g = g.reindex(rows.astype(str))
        in_a = set(s.strip() for s in a.group_a.split(","))
        groups = g.isin(in_a).values

    out = []
    for j, code in enumerate(cols):
        a_, a2_, b_ = A[:, j], A2[:, j], B[:, j]
        k_aa2, k_ab = kappa(a_, a2_), kappa(a_, b_)
        d_k = k_aa2 - k_ab
        d_prev_b = b_.mean() - a_.mean()
        bk, bp = [], []
        for idx in boots:
            bk.append(kappa(a_[idx], a2_[idx]) - kappa(a_[idx], b_[idx]))
            bp.append(a2_[idx].mean() - a_[idx].mean())
        bk, bp = np.array(bk), np.array(bp)
        k_lo, k_hi = np.nanquantile(bk, [lo_q, hi_q])
        n_lo, n_hi = np.quantile(bp, [lo_q, hi_q])
        crit1 = (d_k > th["kappa_drop"]) and (k_lo > 0)
        crit2 = (d_prev_b < n_lo) or (d_prev_b > n_hi)
        row = {"code": code, "prev_A": a_.mean(), "prev_A2": a2_.mean(), "prev_B": b_.mean(),
               "kappa_A_A2": k_aa2, "kappa_A_B": k_ab, "pabak_A_A2": pabak(a_, a2_), "pabak_A_B": pabak(a_, b_),
               "kappa_drop": d_k, "kappa_drop_lo": k_lo, "kappa_drop_hi": k_hi,
               "prev_diff_B_A": d_prev_b, "noise_band_lo": n_lo, "noise_band_hi": n_hi,
               "label_effect": bool(crit1 and crit2)}
        if groups is not None:
            gap_a = a_[groups].mean() - a_[~groups].mean()
            gap_b = b_[groups].mean() - b_[~groups].mean()
            row.update({"gap_A": gap_a, "gap_B": gap_b,
                        "gap_checked": abs(gap_a) >= th["gap_min"],
                        "gap_sign_kept": bool(np.sign(gap_a) == np.sign(gap_b))})
        out.append(row)
    res = pd.DataFrame(out)
    res.to_csv(a.out, index=False)
    print(f"{n} documents, {len(cols)} codes; label effect in {int(res.label_effect.sum())} codes")
    if groups is not None:
        checked = res[res.gap_checked]
        holds = bool(checked.gap_sign_kept.all()) if len(checked) else True
        print(f"substantive conclusion holds in B: {holds} ({len(checked)} codes checked)")
    print(f"results -> {a.out}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("matrix")
    m.add_argument("--segments", required=True)
    m.add_argument("--codebook", required=True, help="CSV with column 'code' (defines the matrix columns)")
    m.add_argument("--doc-col", default="ad_id")
    m.add_argument("--mapping", help="code mapping JSON, e.g. prompts/case/code_mapping.json for run B")
    m.add_argument("--map-direction", default="to_A")
    m.add_argument("--rename-prefix", help="OLD:NEW, e.g. GD:GT, if files use another code prefix than the codebook")
    m.add_argument("--index", help="optional document index so that documents without codes become zero rows")
    m.add_argument("--index-id-col", default="ad_id")
    m.add_argument("--out", required=True)
    m.set_defaults(func=cmd_matrix)
    c = sub.add_parser("compare")
    c.add_argument("--a", required=True)
    c.add_argument("--a2", required=True)
    c.add_argument("--b", required=True)
    c.add_argument("--thresholds", required=True)
    c.add_argument("--groups", help="CSV with document groups for the substantive check")
    c.add_argument("--group-id-col", default="ad_id")
    c.add_argument("--group-col", default="role")
    c.add_argument("--group-a", default="AI Manager,Head of AI,Chief AI Officer,AI Lead",
                   help="comma-separated values that form the first group; all other documents form the second")
    c.add_argument("--out", required=True)
    c.set_defaults(func=cmd_compare)
    a = p.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
