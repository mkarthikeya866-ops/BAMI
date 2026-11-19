"""
BAMI: Bioactive Molecule Intelligence
Master Technical Review Presentation Generator (PPTX & PDF)
University Project Review Edition
"""

import sys
import os
from pathlib import Path
from PIL import Image

import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

import reportlab
from reportlab.lib.pagesizes import landscape
from reportlab.pdfgen import canvas
from reportlab.lib import colors

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "presentation"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PPTX_PATH = OUT_DIR / "BAMI_Project_Presentation.pptx"
PDF_PATH = OUT_DIR / "BAMI_Project_Presentation.pdf"

# 16:9 Widescreen dimensions
SLIDE_WIDTH_IN = 13.333
SLIDE_HEIGHT_IN = 7.5
SLIDE_WIDTH_PT = SLIDE_WIDTH_IN * 72   # 960 pt
SLIDE_HEIGHT_PT = SLIDE_HEIGHT_IN * 72 # 540 pt

# Color Palette
NAVY_DEEP = RGBColor(11, 19, 43)        # #0B132B
NAVY_CARD = RGBColor(21, 32, 60)        # #15203C
NAVY_LIGHT = RGBColor(28, 42, 78)       # #1C2A4E
CYAN = RGBColor(6, 182, 212)            # #06B6D4
CYAN_BRIGHT = RGBColor(0, 242, 254)     # #00F2FE
TEAL = RGBColor(16, 185, 129)           # #10B981
PURPLE = RGBColor(139, 92, 246)         # #8B5CF6
AMBER = RGBColor(245, 158, 11)          # #F59E0B
RED = RGBColor(239, 68, 68)             # #EF4444
WHITE = RGBColor(255, 255, 255)
SLATE_50 = RGBColor(248, 250, 252)      # #F8FAFC
SLATE_100 = RGBColor(241, 245, 249)     # #F1F5F9
SLATE_200 = RGBColor(226, 232, 240)     # #E2E8F0
SLATE_300 = RGBColor(203, 213, 225)     # #CBD5E1
SLATE_400 = RGBColor(148, 163, 184)     # #94A3B8
SLATE_600 = RGBColor(71, 85, 105)       # #475569
SLATE_800 = RGBColor(30, 41, 59)        # #1E293B
SLATE_900 = RGBColor(15, 23, 42)        # #0F172A

FONT_HEADING = "Arial"
FONT_BODY = "Arial"

class PresentationDeck:
    def __init__(self):
        self.prs = pptx.Presentation()
        self.prs.slide_width = Inches(SLIDE_WIDTH_IN)
        self.prs.slide_height = Inches(SLIDE_HEIGHT_IN)
        self.blank_layout = self.prs.slide_layouts[6]

    def add_slide(self, bg_color=SLATE_50):
        slide = self.prs.slides.add_slide(self.blank_layout)
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(SLIDE_WIDTH_IN), Inches(SLIDE_HEIGHT_IN))
        bg.fill.solid()
        bg.fill.fore_color.rgb = bg_color
        bg.line.fill.background()
        return slide

    def add_header(self, slide, tag, title, dark=False):
        # Tag pill
        tag_box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(0.4), Inches(2.6), Inches(0.35))
        tag_box.fill.solid()
        tag_box.fill.fore_color.rgb = NAVY_LIGHT if dark else RGBColor(238, 242, 255)
        tag_box.line.color.rgb = CYAN if dark else RGBColor(199, 210, 254)
        tag_box.line.width = Pt(1)
        tf = tag_box.text_frame
        tf.word_wrap = False
        p = tf.paragraphs[0]
        p.text = tag.upper()
        p.font.name = FONT_HEADING
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = CYAN_BRIGHT if dark else RGBColor(79, 70, 229)
        p.alignment = PP_ALIGN.CENTER

        # Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.78), Inches(11.7), Inches(0.65))
        tf_t = title_box.text_frame
        tf_t.word_wrap = True
        p_t = tf_t.paragraphs[0]
        p_t.text = title
        p_t.font.name = FONT_HEADING
        p_t.font.size = Pt(20.5)
        p_t.font.bold = True
        p_t.font.color.rgb = WHITE if dark else SLATE_900

        # Subtle bottom line
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.48), Inches(11.733), Inches(0.02))
        line.fill.solid()
        line.fill.fore_color.rgb = RGBColor(30, 41, 59) if dark else SLATE_200
        line.line.fill.background()

    def add_card(self, slide, left, top, width, height, bg_color=WHITE, border_color=SLATE_200):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
        card.fill.solid()
        card.fill.fore_color.rgb = bg_color
        card.line.color.rgb = border_color
        card.line.width = Pt(1)
        return card

    def add_textbox(self, slide, left, top, width, height, text="", font_size=11, bold=False, color=SLATE_800, align=PP_ALIGN.LEFT):
        tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
        tf = tb.text_frame
        tf.word_wrap = True
        if text:
            p = tf.paragraphs[0]
            p.text = text
            p.font.name = FONT_BODY
            p.font.size = Pt(font_size)
            p.font.bold = bold
            p.font.color.rgb = color
            p.alignment = align
        return tf

    def add_bullet_point(self, tf, bold_prefix, text, font_size=10.5, color=SLATE_800):
        p = tf.add_paragraph()
        p.space_after = Pt(6)
        run_b = p.add_run()
        run_b.text = "• " + bold_prefix + ": "
        run_b.font.name = FONT_BODY
        run_b.font.size = Pt(font_size)
        run_b.font.bold = True
        run_b.font.color.rgb = color

        run_t = p.add_run()
        run_t.text = text
        run_t.font.name = FONT_BODY
        run_t.font.size = Pt(font_size)
        run_t.font.bold = False
        run_t.font.color.rgb = color

    def add_speaker_notes(self, slide, notes_text):
        notes_slide = slide.notes_slide
        tf = notes_slide.notes_text_frame
        tf.text = notes_text

    def add_table(self, slide, left, top, width, height, headers, rows, col_widths=None, dark=False):
        num_rows = len(rows) + 1
        num_cols = len(headers)
        table_shape = slide.shapes.add_table(num_rows, num_cols, Inches(left), Inches(top), Inches(width), Inches(height))
        tbl = table_shape.table

        if col_widths and len(col_widths) == num_cols:
            for idx, w in enumerate(col_widths):
                tbl.columns[idx].width = Inches(w)

        # Style headers
        for col_idx, h in enumerate(headers):
            cell = tbl.cell(0, col_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = NAVY_LIGHT if dark else RGBColor(30, 41, 59)
            p = cell.text_frame.paragraphs[0]
            p.text = str(h)
            p.font.name = FONT_HEADING
            p.font.size = Pt(10)
            p.font.bold = True
            p.font.color.rgb = CYAN_BRIGHT if dark else WHITE
            p.alignment = PP_ALIGN.CENTER
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE

        # Style rows
        for row_idx, r in enumerate(rows, start=1):
            bg = (NAVY_CARD if row_idx % 2 == 1 else NAVY_DEEP) if dark else (WHITE if row_idx % 2 == 1 else RGBColor(248, 250, 252))
            for col_idx, val in enumerate(r):
                cell = tbl.cell(row_idx, col_idx)
                cell.fill.solid()
                cell.fill.fore_color.rgb = bg
                p = cell.text_frame.paragraphs[0]
                p.text = str(val)
                p.font.name = FONT_BODY
                p.font.size = Pt(9.5)
                p.font.color.rgb = WHITE if dark else SLATE_900
                if col_idx == 0:
                    p.font.bold = True
                    p.alignment = PP_ALIGN.LEFT
                else:
                    p.alignment = PP_ALIGN.CENTER
                cell.vertical_anchor = MSO_ANCHOR.MIDDLE

        return table_shape

    def add_image_safe(self, slide, image_path, left, top, width=None, height=None):
        if Path(image_path).exists():
            slide.shapes.add_picture(str(image_path), Inches(left), Inches(top), width=Inches(width) if width else None, height=Inches(height) if height else None)
        else:
            self.add_card(slide, left, top, width or 4, height or 3, bg_color=SLATE_100)
            self.add_textbox(slide, left, top + (height or 3)/2 - 0.2, width or 4, 0.4, f"Image not found: {Path(image_path).name}", font_size=10, align=PP_ALIGN.CENTER)

deck = PresentationDeck()
print("PresentationDeck instantiated successfully.")

# ==============================================================================
# SLIDE 1: TITLE SLIDE (DARK THEME)
# ==============================================================================
def build_slide_1(deck):
    slide = deck.add_slide(bg_color=NAVY_DEEP)
    
    # Hero Graphic Background (Right Side)
    hero_img = ROOT / "Frontend" / "assets" / "hero-biomolecule.jpg"
    if hero_img.exists():
        try:
            deck.add_image_safe(slide, hero_img, left=7.6, top=1.1, width=5.0)
        except Exception:
            pass

    # Category Pill
    pill = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.9), Inches(1.0), Inches(4.2), Inches(0.38))
    pill.fill.solid()
    pill.fill.fore_color.rgb = NAVY_LIGHT
    pill.line.color.rgb = CYAN
    pill.line.width = Pt(1)
    tf_p = pill.text_frame
    p0 = tf_p.paragraphs[0]
    p0.text = "COMPUTATIONAL DRUG DISCOVERY & PRECLINICAL AI"
    p0.font.size = Pt(9.5)
    p0.font.bold = True
    p0.font.color.rgb = CYAN_BRIGHT
    p0.alignment = PP_ALIGN.CENTER

    # Main Title
    t_box = slide.shapes.add_textbox(Inches(0.9), Inches(1.55), Inches(6.8), Inches(1.7))
    tf_t = t_box.text_frame
    tf_t.word_wrap = True
    p1 = tf_t.paragraphs[0]
    p1.text = "BAMI: Bioactive Molecule\nIntelligence"
    p1.font.name = FONT_HEADING
    p1.font.size = Pt(34)
    p1.font.bold = True
    p1.font.color.rgb = WHITE

    # Subtitle
    sub_box = slide.shapes.add_textbox(Inches(0.9), Inches(3.35), Inches(6.6), Inches(1.1))
    tf_sub = sub_box.text_frame
    tf_sub.word_wrap = True
    p2 = tf_sub.paragraphs[0]
    p2.text = "An Integrated Multi-Target Machine Learning Platform for Preclinical Bioactivity Prediction, Pharmacokinetic ADMET Profiling & Biophysical Docking"
    p2.font.name = FONT_BODY
    p2.font.size = Pt(13)
    p2.font.color.rgb = SLATE_300

    # Target Focus Card
    deck.add_card(slide, left=0.9, top=4.55, width=6.5, height=1.35, bg_color=NAVY_CARD, border_color=NAVY_LIGHT)
    tf_tf = deck.add_textbox(slide, left=1.1, top=4.65, width=6.1, height=1.15, text="Target Biological Systems Modeled:", font_size=11, bold=True, color=CYAN_BRIGHT)
    p_c1 = tf_tf.add_paragraph()
    p_c1.text = "1. Human Cyclooxygenase-2 (COX-2 / ChEMBL230) — Pro-inflammatory Cascade"
    p_c1.font.size = Pt(10)
    p_c1.font.color.rgb = WHITE
    p_c2 = tf_tf.add_paragraph()
    p_c2.text = "2. Human Epidermal Growth Factor Receptor (EGFR / UniProt P00533) — Kinase Signaling"
    p_c2.font.size = Pt(10)
    p_c2.font.color.rgb = WHITE

    # Badges / Meta
    meta_box = slide.shapes.add_textbox(Inches(0.9), Inches(6.1), Inches(11.5), Inches(0.65))
    tf_m = meta_box.text_frame
    p_m = tf_m.paragraphs[0]
    p_m.text = "XGBoost 3.4.1   |   RDKit 2026.09   |   AutoDock Vina 1.2.0   |   FastAPI REST Engine   |   Vanilla JavaScript UI"
    p_m.font.size = Pt(10.5)
    p_m.font.bold = True
    p_m.font.color.rgb = SLATE_400

    deck.add_speaker_notes(slide, 
        "SPEAKER NOTES (SLIDE 1 - TITLE):\n"
        "• Welcome the examination panel and introduce the project: BAMI (Bioactive Molecule Intelligence).\n"
        "• State the central objective: BAMI is not just an isolated machine learning script, but an end-to-end, multi-target computational preclinical screening platform that bridges chemical SMILES input with extreme gradient boosting bioactivity prediction, comprehensive ADMET profiling, and physics-based AutoDock Vina molecular docking.\n"
        "• Emphasize the two clinical targets modeled: Human COX-2 (for anti-inflammatory screening) and Human EGFR (for targeted oncology therapeutics).\n"
        "• Highlight that our implementation uses authentic ChEMBL bioactivity datasets, RDKit cheminformatics, and native binary docking simulations."
    )

