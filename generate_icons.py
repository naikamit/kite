"""
Simple PWA Icon Generator
Creates placeholder icons for the Kite Trading Coach app
"""

from PIL import Image, ImageDraw, ImageFont
import os

ICON_SIZES = [16, 32, 72, 96, 128, 144, 152, 180, 192, 384, 512]
OUTPUT_DIR = "static/icons"

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

def create_icon(size, text="K", bg_color="#1a73e8", text_color="white"):
    """Create a simple icon with text."""
    # Create image with gradient background
    img = Image.new('RGB', (size, size), bg_color)
    draw = ImageDraw.Draw(img)

    # Try to use a nice font, fallback to default
    try:
        font_size = int(size * 0.6)
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except:
        font = ImageFont.load_default()

    # Draw text in center
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    position = (
        (size - text_width) / 2,
        (size - text_height) / 2 - text_bbox[1]
    )

    draw.text(position, text, fill=text_color, font=font)

    return img

def generate_all_icons():
    """Generate all required icon sizes."""
    print("🎨 Generating PWA icons...")

    for size in ICON_SIZES:
        filename = f"icon-{size}x{size}.png"
        filepath = os.path.join(OUTPUT_DIR, filename)

        icon = create_icon(size)
        icon.save(filepath, "PNG")

        print(f"  ✓ Created {filename}")

    print(f"\n✅ Generated {len(ICON_SIZES)} icons in {OUTPUT_DIR}/")
    print("\n💡 Tip: Replace these with your custom logo later!")

if __name__ == "__main__":
    try:
        generate_all_icons()
    except ImportError:
        print("❌ PIL/Pillow not installed. Install with: pip install Pillow")
        print("\n📝 Alternative: Manually create icons or use online generator:")
        print("   https://www.pwabuilder.com/imageGenerator")

        # Create a README instead
        with open(os.path.join(OUTPUT_DIR, "README.md"), "w") as f:
            f.write(f"""# PWA Icons

Required icon sizes: {', '.join(f'{s}x{s}' for s in ICON_SIZES)}

## Quick Generation Options:

1. **Use online generator:**
   - Visit: https://www.pwabuilder.com/imageGenerator
   - Upload a 512x512 logo
   - Download and extract to this folder

2. **Install Pillow and run:**
   ```bash
   pip install Pillow
   python generate_icons.py
   ```

3. **Manually create** icon-NxN.png files for each size listed above
""")
        print(f"\n✅ Created README in {OUTPUT_DIR}/")
