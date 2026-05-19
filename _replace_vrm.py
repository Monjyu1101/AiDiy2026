import os, re

root = r'D:\OneDrive\_sandbox\AiDiy2026'
pattern = 'VRM_AiDiy.vrm'
replacement = 'VRM_AiDiy.vrm'
exts = {'.html', '.js', '.json', '.ts', '.vue', '.md', '.py', '.txt'}
count = 0

for dirpath, dirnames, filenames in os.walk(root):
    for fname in filenames:
        ext = os.path.splitext(fname)[1].lower()
        if ext not in exts:
            continue
        fpath = os.path.join(dirpath, fname)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
            if pattern in content:
                new_content = content.replace(pattern, replacement)
                with open(fpath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                count += 1
                print('Updated:', fpath.replace(root + os.sep, ''))
        except Exception as e:
            print('Error', fpath, e)

print(f'完了: {count} ファイル更新')
