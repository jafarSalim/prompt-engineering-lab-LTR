"""Builds excel/prompt_engineering_lab.xlsx: the rule matrix, live score formulas and native Excel charts."""
import json, pathlib
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.chart import BarChart, LineChart, ScatterChart, RadarChart, DoughnutChart, Reference, Series
from openpyxl.chart.series import DataPoint
from openpyxl.chart.shapes import GraphicalProperties
from openpyxl.chart.label import DataLabelList
from openpyxl.chart.axis import ChartLines
from openpyxl.utils import get_column_letter as L
from xlkit.charts import BLUE_IN, NOTE, OFFICE, header, style, fill, labels, chart_sheet, tiles

A = json.load(open("results/analysis.json", encoding="utf8"))
RULES, ROWS = A["rules"], A["rows"]
NR, NT = len(RULES), len(ROWS)
wb = Workbook(); wb.remove(wb.active)
thin = Side(style="thin", color="BFBFBF")

# ---- Rule matrices (measured by promptlab/lint.py) with score formulas ----
for side in ("Before", "After"):
    ws = wb.create_sheet(f"Rules {side}")
    ws["A1"] = f"Checklist results, {side.lower()} prompts (✓ pass, ✗ fix, blank = not applicable)"
    ws["A1"].font = Font(name="Calibri", bold=True, size=15, color="1F4E79")
    header(ws, 2, ["Rule", "Weight"] + [r["task"] for r in ROWS], [34, 8] + [11] * NT)
    ws.row_dimensions[2].height = 48
    for i, rule in enumerate(RULES, 3):
        ws.cell(i, 1, rule["name"]); ws.cell(i, 2, rule["weight"]).font = BLUE_IN
        for j, row in enumerate(ROWS, 3):
            v = row[f"rules_{side.lower()}"][rule["key"]]
            c = ws.cell(i, j, None if v is None else int(v))
            c.number_format, c.alignment, c.border = '"✓";;"✗"', Alignment(horizontal="center"), Border(thin, thin, thin, thin)
            c.font = Font(name="Calibri", bold=True, size=13)
    last = 2 + NR
    ws.conditional_formatting.add(f"C3:{L(2 + NT)}{last}", ColorScaleRule(start_type="num", start_value=0, start_color="F8696B", end_type="num", end_value=1, end_color="63BE7B"))
    sr = last + 1
    ws.cell(sr, 1, "Score (0-100)").font = Font(name="Calibri", bold=True)
    for j in range(3, 3 + NT):
        col = L(j)
        c = ws.cell(sr, j, f'=100*SUMPRODUCT($B$3:$B${last},{col}3:{col}{last})/SUMPRODUCT($B$3:$B${last},--({col}3:{col}{last}<>""))')
        c.number_format, c.font, c.alignment = "0", Font(name="Calibri", bold=True), Alignment(horizontal="center")
    ws.cell(sr + 2, 1, "Score = sum of weights of passed rules ÷ sum of weights of applicable rules. Change a weight and every score updates.").font = NOTE
    ws.page_setup.orientation = "landscape"; ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_area = f"A1:{L(2 + NT)}{sr}"
SR = 3 + NR

# ---- Scores per task ----
sc = wb.create_sheet("Scores Data")
header(sc, 1, ["Task", "Before", "After", "Tokens before", "Tokens after", "Gain per extra token"], [28, 9, 9, 13, 12, 18])
for i, row in enumerate(ROWS, 2):
    col = L(i + 1)
    sc.cell(i, 1, row["task"])
    sc.cell(i, 2, f"='Rules Before'!{col}{SR}").number_format = "0"
    sc.cell(i, 3, f"='Rules After'!{col}{SR}").number_format = "0"
    sc.cell(i, 4, row["tokens_before"]); sc.cell(i, 5, row["tokens_after"])
    sc.cell(i, 6, f"=(C{i}-B{i})/(E{i}-D{i})").number_format = "0.00"
