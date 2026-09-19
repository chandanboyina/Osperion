from __future__ import annotations

from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether

def _text(value) -> str:
    return str(value if value is not None else "")

def _safe(value, limit: int = 1800) -> str:
    value = _text(value)
    return value if len(value) <= limit else value[:limit] + "…"

def _p(value, style) -> Paragraph:
    return Paragraph(_safe(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"), style)

def build_investigation_pdf(snapshot: dict) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm,
        topMargin=15*mm, bottomMargin=15*mm,
        title=f"OSPERION Investigation Report — {snapshot['investigation']['name']}",
        author="OSPERION",
    )
    styles = getSampleStyleSheet()
    title = ParagraphStyle("ReportTitle", parent=styles["Title"], alignment=TA_CENTER, spaceAfter=8)
    subtitle = ParagraphStyle("Subtitle", parent=styles["Normal"], alignment=TA_CENTER, textColor=colors.HexColor("#555555"), spaceAfter=16)
    h1 = ParagraphStyle("ReportH1", parent=styles["Heading1"], spaceBefore=10, spaceAfter=7)
    h2 = ParagraphStyle("ReportH2", parent=styles["Heading2"], spaceBefore=8, spaceAfter=5)
    body = ParagraphStyle("ReportBody", parent=styles["BodyText"], leading=14, spaceAfter=5)
    small = ParagraphStyle("ReportSmall", parent=styles["BodyText"], fontSize=8, leading=10)
    mono = ParagraphStyle("ReportMono", parent=small, fontName="Courier")
    story = []
    inv = snapshot["investigation"]
    stats = snapshot["stats"]
    evidence = snapshot["evidence"]
    entries = snapshot["entries"]
    images = snapshot["images"]

    story += [
        Paragraph("OSPERION", title),
        Paragraph("Investigation Report", h1),
        Paragraph(_safe(inv["name"]), subtitle),
        Paragraph("<b>Description</b>", h2),
        _p(inv.get("description") or "No description provided.", body),
    ]

    summary = [
        ["Investigation ID", _text(inv["investigation_id"])],
        ["Created", _text(inv["created_at"])],
        ["Last updated", _text(inv["updated_at"])],
        ["Report generated", _text(snapshot["generated_at"])],
        ["Saved evidence", _text(stats["evidence"])],
        ["Extracted artifacts", _text(stats["artifacts"])],
        ["Saved images", _text(stats["images"])],
        ["Journal entries", _text(len(entries))],
    ]
    story.append(Paragraph("Investigation Summary", h2))
    t = Table(summary, colWidths=[48*mm, 125*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(0,-1),colors.HexColor("#eeeeee")),
        ("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#cccccc")),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),
        ("FONTSIZE",(0,0),(-1,-1),8),
        ("LEFTPADDING",(0,0),(-1,-1),5),("RIGHTPADDING",(0,0),(-1,-1),5),
        ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
    ]))
    story += [t, Spacer(1,8)]

    if stats.get("platforms"):
        platforms = ", ".join(f"{_text(p['platform'])}: {p['n']}" for p in stats["platforms"])
        story.append(_p(f"<b>Evidence by platform:</b> {platforms}", body))

    story.append(Paragraph("Evidence Inventory", h1))
    if not evidence:
        story.append(Paragraph("No saved evidence is currently attached to this investigation.", body))
    else:
        rows = [["ID","Created","Platform","Filename","Artifacts","Parser"]]
        for e in evidence:
            rows.append([_text(e["evidence_id"]),_safe(e["created_at"],30),_safe(e["platform"],24),
                         _safe(e["filename"],38),_text(e["artifact_count"]),_safe(e["parser_version"],22)])
        et = Table(rows, colWidths=[10*mm,31*mm,22*mm,53*mm,17*mm,27*mm], repeatRows=1)
        et.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#222222")),
            ("TEXTCOLOR",(0,0),(-1,0),colors.white),
            ("GRID",(0,0),(-1,-1),0.35,colors.HexColor("#cccccc")),
            ("FONTSIZE",(0,0),(-1,-1),7),("VALIGN",(0,0),(-1,-1),"TOP"),
            ("LEFTPADDING",(0,0),(-1,-1),3),("RIGHTPADDING",(0,0),(-1,-1),3),
            ("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3),
        ]))
        story.append(et)
        for e in evidence:
            story.append(KeepTogether([
                Paragraph(f"Evidence #{_text(e['evidence_id'])}", h2),
                _p(f"<b>File:</b> {_safe(e['filename'])}", body),
                _p(f"<b>Platform:</b> {_safe(e['platform'])} &nbsp; <b>Created:</b> {_safe(e['created_at'])}", body),
                _p(f"<b>SHA-256:</b> {_safe(e['sha256'])}", mono),
                _p(f"<b>Parser:</b> {_safe(e['parser_version'])}", body),
            ]))
            artifacts = e.get("artifacts", [])
            if artifacts:
                rows = [["Confidence","Type","Value","Context","Location"]]
                for a in artifacts:
                    rows.append([_safe(a["confidence"],16),_safe(a["type"],24),_safe(a["value"],55),
                                 _safe(a["context"],45),_safe(a["location"],30)])
                at = Table(rows, colWidths=[20*mm,25*mm,58*mm,42*mm,28*mm], repeatRows=1)
                at.setStyle(TableStyle([
                    ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#444444")),
                    ("TEXTCOLOR",(0,0),(-1,0),colors.white),
                    ("GRID",(0,0),(-1,-1),0.3,colors.HexColor("#cccccc")),
                    ("FONTSIZE",(0,0),(-1,-1),6.5),("VALIGN",(0,0),(-1,-1),"TOP"),
                    ("LEFTPADDING",(0,0),(-1,-1),2),("RIGHTPADDING",(0,0),(-1,-1),2),
                    ("TOPPADDING",(0,0),(-1,-1),2),("BOTTOMPADDING",(0,0),(-1,-1),2),
                ]))
                story.append(at)
            else:
                story.append(Paragraph("No artifacts recorded for this evidence item.", small))

    story += [PageBreak(), Paragraph("Research Journal", h1)]
    if not entries:
        story.append(Paragraph("No notes, reports, or remarks are saved in this investigation.", body))
    else:
        for entry in entries:
            story.append(Paragraph(f"{_text(entry['entry_type']).upper()}: {_safe(entry['title'])}", h2))
            story.append(_p(f"<b>Created:</b> {_safe(entry['created_at'])} &nbsp; <b>Updated:</b> {_safe(entry['updated_at'])}", small))
            content = _safe(entry["content"], 6000).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace("\n","<br/>")
            story.append(Paragraph(content, body))
            story.append(Spacer(1,5))

    story.append(Paragraph("Saved Image Evidence", h1))
    if not images:
        story.append(Paragraph("No saved profile/media images are attached to this investigation.", body))
    else:
        rows = [["ID","Created","Label","Platform","SHA-256","pHash","Size"]]
        for image in images:
            rows.append([_text(image["image_id"]),_safe(image["created_at"],30),
                         _safe(image["label"] or image["filename"],30),_safe(image["platform"],18),
                         _safe(image["sha256"],22),_safe(image["phash"],18),
                         f"{image['width']}×{image['height']} / {image['byte_size']} B"])
        it = Table(rows, colWidths=[9*mm,28*mm,38*mm,22*mm,30*mm,25*mm,27*mm], repeatRows=1)
        it.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#222222")),
            ("TEXTCOLOR",(0,0),(-1,0),colors.white),
            ("GRID",(0,0),(-1,-1),0.3,colors.HexColor("#cccccc")),
            ("FONTSIZE",(0,0),(-1,-1),6.5),("VALIGN",(0,0),(-1,-1),"TOP"),
            ("LEFTPADDING",(0,0),(-1,-1),2),("RIGHTPADDING",(0,0),(-1,-1),2),
            ("TOPPADDING",(0,0),(-1,-1),2),("BOTTOMPADDING",(0,0),(-1,-1),2),
        ]))
        story.append(it)

    story += [
        Paragraph("Interpretation & Accuracy Note", h1),
        Paragraph(
            "OSPERION records observable artifacts and correlations from evidence supplied by the user. "
            "A match means an artifact was previously observed; it is not proof that two accounts or artifacts "
            "belong to the same real-world person. Stable identifiers can provide strong artifact matches, while "
            "usernames, CDN filenames and perceptual image similarity are correlation signals that require validation. "
            "Exact SHA-256 matches indicate identical file bytes. This report is a point-in-time export of information "
            "saved in the investigation when the report was generated. Temporary, unsaved analysis is not included.",
            body
        ),
    ]

    def footer(canvas, doc_obj):
        canvas.saveState()
        canvas.setFont("Helvetica",7)
        canvas.setFillColor(colors.HexColor("#666666"))
        canvas.drawString(15*mm,8*mm,"OSPERION — Local-first digital evidence correlation and investigation workspace")
        canvas.drawRightString(A4[0]-15*mm,8*mm,f"Page {doc_obj.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buffer.getvalue()
