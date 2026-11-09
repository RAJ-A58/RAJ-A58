#!/usr/bin/env python3
"""
Adds native SMIL self-typing animations to ASCII portrait SVG cards.
Each row is wrapped in an animated clipPath, with an optional riding cursor.
Compatible with GitHub's SVG rendering sanitization (no JavaScript required).
"""
import re
import sys
from pathlib import Path

def animate_svg(input_path: Path, output_path: Path = None, is_light: bool = False):
    if output_path is None:
        output_path = input_path

    with open(input_path, 'r', encoding='utf-8') as f:
        svg_content = f.read()

    # Identify cursor color
    cursor_color = "#0969da" if is_light else "#58a6ff"

    # Match all <text ...>...</text> tags
    # Each text tag: <text x=".." y=".." ...>content</text>
    pattern = re.compile(r'(<text\s+([^>]*?)>)(.*?)(</text>)', re.DOTALL)
    matches = list(pattern.finditer(svg_content))

    if not matches:
        print(f"No text elements found in {input_path}")
        return

    clip_defs = []
    cursor_rects = []
    replacements = []

    # Distinguish portrait rows vs card details rows based on x coordinate
    portrait_index = 0
    card_index = 0

    for idx, match in enumerate(matches):
        full_tag = match.group(0)
        open_tag = match.group(1)
        attrs_str = match.group(2)
        inner_text = match.group(3)
        close_tag = match.group(4)

        # Extract x and y
        x_match = re.search(r'x="([\d.]+)"', attrs_str)
        y_match = re.search(r'y="([\d.]+)"', attrs_str)
        font_match = re.search(r'font-size="([\d.]+)"', attrs_str)

        x = float(x_match.group(1)) if x_match else 28.0
        y = float(y_match.group(1)) if y_match else 34.0
        font_size = float(font_match.group(1)) if font_match else 8.0

        clip_id = f"type-row-{idx}"
        
        # Is this a left portrait row or right card row?
        if x < 400:
            # Left portrait row
            start_time = round(portrait_index * 0.055, 3)
            duration = 0.12
            row_width = 620
            row_height = font_size + 3.0
            y_box = round(y - font_size, 2)
            x_start = round(x - 2, 2)
            portrait_index += 1
        else:
            # Right side terminal card row
            start_time = round(0.4 + (card_index * 0.12), 3)
            duration = 0.18
            row_width = 570
            row_height = font_size + 4.0
            y_box = round(y - font_size, 2)
            x_start = round(x - 2, 2)
            card_index += 1

        # ClipPath definition
        clip_def = f'''    <clipPath id="{clip_id}">
      <rect x="{x_start}" y="{y_box}" width="0" height="{row_height}">
        <animate attributeName="width" from="0" to="{row_width}" dur="{duration}s" begin="{start_time}s" fill="freeze" />
      </rect>
    </clipPath>'''
        clip_defs.append(clip_def)

        # Cursor definition (rides the wipe edge)
        cursor_w = 6 if font_size <= 10 else 9
        cursor_def = f'''    <rect x="{x_start}" y="{y_box}" width="{cursor_w}" height="{row_height}" fill="{cursor_color}" opacity="0">
      <set attributeName="opacity" to="0.9" begin="{start_time}s" />
      <animate attributeName="x" from="{x_start}" to="{x_start + row_width}" dur="{duration}s" begin="{start_time}s" fill="freeze" />
      <set attributeName="opacity" to="0" begin="{round(start_time + duration, 3)}s" />
    </rect>'''
        cursor_rects.append(cursor_def)

        # Update the open text tag to include clip-path
        new_open_tag = open_tag[:-1] + f' clip-path="url(#{clip_id})">'
        new_full_tag = new_open_tag + inner_text + close_tag
        replacements.append((full_tag, new_full_tag))

    # Apply tag replacements
    new_svg = svg_content
    for old_tag, new_tag in replacements:
        new_svg = new_svg.replace(old_tag, new_tag, 1)

    # Insert <defs> right after <svg ...>
    defs_block = "\n  <defs>\n" + "\n".join(clip_defs) + "\n  </defs>\n  <g id=\"typing-cursors\">\n" + "\n".join(cursor_rects) + "\n  </g>\n"
    
    # Place defs right after the opening <svg ...>
    svg_tag_end = new_svg.find('>')
    if svg_tag_end != -1:
        new_svg = new_svg[:svg_tag_end + 1] + defs_block + new_svg[svg_tag_end + 1:]

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(new_svg)

    print(f"Successfully animated {len(matches)} rows in {output_path}")

def main():
    root = Path(__file__).resolve().parent.parent
    dark_svg = root / "dark_mode.svg"
    light_svg = root / "light_mode.svg"

    if dark_svg.exists():
        animate_svg(dark_svg, dark_svg, is_light=False)
    if light_svg.exists():
        animate_svg(light_svg, light_svg, is_light=True)

if __name__ == "__main__":
    main()
