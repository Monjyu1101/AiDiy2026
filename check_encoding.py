import os

files = [
    r"D:\OneDrive\_sandbox\AiDiy2026\frontend_avatar\src\components\AIイメージ.vue",
    r"D:\OneDrive\_sandbox\AiDiy2026\frontend_web\src\components\AiDiy\compornents\AIイメージ.vue",
    r"D:\OneDrive\_sandbox\AiDiy2026\frontend_avatar\src\AiDiy.vue",
]

for path in files:
    with open(path, 'rb') as f:
        content = f.read()
    
    # Check for BOM
    has_bom = content.startswith(b'\xef\xbb\xbf')
    # Check for CRLF
    has_crlf = b'\r\n' in content
    
    print(f"{os.path.basename(path)}: BOM={has_bom}, CRLF={has_crlf}")
    
    if has_crlf or has_bom:
        # Fix: remove BOM, convert CRLF to LF
        if has_bom:
            content = content[3:]
        content = content.replace(b'\r\n', b'\n')
        with open(path, 'wb') as f:
            f.write(content)
        print(f"  -> Fixed")
    else:
        print(f"  -> OK")
