#!/bin/bash

# File paths (using forward slashes for compatibility)
files=(
  "D:/OneDrive/_sandbox/AiDiy2026/frontend_web/src/components/Tトラン/T生産/T生産編集.vue"
  "D:/OneDrive/_sandbox/AiDiy2026/frontend_web/src/components/Mマスタ/M商品構成/components/M商品構成一覧テーブル.vue"
  "D:/OneDrive/_sandbox/AiDiy2026/frontend_web/src/components/Tトラン/T生産/components/T生産一覧テーブル.vue"
)

for fpath in "${files[@]}"; do
  # Convert forward slashes to backslashes for Windows paths if needed
  win_fpath="${fpath//\//\\}"
  
  # Use sed to replace the text
  sed -i 's/生産ロット/最小ロット数量/g' "$fpath"
  echo "✓ Updated: $fpath"
done

# Special handling for error messages in specific files
error_msg_files=(
  "D:/OneDrive/_sandbox/AiDiy2026/frontend_web/src/components/Tトラン/T生産/T生産編集.vue"
)

for fpath in "${error_msg_files[@]}"; do
  sed -i 's/最小ロット数量は0より大きい値を入力してください。/最小ロット数量は0より大きい値を入力してください。/g' "$fpath"
  echo "✓ Updated error message in: $fpath"
done

echo "All files processed successfully!"
