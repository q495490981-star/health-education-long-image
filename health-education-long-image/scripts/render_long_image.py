#!/usr/bin/env python3
"""Offline, deterministic Chinese long-image layout. See SKILL.md for input schema."""
import argparse
import json
import os
import sys
import tempfile
import atexit
import random
from pathlib import Path
from functools import lru_cache

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit('Missing Pillow. Install it with: python -m pip install Pillow')

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets' / 'illustrations'
WIDTH = 1080
MARGIN = 86
BG = '#faf6eb'
DARK = '#453326'
ORANGE = '#bd5520'
GREEN = '#e7edd3'


def font_path(explicit):
    home = Path.home()
    if explicit and not Path(explicit).is_file():
        raise SystemExit(f'Chinese font file not found: {explicit}')
    bundled = ROOT / 'assets' / 'fonts' / 'NotoSansSC-Standard-Light.ttf'
    if not bundled.is_file():
        parts = sorted((ROOT / 'assets' / 'fonts').glob('NotoSansSC-Standard-Light.ttf.part[0-9][0-9][0-9]'))
        if len(parts) == 6:
            with tempfile.NamedTemporaryFile(suffix='.ttf', delete=False) as tmp:
                for part in parts:
                    tmp.write(part.read_bytes())
                bundled = Path(tmp.name)
            atexit.register(lambda: bundled.unlink(missing_ok=True))
    choices = [explicit, os.getenv('HEALTH_IMAGE_FONT'),
        str(bundled),
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
        '/System/Library/Fonts/PingFang.ttc',
        str(home / 'Library/Fonts/Arial Unicode.ttf'),
        r'C:\Windows\Fonts\msyh.ttc', r'C:\Windows\Fonts\simhei.ttf']
    for candidate in choices:
        if candidate and Path(candidate).is_file():
            f = ImageFont.truetype(str(candidate), 40)
            if bytes(f.getmask('中')) != bytes(f.getmask('\U0010ffff')):
                return str(candidate)
    raise SystemExit('A Chinese font is required. Pass --font PATH or set HEALTH_IMAGE_FONT to a Chinese font file.')


@lru_cache(maxsize=16384)
def glyph_font(char, primary, fallback):
    if char.isspace():
        return primary
    for font in (primary, fallback):
        if font is not None and bytes(font.getmask(char)) != bytes(font.getmask('\U0010ffff')):
            return font
    raise ValueError(f'Font does not support character {char!r} (U+{ord(char):04X}); pass --font with a font containing it.')


def split_runs(text, primary, fallback):
    runs = []
    for char in text:
        font = glyph_font(char, primary, fallback)
        if runs and runs[-1][1] is font:
            runs[-1] = (runs[-1][0] + char, font)
        else:
            runs.append((char, font))
    return runs


def line_width(text, primary, fallback, draw):
    return sum(draw.textlength(run, font=font) for run, font in split_runs(text, primary, fallback))


def wrap(text, font, fallback, width, draw):
    # Line-wrap only: characters and punctuation are neither rewritten nor removed.
    result = []
    for line in text.split('\n'):
        cur = ''
        for ch in line:
            candidate = cur + ch
            if cur and line_width(candidate, font, fallback, draw) > width:
                if ch in '，。！？；：、）》】」』' and len(cur) > 1:
                    result.append(cur[:-1])
                    cur = cur[-1] + ch
                else:
                    result.append(cur)
                    cur = ch
            else:
                cur = candidate
        result.append(cur)
    return result


def checked_text(value, name):
    if not isinstance(value, str):
        raise ValueError(f'{name} must be a string')
    return value


