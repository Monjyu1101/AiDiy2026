import json
import subprocess
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image, ImageDraw
from pypdf import PdfReader

root = Path(__file__).resolve().parents[2]
books = json.loads((root / 'tmp/pdfs/final-books.json').read_text(encoding='utf-8'))
output = root / 'tmp/pdfs/final-960-qa'
output.mkdir(exist_ok=True)
poppler = Path('C:/Users/admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin/pdftoppm.exe')


def verify(entry):
    index, book = entry
    pdf = root / '_AIDIY/knowledge' / Path(book['name']).with_suffix('.pdf')
    reader = PdfReader(pdf)
    page_texts = [page.extract_text() for page in reader.pages]
    assert all(text.strip() for text in page_texts), pdf
    images = sum(len(page.images) for page in reader.pages)
    assert images == book['images'], (book['name'], images, book['images'])
    if 'frontend_web,AiDiy' in book['name']:
        text = ''.join(unicodedata.normalize('NFKC', ''.join(page_texts)).split())
        for expected in ('277件すべて成功', '検証作業が衝突', '検証だけを別途依頼'):
            assert expected in text, expected
        assert '後で本文の最終版' not in text
    folder = output / f'book-{index:02d}'
    folder.mkdir(exist_ok=True)
    subprocess.run([str(poppler), '-scale-to', '1500', '-png', str(pdf), str(folder / 'page')], check=True, capture_output=True)
    pages = sorted(folder.glob('page-*.png'))
    assert len(pages) == len(reader.pages)
    sheets = []
    for start in range(0, len(pages), 6):
        sheet = Image.new('RGB', (1500, 1470), '#d4dce0')
        draw = ImageDraw.Draw(sheet)
        for offset, path in enumerate(pages[start:start + 6]):
            with Image.open(path) as image:
                image.thumbnail((490, 705))
                x = (offset % 3) * 500 + (500 - image.width) // 2
                y = (offset // 3) * 735 + 25
                sheet.paste(image, (x, y))
                draw.text(((offset % 3) * 500 + 10, (offset // 3) * 735 + 5), f'Book {index:02d} / Page {start + offset + 1}', fill='black')
        target = folder / f'contact-{start // 6 + 1:02d}.jpg'
        sheet.save(target, quality=92)
        sheets.append(str(target))
    result = {'index': index, 'name': book['name'], 'pages': len(pages), 'images': images, 'sheets': sheets}
    print(json.dumps({key: value for key, value in result.items() if key != 'sheets'}, ensure_ascii=False), flush=True)
    return result


with ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(verify, enumerate(books, 1)))
(output / 'results.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'全{sum(item["pages"] for item in results)}ページ / 画像{sum(item["images"] for item in results)}枚 / 読込・本文照合OK', flush=True)
