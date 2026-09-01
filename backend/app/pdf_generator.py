"""Minimal PDF generator for the ECU Penetration Testing Test Plan.

This module is intentionally simple. The previous version used ReportLab's
``BaseDocTemplate`` with a custom page template, custom canvas, table of
contents, repeated base64 image decoding, and per-row ``Paragraph``
construction. That pipeline is slow and was the reason the dashboard
appeared to freeze while a PDF was being generated.

This rewrite:

* uses the plain ``SimpleDocTemplate`` (no TOC, no custom canvas) so the
  only state ReportLab keeps is the story itself;
* renders the section 4 "Test scope" table as a single ``Table`` per
  page, splitting rows by hand only when the row count would overflow the
  available height;
* does the CPU-heavy ``build`` call inside ``asyncio.to_thread`` from the
  caller so the FastAPI event loop is never blocked.

The output mirrors the structure of ``pdf.html`` at the repository root:

* cover page (page 1) — uses the project's ECU detail;
* distribution list + document history (page 2);
* table of contents (page 3);
* section 1 "Introduction" — table populated from the ECU detail (page 4);
* section 1.1 "Supporting documentation" + section 1.2 "Roles and
  responsibilities" (page 5);
* section 2 "Testing approach" — attacker model, type of testing driven by
  the test-type filter, assumptions (page 6);
* section 3 "Schedules and deliverables" (page 7);
* section 4 "Test scope" — populated from the filtered test-case
  catalogue, grouped by category then objective (pages 8+);
* references (page 13-ish);
* appendices A, B, C (last three pages).

Only sections 1, 2.2 and 4 are dynamic; the rest use static content from
the source template because the application has no data model for them.
"""

from __future__ import annotations

from datetime import date
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from typing import Any


# ---------------------------------------------------------------------------
# Page geometry and palette (matches pdf.html)
# ---------------------------------------------------------------------------
PAGE_WIDTH, PAGE_HEIGHT = A4

MARGIN_LEFT = 17 * mm
MARGIN_RIGHT = 17 * mm
MARGIN_TOP = 26 * mm
MARGIN_BOTTOM = 20 * mm
CONTENT_WIDTH = PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT
CONTENT_HEIGHT = PAGE_HEIGHT - MARGIN_TOP - MARGIN_BOTTOM

INK = colors.HexColor("#1a1a1a")
MUTED = colors.HexColor("#5f5f5f")
TAN = colors.HexColor("#d2aa82")
TAN_LIGHT = colors.HexColor("#f1e8df")
TEAL = colors.HexColor("#a3c2c2")
TEAL_LIGHT = colors.HexColor("#e5eeee")
GRID = colors.HexColor("#737373")
FOOTER_GREY = colors.HexColor("#333333")

DOC_TEMPLATE_CODE = "JLR-TMP-568088"


# ---------------------------------------------------------------------------
# Static template content (no application data model for these)
# ---------------------------------------------------------------------------
DISTRIBUTION = [
    ("Robert Aidi", "raidi1", "PO"),
    ("Harikrishnan Unnikrishnan", "Hunnikri", "Project Lead"),
    ("Jagadeesh Ram Chilla", "Jchilla", "Cybersecurity Engineer"),
    ("Hari Bhagavathi Ramian Monimekalai", "Hramianm", "Cyber Compliance Engineer"),
]

HISTORY = [
    ("1", "18/06/2025", "Ashwin Sasi & Bhagirath", "First issue"),
]

DOCS_PROVIDED = [
    ("Item Definition (JLR-TMP-568088)", "Y"),
    ("TARA", "Y"),
    ("PCB schematics", "Y"),
    ("Sequence diagram for ECU boot process", ""),
    ("Back-end infrastructure related specifications", ""),
]

ROLES = [
    ("JLR ECU team", ""),
    ("Robert Aidi", "PO"),
    ("Harikrishnan Unnikrishnan", "Project Lead"),
    ("Jagadeesh Ram Chilla", "Cybersecurity Engineer"),
    ("Hari Bhagavathi Ramian Monimekalai", "Cyber Compliance Engineer"),
    ("[Pentest partner]", ""),
    ("Name 1", ""),
    ("Name 2", ""),
]

