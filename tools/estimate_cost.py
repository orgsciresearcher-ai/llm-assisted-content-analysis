"""Estimate API cost before a coding run.

Two ways, use both and compare:

  tokens     documents x runs x (mean input tokens x input price + mean output tokens x output price),
             plus a surcharge for repeated calls. Prices are per million tokens and must be looked up
             on the provider's current price list; the script has no built-in prices.
  empirical  documents x runs x cost per document observed in an earlier run

Defaults for the token means come from the processing log of our first run (706 documents that
returned valid output on the first pass: mean 4,947 input and 1,887 output tokens per document).
In our first run, 88 of 794 responses had to be repeated. The provider invoice for the whole first
run, repeats included, was about USD 50, i.e. about 6 cents per document.

Examples
  python tools/estimate_cost.py tokens --docs 794 --runs 3 --price-in <USD per 1M> --price-out <USD per 1M>
  python tools/estimate_cost.py empirical --docs 794 --runs 3 --cost-per-doc 0.063
  python tools/estimate_cost.py tokens --log runs/log_A1.csv --docs 1700 --runs 1 --price-in ... --price-out ...
"""
import argparse

import pandas as pd


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("tokens")
    t.add_argument("--docs", type=int, required=True)
    t.add_argument("--runs", type=int, default=1)
    t.add_argument("--in-tokens", type=float, default=4947)
    t.add_argument("--out-tokens", type=float, default=1887)
    t.add_argument("--log", help="processing log with input_tokens/output_tokens columns; overrides the means")
    t.add_argument("--price-in", type=float, required=True, help="USD per 1M input tokens")
    t.add_argument("--price-out", type=float, required=True, help="USD per 1M output tokens")
    t.add_argument("--repeat-share", type=float, default=0.11, help="share of documents that need a second call")
    e = sub.add_parser("empirical")
    e.add_argument("--docs", type=int, required=True)
    e.add_argument("--runs", type=int, default=1)
    e.add_argument("--cost-per-doc", type=float, default=0.063, help="USD per document from an earlier invoice")
    a = p.parse_args()
    if a.cmd == "tokens":
        if a.log:
            lg = pd.read_csv(a.log)
            ok = lg[lg["status"].astype(str).str.lower() == "ok"]
            a.in_tokens, a.out_tokens = ok["input_tokens"].mean(), ok["output_tokens"].mean()
        per_doc = a.in_tokens / 1e6 * a.price_in + a.out_tokens / 1e6 * a.price_out
        total = per_doc * a.docs * a.runs * (1 + a.repeat_share)
        print(f"mean tokens per document: {a.in_tokens:,.0f} in, {a.out_tokens:,.0f} out")
        print(f"cost per document: USD {per_doc:.4f}; total for {a.docs} documents x {a.runs} runs "
              f"(+{a.repeat_share:.0%} repeats): USD {total:,.2f}")
    else:
        total = a.cost_per_doc * a.docs * a.runs
        print(f"USD {a.cost_per_doc:.3f} per document x {a.docs} documents x {a.runs} runs = USD {total:,.2f}")


if __name__ == "__main__":
    main()