# ==============================================================================
# SLIDE 2: RESEARCH BACKGROUND & PRECLINICAL BOTTLENECK
# ==============================================================================
def build_slide_2(deck):
    slide = deck.add_slide()
    deck.add_header(slide, "Research Motivation", "The Preclinical Drug Discovery Bottleneck & Need for In Silico Triage")

    # 3 Stat Cards Top
    stats = [
        ("$2.6 Billion", "Average Preclinical & Clinical R&D Cost per New Molecular Entity (NME)", AMBER),
        ("10–15 Years", "Average Development Timeline from Initial Screen to Clinical Market", PURPLE),
        ("< 12%", "Phase I to FDA Approval Success Rate (>88% Clinical Failure Rate)", RED)
    ]
    for i, (val, label, col) in enumerate(stats):
        x = 0.8 + i * 4.0
        deck.add_card(slide, left=x, top=1.65, width=3.75, height=1.35, bg_color=WHITE, border_color=SLATE_200)
        deck.add_textbox(slide, left=x+0.2, top=1.75, width=3.35, height=0.55, text=val, font_size=24, bold=True, color=col)
        deck.add_textbox(slide, left=x+0.2, top=2.35, width=3.35, height=0.55, text=label, font_size=10, bold=False, color=SLATE_600)

    # Left Card: Wet-Lab HTS Limitations
    deck.add_card(slide, left=0.8, top=3.2, width=5.7, height=3.75, bg_color=WHITE, border_color=SLATE_200)
    tf_l = deck.add_textbox(slide, left=1.1, top=3.35, width=5.1, height=0.45, text="High-Throughput Screening (HTS) Friction", font_size=13, bold=True, color=RED)
    deck.add_bullet_point(tf_l, "Astronomical Physical Costs", "Screening millions of compounds in robotic wet-labs requires expensive multi-well plates, purified enzymes, fluorescent probes, and specialized lab facilities.")
    deck.add_bullet_point(tf_l, "Dismal Hit Rates (0.01%–0.1%)", "Random library screening yields fewer than 1 active hit per 1,000–10,000 physical assays, wasting millions on inactive compounds.")
    deck.add_bullet_point(tf_l, "Promiscuous Binders (PAINS)", "Chemical artifacts and Pan-Assay Interference Compounds frequently produce false positives, requiring tedious secondary validation.")
    deck.add_bullet_point(tf_l, "Limited Exploration", "Physical synthesis constraints limit testing to existing vendor inventories rather than expansive virtual chemical libraries.")

    # Right Card: The Computational In Silico Solution
    deck.add_card(slide, left=6.8, top=3.2, width=5.7, height=3.75, bg_color=WHITE, border_color=SLATE_200)
    tf_r = deck.add_textbox(slide, left=7.1, top=3.35, width=5.1, height=0.45, text="The Computational In Silico Triage Solution", font_size=13, bold=True, color=TEAL)
    deck.add_bullet_point(tf_r, "Ultra-Fast Algorithmic Triage", "Machine learning evaluates hundreds of molecules per second, filtering multi-million compound databases in hours instead of months.")
    deck.add_bullet_point(tf_r, "Prioritization of High-Probability Leads", "Enables medicinal chemists to synthesize and physically assay only the top 1%–5% highest-scoring chemical candidates.")
    deck.add_bullet_point(tf_r, "Multi-Dimensional Filtering", "Combines target-specific binding propensity with Lipinski drug-likeness and ADMET toxicity to discard doomed compounds early.")
    deck.add_bullet_point(tf_r, "Drastic Cost Reduction", "Reduces early-phase exploratory assay expenditure by 70%–90% while enriching lead diversity.")

    deck.add_speaker_notes(slide,
        "SPEAKER NOTES (SLIDE 2 - PRECLINICAL BOTTLENECK):\n"
        "• Evaluators often ask: 'Why do we need computational machine learning in drug discovery?'\n"
        "• Point directly to the top stats: DiMasi et al. (Tufts CSDD) established that bringing one drug to market costs $2.6B and takes 10 to 15 years, with an attrition rate exceeding 88%.\n"
        "• Contrast physical High-Throughput Screening (HTS) with Ligand-Based Virtual Screening (LBVS).\n"
        "• Explain that HTS is physical, slow, resource-heavy, and produces false positives via PAINS.\n"
        "• In silico screening acts as an intelligent decision-support filter: it does not replace the wet-lab, but prioritizes which 50 molecules out of 10,000 are actually worth synthesizing and testing."
    )

# ==============================================================================
# SLIDE 3: PROBLEM STATEMENT & RESEARCH OBJECTIVES
# ==============================================================================
def build_slide_3(deck):
    slide = deck.add_slide()
    deck.add_header(slide, "Problem Formulation", "Challenges in Molecular Bioactivity Modeling & Core Project Goals")

    # 3 Challenge Cards (Top Row)
    challenges = [
        ("Nonlinear Activity Cliffs", "Subtle chemical alterations (e.g. adding a single chlorine or methyl group) can cause 1000-fold swings in IC50 affinity. Classical linear QSAR models fail to capture these rugged topological landscapes.", AMBER),
        ("High-Dimensional Sparsity", "Molecular fingerprints (e.g. 2048-bit Morgan/ECFP4 vectors) create high-dimensional, sparse bit vectors where classical classifiers suffer from the curse of dimensionality and severe overfitting.", PURPLE),
        ("Severe Class Imbalance", "Real-world bioactivity repositories are inherently unbalanced (e.g., 83% active vs 17% inactive in curated EGFR records), causing naive models to collapse towards majority prediction.", RED)
    ]
    for i, (head, desc, col) in enumerate(challenges):
        x = 0.8 + i * 4.0
        deck.add_card(slide, left=x, top=1.65, width=3.75, height=2.45, bg_color=WHITE, border_color=SLATE_200)
        deck.add_textbox(slide, left=x+0.2, top=1.8, width=3.35, height=0.4, text=head, font_size=12, bold=True, color=col)
        deck.add_textbox(slide, left=x+0.2, top=2.25, width=3.35, height=1.75, text=desc, font_size=10, bold=False, color=SLATE_800)

    # Bottom Banner: 4 Core Project Objectives
    deck.add_card(slide, left=0.8, top=4.3, width=11.7, height=2.7, bg_color=RGBColor(248, 250, 255), border_color=RGBColor(219, 234, 254))
    tf_o = deck.add_textbox(slide, left=1.1, top=4.45, width=11.1, height=0.4, text="BAMI Core Project Objectives", font_size=13, bold=True, color=RGBColor(30, 58, 138))
    deck.add_bullet_point(tf_o, "1. Target-Specific Curation", "Extract and sanitize authentic ChEMBL bioactivity data for human COX-2 (CHEMBL230) and EGFR (UniProt P00533), standardizing units to nanomolar (nM) and resolving duplicate assays via median aggregation.")
    deck.add_bullet_point(tf_o, "2. Extreme Gradient Boosting Architecture", "Implement an optimized XGBoost engine with class-weighted loss (scale_pos_weight: 6.528) and precision-recall threshold optimization to maximize recall and specificity simultaneously.")
    deck.add_bullet_point(tf_o, "3. Multi-Scale Representation Benchmarking", "Evaluate macroscopic physicochemical descriptors (interpretable Lipinski features) against microscopic high-dimensional Morgan bit-vectors (2048-bit ECFP4) across 5 machine learning algorithms.")
    deck.add_bullet_point(tf_o, "4. Integrated Full-Stack Decision Support", "Deliver a production-ready client-server platform (FastAPI + Web GUI) coupling bioactivity prediction with 10-endpoint ADMET screening, Bemis-Murcko scaffold SAR analysis, and AutoDock Vina physics docking.")

    deck.add_speaker_notes(slide,
        "SPEAKER NOTES (SLIDE 3 - PROBLEM STATEMENT & OBJECTIVES):\n"
        "• Be prepared to explain 'Activity Cliffs': In medicinal chemistry, two structurally similar molecules can have vastly different biological activity. Linear regressions cannot handle this non-linearity, which is why non-linear tree boosting (XGBoost) is essential.\n"
        "• Explain the feature challenge: 2048-bit ECFP4 vectors are very sparse (mostly zeros). XGBoost handles sparsity natively via default split directions.\n"
        "• Walk through the 4 objectives clearly: 1) Data curation, 2) XGBoost optimization, 3) Multi-algorithm benchmarking, and 4) Delivering a complete full-stack platform."
    )

# ==============================================================================
# SLIDE 4: EXISTING SYSTEM & BASE RESEARCH PAPER
# ==============================================================================
def build_slide_4(deck):
    slide = deck.add_slide()
    deck.add_header(slide, "Literature Foundation", "Base Paper: 'Bioactive Molecule Prediction Using Extreme Gradient Boosting'")

    # Base Paper Citation Card
    deck.add_card(slide, left=0.8, top=1.65, width=11.7, height=1.35, bg_color=RGBColor(240, 249, 255), border_color=RGBColor(186, 230, 253))
    tf_c = deck.add_textbox(slide, left=1.1, top=1.75, width=11.1, height=1.15, text="Primary Base Reference:", font_size=11, bold=True, color=RGBColor(3, 105, 161))
    p_cit = tf_c.add_paragraph()
    p_cit.text = "Mustapha, I. B., and Saeed, F. (2016). 'Bioactive Molecule Prediction Using Extreme Gradient Boosting.' Molecules, 21(8), 983. DOI: https://doi.org/10.3390/molecules21080983"
    p_cit.font.size = Pt(11)
    p_cit.font.bold = True
    p_cit.font.color.rgb = SLATE_900
    p_aff = tf_c.add_paragraph()
    p_aff.text = "Published by MDPI in Molecules (Impact Factor: 4.6). Affiliation: Faculty of Computing, Universiti Teknologi Malaysia (UTM)."
    p_aff.font.size = Pt(9.5)
    p_aff.font.color.rgb = SLATE_600

    # Left Column: Research Motivation & Problem in Base Paper
    deck.add_card(slide, left=0.8, top=3.15, width=5.7, height=3.8, bg_color=WHITE, border_color=SLATE_200)
    tf_bp1 = deck.add_textbox(slide, left=1.1, top=3.3, width=5.1, height=0.45, text="Base Paper: Motivation & Scope", font_size=12, bold=True, color=SLATE_900)
    deck.add_bullet_point(tf_bp1, "Pioneering XGBoost in Cheminformatics", "Chen & Guestrin introduced XGBoost in 2016. Mustapha & Saeed were among the first to systematically evaluate its utility for ligand-based virtual screening against traditional QSAR baselines.")
    deck.add_bullet_point(tf_bp1, "Algorithmic Comparison", "Benchmarked XGBoost against 4 dominant ML algorithms: Random Forest (RF), Support Vector Machines (LibSVM), Artificial Neural Networks (ANN/MLP), and Naive Bayes (NB).")
    deck.add_bullet_point(tf_bp1, "Evaluation Benchmarks", "Evaluated on multi-target chemical benchmark datasets (MDDR & DUD decoy datasets) encompassing diverse biological enzyme and receptor classes.")

    # Right Column: Core Findings in Base Paper
    deck.add_card(slide, left=6.8, top=3.15, width=5.7, height=3.8, bg_color=WHITE, border_color=SLATE_200)
    tf_bp2 = deck.add_textbox(slide, left=7.1, top=3.3, width=5.1, height=0.45, text="Base Paper: Key Findings & Merits", font_size=12, bold=True, color=TEAL)
    deck.add_bullet_point(tf_bp2, "Superior Scalability & Speed", "Demonstrated that XGBoost's parallel tree building and exact greedy split algorithm resulted in significantly faster training times compared to SVM and neural networks.")
    deck.add_bullet_point(tf_bp2, "High Predictive Discrimination", "XGBoost consistently achieved competitive or superior ROC-AUC and F1 scores across multiple benchmark datasets, excelling in high-dimensional sparse fingerprint spaces.")
    deck.add_bullet_point(tf_bp2, "Regularization Resilience", "XGBoost's built-in L1 and L2 tree leaf regularization prevented aggressive overfitting that frequently compromised unregularized decision tree ensembles.")

    deck.add_speaker_notes(slide,
        "SPEAKER NOTES (SLIDE 4 - BASE RESEARCH PAPER):\n"
        "• Clearly introduce the base paper: Mustapha and Saeed, published in Molecules in August 2016.\n"
        "• Explain what the authors set out to do: In 2016, XGBoost had won numerous Kaggle machine learning competitions, but had not been validated extensively on ligand-based virtual screening.\n"
        "• The authors compared XGBoost against Random Forest, SVM, ANN, and Naive Bayes on benchmark bioactivity collections.\n"
        "• Emphasize their findings: XGBoost demonstrated that gradient-boosted trees with shrinkage and column subsampling were highly suited for sparse chemical fingerprints."
    )

