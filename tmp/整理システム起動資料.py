from pathlib import Path
import re
import shutil
from PIL import Image

root = Path('C:/Users/admin/Desktop/AiDiy2026_dev')
knowledge = root / '_AIDIY/knowledge'
book = 'セルフテスト,aidiy_diag,システム起動編'
document = knowledge / (book + '.md')
folder = knowledge / 'images' / book
source = document.read_text(encoding='utf-8')

# 今回取得した実画面をPNGにし、説明資料の上限へそろえる。
for original in folder.glob('20261019-taskteam-pulse__*.jpg'):
    target = original.with_suffix('.png')
    if target.exists():
        raise RuntimeError('画像は上書きしません: ' + str(target))
    with Image.open(original) as raw:
        image = raw.convert('RGB')
        image.thumbnail((960, 960), Image.Resampling.LANCZOS)
        image.save(target)
    with Image.open(target) as check:
        check.verify()
    original.unlink()
for original in folder.glob('20261019-taskteam-pulse__*.png'):
    with Image.open(original) as raw:
        if max(raw.size) > 960:
            image = raw.convert('RGB')
            image.thumbnail((960, 960), Image.Resampling.LANCZOS)
            image.save(original)

sections = re.split(r'(?m)^## (?=\d+\. )', source)
intro = sections[0]
old = {int(part.split('.', 1)[0]): '## ' + part for part in sections[1:]}

def figure(number, caption, alt):
    files = list(folder.glob(f'20261019-taskteam-pulse__aidiy_diag-システム起動_{number}_*.png'))
    if len(files) != 1:
        raise RuntimeError(f'画像{number}: {files}')
    return f'{caption}\n\n![{alt}](./images/{book}/{files[0].name})\n\n'

intro = intro.replace('起動・停止・ログコピー・ミニ表示を確認しました。', '設定起動・Webの手動表示・赤／緑の状態表示・停止・ログコピーを確認しました。')
intro = intro.replace('個別停止と復帰、選択ログとクリップボードの一致、約5秒更新、通常・ミニの長押し移動、透明領域内の開始ズームを確認しました。', 'Task / Teamの手動停止・復帰、Webの手動表示、強制停止と設定起動の切り替え、選択ログのコピー、ミニ表示を確認しました。')
intro = intro.replace('1章から順に起動・状態確認・停止を試します。', '1章から順に、起動、Web表示、状態確認、ログ、停止を試します。')
intro = intro.replace('停止操作は **5章**', '停止操作は **6章**')
intro = intro.replace('PDF版は本文に合わせて再生成し、全ページの日本語・表・画像・改ページを目視確認しました。', 'PDF版は本文に合わせて再生成し、全ページの日本語・表・画像・改ページを目視確認しました。\n\n操作の流れは、**1章：開く → 2章：設定起動 → 3章：Webを手動で開く → 4章：状態・ミニ表示 → 5章：ログ → 6章：停止・終了**です。実画面はWindowsのComputer Useで操作し、Web表示先はChrome MCPでも照合しました。今回の追加試験は2026年10月19日21時台に実施し、修正後の最終結果だけを掲載しています。')

