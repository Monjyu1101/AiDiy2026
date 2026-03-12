# Electron 起動不具合対応メモ

> 作成日: 2026-03-12

---

## 不具合の症状

- `_cleanup.py` → `_setup.py` → `_start.py` の順に実行すると、  
  Avatar（Electron）のログイン画面が表示されない。
- `_start.py` を Ctrl+C で停止しても、Electron ウィンドウが残る。  
  その後 `_start.py` を再実行すると二重起動になる場合がある。

---

## 原因①：`dist-electron/` が再生成されない

| タイミング | 状態 |
|-----------|------|
| `_cleanup.py` 実行後 | `node_modules/` と `dist-electron/` が削除される |
| `_setup.py` 実行後 | `node_modules/` は復元される。**`dist-electron/` は再生成されない** |
| `_start.py` で `npm run dev` 起動 | `tsc --watch` が `dist-electron/main.js` をビルドするまで Electron が起動しない |

`npm run dev` の内部構造（`package.json` の `scripts`）:

```
dev
├── dev:renderer  → vite (ポート 8099)
└── dev:electron
    ├── dev:main  → tsc -p tsconfig.electron.json --watch  ← dist-electron/ を生成
    └── dev:run   → wait-on (Vite + dist-electron/main.js) → electronmon dist-electron/main.js
```

`wait-on` は Vite **かつ** `dist-electron/main.js` の両方が揃うまで Electron を起動しない。  
`dist-electron/main.js` がなければ、`tsc --watch` が初回コンパイルを完了するまで待たされる。

**初回コンパイルが遅い・失敗した場合 → Electron が起動しない。**

### 対処（`_setup.py` に追加）

```python
# Step4: TypeScript 事前ビルド
run_command([npm_command(), "run", "build:electron"], cwd=FRONTEND_AVATAR_DIR)
```

セットアップ時に `npm run build:electron`（= `tsc -p tsconfig.electron.json`）を実行し、  
`dist-electron/main.js` を事前生成するようにした。

---

## 原因②：`electron.exe` が停止時に残留する

`_start.py` の `stop_processes()` は `taskkill /F /T /PID <npm_pid>` で  
`npm` → `concurrently` → `electronmon` と子プロセスを再帰的に終了する。

しかし `electronmon` が spawn した `electron.exe` は  
**別のプロセスグループ**として動くため、`/T` ツリーキルに含まれないことがある。

結果として `electron.exe` がゾンビとして残留し、  
次回起動時に `electronmon` が二重起動した Electron を制御できない状態になる。

### 対処（`_start.py` に追加）

```python
def kill_electron_processes() -> None:
    """このプロジェクトの electron.exe を WMIC で特定して強制終了する"""
    # WMIC で ExecutablePath を確認し、frontend_avatar/node_modules/electron/dist/electron.exe に
    # 一致するプロセスだけを taskkill する（無関係な Electron アプリを誤殺しない）
```

呼び出しタイミング：
1. **起動前**（`maybe_kill_initial_ports` の `avatar_enabled` ブロック）
2. **停止後**（`stop_processes` の末尾、Avatar が起動していた場合）

---

## ホットリロードについて

`npm run dev` は `electronmon` を使用しているため、  
`dist-electron/main.js`（= `electron/main.ts` のコンパイル結果）が更新されると  
Electron が自動で再起動される（ホットリロード）。

Vue コンポーネント（`src/**`）の変更は Vite の HMR で即時反映される。

**`_start.py` から `npm run dev` で起動している限り、ホットリロードは維持される。**

---

---

## 原因③：Vite 初回依存関係最適化によるリロード（2026-03-12 追記）

`cleanup` 後の `npm run dev` 初回実行時、Vite が重いパッケージを pre-bundle（事前最適化）する。
これが完了するまで **約 3〜5 分** かかる。

