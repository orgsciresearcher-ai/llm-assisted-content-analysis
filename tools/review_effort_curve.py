"""Review-effort curve: expected percent agreement of a coded dataset as a function of
the share of segments that researchers review, lowest model confidence first.

Definitions (see guide/07_calibration_and_curve.md and the technical appendix)
  unit         one segment; it agrees only if its full set of codes matches the reference
  p_l          percent agreement between model and reference coding in confidence level l
  h            percent agreement between the two human coders before adjudication
               (per level, or pooled with --pooled-human)
  w_l          share of level l among all coded segments
  order        levels are reviewed from lowest to highest confidence, in random order within a level
  s            share of all segments reviewed, 0 <= s <= 1
  r_l(s)       reviewed fraction of level l = clip((s - W_{l-1}) / w_l, 0, 1), W = cumulative shares
  curve        PA(s) = sum_l w_l * [ r_l(s) * h_l + (1 - r_l(s)) * p_l ]
Random order within a level makes PA(s) linear inside each level, so the expected curve is
piecewise linear. The smallest s with PA(s) >= target is the review share to plan for.

Modes
  params  illustrative or planning curve from assumed values
          python tools/review_effort_curve.py params --levels "LOW:0.004:0.60,MEDIUM:0.231:0.80,HIGH:0.765:0.85" \
              --human 0.97 --target 0.90 --out curve.csv --plot curve.png
  data    curve from adjudicated blind-coding sheets, with a bootstrap band
          python tools/review_effort_curve.py data --coded adjudicated.csv \
              --sample case/samples/calibration_test_sample.csv --shares "LOW:0.004,MEDIUM:0.231,HIGH:0.765" \
              --target 0.90 --out curve.csv --plot curve.png
          adjudicated.csv needs: seg_id, model_codes, coder1_codes, coder2_codes, reference_codes
          (codes separated by ';'; empty or NONE = no code). Strata such as MEDIUM_contextual are
          pooled into their level (text before '_') with population weights from the sample file.
"""
import argparse
import re

import numpy as np
import pandas as pd

NONE_VALUES = {"", "none", "nan", "null"}


def codeset(v):
    return frozenset(c.strip().upper() for c in re.split(r"[;,]", str(v)) if c.strip() and c.strip().lower() not in NONE_VALUES)


def curve(levels, s_grid):
    """levels: list of dicts with name, w, p, h (in review order)."""
    w = np.array([l["w"] for l in levels], float)
    w = w / w.sum()
    cum = np.concatenate([[0], np.cumsum(w)])
    out = np.zeros_like(s_grid, dtype=float)
    for i, l in enumerate(levels):
        r = np.clip((s_grid - cum[i]) / w[i], 0, 1) if w[i] > 0 else np.ones_like(s_grid)
        out += w[i] * (r * l["h"] + (1 - r) * l["p"])
    return out


def crossing(s_grid, pa, target):
    hit = np.where(pa >= target - 1e-12)[0]
    return float(s_grid[hit[0]]) if len(hit) else np.nan


def parse_pairs(text, n):
    out = []
    for part in text.split(","):
        bits = part.split(":")
        if len(bits) != n:
            raise SystemExit(f"cannot parse '{part}'")
        out.append([bits[0]] + [float(b) for b in bits[1:]])
    return out


def level_stats(df, pooled_human):
    """percent agreement per level, weighting strata by population size."""
    res = {}
    h_all = (df.c1 == df.c2).mean()
    for lvl, g in df.groupby("level", sort=False):
        num_p = num_h = den = 0.0
        for _, s in g.groupby("stratum"):
            wpop = s["population_size"].iloc[0]
            num_p += wpop * (s.model == s.ref).mean()
            num_h += wpop * (s.c1 == s.c2).mean()
            den += wpop
        res[lvl] = {"p": num_p / den, "h": h_all if pooled_human else num_h / den, "n": len(g)}
    return res


def cmd_params(a):
    levels = [{"name": n, "w": w, "p": p, "h": a.human} for n, w, p in parse_pairs(a.levels, 3)]
    s = np.round(np.linspace(0, 1, 1001), 3)
    pa = curve(levels, s)
    pd.DataFrame({"share_reviewed": s, "expected_percent_agreement": pa}).to_csv(a.out, index=False)
    print(f"review share needed for {a.target:.0%}: {crossing(s, pa, a.target):.1%}")
    if a.plot:
        plot(s, pa, None, a.target, a.plot)