chapter2 = '''## 2. 設定起動でシステムを起動する

### 操作手順

1. 6章の停止操作で全機能を止めてから、「システム起動」を開きます。1つでも稼働中なら右上は「強制停止」、全停止後は「設定起動」になります。
2. Tools / MCP、Core、Apps、Task / Team、Webの「起動対象」をオンにし、Localはオフにします。変更は自動保存されます。
3. Webの「ブラウザで開く」をオンにします。自動表示にもTools / MCPが必要です。
4. 「設定起動」を1回押します。通常表示のまま、Tools → Core → Apps → Task / Team → Webへタブとコンソールが追従します。
5. 「起動処理が完了しました」と5機能の緑の状態表示を確認します。WebはHTTP応答が20秒間安定してからChromeで開きます。
6. ミニ表示を使いたい場合だけ、自分で「ミニ表示」を押します。設定起動から自動でミニ表示へは変わりません。

| 機能 | 役割 | ポート（参考） | 起動対象 |
|---|---|---|---|
| Local | PC内のAIモデル | 8096 | オフ |
| Tools / MCP | AIやアプリの共通の道具 | 8095 | オン |
| Core | 認証・AI会話の共通処理 | 8091 | オン |
| Apps | 業務画面の処理 | 8098 | オン |
| Task / Team | AIへの作業依頼 | 8093 | オン |
| Web | ブラウザで使う画面 | 8090 | オン |

### 成功の見分け方と今回の結果

**✅ OK**：全停止から設定起動し、通常表示を維持したまま5機能が順番に起動しました。起動待ちの対象は赤く脈動し、ポートが開くと緑へ変わりました。Webの20秒間の安定確認とChromeでの表示、起動完了まで確認しました。Localの実起動は対象外です。

'''
chapter2 += figure('804', '設定起動の直後です。通常表示のままToolsのコンソールへ移り、起動対象の未開放ポートは赤く表示されています。', '設定起動後も通常表示を維持')
chapter2 += figure('805', '起動がWebまで進みました。タブがWebへ追従し、HTTP応答の20秒間の安定確認が行われています。', 'Webへタブが追従して安定確認')
chapter2 += figure('806', '5機能が起動した最終画面です。Webは稼働中となり、画面下に起動完了が表示されています。', '5機能の設定起動完了')

chapter3 = '''## 3. Webを手動で開く

### 操作手順

1. Tools / MCPとWebが起動していることを確認し、「Web」タブを選びます。
2. 「ブラウザで開く」のすぐ右にある「手動で開く」を押します。
3. 「ブラウザで http://localhost:8090/ を開きました。」を確認します。ChromeにWebの画面が開きます。

この操作はブラウザを開くだけです。サービスの起動・再起動は行いません。「ブラウザで開く」のチェックがオフでも使えます。Tools / MCPまたはWebが停止中・未確認なら、ボタンは押せません。

### 成功の見分け方と今回の結果

| ケース | 確認したこと | 結果 |
|---|---|---|
| WEB-01 | ボタンがチェック欄の右にある | ✅ OK：実Electronで確認しました。 |
| WEB-02 | 自動表示をオフにして手動で開く | ✅ OK：実操作で成功通知が出て、localhost:8090の新しいタブを確認しました。 |
| WEB-03 | 実際に開いたWeb画面 | ✅ OK：Chrome MCPで表示先とログイン画面を照合しました。ログインはこの試験の対象外です。 |
| WEB-04 | 停止中の押下を防ぐ | ✅ OK：実機の全停止時に無効でした。片方だけ停止・未確認の条件も合成サービスの自動試験で確認しました。 |

'''
chapter3 += figure('701', 'Webタブの設定欄です。「ブラウザで開く」の右に「手動で開く」があります。ToolsとWebのポートが開いているため有効です。', 'Webの手動表示ボタン')
chapter3 += figure('702', '自動表示のチェックをオフにして手動ボタンを押しました。チェックがオフのまま、localhost:8090を開いた成功通知が出ています。', 'チェックをオフにしてもWeb手動表示に成功')
chapter3 += figure('703', '手動操作で新しく開いたWeb画面です。Chrome MCPでlocalhost:8090のタブと一致することを確認しました。', '手動表示したWebのログイン画面')
chapter3 += figure('704', 'ToolsとWebを停止した画面です。「手動で開く」は無効になり、停止中のWebを起動する操作にはなりません。試験後、自動表示のチェックは元のオンへ戻しました。', '停止中はWebの手動表示を無効化')

