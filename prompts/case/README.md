# Case prompts

| File | Content |
|---|---|
| `A_system.txt`, `A_user.txt` | prompt A: original prompt with theoretical labels; used for runs A and A′ of the theory-label test |
| `B_system.txt`, `B_user.txt` | prompt B: de-labeled copy, derived from A by `tools/build_delabeled_prompt.py` |
| `code_mapping.json` | mapping between neutral IDs in B (L1-01 ... L2-03) and codes in A (GT1.1 ... SK3) |
| `change_log_A_to_B.md` | all 28 edits with hit counts, reasons, hashes and the full diff |

The user templates contain the placeholders `{ad_id}`, `{role_family}`, `{language}` and `{full_text}`; literal braces are doubled because `tools/run_coding.py` fills the template with Python's `str.format`.

Prompt A is the coding prompt of the case and the original prompt of the theory-label test.

The prompt maps onto the nine modular blocks of `prompts/template/` as follows: 1 role statement (system prompt), 2 research context, 3 task, 4 AI specificity rule, 5 responsibilities vs. requirements rule, 6 dual coding rule, 7 primary code rule, 8 codebook, 9 output format and worked examples, followed by the input slot.
