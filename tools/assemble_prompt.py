"""Assemble a system prompt and a user prompt template from the nine modular blocks.

Block files (prompts/template/):
  01_role_statement.txt            -> system prompt
  02_research_context.txt          \
  03_task.txt                       |
  04_rule_specificity.txt           |
  05_rule_section_scope.txt         |  user prompt, in this order
  06_rule_multiple_codes.txt        |
  07_rule_primary_code.txt          |
  08_codebook.txt                   |
  09_output_schema_and_examples.txt/
  input_slot.txt                   -> appended last; holds the {placeholders} filled per document

Write placeholders for your study as [[LIKE_THIS]]. The script stops if any remain, so no
template text reaches the model by accident. Lines starting with // are notes for researchers
and are removed. Braces in blocks 02-09 (for example in the JSON
schema) are escaped automatically so that run_coding.py can fill the input slot with str.format.

Example
  python tools/assemble_prompt.py --blocks my_study/blocks --out-dir my_study/prompt
  python tools/assemble_prompt.py --blocks prompts/template --out-dir /tmp/check --allow-placeholders
"""
import argparse
import re
import sys
from pathlib import Path

ORDER = ["01_role_statement", "02_research_context", "03_task", "04_rule_specificity", "05_rule_section_scope",
         "06_rule_multiple_codes", "07_rule_primary_code", "08_codebook", "09_output_schema_and_examples"]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--blocks", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--allow-placeholders", action="store_true", help="do not stop on remaining [[...]] markers")
    a = p.parse_args()
    d = Path(a.blocks)
    parts = {}
    for name in ORDER + ["input_slot"]:
        f = d / f"{name}.txt"
        if not f.exists():
            sys.exit(f"missing block {f}")
        parts[name] = f.read_text(encoding="utf-8").strip()
    parts = {k: "\n".join(l for l in v.splitlines() if not l.lstrip().startswith("//")).strip() for k, v in parts.items()}
    left = sorted(set(re.findall(r"\[\[[^\]]+\]\]", "\n".join(parts.values()))))
    if left and not a.allow_placeholders:
        sys.exit("unfilled placeholders: " + ", ".join(left))
    system = parts["01_role_statement"]
    esc = lambda t: t.replace("{", "{{").replace("}", "}}")
    user = "\n\n---\n\n".join(esc(parts[n]) for n in ORDER[1:]) + "\n\n---\n\n" + parts["input_slot"]
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "system.txt").write_text(system + "\n", encoding="utf-8")
    (out / "user.txt").write_text(user + "\n", encoding="utf-8")
    print(f"wrote {out / 'system.txt'} and {out / 'user.txt'}" + (f" ({len(left)} placeholders left)" if left else ""))


if __name__ == "__main__":
    main()