chapter4 = old[3].replace('## 3. ミニパネルでサーバー状態を見る', '## 4. 状態とミニ表示を確認する')
chapter4 = chapter4.replace('緑は通信窓口が開いている状態、灰色は閉じているか、確認できない状態です。', '緑の脈動は通信窓口が開いている状態です。ほかが稼働中、または設定起動中に、起動対象の通信窓口が閉じていると赤く脈動します。起動対象外と、最初から未確認の項目は灰色です。全停止後は赤い脈動を止め、通常表示で選択した未起動タブの下線は注意色の橙色になります。')
chapter4 = chapter4.replace('![3章: ミニパネルのサーバー状態](./images/' + book + '/aidiy_diag-システム起動_301_ミニパネル表示画面.png)', re.search(r'!\[.*?\]\(.*?\)', figure('807', '', '手動でミニ表示へ切り替えた5機能の状態')).group())
chapter4 += '''### Task / Teamの手動停止と復帰

2026年10月19日・Windowsの実ElectronをComputer Useで操作しました。この個別試験ではTools / MCPとWebを稼働させ、Task / Teamの「起動対象」と「自動再起動」をオンにしました。Core・Apps・Localはこの個別試験の起動条件に含めていません。

1. Task / Teamを起動し、通常表示とミニ表示で緑を確認します。
2. 通常表示で「Task / Team」を選び、「停止（Ctrl+C）」を押します。
3. 「停止済み」と赤い下線を確認し、自分でミニ表示へ切り替えて赤い脈動を確認します。
4. 「Task / Team」からコンソールへ戻り、「再起動」を押します。ポートが開き、通常表示・ミニ表示が緑へ戻ることを確認します。

**✅ OK**：Task / Teamのポート8093が開放 → 未開放 → 開放へ変わり、両表示で緑 → 赤 → 緑になりました。明示停止後は自動再起動オンでも停止を維持しました。Tools / MCPとWebは稼働を維持しています。ミニ表示は約5秒ごとの確認に合わせて変わります。内部再起動の一時的なポート閉鎖も同じ表示判定です。

'''
chapter4 += figure('602', '停止前の通常表示です。Task / Teamは稼働中で、起動対象にチェックが入り、緑の下線になっています。', 'Task / Team稼働中の通常表示')
chapter4 += figure('603', 'Task / Teamだけを手動停止しました。状態は停止済み、下線と丸印は赤です。ToolsとWebは緑のままです。', '手動停止後のTask / Teamは赤')
chapter4 += figure('604', '停止したままミニ表示へ切り替えた1時点目です。Task/Teamは赤で、ToolsとWebは緑です。', '停止中ミニ表示の脈動1')
chapter4 += figure('605', '同じ停止状態を別時点で撮影しました。Task/Teamの明るさが変わり、赤い脈動が続いていることを確認しました。', '停止中ミニ表示の脈動2')
chapter4 += figure('606', 'Task / Teamを再起動した最終画面です。稼働中となり、赤から緑の下線へ戻りました。', '再起動後のTask / Teamは緑')
chapter4 += figure('607', '復帰後に自分でミニ表示へ切り替えました。Task/Teamは再び緑になっています。', '復帰後のミニ表示も緑')

