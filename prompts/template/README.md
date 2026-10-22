# Prompt template: nine modular blocks

Fill each block for your study, replacing every `[[PLACEHOLDER]]`, then run

```bash
python tools/assemble_prompt.py --blocks prompts/template --out-dir my_study/prompt
```

The script writes `system.txt` (block 1) and `user.txt` (blocks 2 to 9 and the input slot), removes lines that start with `//`, escapes braces for `str.format`, and stops if any placeholder is left. See `guide/03_prompt.md` for what each block does and `prompts/case/` for a filled example.
