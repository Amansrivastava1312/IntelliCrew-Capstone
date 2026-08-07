"""Build the centralized report PDF from data + LLM narrative."""

from datetime import date
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
)

PRIMARY = colors.HexColor("#5559b8")
LIGHT = colors.HexColor("#eee7ff")
GREY = colors.HexColor("#4f5565")


def _styles():
    styles = getSampleStyleSheet()
    # NOTE: use unique names (IC prefix) — 'Bullet', 'Body', 'Title', 'Heading1'
    # etc. already exist in ReportLab's default stylesheet.
    styles.add(ParagraphStyle(name="ICH1", fontSize=20, leading=24,
                              textColor=PRIMARY, spaceAfter=6, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="ICSub", fontSize=10, leading=14,
                              textColor=GREY, spaceAfter=14))
    styles.add(ParagraphStyle(name="ICH2", fontSize=13, leading=16,
                              textColor=PRIMARY, spaceBefore=12, spaceAfter=6,
                              fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="ICBody", fontSize=10, leading=15,
                              textColor=colors.HexColor("#2f3445"), spaceAfter=6))
    styles.add(ParagraphStyle(name="ICBullet", fontSize=10, leading=15,
                              leftIndent=12, textColor=colors.HexColor("#2f3445"),
                              spaceAfter=3))
    return styles


def build_report_pdf(report_data: dict, narrative: str) -> bytes:
    """Return PDF bytes for the centralized organization report."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=16 * mm, bottomMargin=16 * mm,
        title="IntelliCrew Organization Report",
    )
    s = _styles()
    story = []

    # ---- header ----
    story.append(Paragraph("IntelliCrew — Organization Report", s["ICH1"]))
    story.append(Paragraph(
        f"Centralized workforce &amp; project analysis · Generated {date.today():%d %b %Y}",
        s["ICSub"],
    ))

    # ---- KPI table ----
    t = report_data["totals"]
    kpi = [
        ["Total Employees", str(t["total_employees"]),
         "Active", str(t["active_employees"])],
        ["Total Projects", str(t["total_projects"]),
         "On Bench", str(t["bench_count"])],
        ["Distinct Skills", str(t["total_skills"]), "", ""],
    ]
    kpi_table = Table(kpi, colWidths=[42 * mm, 30 * mm, 42 * mm, 30 * mm])
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#373c4b")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [LIGHT, colors.HexColor("#f5f3ff")]),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#ddd8f7")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.white),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 10))

    # ---- narrative sections (parse plain text into styled paragraphs) ----
    for block in narrative.split("\n"):
        line = block.strip()
        if not line:
            story.append(Spacer(1, 4))
            continue
        if line.endswith(":") and len(line) < 60:
            story.append(Paragraph(line[:-1], s["ICH2"]))
        elif line.startswith(("- ", "* ", "•")):
            story.append(Paragraph("• " + line.lstrip("-*• ").strip(), s["ICBullet"]))
        else:
            story.append(Paragraph(line, s["ICBody"]))

    # ---- project table ----
    story.append(Paragraph("Project Portfolio Detail", s["ICH2"]))
    header = ["Project", "Client", "Status", "Allocated"]
    rows = [header] + [
        [p["project_name"], p["client"], p["status"], str(p["allocated_count"])]
        for p in report_data["projects"]
    ]
    proj_table = Table(rows, colWidths=[62 * mm, 46 * mm, 30 * mm, 24 * mm], repeatRows=1)
    proj_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f3ff")]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e4e5ec")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(proj_table)
    story.append(Spacer(1, 10))

    # ---- top skills table ----
    story.append(Paragraph("Top Skills Across the Organization", s["ICH2"]))
    skill_rows = [["Skill", "Employees"]] + [
        [sk["skill_name"], str(sk["count"])] for sk in report_data["top_skills"]
    ]
    skill_table = Table(skill_rows, colWidths=[120 * mm, 42 * mm], repeatRows=1)
    skill_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3f8763")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef8f1")]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e4e5ec")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(skill_table)

    doc.build(story)
    buffer.seek(0)
    return buffer.read()