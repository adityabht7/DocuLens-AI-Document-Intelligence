"""Script to generate realistic sample PDF documents for DocuLens
Generates:
1. Research_Paper_AI_RAG.pdf (Academic & Research)
2. Research_Paper_Quantum.pdf (Academic & Research)
3. Government_Economic_Survey.pdf (Government / Public Policy)
4. Government_Education_Policy.pdf (Government / Public Policy)
5. Corporate_Annual_Report_2025.pdf (Financial / Business)
6. Q3_Financial_Earnings_TechCorp.pdf (Financial / Business)
7. Employee_Leave_and_Ethics_Policy.pdf (Policy & Compliance)
8. Edge_Case_Test_Doc.pdf (Controlled test cases)
"""
import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib import colors

DOCS_DIR = Path(__file__).resolve().parent.parent / "sample_docs"
DOCS_DIR.mkdir(parents=True, exist_ok=True)


def build_pdf(filename: str, pages_content: list):
    filepath = DOCS_DIR / filename
    doc = SimpleDocTemplate(
        str(filepath),
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#1E293B'),
        spaceAfter=12
    )
    h2_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#0F172A'),
        spaceBefore=10,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['BodyText'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#334155'),
        spaceAfter=8
    )

    story = []
    for page_idx, page_sections in enumerate(pages_content):
        for section in page_sections:
            sec_type = section.get("type", "p")
            text = section.get("text", "")
            if sec_type == "title":
                story.append(Paragraph(text, title_style))
            elif sec_type == "h2":
                story.append(Paragraph(text, h2_style))
            else:
                story.append(Paragraph(text, body_style))
            story.append(Spacer(1, 4))
        
        # Add PageBreak except on last page
        if page_idx < len(pages_content) - 1:
            story.append(PageBreak())

    doc.build(story)
    print(f"Generated: {filepath.name} ({len(pages_content)} pages)")


