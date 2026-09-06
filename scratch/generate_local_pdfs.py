import os
import json
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

DOCS_DIR = Path("data/documents")
DOCS_DIR.mkdir(parents=True, exist_ok=True)

KNOWLEDGE_DIR = Path("data/knowledge")

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
    
    # Header tag
    elements.append(Paragraph("OFFICIAL AUTHORISED KNOWLEDGE DOCUMENT ARCHIVE", ParagraphStyle('HeaderTag', fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=colors.HexColor('#2563eb'))))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(title, title_style))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#1e3a8a'), spaceAfter=12))
    
    # Metadata Table
    meta_text = f"<b>Issuing Authority:</b> {org} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Type:</b> {doc_type.upper()} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Jurisdiction:</b> {jurisdiction.upper()}<br/><b>Document ID:</b> {doc_key} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Publication Date:</b> {pub_date}"
    elements.append(Paragraph(meta_text, meta_style))
    elements.append(Spacer(1, 10))
    
    # Section Heading
    elements.append(Paragraph("Statutory & Regulatory Provisions", heading_style))
    
    # Main Content
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
    # Map of document configurations
    documents = [
        {
            "keys": ["ayush_rule_158b", "doc_ayush_rule_158b"],
            "title": "Drugs and Cosmetics Rules, 1945 — Rule 158-B Licensing Requirements for ASU Drugs",
            "org": "Ministry of AYUSH / Central Drugs Standard Control Organization",
            "doc_type": "rule",
            "jurisdiction": "india",
            "url": "https://www.ayush.gov.in/docs/asu-l-rules.pdf",
            "pub_date": "2010-08-10",
            "kb_file": "doc_ayush_rule_158b.json"
        },
        {
            "keys": ["ayush_form_24d", "doc_ayush_form_24d"],
            "title": "Form 24D Application Procedure and Checklist for ASU Manufacturing License",
            "org": "Ministry of AYUSH",
            "doc_type": "rule",
            "jurisdiction": "india",
            "url": "https://www.ayush.gov.in/regulatory-framework",
            "pub_date": "2010-08-10",
            "kb_file": "doc_ayush_form_24d.json"
        },
        {
            "keys": ["ip_india_patents_act_3p", "doc_patents_act_3p", "patents_act_3p"],
            "title": "The Patents Act, 1970 — Section 3(p) Inventions Not Patentable",
            "org": "Office of the Controller General of Patents, Designs and Trade Marks",
            "doc_type": "act",
            "jurisdiction": "india",
            "url": "https://www.ipindia.gov.in/patents.htm",
            "pub_date": "1970-09-19",
            "kb_file": "doc_patents_act_3p.json"
        },
        {
            "keys": ["biodiversity_act_2002", "doc_biodiversity_act_2002"],
            "title": "The Biological Diversity Act, 2002 — Access and Benefit Sharing (ABS) Provisions",
            "org": "National Biodiversity Authority / MoEFCC",
            "doc_type": "act",
            "jurisdiction": "india",
            "url": "https://www.indiacode.nic.in/handle/123456789/2046",
            "pub_date": "2003-02-05",
            "kb_file": "doc_biodiversity_act_2002.json"
        },
        {
            "keys": ["nba_abs_regulations_2014", "doc_nba_abs_regulations_2014"],
            "title": "Guidelines on Access to Biological Resources and Associated Knowledge Regulations 2014",
            "org": "National Biodiversity Authority",
            "doc_type": "regulation",
            "jurisdiction": "india",
            "url": "https://nbaindia.org/uploaded/pdf/ABS_Regulations_2014.pdf",
            "pub_date": "2014-11-21",
            "kb_file": "doc_nba_abs_regulations_2014.json"
        },
        {
            "keys": ["tkdl_wipo_policy", "doc_tkdl_wipo_policy"],
            "title": "WIPO Traditional Knowledge Digital Library (TKDL) & IP Protection Framework",
            "org": "World Intellectual Property Organization / CSIR",
            "doc_type": "database_entry",
            "jurisdiction": "both",
            "url": "https://www.wipo.int/tk/en/databases/tkdl.html",
            "pub_date": "2018-05-14",
            "kb_file": "doc_tkdl_wipo_policy.json"
        }
    ]

    for d in documents:
        kb_path = KNOWLEDGE_DIR / d["kb_file"]
        content = ""
        if kb_path.exists():
            with kb_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
                content = data.get("content", "")

        for key in d["keys"]:
            outfile = DOCS_DIR / f"{key}.pdf"
            generate_pdf(
                doc_key=key,
                title=d["title"],
                org=d["org"],
                doc_type=d["doc_type"],
                jurisdiction=d["jurisdiction"],
                url=d["url"],
                pub_date=d["pub_date"],
                content=content,
                outfile=outfile
            )

if __name__ == "__main__":
    main()
