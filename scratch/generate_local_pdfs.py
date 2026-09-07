import os
import json
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

DOCS_DIR = Path("data/documents")
DOCS_DIR.mkdir(parents=True, exist_ok=True)

KNOWLEDGE_DIR = Path("data/knowledge")
SOURCES_CONFIG = Path("config/sources.json")

def generate_pdf(doc_key, title, org, doc_type, jurisdiction, url, pub_date, content, outfile):
    doc = SimpleDocTemplate(
        str(outfile),
        pagesize=letter,
        rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54
    )
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#1e3a8a'),
        spaceAfter=10
    )
    
    meta_style = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#475569'),
        spaceAfter=15
    )
    
    heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#1e3a8a'),
        spaceBefore=15,
        spaceAfter=8
    )

    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=10.5,
        leading=15,
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=12
    )

    footer_style = ParagraphStyle(
        'FooterText',
        parent=styles['Italic'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#64748b'),
        spaceBefore=20
    )

    elements = []
    
    elements.append(Paragraph("OFFICIAL AUTHORISED KNOWLEDGE DOCUMENT ARCHIVE", ParagraphStyle('HeaderTag', fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=colors.HexColor('#2563eb'))))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(title, title_style))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#1e3a8a'), spaceAfter=12))
    
    meta_text = f"<b>Issuing Authority:</b> {org} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Type:</b> {doc_type.upper()} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Jurisdiction:</b> {jurisdiction.upper()}<br/><b>Document ID:</b> {doc_key} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Publication Date:</b> {pub_date}"
    elements.append(Paragraph(meta_text, meta_style))
    elements.append(Spacer(1, 10))
    
    elements.append(Paragraph("Statutory & Regulatory Provisions", heading_style))
    
    paragraphs = content.split("\n")
    for p in paragraphs:
        if p.strip():
            elements.append(Paragraph(p.strip(), body_style))
            
    elements.append(Spacer(1, 15))
    elements.append(HRFlowable(width="100%", thickness=0.75, color=colors.HexColor('#cbd5e1'), spaceBefore=10, spaceAfter=10))
    elements.append(Paragraph(f"<b>Official Statutory URL:</b> {url}<br/><i>Archived locally by IP-SAKTI Sahayak per AGENTS.md statutory decision support requirements.</i>", footer_style))

    doc.build(elements)
    print(f"Generated PDF: {outfile}")

def main():
    with open(SOURCES_CONFIG, "r", encoding="utf-8") as f:
        sources_list = json.load(f)
    
    source_map = {s["source_id"]: s for s in sources_list}

    documents = [
        {
            "keys": ["ayush_rule_158b", "doc_ayush_rule_158b"],
            "source_id": "ayush_rule_158b",
            "kb_file": "doc_ayush_rule_158b.json"
        },
        {
            "keys": ["ayush_form_24d", "doc_ayush_form_24d"],
            "source_id": "ayush_form_24d",
            "kb_file": "doc_ayush_form_24d.json"
        },
        {
            "keys": ["ip_india_patents_act_3p", "doc_patents_act_3p", "patents_act_3p"],
            "source_id": "ip_india_patents_act_3p",
            "kb_file": "doc_patents_act_3p.json"
        },
        {
            "keys": ["biodiversity_act_2002", "doc_biodiversity_act_2002"],
            "source_id": "biodiversity_act_2002",
            "kb_file": "doc_biodiversity_act_2002.json"
        },
        {
            "keys": ["nba_abs_regulations_2014", "doc_nba_abs_regulations_2014"],
            "source_id": "nba_abs_regulations_2014",
            "kb_file": "doc_nba_abs_regulations_2014.json"
        },
        {
            "keys": ["tkdl_wipo_policy", "doc_tkdl_wipo_policy"],
            "source_id": "tkdl_wipo_policy",
            "kb_file": "doc_tkdl_wipo_policy.json"
        },
        {
            "keys": ["ip_india_ayush_guidelines_2025", "doc_ip_india_ayush_guidelines_2025"],
            "source_id": "ip_india_ayush_guidelines_2025",
            "kb_file": "doc_ip_india_ayush_guidelines_2025.json"
        }
    ]

    for d in documents:
        kb_path = KNOWLEDGE_DIR / d["kb_file"]
        content = ""
        title = ""
        org = ""
        doc_type = ""
        jurisdiction = ""
        pub_date = ""
        url = ""

        if d["source_id"] in source_map:
            sm = source_map[d["source_id"]]
            title = sm["title"]
            org = sm["organisation"]
            doc_type = sm["source_type"]
            jurisdiction = sm["jurisdiction"]
            url = sm["url"]
            pub_date = sm.get("publication_date", "")

        if kb_path.exists():
            with kb_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
                content = data.get("content", "")
                if not title and data.get("title"):
                    title = data.get("title")

        for key in d["keys"]:
            outfile = DOCS_DIR / f"{key}.pdf"
            generate_pdf(
                doc_key=key,
                title=title,
                org=org,
                doc_type=doc_type,
                jurisdiction=jurisdiction,
                url=url,
                pub_date=pub_date,
                content=content,
                outfile=outfile
            )

if __name__ == "__main__":
    main()