```
[dev:main] 16:11:33 - Found 0 errors. Watching for file changes.   ← tsc 完了
            ↓ ここから 5 分間、何も起きない
[dev:renderer] 16:16:25 [vite] ✨ new dependencies optimized: three, @pixiv/three-vrm, ...
[dev:renderer] 16:16:25 [vite] ✨ optimized dependencies changed. reloading   ← ここでリロード発生
```

対象パッケージ（重いもの）：

| パッケージ | サイズ |
|-----------|--------|
| `three` | ≈ 1.7 MB |
| `@pixiv/three-vrm` | 大 |
| `@pixiv/three-vrm-animation` | 大 |
| `monaco-editor` | 非常に大 |

**症状：**
- Electron ウィンドウは起動する（または起動直後に消える）
- Vite が最適化完了後に `reloading` を送信するため、ログイン画面がブランクになる
- ユーザーには「ログイン画面が出ない」と見える

**Electron がなぜ今度は表示されたか：**
最初の `npm run dev` で Vite が 16:16:25 に最適化完了。
その後に手動で `electronmon` を再実行したため、最適化済みの Vite に接続 → 即座に表示された。

### 対処（`_setup.py` に追加）

```python
# Step5: Vite 依存関係の事前最適化
run_command([npm_command(), "exec", "--", "vite", "optimize"], cwd=FRONTEND_AVATAR_DIR)
```

セットアップ時に `vite optimize` を実行し、`node_modules/.vite/deps/` への pre-bundle キャッシュを生成する。
次回 `npm run dev` 時は最適化済みキャッシュを再利用するため、即座にログイン画面が表示される。

---

## 原因⑤：`wait-on` が Vite に HEAD を投げて詰まっていた（2026-03-12 追記）

`frontend_avatar/package.json` の `dev:run` は次の待機条件だった。

```json
"dev:run": "wait-on http://127.0.0.1:8099 file:dist-electron/main.js && cross-env VITE_DEV_SERVER_URL=http://127.0.0.1:8099 electronmon dist-electron/main.js"
```

`wait-on` は `http://...` 指定時に **HTTP HEAD** を送る。
今回の Vite dev server ではこの HEAD 待機が安定せず、実測で `ECONNRESET` になり続けた。

```
waiting for 2 resources: http://127.0.0.1:8099, file:dist-electron/main.js
making HTTP(S) head request to  url:http://127.0.0.1:8099 ...
...
HTTP(S) error for http://127.0.0.1:8099 Error: read ECONNRESET
wait-on(...) Timed out waiting for: http://127.0.0.1:8099
```

そのため、`dist-electron/main.js` が存在していても `wait-on` が解除されず、
後段の `electronmon dist-electron/main.js` が**一度も実行されない**。
結果として Renderer は `http://127.0.0.1:8099` で開けるのに、`electron.exe` が起動しなかった。

`http-get://` への変更も試したが、`wait-on` からの短周期 GET では依然として `ECONNRESET` が混ざり、
安定待機条件として不十分だった。

### 対処（`frontend_avatar/package.json` を修正）

```json
"dev:run": "wait-on tcp:127.0.0.1:8099 file:dist-electron/main.js && cross-env VITE_DEV_SERVER_URL=http://127.0.0.1:8099 electronmon dist-electron/main.js"
```

HTTP 応答の健全性判定をやめ、**TCP ポートが listen 状態か**で待機する。
Renderer 起動判定としてはこれで十分で、`ECONNRESET` に影響されず安定して `electronmon` まで進める。

---

## 原因④：`vite optimize` の対象に重いパッケージが含まれていなかった（2026-03-12 追記）

`_setup.py` に `vite optimize --force` を追加したが、`axos`, `vue`, `monaco-editor` の 3 つしか
最適化されていなかった。`three`, `@pixiv/three-vrm`, `@pixiv/three-vrm-animation` は
`vite.config.ts` の `optimizeDeps.include` に含まれていなかったため、
`vite optimize` がスキャン対象外となり Vite deps キャッシュに入らなかった。