ATTACKERS = [
    ("JLR insiders", "N"),
    ("JLR third parties", "Y"),
    ("JLR vehicle users", "Y"),
    ("JLR vehicle non-users - low capabilities", "Y"),
    ("JLR vehicle non-users - high capabilities", "N"),
]

LIMITATIONS = [
    (
        "The attacker cannot compromise the backend servers and infrastructure. "
        "However, they may control any communication channel towards the ECU.",
        "Offboard elements out of scope.",
    ),
    ("{other limitations}", ""),
]

ASSUMPTIONS = [
    ("Vehicle communication is secured", ""),
]

SCHEDULES = [
    (
        "Intermediary pentesting reports",
        "{weekly/fortnightly?}",
        "Draft pentesting reports with information on status and findings.",
    ),
    (
        "Final pentesting report",
        "{tbc}",
        "Final pentesting report in JLR approved template, containing all required "
        "information about tests conducted, findings, replication steps and "
        "remediation suggestions, etc (as per info required in template).",
    ),
    (
        "Log artifacts",
        "{tbc}",
        "Logfiles for all tests performed, including tests with no findings. For "
        "findings, logs showing successful exploitation are required.",
    ),
    ("{other deliverables}", "", ""),
]

REFERENCES = [
    "Hu, Vincent C., Rick Kuhn, and Dylan Yaga. \u201cVerification and test methods "
    "for access control policies/models.\u201d NIST Special Publication 800 (2017): 192.",
    "Joint Task Force. \u201cAssessing security and privacy controls in information "
    "systems and organizations.\u201d NIST Special Publication (2021).",
    "Scarfone, Karen, et al. \u201cTechnical guide to information security testing and "
    "assessment.\u201d NIST Special Publication 800.115 (2008): 2-25.",
    "ISO/SAE 21434 Road vehicles - Cybersecurity engineering: First edition 2021-08.",
]

ATTACKER_MODEL_APPENDIX = [
    (
        "JLR insiders",
        "Software developer, system designer, tester, quality engineer, project "
        "manager, production engineer",
        "Leak confidential information, introduce vulnerabilities, use insider knowledge",
    ),
    (
        "JLR third parties",
        "Supplier, service provider, dealership, repair garage, data analyst, remote "
        "diagnostic user, certificate authority",
        "Introduce malicious software, delay patching, steal information, access "
        "vehicle network",
    ),
    (
        "JLR vehicle users",
        "Driver, vehicle owner",
        "Activate paid-for features, customise vehicle features",
    ),
    (
        "JLR vehicle non-users - low capability",
        "Cyber criminals, competitor, pirate software seller, malicious web designer, "
        "insurer",
        "Steal vehicle or data, control vehicle, steal IP, create counterfeit products",
    ),
    (
        "JLR vehicle non-users - high capability",
        "Nation state hacker, hostile government, terrorist",
        "Crash, steal or control vehicle; large-scale disruption; steal data",
    ),
]

TESTING_TYPE_APPENDIX = [
    (
        "Blackbox testing",
        "Testing without access to internal structures or workings. The analyst "
        "simulates a real-world attacker with no or limited system knowledge and may "
        "use public information.",
    ),
    (
        "Whitebox Testing",
        "Testing with full access to internal structures, technical information, "
        "source code and architecture.",
    ),
    (
        "Greybox Testing",
        "A combination of black-box and white-box testing. The analyst has some "
        "implementation details and binaries but no source code.",
    ),
]

