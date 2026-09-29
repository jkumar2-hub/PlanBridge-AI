import os
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter

SRC_DIR = Path(r"C:\Users\jitin\Downloads\SIHPS2\slide_images")
OUT_4K_DIR = Path(r"C:\Users\jitin\Downloads\SIHPS2\slide_images_4k")
OUT_8K_DIR = Path(r"C:\Users\jitin\Downloads\SIHPS2\slide_images_8k")

OUT_4K_DIR.mkdir(parents=True, exist_ok=True)
OUT_8K_DIR.mkdir(parents=True, exist_ok=True)

# Also create local mirrors in the scratch directory
LOCAL_4K = Path(r"C:\Users\jitin\.gemini\antigravity\scratch\sih-ps26122-bridge\slide_images_4k")
LOCAL_8K = Path(r"C:\Users\jitin\.gemini\antigravity\scratch\sih-ps26122-bridge\slide_images_8k")
LOCAL_4K.mkdir(parents=True, exist_ok=True)
LOCAL_8K.mkdir(parents=True, exist_ok=True)

images = [
    "Slide_1_Title.jpg",
    "Slide_2_Proposed_Solution.jpg",
    "Slide_3_Platform_Preview.jpg",
    "Slide_3_Technical_Approach.jpg",
    "Slide_4_Feasibility_Viability.jpg",
    "Slide_5_Impact_Benefits.jpg",
    "Slide_6_Research_References.jpg",
]

print("=== ENHANCING SLIDE IMAGES TO 4K & 8K (16:9) ===")

for img_name in images:
    src_path = SRC_DIR / img_name
    if not src_path.exists():
        print(f"Skipping missing: {src_path}")
        continue
    
    base_name = img_name.replace(".jpg", "")
    im = Image.open(src_path)
    w, h = im.size
    print(f"\nProcessing {img_name} (original {w}x{h})...")
    
    # Target 16:9 is 1.77778
    # Original 1376x768 is 1.79167
    # Perfect 16:9 crop: width = 768 * 16 / 9 = 1365.33 -> 1366
    crop_w = int(h * 16 / 9)
    if crop_w < w:
        left = (w - crop_w) // 2
        right = left + crop_w
        im_16_9 = im.crop((left, 0, right, h))
    else:
        im_16_9 = im
    
    # ---------------- 4K UHD (3840 x 2160) ----------------
    im_4k = im_16_9.resize((3840, 2160), Image.Resampling.LANCZOS)
    enh_4k = ImageEnhance.Sharpness(im_4k).enhance(1.30)
    im_4k_final = enh_4k.filter(ImageFilter.UnsharpMask(radius=2, percent=125, threshold=2))
    
    path_4k_down = OUT_4K_DIR / f"{base_name}_4K.png"
    path_4k_loc = LOCAL_4K / f"{base_name}_4K.png"
    im_4k_final.save(path_4k_down, format="PNG", optimize=True)
    im_4k_final.save(path_4k_loc, format="PNG", optimize=True)
    print(f"  -> 4K saved: {path_4k_down.name} ({path_4k_down.stat().st_size / 1024 / 1024:.2f} MB)")
    
    # ---------------- 8K UHD (7680 x 4320) ----------------
    im_8k = im_16_9.resize((7680, 4320), Image.Resampling.LANCZOS)
    enh_8k = ImageEnhance.Sharpness(im_8k).enhance(1.25)
    im_8k_final = enh_8k.filter(ImageFilter.UnsharpMask(radius=3, percent=120, threshold=2))
    
    path_8k_down = OUT_8K_DIR / f"{base_name}_8K.png"
    path_8k_loc = LOCAL_8K / f"{base_name}_8K.png"
    im_8k_final.save(path_8k_down, format="PNG", optimize=True)
    im_8k_final.save(path_8k_loc, format="PNG", optimize=True)
    print(f"  -> 8K saved: {path_8k_down.name} ({path_8k_down.stat().st_size / 1024 / 1024:.2f} MB)")

print("\nAll slide images successfully enhanced to 4K and 8K 16:9!")
