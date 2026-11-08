"""Exports the workbook's Excel charts as PNG images for the README (needs LibreOffice)."""
from xlkit.charts import render

PAGES = {"Overview": "overview.png", "Chart Scores": "scores.png", "Rules Before": "rules_before.png", "Rules After": "rules_after.png",
         "Chart Rules Radar": "rules_radar.png", "Chart Pareto": "pareto.png", "Chart Anatomy": "anatomy.png", "Chart Sections": "sections.png",
         "Chart Length vs Score": "length_vs_score.png", "Chart Cost": "cost.png"}
for n in render("excel/prompt_engineering_lab.xlsx", PAGES, "results"):
    print(n, "->", PAGES[n])