```
# 修正前：vite optimize --force の出力
Optimizing dependencies:
  axios, vue, monaco-editor   ← three 系がない！

# 修正後：vite optimize --force の出力
Optimizing dependencies:
  axios, vue, monaco-editor, three, @pixiv/three-vrm, @pixiv/three-vrm-animation
```

`npm run dev` 起動時、キャッシュにない `three` 等を Vite が発見 →
再最適化（3〜5 分） → `reloading` 送信 → Electron がブランク → 「ログイン画面が出ない」となっていた。

### 対処（`frontend_avatar/vite.config.ts` を修正）

```ts
optimizeDeps: {
  include: [
    'monaco-editor',
    'three',
    '@pixiv/three-vrm',
    '@pixiv/three-vrm-animation',
  ],
},
```

重いパッケージを `optimizeDeps.include` に明示追加することで、
`_setup.py` の `vite optimize --force` 実行時にこれらもキャッシュへ入る。
次回 `npm run dev` 起動時はキャッシュ済みのため再最適化が発生しない。

---

## 修正ファイルまとめ

| ファイル | 変更内容 |
|---------|---------|
| `_setup.py` | `setup_frontend_avatar()` に `npm run build:electron`（TypeScript 事前ビルド）を追加 |
| `_setup.py` | `setup_frontend_avatar()` に `vite optimize`（Vite 依存関係事前最適化）を追加 |
| `_start.py` | `kill_electron_processes()` 関数を追加。`maybe_kill_initial_ports`（起動前）と `stop_processes`（停止後）で呼ぶ |
| `frontend_avatar/vite.config.ts` | `optimizeDeps.include` に `three`, `@pixiv/three-vrm`, `@pixiv/three-vrm-animation` を追加 |
| `frontend_avatar/package.json` | `dev:run` の `wait-on` を HTTP待機から `tcp:127.0.0.1:8099` 待機へ変更 |

---

## 再発防止チェックリスト

- [ ] `_cleanup.py` で `dist-electron/` を削除する場合は、`_setup.py` を必ず再実行すること
- [ ] `_setup.py` の `setup_frontend_avatar()` が正常終了していることを確認（TypeScript ビルド + vite optimize 成功ログを確認）
- [ ] `vite optimize` の出力に `three, @pixiv/three-vrm, @pixiv/three-vrm-animation` が含まれていることを確認
- [ ] `npm run dev` 中に `wait-on` が `Timed out waiting for: http://127.0.0.1:8099` を出していないことを確認
- [ ] `_start.py` で Avatar を起動する前に「[Electron] 残留プロセスはありません」または「停止しました」が表示されることを確認
- [ ] Electron ログイン画面が表示されない場合は、`frontend_avatar/dist-electron/main.js` が存在するか確認
- [ ] Electron ログイン画面が表示されない場合は、`frontend_avatar/node_modules/.vite/deps/three.js` が存在するか確認（vite optimize の結果）

```powershell
# dist-electron の確認
Get-ChildItem c:\Users\kondo-mitsuo\AiDiy2026\frontend_avatar\dist-electron

# vite deps キャッシュに three が含まれているか確認
Test-Path "c:\Users\kondo-mitsuo\AiDiy2026\frontend_avatar\node_modules\.vite\deps\three.js"

# 残留 electron プロセスの確認
Get-Process electron -ErrorAction SilentlyContinue
```

---

## モジュールバージョン差分調査（2026-03-12）

### 【パターンA】npm install electron を手動実行した後の状態

記録日時: 2026-03-12 19:24 頃

#### npm list --depth=0

