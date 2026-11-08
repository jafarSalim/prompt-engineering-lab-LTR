"""Checks a prompt against 11 rules. Each rule cites the guidance it comes from.

This is a checklist, not a model: it shows what a prompt contains, not how
good the answer will be. Always test prompts on real inputs.
"""
import re
from dataclasses import dataclass

GUIDE = "https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices"
TASK_VERBS = r"\b(write|summari[sz]e|classify|extract|translate|explain|generate|review|answer|list|draft|rewrite|compare|calculate|solve|create|analy[sz]e|convert|label|describe|produce|return|find|identify|plan|design|edit|check|grade)\b"
VAGUE = r"\b(some|good|nice|stuff|things?|etc|whatever|kind of|sort of|maybe|a bit|properly|better)\b"
NEG = r"\b(don't|do not|never|avoid|no)\b(?!\s*(more|later|longer)\s+than)"
FORMAT = r"\b(json|table|bullet|list|paragraphs?|csv|markdown|headings?|format|tags?|yaml|numbered|columns?|fields?|keys?|schema|plain text|prose|code block|one block|sections?)\b|<\w+>\s*(tags?)?"
LENGTH = r"\b(\d+|one|two|three|four|five|six|seven|eight|ten)\s*(-\s*\d+\s*)?(words?|sentences?|items?|bullets?|lines?|paragraphs?|characters?|examples?|points?|steps?|rows?|tokens?|minutes?|hours?|days?)\b|\b(at most|no more than|under|maximum|up to)\b"
WHY = r"\b(because|so that|since|in order to|the reader|readers?|audience|will (be|run|appear|feed|go|read)\b|feeds?|appears? (on|in)|for (a|an|my|our|the) [\w ]{0,20}(report|dashboard|page|team|system)|purpose|goal)\b|,\s*so\b"
ROLE = r"(^|\n)\s*(you are|act as|you're|as an? )\b"
EXAMPLE = r"<examples?>|\bexamples?:|\bfor example\b|\be\.g\.|\binput:.*\boutput:"
VERIFY = r"\b(verify|double-check|check your|check that|before (you )?(finish|answer)|before answering|make sure|confirm that|test (it|the))\b"
LONGDATA = r"\{\{[A-Z_]+\}\}|<(document|report|data|text|email|article|transcript|code|reviews?|table)[^>]*>"


@dataclass
class Rule:
    key: str
    name: str
    weight: int
    source: str


RULES = [
    Rule("role", "Gives a role", 1, "Give Claude a role"),
    Rule("task", "States the task with a clear verb", 2, "Be clear and direct"),
    Rule("why", "Explains the purpose or audience", 2, "Add context to improve performance"),
    Rule("format", "Specifies the output format", 2, "Control the format of responses"),
    Rule("length", "Sets length or other limits", 1, "Be clear and direct"),
    Rule("examples", "Includes examples", 1, "Use examples effectively"),
    Rule("structure", "Uses XML tags for structure", 1, "Structure prompts with XML tags"),
    Rule("positive", "Says what to do, not only what not to do", 1, "Tell Claude what to do instead of what not to do"),
    Rule("data_first", "Puts long data before the question", 2, "Long context prompting"),
    Rule("verify", "Asks for a self-check", 1, "Leverage thinking"),
    Rule("specific", "Avoids vague words", 1, "Be clear and direct"),
]


def check(prompt, kind="general"):
    """Returns {rule key: True, False or None (not applicable)}."""
    p = prompt.strip()
    low = p.lower()
    # Placeholders and tags are not instructions, so verbs are searched without them
    plain = re.sub(r"\{\{[A-Z_]+\}\}|<[^>]+>", " ", p).lower()
    r = {}
    r["role"] = bool(re.search(ROLE, low))
    r["task"] = bool(re.search(TASK_VERBS, plain))
    r["why"] = bool(re.search(WHY, low))
    r["format"] = bool(re.search(FORMAT, low))
    r["length"] = bool(re.search(LENGTH, low)) if kind in ("general", "style", "math") else None
    r["examples"] = bool(re.search(EXAMPLE, low)) if kind in ("classify", "extract", "format", "style") else None
    # XML structure matters when a prompt mixes instructions with data or examples, or is long
    needs = bool(re.search(r"\{\{[A-Z_]+\}\}", p)) or bool(re.search(EXAMPLE, low)) or len(p) > 600
    r["structure"] = bool(re.search(r"<(\w+)[^>]*>[\s\S]*?</\1>", p)) if needs else None
    negs = len(re.findall(NEG, low))
    r["positive"] = negs <= 1
    m = re.search(LONGDATA, p)
    if m:
        masked = re.sub(r"\{\{[A-Z_]+\}\}|<[^>]+>", lambda s: " " * len(s.group()), p).lower()
        verb = [x.start() for x in re.finditer(TASK_VERBS, masked)]
        r["data_first"] = bool(verb) and max(verb) > m.start()
    else:
        r["data_first"] = None
    r["verify"] = bool(re.search(VERIFY, low)) if kind in ("math", "code", "extract", "data") else None
    r["specific"] = len(re.findall(VAGUE, low)) <= 1
    return r


def score(result):
    num = sum(x.weight for x in RULES if result[x.key] is True)
    den = sum(x.weight for x in RULES if result[x.key] is not None)
    return 100 * num / den if den else 0.0


ADVICE = {
    "role": "Start with one sentence that sets a role, for example 'You are a support agent for ...'.",
    "task": "State the task with a clear verb: write, summarize, extract, classify, translate ...",
    "why": "Say who the answer is for and why, so the model can make sensible choices.",
    "format": "Describe the exact output format: a JSON object with named keys, a table, numbered steps ...",
    "length": "Set limits: 'at most 5 bullets', '120 words', 'one paragraph'.",
    "examples": "Add 3 to 5 short examples inside <examples> tags.",
    "structure": "Wrap instructions, data and examples in separate XML tags such as <document> and <instructions>.",
    "positive": "Replace 'don't' rules with what you want instead.",
    "data_first": "Put the long document first and the question at the end.",
    "verify": "Ask the model to check its answer against your criteria before finishing.",
    "specific": "Replace vague words such as 'good' or 'some' with concrete requirements.",
}
