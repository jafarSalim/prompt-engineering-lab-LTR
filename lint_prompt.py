"""Usage: python lint_prompt.py my_prompt.txt [--kind math|code|extract|classify|data|style|format|general]"""
import argparse
from promptlab.lint import RULES, ADVICE, check, score

ap = argparse.ArgumentParser()
ap.add_argument("file")
ap.add_argument("--kind", default="general")
a = ap.parse_args()
text = open(a.file, encoding="utf8").read()
r = check(text, a.kind)
print(f"\nScore: {score(r):.0f}/100\n")
for rule in RULES:
    v = r[rule.key]
    mark = "PASS" if v else ("n/a " if v is None else "FIX ")
    print(f"  [{mark}] {rule.name}")
fixes = [k for k, v in r.items() if v is False]
if fixes:
    print("\nSuggestions:")
    for k in fixes:
        print("  -", ADVICE[k])
