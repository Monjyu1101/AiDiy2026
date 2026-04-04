#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Replace text in Vue files with UTF-8 encoding and LF newlines
"""

files = [
    r'D:\OneDrive\_sandbox\AiDiy2026\frontend_web\src\components\Mマスタ\M商品構成\M商品構成編集.vue',
    r'D:\OneDrive\_sandbox\AiDiy2026\frontend_web\src\components\Tトラン\T生産\T生産編集.vue',
    r'D:\OneDrive\_sandbox\AiDiy2026\frontend_web\src\components\Mマスタ\M商品構成\components\M商品構成一覧テーブル.vue',
    r'D:\OneDrive\_sandbox\AiDiy2026\frontend_web\src\components\Tトラン\T生産\components\T生産一覧テーブル.vue',
]

error_message_files = {
    r'D:\OneDrive\_sandbox\AiDiy2026\frontend_web\src\components\Mマスタ\M商品構成\M商品構成編集.vue',
    r'D:\OneDrive\_sandbox\AiDiy2026\frontend_web\src\components\Tトラン\T生産\T生産編集.vue',
}

for fpath in files:
    try:
        # Read the file with UTF-8 encoding
        with open(fpath, encoding='utf-8') as f:
            content = f.read()
        
        # Replace the main text
        new_content = content.replace('生産ロット', '最小ロット数量')
        
        # Replace error message if this is one of the specified files
        if fpath in error_message_files:
            new_content = new_content.replace(
                '生産ロットは0より大きい値を入力してください。',
                '最小ロット数量は0より大きい値を入力してください。'
            )
        
        # Write back with UTF-8 encoding and LF newlines
        with open(fpath, 'w', encoding='utf-8', newline='\n') as f:
            f.write(new_content)
        
        print(f'✓ Updated: {fpath}')
    except Exception as e:
        print(f'✗ Error updating {fpath}: {e}')

print('\nAll files processed successfully!')
