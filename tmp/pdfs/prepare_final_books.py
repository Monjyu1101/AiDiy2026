import importlib.util
import json
import re
from pathlib import Path

root = Path(__file__).resolve().parents[2]
knowledge = root / '_AIDIY/knowledge'
spec = importlib.util.spec_from_file_location('resize_evidence', knowledge / 'images/画像サイズ調整.py')
resize = importlib.util.module_from_spec(spec)
spec.loader.exec_module(resize)
books = []
count = changed = 0
for book in sorted(knowledge.glob('セルフテスト,*.md')):
    text = book.read_text(encoding='utf-8')
    if '**総合評価：✅ OK' not in text:
        continue
    paths = sorted({(book.parent / ref).resolve() for ref in re.findall(r'!\[[^\]]*\]\(([^)]+)\)', text)})
    for path in paths:
        changed += resize.画像を縮小(path, 960, 2_147_483_647, False)
        assert not resize.画像を縮小(path, 960, 2_147_483_647, True), path
    count += len(paths)
    books.append({'name': book.name, 'images': len(paths)})
destination = root / 'tmp/pdfs/final-books.json'
destination.write_text(json.dumps(books, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'{len(books)}冊 / 掲載画像{count}枚 / 縮小{changed}枚 / 横幅960px以下・縦横比維持・画像エラー0件')