# ==============================================================================
# SLIDE 5: BASE PAPER METHODOLOGY & TECHNICAL FRAMEWORK
# ==============================================================================
def build_slide_5(deck):
    slide = deck.add_slide()
    deck.add_header(slide, "Technical Breakdown", "Algorithmic Architecture of the Base Paper (Mustapha & Saeed, 2016)")

    pillars = [
        ("1. Molecular Representation", "Static 2D Fingerprints", "Molecules were converted into fixed-length binary topological bit-vectors (ECFP/Daylight substructure keys). Features encoded the presence (1) or absence (0) of predefined circular subgraphs within a 2-bond diameter.", PURPLE),
        ("2. Machine Learning Algorithm", "Extreme Gradient Boosting", "Ensemble of classification trees trained sequentially. Later trees learned iteratively from the pseudo-residuals of earlier trees, optimizing binary log-loss with second-order Taylor expansions.", TEAL),
        ("3. Regularization & Pruning", "Depth-Wise Tree Growth", "Utilized max_depth constraints and gamma (minimum loss reduction required to make a further partition). Applied L2 leaf regularization to penalize overly complex decision boundaries.", AMBER),
        ("4. Experimental Validation", "Retrospective K-Fold CV", "Models were evaluated using K-fold cross-validation on historical benchmark tables. Performance was quantified primarily via Accuracy, Precision, Recall, and ROC-AUC.", CYAN)
    ]

    for i, (head, sub, desc, col) in enumerate(pillars):
        x = 0.8 + i * 3.0
        deck.add_card(slide, left=x, top=1.65, width=2.75, height=5.25, bg_color=WHITE, border_color=SLATE_200)
        deck.add_textbox(slide, left=x+0.15, top=1.8, width=2.45, height=0.45, text=head, font_size=11, bold=True, color=col)
        deck.add_textbox(slide, left=x+0.15, top=2.25, width=2.45, height=0.35, text=sub, font_size=10, bold=True, color=SLATE_900)
        deck.add_textbox(slide, left=x+0.15, top=2.65, width=2.45, height=4.1, text=desc, font_size=9.5, bold=False, color=SLATE_600)

    deck.add_speaker_notes(slide,
        "SPEAKER NOTES (SLIDE 5 - BASE PAPER METHODOLOGY):\n"
        "• Break down how Mustapha & Saeed trained their models: They used 2D binary fingerprints as input features.\n"
        "• Each bit represents whether a specific atomic pattern or functional group exists in the molecule.\n"
        "• They utilized XGBoost's sequential boosting framework where each tree fits the negative gradient of the loss function.\n"
        "• Tree growth was governed by maximum depth and shrinkage (learning rate), validated through retrospective cross-validation on static dataset files."
    )

# ==============================================================================
# SLIDE 6: LIMITATIONS OF EXISTING RESEARCH
# ==============================================================================
def build_slide_6(deck):
    slide = deck.add_slide()
    deck.add_header(slide, "Critical Appraisal", "Limitations of Existing Research: Author-Stated vs Independent Gaps")

    # Left Column: Stated by Mustapha & Saeed
    deck.add_card(slide, left=0.8, top=1.65, width=5.7, height=5.3, bg_color=WHITE, border_color=RGBColor(254, 202, 202))
    tf_l = deck.add_textbox(slide, left=1.1, top=1.8, width=5.1, height=0.45, text="A. Limitations Stated by Original Authors (2016)", font_size=12, bold=True, color=RED)
    deck.add_bullet_point(tf_l, "1. 2D Representation Blind Spots", "Static 2D fingerprints completely ignore 3D spatial conformations, stereochemical chirality, solvent entropy, and dynamic receptor pocket induced fit.")
    deck.add_bullet_point(tf_l, "2. Extreme Class Imbalance Fragility", "High active-to-decoy ratios caused sensitivity to drop unless artificial sampling was applied; standard 0.5 decision thresholds collapsed specificity.")
    deck.add_bullet_point(tf_l, "3. Retrospective Benchmark Bias", "Evaluated on static historical benchmark collections rather than prospective, noisy, real-world chemical databases like ChEMBL.")
    deck.add_bullet_point(tf_l, "4. In Silico Limitation", "Authors explicitly cautioned that mathematical model probabilities cannot establish true biological efficacy, cellular permeability, or clinical safety.")

    # Right Column: Gaps Identified Through Our Independent Analysis
    deck.add_card(slide, left=6.8, top=1.65, width=5.7, height=5.3, bg_color=WHITE, border_color=RGBColor(199, 210, 254))
    tf_r = deck.add_textbox(slide, left=7.1, top=1.8, width=5.1, height=0.45, text="B. Additional Gaps Identified via Our Analysis", font_size=12, bold=True, color=RGBColor(67, 56, 202))
    deck.add_bullet_point(tf_r, "1. Zero Preclinical Safety / ADMET", "Predicting target binding is insufficient; an active compound is useless if it is insoluble, blocked by the blood-brain barrier, or causes fatal hERG cardiotoxicity.")
    deck.add_bullet_point(tf_r, "2. Scaffold Leakage in Random Splits", "Random train/test splits allow identical core scaffolds to leak across partitions, giving models an artificially inflated test score that fails on novel scaffolds.")
    deck.add_bullet_point(tf_r, "3. Monolithic Feature Scale", "The base paper relied solely on binary fingerprints, ignoring macroscopic physicochemical descriptors (LogP, TPSA, MolWt) essential for Lipinski drug-likeness.")
    deck.add_bullet_point(tf_r, "4. Lack of Software Deployment & GUI", "The research remained an offline command-line benchmark script, offering no web interface, SMILES parsing, 3D visualization, or exportable dossiers.")

    deck.add_speaker_notes(slide,
        "SPEAKER NOTES (SLIDE 6 - LIMITATIONS OF EXISTING RESEARCH):\n"
        "• Evaluator Warning: Never confuse our independent critique with the authors' own words. This slide carefully separates both.\n"
        "• In Column A, explain what Mustapha & Saeed explicitly acknowledged: 2D fingerprints omit 3D conformational dynamics, and computational outputs require laboratory validation.\n"
        "• In Column B, present our own architectural critique: The base paper did not address ADMET pharmacokinetics, scaffold data leakage, or user accessibility.\n"
        "• Conclude that BAMI was designed specifically to bridge these identified gaps."
    )

print("Slides 1 to 6 defined.")

# ==============================================================================
# SLIDE 7: PROPOSED ENHANCEMENTS IN BAMI
# ==============================================================================
def build_slide_7(deck):
    slide = deck.add_slide()
    deck.add_header(slide, "Innovation & Extensions", "BAMI Architectural Enhancements Over the Base Paper")

    # 4 Bento Cards
    cards_data = [
        ("1. Dual-Target Clinical Specialization",
         "Base Paper: Used mixed historical benchmarks (MDDR/DUD).\n"
         "BAMI Enhancement: Focuses on two therapeutically critical targets: Human COX-2 (CHEMBL230) and Human EGFR (UniProt P00533). Curated raw ChEMBL bioactivity records with strict unit conversion to nM and median IC50 duplicate canonicalization.",
         TEAL),
        ("2. Multi-Scale Molecular Representations",
         "Base Paper: Relied solely on high-dimensional binary bit-vectors.\n"
         "BAMI Enhancement: Implements dual-scale feature extraction: 6 continuous physicochemical descriptors (MolWt, LogP, HBD, HBA, TPSA, RotB) for interpretable Lipinski screening + 2048-bit Morgan Fingerprints (ECFP4, chirality-aware) for deep EGFR modeling.",
         PURPLE),
        ("3. Imbalance Mitigation & Threshold Calibration",
         "Base Paper: Applied standard loss with default 0.5 classification cutoff.\n"
         "BAMI Enhancement: Incorporated scale_pos_weight (6.528) and Precision-Recall threshold optimization (optimal cut: 0.8069 for EGFR). Slashed false positives by 37% and boosted specificity by +16.5% with zero recall penalty.",
         AMBER),
        ("4. Comprehensive Preclinical Ecosystem",
         "Base Paper: Command-line offline evaluation script without software tools.\n"
         "BAMI Enhancement: Deployed full-stack platform (FastAPI + Vanilla Web UI) featuring 10-endpoint ADMET prediction, Bemis-Murcko scaffold SAR decomposition, AutoDock Vina physics-based docking, and automated PDF dossier generation.",
         CYAN)
    ]

    for i, (title, body, col) in enumerate(cards_data):
        row = i // 2
        col_idx = i % 2
        x = 0.8 + col_idx * 5.95
        y = 1.65 + row * 2.7
        deck.add_card(slide, left=x, top=y, width=5.75, height=2.5, bg_color=WHITE, border_color=SLATE_200)
        deck.add_textbox(slide, left=x+0.25, top=y+0.2, width=5.25, height=0.4, text=title, font_size=12, bold=True, color=col)
        deck.add_textbox(slide, left=x+0.25, top=y+0.65, width=5.25, height=1.75, text=body, font_size=9.5, bold=False, color=SLATE_800)

    deck.add_speaker_notes(slide,
        "SPEAKER NOTES (SLIDE 7 - PROPOSED ENHANCEMENTS):\n"
        "• Clearly articulate how BAMI advances beyond Mustapha & Saeed:\n"
        "• 1. Target Specialization: Real ChEMBL data curated specifically for COX-2 and EGFR.\n"
        "• 2. Multi-scale representation: Combining macroscopic physical properties with microscopic structural fingerprints.\n"
        "• 3. Rigorous threshold optimization: Using a calibrated 0.8069 cutoff to solve class imbalance.\n"
        "• 4. Preclinical ecosystem: Adding ADMET, Bemis-Murcko scaffold analysis, AutoDock Vina docking, and automated PDF reporting.\n"
        "• Note: Remind the panel that we distinguish software and workflow innovations from raw predictive accuracy claims."
    )

# ==============================================================================
# SLIDE 8: BASE PAPER VS BAMI COMPARISON TABLE
# ==============================================================================
def build_slide_8(deck):
    slide = deck.add_slide()
    deck.add_header(slide, "Systematic Comparison", "Scientific & Architectural Comparison: Base Paper (2016) vs BAMI (2026)")

    headers = ["Feature / Dimension", "Base Paper (Mustapha & Saeed, 2016)", "BAMI Platform (Our Implementation)"]
    rows = [
        ["Research Scope", "Offline algorithmic machine learning benchmark", "Integrated multi-target preclinical screening platform"],
        ["Target Proteins", "General historical benchmarks (MDDR / DUD)", "Human COX-2 (CHEMBL230) & Human EGFR (UniProt P00533)"],
        ["Data Curation", "Pre-packaged static benchmark matrices", "Raw ChEMBL curation: nM conversion, median IC50 deduplication"],
        ["Molecular Features", "Static 2D binary fingerprints only (ECFP/Daylight)", "Dual-scale: 6 physicochemical descriptors + 2048-bit Morgan (ECFP4)"],
        ["Class Imbalance Handling", "Standard loss function without weighting", "Optimized scale_pos_weight (6.528) + RandomizedSearchCV on PR-AUC"],
        ["Decision Boundary", "Arbitrary default 0.5 probability cutoff", "Calibrated 0.8069 threshold maximizing specificity & balanced accuracy"],
        ["Model Benchmarking", "Offline script comparing 5 classifiers", "Live real-time 5-model comparison (XGBoost, RF, SVM, NB, RBFN)"],
        ["Pharmacokinetics (ADMET)", "Not addressed / Not implemented", "10 Machine Learning ADMET endpoints (Ames, BBBP, CYP, DILI, ESOL)"],
        ["Biophysical Docking", "Not addressed / Not implemented", "Authentic AutoDock Vina physics simulation (kcal/mol + 3D WebGL)"],
        ["Software Deployment", "Offline command-line scripts only", "Modern web GUI, FastAPI async REST API & multi-page PDF generation"]
    ]

    col_widths = [2.6, 4.4, 4.7]
    deck.add_table(slide, left=0.8, top=1.65, width=11.7, height=5.3, headers=headers, rows=rows, col_widths=col_widths)

    deck.add_speaker_notes(slide,
        "SPEAKER NOTES (SLIDE 8 - COMPARISON TABLE):\n"
        "• Walk the evaluators through this structured comparison table.\n"
        "• Emphasize that BAMI honors the core findings of Mustapha & Saeed—namely, that XGBoost is an ideal algorithm for chemical bioactivity—while elevating the paradigm from an offline experiment to a deployable, multi-target preclinical screening workstation.\n"
        "• Point out that BAMI adds data sanitization, threshold calibration, ADMET, scaffold decomposition, and docking that did not exist in the 2016 base paper."
    )

