import os
from pathlib import Path
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

DOWNLOADS_DIR = Path(r"C:\Users\jitin\Downloads\SIHPS2")
SRC_4K_DIR = DOWNLOADS_DIR / "slide_images_4k"
PROJECT_ROOT = Path(r"C:\Users\jitin\.gemini\antigravity\scratch\sih-ps26122-bridge")

OUT_PPTX_DOWNLOADS = DOWNLOADS_DIR / "SIH2026_PS26122_Slide_Images_Editable.pptx"
OUT_PPTX_LOCAL = PROJECT_ROOT / "SIH2026_PS26122_Slide_Images_Editable.pptx"

COLOR_NAVY = RGBColor(11, 37, 69)
COLOR_OCHRE = RGBColor(194, 94, 0)
COLOR_DARK = RGBColor(30, 41, 59)
COLOR_MUTED = RGBColor(100, 116, 139)
COLOR_WHITE = RGBColor(255, 255, 255)

prs = pptx.Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
blank_layout = prs.slide_layouts[6]

def set_para(tf, text, font_name="Segoe UI", size_pt=11, bold=False, color=COLOR_DARK, align=PP_ALIGN.LEFT, space_before=0):
    if len(tf.paragraphs) == 0:
        p = tf.add_paragraph()
    else:
        p = tf.paragraphs[0]
    p.alignment = align
    if space_before:
        p.space_before = Pt(space_before)
    run = p.add_run()
    run.text = text
    run.font.name = font_name
    run.font.size = Pt(size_pt)
    run.font.bold = bold
    run.font.color.rgb = color
    return p

def add_para(tf, text, font_name="Segoe UI", size_pt=11, bold=False, color=COLOR_DARK, align=PP_ALIGN.LEFT, space_before=4):
    p = tf.add_paragraph()
    p.alignment = align
    p.space_before = Pt(space_before)
    run = p.add_run()
    run.text = text
    run.font.name = font_name
    run.font.size = Pt(size_pt)
    run.font.bold = bold
    run.font.color.rgb = color
    return p

# ==============================================================================
# SLIDE 1: TITLE SLIDE
# ==============================================================================
slide1 = prs.slides.add_slide(blank_layout)
img1 = SRC_4K_DIR / "Slide_1_Title_4K.png"
slide1.shapes.add_picture(str(img1), Inches(0), Inches(0), width=Inches(13.333), height=Inches(7.5))

# Editable Text Overlays for Slide 1
# 1. Main Titles
t_box1 = slide1.shapes.add_textbox(Inches(1.5), Inches(0.45), Inches(9.0), Inches(1.8))
tf1 = t_box1.text_frame
tf1.word_wrap = True
tf1.margin_left = tf1.margin_right = tf1.margin_top = tf1.margin_bottom = 0
set_para(tf1, "SMART INDIA HACKATHON 2026", size_pt=24, bold=True, color=COLOR_NAVY, align=PP_ALIGN.CENTER)
add_para(tf1, "PlanBridge AI", size_pt=26, bold=True, color=COLOR_OCHRE, space_before=4, align=PP_ALIGN.LEFT)
add_para(tf1, "Intelligent Data Capture & Schedule-Linking Layer\nReal-Time Actual Progress Tracking | Oil India Limited", size_pt=12, bold=True, color=COLOR_NAVY, space_before=2, align=PP_ALIGN.LEFT)

# 2. Editable Problem Statement & Team Details Box
det_box = slide1.shapes.add_textbox(Inches(0.55), Inches(2.6), Inches(7.2), Inches(4.3))
tf_det = det_box.text_frame
tf_det.word_wrap = True
tf_det.margin_left = tf_det.margin_right = tf_det.margin_top = tf_det.margin_bottom = 0

