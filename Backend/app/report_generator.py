"""
BAMI SCIENTIFIC PDF REPORT GENERATOR
Produces publication-grade, comprehensive molecular screening reports
using ReportLab, RDKit, and trained ML models.
Includes chemical structures, Lipinski descriptors, dual-target bioactivity
(COX-2 and EGFR), Bemis-Murcko core decomposition, and 10-endpoint ADMET profiling.
"""

from __future__ import annotations

import io
import uuid
from datetime import datetime, timezone
from typing import Any

from rdkit import Chem
from rdkit.Chem import Descriptors, Lipinski, Crippen
from rdkit.Chem.Draw import rdMolDraw2D

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    Table,
    TableStyle,
    KeepTogether,
    HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


# ==============================================================================
# NUMBERED CANVAS FOR TWO-PASS RUNNING HEADERS & FOOTERS
# ==============================================================================
class BAMINumberedCanvas(canvas.Canvas):
    """Two-pass canvas that computes accurate total page counts and stamps running headers/footers."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._saved_page_states: list[dict[str, Any]] = []

    def showPage(self) -> None:
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int) -> None:
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#554A6F"))

        # Running header on page 2+
        if self._pageNumber > 1:
            self.drawString(36, 756, "BAMI: Bioactive Molecule Intelligence — Comprehensive Scientific Screening Report")
            self.setStrokeColor(colors.HexColor("#DDD4EC"))
            self.setLineWidth(0.6)
            self.line(36, 750, 576, 750)

        # Running footer on all pages
        self.setStrokeColor(colors.HexColor("#DDD4EC"))
        self.setLineWidth(0.6)
        self.line(36, 42, 576, 42)

        self.drawString(36, 28, "CONFIDENTIAL & PROPRIETARY — FOR RESEARCH LEADS ONLY — NOT PROOF OF MEDICAL SAFETY")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(576, 28, page_str)
        self.restoreState()


# ==============================================================================
# 2D MOLECULAR DEPICTION HELPER
# ==============================================================================
def render_mol_png_bytes(mol: Chem.Mol, width: int = 480, height: int = 300) -> bytes:
    """Renders high-resolution 2D chemical structure PNG bytes via RDKit Cairo."""
    d = rdMolDraw2D.MolDraw2DCairo(width, height)
    opts = d.drawOptions()
    opts.clearBackground = True
    opts.bondLineWidth = 2
    d.DrawMolecule(mol)
    d.FinishDrawing()
    return d.GetDrawingText()


# ==============================================================================
# REPORT BUILDER ENGINE
# ==============================================================================
def generate_bami_pdf_report(
    smiles: str,
    compound_name: str | None = None,
    include_admet: bool = True,
    bioactivity_data: dict[str, Any] | None = None,
    admet_data: dict[str, Any] | None = None,
    scaffold_data: dict[str, Any] | None = None
) -> bytes:
    """
    Builds a multi-page, publication-grade scientific PDF report for a given molecule.
    Uses actual computational outputs only; clearly marks unavailable endpoints.
    """
    mol = Chem.MolFromSmiles(smiles)
    if not mol:
        raise ValueError(f"Invalid molecular SMILES string: '{smiles}'")

    canonical_smiles = Chem.MolToSmiles(mol)
    resolved_name = compound_name.strip() if compound_name and compound_name.strip() else "Virtual Screening Candidate"
    report_id = f"BAMI-{uuid.uuid4().hex[:8].upper()}"
    timestamp_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # Document Setup
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=46,
        bottomMargin=54
    )

    # Styles
    base_styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=base_styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1E1530"),
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=base_styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#651FFF")
    )

    section_header_style = ParagraphStyle(
        "SectionHeader",
        parent=base_styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1E1530"),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        "BodyDark",
        parent=base_styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#2A223B")
    )

    body_bold_style = ParagraphStyle(
        "BodyDarkBold",
        parent=body_style,
        fontName="Helvetica-Bold"
    )

    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=base_styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#1E1530"),
        alignment=0
    )

    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=base_styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#2A223B"),
        alignment=0
    )

    table_cell_bold = ParagraphStyle(
        "TableCellBold",
        parent=table_cell_style,
        fontName="Helvetica-Bold"
    )

    badge_pass_style = ParagraphStyle(
        "BadgePass",
        parent=table_cell_style,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#047857")
    )

    badge_fail_style = ParagraphStyle(
        "BadgeFail",
        parent=table_cell_style,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#B91C1C")
    )

    badge_amber_style = ParagraphStyle(
        "BadgeAmber",
        parent=table_cell_style,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#B45309")
    )

    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=base_styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=7.5,
        leading=10.5,
        textColor=colors.HexColor("#645B7A")
    )

    story: list[Any] = []

    # ==========================================================================
    # 1. HEADER & METADATA BANNER
    # ==========================================================
    header_table_data = [
        [
            Paragraph("✦ BAMI : Bioactive Molecule Intelligence", title_style),
            Paragraph(f"<b>Report ID:</b> {report_id}<br/><b>Date:</b> {timestamp_str}", subtitle_style)
        ]
    ]
    header_table = Table(header_table_data, colWidths=[360, 180])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#651FFF"), spaceBefore=2, spaceAfter=12))

    # ==========================================================================
    # 2. MOLECULE SPECIFICATION & 2D STRUCTURE
    # ==========================================================================
    story.append(Paragraph("1. Molecule Identification & 2D Chemical Structure", section_header_style))

    # Render 2D Depiction
    png_bytes = render_mol_png_bytes(mol, width=420, height=260)
    structure_img = Image(io.BytesIO(png_bytes), width=210, height=130)

    # Calculate Core Physicochemical Descriptors
    mw = round(Descriptors.MolWt(mol), 2)
    logp = round(Crippen.MolLogP(mol), 2)
    hbd = Lipinski.NumHDonors(mol)
    hba = Lipinski.NumHAcceptors(mol)
    tpsa = round(Descriptors.TPSA(mol), 2)
    rotb = Lipinski.NumRotatableBonds(mol)
    rings = Lipinski.RingCount(mol)
    aromatic_rings = Lipinski.NumAromaticRings(mol)
    heavy_atoms = mol.GetNumHeavyAtoms()
    formula = Chem.rdMolDescriptors.CalcMolFormula(mol)

    spec_data = [
        [Paragraph("<b>Compound Name:</b>", body_style), Paragraph(resolved_name, body_bold_style)],
        [Paragraph("<b>Molecular Formula:</b>", body_style), Paragraph(formula, body_style)],
        [Paragraph("<b>Canonical SMILES:</b>", body_style), Paragraph(f"<font size='7.5' face='Courier'>{canonical_smiles}</font>", body_style)],
        [Paragraph("<b>Molecular Weight:</b>", body_style), Paragraph(f"{mw} g/mol", body_style)],
        [Paragraph("<b>Calculated LogP:</b>", body_style), Paragraph(f"{logp}", body_style)],
        [Paragraph("<b>Heavy Atom Count:</b>", body_style), Paragraph(f"{heavy_atoms}", body_style)]
    ]
    spec_table = Table(spec_data, colWidths=[110, 210])
    spec_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F9F7FD")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5DDF2")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#EFEBF8"))
    ]))

    spec_layout_data = [[spec_table, structure_img]]
    spec_layout_table = Table(spec_layout_data, colWidths=[320, 220])
    spec_layout_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (1, 0), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(spec_layout_table)
    story.append(Spacer(1, 12))

    # ==========================================================================
    # 3. PHYSICOCHEMICAL PROPERTIES & LIPINSKI RULE OF 5
    # ==========================================================================
    story.append(Paragraph("2. Lipinski Rule of 5 & Oral Bioavailability Qualification", section_header_style))

    # Lipinski rules
    r_mw = mw <= 500
    r_logp = logp <= 5.0
    r_hbd = hbd <= 5
    r_hba = hba <= 10
    violations = sum([not r_mw, not r_logp, not r_hbd, not r_hba])
    is_druglike = violations <= 1

    lipinski_rows = [
        [
            Paragraph("Lipinski Rule Property", table_header_style),
            Paragraph("Criteria", table_header_style),
            Paragraph("Calculated Value", table_header_style),
            Paragraph("Rule Compliance", table_header_style)
        ],
        [
            Paragraph("Molecular Weight (MW)", table_cell_style),
            Paragraph("≤ 500.0 Da", table_cell_style),
            Paragraph(f"{mw} Da", table_cell_style),
            Paragraph("PASSED" if r_mw else "VIOLATION", badge_pass_style if r_mw else badge_fail_style)
        ],
        [
            Paragraph("Octanol/Water LogP", table_cell_style),
            Paragraph("≤ 5.00", table_cell_style),
            Paragraph(f"{logp}", table_cell_style),
            Paragraph("PASSED" if r_logp else "VIOLATION", badge_pass_style if r_logp else badge_fail_style)
        ],
        [
            Paragraph("Hydrogen Bond Donors (HBD)", table_cell_style),
            Paragraph("≤ 5", table_cell_style),
            Paragraph(f"{hbd}", table_cell_style),
            Paragraph("PASSED" if r_hbd else "VIOLATION", badge_pass_style if r_hbd else badge_fail_style)
        ],
        [
            Paragraph("Hydrogen Bond Acceptors (HBA)", table_cell_style),
            Paragraph("≤ 10", table_cell_style),
            Paragraph(f"{hba}", table_cell_style),
            Paragraph("PASSED" if r_hba else "VIOLATION", badge_pass_style if r_hba else badge_fail_style)
        ],
        [
            Paragraph("<b>Total Lipinski Violations</b>", table_cell_bold),
            Paragraph("≤ 1 violation allowed", table_cell_style),
            Paragraph(f"<b>{violations} of 4</b>", table_cell_bold),
            Paragraph("QUALIFIED (Drug-like)" if is_druglike else "NON-COMPLIANT", badge_pass_style if is_druglike else badge_fail_style)
        ]
    ]

    lipinski_table = Table(lipinski_rows, colWidths=[160, 110, 130, 140])
    lipinski_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDE7F6")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DDD4EC")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#FBF9FD")]),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#F3EEFA")),
    ]))
    story.append(lipinski_table)
    story.append(Spacer(1, 12))

    # ==========================================================================
    # 4. TARGET BIOACTIVITY MACHINE LEARNING PREDICTIONS
    # ==========================================================================
    story.append(Paragraph("3. Target Bioactivity Predictions (XGBoost Models)", section_header_style))

    bio_rows = [
        [
            Paragraph("Biological Target", table_header_style),
            Paragraph("ML Algorithm", table_header_style),
            Paragraph("Prediction", table_header_style),
            Paragraph("Confidence / Probability", table_header_style),
            Paragraph("Decision Threshold", table_header_style)
        ]
    ]

    # Fill COX-2
    cox2 = bioactivity_data.get("COX-2", {}) if bioactivity_data else {}
    c_pred = cox2.get("prediction", "Not Evaluated")
    c_prob = cox2.get("probability_active")
    c_prob_str = f"{c_prob * 100:.1f}%" if c_prob is not None else "N/A"
    c_style = badge_pass_style if c_pred == "Active" else (badge_fail_style if c_pred == "Inactive" else table_cell_style)

    bio_rows.append([
        Paragraph("<b>COX-2 (PTGS2)</b><br/><font size='7' color='#654E82'>UniProt P35354</font>", table_cell_style),
        Paragraph("Final XGBoost Classifier<br/><font size='7'>2048-bit Morgan (r=2)</font>", table_cell_style),
        Paragraph(f"<b>{c_pred}</b>", c_style),
        Paragraph(c_prob_str, table_cell_style),
        Paragraph("50.0% (0.50)", table_cell_style)
    ])

    # Fill EGFR
    egfr = bioactivity_data.get("EGFR", {}) if bioactivity_data else {}
    e_pred = egfr.get("prediction", "Not Evaluated")
    e_prob = egfr.get("probability_active")
    e_thresh = egfr.get("classification_threshold", 0.8068)
    e_prob_str = f"{e_prob * 100:.1f}% (Calibrated)" if e_prob is not None else "N/A"
    e_style = badge_pass_style if e_pred == "Active" else (badge_fail_style if e_pred == "Inactive" else table_cell_style)

    bio_rows.append([
        Paragraph("<b>EGFR (Receptor Kinase)</b><br/><font size='7' color='#654E82'>UniProt P00533</font>", table_cell_style),
        Paragraph("Tuned EGFR XGBoost<br/><font size='7'>Calibrated Probability</font>", table_cell_style),
        Paragraph(f"<b>{e_pred}</b>", e_style),
        Paragraph(e_prob_str, table_cell_style),
        Paragraph(f"{e_thresh * 100:.1f}%", table_cell_style)
    ])

    bio_table = Table(bio_rows, colWidths=[130, 140, 90, 100, 80])
    bio_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDE7F6")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DDD4EC")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FBF9FD")]),
    ]))
    story.append(bio_table)
    story.append(Spacer(1, 12))

    # ==========================================================================
    # 5. MOLECULAR SCAFFOLD (BEMIS-MURCKO) DECOMPOSITION
    # ==========================================================================
    story.append(Paragraph("4. Bemis-Murcko Scaffold & Substituent Decomposition", section_header_style))

    has_scaff = False
    core_smiles = "Acyclic / No Ring Assembly"
    ring_count = 0
    substituents_count = 0

    if scaffold_data and "scaffold" in scaffold_data:
        sc = scaffold_data["scaffold"]
        has_scaff = sc.get("has_scaffold", False)
        core_smiles = sc.get("scaffold_smiles") or core_smiles
        ring_count = sc.get("ring_count", 0)
        substituents_count = len(scaffold_data.get("substituents", []))
    else:
        # Compute on the fly if mol has rings
        from rdkit.Chem.Scaffolds import MurckoScaffold
        core_mol = MurckoScaffold.GetScaffoldForMol(mol)
        if core_mol and core_mol.GetNumHeavyAtoms() > 0:
            has_scaff = True
            core_smiles = Chem.MolToSmiles(core_mol)
            ring_count = core_mol.GetRingInfo().NumRings()

    scaff_rows = [
        [
            Paragraph("Scaffold Property", table_header_style),
            Paragraph("Extraction Outcome", table_header_style),
            Paragraph("SAR Significance", table_header_style)
        ],
        [
            Paragraph("Bemis-Murcko Core Type", table_cell_style),
            Paragraph("Ring Scaffold Assembly" if has_scaff else "Acyclic Aliphatic Chain", badge_pass_style if has_scaff else table_cell_style),
            Paragraph("Defines primary conformational backbone and target binding geometry", table_cell_style)
        ],
        [
            Paragraph("Core Framework SMILES", table_cell_style),
            Paragraph(f"<font size='7' face='Courier'>{core_smiles}</font>", table_cell_style),
            Paragraph(f"{ring_count} interconnected rings in conserved structural assembly", table_cell_style)
        ],
        [
            Paragraph("Peripheral Substituents", table_cell_style),
            Paragraph(f"{substituents_count} functional groups identified" if substituents_count > 0 else "Direct scaffold core", table_cell_style),
            Paragraph("Modulates solubility, polar interactions, and isoform selectivity", table_cell_style)
        ]
    ]

    scaff_table = Table(scaff_rows, colWidths=[150, 190, 200])
    scaff_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDE7F6")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DDD4EC")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FBF9FD")]),
    ]))
    story.append(scaff_table)
    story.append(Spacer(1, 12))

    # ==========================================================================
    # 6. ADMET PHARMACOKINETICS & TOXICOLOGY PROFILING
    # ==========================================================================
    story.append(Paragraph("5. Preclinical ADMET Pharmacokinetics & Safety Profiling", section_header_style))

    if include_admet and admet_data and "admet_results" in admet_data:
        admet_res = admet_data["admet_results"]

        admet_rows = [
            [
                Paragraph("ADMET Category", table_header_style),
                Paragraph("Endpoint Model", table_header_style),
                Paragraph("Predicted Value / Class", table_header_style),
                Paragraph("Interpretation & Risk Flag", table_header_style)
            ]
        ]

        def get_admet_badge(flag: str):
            f_lower = (flag or "").lower()
            if "favour" in f_lower or "low" in f_lower or "negative" in f_lower or "non" in f_lower or "high" in f_lower:
                return badge_pass_style
            elif "risk" in f_lower or "alert" in f_lower or "positive" in f_lower or "blocker" in f_lower:
                return badge_fail_style
            return badge_amber_style

        for ep_key, ep_info in admet_res.items():
            cat = ep_info.get("category", "General").title()
            name = ep_info.get("name", ep_key)
            val = ep_info.get("formatted_value") or str(ep_info.get("predicted_value", "--"))
            flag = ep_info.get("flag", "Informational")
            interp = ep_info.get("interpretation", "")

            flag_style = get_admet_badge(flag)

            admet_rows.append([
                Paragraph(cat, table_cell_bold),
                Paragraph(name, table_cell_style),
                Paragraph(val, table_cell_style),
                Paragraph(f"{interp} (<b>{flag}</b>)", flag_style)
            ])

        admet_table = Table(admet_rows, colWidths=[90, 130, 120, 200])
        admet_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDE7F6")),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DDD4EC")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FBF9FD")]),
        ]))
        story.append(admet_table)

    else:
        # Clearly marked as uncomputed if not executed
        unavail_rows = [
            [
                Paragraph("Preclinical ADMET Screening", table_header_style),
                Paragraph("Execution Status", table_header_style),
                Paragraph("Guidance & Documentation", table_header_style)
            ],
            [
                Paragraph("10-Endpoint ADMET Profile<br/>(Solubility, Caco-2, HIA, BBB, CYPs, Ames, DILI, hERG)", table_cell_style),
                Paragraph("<b>NOT COMPUTED IN THIS RUN</b>", badge_amber_style),
                Paragraph("Available on demand via the BAMI ADMET module. Evaluates 10 machine-learning models trained on TDC benchmarks.", table_cell_style)
            ]
        ]
        unavail_table = Table(unavail_rows, colWidths=[180, 160, 200])
        unavail_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDE7F6")),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DDD4EC")),
            ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#FFFBEB")),
        ]))
        story.append(unavail_table)

    story.append(Spacer(1, 12))

    # ==========================================================================
    # 7. DOCKING SIMULATION STATUS
    # ==========================================================================
    story.append(Paragraph("6. Molecular Docking Simulation Status", section_header_style))

    docking_rows = [
        [
            Paragraph("In Silico Simulation Target", table_header_style),
            Paragraph("Docking Protocol Status", table_header_style),
            Paragraph("Scientific Guidance", table_header_style)
        ],
        [
            Paragraph("EGFR Kinase Domain (1M17 / 2J6M)<br/>COX-2 Active Site (1CX2 / 6COX)", table_cell_style),
            Paragraph("<b>UNAVAILABLE / NOT EXECUTED</b>", badge_amber_style),
            Paragraph("Molecular mechanics docking (AutoDock Vina / Glide) was not conducted in this 2D ligand-based screening phase. High-scoring predictions should proceed to molecular dynamics or crystallographic validation.", table_cell_style)
        ]
    ]
    docking_table = Table(docking_rows, colWidths=[180, 160, 200])
    docking_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDE7F6")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DDD4EC")),
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#FFFBEB")),
    ]))
    story.append(docking_table)
    story.append(Spacer(1, 14))

    # ==========================================================================
    # 8. SCIENTIFIC & REGULATORY DISCLAIMER
    # ==========================================================================
    disclaimer_block = [
        Paragraph(
            "<b>SCIENTIFIC &amp; REGULATORY NOTICE:</b> BAMI is a computational cheminformatics screening and decision-support system. "
            "All predicted bioactivity scores, probabilities, and ADMET profiles represent statistical estimations derived from trained machine-learning "
            "models (XGBoost, Scikit-Learn) and historical ChEMBL/TDC datasets. Predictions do not guarantee biological efficacy, safety, metabolic "
            "tolerance, or clinical utility. All computational candidate leads strictly require experimental in vitro confirmation (e.g., enzymatic IC50 assays, "
            "surface plasmon resonance, cellular toxicity assays) prior to any clinical or translational research use.",
            disclaimer_style
        )
    ]
    disclaimer_table = Table([[disclaimer_block]], colWidths=[540])
    disclaimer_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F9F7FD")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#DDD4EC")),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(KeepTogether(disclaimer_table))

    # Build PDF
    doc.build(story, canvasmaker=BAMINumberedCanvas)
    return pdf_buffer.getvalue()