```
frontend-avatar@0.1.0
+-- @pixiv/three-vrm-animation@3.5.0
+-- @pixiv/three-vrm@3.5.0
+-- @types/node@25.4.0
+-- @types/three@0.183.1
+-- @vitejs/plugin-vue@6.0.4
+-- @vue/tsconfig@0.8.1
+-- axios@1.13.6
+-- concurrently@9.2.1
+-- cross-env@10.1.0
+-- electron@37.10.3
+-- electronmon@2.0.4
+-- monaco-editor@0.55.1
+-- three@0.179.1
+-- typescript@5.9.3
+-- vite@7.3.1
+-- vue-tsc@3.2.5
+-- vue@3.5.30
`-- wait-on@8.0.5
```

#### package.json の devDependencies (electron 行)

```json
"electron": "^37.10.3"
```

---

### 【パターンB】install_electron_binary() のみ実行後の状態

記録日時: 2026-03-12（`npm install electron` 実施後に `install_electron_binary()` のみ追加実行）

#### npm list --depth=0

```
frontend-avatar@0.1.0
+-- @pixiv/three-vrm-animation@3.5.0
+-- @pixiv/three-vrm@3.5.0
+-- @types/node@25.4.0
+-- @types/three@0.183.1
+-- @types/trusted-types@2.0.7  ★ extraneous
+-- @vitejs/plugin-vue@6.0.4
+-- @vue/tsconfig@0.8.1
+-- axios@1.13.6
+-- concurrently@9.2.1
+-- cross-env@10.1.0
+-- dompurify@3.2.7             ★ extraneous
+-- electron@37.10.3
+-- electronmon@2.0.4
+-- marked@14.0.0               ★ extraneous
+-- monaco-editor@ invalid: "^0.55.1"  ★ package.json が存在しない
+-- three@0.179.1
+-- typescript@5.9.3
+-- vite@7.3.1
+-- vue-tsc@3.2.5
+-- vue@3.5.30
`-- wait-on@8.0.5
（exit code 1）
```

---

### 差分メモ

| パッケージ | パターンA (npm install electron) | パターンB (binary only) | 差異 |
|-----------|-------------------------------|------------------------|------|
| monaco-editor | `0.55.1` ✅ | `invalid` ❌ package.json なし | **重大** |
| @types/trusted-types | なし | `2.0.7 extraneous` | 余分に存在 |
| dompurify | なし | `3.2.7 extraneous` | 余分に存在 |
| marked | なし | `14.0.0 extraneous` | 余分に存在 |
| exit code | 0 ✅ | 1 ❌ | |

---

### 原因分析

#### ① monaco-editor の package.json が消える問題

`node_modules/monaco-editor/` 配下にファイル群 (`dev/`, `esm/`, `min/`, `LICENSE`) は存在するが、
`package.json` だけが存在しない状態になっている。

**なぜ起きるか：**
`npm install electron` を実行すると、npm は electron を追加しつつ全パッケージを再解決する。
この過程で monaco-editor が「既にファイルがある＝インストール済み」と判断され、
package.json が欠落したままでも再インストールをスキップされる可能性がある。

`install_electron_binary()` は `node_modules/electron/dist/` しか触らないため、
monaco-editor 欠落の原因は binary インストール前（git からの checkout 時点）にある可能性が高い。

**結論：git から取得した時点で monaco-editor の package.json が gitignore 等により欠落している、
または `npm install --ignore-scripts` が正常に完了していない。**

#### ② extraneous パッケージ（dompurify / marked / @types/trusted-types）

これらは monaco-editor のオプション依存パッケージ（Markdown レンダリング等）。
`npm install electron` ではデフォルト install が走り重複排除でルートに残らないが、
`--ignore-scripts` や不完全 install 状態では node_modules ルートに残留する。

---

### 対処

**`_setup.py` の `setup_frontend_avatar()` Step3（`npm install` 再実行）が正しく走れば修復される。**

```
Step1: npm install --ignore-scripts   ← extraneous 残留の可能性あり
Step2: install_electron_binary()       ← binary 配置のみ
Step3: npm install                    ← ← ここで monaco-editor 再インストール・extraneous 除去
Step4: npm run build:electron
Step5: vite optimize --force
```

Step3 をスキップすると上記の差分状態が残る。
