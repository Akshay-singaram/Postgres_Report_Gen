"""
PDF Report Generator for Equipment Maintenance Tracker.

Uses ReportLab to produce a professional maintenance report with:
- Summary table with color-coded status rows
- Progress bars for % consumed
- Notes section
- Page headers and footers
"""

from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.graphics.shapes import Drawing, Rect


# ---------------------------------------------------------------------------
# Color constants
# ---------------------------------------------------------------------------
COLOR_RED = colors.Color(1.0, 0.8, 0.8)       # light red
COLOR_YELLOW = colors.Color(1.0, 1.0, 0.75)   # light yellow
COLOR_GREEN = colors.Color(0.8, 1.0, 0.8)      # light green
COLOR_ALT = colors.Color(0.95, 0.95, 0.95)     # alternating row shade
COLOR_HEADER = colors.Color(0.2, 0.3, 0.5)     # header background


def _status_color(result: dict) -> colors.Color:
    """Return the row background color based on alert status."""
    if result["alert_critical"]:
        return COLOR_RED
    elif result["alert_warning"]:
        return COLOR_YELLOW
    return COLOR_GREEN


def _status_label(result: dict) -> str:
    if result["alert_critical"]:
        return "CRITICAL"
    elif result["alert_warning"]:
        return "WARNING"
    return "OK"


def _progress_bar(pct: float, width=60, height=10) -> Drawing:
    """Create a small progress bar Drawing for the % consumed column."""
    d = Drawing(width, height)
    # Background
    d.add(Rect(0, 0, width, height, fillColor=colors.Color(0.85, 0.85, 0.85),
               strokeColor=colors.grey, strokeWidth=0.5))
    # Filled portion
    fill_width = min(max(pct / 100.0, 0), 1.0) * width
    if pct >= 90:
        fill_color = colors.Color(0.9, 0.2, 0.2)
    elif pct >= 75:
        fill_color = colors.Color(0.9, 0.75, 0.1)
    else:
        fill_color = colors.Color(0.2, 0.7, 0.3)
    d.add(Rect(0, 0, fill_width, height, fillColor=fill_color,
               strokeColor=None, strokeWidth=0))
    return d


def _format_date(dt) -> str:
    if dt is None:
        return "N/A"
    if isinstance(dt, datetime):
        return dt.strftime("%Y-%m-%d")
    return str(dt)


# ---------------------------------------------------------------------------
# Page header/footer callbacks
# ---------------------------------------------------------------------------
def _header_footer(canvas, doc, generated_dt: datetime):
    """Draw header and footer on every page."""
    canvas.saveState()
    page_width, page_height = landscape(A4)

    # Header
    canvas.setFont("Helvetica-Bold", 16)
    canvas.drawString(30, page_height - 35, "Facility Maintenance Report")
    canvas.setFont("Helvetica", 9)
    canvas.drawString(30, page_height - 50,
                      f"Generated: {generated_dt.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    canvas.drawString(30, page_height - 62,
                      f"As of: {generated_dt.strftime('%Y-%m-%d')}")

    # Footer
    canvas.setFont("Helvetica", 8)
    canvas.drawString(30, 20,
                      f"Page {doc.page}  |  Generated: {generated_dt.strftime('%Y-%m-%d %H:%M:%S UTC')}  |  Confidential — Internal Use Only")

    canvas.restoreState()


# ---------------------------------------------------------------------------
# Main generation function
# ---------------------------------------------------------------------------
def generate_report(results: list, filepath: str, generated_dt: datetime):
    """Generate the PDF maintenance report and save to filepath."""

    page_width, page_height = landscape(A4)
    styles = getSampleStyleSheet()

    # Build the document
    doc = BaseDocTemplate(
        filepath,
        pagesize=landscape(A4),
        leftMargin=20,
        rightMargin=20,
        topMargin=75,
        bottomMargin=40,
    )

    frame = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        page_width - doc.leftMargin - doc.rightMargin,
        page_height - doc.topMargin - doc.bottomMargin,
        id="main",
    )

    def on_page(canvas, doc):
        _header_footer(canvas, doc, generated_dt)

    template = PageTemplate(id="report", frames=frame, onPage=on_page)
    doc.addPageTemplates([template])

    story = []

    # ------------------------------------------------------------------
    # Summary table
    # ------------------------------------------------------------------
    col_style = styles["Normal"]
    col_style.fontSize = 7
    col_style.leading = 9

    header_style = styles["Normal"].clone("header_style")
    header_style.fontSize = 7
    header_style.leading = 9
    header_style.textColor = colors.white
    header_style.fontName = "Helvetica-Bold"

    headers = [
        "Equip ID",
        "Label",
        "Last Maint.",
        "Hrs Since\nMaint.",
        "Lifetime\nHrs",
        "Interval\n(hrs)",
        "Hrs\nRemaining",
        "% Consumed",
        "Progress",
        "Projected\nNext Maint.",
        "Status",
    ]

    table_data = [[Paragraph(h, header_style) for h in headers]]

    for r in results:
        row = [
            Paragraph(r["id"], col_style),
            Paragraph(r["label"], col_style),
            Paragraph(_format_date(r["last_maintenance"]), col_style),
            Paragraph(str(r["run_hours_since_maintenance"]), col_style),
            Paragraph(str(r["run_hours_lifetime"]), col_style),
            Paragraph(str(r["maintenance_interval_hours"]), col_style),
            Paragraph(str(r["hours_remaining"]), col_style),
            Paragraph(f"{r['pct_consumed']}%", col_style),
            _progress_bar(r["pct_consumed"]),
            Paragraph(_format_date(r.get("projected_maintenance_date")), col_style),
            Paragraph(_status_label(r), col_style),
        ]
        table_data.append(row)

    col_widths = [55, 100, 60, 48, 48, 48, 48, 48, 65, 65, 50]

    table = Table(table_data, colWidths=col_widths, repeatRows=1)

    # Build style commands
    style_cmds = [
        # Header row
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_HEADER),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 7),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        # All cells
        ("FONTNAME", (0, 1), (-1, -1), "Courier"),
        ("FONTSIZE", (0, 1), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("TOPPADDING", (0, 1), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 3),
    ]

    # Row color coding — status colors with subtle alternating shade overlay
    for i, r in enumerate(results):
        row_idx = i + 1  # skip header
        bg = _status_color(r)
        # Blend with alternating shade for even rows
        if i % 2 == 1:
            bg = colors.Color(
                bg.red * 0.95,
                bg.green * 0.95,
                bg.blue * 0.95,
            )
        style_cmds.append(("BACKGROUND", (0, row_idx), (-1, row_idx), bg))

    table.setStyle(TableStyle(style_cmds))
    story.append(table)

    # ------------------------------------------------------------------
    # Notes section
    # ------------------------------------------------------------------
    notes = [(r["id"], r["notes"]) for r in results if r.get("notes")]
    if notes:
        story.append(Spacer(1, 15))
        note_title_style = styles["Heading3"]
        note_title_style.fontSize = 10
        story.append(Paragraph("Equipment Notes", note_title_style))

        note_style = styles["Normal"].clone("note_style")
        note_style.fontSize = 8
        note_style.fontName = "Courier"
        note_style.leading = 12

        for equip_id, note_text in notes:
            story.append(Paragraph(f"<b>{equip_id}:</b> {note_text}", note_style))

    # Build the PDF
    doc.build(story)