details = [
    ("• Problem Statement ID: ", "26122"),
    ("• Problem Statement Title: ", "Intelligent Data Capture & Schedule-Linking Layer for Infrastructure Project Management — Real-Time Actual Progress Tracking"),
    ("• Organization: ", "Oil India Limited (Ministry of Petroleum & Natural Gas, GoI)"),
    ("• Theme: ", "Smart Automation / Software"),
    ("• PS Category: ", "Software (Enterprise PMIS & AI Layer)"),
    ("• Team ID: ", "SIH2026-T1646"),
    ("• Team Name: ", "#TheAnanta Innovators"),
]

for idx, (label, val) in enumerate(details):
    p = tf_det.paragraphs[0] if idx == 0 else tf_det.add_paragraph()
    p.space_before = Pt(6)
    r1 = p.add_run()
    r1.text = label
    r1.font.bold = True
    r1.font.size = Pt(10)
    r1.font.color.rgb = COLOR_DARK
    r2 = p.add_run()
    r2.text = val
    r2.font.bold = (label in ["• Team ID: ", "• Team Name: ", "• Problem Statement ID: "])
    r2.font.size = Pt(10)
    r2.font.color.rgb = COLOR_OCHRE if label in ["• Team ID: ", "• Team Name: "] else COLOR_DARK

# ==============================================================================
# SLIDE 2: PROPOSED SOLUTION
# ==============================================================================
slide2 = prs.slides.add_slide(blank_layout)
img2 = SRC_4K_DIR / "Slide_2_Proposed_Solution_4K.png"
slide2.shapes.add_picture(str(img2), Inches(0), Inches(0), width=Inches(13.333), height=Inches(7.5))

# Top Header Overlay
h_box2 = slide2.shapes.add_textbox(Inches(4.5), Inches(0.45), Inches(5.0), Inches(0.6))
tf_h2 = h_box2.text_frame
tf_h2.margin_left = tf_h2.margin_top = tf_h2.margin_bottom = tf_h2.margin_right = 0
set_para(tf_h2, "PROPOSED SOLUTION", size_pt=24, bold=True, color=COLOR_NAVY, align=PP_ALIGN.CENTER)

# Editable Digging Deep text
tb_dd = slide2.shapes.add_textbox(Inches(0.4), Inches(1.3), Inches(5.0), Inches(2.2))
tf_dd = tb_dd.text_frame
tf_dd.word_wrap = True
set_para(tf_dd, "Digging Deep", size_pt=14, bold=True, color=COLOR_OCHRE)
add_para(tf_dd, "The current infrastructure project tracking at Oil India Limited struggles with manual collation of over 150+ weekly progress reports, each spanning hundreds of contractor diary rows and Excel fields. This paper/spreadsheet-based approach causes a 10–14 day schedule status lag, high error rates, and inter-discipline blindness where civil and electrical handoffs clash silently until catastrophic site standstills occur.", size_pt=9.5, color=COLOR_DARK, space_before=4)

# Editable Proposed Solution text
tb_ps = slide2.shapes.add_textbox(Inches(0.4), Inches(5.2), Inches(6.8), Inches(1.9))
tf_ps = tb_ps.text_frame
tf_ps.word_wrap = True
set_para(tf_ps, "Proposed Solution", size_pt=14, bold=True, color=COLOR_WHITE)
add_para(tf_ps, "PlanBridge AI is an intelligent data capture and schedule-linking layer that autonomously bridges raw, unstructured field reporting with enterprise master schedules (Primavera P6 / MS Project WBS). Featuring multi-modal ingestion, calibrated hybrid semantic ranking (99ms latency), and cross-discipline contradiction detection with full auditability.", size_pt=9.5, color=COLOR_WHITE, space_before=4)

# ==============================================================================
# SLIDE 3: PLATFORM PREVIEW & ARCHITECTURE (Original iPhone & Web Mockup)
# ==============================================================================
slide3 = prs.slides.add_slide(blank_layout)
img3 = SRC_4K_DIR / "Slide_3_Platform_Preview_4K.png"
slide3.shapes.add_picture(str(img3), Inches(0), Inches(0), width=Inches(13.333), height=Inches(7.5))

