"""Remove personal contact details from text columns before sharing coded data.

Replaces e-mail addresses, phone numbers (9 or more digits) and profile links with placeholders and
reports how many replacements it made per column. It cannot find every personal name, so also search
the output for names of recruiters or contact persons by hand, for example with --names names.txt
(one name per line), before you publish.

  python tools/redact_personal_data.py --in segments.csv --out segments_shared.csv \
      --columns text_segment,rationale [--names names.txt]
"""
import argparse
import re

import pandas as pd

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
PROFILE = re.compile(r"(?:linkedin\.com/in|xing\.com/profile)/[\w%-]+", re.I)
PHONE = re.compile(r"(?<![\w$€£])\+?\(?\d[\d ()./-]{7,}\d(?!\w)")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--in", dest="inp", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--columns", required=True)
    p.add_argument("--names", help="text file with one personal name per line to replace")
    a = p.parse_args()
    df = pd.read_csv(a.inp)
    names = []
    if a.names:
        names = [n.strip() for n in open(a.names, encoding="utf-8") if n.strip()]
    report = {}
    for col in a.columns.split(","):
        counts = {"email": 0, "profile": 0, "phone": 0, "name": 0}

        def clean(t):
            if not isinstance(t, str):
                return t
            for key, rx in (("email", EMAIL), ("profile", PROFILE)):
                t, n = rx.subn(f"[{key} removed]", t)
                counts[key] += n

            def ph(m):
                if len(re.sub(r"\D", "", m.group(0))) >= 9:
                    counts["phone"] += 1
                    return "[phone removed]"
                return m.group(0)
            t = PHONE.sub(ph, t)
            for name in names:
                t, n = re.subn(re.escape(name), "[name removed]", t)
                counts["name"] += n
            return t
        df[col] = df[col].map(clean)
        report[col] = counts
    df.to_csv(a.out, index=False)
    for col, c in report.items():
        print(col, c)


if __name__ == "__main__":
    main()
