#!/usr/bin/env python3
"""Offline, deterministic Chinese long-image layout. See SKILL.md for input schema."""
import argparse
import gzip
import json
import os
import sys
import tempfile
import atexit
import random
import math
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


@lru_cache(maxsize=4)
def bundled_font(name):
    path = ROOT / 'assets' / 'fonts' / name
    if path.is_file():
        return str(path)
    parts = sorted(path.parent.glob(name + '.gz.part[0-9][0-9][0-9]'))
    if not parts:
        return str(path)
    try:
        data = gzip.decompress(b''.join(part.read_bytes() for part in parts))
    except (OSError, EOFError) as exc:
        raise ValueError(f'Bundled font is incomplete: {name}') from exc
    with tempfile.NamedTemporaryFile(suffix='.ttf', delete=False) as tmp:
        tmp.write(data)
        result = Path(tmp.name)
    atexit.register(lambda: result.unlink(missing_ok=True))
    return str(result)


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
        bundled_font('LXGWWenKai-Regular.ttf'), str(bundled),
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
        start = len(result)
        cur = ''
        for ch in line:
            candidate = cur + ch
            if cur and line_width(candidate, font, fallback, draw) > width:
                # Prefer a natural punctuation boundary when it does not waste
                # too much line width; never alter the original characters.
                breaks = [i + 1 for i, c in enumerate(cur) if c in '，。！？；：、']
                cut = breaks[-1] if breaks else 0
                if cut and line_width(cur[:cut], font, fallback, draw) >= width * 0.48 and (cut < len(cur) or ch not in '，。！？；：、）》】」』'):
                    result.append(cur[:cut])
                    cur = cur[cut:] + ch
                elif ch in '，。！？；：、）》】」』' and len(cur) > 1:
                    result.append(cur[:-1])
                    cur = cur[-1] + ch
                else:
                    result.append(cur)
                    cur = ch
            else:
                cur = candidate
        result.append(cur)
        # Avoid a near-empty final line in an individual paragraph.
        if len(result) - start >= 2 and len(result[-1]) <= 2:
            previous, last = result[-2:]
            for count in range(min(2, len(previous) - 1), 0, -1):
                tail = previous[-count:] + last
                if tail[0] not in '，。！？；：、）》】」』' and line_width(tail, font, fallback, draw) <= width:
                    result[-2:] = [previous[:-count], tail]
                    break
    return result


def checked_text(value, name):
    if not isinstance(value, str):
        raise ValueError(f'{name} must be a string')
    return value


def split_for_inline(text, font, fallback, width, draw, max_lines=4):
    """Split only at paragraph boundaries; preserve every input character."""
    consumed = 0
    for paragraph in text.splitlines(keepends=True):
        end = consumed + len(paragraph)
        candidate = text[:end].rstrip('\r\n')
        if consumed and len(wrap(candidate, font, fallback, width, draw)) > max_lines:
            break
        consumed = end
    return text[:consumed], text[consumed:]


def feather_image_edges(img, amount=0.06):
    """Fade image edges only when explicitly requested; never modify source files."""
    width, height = img.size
    pad = max(1, int(min(width, height) * amount))
    mask = Image.new('L', (width, height), 255)
    md = ImageDraw.Draw(mask)
    for i in range(pad):
        value = round(255 * i / pad)
        md.rectangle((i, i, width - 1 - i, height - 1 - i), outline=value)
    from PIL import ImageChops
    img.putalpha(ImageChops.multiply(img.getchannel('A'), mask))
    return img


