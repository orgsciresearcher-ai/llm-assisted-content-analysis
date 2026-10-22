"""Derive the de-labeled prompt B from the original prompt A (case study), reproducibly and checkably.

Every edit is an explicit replacement with an expected number of hits. If a count differs, the script
stops. Afterwards it checks that no theory markers remain (code prefixes, construct names, references)
and that the input placeholders still work.

This file is case-specific: the replacement list fits our codebook. To adapt it, keep the structure
(replace labels, prefixes, theoretical headings and references; keep definitions, rules, indicators and
worked examples word for word) and write your own CHANGES list. See guide/06_theory_label_test.md.

Inputs   prompts/case/A_system.txt, prompts/case/A_user.txt
Outputs  B_system.txt, B_user.txt, code_mapping.json, change_log_A_to_B.md (in --out-dir)

  python tools/build_delabeled_prompt.py --prompts prompts/case --out-dir prompts/case --check
"""
import argparse
import difflib
import hashlib
import json
import re
import sys
from pathlib import Path

L1_ORIG = ["GT1.1", "GT1.2", "GT1.3", "GT2.1", "GT2.2", "GT2.3", "GT2.4", "GT3.1", "GT3.2", "GT3.3",
           "GT4.1", "GT4.2", "GT4.3", "GT5.1", "GT5.2", "GT5.3", "GT5.4"]
L2_ORIG = ["SK1", "SK2", "SK3"]
MAP = {c: f"L1-{i:02d}" for i, c in enumerate(L1_ORIG, 1)}
MAP.update({c: f"L2-{i:02d}" for i, c in enumerate(L2_ORIG, 1)})
REV = {v: k for k, v in MAP.items()}

# (id, target, old, new, expected hits, reason)
CHANGES = [
    ("S1", "sys", "apply a theory-derived codebook", "apply a codebook", 1, "reference to theoretical derivation removed"),
    ("U1", "user",
     "- Layer 1: Governance tension codes (GT) — derived from IS governance theory\n"
     "- Layer 2: Skill/competence codes (SK) — derived from Todd et al. (1995)",
     "- Layer 1: Responsibility codes (L1)\n"
     "- Layer 2: Skill/competence codes (L2)", 1,
     "construct name, theory and reference removed; layers kept as operational levels"),
    ("U2", "user", "maps to at least one GT or SK code", "maps to at least one L1 or L2 code", 1, "code prefixes neutralized"),
    ("U3", "user", "contain no AI-relevant governance or competence content",
     "contain no AI-relevant responsibility or competence content", 1,
     "'governance' as construct name replaced by the layer name"),
    ("U4", "user", "GT_Code: NONE, SK_Code: NONE", "L1_Code: NONE, L2_Code: NONE", 2, "output fields neutralized"),
    ("U5", "user", "- GT codes (Layer 1) are assigned EXCLUSIVELY", "- L1 codes (Layer 1) are assigned EXCLUSIVELY", 1,
     "code prefixes neutralized"),
    ("U6", "user", "- SK codes (Layer 2) are assigned EXCLUSIVELY", "- L2 codes (Layer 2) are assigned EXCLUSIVELY", 1,
     "code prefixes neutralized"),
    ("U7", "user", "assign GT codes only if the language", "assign L1 codes only if the language", 1,
     "code prefixes neutralized"),
    ("U8", "user", "## CRITICAL RULE: DUAL CODING GT + SK", "## CRITICAL RULE: DUAL CODING L1 + L2", 1,
     "code prefixes neutralized"),
    ("U9", "user",
     "A single passage may receive both GT codes and SK codes simultaneously if it describes "
     "a governance responsibility (GT layer) AND implies a required competence (SK layer).",
     "A single passage may receive both L1 codes and L2 codes simultaneously if it describes "
     "a responsibility (L1 layer) AND implies a required competence (L2 layer).", 1,
     "code prefixes neutralized; 'governance' as construct name removed"),
    ("U10", "user", "When a passage addresses multiple governance tensions,",
     "When a passage addresses multiple responsibilities,", 1, "construct name 'governance tension' replaced; rule unchanged"),
    ("U11", "user", "If one tension is clearly dominant", "If one responsibility is clearly dominant", 1, "as U10"),
    ("U12", "user", "note the secondary tension in the Rationale", "note the secondary responsibility in the Rationale", 1,
     "as U10"),
    ("U13", "user", "### LAYER 1 — GOVERNANCE TENSION CODES", "### LAYER 1 — RESPONSIBILITY CODES (L1)", 1,
     "construct name removed"),
    ("U14", "user", "### LAYER 2 — SKILL/COMPETENCE CODES (Todd et al., 1995)", "### LAYER 2 — SKILL/COMPETENCE CODES (L2)", 1,
     "reference removed"),
    ("U15", "user", "or platforms as a governance dimension.", "or platforms.", 1,
     "theoretical framing inside one definition (GT3.1) removed; the spreadsheet version of the codebook "
     "does not contain this phrase either"),
    ("U16", "user", '"GT_Code": "<semicolon-separated GT codes, or NONE>",', '"L1_Code": "<semicolon-separated L1 codes, or NONE>",', 1,
     "output schema neutralized"),
    ("U17", "user", '"SK_Code": "<semicolon-separated SK codes, or NONE>",', '"L2_Code": "<semicolon-separated L2 codes, or NONE>",', 1,
     "output schema neutralized"),
    ("U18", "user", "why GT or SK applies", "why L1 or L2 applies", 1, "output schema neutralized"),
    ("U19", "user", "Example B — Dual GT + SK passage:", "Example B — Dual L1 + L2 passage:", 1, "example heading neutralized"),
    ("U20", "user", "Responsibilities section, so no SK code applies.", "Responsibilities section, so no L2 code applies.", 1,
     "example rationale neutralized"),
    ("U21", "user", '"GT_Code": ', '"L1_Code": ', 3, "field names in examples A to C"),
    ("U22", "user", '"SK_Code": ', '"L2_Code": ', 3, "field names in examples A to C"),
]
REGEX_CHANGES = [
    ("R1", r"^GT[1-5] — [^\n]+\n\n", lambda m: "", 5, "group headings GT1 to GT5 removed (theoretical grouping)"),
    ("R2", r"^GT([1-5])\.([1-4]) \| [^\n]+$", lambda m: MAP[f"GT{m.group(1)}.{m.group(2)}"], 17,
     "code ID and label replaced by a neutral ID (label dropped)"),
    ("R3", r"^SK([1-3]) \| [^\n]+$", lambda m: MAP[f"SK{m.group(1)}"], 3, "code ID and label replaced by a neutral ID"),
    ("R4", r"\bGT([1-5])\.([1-4])\b", lambda m: MAP[f"GT{m.group(1)}.{m.group(2)}"], 6,
     "remaining code IDs in the examples (code field and rationale)"),
    ("R5", r"\bSK([1-3])\b", lambda m: MAP[f"SK{m.group(1)}"], 2, "remaining code IDs in the examples"),
]
MARKERS = re.compile(r"\bGT|\bGD|\bSK\d|\bSK\b|Todd|theor|tension|demand", re.I)