E_ = NT + 1
sc.cell(E_ + 1, 1, "Average").font = Font(name="Calibri", bold=True)
for c in "BCDE":
    sc[f"{c}{E_ + 1}"] = f"=AVERAGE({c}2:{c}{E_})"; sc[f"{c}{E_ + 1}"].number_format = "0"
sc.cell(E_ + 3, 1, "Tokens: open Llama 4 tokenizer as a stand-in. Claude counts differ.").font = NOTE

# ---- Pass rate per rule ----
pr = wb.create_sheet("Pass Rate Data")
header(pr, 1, ["Rule", "Before", "After"], [34, 10, 10])
for i, rule in enumerate(RULES, 2):
    r = i + 1
    pr.cell(i, 1, rule["name"])
    for side, col in (("Before", 2), ("After", 3)):
        pr.cell(i, col, f"=IFERROR(SUM('Rules {side}'!C{r}:{L(2 + NT)}{r})/COUNT('Rules {side}'!C{r}:{L(2 + NT)}{r}),0)").number_format = "0%"

# ---- Pareto of missing rules in the before prompts ----
pa = wb.create_sheet("Pareto Data")
header(pa, 1, ["Rule", "Prompts missing it", "Cumulative share"], [34, 18, 16])
fails = list(A["fails_before"].items())
name = {r["key"]: r["name"] for r in RULES}
idx = {r["key"]: k + 3 for k, r in enumerate(RULES)}
for i, (k, _) in enumerate(fails, 2):
    pa.cell(i, 1, name[k])
    pa.cell(i, 2, f"=COUNTIF('Rules Before'!C{idx[k]}:{L(2 + NT)}{idx[k]},0)")
    pa.cell(i, 3, f"=SUM($B$2:B{i})/SUM($B$2:$B${len(fails) + 1})").number_format = "0%"

# ---- Anatomy of the improved prompts ----
an = wb.create_sheet("Anatomy Data")
secs = ["role", "context", "data", "task", "format", "examples", "checks"]
header(an, 1, ["Task"] + [s.capitalize() for s in secs], [28] + [10] * len(secs))
for i, row in enumerate(ROWS, 2):
    an.cell(i, 1, row["task"])
    for j, s in enumerate(secs, 2):
        an.cell(i, j, row["sections"].get(s, 0))
an.cell(E_ + 1, 1, "Total").font = Font(name="Calibri", bold=True)
for j in range(2, 2 + len(secs)):
    an.cell(E_ + 1, j, f"=SUM({L(j)}2:{L(j)}{E_})")

# ---- Cost calculator ----
cc = wb.create_sheet("Cost Calculator", 0)
cc.column_dimensions["A"].width, cc.column_dimensions["B"].width, cc.column_dimensions["C"].width = 42, 14, 14
cc["A1"] = "Does a better prompt cost much more?"; cc["A1"].font = Font(name="Calibri", bold=True, size=16, color="1F4E79")
cc["A3"], cc["B3"] = "Price, USD per million input tokens", 2
cc["A4"], cc["B4"] = "Average tokens, before", f"='Scores Data'!D{E_ + 1}"
cc["A5"], cc["B5"] = "Average tokens, after", f"='Scores Data'!E{E_ + 1}"
cc["A6"] = "Example price: Claude Sonnet 5.5 input, $2 per million tokens (platform.claude.com pricing, Nov 2026)."; cc["A6"].font = NOTE
cc["B3"].font = BLUE_IN; cc["B3"].number_format = '"$"0.00'
for c in ("B4", "B5"):
    cc[c].number_format = "0"
header(cc, 8, ["Requests per day", "Before, $/month", "After, $/month"])
for i, n in enumerate([100, 500, 1000, 5000, 10000, 50000, 100000], 9):
    cc.cell(i, 1, n).number_format = "#,##0"
    cc.cell(i, 2, f"=A{i}*30*$B$4*$B$3/1000000").number_format = '"$"#,##0.00'
    cc.cell(i, 3, f"=A{i}*30*$B$5*$B$3/1000000").number_format = '"$"#,##0.00'

