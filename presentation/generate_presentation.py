"""
BAMI: Bioactive Molecule Intelligence
Master Technical Review Presentation Generator (PPTX & PDF)
University Project Review Edition

Generates:
1. presentation/BAMI_Project_Presentation.pptx (Editable PowerPoint with Speaker Notes)
2. presentation/BAMI_Project_Presentation.pdf (Widescreen 16:9 PDF Presentation)
"""

import os
import sys
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

print(f"BAMI Presentation Generator started...")
print(f"Output PPTX: {PPTX_PATH}")
print(f"Output PDF:  {PDF_PATH}")