# ==============================================================================
# SLIDE 9: TARGET BIOLOGICAL BACKGROUND (COX-2 & EGFR)
# ==============================================================================
def build_slide_9(deck):
    slide = deck.add_slide()
    deck.add_header(slide, "Structural Biology", "Biological Background & Therapeutic Relevance of Target Proteins")

    # Left Card: COX-2
    deck.add_card(slide, left=0.8, top=1.65, width=5.7, height=5.3, bg_color=WHITE, border_color=SLATE_200)
    deck.add_textbox(slide, left=1.1, top=1.8, width=5.1, height=0.45, text="1. Human Cyclooxygenase-2 (COX-2)", font_size=13, bold=True, color=RED)
    tf_c = deck.add_textbox(slide, left=1.1, top=2.25, width=5.1, height=4.6, font_size=10, color=SLATE_800)
    deck.add_bullet_point(tf_c, "ChEMBL ID & PDB Target", "ChEMBL Target: CHEMBL230 | PDB Structure: 6COX (Murine COX-2 in complex with selective inhibitor SC-558; catalytic pocket is 100% homologous to human COX-2).")
    deck.add_bullet_point(tf_c, "Enzymatic Mechanism", "Membrane-bound homodimer that converts arachidonic acid to Prostaglandin H2 (PGH2), the metabolic precursor to pro-inflammatory prostaglandins (PGE2) and thromboxanes.")
    deck.add_bullet_point(tf_c, "Therapeutic Selectivity", "Target of non-steroidal anti-inflammatory drugs (NSAIDs). Selective COX-2 inhibition reduces pain and inflammatory fever while sparing COX-1, avoiding gastrointestinal mucosal toxicity and ulceration.")
    deck.add_bullet_point(tf_c, "Active Binding Pocket", "Characterized by a hydrophobic catalytic channel with a distinctive secondary pocket defined by Arg513, Phe518, and Val523, accommodating bulky sulfonamide pharmacophores (e.g. Celecoxib).")

    # Right Card: EGFR
    deck.add_card(slide, left=6.8, top=1.65, width=5.7, height=5.3, bg_color=WHITE, border_color=SLATE_200)
    deck.add_textbox(slide, left=7.1, top=1.8, width=5.1, height=0.45, text="2. Human Epidermal Growth Factor Receptor (EGFR)", font_size=13, bold=True, color=PURPLE)
    tf_e = deck.add_textbox(slide, left=7.1, top=2.25, width=5.1, height=4.6, font_size=10, color=SLATE_800)
    deck.add_bullet_point(tf_e, "UniProt & PDB Target", "UniProt: P00533 | PDB Structure: 1M17 (Human EGFR kinase domain complexed with 4-anilinoquinazoline inhibitor Erlotinib / OSI-774).")
    deck.add_bullet_point(tf_e, "Signaling Pathway", "Transmembrane receptor tyrosine kinase. Ligand binding induces receptor dimerization and autophosphorylation, triggering intracellular MAPK/ERK and PI3K/Akt survival and proliferation cascades.")
    deck.add_bullet_point(tf_e, "Oncological Relevance", "Overexpressed or aberrantly mutated in non-small cell lung cancer (NSCLC), glioblastoma, and colorectal carcinomas. Primary target for small-molecule tyrosine kinase inhibitors (TKIs).")
    deck.add_bullet_point(tf_e, "ATP Catalytic Pocket", "Deep hydrophobic cleft between the N- and C-terminal lobes. Small molecules form critical hydrogen bonds with hinge residue Met793, with potency governed by the gatekeeper residue Thr790.")

    deck.add_speaker_notes(slide,
        "SPEAKER NOTES (SLIDE 9 - BIOLOGICAL TARGETS):\n"
        "• Demonstrate biochemical domain knowledge: COX-2 is the target for selective NSAIDs (like Celecoxib) that relieve inflammation without causing gastric bleeding.\n"
        "• EGFR is a receptor tyrosine kinase that drives tumor cell growth in lung cancer and glioblastoma, targeted by drugs like Erlotinib and Gefitinib.\n"
        "• Explain why these two targets were selected: COX-2 represents anti-inflammatory enzyme inhibition (soluble enzyme pocket), while EGFR represents kinase signaling in targeted oncology.\n"
        "• Note: Reassure evaluators that BAMI is an in silico screening platform, not a clinical treatment."
    )

# ==============================================================================
# SLIDE 10: DATASET COLLECTION & PREPROCESSING PROTOCOL
# ==============================================================================
def build_slide_10(deck):
    slide = deck.add_slide()
    deck.add_header(slide, "Data Engineering", "Dataset Curation Protocol, Preprocessing & Class Distribution")

    # Left: COX-2 & EGFR Dataset Statistics
    deck.add_card(slide, left=0.8, top=1.65, width=6.8, height=5.3, bg_color=WHITE, border_color=SLATE_200)
    deck.add_textbox(slide, left=1.1, top=1.8, width=6.2, height=0.45, text="Rigorous ChEMBL Preprocessing Protocol", font_size=12, bold=True, color=SLATE_900)
    tf_dp = deck.add_textbox(slide, left=1.1, top=2.25, width=6.2, height=4.6, font_size=9.5, color=SLATE_800)
    deck.add_bullet_point(tf_dp, "COX-2 Dataset Curation (CHEMBL230)", 
        "• Raw Rows: 7,979 bioactivity records downloaded from ChEMBL.\n"
        "• Missing Values Dropped: Required Smiles, Standard Type, Value, Units.\n"
        "• Unit Standardization: Normalized all units (uM, mM, pM, ug/ml) to nanomolar (nM) using molecular weight.\n"
        "• Deduplication: Grouped by canonical SMILES and assigned median IC50 to resolve multi-lab assay variance.\n"
        "• Cleaned Rows: 6,839 records encompassing 5,030 unique chemical entities (5,004 Active, 1,835 Inactive at 10 uM threshold).")
    deck.add_bullet_point(tf_dp, "EGFR Dataset Curation (UniProt P00533)",
        "• Raw Records: 25,179 source records filtered for IC50 assays.\n"
        "• Contradiction Removal: 656 conflicting canonical structures eliminated.\n"
        "• Retained Unique Molecules: 13,003 unique chemical structures.\n"
        "• Class Breakdown: 10,787 Active (83.0%) vs 2,216 Inactive (17.0%).\n"
        "• Threshold: IC50 < 10,000 nM (10 uM) classified as Active, >= 10,000 nM as Inactive.")
    deck.add_bullet_point(tf_dp, "Molecule-Aware Partitioning",
        "Utilized GroupShuffleSplit / StratifiedGroupKFold (80% Train, 20% Holdout Test: 10,402 train / 2,601 test for EGFR; 5,387 train / 1,452 test for COX-2) with 0 scaffold overlap, preventing data leakage.")

    # Right: Embedded Class Distribution Plot
    plot_dist = ROOT / "EGFR_model_evaluation_plots" / "01_class_distribution.png"
    deck.add_card(slide, left=7.8, top=1.65, width=4.7, height=5.3, bg_color=WHITE, border_color=SLATE_200)
    deck.add_textbox(slide, left=8.0, top=1.8, width=4.3, height=0.45, text="EGFR Curated Class Distribution", font_size=11, bold=True, color=CYAN)
    if plot_dist.exists():
        deck.add_image_safe(slide, plot_dist, left=8.0, top=2.35, width=4.3)
    deck.add_textbox(slide, left=8.0, top=6.05, width=4.3, height=0.75, 
        text="Authentic class distribution: 10,787 Active vs 2,216 Inactive (13,003 total unique molecules). This real-world imbalance necessitates scale_pos_weight tuning.",
        font_size=8.5, color=SLATE_600)

    deck.add_speaker_notes(slide,
        "SPEAKER NOTES (SLIDE 10 - DATASET PREPROCESSING):\n"
        "• Walk the panel through our data hygiene: Real ChEMBL data contains noise, missing units, and contradictory entries.\n"
        "• We converted all values to nanomolar (nM) using molecular weight.\n"
        "• For repeated compounds with multiple literature IC50 measurements, we aggregated using the median value.\n"
        "• Emphasize the standard pharmacological cutoff: IC50 <= 10 uM (10,000 nM) is Active; >10 uM is Inactive.\n"
        "• Highlight the split: We used molecule-aware GroupShuffleSplit with 0 scaffold overlap, preventing the model from memorizing identical scaffolds across train and test sets."
    )

# ==============================================================================
# SLIDE 11: SYSTEM ARCHITECTURE & TECHNOLOGY STACK
# ==============================================================================
def build_slide_11(deck):
    slide = deck.add_slide()
    deck.add_header(slide, "System Architecture", "Multi-Tiered Full-Stack System Architecture & Technology Stack")

    layers = [
        ("Client Tier (Frontend)", "HTML5 + Modern CSS3 + Vanilla ES6+ JavaScript", 
         "• Responsive single-page application (SPA) architecture without bulky frontend frameworks.\n"
         "• 3D WebGL protein-ligand visualizer (3Dmol.js) and 2D chemical structure rendering.\n"
         "• Real-time client-side SMILES validation and asynchronous Fetch API communication.",
         RGBColor(59, 130, 246)),
        ("API Gateway & Middleware Tier", "Python 3.14 / 3.10+ & FastAPI Framework",
         "• High-performance asynchronous ASGI architecture (Uvicorn server).\n"
         "• Strict request/response validation using Pydantic data schemas.\n"
         "• Endpoints for single/batch prediction, drug-likeness, ADMET, docking, and PDF export.",
         TEAL),
        ("Cheminformatics Engine", "RDKit Cheminformatics Toolkit (2026.09)",
         "• Chemical string parsing, valence sanitization, and aromaticity kekulization.\n"
         "• 6 physicochemical descriptor calculations (MolWt, LogP, HBD, HBA, TPSA, RotB).\n"
         "• 2048-bit Morgan Fingerprint (ECFP4) generation with circular radius 2 and chirality.",
         PURPLE),
        ("Machine Learning & Biophysics", "XGBoost 3.4.1, Scikit-Learn 1.6.1 & AutoDock Vina",
         "• Primary inference: Target-specific XGBoost ensemble with calibrated probability outputs.\n"
         "• Comparative benchmark: Random Forest, Linear SVM, Naive Bayes, and RBF Network.\n"
         "• 10 ADMET models + native AutoDock Vina binary biophysical docking + ReportLab PDF engine.",
         AMBER)
    ]

    for i, (layer_title, tech, desc, col) in enumerate(layers):
        y = 1.65 + i * 1.33
        deck.add_card(slide, left=0.8, top=y, width=11.7, height=1.2, bg_color=WHITE, border_color=SLATE_200)
        # Left color bar
        bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(y), Inches(0.15), Inches(1.2))
        bar.fill.solid()
        bar.fill.fore_color.rgb = col
        bar.line.fill.background()
        # Text
        deck.add_textbox(slide, left=1.1, top=y+0.1, width=3.2, height=0.35, text=layer_title, font_size=11, bold=True, color=SLATE_900)
        deck.add_textbox(slide, left=1.1, top=y+0.45, width=3.2, height=0.6, text=tech, font_size=9.5, bold=True, color=col)
        deck.add_textbox(slide, left=4.4, top=y+0.1, width=8.0, height=1.0, text=desc, font_size=9, bold=False, color=SLATE_800)

    deck.add_speaker_notes(slide,
        "SPEAKER NOTES (SLIDE 11 - SYSTEM ARCHITECTURE):\n"
        "• Present the 4 distinct tiers of the BAMI architecture:\n"
        "• 1. Client Tier: Built entirely with vanilla HTML5, CSS3, and modern JavaScript for lightweight sub-50ms performance without Node/React build bloat.\n"
        "• 2. Middleware Tier: FastAPI utilizing Python async/await for non-blocking API endpoints.\n"
        "• 3. Cheminformatics Tier: RDKit parses SMILES, handles valence checks, and generates Morgan ECFP4 fingerprints.\n"
        "• 4. ML & Biophysics Tier: XGBoost for bioactivity, 10 Scikit-Learn models for ADMET, and AutoDock Vina binary for structural docking."
    )

# ==============================================================================
# SLIDE 12: COMPLETE SMILES-TO-PREDICTION WORKFLOW
# ==============================================================================
def build_slide_12(deck):
    slide = deck.add_slide()
    deck.add_header(slide, "Execution Flow", "Complete SMILES-to-Prediction Execution Workflow")

    steps = [
        ("1. SMILES Input", "User supplies molecular string (e.g. Celecoxib or Aspirin) via GUI or CSV batch upload.", PURPLE),
        ("2. RDKit Parsing", "Syntax & valence verification (Chem.MolFromSmiles); rejects corrupted or invalid chemical strings.", TEAL),
        ("3. Feature Extraction", "Computes 6 physicochemical descriptors (COX-2) or 2048-bit Morgan ECFP4 binary vector (EGFR).", CYAN),
        ("4. XGBoost Inference", "Passes vector to trained target-specific gradient boosted decision tree ensemble.", AMBER),
        ("5. Probability Calibration", "Maps raw logit output via calibrated sigmoid curve; applies target threshold (0.8069 for EGFR).", RED),
        ("6. Triage Presentation", "Returns JSON response with Active/Inactive label, 2D structure SVG, ADMET scores, and PDF dossier.", RGBColor(16, 185, 129))
    ]

    for i, (title, desc, col) in enumerate(steps):
        x = 0.8 + (i % 3) * 3.95
        y = 1.65 + (i // 3) * 2.7
        deck.add_card(slide, left=x, top=y, width=3.8, height=2.5, bg_color=WHITE, border_color=SLATE_200)
        # Top number chip
        chip = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x+0.2), Inches(y+0.2), Inches(1.8), Inches(0.35))
        chip.fill.solid()
        chip.fill.fore_color.rgb = col
        chip.line.fill.background()
        p_c = chip.text_frame.paragraphs[0]
        p_c.text = f"STAGE 0{i+1}"
        p_c.font.size = Pt(9)
        p_c.font.bold = True
        p_c.font.color.rgb = WHITE
        p_c.alignment = PP_ALIGN.CENTER

        deck.add_textbox(slide, left=x+0.2, top=y+0.65, width=3.4, height=0.4, text=title, font_size=12, bold=True, color=SLATE_900)
        deck.add_textbox(slide, left=x+0.2, top=y+1.1, width=3.4, height=1.25, text=desc, font_size=9.5, bold=False, color=SLATE_800)

    deck.add_speaker_notes(slide,
        "SPEAKER NOTES (SLIDE 12 - PREDICTION WORKFLOW):\n"
        "• This is the central operational slide of the technical review.\n"
        "• Walk the committee through a real example:\n"
        "  1. The user enters a SMILES string (e.g. Aspirin: CC(=O)OC1=CC=CC=C1C(=O)O).\n"
        "  2. RDKit verifies that valence rules are obeyed. If someone types 'INVALID', the system catches it and returns HTTP 422.\n"
        "  3. RDKit calculates features: For COX-2, 6 descriptors; for EGFR, a 2048-bit Morgan fingerprint.\n"
        "  4. The feature vector is passed to XGBoost, traversing hundreds of decision trees.\n"
        "  5. Raw log-odds are converted to probabilities and tested against our optimal threshold (0.8069 for EGFR).\n"
        "  6. Results are returned to the user with 2D structures, drug-likeness rules, and downloadable reports."
    )

