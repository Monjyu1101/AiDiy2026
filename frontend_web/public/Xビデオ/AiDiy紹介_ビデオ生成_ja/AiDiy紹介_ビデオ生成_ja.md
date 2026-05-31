# テスト紹介_ビデオページ生成_ja
テーマ: AiDiy のビデオページ生成機能を紹介する。 ビデオページ生成_紹介.py（ひとりアバター）と ビデオページ生成_解説.py（二人掛け合い）の 2 スクリプトで、topic から scenario.js 生成 → 画像生成 → 音声合成 → HTML 組み立てまでを 9 ステップで全自動化する。 設定は _ビデオページ生成_*_設定.json（topic / folder_name / template_dir / language / shared API URL 等）で管理。状況は _ビデオページ生成_*_状況.json でステップ番号を記録し、途中再開・特定ステップ再実行が可能。 Step 00: 初期確認（設定・テンプレート・API・CodeAgents の疎通）。 Step 01: テンプレートフォルダをコピーして出力フォルダを作成。 Step 02: CodeAgents が scenario.js を生成（scenes 配列・short/long narration・画像パス・音声パス）。 Step 03: CodeAgents が index.html の表示文言をテーマに合わせて更新。 Step 04: aidiy_image_generation MCP で各シーン画像を自動生成（image_prompt を活用）。 Step 05: 中間確認（シナリオ・HTML・画像の内容を検証し問題があれば修正）。 Step 06: aidiy_text_to_speech MCP で short/long ナレーション音声を生成（edge TTS）。 Step 07: 生成音声の実再生時間を ffmpeg で計測し scenario.js の duration_sec を更新。 Step 08: 必須ファイル・画像数・音声数の最終確認。 Step 99: 完成案内。 シーン構成は最小構成で生成: scene_000（イントロ）、scene_001〜scene_005（各機能説明）、scene_999（まとめ）の計 7 シーンのみ作成すること。scene_006 以降は作成しない。

## 進捗
- [x] フォルダ作成
- [x] シナリオ作成
- [x] HTML修正
- [x] 画像生成
- [x] 中間確認
- [x] 音声生成
- [x] 再生時間更新
- [x] 完成
