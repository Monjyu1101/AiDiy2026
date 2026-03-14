import os

files = [
    r"D:\OneDrive\_sandbox\AiDiy2026\frontend_avatar\src\components\AIイメージ.vue",
    r"D:\OneDrive\_sandbox\AiDiy2026\frontend_web\src\components\AiDiy\compornents\AIイメージ.vue",
    r"D:\OneDrive\_sandbox\AiDiy2026\frontend_avatar\src\AiDiy.vue",
]

for path in files:
    with open(path, "rb") as f:
        content = f.read()
    has_bom = content.startswith(b"\xef\xbb\xbf")
    has_crlf = b"\r\n" in content
    print(f"{os.path.basename(path)}: BOM={has_bom}, CRLF={has_crlf}")
    if has_crlf or has_bom:
        if has_bom:
            content = content[3:]
        content = content.replace(b"\r\n", b"\n")
        with open(path, "wb") as f:
            f.write(content)
        print("  -> Fixed")
    else:
        print("  -> OK")