chapter5 = old[4].replace('## 4. ログを読む・コピーする', '## 5. ログを読む・コピーする')
chapter6 = old[5].replace('## 5. 停止・終了する', '## 6. 停止・終了する')
start = chapter6.index('### 全停止からの再始動も確認')
end = chapter6.index('### Electron起動時のコマンド画面も確認')
chapter6 = chapter6[:start] + chapter6[end:]
chapter6 = chapter6.replace('停止要求から5秒で通常終了しなかったため、既定の残存プロセス回収へ進み、ポート8098は閉じました。', 'ポート8098が閉じたことも確認しました。')
bulk = '''### Diagを開いたまま一括停止する

1. 1つでも稼働中なら、右上の「強制停止」を押します。
2. 停止中はボタンが無効になります。稼働中の機能をWeb → Task / Team → Apps → Core → Tools / MCP → Localの逆順で停止し、停止済みは飛ばします。起動対象のチェックを外した機能でも、稼働中なら停止対象です。
3. 全停止後、「設定起動」へ戻ったことを確認します。必要なら2章から再び起動できます。

**✅ OK（実機）**：稼働中だったWeb → Task / Team → Tools / MCPの順に停止しました。停止済みのCore・Apps・Localは飛ばし、3ポートがこの順に閉じたことも照合しました。管理外で起動したWeb・Toolsも停止し、自動復活しませんでした。全停止後は「設定起動」が有効になり、選択中タブの下線が橙色へ戻りました。その後の5機能の設定起動も2章のとおり完了しました。

**✅ OK（合成サービス）**：6機能すべての逆順停止、起動途中の後続取り消し、連打防止、1件の停止失敗後も残りを続けることを自動試験で確認しました。関連試験はNode.js 36件・Python 3件が成功し、実ブラウザの画面試験も通過しました。Localの実起動成功を意味する結果ではありません。

'''
bulk += figure('801', 'Web・Task / Team・Toolsが稼働中の画面です。右上は起動操作ではなく「強制停止」になっています。', '稼働中は強制停止へ切り替え')
bulk += figure('802', '一括停止を受け付けた画面です。最初はWebのコンソールに移り、右上は停止中となって連打を防いでいます。', 'Webから逆順の一括停止を開始')
bulk += figure('803', 'すべての停止が完了しました。「設定起動」が有効になり、選択中のToolsタブは橙色の下線になっています。', '全停止後は設定起動と橙色の下線')
chapter6 = chapter6.replace('### 操作手順\n', bulk + '### 個別停止とDiag終了の操作手順\n', 1)
chapter7 = old[6].replace('## 6. 試験担当者向け：次回の記録方法', '## 7. 試験の記録方法')
chapter7 = chapter7.replace('後ろ2桁は章内の連番です。', '後ろ2桁は章内の連番です。操作説明に合わせて章を並べ替えた場合は、採用画像のファイル名・代替テキスト・本文の参照も一緒に更新します。')

final = intro + old[1] + chapter2 + chapter3 + chapter4 + chapter5 + chapter6 + chapter7

# 採用画像だけを、操作順にした章番号と章内連番へ一括整理する。
image_re = re.compile(r'!\[([^\]]*)\]\(\./images/' + re.escape(book) + r'/([^\)]+)\)')
other_documents = {p: p.read_text(encoding='utf-8') for p in knowledge.glob('*.md') if p != document}
mapping = []
chapter = 0
counts = {}
lines = []
for line in final.splitlines(keepends=True):
    heading = re.match(r'## (\d+)\. ', line)
    if heading:
        chapter = int(heading.group(1))
    def replace_image(match):
        counts[chapter] = counts.get(chapter, 0) + 1
        filename = match.group(2)
        original = folder / filename
        if not original.is_file():
            raise RuntimeError('画像がありません: ' + str(original))
        description = re.sub(r'^.*?aidiy_diag-システム起動_\d{3}_', '', original.stem)
        target = folder / f'20261019-system-final__aidiy_diag-システム起動_{chapter}{counts[chapter]:02d}_{description}.png'
        if target.exists():
            raise RuntimeError('整理先は上書きしません: ' + str(target))
        mapping.append((original, target))
        alt = re.sub(r'^\d+章\s*[:：]\s*', '', match.group(1))
        return f'![{chapter}章：{alt}](./images/{book}/{target.name})'
    lines.append(image_re.sub(replace_image, line))
final = ''.join(lines)

for original, target in mapping:
    assert original.resolve().parent == folder.resolve() == target.resolve().parent
    if any(original.name in text for text in other_documents.values()):
        shutil.copy2(original, target)
    else:
        original.rename(target)
document.write_text(final, encoding='utf-8', newline='\n')
print('章別採用画像数:', counts)
print('採用画像数:', len(mapping))
print('更新文書:', document)
