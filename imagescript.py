import os
import math
from PIL import Image, ImageDraw, ImageFont

# Directories to scan
INSPECTION_DIRS = [
    'Inspection_Dec1',
    'Inspection_Dec2',
    'Inspection_Nov17',
    'Inspection_Nov21'
]

OUTPUT_FILENAME = "Total_Analysis_Report.pdf"

# --- STYLE SETTINGS (HIGH RES / 150 DPI) ---
# This is 2x the size of the last one, so text will be crisp.
PAGE_WIDTH = 1240
PAGE_HEIGHT = 1754
HEADER_HEIGHT = 250
MARGIN = 40
PADDING = 8

# Colors
COLOR_HEADER_BG = "#2C3E50"  # Dark Slate Blue
COLOR_TEXT_WHITE = "#FFFFFF"

def get_all_images():
    image_paths = []
    print("Scanning folders...")
    for folder in INSPECTION_DIRS:
        if os.path.exists(folder):
            for f in os.listdir(folder):
                if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    image_paths.append(os.path.join(folder, f))
    return image_paths

def create_styled_report():
    images = get_all_images()
    total_images = len(images)
    
    if total_images == 0:
        print("No images found!")
        return

    print(f"Found {total_images} images. Generating High-Res Report...")

    # 1. Create the Canvas
    canvas = Image.new('RGB', (PAGE_WIDTH, PAGE_HEIGHT), 'white')
    draw = ImageDraw.Draw(canvas)

    # 2. Draw the Header
    draw.rectangle([0, 0, PAGE_WIDTH, HEADER_HEIGHT], fill=COLOR_HEADER_BG)

    # 3. Load Fonts (Sharp Size)
    try:
        # Font size 70 looks sharp at this resolution
        title_font = ImageFont.truetype("Arial Bold.ttf", 70)
    except:
        try:
            title_font = ImageFont.truetype("Arial.ttf", 70)
        except:
            print("Warning: Arial font not found. Using default.")
            title_font = ImageFont.load_default()

    # 4. Draw Header Text
    title_text = "TOTAL IMAGES ANALYZED"
    draw.text((MARGIN, 90), title_text, fill=COLOR_TEXT_WHITE, font=title_font)

    # 5. Calculate Grid
    usable_width = PAGE_WIDTH - (MARGIN * 2)
    usable_height = PAGE_HEIGHT - HEADER_HEIGHT - MARGIN
    
    area_ratio = usable_width / usable_height
    
    cols = math.ceil(math.sqrt(total_images * area_ratio))
    rows = math.ceil(total_images / cols)
    
    total_gap_width = (cols - 1) * PADDING
    total_gap_height = (rows - 1) * PADDING
    
    if cols > 0: thumb_w = int((usable_width - total_gap_width) / cols)
    else: thumb_w = usable_width

    if rows > 0: thumb_h = int((usable_height - total_gap_height) / rows)
    else: thumb_h = usable_height
    
    thumb_size = min(thumb_w, thumb_h)
    if thumb_size < 1: thumb_size = 1
    
    print(f"Grid Layout: {cols} cols x {rows} rows | Thumb Size: {thumb_size}px")

    # 6. Paste Images
    print("Processing images...")
    current_idx = 0
    
    for r in range(rows):
        for c in range(cols):
            if current_idx >= total_images:
                break
            
            img_path = images[current_idx]
            
            try:
                with Image.open(img_path) as img:
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    # Resize with High Quality Filter
                    img = img.resize((thumb_size, thumb_size), Image.Resampling.LANCZOS)
                    
                    x_pos = MARGIN + (c * (thumb_size + PADDING))
                    y_pos = HEADER_HEIGHT + MARGIN + (r * (thumb_size + PADDING))
                    
                    canvas.paste(img, (x_pos, y_pos))
                    
            except Exception as e:
                print(f"Skipping bad image {img_path}: {e}")
            
            current_idx += 1
            if current_idx % 100 == 0:
                print(f"   Placed {current_idx}/{total_images}...")

    # 7. Save with Metadata
    print(f"Saving to {OUTPUT_FILENAME}...")
    
    # resolution=150.0 tells the PDF viewer: "This is a standard page, just with good detail."
    canvas.save(OUTPUT_FILENAME, "PDF", resolution=150.0) 
    print("Done!")

if __name__ == "__main__":
    create_styled_report()