# ================= Charts =================
c1 = BarChart(); c1.type = "bar"; c1.gapWidth = 40
for col, colr in ((2, "A5A5A5"), (3, "70AD47")):
    s = Series(Reference(sc, min_col=col, min_row=1, max_row=E_), title_from_data=True); fill(s, colr); labels(s, "0", "outEnd"); c1.series.append(s)
c1.set_categories(Reference(sc, min_col=1, min_row=2, max_row=E_))
c1.x_axis.scaling.orientation = "maxMin"; c1.y_axis.scaling.max = 110; c1.y_axis.scaling.min = 0; c1.y_axis.title = "Checklist score (0-100)"; c1.legend.position = "b"
style(c1, "Checklist score of 12 prompts, before and after rewriting", 24, 16)
chart_sheet(wb, "Chart Scores", c1)

c2 = RadarChart(); c2.type = "marker"
for col, colr in ((2, "ED7D31"), (3, "70AD47")):
    s = Series(Reference(pr, min_col=col, min_row=1, max_row=NR + 1), title_from_data=True)
    fill(s, colr, line=True, width=38100)
    s.marker.symbol = "circle"; s.marker.size = 8; s.marker.graphicalProperties = GraphicalProperties(solidFill=colr)
    c2.series.append(s)
c2.set_categories(Reference(pr, min_col=1, min_row=2, max_row=NR + 1))
c2.y_axis.delete = False; c2.y_axis.numFmt = "0%"; c2.legend.position = "b"
style(c2, "Share of prompts passing each rule", 22, 15)
chart_sheet(wb, "Chart Rules Radar", c2)

c3 = BarChart(); c3.type = "col"; c3.gapWidth = 40
s = Series(Reference(pa, min_col=2, min_row=1, max_row=len(fails) + 1), title_from_data=True); fill(s, "4472C4"); labels(s, "0", "outEnd"); c3.series.append(s)
c3.set_categories(Reference(pa, min_col=1, min_row=2, max_row=len(fails) + 1))
c3.y_axis.title = "Prompts missing the rule"; c3.y_axis.majorGridlines = None
ln = LineChart()
s2 = Series(Reference(pa, min_col=3, min_row=1, max_row=len(fails) + 1), title_from_data=True); fill(s2, "ED7D31", line=True)
s2.marker.symbol = "circle"; s2.marker.size = 7; s2.marker.graphicalProperties = GraphicalProperties(solidFill="ED7D31")
ln.series.append(s2); ln.y_axis.axId = 200; ln.y_axis.title = "Cumulative share"; ln.y_axis.numFmt = "0%"; ln.y_axis.crosses = "max"; ln.y_axis.scaling.max = 1
c3 += ln
c3.legend.position = "b"
style(c3, "Pareto: what the original prompts were missing", 26, 15)
chart_sheet(wb, "Chart Pareto", c3)

c4 = DoughnutChart(holeSize=55)
c4.add_data(Reference(an, min_col=2, min_row=E_ + 1, max_col=1 + len(secs), max_row=E_ + 1), from_rows=True, titles_from_data=False)
c4.set_categories(Reference(an, min_col=2, min_row=1, max_col=1 + len(secs), max_row=1))
for k, colr in enumerate(["7030A0", "4472C4", "A5A5A5", "ED7D31", "70AD47", "FFC000", "C00000"]):
    p = DataPoint(idx=k); p.graphicalProperties = GraphicalProperties(solidFill=colr); c4.series[0].dPt.append(p)
c4.dataLabels = DataLabelList(); c4.dataLabels.showPercent = True
for k in ("showVal", "showCatName", "showSerName", "showLegendKey"):
    setattr(c4.dataLabels, k, False)
