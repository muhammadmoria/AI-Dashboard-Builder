"""Premium PDF report generation using ReportLab."""
from __future__ import annotations
import io
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, PageBreak, Image, Flowable)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from analytics.profiler import Profile
from analytics.insights import generate_insights
from analytics.kpis import generate_kpis, format_kpi
from utils.logger import log

class HorizontalLine(Flowable):
    """Custom flowable for a horizontal line."""
    def __init__(self, width, thickness=1, color=colors.HexColor("#E5E7EB")):
        Flowable.__init__(self)
        self.width = width
        self.thickness = thickness
        self.color = color

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 0, self.width, 0)

def _header_footer(canvas, doc):
    canvas.saveState()
    # Header
    canvas.setFillColor(colors.HexColor("#7C3AED"))
    canvas.rect(0, A4[1]-1.5*cm, A4[0], 1.5*cm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 12)
    canvas.drawString(2*cm, A4[1]-1*cm, "NEXUS BI")
    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(A4[0]-2*cm, A4[1]-1*cm, "Enterprise AI Dashboard Report")
    
    # Footer
    canvas.setStrokeColor(colors.HexColor("#E5E7EB"))
    canvas.setLineWidth(1)
    canvas.line(2*cm, 1.5*cm, A4[0]-2*cm, 1.5*cm)
    canvas.setFillColor(colors.HexColor("#6B7280"))
    canvas.setFont("Helvetica", 8)
    canvas.drawString(2*cm, 1*cm, f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    canvas.drawRightString(A4[0]-2*cm, 1*cm, f"Page {doc.page}")
    canvas.restoreState()

def generate_pdf_report(df: pd.DataFrame, profile: Profile, username: str = "analyst") -> bytes:
    log.info("Generating Premium PDF report")
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2.2*cm, bottomMargin=2*cm)
    
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle("Title", parent=styles["Title"],
                                 fontSize=32, textColor=colors.HexColor("#111827"),
                                 alignment=TA_LEFT, spaceAfter=6, fontName="Helvetica-Bold")
    subtitle_style = ParagraphStyle("Sub", parent=styles["Normal"],
                                    fontSize=12, textColor=colors.HexColor("#6B7280"),
                                    alignment=TA_LEFT, spaceAfter=20)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"],
                        fontSize=18, textColor=colors.HexColor("#4F46E5"),
                        spaceBefore=20, spaceAfter=10, fontName="Helvetica-Bold")
    body = ParagraphStyle("Body", parent=styles["Normal"], fontSize=10, leading=16, 
                          textColor=colors.HexColor("#374151"), alignment=TA_JUSTIFY)
    card_title = ParagraphStyle("CardTitle", parent=styles["Normal"], fontSize=9, 
                                textColor=colors.HexColor("#6B7280"), fontName="Helvetica-Bold")
    card_val = ParagraphStyle("CardVal", parent=styles["Normal"], fontSize=16, 
                              textColor=colors.HexColor("#111827"), fontName="Helvetica-Bold")

    story: list = []

    # Cover Page
    story.append(Spacer(1, 4*cm))
    story.append(Paragraph("Data Analytics", title_style))
    story.append(Paragraph("Executive Report", ParagraphStyle("Title2", parent=title_style, textColor=colors.HexColor("#7C3AED"))))
    story.append(HorizontalLine(A4[0]-4*cm, 2, colors.HexColor("#7C3AED")))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(f"Prepared for <b>{username}</b>", subtitle_style))
    story.append(Paragraph(f"Dataset contains <b>{profile.rows:,} rows</b> and <b>{profile.cols} columns</b>.", body))
    story.append(Paragraph(f"Overall Data Quality Score: <b>{profile.quality_score:.1f}/100</b>", body))
    story.append(PageBreak())

    # Executive Summary & KPIs
    story.append(Paragraph("Executive Summary", h2))
    kpis = generate_kpis(df, profile)
    
    summary = (f"This report analyzes a dataset of <b>{profile.rows:,} rows</b> and <b>{profile.cols} columns</b>. "
               f"Data quality score: <b>{profile.quality_score:.1f}/100</b>. "
               f"Numeric columns: {len(profile.numeric_cols)}, Categorical: {len(profile.categorical_cols)}, "
               f"Datetime: {len(profile.datetime_cols)}.")
    story.append(Paragraph(summary, body))
    story.append(Spacer(1, 0.5*cm))

    # KPI Grid (Table layout)
    story.append(Paragraph("Key Performance Indicators", h2))
    kpi_items = list(kpis.items())[:6]
    kpi_data = []
    row1, row2 = [], []
    
    for i, (k, v) in enumerate(kpi_items):
        val_str = format_kpi(v) if not isinstance(v, dict) else ", ".join(f"{k2}:{v2}" for k2,v2 in list(v.items())[:2])
        cell = [Paragraph(k.upper(), card_title), Spacer(1, 4), Paragraph(val_str, card_val)]
        if i < 3: row1.append(cell)
        else: row2.append(cell)
        
    while len(row1) < 3: row1.append("")
    while len(row2) < 3: row2.append("")
        
    kpi_data = [row1, row2]
    t = Table(kpi_data, colWidths=[5.5*cm, 5.5*cm, 5.5*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#F9FAFB")),
        ("BOX", (0,0), (-1,-1), 0.5, colors.HexColor("#E5E7EB")),
        ("INNERGRID", (0,0), (-1,-1), 0.5, colors.HexColor("#E5E7EB")),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 12),
        ("RIGHTPADDING", (0,0), (-1,-1), 12),
        ("TOPPADDING", (0,0), (-1,-1), 12),
        ("BOTTOMPADDING", (0,0), (-1,-1), 12),
    ]))
    story.append(t)
    story.append(PageBreak())

    # AI Insights
    story.append(Paragraph("AI Insights & Anomalies", h2))
    insights = generate_insights(df, profile)
    
    for ins in insights:
        # Create a boxed insight
        title_html = f"<b>{ins['title']}</b> <font color='#9CA3AF' size='8'>[{ins['category']} | Confidence: {ins['confidence']*100:.0f}%]</font>"
        body_html = ins["body"]
        
        ins_table = Table([[Paragraph(title_html, body)], [Paragraph(body_html, body)]], colWidths=[16*cm])
        bg_color = colors.HexColor("#FEF3C7") if ins['severity'] == "warning" else colors.HexColor("#EFF6FF")
        border_color = colors.HexColor("#F59E0B") if ins['severity'] == "warning" else colors.HexColor("#3B82F6")
        
        ins_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), bg_color),
            ("LINEBEFORE", (0,0), (0,-1), 3, border_color),
            ("LEFTPADDING", (0,0), (-1,-1), 12),
            ("RIGHTPADDING", (0,0), (-1,-1), 12),
            ("TOPPADDING", (0,0), (-1,-1), 8),
            ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ]))
        story.append(ins_table)
        story.append(Spacer(1, 0.4*cm))

    # Column Metadata
    story.append(PageBreak())
    story.append(Paragraph("Column Metadata", h2))
    col_rows = [["Column", "Type", "Missing", "Unique", "Sample"]]
    for c in profile.columns[:15]:
        col_rows.append([c["name"], c["inferred_type"], str(c["missing"]),
                         str(c["unique"]), ", ".join(c["sample"][:2])])
    
    t2 = Table(col_rows, colWidths=[3.5*cm, 2.5*cm, 2*cm, 2*cm, 6*cm])
    t2.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#111827")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 8),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F9FAFB")]),
        ("GRID", (0,0), (-1,-1), 0.25, colors.HexColor("#E5E7EB")),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
    ]))
    story.append(t2)

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return buf.getvalue()