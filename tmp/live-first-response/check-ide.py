from pathlib import Path
from urllib.parse import unquote
from html.parser import HTMLParser
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfReader
import json, re, subprocess, unicodedata

ROOT = Path(__file__).resolve().parents[2]
WORK = Path(__file__).parent / "qa-ide-final"
WORK.mkdir(exist_ok=True)
KNOWLEDGE = ROOT / '_AIDIY/knowledge'
POPPLER = Path(r'C:/Users/admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin/pdftoppm.exe')

def normalize(text):
    # Chrome's Japanese font map extracts several kanji as equivalent radicals.
    text = unicodedata.normalize('NFKC', text).translate(str.maketrans('⻑⻘⻭黑', '長青歯黒'))
    return re.sub(r'\s+', '', text)

def slug(text):
    return ''.join(c for c in text.lower().replace(' ', '-') if c in '-_' or not unicodedata.category(c).startswith(('P', 'S')))

class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__(); self.skip = 0; self.parts = []
    def handle_starttag(self, tag, attrs):
        if tag in ('style', 'script'): self.skip += 1
    def handle_endtag(self, tag):
        if tag in ('style', 'script'): self.skip -= 1
    def handle_data(self, data):
        if not self.skip and data.strip(): self.parts.append(data.strip())

def check(book):
    source = book.read_text(encoding='utf-8')
    assert not book.read_bytes().startswith(b'\xef\xbb\xbf')
    issues = []; image_count = 0; link_count = 0
    for m in re.finditer(r'(!?)\[([^\]]*)\]\(([^\n)]+)\)', source):
        target = unquote(m[3].strip('<>'))
        if re.match(r'\w+://', target): continue
        link_count += 1
        path, _, anchor = target.partition('#')
        dest = (book.parent / path).resolve() if path else book
        if not dest.exists(): issues.append('missing: ' + target); continue
        if anchor and dest.suffix == '.md':
            headings = re.findall(r'^#{1,6}\s+(.+)$', dest.read_text(encoding='utf-8'), re.M)
            if anchor not in [slug(h) for h in headings]: issues.append('anchor: ' + target)
        if m[1]:
            image_count += 1
            with Image.open(dest) as img:
                if max(img.size) > 960: issues.append('oversize: ' + dest.name)
            if dest.parent.name != book.stem: issues.append('image folder: ' + dest.name)
            caption = source[:m.start()].rstrip().split('\n')[-1]
            if not caption or caption.startswith(('![', '#', '|')): issues.append('caption: ' + dest.name)
    pdf = book.with_suffix('.pdf')
    reader = PdfReader(pdf)
    pages = [page.extract_text() for page in reader.pages]
    text = normalize(''.join(re.sub(r'AiDiy\s*総合テスト実施記録\s*\d+\s*/\s*\d+', '', page) for page in pages))
    html = ROOT / 'tmp/pdfs' / book.with_suffix('.html').name
    parser = VisibleText(); parser.feed(html.read_text(encoding='utf-8'))
    missing = [part for part in parser.parts if len(normalize(part)) >= 5 and normalize(part) not in text]
    if missing: issues.extend('pdf text: ' + part[:120] for part in missing)
    out = WORK / book.stem; out.mkdir(exist_ok=True)
    subprocess.run([str(POPPLER), '-scale-to', '850', '-png', str(pdf), str(out / 'page')], check=True, capture_output=True)
    font = ImageFont.truetype('C:/Windows/Fonts/meiryo.ttc', 18)
    rendered = sorted(out.glob('page-*.png'), key=lambda p: int(p.stem.split('-')[-1]))
    assert len(rendered) == len(pages)
    sheets = []
    for first in range(0, len(rendered), 6):
        sheet = Image.new('RGB', (1240, 2710), '#bfc5cb')
        draw = ImageDraw.Draw(sheet)
        draw.text((12, 6), book.stem, font=font, fill='black')
        for n, path in enumerate(rendered[first:first+6]):
            with Image.open(path) as im:
                im.thumbnail((602, 850))
                x = 12 + (n % 2) * 616; y = 40 + (n // 2) * 890
                sheet.paste(im, (x, y))
                draw.text((x, y+851), f'page {first+n+1} / {len(rendered)}', font=font, fill='black')
        target = out / f'sheet-{first//6+1:02}.png'; sheet.save(target); sheets.append(str(target))
    return {'book': book.name, 'pages': len(pages), 'images': image_count, 'links': link_count, 'issues': issues, 'sheets': sheets}

books = [p for p in sorted(KNOWLEDGE.glob('セルフテスト*.md')) if '総合評価：✅' in p.read_text(encoding='utf-8')]
books = [p for p in books if p.name == 'セルフテスト,aidiy_ide,操作編.md']
with ThreadPoolExecutor(max_workers=3) as pool:
    result = list(pool.map(check, books))
(WORK / 'checks.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
for item in result:
    print({k: v for k, v in item.items() if k != 'sheets'})
print('TOTAL', sum(x['pages'] for x in result), 'pages;', sum(x['images'] for x in result), 'images;', sum(x['links'] for x in result), 'links')
