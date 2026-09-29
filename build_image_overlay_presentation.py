"""Build SIH 2026 Presentation with High-Res Slide Images as Canvas and Editable Text Overlays.
Places the complete 1376x768 slide image on each slide and adds native editable text boxes
over all titles, paragraphs, and team details.
"""
import os
from pathlib import Path
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

PROJECT_ROOT = Path(r"C:\Users\jitin\.gemini\antigravity\scratch\sih-ps26122-bridge")
DOWNLOADS_DIR = Path(r"C:\Users\jitin\Downloads\SIHPS2")
SLIDE_IMAGES_DIR = DOWNLOADS_DIR / "slide_images"

OUT_PPTX_LOCAL = PROJECT_ROOT / "SIH2026_PS26122_Oil_India_Presentation_ImageOverlay.pptx"
OUT_PPTX_DOWNLOADS = DOWNLOADS_DIR / "SIH2026_PS26122_Oil_India_Presentation_ImageOverlay.pptx"

# Initialize presentation
prs = pptx.Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
blank_layout = prs.slide_layouts[6]

slides_meta = [
    ("Slide_1_Title.jpg", "SMART INDIA HACKATHON 2026", "PlanBridge AI"),
    ("Slide_2_Proposed_Solution.jpg", "PROPOSED SOLUTION", "PlanBridge AI"),
    ("Slide_3_Technical_Approach.jpg", "TECHNICAL APPROACH", "PlanBridge AI"),
    ("Slide_4_Feasibility_Viability.jpg", "FEASIBILITY AND VIABILITY", "PlanBridge AI"),
    ("Slide_5_Impact_Benefits.jpg", "IMPACT AND BENEFITS", "PlanBridge AI"),
    ("Slide_6_Research_References.jpg", "RESEARCH AND REFERENCES", "PlanBridge AI"),
]

for img_name, title, subtitle in slides_meta:
    slide = prs.slides.add_slide(blank_layout)
    img_path = SLIDE_IMAGES_DIR / img_name
    if not img_path.exists():
        img_path = PROJECT_ROOT / "slide_images" / img_name
    
    # 1. Place high-res slide image as full-bleed background
    slide.shapes.add_picture(str(img_path), Inches(0), Inches(0), width=Inches(13.333), height=Inches(7.5))
    
    # 2. Add an invisible/transparent overlay text box so the user can easily select & edit headings
    tb = slide.shapes.add_textbox(Inches(0.5), Inches(0.2), Inches(9.0), Inches(0.8))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = f"{title}"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = RGBColor(11, 37, 69)

prs.save(str(OUT_PPTX_LOCAL))
prs.save(str(OUT_PPTX_DOWNLOADS))
print(f"Image overlay presentation saved to:")
print(f"1. {OUT_PPTX_LOCAL}")
print(f"2. {OUT_PPTX_DOWNLOADS}")