def main():
    parser = argparse.ArgumentParser(description='Render user-supplied text and optional bundled illustrations without an image API.')
    parser.add_argument('--input', required=True, help='UTF-8 JSON input file')
    parser.add_argument('--output', required=True, help='Output PNG path')
    parser.add_argument('--font', help='Path to a Chinese TrueType or OpenType font')
    parser.add_argument('--illustrations-dir', type=Path, help='Directory of topic-specific PNGs named by illustration key; defaults to bundled library')
    args = parser.parse_args()
    with open(args.input, encoding='utf-8') as f:
        data = json.load(f)
    if not isinstance(data, dict) or not isinstance(data.get('sections'), list):
        raise ValueError('Input must have a sections array')
    illustration_dir = args.illustrations_dir if args.illustrations_dir is not None else ASSETS
    if not illustration_dir.is_dir():
        raise ValueError(f'Illustration directory not found: {illustration_dir}')
    fontfile = font_path(args.font)
    fonts = {k: ImageFont.truetype(fontfile, n) for k,n in [('title',64),('subtitle',37),('heading',48),('body',36)]}
    fallback_path = ROOT / 'assets' / 'fonts' / 'DejaVuSans.ttf'
    fallbacks = {k: ImageFont.truetype(str(fallback_path), n) if fallback_path.is_file() else None
                 for k,n in [('title',64),('subtitle',37),('heading',48),('body',36)]}
    measure = ImageDraw.Draw(Image.new('RGB', (1,1)))
    ops = []
    y = 100
    advances = {'title': 86, 'subtitle': 62, 'heading': 72, 'body': 58}

    def add_text(text, style, color, x, top, available_width, target):
        for line in wrap(text, fonts[style], fallbacks[style], available_width, measure):
            target.append(('line', x, top, style, color, line))
            top += advances[style]
        return top

    title_start = len(ops)
    y = add_text(checked_text(data.get('title',''), 'title'), 'title', DARK, MARGIN, y, WIDTH-2*MARGIN, ops)
    for pos in range(title_start, len(ops)):
        kind, _, top, style, color, line = ops[pos]
        ops[pos] = (kind, int((WIDTH-line_width(line, fonts[style], fallbacks[style], measure))/2), top, style, color, line)
    if data.get('subtitle'):
        y += 10
        subtitle_start = len(ops)
        y = add_text(checked_text(data['subtitle'], 'subtitle'), 'subtitle', DARK, MARGIN, y, WIDTH-2*MARGIN, ops)
        for pos in range(subtitle_start, len(ops)):
            kind, _, top, style, color, line = ops[pos]
            ops[pos] = (kind, int((WIDTH-line_width(line, fonts[style], fallbacks[style], measure))/2), top, style, color, line)
    y += 56
    accepted = {'auto','text-left','text-right','image-inline','image-top','image-middle','image-bottom','text-only','warning'}
    for index, section in enumerate(data['sections']):
        if not isinstance(section, dict):
            raise ValueError('Each section must be an object')
        heading = checked_text(section.get('heading',''), f'sections[{index}].heading')
        body = checked_text(section.get('body',''), f'sections[{index}].body')
        layout = section.get('layout', 'auto')
        if layout not in accepted:
            raise ValueError(f'Unknown layout {layout!r}; use one of {sorted(accepted)}')
        illustration = section.get('illustration')
        img = None
        if illustration:
            if not isinstance(illustration, str) or not illustration.replace('-','').isalnum():
                raise ValueError('Illustration must be a simple asset key')
            path = illustration_dir / (illustration + '.png')
            if not path.is_file():
                raise ValueError(f'Unknown illustration {illustration!r}; use an existing asset or omit it')
            with Image.open(path) as loaded:
                img = loaded.convert('RGBA')
            # Trim only fully transparent padding, never opaque picture content.
            alpha_box = img.getchannel('A').getbbox()
            if alpha_box:
                img = img.crop(alpha_box)
        if layout == 'auto':
            if any(term in heading for term in ('红旗','警示','紧急')):
                layout = 'warning'
            elif not img:
                layout = 'text-only'
            elif len(body) > 110:
                first = body.split('\n', 1)[0]
                layout = ('image-inline' if index % 2 and len(first) <= 100 else 'image-middle') if '\n' in body else 'image-top'
            else:
                layout = 'text-left' if index % 2 == 0 else 'text-right'
        if layout in ('text-left','text-right','image-inline','image-top','image-middle','image-bottom') and img is None:
            raise ValueError(f'Layout {layout!r} requires an illustration')
        if layout == 'text-only' and img is not None:
            raise ValueError("text-only cannot be used with an illustration; choose image-bottom or remove it")

        section_ops = []
        is_warning = layout == 'warning'
        start = y
        x = MARGIN + (28 if is_warning else 0)
        usable = WIDTH - 2 * x
        if is_warning: y += 28
        if heading:
            y = add_text(heading, 'heading', ORANGE, x, y, usable, section_ops)
            y += 16
        def add_image(max_width, max_height):
            nonlocal y, img
            scale = min(max_width / img.width, max_height / img.height, 2.0)
            size = (max(1, round(img.width * scale)), max(1, round(img.height * scale)))
            sized = img.resize(size, Image.Resampling.LANCZOS)
            section_ops.append(('image', (WIDTH-sized.width)//2, y, sized))
            y += sized.height + 24

        if layout in ('text-left','text-right','image-inline'):
            gap, image_width = 28, min(400, int(usable * 0.44))
            text_width = usable - image_width - gap
            scale = min(image_width/img.width, 440/img.height, 2.0)
            img = img.resize((max(1,round(img.width*scale)),max(1,round(img.height*scale))),Image.Resampling.LANCZOS)
            image_left = layout == 'text-right' or (layout == 'image-inline' and index % 2 == 1)
            text_x = x + image_width + gap if image_left else x
            image_x = x if image_left else x + text_width + gap
            first, separator, rest = body.partition('\n') if layout == 'image-inline' else (body, '', '')
            text_end = add_text(first, 'body', DARK, text_x, y, text_width, section_ops) if first else y
            section_ops.append(('image', image_x + (image_width-img.width)//2, y, img))
            y = max(text_end, y + img.height)
            if separator:
                y += 20
                y = add_text(rest, 'body', DARK, x, y, usable, section_ops)
        else:
            if layout == 'image-top':
                add_image(min(usable, 760), 600)
            if layout == 'image-middle' and body:
                cut = body.find('\n')
                if cut < 0:
                    add_image(min(usable, 760), 600)
                    y = add_text(body, 'body', DARK, x, y, usable, section_ops)
                else:
                    y = add_text(body[:cut], 'body', DARK, x, y, usable, section_ops)
                    y += 12
                    add_image(min(usable, 760), 600)
                    y = add_text(body[cut+1:], 'body', DARK, x, y, usable, section_ops)
            else:
                if body:
                    y = add_text(body, 'body', DARK, x, y, usable, section_ops)
                if img is not None and layout not in ('image-top',):
                    y += 20
                    add_image(min(usable, 760), 600)
        if is_warning:
            y += 28
            ops.append(('box', MARGIN-12, start, WIDTH-MARGIN+12, y))
        ops.extend(section_ops)
        y += 58
    total = y + 50
    if total > 50000:
        raise SystemExit('Document is too long for one image. Split into ordered input files without dropping text.')
    canvas = Image.new('RGB', (WIDTH, total), BG)
    draw = ImageDraw.Draw(canvas)

    def brush(left, top, width, height, seed):
        # Pale, irregular strokes remain behind the text and never change it.
        rng = random.Random(seed)
        right = min(WIDTH - MARGIN // 2, left + width)
        for row in range(4):
            yy = top + 13 + row * max(5, (height - 22) // 4)
            inset = rng.randint(0, 18)
            draw.line([(left + inset, yy), (right - rng.randint(0, 20), yy + rng.randint(-3, 3))],
                      fill=('#f8e6ce' if row % 2 else '#f9ead7'), width=16)

    def sprig(x, top):
        draw.line([(x, top + 42), (x + 18, top + 10)], fill='#a5ae83', width=3)
        draw.ellipse((x-4, top+21, x+9, top+32), fill='#b9c29a')
        draw.ellipse((x+9, top+6, x+22, top+18), fill='#b9c29a')
        draw.ellipse((x+25, top+23, x+33, top+31), fill='#e5b788')

    for op in ops:
        if op[0] == 'box':
            _, left, top, right, bottom = op
            draw.rounded_rectangle((left, top, right, bottom), radius=24, fill='#fbe9df', outline='#e6b8a4', width=2)
        elif op[0] == 'line':
            _, x, top, style, color, line = op
            if line and style in ('title', 'heading'):
                width = int(line_width(line, fonts[style], fallbacks[style], measure))
                brush(max(0, x - 10), top + 3, min(width + 30, WIDTH - x - 20),
                      advances[style] - 4, top)
                if x + width + 65 < WIDTH - MARGIN:
                    sprig(int(x + width + 28), top + 6)
            for run, font in split_runs(line, fonts[style], fallbacks[style]):
                draw.text((x,top), run, font=font, fill=color,
                          stroke_width=1 if style in ('title', 'heading') else 0,
                          stroke_fill=color)
                x += draw.textlength(run, font=font)
        else:
            _, x, top, img = op
            canvas.paste(img, (x,top), img)
    output=Path(args.output); output.parent.mkdir(parents=True,exist_ok=True)
    canvas.save(output,format='PNG')
    print(f'Saved {output} ({WIDTH} x {total})')

if __name__ == '__main__':
    try: main()
    except (ValueError, OSError, json.JSONDecodeError) as exc: sys.exit(f'Error: {exc}')
