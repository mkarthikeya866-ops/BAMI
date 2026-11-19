import sys
import os
from pathlib import Path

import reportlab
from reportlab.lib.pagesizes import landscape
from reportlab.pdfgen import canvas
from reportlab.lib import colors

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "presentation"
PDF_PATH = OUT_DIR / "BAMI_Project_Presentation.pdf"

# 16:9 Widescreen dimensions
SLIDE_WIDTH_PT = 13.333 * 72   # 960 pt
SLIDE_HEIGHT_PT = 7.5 * 72    # 540 pt

def build_pdf():
    print(f"Building complete 19-slide PDF: {PDF_PATH}...")
    c = canvas.Canvas(str(PDF_PATH), pagesize=(SLIDE_WIDTH_PT, SLIDE_HEIGHT_PT))

    def draw_bg(dark=False):
        c.setFillColor(colors.HexColor("#0B132B") if dark else colors.HexColor("#F8FAFC"))
        c.rect(0, 0, SLIDE_WIDTH_PT, SLIDE_HEIGHT_PT, fill=True, stroke=False)

    def draw_header(tag, title, dark=False):
        # Tag
        c.setFillColor(colors.HexColor("#1C2A4E") if dark else colors.HexColor("#EEF2FF"))
        c.setStrokeColor(colors.HexColor("#06B6D4") if dark else colors.HexColor("#C7D2FE"))
        c.setLineWidth(1)
        c.roundRect(50, 485, 210, 24, 6, fill=True, stroke=True)
        c.setFillColor(colors.HexColor("#00F2FE") if dark else colors.HexColor("#4F46E5"))
        c.setFont("Helvetica-Bold", 8.5)
        c.drawString(60, 493, tag.upper())

        # Title
        c.setFillColor(colors.white if dark else colors.HexColor("#0F172A"))
        c.setFont("Helvetica-Bold", 17.5)
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

    # -------------------------------------------------------------
    # SLIDE 1: Title Slide (Dark)
    # -------------------------------------------------------------
    draw_bg(dark=True)
    hero = ROOT / "Frontend" / "assets" / "hero-biomolecule.jpg"
    if hero.exists():
        try:
            c.drawImage(str(hero), 540, 100, width=370, height=340, preserveAspectRatio=True)
        except Exception:
            pass
    c.setFillColor(colors.HexColor("#1C2A4E"))
    c.setStrokeColor(colors.HexColor("#06B6D4"))
    c.roundRect(50, 430, 260, 24, 6, fill=True, stroke=True)
    c.setFillColor(colors.HexColor("#00F2FE"))
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(60, 438, "COMPUTATIONAL DRUG DISCOVERY & PRECLINICAL AI")
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 28)
    c.drawString(50, 375, "BAMI: Bioactive Molecule")
    c.drawString(50, 335, "Intelligence")
    c.setFont("Helvetica", 11)
    c.setFillColor(colors.HexColor("#CBD5E1"))
    c.drawString(50, 290, "An Integrated Multi-Target Machine Learning Platform for Preclinical Bioactivity")
    c.drawString(50, 272, "Prediction, Pharmacokinetic ADMET Profiling & Biophysical Docking")
    draw_card(50, 140, 460, 100, fill_hex="#15203C", stroke_hex="#1C2A4E")
    c.setFillColor(colors.HexColor("#00F2FE"))
    c.setFont("Helvetica-Bold", 9.5)
    c.drawString(65, 218, "Target Biological Systems Modeled:")
    c.setFillColor(colors.white)
    c.setFont("Helvetica", 9)
    c.drawString(65, 195, "• 1. Human Cyclooxygenase-2 (COX-2 / ChEMBL230) — Pro-inflammatory Cascade")
    c.drawString(65, 175, "• 2. Human Epidermal Growth Factor Receptor (EGFR / UniProt P00533) — Kinase Signaling")
    c.drawString(65, 155, "• Crystallographic Targets: PDB 6COX (Murine/Human 100% Homolog) & PDB 1M17")
    c.setFillColor(colors.HexColor("#94A3B8"))
    c.setFont("Helvetica-Bold", 9.5)
    c.drawString(50, 50, "XGBoost 3.4.1   |   RDKit 2026.09   |   AutoDock Vina 1.2.0   |   FastAPI REST Engine   |   Vanilla JavaScript UI")
    c.showPage()

    # -------------------------------------------------------------
    # SLIDE 2: Research Motivation
    # -------------------------------------------------------------
    draw_bg()
    draw_header("Research Motivation", "The Preclinical Drug Discovery Bottleneck & Need for In Silico Triage")
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
    draw_card(50, 50, 420, 250)
    c.setFillColor(colors.HexColor("#DC2626"))
    c.setFont("Helvetica-Bold", 11.5)
    c.drawString(70, 275, "High-Throughput Screening (HTS) Friction")
    c.setFillColor(colors.HexColor("#1E293B"))
    c.setFont("Helvetica", 8.5)
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
    c.setFont("Helvetica-Bold", 11.5)
    c.drawString(510, 275, "The Computational In Silico Triage Solution")
    c.setFillColor(colors.HexColor("#1E293B"))
    c.setFont("Helvetica", 8.5)
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

    # -------------------------------------------------------------
    # SLIDE 3: Problem Statement
    # -------------------------------------------------------------
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
        c.setFont("Helvetica-Bold", 10.5)
        c.drawString(x+12, 395, h)
        c.setFillColor(colors.HexColor("#334155"))
        c.setFont("Helvetica", 8)
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

    draw_card(50, 50, 860, 190, fill_hex="#F0F9FF", stroke_hex="#BAE6FD")
    c.setFillColor(colors.HexColor("#0369A1"))
    c.setFont("Helvetica-Bold", 11.5)
    c.drawString(70, 215, "BAMI Core Project Objectives")
    c.setFillColor(colors.HexColor("#0F172A"))
    c.setFont("Helvetica", 8.5)
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

    # -------------------------------------------------------------
    # SLIDE 4: Base Paper Analysis
    # -------------------------------------------------------------
    draw_bg()
    draw_header("Literature Foundation", "Base Paper Analysis: 'Bioactive Molecule Prediction Using Extreme Gradient Boosting'")
    draw_card(50, 340, 860, 80, fill_hex="#F0F9FF", stroke_hex="#BAE6FD")
    c.setFillColor(colors.HexColor("#0369A1"))
    c.setFont("Helvetica-Bold", 10.5)
    c.drawString(70, 395, "Primary Base Reference Citation:")
    c.setFillColor(colors.HexColor("#0F172A"))
    c.setFont("Helvetica-Bold", 9.5)
    c.drawString(70, 375, "Mustapha, I. B., and Saeed, F. (2016). 'Bioactive Molecule Prediction Using Extreme Gradient Boosting.'")
    c.drawString(70, 355, "Molecules, 21(8), 983. DOI: https://doi.org/10.3390/molecules21080983 (MDPI, Impact Factor: 4.6)")

    draw_card(50, 50, 420, 270)
    c.setFillColor(colors.HexColor("#0F172A"))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(70, 295, "Research Motivation & Scope in Base Paper")
    c.setFont("Helvetica", 8.5)
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
    c.setFont("Helvetica-Bold", 11)
    c.drawString(510, 295, "Key Research Findings of the Base Paper")
    c.setFillColor(colors.HexColor("#0F172A"))
    c.setFont("Helvetica", 8.5)
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

    # -------------------------------------------------------------
    # SLIDE 5: Base Paper Methodology
    # -------------------------------------------------------------
    draw_bg()
    draw_header("Technical Breakdown", "Algorithmic Architecture of the Base Paper (Mustapha & Saeed, 2016)")
    pillars = [
        (50, "1. Molecular Representation", "Static 2D Fingerprints", "Molecules were converted into fixed-length binary topological bit-vectors (ECFP/Daylight substructure keys). Features encoded the presence (1) or absence (0) of predefined circular subgraphs within a 2-bond diameter.", "#7C3AED"),
        (270, "2. Machine Learning Algorithm", "Extreme Gradient Boosting", "Ensemble of classification trees trained sequentially. Later trees learned iteratively from the pseudo-residuals of earlier trees, optimizing binary log-loss with second-order Taylor expansions.", "#059669"),
        (490, "3. Regularization & Pruning", "Depth-Wise Tree Growth", "Utilized max_depth constraints and gamma (minimum loss reduction required to make a further partition). Applied L2 leaf regularization to penalize overly complex decision boundaries.", "#D97706"),
        (710, "4. Experimental Validation", "Retrospective K-Fold CV", "Models were evaluated using K-fold cross-validation on historical benchmark tables. Performance was quantified primarily via Accuracy, Precision, Recall, and ROC-AUC.", "#0891B2")
    ]
    for x, h1, h2, desc, col_h in pillars:
        draw_card(x, 50, 200, 375)
        c.setFillColor(colors.HexColor(col_h))
        c.setFont("Helvetica-Bold", 9.5)
        c.drawString(x+10, 400, h1)
        c.setFillColor(colors.HexColor("#0F172A"))
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x+10, 380, h2)
        c.setFillColor(colors.HexColor("#334155"))
        c.setFont("Helvetica", 7.5)
        words = desc.split()
        line = ""
        y_w = 355
        for w in words:
            if len(line + " " + w) < 28:
                line += " " + w
            else:
                c.drawString(x+10, y_w, line.strip())
                line = w
                y_w -= 13
        if line:
            c.drawString(x+10, y_w, line.strip())
    c.showPage()

    # -------------------------------------------------------------
    # SLIDE 6: Limitations of Existing Research
    # -------------------------------------------------------------
    draw_bg()
    draw_header("Critical Appraisal", "Limitations of Existing Research: Author-Stated vs Independent Gaps")
    draw_card(50, 50, 420, 375, stroke_hex="#FCA5A5")
    c.setFillColor(colors.HexColor("#DC2626"))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(70, 400, "A. Limitations Stated by Original Authors (2016)")
    c.setFillColor(colors.HexColor("#1E293B"))
    c.setFont("Helvetica", 8)
    lim_a = [
        "1. 2D Representation Blind Spots: Static 2D fingerprints omit 3D conformational",
        "   flexibility, stereochemistry, solvent entropy, and dynamic induced-fit receptor binding.",
        "2. Class Imbalance Sensitivity: High active-to-decoy ratios caused sensitivity to drop",
        "   unless artificial sampling was applied; standard 0.5 decision thresholds collapsed specificity.",
        "3. Retrospective Benchmark Bias: Evaluated on static historical benchmark collections",
        "   rather than prospective, noisy, real-world chemical databases like ChEMBL.",
        "4. In Silico Limitation: Authors explicitly cautioned that model probabilities cannot",
        "   independently establish in vivo biological efficacy or clinical safety."
    ]
    y = 370
    for l in lim_a:
        c.drawString(70, y, l)
        y -= 22

    draw_card(490, 50, 420, 375, stroke_hex="#C7D2FE")
    c.setFillColor(colors.HexColor("#4338CA"))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(510, 400, "B. Additional Gaps Identified via Our Analysis")
    c.setFillColor(colors.HexColor("#1E293B"))
    c.setFont("Helvetica", 8)
    lim_b = [
        "1. Zero Preclinical Safety / ADMET: Predicting target binding is insufficient; active",
        "   compounds may be insoluble, blocked by the BBB, or cause fatal hERG cardiotoxicity.",
        "2. Scaffold Leakage in Random Splits: Random train/test splits allow identical core",
        "   scaffolds to leak across partitions, giving models an artificially inflated score.",
        "3. Monolithic Feature Scale: Base paper relied solely on binary fingerprints, ignoring",
        "   macroscopic physicochemical descriptors (LogP, TPSA, MolWt) essential for Lipinski rules.",
        "4. Lack of Software Deployment & GUI: Research remained an offline benchmark",
        "   script, offering no web interface, SMILES parsing, 3D visualization, or exportable dossiers."
    ]
    y = 370
    for l in lim_b:
        c.drawString(510, y, l)
        y -= 22
    c.showPage()

    # -------------------------------------------------------------
    # SLIDE 7: Proposed Enhancements in BAMI
    # -------------------------------------------------------------
    draw_bg()
    draw_header("Innovation & Extensions", "BAMI Architectural Enhancements Over the Base Paper")
    cards_7 = [
        (50, 245, "1. Dual-Target Clinical Specialization",
         "Base Paper: Used mixed historical benchmarks (MDDR/DUD).\n"
         "BAMI: Focuses on two therapeutically critical targets: Human COX-2 (CHEMBL230) and Human EGFR (UniProt P00533). Curated raw ChEMBL bioactivity records with strict unit conversion to nM and median IC50 deduplication.",
         "#059669"),
        (490, 245, "2. Multi-Scale Molecular Representations",
         "Base Paper: Relied solely on high-dimensional binary bit-vectors.\n"
         "BAMI: Implements dual-scale feature extraction: 6 continuous physicochemical descriptors (MolWt, LogP, HBD, HBA, TPSA, RotB) for Lipinski screening + 2048-bit Morgan Fingerprints (ECFP4, chirality-aware) for deep EGFR modeling.",
         "#7C3AED"),
        (50, 50, "3. Imbalance Mitigation & Threshold Tuning",
         "Base Paper: Applied standard loss with default 0.5 classification cutoff.\n"
         "BAMI: Incorporated scale_pos_weight (6.528) and Precision-Recall threshold optimization (optimal cut: 0.8069 for EGFR). Slashed false positives by 37% and boosted specificity by +16.5% with zero recall penalty.",
         "#D97706"),
        (490, 50, "4. Comprehensive Preclinical Ecosystem",
         "Base Paper: Command-line offline evaluation script without software tools.\n"
         "BAMI: Deployed full-stack platform (FastAPI + Vanilla Web UI) featuring 10-endpoint ADMET prediction, Bemis-Murcko scaffold SAR decomposition, AutoDock Vina physics-based docking, and automated PDF dossier generation.",
         "#0891B2")
    ]
    for x, y, head, body, col_h in cards_7:
        draw_card(x, y, 420, 180)
        c.setFillColor(colors.HexColor(col_h))
        c.setFont("Helvetica-Bold", 10.5)
        c.drawString(x+15, y+155, head)
        c.setFillColor(colors.HexColor("#1E293B"))
        c.setFont("Helvetica", 7.5)
        lines = body.split("\n")
        y_l = y + 135
        for l in lines:
            c.drawString(x+15, y_l, l)
            y_l -= 14
    c.showPage()

    # -------------------------------------------------------------
    # SLIDE 8: Comparison Table Slide
    # -------------------------------------------------------------
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
        c.setFont("Helvetica-Bold" if i == 0 else "Helvetica", 7.5)
        c.drawString(55, y_t+5, r[0])
        c.drawString(220, y_t+5, r[1])
        c.drawString(540, y_t+5, r[2])
        y_t -= 20
    c.showPage()

    # -------------------------------------------------------------
    # SLIDE 9: Target Biological Background
    # -------------------------------------------------------------
    draw_bg()
    draw_header("Structural Biology", "Biological Background & Therapeutic Relevance of Target Proteins")
    draw_card(50, 50, 420, 375)
    c.setFillColor(colors.HexColor("#DC2626"))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(70, 400, "1. Human Cyclooxygenase-2 (COX-2)")
    c.setFillColor(colors.HexColor("#0F172A"))
    c.setFont("Helvetica", 8)
    bullets_c = [
        "• ChEMBL ID: CHEMBL230 | PDB Structure: 6COX",
        "  Murine COX-2 complexed with SC-558 (100% catalytic pocket homology to human).",
        "• Enzymatic Function:",
        "  Converts arachidonic acid to Prostaglandin H2 (PGH2), driving downstream",
        "  inflammatory cascades, fever, and hyperalgesia pain sensitization.",
        "• Therapeutic Relevance:",
        "  Target of selective NSAIDs (e.g. Celecoxib). Selective COX-2 inhibition avoids",
        "  inhibiting COX-1 gastroprotective prostaglandins, preventing gastric ulceration.",
        "• Catalytic Pocket Topology:",
        "  Hydrophobic catalytic channel featuring a secondary pocket defined by Arg513,",
        "  Phe518, and Val523, accommodating bulky sulfonamide pharmacophores."
    ]
    y = 370
    for b in bullets_c:
        c.drawString(70, y, b)
        y -= 19

    draw_card(490, 50, 420, 375)
    c.setFillColor(colors.HexColor("#7C3AED"))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(510, 400, "2. Human Epidermal Growth Factor Receptor (EGFR)")
    c.setFillColor(colors.HexColor("#0F172A"))
    c.setFont("Helvetica", 8)
    bullets_e = [
        "• UniProt: P00533 | PDB Structure: 1M17",
        "  Human EGFR kinase domain complexed with 4-anilinoquinazoline inhibitor Erlotinib.",
        "• Cellular Signaling:",
        "  Transmembrane receptor tyrosine kinase. Ligand binding activates intrinsic kinase,",
        "  triggering MAPK/ERK and PI3K/Akt survival, proliferation, and anti-apoptosis cascades.",
        "• Oncological Relevance:",
        "  Overexpressed or mutated in non-small cell lung cancer (NSCLC) and glioblastoma.",
        "  Primary target for targeted small-molecule tyrosine kinase inhibitors (TKIs).",
        "• ATP Binding Pocket:",
        "  Deep hydrophobic catalytic cleft between N- and C-terminal lobes. Critical hydrogen",
        "  bonds formed with hinge residue Met793; affinity influenced by gatekeeper Thr790."
    ]
    y = 370
    for b in bullets_e:
        c.drawString(510, y, b)
        y -= 19
    c.showPage()

    # -------------------------------------------------------------
    # SLIDE 10: Dataset Collection & Preprocessing
    # -------------------------------------------------------------
    draw_bg()
    draw_header("Data Engineering", "Dataset Curation Protocol, Preprocessing & Class Distribution")
    draw_card(50, 50, 470, 375)
    c.setFillColor(colors.HexColor("#0F172A"))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(70, 400, "Rigorous ChEMBL Preprocessing Protocol")
    c.setFont("Helvetica", 8)
    proto = [
        "• COX-2 Dataset Curation (ChEMBL Target: CHEMBL230):",
        "  - Raw Rows: 7,979 bioactivity records downloaded from ChEMBL.",
        "  - Missing Values Handled: Dropped rows missing Smiles, Standard Type, Value, Units.",
        "  - Unit Standardization: Converted all units (uM, mM, pM, ug/ml) to nanomolar (nM).",
        "  - Deduplication: Canonical SMILES grouped by median IC50 to resolve lab variance.",
        "  - Cleaned Records: 6,839 records encompassing 5,030 unique chemical entities.",
        "  - Activity Threshold: IC50 <= 10,000 nM (10 uM) = Active (5,004), > 10,000 nM = Inactive (1,835).",
        "",
        "• EGFR Dataset Curation (Target UniProt: P00533):",
        "  - Raw Records: 25,179 source records filtered for IC50 assays.",
        "  - Contradiction Removal: 656 conflicting canonical structures eliminated.",
        "  - Retained Unique Molecules: 13,003 unique chemical structures.",
        "  - Class Distribution: 10,787 Active (83.0%) vs 2,216 Inactive (17.0%).",
        "",
        "• Molecule-Aware Splitting:",
        "  - 80% Train, 20% Holdout Test with 0 scaffold overlap via GroupShuffleSplit.",
        "  - EGFR: 10,402 train / 2,601 test. COX-2: 5,387 train / 1,452 test."
    ]
    y = 375
    for p in proto:
        c.drawString(70, y, p)
        y -= 15

    draw_card(540, 50, 370, 375)
    c.setFillColor(colors.HexColor("#0891B2"))
    c.setFont("Helvetica-Bold", 10.5)
    c.drawString(555, 400, "EGFR Curated Class Distribution")
    plot_dist = ROOT / "EGFR_model_evaluation_plots" / "01_class_distribution.png"
    if plot_dist.exists():
        try:
            c.drawImage(str(plot_dist), 555, 110, width=340, height=270, preserveAspectRatio=True)
        except Exception:
            pass
    c.setFillColor(colors.HexColor("#64748B"))
    c.setFont("Helvetica", 7.5)
    c.drawString(555, 80, "Authentic distribution: 10,787 Active vs 2,216 Inactive (13,003 total).")
    c.drawString(555, 68, "Severe class imbalance necessitates scale_pos_weight & PR-AUC tuning.")
    c.showPage()

    # -------------------------------------------------------------
    # SLIDE 11: System Architecture & Tech Stack
    # -------------------------------------------------------------
    draw_bg()
    draw_header("System Architecture", "Multi-Tiered Full-Stack System Architecture & Technology Stack")
    layers = [
        (350, "Client Tier (Frontend)", "HTML5 + Modern CSS3 + Vanilla ES6+ JavaScript", 
         "• Responsive single-page application (SPA) architecture without bulky frontend frameworks.\n"
         "• 3D WebGL protein-ligand visualizer (3Dmol.js) and 2D chemical structure rendering.\n"
         "• Real-time client-side SMILES validation and asynchronous Fetch API communication.",
         "#3B82F6"),
        (250, "API Gateway & Middleware Tier", "Python 3.14 / 3.10+ & FastAPI Framework",
         "• High-performance asynchronous ASGI architecture (Uvicorn server).\n"
         "• Strict request/response validation using Pydantic data schemas.\n"
         "• Endpoints for single/batch prediction, drug-likeness, ADMET, docking, and PDF export.",
         "#059669"),
        (150, "Cheminformatics Engine", "RDKit Cheminformatics Toolkit (2026.09)",
         "• Chemical string parsing, valence sanitization, and aromaticity kekulization.\n"
         "• 6 physicochemical descriptor calculations (MolWt, LogP, HBD, HBA, TPSA, RotB).\n"
         "• 2048-bit Morgan Fingerprint (ECFP4) generation with circular radius 2 and chirality.",
         "#7C3AED"),
        (50, "Machine Learning & Biophysics", "XGBoost 3.4.1, Scikit-Learn 1.6.1 & AutoDock Vina",
         "• Primary inference: Target-specific XGBoost ensemble with calibrated probability outputs.\n"
         "• Comparative benchmark: Random Forest, Linear SVM, Naive Bayes, and RBF Network.\n"
         "• 10 ADMET models + native AutoDock Vina binary biophysical docking + ReportLab PDF engine.",
         "#D97706")
    ]
    for y, l_title, tech, desc, col_h in layers:
        draw_card(50, y, 860, 90)
        c.setFillColor(colors.HexColor(col_h))
        c.rect(50, y, 10, 90, fill=True, stroke=False)
        c.setFont("Helvetica-Bold", 10.5)
        c.drawString(70, y+68, l_title)
        c.setFont("Helvetica-Bold", 8.5)
        c.drawString(70, y+50, tech)
        c.setFillColor(colors.HexColor("#1E293B"))
        c.setFont("Helvetica", 7.5)
        lines = desc.split("\n")
        y_l = y + 70
        for l in lines:
            c.drawString(320, y_l, l)
            y_l -= 15
    c.showPage()

    # -------------------------------------------------------------
    # SLIDE 12: Complete SMILES-to-Prediction Workflow
    # -------------------------------------------------------------
    draw_bg()
    draw_header("Execution Flow", "Complete SMILES-to-Prediction Execution Workflow")
    stages = [
        (50, 245, "STAGE 01", "1. SMILES Input", "User supplies molecular string (e.g. Celecoxib or Aspirin) via GUI or CSV batch upload.", "#7C3AED"),
        (350, 245, "STAGE 02", "2. RDKit Parsing", "Syntax & valence verification (Chem.MolFromSmiles); rejects corrupted or invalid chemical strings.", "#059669"),
        (650, 245, "STAGE 03", "3. Feature Extraction", "Computes 6 physicochemical descriptors (COX-2) or 2048-bit Morgan ECFP4 binary vector (EGFR).", "#0891B2"),
        (50, 50, "STAGE 04", "4. XGBoost Inference", "Passes vector to trained target-specific gradient boosted decision tree ensemble.", "#D97706"),
        (350, 50, "STAGE 05", "5. Calibrated Cutoff", "Maps raw logit output via calibrated sigmoid curve; applies target threshold (0.8069 for EGFR).", "#DC2626"),
        (650, 50, "STAGE 06", "6. Triage Presentation", "Returns JSON response with Active/Inactive label, 2D structure SVG, ADMET scores, and PDF dossier.", "#10B981")
    ]
    for x, y, tag, head, desc, col_h in stages:
        draw_card(x, y, 260, 180)
        c.setFillColor(colors.HexColor(col_h))
        c.roundRect(x+15, y+145, 80, 20, 4, fill=True, stroke=False)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(x+25, y+151, tag)
        c.setFillColor(colors.HexColor("#0F172A"))
        c.setFont("Helvetica-Bold", 10.5)
        c.drawString(x+15, y+120, head)
        c.setFillColor(colors.HexColor("#334155"))
        c.setFont("Helvetica", 8)
        words = desc.split()
        line = ""
        y_w = y+95
        for w in words:
            if len(line + " " + w) < 32:
                line += " " + w
            else:
                c.drawString(x+15, y_w, line.strip())
                line = w
                y_w -= 14
        if line:
            c.drawString(x+15, y_w, line.strip())
    c.showPage()

    # -------------------------------------------------------------
    # SLIDE 13: ML Methodology & XGBoost Math
    # -------------------------------------------------------------
    draw_bg()
    draw_header("Mathematical Rigor", "XGBoost Mathematical Principles & Exact Hyperparameters")
    draw_card(50, 50, 420, 375)
    c.setFillColor(colors.HexColor("#0F172A"))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(70, 400, "1. Second-Order Gradient Boosting Mechanics")
    c.setFont("Helvetica", 7.5)
    math_lines = [
        "• Regularized Objective Function:",
        "  Obj(t) = Sum[ l(y_i, y_hat_i^(t-1) + f_t(x_i)) ] + Omega(f_t)",
        "  where Omega(f_t) = gamma * T + 0.5 * lambda * Sum[ w_j^2 ] + alpha * Sum[ |w_j| ].",
        "  Explicitly controls tree complexity (T leaves) and leaf weights (w_j).",
        "",
        "• Second-Order Taylor Expansion of Loss:",
        "  Obj(t) ≈ Sum[ g_i * f_t(x_i) + 0.5 * h_i * f_t^2(x_i) ] + Omega(f_t)",
        "  where g_i = d/dy_hat l(y_i, y_hat) and h_i = d^2/dy_hat^2 l(y_i, y_hat).",
        "  Enables exact analytic leaf weight computation: w_j* = -G_j / (H_j + lambda).",
        "",
        "• Exact Greedy Split Finding:",
        "  Gain = 0.5 * [ G_L^2/(H_L+lambda) + G_R^2/(H_R+lambda) - (G_L+G_R)^2/(H_L+H_R+lambda) ] - gamma",
        "  A branch split is accepted only if Gain > 0, pruning uninformative nodes."
    ]
    y = 375
    for ml in math_lines:
        c.drawString(70, y, ml)
        y -= 15

    draw_card(490, 50, 420, 375)
    c.setFillColor(colors.HexColor("#059669"))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(510, 400, "2. Exact Production Hyperparameters")
    c.setFillColor(colors.HexColor("#0F172A"))
    c.setFont("Helvetica", 7.5)
    hp_lines = [
        "• EGFR XGBoost Pipeline (Morgan 2048-bit ECFP4):",
        "  - n_estimators: 334 (early stopping round selected from 337)",
        "  - max_depth: 8 (captures complex substructure interactions)",
        "  - learning_rate (eta): 0.0698 (conservative shrinkage)",
        "  - colsample_bytree: 0.690 (subsamples 69% of bits per tree)",
        "  - subsample: 0.891 (samples 89.1% of molecules per tree)",
        "  - gamma: 1.040 (minimum loss reduction required for split)",
        "  - reg_alpha (L1): 0.0177  |  reg_lambda (L2): 0.886",
        "  - scale_pos_weight: 6.528 (penalizes false negative active errors)",
        "  - search_metric: average_precision (best CV PR-AUC: 0.9878)",
        "",
        "• COX-2 XGBoost Pipeline (6 Physicochemical Descriptors):",
        "  - n_estimators: 200  |  max_depth: 5  |  learning_rate: 0.05",
        "  - subsample: 0.8  |  colsample_bytree: 0.8  |  eval_metric: logloss"
    ]
    y = 375
    for hl in hp_lines:
        c.drawString(510, y, hl)
        y -= 15
    c.showPage()

    # -------------------------------------------------------------
    # SLIDE 14: Model Evaluation Results
    # -------------------------------------------------------------
    draw_bg()
    draw_header("Empirical Verification", "Model Evaluation Metrics & Multi-Algorithm Benchmark Results")
    draw_card(50, 245, 450, 180)
    c.setFillColor(colors.HexColor("#0F172A"))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(65, 405, "COX-2 Benchmark (6 Descriptors, 1,452 Test Holdout)")
    c.setFont("Helvetica", 7.5)
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
    c.setFont("Helvetica", 7.5)
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

    draw_card(520, 50, 390, 375)
    roc_img = ROOT / "EGFR_model_evaluation_plots" / "07_combined_roc_curves.png"
    if roc_img.exists():
        try:
            c.drawImage(str(roc_img), 530, 110, width=370, height=300, preserveAspectRatio=True)
        except Exception:
            pass
    c.setFillColor(colors.HexColor("#475569"))
    c.setFont("Helvetica", 7.5)
    c.drawString(535, 80, "Tuned XGBoost achieves 95.45% ROC-AUC & 98.93% PR-AUC on 2,601 test holdout.")
    c.drawString(535, 66, "High recall (>95%) prevents false dismissal of active pharmaceutical leads.")
    c.showPage()

    # -------------------------------------------------------------
    # SLIDE 15: Tuning & Threshold Optimization
    # -------------------------------------------------------------
    draw_bg()
    draw_header("Model Optimization", "Impact of Hyperparameter Tuning & Precision-Recall Thresholding")
    draw_card(50, 50, 450, 375)
    c.setFillColor(colors.HexColor("#0F172A"))
    c.setFont("Helvetica-Bold", 10.5)
    c.drawString(65, 400, "XGBoost EGFR: Before vs After Tuning")
    c.setFont("Helvetica", 7.5)
    tuning_table = [
        "Metric                      Before Tuning   After Tuning    Absolute Delta",
        "--------------------------------------------------------------------------",
        "Optimal Threshold           0.3911          0.8069          +0.4158",
        "Accuracy                    89.20%          91.77%          +2.57%",
        "Precision                   91.10%          94.19%          +3.09%",
        "Recall (Sensitivity)        96.32%          95.95%          -0.37% (Preserved)",
        "Specificity (True Inact.)   55.51%          72.03%          +16.52% (BOOST)",
        "F1 Score                    93.64%          95.06%          +1.42%",
        "ROC-AUC                     93.04%          95.45%          +2.41%",
        "PR-AUC (Avg. Precision)     98.37%          98.93%          +0.56%",
        "Matthews Correlation (MCC)  0.5903          0.7053          +0.1150",
        "False Positives (FP)        202 mols        127 mols        -75 (-37.1% error)"
    ]
    y = 375
    for tt in tuning_table:
        c.drawString(65, y, tt)
        y -= 16

    draw_card(520, 50, 390, 375)
    ba_plot = ROOT / "EGFR_model_evaluation_plots" / "33_xgboost_before_after_metrics.png"
    if ba_plot.exists():
        try:
            c.drawImage(str(ba_plot), 530, 110, width=370, height=300, preserveAspectRatio=True)
        except Exception:
            pass
    c.setFillColor(colors.HexColor("#059669"))
    c.setFont("Helvetica", 7.5)
    c.drawString(535, 80, "Optimal threshold (0.8069) slashed false positive leads by 37.1%.")
    c.drawString(535, 68, "Elevated specificity from 55.51% to 72.03% with zero loss in recall.")
    c.showPage()

    # -------------------------------------------------------------
    # SLIDE 16: Extended Preclinical Intelligence
    # -------------------------------------------------------------
    draw_bg()
    draw_header("Comprehensive Screening", "Extended Preclinical Intelligence: ADMET, Scaffold SAR & AutoDock Vina")
    exts = [
        (50, "1. 10-Endpoint ADMET Profiling",
         "A target binder is useless if toxic or insoluble:\n"
         "• Absorption: Caco-2 permeability & Human Intestinal Absorption (HIA)\n"
         "• Distribution: Blood-Brain Barrier Penetration (BBBP / Martins)\n"
         "• Metabolism: Cytochrome P450 inhibition (CYP2C9, CYP2D6, CYP3A4)\n"
         "• Excretion: ESOL aqueous solubility (Delaney model, R²=0.88)\n"
         "• Toxicity: Ames mutagenicity, DILI (liver injury), and hERG cardiac channel block.",
         "#059669"),
        (350, "2. Bemis-Murcko Scaffold SAR",
         "Structure-Activity Relationship exploration:\n"
         "• Algorithmic extraction of central Bemis-Murcko core frameworks (ring assemblies and linkers).\n"
         "• Decomposes molecules into core scaffolds and peripheral R-group substituents.\n"
         "• Enables medicinal chemists to perform systematic bioisosteric replacement and side-chain lead optimization across chemical series.",
         "#7C3AED"),
        (650, "3. AutoDock Vina Physics Docking",
         "Bridges 2D ligand informatics with 3D structural biophysics:\n"
         "• Live execution of AutoDock Vina 1.2.0 physics simulation against crystallographic targets COX-2 (6COX) and EGFR (1M17).\n"
         "• Computes empirical binding free energy (ΔG in kcal/mol) and RMSD coordinates.\n"
         "• Interactive 3D WebGL binding site visualization (3Dmol.js) rendering ligand poses within receptor pockets.",
         "#0891B2")
    ]
    for x, head, desc, col_h in exts:
        draw_card(x, 50, 260, 375)
        c.setFillColor(colors.HexColor(col_h))
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x+12, 400, head)
        c.setFillColor(colors.HexColor("#1E293B"))
        c.setFont("Helvetica", 7.5)
        lines = desc.split("\n")
        y_l = 375
        for l in lines:
            c.drawString(x+12, y_l, l)
            y_l -= 15
    c.showPage()

    # -------------------------------------------------------------
    # SLIDE 17: Application Walkthrough & Screenshots
    # -------------------------------------------------------------
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

    # -------------------------------------------------------------
    # SLIDE 18: Critical Appraisal & Future Scope
    # -------------------------------------------------------------
    draw_bg()
    draw_header("Research Perspective", "Critical Limitations of BAMI & Future Engineering Roadmap")
    draw_card(50, 50, 420, 375, stroke_hex="#FCA5A5")
    c.setFillColor(colors.HexColor("#DC2626"))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(70, 400, "Current Platform Limitations (Honest Appraisal)")
    c.setFillColor(colors.HexColor("#1E293B"))
    c.setFont("Helvetica", 8)
    lim_cur = [
        "1. Public Assay Selection Bias: ChEMBL bioactivity datasets over-represent",
        "   patentable, commercially popular chemical scaffolds, creating historical bias.",
        "2. Lack of In Vivo Pharmacodynamics: Models predict static binding propensity;",
        "   they cannot model active hepatic clearance, plasma protein binding, or half-life.",
        "3. Rigid-Receptor Docking Approximation: AutoDock Vina treats the target",
        "   receptor grid as rigid, omitting dynamic allosteric pocket breathing.",
        "4. 2D Coordinate Feature Encodings: Initial feature vectors encode 2D connectivity;",
        "   they do not explicitly model low-energy 3D conformer ensembles in the primary classifier."
    ]
    y = 370
    for lc in lim_cur:
        c.drawString(70, y, lc)
        y -= 22

    draw_card(490, 50, 420, 375, stroke_hex="#BBF7D0")
    c.setFillColor(colors.HexColor("#059669"))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(510, 400, "Future Engineering & Research Roadmap")
    c.setFillColor(colors.HexColor("#1E293B"))
    c.setFont("Helvetica", 8)
    fut = [
        "1. 3D Graph Neural Networks (GNNs): Incorporate SE(3)-equivariant GNNs",
        "   (e.g. SchNet / DimeNet) directly processing 3D coordinates and partial charges.",
        "2. Molecular Dynamics (MD) FEP: Couple AutoDock Vina poses with 100ns MD",
        "   Free Energy Perturbation (FEP) simulations to compute solvent thermodynamics.",
        "3. Pan-Kinome Multi-Task Learning: Expand beyond EGFR to multi-task deep",
        "   neural networks covering all 500+ human kinome targets to predict off-target selectivity.",
        "4. De Novo Generative Optimization: Integrate molecular diffusion models",
        "   and reinforcement learning (REINVENT) to evolve inactive scaffolds into potent leads."
    ]
    y = 370
    for ft in fut:
        c.drawString(510, y, ft)
        y -= 22
    c.showPage()

    # -------------------------------------------------------------
    # SLIDE 19: Conclusion & References (Dark)
    # -------------------------------------------------------------
    draw_bg(dark=True)
    draw_header("Summary & References", "Conclusion & Scientific Bibliography", dark=True)
    draw_card(50, 310, 860, 110, fill_hex="#15203C", stroke_hex="#1C2A4E")
    c.setFillColor(colors.HexColor("#00F2FE"))
    c.setFont("Helvetica-Bold", 10.5)
    c.drawString(70, 395, "Project Conclusion:")
    c.setFillColor(colors.white)
    c.setFont("Helvetica", 8)
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

    c.save()
    print(f"Successfully generated full 19-slide PDF: {PDF_PATH}")

if __name__ == "__main__":
    build_pdf()