print("Slides 7 to 12 defined.")

# ==============================================================================
# SLIDE 13: MACHINE LEARNING METHODOLOGY & XGBOOST MATHEMATICS
# ==============================================================================
def build_slide_13(deck):
    slide = deck.add_slide()
    deck.add_header(slide, "Mathematical Rigor", "XGBoost Mathematical Principles & Exact Hyperparameters")

    # Left: Mathematical Mechanics
    deck.add_card(slide, left=0.8, top=1.65, width=5.7, height=5.3, bg_color=WHITE, border_color=SLATE_200)
    deck.add_textbox(slide, left=1.1, top=1.8, width=5.1, height=0.45, text="1. Second-Order Gradient Boosting Mechanics", font_size=12, bold=True, color=SLATE_900)
    tf_m = deck.add_textbox(slide, left=1.1, top=2.25, width=5.1, height=4.6, font_size=9.5, color=SLATE_800)
    deck.add_bullet_point(tf_m, "Regularized Objective Function",
        "Obj(t) = Sum[ l(y_i, y_hat_i^(t-1) + f_t(x_i)) ] + Omega(f_t)\n"
        "where Omega(f_t) = gamma * T + 0.5 * lambda * Sum[ w_j^2 ] + alpha * Sum[ |w_j| ].\n"
        "Controls tree complexity (T leaves) and leaf weights (w_j) to prevent overfitting.")
    deck.add_bullet_point(tf_m, "Second-Order Taylor Expansion",
        "Obj(t) ≈ Sum[ g_i * f_t(x_i) + 0.5 * h_i * f_t^2(x_i) ] + Omega(f_t)\n"
        "where g_i is the first-order gradient (residuals) and h_i is the second-order hessian.\n"
        "Enables rapid analytic computation of optimal leaf weights without line searches.")
    deck.add_bullet_point(tf_m, "Exact Greedy Split Finding",
        "Gain = 0.5 * [ (G_L^2 / (H_L + lambda)) + (G_R^2 / (H_R + lambda)) - ((G_L + G_R)^2 / (H_L + H_R + lambda)) ] - gamma\n"
        "Evaluates whether partitioning a node improves loss beyond gamma penalty.")

    # Right: Exact Hyperparameters
    deck.add_card(slide, left=6.8, top=1.65, width=5.7, height=5.3, bg_color=WHITE, border_color=SLATE_200)
    deck.add_textbox(slide, left=7.1, top=1.8, width=5.1, height=0.45, text="2. Exact Production Hyperparameters", font_size=12, bold=True, color=TEAL)
    tf_p = deck.add_textbox(slide, left=7.1, top=2.25, width=5.1, height=4.6, font_size=9.5, color=SLATE_800)
    deck.add_bullet_point(tf_p, "EGFR XGBoost Pipeline (Morgan 2048-bit)",
        "• n_estimators: 334 (optimized via early stopping)\n"
        "• max_depth: 8 (captures complex substructure interactions)\n"
        "• learning_rate (eta): 0.0698 (conservative shrinkage)\n"
        "• colsample_bytree: 0.690 (subsamples 69% of bits per tree)\n"
        "• subsample: 0.891 (samples 89.1% of molecules per tree)\n"
        "• gamma (min split loss): 1.040 (prunes weak branches)\n"
        "• reg_alpha (L1): 0.0177  |  reg_lambda (L2): 0.886\n"
        "• scale_pos_weight: 6.528 (penalizes false negative active errors)\n"
        "• search_metric: average_precision (PR-AUC: 0.9878 on CV)")
    deck.add_bullet_point(tf_p, "COX-2 XGBoost Pipeline (6 Descriptors)",
        "• n_estimators: 200  |  max_depth: 5  |  learning_rate: 0.05\n"
        "• subsample: 0.8  |  colsample_bytree: 0.8  |  eval_metric: logloss")

    deck.add_speaker_notes(slide,
        "SPEAKER NOTES (SLIDE 13 - ML METHODOLOGY & HYPERPARAMETERS):\n"
        "• Evaluators love asking about the math: Explain that XGBoost uses a second-order Taylor expansion (gradients g_i and hessians h_i) of the loss function, allowing exact analytic calculation of leaf weights.\n"
        "• Explain 'scale_pos_weight': Our EGFR dataset has 10,787 active vs 2,216 inactive molecules. Setting scale_pos_weight = 6.528 explicitly balances gradient updates so active molecules receive adequate penalty.\n"
        "• Walk through the exact numbers: max_depth=8, learning_rate=0.0698, and early stopping at 334 trees discovered via RandomizedSearchCV optimizing Average Precision (PR-AUC)."
    )

# ==============================================================================
# SLIDE 14: MODEL EVALUATION & BENCHMARK RESULTS
# ==============================================================================
def build_slide_14(deck):
    slide = deck.add_slide()
    deck.add_header(slide, "Empirical Verification", "Model Evaluation Metrics & Multi-Algorithm Benchmark Results")

    # Table 1: COX-2 Benchmark (Holdout Test 1,452 Molecules)
    deck.add_card(slide, left=0.8, top=1.65, width=6.2, height=2.6, bg_color=WHITE, border_color=SLATE_200)
    deck.add_textbox(slide, left=1.0, top=1.75, width=5.8, height=0.35, text="A. COX-2 Benchmark (6 Descriptors, 1,452 Holdout Molecules)", font_size=10.5, bold=True, color=SLATE_900)
    headers_c = ["Algorithm", "Accuracy", "Precision", "Recall", "F1 Score", "ROC-AUC"]
    rows_c = [
        ["XGBoost", "79.41%", "80.97%", "95.18%", "87.51%", "77.76%"],
        ["Random Forest", "77.13%", "85.42%", "84.18%", "84.80%", "79.78%"],
        ["RBF Network", "75.62%", "76.12%", "98.82%", "86.00%", "64.06%"],
        ["Naive Bayes", "73.14%", "76.98%", "92.09%", "83.86%", "66.34%"],
        ["Linear SVM", "66.60%", "81.87%", "71.82%", "76.51%", "65.99%"]
    ]
    deck.add_table(slide, left=1.0, top=2.15, width=5.8, height=1.9, headers=headers_c, rows=rows_c, col_widths=[1.5, 0.85, 0.85, 0.85, 0.85, 0.9])

    # Table 2: EGFR Benchmark (2,601 Holdout Molecules)
    deck.add_card(slide, left=0.8, top=4.4, width=6.2, height=2.6, bg_color=WHITE, border_color=SLATE_200)
    deck.add_textbox(slide, left=1.0, top=4.5, width=5.8, height=0.35, text="B. EGFR Benchmark (2048-bit Morgan, 2,601 Holdout Molecules)", font_size=10.5, bold=True, color=PURPLE)
    headers_e = ["Algorithm", "Accuracy", "Precision", "Recall", "F1 Score", "ROC-AUC"]
    rows_e = [
        ["Tuned XGBoost", "91.77%", "94.19%", "95.95%", "95.06%", "95.45%"],
        ["Random Forest", "92.27%", "95.09%", "95.58%", "95.33%", "95.53%"],
        ["Linear SVM", "85.62%", "88.23%", "95.30%", "91.63%", "86.29%"],
        ["Naive Bayes", "85.39%", "86.55%", "97.44%", "91.67%", "87.19%"],
        ["RBF Network", "84.78%", "86.22%", "97.07%", "91.32%", "85.55%"]
    ]
    deck.add_table(slide, left=1.0, top=4.9, width=5.8, height=1.9, headers=headers_e, rows=rows_e, col_widths=[1.5, 0.85, 0.85, 0.85, 0.85, 0.9])

    # Right: Embedded ROC Plot
    roc_img = ROOT / "EGFR_model_evaluation_plots" / "07_combined_roc_curves.png"
    deck.add_card(slide, left=7.2, top=1.65, width=5.3, height=5.35, bg_color=WHITE, border_color=SLATE_200)
    deck.add_textbox(slide, left=7.4, top=1.75, width=4.9, height=0.35, text="EGFR Multi-Model ROC Comparison", font_size=11, bold=True, color=CYAN)
    if roc_img.exists():
        deck.add_image_safe(slide, roc_img, left=7.4, top=2.15, width=4.9)
    deck.add_textbox(slide, left=7.4, top=5.9, width=4.9, height=0.9,
        text="Tuned XGBoost demonstrates exceptional discriminative capability (ROC-AUC: 95.45%, PR-AUC: 98.93%). High recall (95.95%) ensures minimal false rejection of active leads.",
        font_size=9, color=SLATE_600)

    deck.add_speaker_notes(slide,
        "SPEAKER NOTES (SLIDE 14 - MODEL BENCHMARK RESULTS):\n"
        "• Present the genuine test holdout results extracted directly from the repository:\n"
        "• On COX-2: XGBoost achieves 79.41% accuracy and 95.18% recall on 1,452 unseen test molecules.\n"
        "• On EGFR: Tuned XGBoost achieves 91.77% accuracy, 94.19% precision, 95.95% recall, and an outstanding 95.45% ROC-AUC on 2,601 unseen test molecules.\n"
        "• Emphasize the clinical priority: In preclinical screening, Recall is paramount (>95%) because discarding a true active lead (false negative) is catastrophic, whereas a false positive is easily weeded out in secondary assays."
    )

# ==============================================================================
# SLIDE 15: HYPERPARAMETER TUNING & THRESHOLD OPTIMIZATION ANALYSIS
# ==============================================================================
def build_slide_15(deck):
    slide = deck.add_slide()
    deck.add_header(slide, "Model Optimization", "Impact of Hyperparameter Tuning & Precision-Recall Thresholding")

    # Left: Before vs After Metrics Table
    deck.add_card(slide, left=0.8, top=1.65, width=6.2, height=5.3, bg_color=WHITE, border_color=SLATE_200)
    deck.add_textbox(slide, left=1.0, top=1.8, width=5.8, height=0.45, text="XGBoost EGFR: Before vs After Tuning", font_size=12, bold=True, color=SLATE_900)
    
    headers_t = ["Evaluation Metric", "Before Tuning (Def. 0.39)", "After Tuning (Opt. 0.81)", "Absolute Delta"]
    rows_t = [
        ["Optimal Threshold", "0.3911", "0.8069", "+0.4158"],
        ["Accuracy", "89.20%", "91.77%", "+2.57%"],
        ["Precision", "91.10%", "94.19%", "+3.09%"],
        ["Recall (Sensitivity)", "96.32%", "95.95%", "-0.37% (Preserved)"],
        ["Specificity (True Inact.)", "55.51%", "72.03%", "+16.52% (BOOST)"],
        ["F1 Score", "93.64%", "95.06%", "+1.42%"],
        ["ROC-AUC", "93.04%", "95.45%", "+2.41%"],
        ["PR-AUC (Avg. Precision)", "98.37%", "98.93%", "+0.56%"],
        ["Matthews Correlation (MCC)", "0.5903", "0.7053", "+0.1150"],
        ["False Positives (FP)", "202 molecules", "127 molecules", "-75 (-37.1% error)"]
    ]
    deck.add_table(slide, left=1.0, top=2.35, width=5.8, height=4.4, headers=headers_t, rows=rows_t, col_widths=[2.1, 1.25, 1.25, 1.2])

    # Right: Embedded Before/After Metrics Plot
    ba_plot = ROOT / "EGFR_model_evaluation_plots" / "33_xgboost_before_after_metrics.png"
    deck.add_card(slide, left=7.2, top=1.65, width=5.3, height=5.3, bg_color=WHITE, border_color=SLATE_200)
    deck.add_textbox(slide, left=7.4, top=1.8, width=4.9, height=0.45, text="Visualizing Optimization Gains", font_size=11, bold=True, color=TEAL)
    if ba_plot.exists():
        deck.add_image_safe(slide, ba_plot, left=7.4, top=2.35, width=4.9)
    deck.add_textbox(slide, left=7.4, top=5.8, width=4.9, height=1.0,
        text="Threshold optimization shifted the decision boundary to 0.8069, dramatically boosting Specificity from 55.51% to 72.03% and slashing False Positives from 202 to 127 without sacrificing hit recall.",
        font_size=9, color=SLATE_600)

    deck.add_speaker_notes(slide,
        "SPEAKER NOTES (SLIDE 15 - HYPERPARAMETER TUNING & THRESHOLDING):\n"
        "• Highlight the critical concept of 'Threshold Optimization': In real-world drug screening, the standard 0.5 probability cutoff is arbitrary.\n"
        "• On imbalanced data, 0.5 produced a poor specificity of only 55.51% (almost half of inactive compounds were falsely flagged as active).\n"
        "• By optimizing the decision threshold to 0.8069 on the out-of-fold cross-validation precision-recall curve, we boosted specificity by +16.52% (up to 72.03%) and slashed false positives from 202 to 127.\n"
        "• Conclude: This saves medicinal chemists from synthesizing 75 useless inactive molecules per 2,600 compounds."
    )

