#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const files = [
  'D:\\OneDrive\\_sandbox\\AiDiy2026\\frontend_web\\src\\components\\Mマスタ\\M商品構成\\M商品構成編集.vue',
  'D:\\OneDrive\\_sandbox\\AiDiy2026\\frontend_web\\src\\components\\Tトラン\\T生産\\T生産編集.vue',
  'D:\\OneDrive\\_sandbox\\AiDiy2026\\frontend_web\\src\\components\\Mマスタ\\M商品構成\\components\\M商品構成一覧テーブル.vue',
  'D:\\OneDrive\\_sandbox\\AiDiy2026\\frontend_web\\src\\components\\Tトラン\\T生産\\components\\T生産一覧テーブル.vue',
];

const errorMessageFiles = {
  'D:\\OneDrive\\_sandbox\\AiDiy2026\\frontend_web\\src\\components\\Mマスタ\\M商品構成\\M商品構成編集.vue': true,
  'D:\\OneDrive\\_sandbox\\AiDiy2026\\frontend_web\\src\\components\\Tトラン\\T生産\\T生産編集.vue': true,
};

for (const fpath of files) {
  try {
    // Read the file with UTF-8 encoding
    let content = fs.readFileSync(fpath, 'utf-8');
    
    // Replace the main text
    const newContent = content.replace(/生産ロット/g, '最小ロット数量');
    
    // Replace error message if this is one of the specified files
    let finalContent = newContent;
    if (errorMessageFiles[fpath]) {
      finalContent = finalContent.replace(
        '生産ロットは0より大きい値を入力してください。',
        '最小ロット数量は0より大きい値を入力してください。'
      );
    }
    
    // Write back with UTF-8 encoding and LF newlines
    fs.writeFileSync(fpath, finalContent, { encoding: 'utf-8' });
    
    console.log(`✓ Updated: ${fpath}`);
  } catch (e) {
    console.error(`✗ Error updating ${fpath}: ${e.message}`);
  }
}

console.log('\nAll files processed successfully!');
