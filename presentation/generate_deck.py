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

class PPTXBuilder:
    def __init__(self):
        self.prs = pptx.Presentation()
        self.prs.slide_width = Inches(SLIDE_WIDTH_IN)
        self.prs.slide_height = Inches(SLIDE_HEIGHT_IN)
        self.blank_layout = self.prs.slide_layouts[6]

    def add_slide(self, bg_color=SLATE_50):
        slide = self.prs.slides.add_slide(self.blank_layout)
        # Background shape
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
        p_t.font.size = Pt(21)
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

    def add_textbox(self, slide, left, top, width, height, text="", font_size=12, bold=False, color=SLATE_800, align=PP_ALIGN.LEFT):
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
            p.font.size = Pt(10.5)
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

print("PPTXBuilder defined.")
