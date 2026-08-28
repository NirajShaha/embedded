"""PDF report generation for test cases."""

from datetime import datetime
from io import BytesIO
from typing import Any

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white, grey
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    PageBreak,
    Image,
)
from reportlab.lib import colors
from reportlab.pdfgen import canvas

from app.models import TestCase


def _format_text(text: str | None, max_length: int = 200) -> str:
    """Format text for PDF display."""
    if not text:
        return "—"
    text = str(text).strip()
    if len(text) > max_length:
        return text[:max_length] + "..."
    return text


def _build_header(pdf_doc: SimpleDocTemplate, story: list, title: str, filters_info: str) -> None:
    """Add header section to PDF."""
    styles = getSampleStyleSheet()

    # Title
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=24,
        textColor=HexColor("#1a202c"),
        spaceAfter=6,
        fontName="Helvetica-Bold",
    )
    story.append(Paragraph(title, title_style))

    # Date and info
    info_style = ParagraphStyle(
        "Info",
        parent=styles["Normal"],
        fontSize=10,
        textColor=HexColor("#718096"),
        spaceAfter=12,
    )
    generated_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    story.append(Paragraph(f"Generated on: <b>{generated_date}</b>", info_style))

    if filters_info:
        story.append(Paragraph(f"Filters Applied: <b>{filters_info}</b>", info_style))

    story.append(Spacer(1, 0.3 * inch))


def _build_test_case_section(story: list, test_case: TestCase, case_number: int) -> None:
    """Add a test case section to PDF."""
    styles = getSampleStyleSheet()

    # Test case number and title
    title_style = ParagraphStyle(
        "CaseTitle",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=HexColor("#2d3748"),
        spaceAfter=8,
        fontName="Helvetica-Bold",
    )
    story.append(Paragraph(f"Test Case #{case_number}", title_style))

    # Action/Test Case Description
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=9,
        spaceAfter=6,
        leading=12,
    )
    story.append(
        Paragraph(
            f"<b>Action/Test Case:</b> {_format_text(test_case.action_test_case, 500)}",
            body_style,
        )
    )

    # Create a table for test case details
    details_data = [
        ["Category", test_case.category.name if test_case.category else "—"],
        ["Objective", _format_text(test_case.objective.name if test_case.objective else None, 200)],
        ["Test Type", test_case.test_type.name if test_case.test_type else "—"],
        ["Severity", test_case.severity.name if test_case.severity else "—"],
        ["Asset", test_case.asset.asset_name if test_case.asset else "—"],
        ["Protocol", test_case.protocol.name if test_case.protocol else "—"],
        ["Attack Vector", test_case.attack_vector.name if test_case.attack_vector else "—"],
        ["Source/Scope Status", _format_text(test_case.source_scope_status)],
        ["Automation Possible", _format_text(test_case.automation_possible)],
    ]

    # Filter out empty details
    details_data = [[k, v] for k, v in details_data if v != "—"]

    if details_data:
        details_table = Table(details_data, colWidths=[1.8 * inch, 4.2 * inch])
        details_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), HexColor("#f7fafc")),
                    ("TEXTCOLOR", (0, 0), (-1, -1), black),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#e2e8f0")),
                    ("ROWBACKGROUNDS", (0, 0), (-1, -1), [white, HexColor("#f9fafb")]),
                ]
            )
        )
        story.append(details_table)
        story.append(Spacer(1, 0.15 * inch))

    # Description
    if test_case.description:
        story.append(
            Paragraph(
                f"<b>Description:</b> {_format_text(test_case.description, 500)}",
                body_style,
            )
        )

    # Attack Path
    if test_case.attack_path:
        story.append(
            Paragraph(
                f"<b>Attack Path:</b> {_format_text(test_case.attack_path, 500)}",
                body_style,
            )
        )

    # Test Steps
    if test_case.test_steps:
        story.append(
            Paragraph(
                f"<b>Test Steps:</b> {_format_text(test_case.test_steps, 500)}",
                body_style,
            )
        )

    # Expected Output
    if test_case.expected_output:
        story.append(
            Paragraph(
                f"<b>Expected Output:</b> {_format_text(test_case.expected_output, 500)}",
                body_style,
            )
        )

    # Attack Feasibility
    if test_case.attack_feasibility:
        story.append(
            Paragraph(
                f"<b>Attack Feasibility:</b> {_format_text(test_case.attack_feasibility, 300)}",
                body_style,
            )
        )

    # CIA Impact
    if test_case.cia_impact:
        story.append(
            Paragraph(
                f"<b>CIA Impact:</b> {_format_text(test_case.cia_impact, 300)}",
                body_style,
            )
        )

    # Safety Impact
    if test_case.safety_impact:
        story.append(
            Paragraph(
                f"<b>Safety Impact:</b> {_format_text(test_case.safety_impact, 300)}",
                body_style,
            )
        )

    # Threat
    if test_case.threat:
        story.append(
            Paragraph(
                f"<b>Threat:</b> {_format_text(test_case.threat.threat_text, 500)}",
                body_style,
            )
        )

    # Tools
    if test_case.test_case_tools:
        tools_list = ", ".join([tool.tool.tool_name for tool in test_case.test_case_tools])
        story.append(
            Paragraph(
                f"<b>Tools:</b> {_format_text(tools_list, 500)}",
                body_style,
            )
        )

    # References
    if test_case.test_case_references:
        refs_list = "; ".join([ref.reference.ref_text for ref in test_case.test_case_references])
        story.append(
            Paragraph(
                f"<b>References:</b> {_format_text(refs_list, 500)}",
                body_style,
            )
        )

    story.append(Spacer(1, 0.3 * inch))


def generate_pdf_report(
    test_cases: list[TestCase],
    category_names: list[str] | None = None,
    test_type_names: list[str] | None = None,
) -> BytesIO:
    """
    Generate a PDF report for test cases.

    Args:
        test_cases: List of TestCase objects to include in the report
        category_names: List of category names used in filtering
        test_type_names: List of test type names used in filtering

    Returns:
        BytesIO object containing the PDF data
    """
    pdf_buffer = BytesIO()

    # Create PDF document
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=letter,
        rightMargin=0.5 * inch,
        leftMargin=0.5 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
    )

    # Build the story (content)
    story = []

    # Build filters info
    filters_parts = []
    if category_names:
        filters_parts.append(f"Categories: {', '.join(category_names)}")
    if test_type_names:
        filters_parts.append(f"Test Types: {', '.join(test_type_names)}")
    filters_info = " | ".join(filters_parts) if filters_parts else "No filters applied"

    # Add header
    _build_header(doc, story, "Security Test Cases Report", filters_info)

    # Add summary
    summary_style = ParagraphStyle(
        "Summary",
        parent=getSampleStyleSheet()["Normal"],
        fontSize=11,
        textColor=HexColor("#2d3748"),
        spaceAfter=12,
        fontName="Helvetica-Bold",
    )
    story.append(
        Paragraph(
            f"Total Test Cases: <b>{len(test_cases)}</b>",
            summary_style,
        )
    )
    story.append(Spacer(1, 0.2 * inch))

    # Add test cases
    for idx, test_case in enumerate(test_cases, 1):
        _build_test_case_section(story, test_case, idx)

        # Add page break every 5 test cases for readability
        if idx % 5 == 0 and idx < len(test_cases):
            story.append(PageBreak())

    # Build PDF
    doc.build(story)
    pdf_buffer.seek(0)

    return pdf_buffer
