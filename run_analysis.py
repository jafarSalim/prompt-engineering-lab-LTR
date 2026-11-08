"""Scores the 12 prompt pairs and writes results/analysis.json."""
import json, pathlib
from collections import Counter
from promptlab.lint import RULES, check, score
from promptlab.tokens import count

pairs = json.load(open("data/prompt_pairs.json", encoding="utf8"))
rows, sections = [], Counter()
fails_before = Counter()
for p in pairs:
    after = "\n\n".join(t for _, t in p["after"])
    rb, ra = check(p["before"], p["kind"]), check(after, p["kind"])
    for k, v in rb.items():
        if v is False:
            fails_before[k] += 1
    sec = Counter()
    for name, t in p["after"]:
        sec[name] += count(t)
    sections.update(sec)
    rows.append(dict(task=p["task"], kind=p["kind"], score_before=score(rb), score_after=score(ra),
                     tokens_before=count(p["before"]), tokens_after=count(after), rules_before=rb, rules_after=ra, sections=dict(sec)))
pass_rate = {}
for r in RULES:
    for side in ("before", "after"):
        vals = [x[f"rules_{side}"][r.key] for x in rows if x[f"rules_{side}"][r.key] is not None]
        pass_rate.setdefault(r.key, {})[side] = sum(vals) / len(vals) if vals else None
    pass_rate[r.key]["applicable"] = sum(x["rules_before"][r.key] is not None for x in rows)
out = dict(rules=[r.__dict__ for r in RULES], rows=rows, pass_rate=pass_rate, fails_before=dict(fails_before.most_common()),
           sections=dict(sections), mean_before=sum(x["score_before"] for x in rows) / len(rows), mean_after=sum(x["score_after"] for x in rows) / len(rows),
           tokens_before=sum(x["tokens_before"] for x in rows), tokens_after=sum(x["tokens_after"] for x in rows))
pathlib.Path("results").mkdir(exist_ok=True)
json.dump(out, open("results/analysis.json", "w", encoding="utf8"), indent=1, ensure_ascii=False)
print(f"mean score {out['mean_before']:.1f} -> {out['mean_after']:.1f}; tokens {out['tokens_before']} -> {out['tokens_after']}")
print("fails before", out["fails_before"])
print("sections", out["sections"])
for x in rows:
    print(f"  {x['task']:28s} {x['tokens_before']:4d} -> {x['tokens_after']:4d}")