c4.legend.position = "r"
style(c4, "Anatomy of a good prompt: where the tokens go", 18, 12)
chart_sheet(wb, "Chart Anatomy", c4)

c5 = BarChart(); c5.type = "col"; c5.grouping = "stacked"; c5.overlap = 100; c5.gapWidth = 50
for j, colr in zip(range(2, 2 + len(secs)), ["7030A0", "4472C4", "A5A5A5", "ED7D31", "70AD47", "FFC000", "C00000"]):
    s = Series(Reference(an, min_col=j, min_row=1, max_row=E_), title_from_data=True); fill(s, colr); c5.series.append(s)
c5.set_categories(Reference(an, min_col=1, min_row=2, max_row=E_))
c5.y_axis.title = "Tokens"; c5.legend.position = "b"
style(c5, "Each improved prompt, section by section", 26, 15)
chart_sheet(wb, "Chart Sections", c5)

c6 = ScatterChart(); c6.style = 13
for col, title, colr in ((2, "Before", "ED7D31"), (3, "After", "70AD47")):
    s = Series(Reference(sc, min_col=col, min_row=2, max_row=E_), Reference(sc, min_col=col + 2, min_row=2, max_row=E_), title=title)
    s.marker.symbol = "circle"; s.marker.size = 10
    s.marker.graphicalProperties = GraphicalProperties(solidFill=colr); s.marker.graphicalProperties.line.solidFill = colr
    s.graphicalProperties = GraphicalProperties(); s.graphicalProperties.line.noFill = True
    c6.series.append(s)
c6.x_axis.title = "Prompt length (tokens)"; c6.y_axis.title = "Checklist score"; c6.y_axis.scaling.max = 105; c6.y_axis.scaling.min = 0
c6.legend.position = "b"
style(c6, "Prompt length vs checklist score (each dot is a prompt)")
chart_sheet(wb, "Chart Length vs Score", c6)

c7 = LineChart()
c7.add_data(Reference(cc, min_col=2, min_row=8, max_col=3, max_row=15), titles_from_data=True)
c7.set_categories(Reference(cc, min_col=1, min_row=9, max_row=15))
for s, colr in zip(c7.series, ["ED7D31", "70AD47"]):
    fill(s, colr, line=True); s.marker.symbol = "circle"; s.marker.size = 7
    s.marker.graphicalProperties = GraphicalProperties(solidFill=colr)
c7.y_axis.scaling.logBase = 10; c7.y_axis.numFmt = '"$"#,##0.00'; c7.y_axis.title = "Prompt input cost per month (log)"; c7.x_axis.title = "Requests per day"
c7.legend.position = "b"
style(c7, "What the longer prompt costs per month at $2 per million tokens")
chart_sheet(wb, "Chart Cost", c7)

gain = A["mean_after"] - A["mean_before"]
tiles(wb, [(f"='Scores Data'!C{E_ + 1}-'Scores Data'!B{E_ + 1}", '"+"0', "Checklist points gained", "A9D18E"),
           ("='Pareto Data'!B2", '0" of 12"', "Prompts with no role", "FF7C80"),
           (f"='Scores Data'!E{E_ + 1}-'Scores Data'!D{E_ + 1}", '"+"0', "Extra tokens per prompt", "9DC3E6"),
           ("='Cost Calculator'!C11-'Cost Calculator'!B11", '"$"0.00', "Extra per month, 1,000/day", "FFD966")])
order = ["Overview", "Cost Calculator", "Chart Scores", "Rules Before", "Rules After", "Chart Rules Radar", "Chart Pareto", "Chart Anatomy",
         "Chart Sections", "Chart Length vs Score", "Chart Cost", "Scores Data", "Pass Rate Data", "Pareto Data", "Anatomy Data"]
wb._sheets = [wb[n] for n in order]
pathlib.Path("excel").mkdir(exist_ok=True)
wb.save("excel/prompt_engineering_lab.xlsx")
print("saved")