def generate_all():
    # 1. Research_Paper_AI_RAG.pdf (3 pages)
    build_pdf("Research_Paper_AI_RAG.pdf", [
        # Page 1
        [
            {"type": "title", "text": "Retrieval-Augmented Generation in Specialized Domains: A Survey"},
            {"type": "h2", "text": "1. Abstract & Introduction"},
            {"type": "p", "text": "Abstract: Large Language Models (LLMs) often suffer from factual hallucinations and knowledge cutoff limitations. Retrieval-Augmented Generation (RAG) addresses these vulnerabilities by fetching verified evidence from a dynamic vector database. In this empirical study, we evaluate hybrid retrieval mechanisms combining dense sentence embeddings with lexical BM25 matching across technical corpora."},
            {"type": "p", "text": "Our experimental pipeline utilizes all-MiniLM-L6-v2 embeddings generating 384-dimensional dense vectors stored within ChromaDB. Baseline evaluations show that dense retrieval alone achieves 78.4% Recall@5, whereas hybrid retrieval enhances Recall@5 to 89.2% on domain queries."}
        ],
        # Page 2
        [
            {"type": "h2", "text": "2. Methodology and Chunking Analysis"},
            {"type": "p", "text": "Document chunking strategy plays a decisive role in retrieval precision. When text chunks are oversized (> 1000 characters), embedding dilution occurs, lowering similarity scores for fine-grained factual queries."},
            {"type": "p", "text": "Conversely, undersized chunks (< 150 characters) fail to encapsulate full semantic context. Our optimal configuration employs 500-character chunks with an 80-character sliding overlap, preserving sentence boundaries and mitigating contextual boundary loss."}
        ],
        # Page 3
        [
            {"type": "h2", "text": "3. Experimental Results and Conclusion"},
            {"type": "p", "text": "The primary research finding is that prompt injection defense can be strengthened by explicitly demarcating external passages using XML tags and enforcing strict instruction grounding. Models instructed with source verification exhibited a 92% reduction in ungrounded assertions."},
            {"type": "p", "text": "Conclusion: Source-grounded RAG architectures offer enterprise-grade auditability while drastically minimizing generative hallucinations across specialized knowledge bases."}
        ]
    ])

    # 2. Corporate_Annual_Report_2025.pdf (3 pages)
    build_pdf("Corporate_Annual_Report_2025.pdf", [
        # Page 1
        [
            {"type": "title", "text": "Apex Global Innovations Inc. - Annual Report Fiscal Year 2025"},
            {"type": "h2", "text": "1. Letter to Shareholders"},
            {"type": "p", "text": "Fiscal Year 2025 has been a transformative period for Apex Global Innovations. Driven by accelerated adoption of enterprise AI and cloud automation platforms, our consolidated total revenue reached $14.8 billion, representing a 22.4% year-over-year increase compared to Fiscal Year 2024."},
            {"type": "p", "text": "Operating cash flow expanded to $3.6 billion, providing robust liquidity for our strategic cloud infrastructure investments in North America and Europe."}
        ],
        # Page 2
        [
            {"type": "h2", "text": "2. Financial Performance & Revenue Breakdown"},
            {"type": "p", "text": "Segment Performance: The Cloud & AI Enterprise segment contributed $8.2 billion (55.4% of total revenue). Digital Services generated $4.1 billion, while Hardware and Embedded Solutions accounted for $2.5 billion."},
            {"type": "p", "text": "Operating expenses were managed prudently at $6.1 billion. Research and Development (R&D) expenditure reached $2.3 billion, concentrated on proprietary generative workflow engines and edge compute microservices."}
        ],
        # Page 3
        [
            {"type": "h2", "text": "3. Balance Sheet & Dividend Announcement"},
            {"type": "p", "text": "Total assets stood at $31.4 billion against total liabilities of $12.1 billion, resulting in a solid stockholders equity of $19.3 billion. The Board of Directors declared an annual dividend of $1.85 per common share payable on April 15, 2026."}
        ]
    ])

    # 3. Employee_Leave_and_Ethics_Policy.pdf (2 pages)
    build_pdf("Employee_Leave_and_Ethics_Policy.pdf", [
        # Page 1
        [
            {"type": "title", "text": "Global Operations - Employee Leave and Workplace Ethics Policy"},
            {"type": "h2", "text": "1. Annual Leave and Time-Off Entitlement"},
            {"type": "p", "text": "All full-time employees are entitled to 24 business days of paid annual leave per calendar year. Leave accrues on a pro-rata basis at 2.0 days per completed month of continuous service."},
            {"type": "p", "text": "Application Procedure: Employees must submit leave requests through the internal portal at least 10 business days in advance for absences exceeding three consecutive days. Line manager approval is mandatory prior to travel confirmation."}
        ],
        # Page 2
        [
            {"type": "h2", "text": "2. Parental Leave, Medical Absence & Code of Conduct"},
            {"type": "p", "text": "Eligible primary caregivers receive up to 16 weeks of fully paid parental leave, accessible within the first twelve months following birth or adoption. Secondary caregivers are entitled to 6 weeks of paid parental leave."},
            {"type": "p", "text": "Medical Leave: Employees can take up to 12 days of paid sick leave annually without loss of compensation. A medical practitioner certificate is required for medical absences lasting greater than three consecutive days."}
        ]
    ])

    # 4. Government_Economic_Survey.pdf (2 pages)
    build_pdf("Government_Economic_Survey.pdf", [
        # Page 1
        [
            {"type": "title", "text": "National Economic Survey & Macroeconomic Outlook 2025-2026"},
            {"type": "h2", "text": "1. Macroeconomic Growth Indicators"},
            {"type": "p", "text": "The national economy demonstrated resilience in 2025, recording real Gross Domestic Product (GDP) growth of 6.8%, compared to 6.2% in the preceding fiscal period. Inflationary pressures moderated, with the headline Consumer Price Index (CPI) averaging 4.2%."},
            {"type": "p", "text": "Gross capital formation expanded by 9.1%, driven by state-sponsored infrastructure investments in transportation corridors and high-speed broadband backbones."}
        ],
        # Page 2
        [
            {"type": "h2", "text": "2. Renewable Energy Transition & Fiscal Deficit"},
            {"type": "p", "text": "Renewable energy capacity surpassed 180 gigawatts (GW), with solar installations contributing 62% of newly commissioned power utilities. The government reiterated its target to achieve 500 GW of non-fossil energy capacity by 2030."},
            {"type": "p", "text": "The central fiscal deficit for the year settled at 4.9% of GDP, meeting the statutory consolidation target established by the Fiscal Responsibility and Budget Management roadmap."}
        ]
    ])

    # 5. Edge_Case_Test_Doc.pdf (1 page)
    build_pdf("Edge_Case_Test_Doc.pdf", [
        [
            {"type": "title", "text": "DocuLens Edge Case Testing & System Diagnostics Document"},
            {"type": "h2", "text": "1. Verification Markers"},
            {"type": "p", "text": "Special Verification Code: ALPHA-OMEGA-9942. The emergency contact protocol frequency is set to 433.92 MHz."},
            {"type": "p", "text": "Confidential Security Clause: Unauthorized redistribution is strictly prohibited under Federal Code Section 884-B."}
        ]
    ])


if __name__ == "__main__":
    generate_all()