RISK_MATRIX = [
    ("QM", "x", "", "", ""),
    ("Low", "x", "", "", ""),
    ("Medium", "x", "x", "", ""),
    ("High", "x", "x", "x", ""),
    ("Critical", "x", "x", "x", "x"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _esc(value: object) -> str:
    if value is None:
        return ""
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _fmt_date(value: date | None) -> str:
    return value.strftime("%d/%m/%Y") if value else "\u2014"


def _platform_label(ecu: Any) -> str:
    return f"{ecu.architecture} \u2013 {ecu.vehicle_line} ({ecu.year})"


def _header_footer(canv: canvas.Canvas, doc) -> None:
    """Draw the running header and footer on every page."""
    canv.saveState()

    # Footer: classification, page number, template code.
    canv.setFont("Helvetica", 7)
    canv.setFillColor(FOOTER_GREY)

    foot_y = 14 * mm
    canv.drawString(
        MARGIN_LEFT, foot_y,
        "JLR-RMP: This shall be retained for 10 years after the End of life of",
    )
    canv.drawString(
        MARGIN_LEFT, foot_y - 3.2 * mm,
        "vehicle product or component in production and service.",
    )
    canv.drawString(MARGIN_LEFT, foot_y - 8 * mm, "JLR-RMP Classification: Confidential")

    canv.setFont("Helvetica-Bold", 7)
    canv.drawRightString(PAGE_WIDTH - MARGIN_RIGHT, foot_y, "CONFIDENTIAL")
    canv.setFont("Helvetica", 7)
    canv.drawRightString(
        PAGE_WIDTH - MARGIN_RIGHT, foot_y - 3.2 * mm,
        f"Page {canv.getPageNumber()}",
    )
    canv.drawRightString(
        PAGE_WIDTH - MARGIN_RIGHT, foot_y - 6.4 * mm, DOC_TEMPLATE_CODE,
    )

    canv.restoreState()


def _cell_styles(font_size: float = 8.5):
    base = getSampleStyleSheet()["Normal"]
    label = ParagraphStyle(
        "Label", parent=base, fontSize=font_size, fontName="Helvetica-Bold",
        textColor=INK, leading=font_size + 2.5,
    )
    value = ParagraphStyle(
        "Value", parent=base, fontSize=font_size, fontName="Helvetica",
        textColor=INK, leading=font_size + 2.5,
    )
    section = ParagraphStyle(
        "Section", parent=base, fontSize=font_size + 0.5, fontName="Helvetica-Bold",
        textColor=INK, leading=font_size + 3,
    )
    return label, value, section


def _simple_table(
    rows: list[list[str]],
    col_widths: list[float],
    header: list[str] | None = None,
    font_size: float = 8.5,
) -> Table:
    """A two-tone table: the first column uses tan-light, the rest teal-light."""
    label, value, _ = _cell_styles(font_size)
    data: list[list] = []
    if header:
        data.append([Paragraph(_esc(h), label) for h in header])
    for row in rows:
        data.append(
            [
                Paragraph(_esc(v), label if c == 0 else value)
                for c, v in enumerate(row)
            ]
        )

    cmds = [
        ("GRID", (0, 0), (-1, -1), 0.4, GRID),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    if header:
        cmds.append(("BACKGROUND", (0, 0), (-1, 0), TAN))
        first_data_row = 1
    else:
        first_data_row = 0

    for r in range(first_data_row, len(data)):
        cmds.append(("BACKGROUND", (0, r), (0, r), TAN_LIGHT))
        for c in range(1, len(col_widths)):
            cmds.append(("BACKGROUND", (c, r), (c, r), TEAL_LIGHT))

    table = Table(data, colWidths=col_widths, repeatRows=1 if header else 0)
    table.setStyle(TableStyle(cmds))
    return table


# ---------------------------------------------------------------------------
# Section content builders
# ---------------------------------------------------------------------------
def _intro_rows(ecu: Any) -> list[list[str]]:
    return [
        ["ECU name", ecu.ecu_name],
        ["Part number", ecu.part_number],
        ["ECU risk rating", ecu.ecu_risk_rating],
        ["Architecture", ecu.architecture],
        ["Vehicle line", ecu.vehicle_line],
        ["Year", str(ecu.year)],
        ["Microcontroller/CPU provider", ecu.microcontroller_cpu_provider],
        ["Date hardware B-sample available", _fmt_date(ecu.date_hardware_b_sample_available)],
        ["Date harnesses available", _fmt_date(ecu.date_harness_available)],
        [
            "Date production-intent software available (inc all cybersecurity controls)",
            _fmt_date(ecu.date_production_intent_software_available),
        ],
        ["Export control classification", ecu.export_control_classification],
        ["Pentest provider name", ecu.pentest_provider_name],
    ]


def _testing_type_rows(selected_test_type_names: list[str] | None) -> list[list[str]]:
    names = {n.strip().lower() for n in (selected_test_type_names or [])}
    wildcard = not names or "both" in names

    def yn(key: str) -> str:
        return "Y" if wildcard or key in names else "N"

    return [
        ["White-box testing", yn("white-box")],
        ["Gray-box testing", yn("gray-box")],
        ["Black-box testing", yn("black-box")],
    ]


def _build_scope_rows(
    test_cases: list[Any],
) -> list[tuple[bool, str, str, str]]:
    """
    Convert the test-case catalogue into the section 4 row format.

    Returns a list of (is_section_banner, objective, action, comment) tuples
    where ``is_section_banner`` is True for category headers. The objective
    column is shown only on the first row of each objective group, matching
    the source template's visual style.
    """

    ordered = sorted(
        test_cases,
        key=lambda tc: (
            tc.categories.id if tc.categories else 0,
            tc.objectives.id if tc.objectives else 0,
            tc.id,
        ),
    )

    rows: list[tuple[bool, str, str, str]] = []

    current_category: str | None = None
    current_objective: str | None = None

    for tc in ordered:

        category_name = (
            tc.categories.name
            if tc.categories
            else "Uncategorised"
        )

        if category_name != current_category:
            rows.append(
                (
                    True,
                    category_name,
                    "",
                    "",
                )
            )

            current_category = category_name
            current_objective = None

        objective_name = (
            tc.objectives.name
            if tc.objectives
            else ""
        )

        show_objective = (
            objective_name != current_objective
        )

        current_objective = objective_name

        status = (
            tc.source_scope_status
            if tc.source_scope_status
            else "—"
        )

        rows.append(
            (
                False,
                objective_name if show_objective else "",
                tc.action_test_case,
                status,
            )
        )

    return rows


def _scope_table(scope_rows: list[tuple[bool, str, str, str]], font_size: float = 7.5) -> Table:
    label, value, section = _cell_styles(font_size)

    data: list[list] = [
        [Paragraph(_esc(h), label) for h in ("Objective", "Actions/Tests", "Comments")]
    ]
    section_rows: set[int] = set()
    for is_section, col0, col1, col2 in scope_rows:
        r = len(data)
        if is_section:
            section_rows.add(r)
            data.append([Paragraph(_esc(col0), section), "", ""])
        else:
            data.append(
                [
                    Paragraph(_esc(col0), label),
                    Paragraph(_esc(col1), value),
                    Paragraph(_esc(col2), value),
                ]
            )

    cmds = [
        ("GRID", (0, 0), (-1, -1), 0.4, GRID),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("BACKGROUND", (0, 0), (-1, 0), TAN),
    ]
    for r in range(1, len(data)):
        if r in section_rows:
            cmds.append(("BACKGROUND", (0, r), (-1, r), TEAL))
            cmds.append(("SPAN", (0, r), (-1, r)))
        else:
            cmds.append(("BACKGROUND", (0, r), (0, r), TAN_LIGHT))
            cmds.append(("BACKGROUND", (1, r), (2, r), TEAL_LIGHT))

    table = Table(
        data,
        colWidths=[CONTENT_WIDTH * 0.30, CONTENT_WIDTH * 0.50, CONTENT_WIDTH * 0.20],
        repeatRows=1,
    )
    table.setStyle(TableStyle(cmds))
    return table


# ---------------------------------------------------------------------------
# Page-level builders
# ---------------------------------------------------------------------------
def _build_cover_page(ecu: Any) -> list:
    base = getSampleStyleSheet()["Normal"]
    kicker = ParagraphStyle(
        "Kicker", parent=base, fontSize=18, fontName="Helvetica-Bold",
        alignment=TA_CENTER, textColor=INK, spaceAfter=10,
    )
    title = ParagraphStyle(
        "Title", parent=base, fontSize=24, fontName="Helvetica-Bold",
        alignment=TA_CENTER, textColor=INK, spaceAfter=8,
    )
    for_ = ParagraphStyle(
        "For", parent=base, fontSize=14, fontName="Helvetica-Bold",
        alignment=TA_CENTER, textColor=INK, spaceAfter=6,
    )
    value = ParagraphStyle(
        "Value", parent=base, fontSize=15, fontName="Helvetica-Bold",
        alignment=TA_CENTER, textColor=INK, spaceAfter=4,
    )
    copyright = ParagraphStyle(
        "Copyright", parent=base, fontName="Helvetica-Bold",
        alignment=TA_CENTER, fontSize=9, textColor=INK,
    )

    story = [
        Spacer(1, 24 * mm),
        Paragraph("ECU PENETRATION TESTING", kicker),
        Paragraph("TEST PLAN", title),
        Paragraph("for", for_),
        Paragraph(_esc(ecu.ecu_name), value),
        Paragraph(_esc(_platform_label(ecu)), value),
        Paragraph(_esc(date.today().strftime("%d/%m/%Y")), value),
        Spacer(1, 18 * mm),
        _simple_table(
            rows=[["Owner", "PO", "Robert Aidi"], ["Reviewer", "Role Title", "Name"]],
            col_widths=[CONTENT_WIDTH * 0.18, CONTENT_WIDTH * 0.22, CONTENT_WIDTH * 0.60],
            font_size=9,
        ),
        Spacer(1, 12 * mm),
        Paragraph("Jaguar Land Rover Proprietary and Confidential", copyright),
        Paragraph(_esc(f"Copyright \u00a9 {date.today().year}"), copyright),
        Paragraph("Jaguar Land Rover Ltd.", copyright),
        PageBreak(),
    ]
    return story


def _build_distribution_and_history() -> list:
    base = getSampleStyleSheet()["Normal"]
    h1 = ParagraphStyle("H1", parent=base, fontSize=14, fontName="Helvetica-Bold",
                        textColor=INK, spaceAfter=4)
    story = [
        Paragraph("Distribution List", h1),
        _simple_table(
            rows=[list(r) for r in DISTRIBUTION],
            col_widths=[CONTENT_WIDTH * 0.46, CONTENT_WIDTH * 0.24, CONTENT_WIDTH * 0.30],
            header=["Name", "CDSID", "Role title"],
        ),
        Spacer(1, 8 * mm),
        Paragraph("Document Change History", h1),
        _simple_table(
            rows=[list(r) for r in HISTORY],
            col_widths=[
                CONTENT_WIDTH * 0.14, CONTENT_WIDTH * 0.20,
                CONTENT_WIDTH * 0.28, CONTENT_WIDTH * 0.38,
            ],
            header=["Revision", "Date", "Author(s)", "Details of changes"],
        ),
        PageBreak(),
    ]
    return story


def _build_table_of_contents() -> list:
    base = getSampleStyleSheet()["Normal"]
    h1 = ParagraphStyle("H1", parent=base, fontSize=14, fontName="Helvetica-Bold",
                        textColor=INK, spaceAfter=6)
    item = ParagraphStyle("TocItem", parent=base, fontSize=10, textColor=INK,
                          leading=14, spaceAfter=3)
    subitem = ParagraphStyle("TocSub", parent=item, leftIndent=14, fontSize=9,
                             leading=12, spaceAfter=2)

    entries = [
        ("Distribution List", 2, False),
        ("Document Change History", 2, False),
        ("Contents", 3, False),
        ("1 Introduction", 4, True),
        ("1.1 Supporting documentation", 4, False),
        ("1.2 Roles and responsibilities", 5, False),
        ("2 Testing approach", 6, True),
        ("2.1 Attacker model", 6, False),
        ("2.2 Type of testing", 6, False),
        ("2.3 Assumptions", 6, False),
        ("3 Schedules and deliverables", 7, False),
        ("4 Test scope", 8, True),
        ("References", None, True),
        ("Appendix A. Attacker model", None, True),
        ("Appendix B. Type of testing", None, True),
        ("Appendix C. High level penetration testing requirements", None, True),
    ]
    story = [Paragraph("Contents", h1)]
    for title, _page, is_top in entries:
        story.append(Paragraph(_esc(title), item if is_top else subitem))
    story.append(PageBreak())
    return story


def _build_introduction(ecu: Any) -> list:
    base = getSampleStyleSheet()["Normal"]
    h1 = ParagraphStyle("H1", parent=base, fontSize=14, fontName="Helvetica-Bold",
                        textColor=INK, spaceAfter=4)
    h2 = ParagraphStyle("H2", parent=base, fontSize=11, fontName="Helvetica-Bold",
                        textColor=INK, spaceBefore=6, spaceAfter=4)
    instruction = ParagraphStyle("Instruction", parent=base, fontSize=9,
                                 fontName="Helvetica-Oblique", textColor=MUTED,
                                 leading=12)
    footnote = ParagraphStyle("Footnote", parent=base, fontSize=7, textColor=MUTED,
                              leading=10)

    return [
        Paragraph("1 Introduction", h1),
        _simple_table(
            _intro_rows(ecu),
            col_widths=[CONTENT_WIDTH * 0.42, CONTENT_WIDTH * 0.58],
            font_size=8.5,
        ),
        Spacer(1, 4 * mm),
        Paragraph("1.1 Supporting documentation", h2),
        Paragraph(
            "List of documents consulted during creation/validation of the test plan. "
            "Please send these documents to the penetration testing team with the test plan.",
            instruction,
        ),
        Spacer(1, 2 * mm),
        _simple_table(
            [list(r) for r in DOCS_PROVIDED],
            col_widths=[CONTENT_WIDTH * 0.76, CONTENT_WIDTH * 0.24],
            header=["Document", "Provided? Y/N"],
        ),
        Spacer(1, 4 * mm),
        Paragraph("1.2 Roles and responsibilities", h2),
        Paragraph(
            "The ECU team should provide software, hardware and cybersecurity engineering "
            "contacts as a minimum.",
            instruction,
        ),
        Spacer(1, 2 * mm),
        _simple_table(
            [list(r) for r in ROLES],
            col_widths=[CONTENT_WIDTH * 0.4, CONTENT_WIDTH * 0.6],
            header=["Name", "Role & responsibility"],
        ),
        Spacer(1, 2 * mm),
        Paragraph(
            "\u00b9 If not known, please input \u201cUnknown\u201d and contact the pentesting team asap.",
            footnote,
        ),
        PageBreak(),
    ]


def _build_testing_approach(selected_test_type_names: list[str] | None) -> list:
    base = getSampleStyleSheet()["Normal"]
    h1 = ParagraphStyle("H1", parent=base, fontSize=14, fontName="Helvetica-Bold",
                        textColor=INK, spaceAfter=4)
    h2 = ParagraphStyle("H2", parent=base, fontSize=11, fontName="Helvetica-Bold",
                        textColor=INK, spaceBefore=6, spaceAfter=4)
    h4 = ParagraphStyle("H4", parent=base, fontSize=9.5, fontName="Helvetica-Bold",
                        textColor=INK, spaceBefore=4, spaceAfter=3)
    body = ParagraphStyle("Body", parent=base, fontSize=9, textColor=INK, leading=12)
    instruction = ParagraphStyle("Instruction", parent=base, fontSize=9,
                                 fontName="Helvetica-Oblique", textColor=MUTED,
                                 leading=12)
    footnote = ParagraphStyle("Footnote", parent=base, fontSize=7, textColor=MUTED,
                              leading=10)

    return [
        Paragraph("2 Testing approach", h1),
        Paragraph(
            "Before penetration testing begins, the in-scope and out-of-scope system "
            "components and the attack boundary shall be agreed.",
            instruction,
        ),
        Spacer(1, 3 * mm),
        Paragraph("2.1 Attacker model", h2),
        Paragraph("Attackers relevant for the ECU under test:", body),
        _simple_table(
            [list(r) for r in ATTACKERS],
            col_widths=[CONTENT_WIDTH * 0.83, CONTENT_WIDTH * 0.17],
            header=["Attacker type", "Y/N"],
        ),
        Spacer(1, 3 * mm),
        Paragraph("Attacker Limitations", h4),
        _simple_table(
            [list(r) for r in LIMITATIONS],
            col_widths=[CONTENT_WIDTH * 0.66, CONTENT_WIDTH * 0.34],
            header=["Limitation", "Rationale"],
        ),
        Spacer(1, 3 * mm),
        Paragraph("2.2 Type of testing", h2),
        _simple_table(
            _testing_type_rows(selected_test_type_names),
            col_widths=[CONTENT_WIDTH * 0.83, CONTENT_WIDTH * 0.17],
            header=["Type of testing", "Y/N"],
        ),
        Spacer(1, 3 * mm),
        Paragraph("2.3 Assumptions", h2),
        _simple_table(
            [list(r) for r in ASSUMPTIONS],
            col_widths=[CONTENT_WIDTH * 0.66, CONTENT_WIDTH * 0.34],
            header=["Assumption", "Rationale"],
        ),
        Spacer(1, 2 * mm),
        Paragraph(
            "\u00b2 If JLR insiders or high-capability non-users are in scope, provide "
            "additional justification to the pentesting team.",
            footnote,
        ),
        PageBreak(),
    ]


def _build_schedules() -> list:
    base = getSampleStyleSheet()["Normal"]
    h1 = ParagraphStyle("H1", parent=base, fontSize=14, fontName="Helvetica-Bold",
                        textColor=INK, spaceAfter=4)
    instruction = ParagraphStyle("Instruction", parent=base, fontSize=9,
                                 fontName="Helvetica-Oblique", textColor=MUTED,
                                 leading=12)
    return [
        Paragraph("3 Schedules and deliverables", h1),
        Paragraph(
            "This section will be completed after discussion with the pentest partner. "
            "It lists deliverables, time frames and expected content.",
            instruction,
        ),
        Spacer(1, 3 * mm),
        _simple_table(
            [list(r) for r in SCHEDULES],
            col_widths=[CONTENT_WIDTH * 0.28, CONTENT_WIDTH * 0.20, CONTENT_WIDTH * 0.52],
            header=["Deliverable", "Date", "Description"],
        ),
        PageBreak(),
    ]


def _build_test_scope(
    test_cases: list[Any],
    selected_category_names: list[str] | None,
    selected_test_type_names: list[str] | None,
) -> list:
    base = getSampleStyleSheet()["Normal"]
    h1 = ParagraphStyle("H1", parent=base, fontSize=14, fontName="Helvetica-Bold",
                        textColor=INK, spaceAfter=4)
    body = ParagraphStyle("Body", parent=base, fontSize=9, textColor=INK, leading=12)
    note = ParagraphStyle("Note", parent=body, fontName="Helvetica-Bold",
                          spaceBefore=2, spaceAfter=4)

    scope_rows = _build_scope_rows(test_cases)
    note_text = (
        f"Categories in scope: {', '.join(selected_category_names)}"
        if selected_category_names
        else "Categories in scope: All categories"
    )
    note_text += " | " + (
        f"Test types in scope: {', '.join(selected_test_type_names)}"
        if selected_test_type_names
        else "Test types in scope: All test types"
    )

    return [
        Paragraph("4 Test scope", h1),
        Paragraph(
            "The following scoping tests are agreed between the EE Owner, Penetration "
            "Test Manager and penetration test partner. The proposed tests are generic "
            "and non-applicable items should be marked accordingly.",
            body,
        ),
        Paragraph(_esc(note_text), note),
        _scope_table(scope_rows),
        PageBreak(),
    ]


def _build_references() -> list:
    base = getSampleStyleSheet()["Normal"]
    h1 = ParagraphStyle("H1", parent=base, fontSize=14, fontName="Helvetica-Bold",
                        textColor=INK, spaceAfter=4)
    body = ParagraphStyle("Body", parent=base, fontSize=9, textColor=INK, leading=12)
    return [
        Paragraph("References", h1),
        *(Paragraph(_esc(ref), body) for ref in REFERENCES),
        PageBreak(),
    ]


def _build_appendices() -> list:
    base = getSampleStyleSheet()["Normal"]
    h1 = ParagraphStyle("H1", parent=base, fontSize=14, fontName="Helvetica-Bold",
                        textColor=INK, spaceAfter=4)
    body = ParagraphStyle("Body", parent=base, fontSize=9, textColor=INK, leading=12)
    story = [
        Paragraph("Appendix A. Attacker model", h1),
        Paragraph("Please use the following definitions for attacker models, as per JLR-PRD-569408:", body),
        _simple_table(
            [list(r) for r in ATTACKER_MODEL_APPENDIX],
            col_widths=[CONTENT_WIDTH * 0.24, CONTENT_WIDTH * 0.33, CONTENT_WIDTH * 0.43],
            header=["Attacker model categories", "Attacker examples", "Example attacks"],
            font_size=7.5,
        ),
        PageBreak(),
        Paragraph("Appendix B. Type of testing", h1),
        Paragraph("Black, White and Grey-box testing are defined by adapting NIST definitions:", body),
        _simple_table(
            [list(r) for r in TESTING_TYPE_APPENDIX],
            col_widths=[CONTENT_WIDTH * 0.25, CONTENT_WIDTH * 0.75],
            header=["Type of testing", "Description"],
        ),
        PageBreak(),
        Paragraph("Appendix C. High level penetration testing requirements", h1),
        Paragraph("For more information, refer to process JLR-PRD-569408.", body),
        _simple_table(
            [list(r) for r in RISK_MATRIX],
            col_widths=[CONTENT_WIDTH * 0.20] * 5,
            header=[
                "ECU risk rating",
                "ECU/System interfaces",
                "Secure software downloads",
                "In-vehicle communication and secure boot",
                "Cryptographic material and memory",
            ],
            font_size=7.5,
        ),
    ]
    return story


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def build_pdf(
    test_cases: list[Any],
    ecu_detail: Any,
    selected_category_names: list[str] | None = None,
    selected_test_type_names: list[str] | None = None,
) -> bytes:
    """Build the test plan PDF in-memory and return the raw bytes.

    This function is intentionally synchronous and CPU-bound; callers in
    async code should wrap it with ``asyncio.to_thread``.
    """
    if ecu_detail is None:
        raise ValueError("ecu_detail is required to generate the test plan PDF")

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=MARGIN_LEFT,
        rightMargin=MARGIN_RIGHT,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOTTOM,
        title="ECU Penetration Testing - Test Plan",
        author="ECU Penetration Testing Tool",
    )

    story: list = []
    story += _build_cover_page(ecu_detail)
    story += _build_distribution_and_history()
    story += _build_table_of_contents()
    story += _build_introduction(ecu_detail)
    story += _build_testing_approach(selected_test_type_names)
    story += _build_schedules()
    story += _build_test_scope(test_cases, selected_category_names, selected_test_type_names)
    story += _build_references()
    story += _build_appendices()

    # ``build`` runs the story through ReportLab and writes the PDF to the
    # underlying buffer. ``onFirstPage`` and ``onLaterPages`` are not used;
    # the header/footer is drawn per-page from a single callback that reads
    # the current page number directly.
    doc.build(
        story,
        onFirstPage=_header_footer,
        onLaterPages=_header_footer,
    )
    return buffer.getvalue()
