import fontforge
import os
import sys

# Ensure an argument is provided
if len(sys.argv) < 2:
    print("Usage: export-ttf.py <font-file.ttf>")
    sys.exit(1)

font_path = sys.argv[1]
output_dir = "out"

# Create the output directory if it does not exist
os.makedirs(output_dir, exist_ok=True)

# Open the font
font = fontforge.open(font_path)

# Export each glyph as PNG
for glyph in font.glyphs():
    if glyph.unicode == -1:
        continue  # Skip glyphs without Unicode values

    if glyph not in range(0, 128):
        break

    filename = os.path.join(output_dir, f"{glyph.unicode}.png")
    glyph.export(filename, 16)
