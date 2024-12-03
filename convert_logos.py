from cairosvg import svg2png
import os

def convert_svg_to_png(svg_path, png_path):
    with open(svg_path, 'r') as f:
        svg_content = f.read()
    svg2png(bytestring=svg_content, write_to=png_path, output_width=200, output_height=40)

# Convert English logo
convert_svg_to_png('static/images/logo_en.svg', 'static/images/logo-eng.png')
# Convert German logo
convert_svg_to_png('static/images/logo_de.svg', 'static/images/logo-ger.png')

print("Logo conversion completed")