def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:12]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--prompts", default="prompts/case")
    p.add_argument("--out-dir", default="prompts/case")
    p.add_argument("--check", action="store_true", help="compare the result with existing B files and report")
    a = p.parse_args()
    src, out = Path(a.prompts), Path(a.out_dir)
    a_sys = (src / "A_system.txt").read_text(encoding="utf-8")
    a_user = (src / "A_user.txt").read_text(encoding="utf-8")
    texts, log = {"sys": a_sys, "user": a_user}, []
    for cid, tgt, old, new, n_exp, why in CHANGES:
        n = texts[tgt].count(old)
        if n != n_exp:
            sys.exit(f"{cid}: expected {n_exp} hits, found {n}; stopped")
        texts[tgt] = texts[tgt].replace(old, new)
        log.append((cid, old, new, n, why))
    for cid, pat, repl, n_exp, why in REGEX_CHANGES:
        rx = re.compile(pat, re.M)
        n = len(rx.findall(texts["user"]))
        if n != n_exp:
            sys.exit(f"{cid}: expected {n_exp} hits, found {n}; stopped")
        texts["user"] = rx.sub(repl, texts["user"])
        log.append((cid, f"regex {pat}", "(see mapping)", n, why))
    b_sys, b_user = texts["sys"], texts["user"]
    residual = [m.group(0) for t in (b_sys, b_user) for m in MARKERS.finditer(t)]
    if residual:
        sys.exit(f"theory markers left in B: {residual}")
    b_user.format(ad_id="TEST", role_family="TEST", language="en", full_text="test")

    if a.check and (out / "B_user.txt").exists():
        same = ((out / "B_system.txt").read_text(encoding="utf-8") == b_sys and
                (out / "B_user.txt").read_text(encoding="utf-8") == b_user)
        print("identical to existing B files" if same else "DIFFERS from existing B files")
    out.mkdir(parents=True, exist_ok=True)
    (out / "B_system.txt").write_text(b_sys, encoding="utf-8")
    (out / "B_user.txt").write_text(b_user, encoding="utf-8")
    (out / "code_mapping.json").write_text(json.dumps({"to_B": MAP, "to_A": REV}, indent=2), encoding="utf-8")

    gov = [ln.strip() for ln in b_user.splitlines() if re.search(r"governance", ln, re.I)]
    md = ["# Change log: prompt A to prompt B (theory-label test)", "",
          "Generated by `tools/build_delabeled_prompt.py`. Each row is an explicit replacement with a checked hit count.", "",
          "| Prompt | SHA-256 (first 12) |", "|---|---|",
          f"| A_system | `{sha(a_sys)}` |", f"| A_user | `{sha(a_user)}` |",
          f"| B_system | `{sha(b_sys)}` |", f"| B_user | `{sha(b_user)}` |", "",
          "## What stays the same", "",
          "Definitions, code-when rules, indicators (one exception, U15), all coding rules, the order of codes, the worked "
          "examples (only code IDs and field names mapped), the output schema apart from field names, and the input slot.", "",
          f"## Edits ({len(log)})", "", "| ID | old | new | hits | reason |", "|---|---|---|---|---|"]
    for cid, old, new, n, why in log:
        md.append(f"| {cid} | `{old.replace(chr(10), ' ⏎ ').replace('|', chr(92) + '|')}` | "
                  f"`{new.replace(chr(10), ' ⏎ ').replace('|', chr(92) + '|')}` | {n} | {why} |")
    md += ["", "## Code mapping", "", "| B | A |", "|---|---|"] + [f"| {b} | {a_} |" for b, a_ in REV.items()]
    md += ["", "## Remaining occurrences of 'governance' in B", "",
           "Kept on purpose: operational content of a definition or an example of a section heading.", ""]
    md += [f"- {g}" for g in gov]
    md += ["", "## Full diff A_user to B_user", "", "```diff"]
    md += list(difflib.unified_diff(a_user.splitlines(), b_user.splitlines(), "A_user.txt", "B_user.txt", lineterm="", n=0))
    md += ["```", ""]
    (out / "change_log_A_to_B.md").write_text("\n".join(md), encoding="utf-8")
    print(f"{len(log)} edits; wrote B_system.txt, B_user.txt, code_mapping.json, change_log_A_to_B.md to {out}")


if __name__ == "__main__":
    main()