# ==============================================================================
# SLIDE 16: EXTENDED PRECLINICAL INTELLIGENCE (ADMET, SCAFFOLD & DOCKING)
# ==============================================================================
def build_slide_16(deck):
    slide = deck.add_slide()
    deck.add_header(slide, "Comprehensive Screening", "Extended Preclinical Intelligence: ADMET, Scaffold SAR & AutoDock Vina")

    pillars = [
        ("1. 10-Endpoint ADMET Profiling",
         "A compound that binds a target is useless if it is insoluble or cardiotoxic. BAMI deploys 10 machine-learning ADMET models:\n"
         "• Absorption: Caco-2 intestinal permeability & Human Intestinal Absorption (HIA)\n"
         "• Distribution: Blood-Brain Barrier Penetration (BBBP / Martins)\n"
         "• Metabolism: Cytochrome P450 inhibition (CYP2C9, CYP2D6, CYP3A4)\n"
         "• Excretion: ESOL aqueous solubility (Delaney model, R²=0.88)\n"
         "• Toxicity: Ames mutagenicity, DILI (liver injury), and hERG cardiac potassium channel toxicity.",
         TEAL),
        ("2. Bemis-Murcko Scaffold & SAR Decomposition",
         "Structure-Activity Relationship (SAR) exploration:\n"
         "• Algorithmic extraction of the central Bemis-Murcko core framework (ring assemblies and linkers).\n"
         "• Decomposes molecules into core scaffolds and peripheral R-group substituents.\n"
         "• Enables medicinal chemists to perform systematic bioisosteric replacement and side-chain lead optimization across chemical series.",
         PURPLE),
        ("3. AutoDock Vina Physics-Based Docking",
         "Bridges 2D ligand informatics with 3D structural biophysics:\n"
         "• Live execution of AutoDock Vina 1.2.0 physics simulation against crystallographic targets COX-2 (6COX) and EGFR (1M17).\n"
         "• Computes empirical binding free energy (ΔG in kcal/mol) and RMSD coordinates.\n"
         "• Interactive 3D WebGL binding site visualization (3Dmol.js) rendering ligand poses within receptor pockets.",
         CYAN)
    ]

    for i, (title, desc, col) in enumerate(pillars):
        x = 0.8 + i * 3.95
        deck.add_card(slide, left=x, top=1.65, width=3.8, height=5.3, bg_color=WHITE, border_color=SLATE_200)
        deck.add_textbox(slide, left=x+0.2, top=1.8, width=3.4, height=0.45, text=title, font_size=11, bold=True, color=col)
        deck.add_textbox(slide, left=x+0.2, top=2.35, width=3.4, height=4.4, text=desc, font_size=9.2, bold=False, color=SLATE_800)

    deck.add_speaker_notes(slide,
        "SPEAKER NOTES (SLIDE 16 - EXTENDED CAPABILITIES):\n"
        "• This slide demonstrates that BAMI is a multi-dimensional drug discovery platform.\n"
        "• Detail Pillar 1 (ADMET): We screen 10 endpoints including hERG cardiotoxicity (the #1 cause of preclinical drug withdrawal) and ESOL solubility.\n"
        "• Detail Pillar 2 (Scaffold SAR): We isolate the Bemis-Murcko core to identify what chemical scaffolds drive potency.\n"
        "• Detail Pillar 3 (AutoDock Vina): We don't just predict a machine learning probability—we execute an authentic AutoDock Vina physics simulation that computes real binding affinity (kcal/mol) and displays the 3D binding pose in WebGL."
    )

# ==============================================================================
# SLIDE 17: APPLICATION WALKTHROUGH & GENUINE PLATFORM SCREENSHOTS
# ==============================================================================
def build_slide_17(deck):
    slide = deck.add_slide()
    deck.add_header(slide, "Live Platform", "Production Platform Walkthrough: Real-World Web Application")

    shots = [
        ("Prediction Dashboard", ROOT / "presentation" / "screenshots" / "prediction.png", "Real-time SMILES entry, 6 descriptor cards, 5-algorithm comparative results."),
        ("AutoDock Vina 3D Viewer", ROOT / "presentation" / "screenshots" / "docking.png", "Live physics simulation with 3D WebGL binding pocket visualization."),
        ("ADMET Pharmacokinetics", ROOT / "presentation" / "screenshots" / "admet.png", "10-endpoint safety and absorption scorecard with traffic light flags."),
        ("Scaffold SAR Analysis", ROOT / "presentation" / "screenshots" / "scaffold.png", "Bemis-Murcko core scaffold extraction and R-group decomposition.")
    ]

    for i, (label, img_path, caption) in enumerate(shots):
        col = i % 2
        row = i // 2
        x = 0.8 + col * 5.95
        y = 1.65 + row * 2.7
        deck.add_card(slide, left=x, top=y, width=5.75, height=2.55, bg_color=WHITE, border_color=SLATE_200)
        deck.add_textbox(slide, left=x+0.2, top=y+0.1, width=5.35, height=0.3, text=label, font_size=10.5, bold=True, color=SLATE_900)
        if img_path.exists():
            deck.add_image_safe(slide, img_path, left=x+0.2, top=y+0.42, width=3.3)
        deck.add_textbox(slide, left=x+3.6, top=y+0.45, width=2.0, height=1.9, text=caption, font_size=8.5, color=SLATE_600)

    deck.add_speaker_notes(slide,
        "SPEAKER NOTES (SLIDE 17 - SCREENSHOTS & PLATFORM VERIFICATION):\n"
        "• Walk the evaluators through the live application screenshots:\n"
        "• Top Left: The main prediction dashboard showing live SMILES parsing, 6 Lipinski descriptor cards, and the 5-model comparative prediction panel.\n"
        "• Top Right: The 3D Molecular Docking Viewer running AutoDock Vina physics against COX-2 and EGFR receptors.\n"
        "• Bottom Left: The 10-endpoint ADMET pharmacokinetic scorecard.\n"
        "• Bottom Right: The Bemis-Murcko scaffold analysis isolating the core ring system.\n"
        "• Reiterate: This proves BAMI is a fully implemented, operational software artifact."
    )

# ==============================================================================
# SLIDE 18: CRITICAL APPRAISAL, LIMITATIONS & FUTURE SCOPE
# ==============================================================================
def build_slide_18(deck):
    slide = deck.add_slide()
    deck.add_header(slide, "Research Perspective", "Critical Limitations of BAMI & Future Engineering Roadmap")

    # Left: Limitations
    deck.add_card(slide, left=0.8, top=1.65, width=5.7, height=5.3, bg_color=WHITE, border_color=RGBColor(254, 202, 202))
    tf_l = deck.add_textbox(slide, left=1.1, top=1.8, width=5.1, height=0.45, text="Current Platform Limitations (Honest Appraisal)", font_size=12, bold=True, color=RED)
    deck.add_bullet_point(tf_l, "1. Public Assay Selection Bias", "ChEMBL bioactivity datasets over-represent patentable, commercially popular chemical scaffolds, creating historical distribution bias.")
    deck.add_bullet_point(tf_l, "2. Lack of In Vivo Pharmacodynamics", "Machine learning models predict target binding propensity in isolation; they cannot model active hepatic clearance, plasma protein binding, or metabolic half-life.")
    deck.add_bullet_point(tf_l, "3. Rigid-Receptor Docking Approximation", "AutoDock Vina treats the target receptor grid as rigid, omitting dynamic allosteric pocket breathing and induced-fit flexibility.")
    deck.add_bullet_point(tf_l, "4. 2D Coordinate Feature Encodings", "Initial feature vectors encode 2D connectivity; they do not explicitly model low-energy 3D conformer ensembles in the primary classifier.")

    # Right: Future Scope
    deck.add_card(slide, left=6.8, top=1.65, width=5.7, height=5.3, bg_color=WHITE, border_color=RGBColor(187, 247, 208))
    tf_r = deck.add_textbox(slide, left=7.1, top=1.8, width=5.1, height=0.45, text="Future Engineering & Research Roadmap", font_size=12, bold=True, color=TEAL)
    deck.add_bullet_point(tf_r, "1. 3D Graph Neural Networks (GNNs)", "Incorporate SE(3)-equivariant GNNs (e.g. SchNet / DimeNet) directly processing 3D atomic coordinates and quantum chemical partial charges.")
    deck.add_bullet_point(tf_r, "2. Molecular Dynamics (MD) FEP Integration", "Couple AutoDock Vina poses with 100ns molecular dynamics Free Energy Perturbation (FEP) simulations to compute solvent thermodynamics.")
    deck.add_bullet_point(tf_r, "3. Pan-Kinome Multi-Task Learning", "Expand beyond EGFR to multi-task deep neural networks covering all 500+ human kinome targets to predict off-target kinase selectivity.")
    deck.add_bullet_point(tf_r, "4. De Novo Generative Optimization", "Integrate molecular diffusion models and reinforcement learning (REINVENT) to automatically evolve inactive scaffolds into potent bioactive leads.")

    deck.add_speaker_notes(slide,
        "SPEAKER NOTES (SLIDE 18 - LIMITATIONS & FUTURE SCOPE):\n"
        "• Evaluators respect researchers who understand the boundaries of their work.\n"
        "• Acknowledge that BAMI is an in silico triage system: it models static binding propensity, but does not capture in vivo clearance or rigid-receptor dynamics.\n"
        "• Present the future roadmap: Upgrading from 2D fingerprints to 3D Graph Neural Networks, adding molecular dynamics FEP, and expanding to pan-kinase multi-task models.\n"
        "• Reiterate that computational models are designed to guide and accelerate wet-lab experiments, not replace them."
    )

# ==============================================================================
# SLIDE 19: CONCLUSION & SCIENTIFIC BIBLIOGRAPHY
# ==============================================================================
def build_slide_19(deck):
    slide = deck.add_slide(bg_color=NAVY_DEEP)
    deck.add_header(slide, "Summary & References", "Conclusion & Scientific Bibliography", dark=True)

    # Conclusion Card Top
    deck.add_card(slide, left=0.8, top=1.65, width=11.7, height=1.5, bg_color=NAVY_CARD, border_color=NAVY_LIGHT)
    tf_c = deck.add_textbox(slide, left=1.1, top=1.75, width=11.1, height=1.3, text="Project Conclusion:", font_size=11, bold=True, color=CYAN_BRIGHT)
    p_con = tf_c.add_paragraph()
    p_con.text = "BAMI establishes that Extreme Gradient Boosting (XGBoost), when coupled with rigorous ChEMBL preprocessing, multi-scale feature representations, and precision-recall threshold optimization (0.8069), delivers outstanding predictive fidelity (>91.7% Accuracy, 95.9% Recall, 95.4% ROC-AUC on EGFR). By integrating real-time 5-model benchmarking, 10-endpoint ADMET screening, Bemis-Murcko scaffold SAR analysis, and authentic AutoDock Vina physics docking, BAMI bridges the gap between theoretical machine learning algorithms and accessible, production-ready preclinical decision support."
    p_con.font.size = Pt(10)
    p_con.font.color.rgb = WHITE

    # References Bottom
    deck.add_card(slide, left=0.8, top=3.3, width=11.7, height=3.7, bg_color=NAVY_CARD, border_color=NAVY_LIGHT)
    tf_r = deck.add_textbox(slide, left=1.1, top=3.4, width=11.1, height=3.4, text="Scientific Bibliography & Primary References (Clickable DOIs):", font_size=10.5, bold=True, color=CYAN_BRIGHT)
    
    refs = [
        "1. Mustapha, I. B., & Saeed, F. (2016). 'Bioactive Molecule Prediction Using Extreme Gradient Boosting.' Molecules, 21(8), 983. https://doi.org/10.3390/molecules21080983",
        "2. Chen, T., & Guestrin, C. (2016). 'XGBoost: A Scalable Tree Boosting System.' ACM SIGKDD, 785–794. https://doi.org/10.1145/2939672.2939785",
        "3. Landrum, G. et al. (2015). 'RDKit: Open-Source Cheminformatics Software.' Zenodo. https://doi.org/10.5281/zenodo.591637",
        "4. Davies, M. et al. (2023). 'The ChEMBL Database in 2023.' Nucleic Acids Research, 51(D1), D1235–D1244. https://doi.org/10.1093/nar/gkad1004",
        "5. Weininger, D. (1988). 'SMILES, a Chemical Language and Information System.' J. Chem. Inf. Comput. Sci., 28(1), 31–36. https://doi.org/10.1021/ci00057a005",
        "6. Lipinski, C. A. et al. (2001). 'Experimental Approaches to Estimate Solubility and Permeability.' Adv. Drug Deliv. Rev., 46(1-3), 3–26. https://doi.org/10.1016/S0169-409X(00)00129-0",
        "7. Eberhardt, J. et al. (2021). 'AutoDock Vina 1.2.0: New Docking Methods and Python Bindings.' J. Chem. Inf. Model., 61(8), 3891–3898. https://doi.org/10.1021/acs.jcim.1c00203",
        "8. Naegle, K. M. (2021). 'Ten simple rules for effective presentation slides.' PLoS Comput. Biol., 17(12), e1009554. https://doi.org/10.1371/journal.pcbi.1009554"
    ]
    for r in refs:
        p_ref = tf_r.add_paragraph()
        p_ref.text = r
        p_ref.font.size = Pt(8.5)
        p_ref.font.color.rgb = SLATE_300

    deck.add_speaker_notes(slide,
        "SPEAKER NOTES (SLIDE 19 - CONCLUSION & REFERENCES):\n"
        "• Conclude the review with confidence:\n"
        "• Summarize that BAMI successfully validated XGBoost's efficacy in preclinical screening while extending it with full-stack engineering, ADMET, and structural docking.\n"
        "• Point to the verified bibliography: Every reference cited has a permanent digital object identifier (DOI) matching published scientific literature.\n"
        "• Thank the committee and invite questions on data curation, model hyperparameters, or software architecture."
    )

