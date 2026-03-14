import os

try:
    os.remove(r'D:\OneDrive\_sandbox\AiDiy2026\fix_vue_rename.py')
    print('Deleted: fix_vue_rename.py')
except Exception as e:
    print(f'Error deleting .py: {e}')

try:
    os.remove(r'D:\OneDrive\_sandbox\AiDiy2026\fix_vue_rename.js')
    print('Deleted: fix_vue_rename.js')
except Exception as e:
    print(f'Error deleting .js: {e}')

# Verify files are gone
import os.path
if not os.path.exists(r'D:\OneDrive\_sandbox\AiDiy2026\fix_vue_rename.py'):
    print('✓ Confirmed: fix_vue_rename.py is deleted')
else:
    print('✗ ERROR: fix_vue_rename.py still exists')

if not os.path.exists(r'D:\OneDrive\_sandbox\AiDiy2026\fix_vue_rename.js'):
    print('✓ Confirmed: fix_vue_rename.js is deleted')
else:
    print('✗ ERROR: fix_vue_rename.js still exists')