def cmd_data(a):
    coded = pd.read_csv(a.coded)
    sample = pd.read_csv(a.sample)[["seg_id", "stratum", "population_size"]]
    df = coded.merge(sample, on="seg_id", how="inner")
    if len(df) < len(coded):
        print(f"warning: {len(coded) - len(df)} coded rows not found in the sample file")
    df["model"] = df["model_codes"].map(codeset)
    df["c1"] = df["coder1_codes"].map(codeset)
    df["c2"] = df["coder2_codes"].map(codeset)
    df["ref"] = df["reference_codes"].map(codeset)
    df["level"] = df["stratum"].astype(str).str.split("_").str[0]
    shares = {n: w for n, w in parse_pairs(a.shares, 2)}
    order = [n for n, _ in parse_pairs(a.shares, 2)]
    st = level_stats(df, a.pooled_human)
    for lvl in order:
        print(f"{lvl:8s} n={st[lvl]['n']:4d}  model-reference {st[lvl]['p']:.3f}  coder-coder {st[lvl]['h']:.3f}")
    levels = [{"name": l, "w": shares[l], "p": st[l]["p"], "h": st[l]["h"]} for l in order]
    s = np.round(np.linspace(0, 1, 1001), 3)
    pa = curve(levels, s)
    rng = np.random.default_rng(a.seed)
    boot = []
    for _ in range(a.n_boot):
        parts = [g.sample(len(g), replace=True, random_state=int(rng.integers(1 << 31))) for _, g in df.groupby("stratum")]
        st_b = level_stats(pd.concat(parts), a.pooled_human)
        boot.append(curve([{"name": l, "w": shares[l], "p": st_b[l]["p"], "h": st_b[l]["h"]} for l in order], s))
    boot = np.array(boot)
    lo, hi = np.quantile(boot, [0.025, 0.975], axis=0)
    pd.DataFrame({"share_reviewed": s, "expected_percent_agreement": pa, "lower_95": lo, "upper_95": hi}).to_csv(a.out, index=False)
    cr = [crossing(s, b, a.target) for b in boot]
    print(f"review share needed for {a.target:.0%}: {crossing(s, pa, a.target):.1%} "
          f"(bootstrap 95% interval {np.nanquantile(cr, 0.025):.1%} to {np.nanquantile(cr, 0.975):.1%})")
    if a.plot:
        plot(s, pa, (lo, hi), a.target, a.plot)


def plot(s, pa, band, target, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(6.3, 4.0), dpi=200)
    if band is not None:
        ax.fill_between(s * 100, band[0] * 100, band[1] * 100, color="#9FB8CC", alpha=0.35, linewidth=0)
    ax.plot(s * 100, pa * 100, color="#3979A8", linewidth=2)
    ax.axhline(target * 100, color="#555555", linestyle=(0, (4, 3)), linewidth=0.9)
    x = crossing(s, pa, target)
    if not np.isnan(x):
        ax.axvline(x * 100, color="#3979A8", linestyle=":", linewidth=0.9)
    ax.set_xlabel("Share of segments reviewed, lowest model confidence first (%)")
    ax.set_ylabel("Expected percent agreement with the reference coding (%)")
    ax.set_xlim(0, 100)
    ax.grid(True, color="#e9e8e4", linewidth=0.6)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    fig.tight_layout()
    fig.savefig(path)
    print(f"plot -> {path}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    q = sub.add_parser("params")
    q.add_argument("--levels", required=True, help="name:share:percent_agreement, in review order")
    q.add_argument("--human", type=float, required=True, help="coder-coder percent agreement before adjudication")
    q.add_argument("--target", type=float, default=0.90)
    q.add_argument("--out", required=True)
    q.add_argument("--plot")
    q.set_defaults(func=cmd_params)
    d = sub.add_parser("data")
    d.add_argument("--coded", required=True)
    d.add_argument("--sample", required=True, help="sample file from draw_samples.py (stratum, population_size)")
    d.add_argument("--shares", required=True, help="name:share in review order, e.g. LOW:0.004,MEDIUM:0.231,HIGH:0.765")
    d.add_argument("--pooled-human", action="store_true", help="use one pooled coder-coder agreement for all levels")
    d.add_argument("--target", type=float, default=0.90)
    d.add_argument("--n-boot", type=int, default=2000)
    d.add_argument("--seed", type=int, default=20261101)
    d.add_argument("--out", required=True)
    d.add_argument("--plot")
    d.set_defaults(func=cmd_data)
    a = p.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