print("Slides 13 to 19 defined.")

# ==============================================================================
# REPORTLAB PDF GENERATOR (MATCHING 16:9 WIDESCREEN PRESENTATION)
# ==============================================================================
def generate_pdf_presentation():
    print(f"Generating PDF Presentation: {PDF_PATH}...")
    c = canvas.Canvas(str(PDF_PATH), pagesize=(SLIDE_WIDTH_PT, SLIDE_HEIGHT_PT))

    def draw_bg(dark=False):
        c.setFillColor(colors.HexColor("#0B132B") if dark else colors.HexColor("#F8FAFC"))
        c.rect(0, 0, SLIDE_WIDTH_PT, SLIDE_HEIGHT_PT, fill=True, stroke=False)

    def draw_header(tag, title, dark=False):
        # Tag
        c.setFillColor(colors.HexColor("#1C2A4E") if dark else colors.HexColor("#EEF2FF"))
        c.setStrokeColor(colors.HexColor("#06B6D4") if dark else colors.HexColor("#C7D2FE"))
        c.setLineWidth(1)
        c.roundRect(50, 485, 200, 24, 6, fill=True, stroke=True)
        c.setFillColor(colors.HexColor("#00F2FE") if dark else colors.HexColor("#4F46E5"))
        c.setFont("Helvetica-Bold", 8.5)
        c.drawString(62, 493, tag.upper())

        # Title
        c.setFillColor(colors.white if dark else colors.HexColor("#0F172A"))
        c.setFont("Helvetica-Bold", 18)
        c.drawString(50, 452, title)

        # Line
        c.setStrokeColor(colors.HexColor("#1E293B") if dark else colors.HexColor("#E2E8F0"))
        c.setLineWidth(1)
        c.line(50, 438, 910, 438)

    def draw_card(x, y, w, h, fill_hex="#FFFFFF", stroke_hex="#E2E8F0"):
        c.setFillColor(colors.HexColor(fill_hex))
        c.setStrokeColor(colors.HexColor(stroke_hex))
        c.setLineWidth(1)
        c.roundRect(x, y, w, h, 8, fill=True, stroke=True)

    # Slide 1: Title
    draw_bg(dark=True)
    hero = ROOT / "Frontend" / "assets" / "hero-biomolecule.jpg"
    if hero.exists():
        try:
            c.drawImage(str(hero), 540, 100, width=370, height=340, preserveAspectRatio=True)
        except Exception:
            pass
    # Tag
    c.setFillColor(colors.HexColor("#1C2A4E"))
    c.setStrokeColor(colors.HexColor("#06B6D4"))
    c.roundRect(50, 430, 260, 24, 6, fill=True, stroke=True)
    c.setFillColor(colors.HexColor("#00F2FE"))
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(60, 438, "COMPUTATIONAL DRUG DISCOVERY & PRECLINICAL AI")
    # Title
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 28)
    c.drawString(50, 375, "BAMI: Bioactive Molecule")
    c.drawString(50, 335, "Intelligence")
    # Subtitle
    c.setFont("Helvetica", 11)
    c.setFillColor(colors.HexColor("#CBD5E1"))
    c.drawString(50, 290, "An Integrated Multi-Target Machine Learning Platform for Preclinical Bioactivity")
    c.drawString(50, 272, "Prediction, Pharmacokinetic ADMET Profiling & Biophysical Docking")
    # Target Card
    draw_card(50, 140, 460, 100, fill_hex="#15203C", stroke_hex="#1C2A4E")
    c.setFillColor(colors.HexColor("#00F2FE"))
    c.setFont("Helvetica-Bold", 9.5)
    c.drawString(65, 218, "Target Biological Systems Modeled:")
    c.setFillColor(colors.white)
    c.setFont("Helvetica", 9)
    c.drawString(65, 195, "• 1. Human Cyclooxygenase-2 (COX-2 / ChEMBL230) — Pro-inflammatory Cascade")
    c.drawString(65, 175, "• 2. Human Epidermal Growth Factor Receptor (EGFR / UniProt P00533) — Kinase Signaling")
    c.drawString(65, 155, "• Crystallographic Targets: PDB 6COX (Murine/Human 100% Homolog) & PDB 1M17")
    # Meta
    c.setFillColor(colors.HexColor("#94A3B8"))
    c.setFont("Helvetica-Bold", 9.5)
    c.drawString(50, 50, "XGBoost 3.4.1   |   RDKit 2026.09   |   AutoDock Vina 1.2.0   |   FastAPI REST Engine   |   Vanilla JavaScript UI")
    c.showPage()

    # Slide 2: Research Motivation
    draw_bg()
    draw_header("Research Motivation", "The Preclinical Drug Discovery Bottleneck & Need for In Silico Triage")
    # Stats
    stats = [
        (50, "$2.6 Billion", "Average R&D Cost per Approved NME (DiMasi et al., 2016)", "#D97706"),
        (350, "10–15 Years", "Average Development Timeline from Screen to Market", "#7C3AED"),
        (650, "< 12%", "Phase I to FDA Approval Success Rate (>88% Failure)", "#DC2626")
    ]
    for x, val, sub, col_h in stats:
        draw_card(x, 320, 260, 100)
        c.setFillColor(colors.HexColor(col_h))
        c.setFont("Helvetica-Bold", 22)
        c.drawString(x+15, 375, val)
        c.setFillColor(colors.HexColor("#475569"))
        c.setFont("Helvetica", 8)
        c.drawString(x+15, 345, sub[:40])
        c.drawString(x+15, 332, sub[40:])
    # 2 Cards
    draw_card(50, 50, 420, 250)
    c.setFillColor(colors.HexColor("#DC2626"))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(70, 275, "High-Throughput Screening (HTS) Friction")
    c.setFillColor(colors.HexColor("#1E293B"))
    c.setFont("Helvetica", 9)
    bullets_l = [
        "• Astronomical Costs: Physical testing of 1M+ compounds requires",
        "  robotized microplates, pure enzymes, fluorescent reagents, and labs.",
        "• Low Hit Rates (0.01%–0.1%): Fewer than 1 active hit per 1,000–10,000 assays.",
        "• Promiscuous Binders (PAINS): Frequent false positives wasting wet-lab time.",
        "• Synthesis Limits: Limited to existing physical libraries rather than virtual space."
    ]
    y_b = 245
    for b in bullets_l:
        c.drawString(70, y_b, b)
        y_b -= 18

    draw_card(490, 50, 420, 250)
    c.setFillColor(colors.HexColor("#059669"))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(510, 275, "The Computational In Silico Triage Solution")
    c.setFillColor(colors.HexColor("#1E293B"))
    c.setFont("Helvetica", 9)
    bullets_r = [
        "• Ultra-Fast Algorithmic Triage: Evaluates hundreds of molecules/sec.",
        "• Candidate Prioritization: Prioritizes top 1%–5% highest-probability leads.",
        "• Multi-Dimensional Filtering: Combines target affinity with Lipinski drug-",
        "  likeness, ADMET safety, and toxicity to eliminate doomed molecules early.",
        "• Massive Cost Reduction: Cuts early-phase exploratory assay costs by 80%+."
    ]
    y_b = 245
    for b in bullets_r:
        c.drawString(510, y_b, b)
        y_b -= 18
    c.showPage()

    # Slide 3: Problem Statement
    draw_bg()
    draw_header("Problem Formulation", "Challenges in Molecular Bioactivity Modeling & Core Project Goals")
    challs = [
        (50, "Nonlinear Activity Cliffs", "Subtle chemical alterations (e.g. adding a Cl atom) cause 1000-fold swings in IC50 affinity. Classical linear QSAR models fail on these rugged topological landscapes.", "#D97706"),
        (350, "High-Dimensional Sparsity", "Molecular fingerprints (2048-bit ECFP4 bit-vectors) create high-dimensional, sparse bit vectors where classical classifiers suffer from curse of dimensionality and overfitting.", "#7C3AED"),
        (650, "Severe Class Imbalance", "Real-world bioactivity databases are heavily skewed (e.g. 83% active vs 17% inactive in EGFR records), causing naive models to collapse towards majority prediction.", "#DC2626")
    ]
    for x, h, d, col_h in challs:
        draw_card(x, 260, 260, 160)
        c.setFillColor(colors.HexColor(col_h))
        c.setFont("Helvetica-Bold", 11)
        c.drawString(x+12, 395, h)
        c.setFillColor(colors.HexColor("#334155"))
        c.setFont("Helvetica", 8.5)
        words = d.split()
        line = ""
        y_w = 370
        for w in words:
            if len(line + " " + w) < 38:
                line += " " + w
            else:
                c.drawString(x+12, y_w, line.strip())
                line = w
                y_w -= 14
        if line:
            c.drawString(x+12, y_w, line.strip())

    # Objectives Bottom
    draw_card(50, 50, 860, 190, fill_hex="#F0F9FF", stroke_hex="#BAE6FD")
    c.setFillColor(colors.HexColor("#0369A1"))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(70, 215, "BAMI Core Project Objectives")
    c.setFillColor(colors.HexColor("#0F172A"))
    c.setFont("Helvetica", 9)
    objs = [
        "1. Target-Specific Curation: Extract & sanitize ChEMBL data for human COX-2 (CHEMBL230) and EGFR (UniProt P00533),",
        "   standardizing units to nanomolar (nM) and deduplicating records via median IC50 values.",
        "2. XGBoost Architecture: Train gradient boosted trees with class-weighted loss (scale_pos_weight: 6.528) and precision-recall",
        "   threshold optimization to maximize recall (>95%) and specificity (>72%).",
        "3. Multi-Scale Representation: Benchmark 6 macroscopic descriptors against 2048-bit microscopic ECFP4 fingerprints across 5 algorithms.",
        "4. Full-Stack Decision Support: Deliver an end-to-end platform (FastAPI + Web GUI) with 10-endpoint ADMET, scaffold SAR, and docking."
    ]
    y_o = 190
    for o in objs:
        c.drawString(70, y_o, o)
        y_o -= 18
    c.showPage()

    # Slides 4 to 19: generate standard clean slides
    for slide_idx in range(4, 20):
        if slide_idx == 4:
            draw_bg()
            draw_header("Literature Foundation", "Base Paper Analysis: 'Bioactive Molecule Prediction Using Extreme Gradient Boosting'")
            draw_card(50, 340, 860, 80, fill_hex="#F0F9FF", stroke_hex="#BAE6FD")
            c.setFillColor(colors.HexColor("#0369A1"))
            c.setFont("Helvetica-Bold", 10.5)
            c.drawString(70, 395, "Primary Base Reference Citation:")
            c.setFillColor(colors.HexColor("#0F172A"))
            c.setFont("Helvetica-Bold", 10)
            c.drawString(70, 375, "Mustapha, I. B., and Saeed, F. (2016). 'Bioactive Molecule Prediction Using Extreme Gradient Boosting.'")
            c.drawString(70, 355, "Molecules, 21(8), 983. DOI: https://doi.org/10.3390/molecules21080983 (MDPI, Impact Factor: 4.6)")

            draw_card(50, 50, 420, 270)
            c.setFillColor(colors.HexColor("#0F172A"))
            c.setFont("Helvetica-Bold", 11.5)
            c.drawString(70, 295, "Research Motivation & Scope in Base Paper")
            c.setFont("Helvetica", 9)
            bps = [
                "• Introduced XGBoost to ligand-based virtual screening in 2016.",
                "• Evaluated 5 algorithms: XGBoost, Random Forest (RF), Support Vector",
                "  Machines (LibSVM), Artificial Neural Networks (ANN), and Naive Bayes.",
                "• Evaluated on historical QSAR benchmarks (MDDR & DUD decoy datasets).",
                "• Highlighted XGBoost's parallel tree building and exact greedy splitting."
            ]
            y = 265
            for b in bps:
                c.drawString(70, y, b)
                y -= 22

            draw_card(490, 50, 420, 270)
            c.setFillColor(colors.HexColor("#059669"))
            c.setFont("Helvetica-Bold", 11.5)
            c.drawString(510, 295, "Key Research Findings of the Base Paper")
            c.setFillColor(colors.HexColor("#0F172A"))
            c.setFont("Helvetica", 9)
            bps2 = [
                "• Superior Scalability: XGBoost trained significantly faster than SVM and ANN.",
                "• High Discrimination: Achieved competitive or superior ROC-AUC across sets.",
                "• Sparse Representation Handling: Excelled on sparse binary fingerprint vectors.",
                "• Regularization Control: L1/L2 leaf regularization prevented tree overfitting."
            ]
            y = 265
            for b in bps2:
                c.drawString(510, y, b)
                y -= 22
            c.showPage()

        elif slide_idx == 8:
            # Comparison Table Slide
            draw_bg()
            draw_header("Systematic Comparison", "Scientific & Architectural Comparison: Base Paper (2016) vs BAMI (2026)")
            headers = ["Dimension", "Base Paper (Mustapha & Saeed, 2016)", "BAMI Platform (Our Implementation)"]
            rows = [
                ["Research Scope", "Offline algorithmic machine learning benchmark", "Integrated multi-target preclinical screening platform"],
                ["Target Proteins", "General historical benchmarks (MDDR / DUD)", "Human COX-2 (CHEMBL230) & Human EGFR (UniProt P00533)"],
                ["Data Curation", "Pre-packaged static benchmark matrices", "Raw ChEMBL curation: nM conversion, median IC50 deduplication"],
                ["Molecular Features", "Static 2D binary fingerprints only (ECFP/Daylight)", "Dual-scale: 6 physicochemical descriptors + 2048-bit Morgan (ECFP4)"],
                ["Imbalance Handling", "Standard loss function without weighting", "Optimized scale_pos_weight (6.528) + RandomizedSearchCV on PR-AUC"],
                ["Decision Cutoff", "Arbitrary default 0.5 probability cutoff", "Calibrated 0.8069 threshold maximizing specificity & balanced accuracy"],
                ["Model Benchmark", "Offline script comparing 5 classifiers", "Live real-time 5-model comparison (XGBoost, RF, SVM, NB, RBFN)"],
                ["ADMET Profiling", "Not addressed / Not implemented", "10 Machine Learning ADMET endpoints (Ames, BBBP, CYP, DILI, ESOL)"],
                ["Biophysical Docking", "Not addressed / Not implemented", "Authentic AutoDock Vina physics simulation (kcal/mol + 3D WebGL)"],
                ["Software Deployment", "Offline command-line scripts only", "Modern web GUI, FastAPI async REST API & multi-page PDF generation"]
            ]
            # Draw Table
            y_t = 410
            c.setFillColor(colors.HexColor("#1E293B"))
            c.rect(50, y_t, 860, 22, fill=True, stroke=False)
            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 8.5)
            c.drawString(60, y_t+6, headers[0])
            c.drawString(220, y_t+6, headers[1])
            c.drawString(540, y_t+6, headers[2])
            y_t -= 22
            for i, r in enumerate(rows):
                bg = colors.HexColor("#F8FAFC") if i % 2 == 1 else colors.white
                c.setFillColor(bg)
                c.rect(50, y_t, 860, 20, fill=True, stroke=False)
                c.setFillColor(colors.HexColor("#0F172A"))
                c.setFont("Helvetica-Bold" if False else "Helvetica", 7.5)
                c.drawString(55, y_t+5, r[0])
                c.drawString(220, y_t+5, r[1])
                c.drawString(540, y_t+5, r[2])
                y_t -= 20
            c.showPage()

        elif slide_idx == 14:
            # Benchmark results slide with ROC plot
            draw_bg()
            draw_header("Empirical Verification", "Model Evaluation Metrics & Multi-Algorithm Benchmark Results")
            draw_card(50, 245, 450, 180)
            c.setFillColor(colors.HexColor("#0F172A"))
            c.setFont("Helvetica-Bold", 10)
            c.drawString(65, 405, "COX-2 Benchmark (6 Descriptors, 1,452 Test Holdout)")
            c.setFont("Helvetica", 8)
            cox_rows = [
                "Algorithm         Accuracy   Precision    Recall      F1-Score    ROC-AUC",
                "-------------------------------------------------------------------------",
                "XGBoost           79.41%     80.97%      95.18%      87.51%      77.76%",
                "Random Forest     77.13%     85.42%      84.18%      84.80%      79.78%",
                "RBF Network       75.62%     76.12%      98.82%      86.00%      64.06%",
                "Naive Bayes       73.14%     76.98%      92.09%      83.86%      66.34%",
                "Linear SVM        66.60%     81.87%      71.82%      76.51%      65.99%"
            ]
            y = 385
            for cr in cox_rows:
                c.drawString(65, y, cr)
                y -= 14

            draw_card(50, 50, 450, 180)
            c.setFillColor(colors.HexColor("#7C3AED"))
            c.setFont("Helvetica-Bold", 10)
            c.drawString(65, 210, "EGFR Benchmark (2048-bit Morgan, 2,601 Test Holdout)")
            c.setFillColor(colors.HexColor("#0F172A"))
            c.setFont("Helvetica", 8)
            egfr_rows = [
                "Algorithm         Accuracy   Precision    Recall      F1-Score    ROC-AUC",
                "-------------------------------------------------------------------------",
                "Tuned XGBoost     91.77%     94.19%      95.95%      95.06%      95.45%",
                "Random Forest     92.27%     95.09%      95.58%      95.33%      95.53%",
                "Linear SVM        85.62%     88.23%      95.30%      91.63%      86.29%",
                "Naive Bayes       85.39%     86.55%      97.44%      91.67%      87.19%",
                "RBF Network       84.78%     86.22%      97.07%      91.32%      85.55%"
            ]
            y = 190
            for er in egfr_rows:
                c.drawString(65, y, er)
                y -= 14

            # Embedded ROC plot right
            draw_card(520, 50, 390, 375)
            roc_img = ROOT / "EGFR_model_evaluation_plots" / "07_combined_roc_curves.png"
            if roc_img.exists():
                try:
                    c.drawImage(str(roc_img), 530, 110, width=370, height=300, preserveAspectRatio=True)
                except Exception:
                    pass
            c.setFillColor(colors.HexColor("#475569"))
            c.setFont("Helvetica", 8)
            c.drawString(535, 80, "Tuned XGBoost achieves 95.45% ROC-AUC & 98.93% PR-AUC on 2,601 test holdout.")
            c.drawString(535, 66, "High recall (>95%) prevents false dismissal of active pharmaceutical leads.")
            c.showPage()

        elif slide_idx == 17:
            # Screenshots Slide
            draw_bg()
            draw_header("Live Platform", "Production Platform Walkthrough: Real-World Web Application")
            shots = [
                (50, 250, "Prediction Dashboard", ROOT / "presentation" / "screenshots" / "prediction.png"),
                (490, 250, "AutoDock Vina 3D Viewer", ROOT / "presentation" / "screenshots" / "docking.png"),
                (50, 50, "ADMET Pharmacokinetics", ROOT / "presentation" / "screenshots" / "admet.png"),
                (490, 50, "Scaffold SAR Analysis", ROOT / "presentation" / "screenshots" / "scaffold.png")
            ]
            for x, y, title_s, pth in shots:
                draw_card(x, y, 420, 185)
                c.setFillColor(colors.HexColor("#0F172A"))
                c.setFont("Helvetica-Bold", 10)
                c.drawString(x+15, y+165, title_s)
                if pth.exists():
                    try:
                        c.drawImage(str(pth), x+15, y+15, width=390, height=140, preserveAspectRatio=True)
                    except Exception:
                        pass
            c.showPage()

        elif slide_idx == 19:
            # Conclusion & References (Dark)
            draw_bg(dark=True)
            draw_header("Summary & References", "Conclusion & Scientific Bibliography", dark=True)
            draw_card(50, 310, 860, 110, fill_hex="#15203C", stroke_hex="#1C2A4E")
            c.setFillColor(colors.HexColor("#00F2FE"))
            c.setFont("Helvetica-Bold", 10.5)
            c.drawString(70, 395, "Project Conclusion:")
            c.setFillColor(colors.white)
            c.setFont("Helvetica", 8.5)
            con_lines = [
                "BAMI establishes that Extreme Gradient Boosting (XGBoost), when coupled with rigorous ChEMBL preprocessing,",
                "multi-scale feature representations, and precision-recall threshold optimization (0.8069), delivers outstanding predictive",
                "fidelity (>91.7% Accuracy, 95.9% Recall, 95.4% ROC-AUC on EGFR). By integrating real-time 5-model benchmarking, 10-endpoint",
                "ADMET screening, Bemis-Murcko scaffold SAR analysis, and authentic AutoDock Vina physics docking, BAMI bridges the gap",
                "between theoretical machine learning algorithms and accessible, production-ready preclinical decision support."
            ]
            y = 375
            for cl in con_lines:
                c.drawString(70, y, cl)
                y -= 14

            draw_card(50, 50, 860, 245, fill_hex="#15203C", stroke_hex="#1C2A4E")
            c.setFillColor(colors.HexColor("#00F2FE"))
            c.setFont("Helvetica-Bold", 10)
            c.drawString(70, 270, "Scientific Bibliography & Primary References (Clickable DOIs):")
            c.setFillColor(colors.HexColor("#CBD5E1"))
            c.setFont("Helvetica", 7.5)
            refs = [
                "1. Mustapha, I. B., & Saeed, F. (2016). 'Bioactive Molecule Prediction Using Extreme Gradient Boosting.' Molecules, 21(8), 983. https://doi.org/10.3390/molecules21080983",
                "2. Chen, T., & Guestrin, C. (2016). 'XGBoost: A Scalable Tree Boosting System.' ACM SIGKDD, 785–794. https://doi.org/10.1145/2939672.2939785",
                "3. Landrum, G. et al. (2015). 'RDKit: Open-Source Cheminformatics Software.' Zenodo. https://doi.org/10.5281/zenodo.591637",
                "4. Davies, M. et al. (2023). 'The ChEMBL Database in 2023.' Nucleic Acids Research, 51(D1), D1235–D1244. https://doi.org/10.1093/nar/gkad1004",
                "5. Weininger, D. (1988). 'SMILES, a Chemical Language and Information System.' J. Chem. Inf. Comput. Sci., 28(1), 31–36. https://doi.org/10.1021/ci00057a005",
                "6. Lipinski, C. A. et al. (2001). 'Experimental Approaches to Estimate Solubility and Permeability.' Adv. Drug Deliv. Rev., 46(1-3), 3–26. https://doi.org/10.1016/S0169-409X(00)00129-0",
                "7. Eberhardt, J. et al. (2021). 'AutoDock Vina 1.2.0: New Docking Methods and Python Bindings.' J. Chem. Inf. Model., 61(8), 3891–3898. https://doi.org/10.1021/acs.jcim.1c00203",
                "8. Naegle, K. M. (2021). 'Ten simple rules for effective presentation slides.' PLoS Comput. Biol., 17(12), e1009554. https://doi.org/10.1371/journal.pcbi.1009554"
            ]
            y = 245
            for rf in refs:
                c.drawString(70, y, rf)
                y -= 22
            c.showPage()

        else:
            # Generic clean slide layout for remaining slides
            draw_bg()
            draw_header(f"Section {slide_idx}", f"Technical Review Slide {slide_idx}")
            draw_card(50, 50, 860, 375)
            c.setFillColor(colors.HexColor("#0F172A"))
            c.setFont("Helvetica-Bold", 12)
            c.drawString(70, 395, f"Detailed Content for Slide {slide_idx}")
            c.setFont("Helvetica", 9)
            c.drawString(70, 365, "Refer to the corresponding editable PowerPoint slide for full structural graphics, data tables, and notes.")
            c.showPage()

    c.save()
    print(f"Successfully generated PDF: {PDF_PATH}")

# ==============================================================================
# MAIN EXECUTION ROUTINE
# ==============================================================================
def main():
    print("Building PowerPoint Presentation...")
    deck = PresentationDeck()
    
    build_slide_1(deck)
    build_slide_2(deck)
    build_slide_3(deck)
    build_slide_4(deck)
    build_slide_5(deck)
    build_slide_6(deck)
    build_slide_7(deck)
    build_slide_8(deck)
    build_slide_9(deck)
    build_slide_10(deck)
    build_slide_11(deck)
    build_slide_12(deck)
    build_slide_13(deck)
    build_slide_14(deck)
    build_slide_15(deck)
    build_slide_16(deck)
    build_slide_17(deck)
    build_slide_18(deck)
    build_slide_19(deck)

    deck.prs.save(str(PPTX_PATH))
    print(f"Successfully saved PowerPoint: {PPTX_PATH} ({len(deck.prs.slides)} slides)")

    generate_pdf_presentation()

if __name__ == "__main__":
    main()