def main():
    parser = argparse.ArgumentParser(description='Render user-supplied text and optional bundled illustrations without an image API.')
    parser.add_argument('--input', required=True, help='UTF-8 JSON input file')
    parser.add_argument('--output', required=True, help='Output PNG path')
    parser.add_argument('--font', help='Path to a Chinese TrueType or OpenType font')
    parser.add_argument('--title-font', help='Optional Chinese font for title and headings; body keeps --font or the default')
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
    fonts = {k: ImageFont.truetype(fontfile, n) for k,n in [('title',78),('subtitle',37),('heading',50),('body',44)]}
    fallback_path = ROOT / 'assets' / 'fonts' / 'DejaVuSans.ttf'
    fallbacks = {k: ImageFont.truetype(str(fallback_path), n) if fallback_path.is_file() else None
                 for k,n in [('title',78),('subtitle',37),('heading',50),('body',44)]}
    bundled_title = Path(bundled_font('LXGWZhenKaiSlabGB-Regular.ttf'))
    if not args.title_font and bundled_title.is_file():
        args.title_font = str(bundled_title)
    if args.title_font:
        if not Path(args.title_font).is_file():
            raise ValueError(f'Title font not found: {args.title_font}')
        for style, size in [('title',78), ('heading',50)]:
            fallbacks[style] = fonts[style]
            fonts[style] = ImageFont.truetype(args.title_font, size)
    measure = ImageDraw.Draw(Image.new('RGB', (1,1)))
    ops = []
    y = 100
    advances = {'title': 104, 'subtitle': 62, 'heading': 76, 'body': 70}

    def add_text(text, style, color, x, top, available_width, target):
        paragraphs = text.split('\n')
        for index, paragraph in enumerate(paragraphs):
            for line in wrap(paragraph, fonts[style], fallbacks[style], available_width, measure):
                target.append(('line', x, top, style, color, line))
                top += advances[style]
            if style == 'body' and paragraph and index < len(paragraphs) - 1:
                top += 14
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
        edge_mode = section.get('illustration_edge', 'keep')
        if edge_mode not in ('keep', 'feather'):
            raise ValueError("illustration_edge must be 'keep' or 'feather'")
        img = None
        if illustration:
            if not isinstance(illustration, str) or not illustration.replace('-','').isalnum():
                raise ValueError('Illustration must be a simple asset key')
            path = illustration_dir / (illustration + '.png')
            if not path.is_file():
                raise ValueError(f'Unknown illustration {illustration!r}; use an existing asset or omit it')
            with Image.open(path) as loaded:
                img = loaded.convert('RGBA')
            alpha_min, alpha_max = img.getchannel('A').getextrema()
            if alpha_min == 255 and edge_mode == 'keep':
                print(f'Note: {path.name} has an opaque rectangular background; inspect for visible edges.', file=sys.stderr)
            if edge_mode == 'feather':
                img = feather_image_edges(img)
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
                layout = 'image-middle' if index % 3 == 2 and '\n' in body else 'image-inline'
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

        if layout == 'image-inline' and body:
            inline_width = usable - min(300, int(usable * 0.34)) - 28
            if len(wrap(body.split('\n', 1)[0], fonts['body'], fallbacks['body'], inline_width, measure)) > 7:
                layout = 'image-bottom'
        if layout in ('text-left','text-right','image-inline'):
            gap, image_width = 28, min(300, int(usable * 0.34))
            text_width = usable - image_width - gap
            image_left = layout == 'text-right' or (layout == 'image-inline' and index % 2 == 1)
            text_x = x + image_width + gap if image_left else x
            image_x = x if image_left else x + text_width + gap
            if layout == 'image-inline':
                first, rest = split_for_inline(body, fonts['body'], fallbacks['body'], text_width, measure, 6)
                first = first.rstrip('\r\n')
                side_lines = len(wrap(first, fonts['body'], fallbacks['body'], text_width, measure)) if first else 1
                image_height = min(440, max(280, side_lines * advances['body'] + 20))
            else:
                first, rest = body, ''
                image_height = 440
            scale = min(image_width/img.width, image_height/img.height, 2.0)
            img = img.resize((max(1,round(img.width*scale)),max(1,round(img.height*scale))),Image.Resampling.LANCZOS)
            actual_image_x = image_x + (image_width-img.width)//2
            text_end = y
            alpha = img.getchannel('A').point(lambda a: 255 if a > 24 else 0)
            # Measure the occupied silhouette in each text band, not its canvas.
            for paragraph in first.split('\n'):
                remaining = paragraph
                while remaining:
                    band_top = max(0, text_end - y - 8)
                    band_bottom = min(img.height, text_end - y + advances['body'] + 8)
                    box = alpha.crop((0, band_top, img.width, band_bottom)).getbbox() if band_top < band_bottom else None
                    line_x, line_right = x, WIDTH - x
                    if box:
                        if image_left:
                            line_x = max(x, actual_image_x + box[2] + 30)
                        else:
                            line_right = min(line_right, actual_image_x + box[0] - 30)
                    available = line_right - line_x
                    line = wrap(remaining, fonts['body'], fallbacks['body'], available, measure)[0]
                    section_ops.append(('line', line_x, text_end, 'body', DARK, line))
                    remaining = remaining[len(line):]
                    text_end += advances['body']
                text_end += 14
            section_ops.append(('image', actual_image_x, y, img))
            y = max(text_end, y + img.height)
            if rest:
                # A line break at the transition is already supplied by the layout.
                if rest.startswith('\n'):
                    rest = rest[1:]
                y += 12
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
    brush_file = ROOT / 'assets' / 'decor' / 'watercolor-brush.png'
    brush_art = None
    if brush_file.is_file():
        with Image.open(brush_file) as loaded:
            brush_art = loaded.convert('RGBA')
        bbox = brush_art.getchannel('A').getbbox()
        if bbox:
            brush_art = brush_art.crop(bbox)
    sprig_file = ROOT / 'assets' / 'decor' / 'watercolor-sprig.png'
    sprig_art = None
    if sprig_file.is_file():
        with Image.open(sprig_file) as loaded:
            sprig_art = loaded.convert('RGBA')
        bbox = sprig_art.getchannel('A').getbbox()
        if bbox:
            sprig_art = sprig_art.crop(bbox)

    def brush(left, top, width, height, seed):
        # Artwork stays behind the text; a procedural fallback preserves offline use.
        rng = random.Random(seed)
        right = min(WIDTH - MARGIN // 2, left + width)
        if brush_art is not None and right > left:
            stroke = brush_art.resize((right-left, height), Image.Resampling.LANCZOS)
            canvas.paste(stroke, (left, top), stroke)
            return
        for row in range(4):
            yy = top + 13 + row * max(5, (height - 22) // 4)
            inset = rng.randint(0, 18)
            draw.line([(left + inset, yy), (right - rng.randint(0, 20), yy + rng.randint(-3, 3))],
                      fill=('#f8e6ce' if row % 2 else '#f9ead7'), width=16)

    def sprig(x, top):
        if sprig_art is not None:
            leaf = sprig_art.copy()
            leaf.thumbnail((45, 45), Image.Resampling.LANCZOS)
            canvas.paste(leaf, (x, top + 2), leaf)
            return
        draw.line([(x, top + 42), (x + 18, top + 10)], fill='#a5ae83', width=3)
        draw.ellipse((x-4, top+21, x+9, top+32), fill='#b9c29a')
        draw.ellipse((x+9, top+6, x+22, top+18), fill='#b9c29a')
        draw.ellipse((x+25, top+23, x+33, top+31), fill='#e5b788')

    def wash(left, top, right, bottom, color, seed):
        # Broad irregular translucent pigment; no rectangular border.
        rng = random.Random(seed)
        layer = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        cx, cy = (left + right) / 2, (top + bottom) / 2
        rx, ry = (right-left)/2, (bottom-top)/2
        for k in range(4):
            points = []
            for i in range(80):
                angle = 2 * math.pi * i / 80
                jitter = rng.uniform(0.96, 1.02)
                # Superellipse reads as a brush stroke with soft irregular ends.
                xx, yy = math.cos(angle), math.sin(angle)
                points.append((cx + math.copysign(abs(xx)**0.55, xx)*rx*jitter,
                               cy + math.copysign(abs(yy)**0.65, yy)*ry*jitter))
            ld.polygon(points, fill=(*color, 32 + k * 8))
        from PIL import ImageFilter
        layer = layer.filter(ImageFilter.GaussianBlur(4))
        canvas.paste(layer, (0, 0), layer)

    for op in ops:
        if op[0] == 'box':
            _, left, top, right, bottom = op
            wash(left, top, right, bottom, (163, 184, 116), top)
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
                          stroke_width=0,
                          stroke_fill=color)
                x += draw.textlength(run, font=font)
        else:
            _, x, top, img = op
            wash(x-18, top+img.height-38, x+img.width+18, top+img.height+10, (218, 189, 134), top)
            canvas.paste(img, (x,top), img)
    output=Path(args.output); output.parent.mkdir(parents=True,exist_ok=True)
    canvas.save(output,format='PNG')
    print(f'Saved {output} ({WIDTH} x {total})')

if __name__ == '__main__':
    try: main()
    except (ValueError, OSError, json.JSONDecodeError) as exc: sys.exit(f'Error: {exc}')
