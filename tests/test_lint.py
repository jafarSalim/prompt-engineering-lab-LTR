import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from promptlab.lint import check, score


def test_bare_prompt_scores_low():
    assert score(check("Summarize this.")) <= 40


def test_full_prompt_scores_high():
    p = ("<report>\n{{REPORT}}\n</report>\n\nYou are an analyst writing for managers, so put numbers first.\n"
         "Summarize the report above. Return at most 5 bullets.")
    assert score(check(p)) >= 90


def test_data_after_question_fails_data_first():
    assert check("Summarize this report: {{REPORT}}")["data_first"] is False
    assert check("<report>{{REPORT}}</report> Summarize the report above.")["data_first"] is True


def test_many_negatives_fail_positive_rule():
    assert check("Don't use lists. Never use jargon. Avoid long words.")["positive"] is False


def test_not_applicable_rules_are_none():
    r = check("Write a haiku about rain.", kind="general")
    assert r["examples"] is None and r["verify"] is None and r["data_first"] is None
