#!/usr/bin/env python3
"""Offline, deterministic Chinese long-image layout. See SKILL.md for input schema."""
import argparse
import json
import os
import sys
from pathlib import Path

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
    choices = [explicit, os.getenv('HEALTH_IMAGE_FONT'),
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


def wrap(text, font, width, draw):
    # Line-wrap only: characters and punctuation are neither rewritten nor removed.
    result = []
    for line in text.split('\n'):
        cur = ''
        for ch in line:
            candidate = cur + ch
            if cur and draw.textlength(candidate, font=font) > width:
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
    measure = ImageDraw.Draw(Image.new('RGB', (1,1)))
    blocks=[]
    def add_text(text, style, color):
        for line in wrap(text, fonts[style], WIDTH-2*MARGIN, measure):
            blocks.append(('line', line, style, color, {'title':86,'subtitle':62,'heading':72,'body':58}[style]))
    def space(n): blocks.append(('space',n))
    add_text(checked_text(data.get('title',''), 'title'), 'title', ORANGE)
    if data.get('subtitle'):
        space(10); add_text(checked_text(data['subtitle'],'subtitle'), 'subtitle', DARK)
    space(56)
    for index, section in enumerate(data['sections']):
        if not isinstance(section,dict): raise ValueError('Each section must be an object')
        heading=checked_text(section.get('heading',''),f'sections[{index}].heading')
        body=checked_text(section.get('body',''),f'sections[{index}].body')
        if heading: add_text(heading,'heading',ORANGE); space(20)
        if body: add_text(body,'body',DARK); space(20)
        illustration=section.get('illustration')
        if illustration:
            if not isinstance(illustration,str) or not illustration.replace('-','').isalnum():
                raise ValueError('Illustration must be a simple asset key')
            path=illustration_dir/(illustration+'.png')
            if not path.is_file(): raise ValueError(f'Unknown illustration {illustration!r}; use an existing asset or omit it')
            img=Image.open(path).convert('RGBA')
            img.thumbnail((480,340),Image.Resampling.LANCZOS)
            blocks.append(('image',img,img.height+25))
        space(58)
    total = 100 + sum(b[-1] if b[0] in ('line','image') else b[1] for b in blocks) + 50
    if total > 50000: raise SystemExit('Document is too long for one image. Split into ordered input files without dropping text.')
    canvas=Image.new('RGB',(WIDTH,total),BG)
    draw=ImageDraw.Draw(canvas)
    y=100
    for b in blocks:
        if b[0]=='space': y+=b[1]
        elif b[0]=='line':
            _,line,style,color,advance=b
            draw.text((MARGIN,y),line,font=fonts[style],fill=color,stroke_width=0)
            y+=advance
        else:
            _,img,advance=b
            canvas.paste(img,((WIDTH-img.width)//2,y),img)
            y+=advance
    output=Path(args.output); output.parent.mkdir(parents=True,exist_ok=True)
    canvas.save(output,format='PNG')
    print(f'Saved {output} ({WIDTH} x {total})')

if __name__ == '__main__':
    try: main()
    except (ValueError, OSError, json.JSONDecodeError) as exc: sys.exit(f'Error: {exc}')