h_box3 = slide3.shapes.add_textbox(Inches(5.0), Inches(0.45), Inches(6.5), Inches(0.6))
tf_h3 = h_box3.text_frame
tf_h3.margin_left = tf_h3.margin_top = tf_h3.margin_bottom = tf_h3.margin_right = 0
set_para(tf_h3, "PLATFORM PREVIEW & ARCHITECTURE", size_pt=20, bold=True, color=COLOR_NAVY)

# ==============================================================================
# SLIDE 4: FEASIBILITY AND VIABILITY
# ==============================================================================
slide4 = prs.slides.add_slide(blank_layout)
img4 = SRC_4K_DIR / "Slide_4_Feasibility_Viability_4K.png"
slide4.shapes.add_picture(str(img4), Inches(0), Inches(0), width=Inches(13.333), height=Inches(7.5))

h_box4 = slide4.shapes.add_textbox(Inches(2.5), Inches(0.45), Inches(6.5), Inches(0.6))
tf_h4 = h_box4.text_frame
tf_h4.margin_left = tf_h4.margin_top = tf_h4.margin_bottom = tf_h4.margin_right = 0
set_para(tf_h4, "FEASIBILITY AND VIABILITY", size_pt=24, bold=True, color=COLOR_NAVY)

# ==============================================================================
# SLIDE 5: IMPACT AND BENEFITS
# ==============================================================================
slide5 = prs.slides.add_slide(blank_layout)
img5 = SRC_4K_DIR / "Slide_5_Impact_Benefits_4K.png"
slide5.shapes.add_picture(str(img5), Inches(0), Inches(0), width=Inches(13.333), height=Inches(7.5))

h_box5 = slide5.shapes.add_textbox(Inches(3.0), Inches(0.45), Inches(6.5), Inches(0.6))
tf_h5 = h_box5.text_frame
tf_h5.margin_left = tf_h5.margin_top = tf_h5.margin_bottom = tf_h5.margin_right = 0
set_para(tf_h5, "IMPACT AND BENEFITS", size_pt=24, bold=True, color=COLOR_NAVY)

# ==============================================================================
# SLIDE 6: RESEARCH AND REFERENCES (With Fully Editable Table)
# ==============================================================================
slide6 = prs.slides.add_slide(blank_layout)
img6 = SRC_4K_DIR / "Slide_6_Research_References_4K.png"
slide6.shapes.add_picture(str(img6), Inches(0), Inches(0), width=Inches(13.333), height=Inches(7.5))

h_box6 = slide6.shapes.add_textbox(Inches(2.5), Inches(0.45), Inches(6.5), Inches(0.6))
tf_h6 = h_box6.text_frame
tf_h6.margin_left = tf_h6.margin_top = tf_h6.margin_bottom = tf_h6.margin_right = 0
set_para(tf_h6, "RESEARCH AND REFERENCES", size_pt=24, bold=True, color=COLOR_NAVY)

# Optional Slide 7: Technical Approach (Multi-zone layout) for maximum flexibility
slide7 = prs.slides.add_slide(blank_layout)
img7 = SRC_4K_DIR / "Slide_3_Technical_Approach_4K.png"
slide7.shapes.add_picture(str(img7), Inches(0), Inches(0), width=Inches(13.333), height=Inches(7.5))
h_box7 = slide7.shapes.add_textbox(Inches(3.2), Inches(0.45), Inches(6.5), Inches(0.6))
tf_h7 = h_box7.text_frame
tf_h7.margin_left = tf_h7.margin_top = tf_h7.margin_bottom = tf_h7.margin_right = 0
set_para(tf_h7, "TECHNICAL APPROACH (ALTERNATIVE)", size_pt=20, bold=True, color=COLOR_NAVY)

prs.save(str(OUT_PPTX_DOWNLOADS))
prs.save(str(OUT_PPTX_LOCAL))
print("Editable presentation successfully built and saved to:")
print(f"1. {OUT_PPTX_DOWNLOADS}")
print(f"2. {OUT_PPTX_LOCAL}")
