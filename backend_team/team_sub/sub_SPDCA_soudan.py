# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""改善ループ（S → P → D → C → A）の S（相談）を投入するサブプロセス。

S は計画（P）を立てる前の意見交換で、複数名が並行してそれぞれの意見を出す段です。
ここで出た意見を次の P（計画）で 1 つの計画にまとめます。

team_watcher.py（1分ごとの確認）が temp/pdca/<ファイル名>.json に入力値を書き、
このスクリプトを `python sub_pdca_soudan.py <入力JSONパス>` で起動する。

処理の流れ:
1. 入力 JSON（プロジェクト / チーム目標 / PDCA区分 / 最大ループ回数 / 動員要員数）を読み込む
2. 有効な要員のうち admin 以外から指定された動員要員数までランダムに選ぶ（1名もいなければ admin）
3. 要員ごとに Aチーム作業（状態=準備中）→ Aチーム改善（開始レコード）→
   aidiy_task_agents への投入（Aタスク要求）の順で作る
4. 投入に成功した作業は 準備完了 にする。失敗した作業はエラーにし、
   対応する Aチーム改善レコードも終了させて次のサイクルを止めない

担当要員は既に決まっているため、sub_init.py のような AI による担当選択は行わない。
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

_TEAM_SUB_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_TEAM_SUB_DIR.parent))
sys.path.insert(0, str(_TEAM_SUB_DIR))

from log_config import get_logger, setup_logging
from team_proc import team_db, team_pdca_db

# Aチーム作業・Aチーム改善の作成とタスク投入は全区分で同じ処理を使う
import sub_pdca__common

既定利用者ID = "admin"
既定動員要員数 = 2
# Aチーム目標の動員要員数はここで固定の人数に丸めない。
# 実際に動員できるのは admin 以外の有効要員数までなので、それを上限にする。
動員要員数上限 = 99


def 相談要員を選ぶ(logger, 動員要員数: int = 既定動員要員数) -> list[str]:
    """有効な要員のうちadmin以外から、Aチーム目標の動員要員数までランダムに選ぶ。

    動員要員数がadmin以外の有効要員数を超える場合は、その全員が上限になる。
    admin以外が1名もいなければadmin 1名。
    """
    指定人数 = max(1, min(動員要員数上限, int(動員要員数)))
    候補 = [
        str(要員["要員ID"])
        for 要員 in team_db.要員一覧()
        if str(要員["要員ID"]) != team_db.管理者要員ID
    ]
    if not 候補:
        logger.warning(f"admin以外の有効な要員がいないため{既定利用者ID}へ投入します")
        return [既定利用者ID]
    if 指定人数 > len(候補):
        logger.info(
            f"動員要員数({指定人数})が有効要員数({len(候補)})を超えるため全員を動員します"
        )
    return random.sample(候補, min(指定人数, len(候補)))


def 次ループ番号(プロジェクト: str, 最大ループ回数: int) -> int:
    """Sを投入可能なら最大値+1、上限到達済みなら0を返す（99は無制限）。"""
    現在ループ最大値 = team_pdca_db.ループ最大値(プロジェクト)
    if 最大ループ回数 != 99 and 現在ループ最大値 >= 最大ループ回数:
        return 0
    return 現在ループ最大値 + 1


def 前サイクルの改善内容(プロジェクト: str, ループ: int) -> str:
    """1つ前のループのA（改善）でまとめられた内容を返す（初回や未完了なら空文字）。

    2周目以降は、前サイクルのAで洗い出した改善点を出発点にして議論を続ける。
    """
    if ループ <= 1:
        return ""
    A一覧 = team_pdca_db.ループ区分一覧(プロジェクト, ループ - 1, "A")
    成功一覧 = [row for row in A一覧 if str(row.get("状況", "")) == "済"]
    if not 成功一覧:
        return ""
    return sub_pdca__common.まとめ内容(sub_pdca__common.最新の成功記録(成功一覧))


def プロンプト生成_相談(
    要員ID: str,
    プロジェクト: str,
    チーム目標: str,
    人数: int,
    前サイクル改善: str = "",
) -> str:
    引き継ぎ = ""
    if 前サイクル改善:
        引き継ぎ = f"""
## 前サイクルのA（改善）で洗い出された改善点

{前サイクル改善}

この内容を出発点にしてください。ゼロから考え直すのではなく、前サイクルで残った改善点や
申し送りのうち、いま取り組む価値が高いものを見極めて意見を出してください。
すでに解消済みの項目があれば現状を確認したうえでその旨を述べ、新たに気づいた論点があれば足してください。
"""

    return f"""あなたはAIチームの要員「{要員ID}」です。チーム目標に向けて、いま何に取り組むべきかの意見を出してください。

プロジェクト: {プロジェクト}
チーム目標: {チーム目標}

これは計画を立てる前の意見交換（相談）です。{人数}名がそれぞれ別の観点から意見を出し、
この後の「計画」でそれらを1つの計画にまとめます。結論を1つに決めるのはあなたの役割ではありません。
{引き継ぎ}
進め方:
- 対象プロジェクトの現状（コード・ドキュメント・設定）を調べる
- 目標に近づくうえで効果が高いと考える取り組みを 1〜3 件挙げる
- それぞれ「対象」「現状の課題」「取り組み案」「想定効果」「気になる点・懸念」を簡潔にまとめて回答する

## 厳守事項: この段階では調査と意見出しだけを行うこと

計画（P）を立てる前の事前相談です。実行（D）は後の段になります。
ファイルの読み取り、検索、ログ確認などの**調査は自由に行ってよい**が、
次の操作は理由を問わず**一切行わないこと**。

- ソースコード・設定ファイル・ドキュメントの作成、編集、削除、リネーム
- ビルド、テスト実行、インストール、デプロイ、サーバーの起動や停止
- git のコミット、ブランチ操作、その他リポジトリの状態を変える操作
- 環境やデータベースを変更するコマンドの実行

「小さな修正だから」「ついでに直せるから」という判断も不可です。
直すべきと考えた内容は、実施せずに意見として文章で書いてください。

その他:
- 他の要員も同時に意見を出しています。あなたの役割と経験を活かした観点で、重複しにくい意見を出すこと
"""


def 相談を投入(
    要員ID: str,
    プロジェクト: str,
    チーム目標: str,
    区分: str,
    ループ: int,
    人数: int,
    logger,
    前サイクル改善: str = "",
) -> bool:
    """要員1名分の Aチーム作業・Aチーム改善・Aタスク要求を作る。"""
    return sub_pdca__common.段を投入(
        区分,
        要員ID,
        プロジェクト,
        チーム目標,
        ループ,
        プロンプト生成_相談(要員ID, プロジェクト, チーム目標, 人数, 前サイクル改善),
        logger,
    )


def main() -> int:
    setup_logging("sub_pdca_soudan")
    logger = get_logger("team_sub_pdca_soudan")
    プロジェクト = ""
    チーム目標 = ""
    区分 = "S"
    try:
        if len(sys.argv) < 2:
            raise ValueError("使い方: python sub_pdca_soudan.py <temp/pdca/入力JSON>")
        入力パス = Path(sys.argv[1]).resolve()
        with 入力パス.open("r", encoding="utf-8-sig") as f:
            項目 = json.load(f)
        プロジェクト = str(項目.get("プロジェクト", "")).strip()
        チーム目標 = str(項目.get("チーム目標", "")).strip()
        区分 = str(項目.get("PDCA区分", "")).strip() or "S"
        最大ループ回数 = max(1, min(99, int(項目.get("最大ループ回数", 1) or 1)))
        動員要員数 = max(
            1,
            min(動員要員数上限, int(項目.get("動員要員数", 既定動員要員数) or 既定動員要員数)),
        )
        if not プロジェクト or not チーム目標:
            raise ValueError("入力JSONにプロジェクトとチーム目標がありません")

        ループ = 次ループ番号(プロジェクト, 最大ループ回数)
        if not ループ:
            logger.info(
                f"改善ループ(S)は最大回数到達のため投入しません: プロジェクト={プロジェクト} "
                f"現在={team_pdca_db.ループ最大値(プロジェクト)} 最大={最大ループ回数}"
            )
            return 0

        要員一覧 = 相談要員を選ぶ(logger, 動員要員数)
        # 2周目以降は前サイクルのAで洗い出した改善点を引き継いで議論を続ける
        前サイクル改善 = 前サイクルの改善内容(プロジェクト, ループ)
        logger.info(
            f"改善ループ({区分})を開始します: プロジェクト={プロジェクト} "
            f"ループ={ループ} 要員={','.join(要員一覧)} "
            f"前サイクル改善={'あり' if 前サイクル改善 else 'なし'}"
        )
        成功数 = 0
        for 要員ID in 要員一覧:
            try:
                if 相談を投入(
                    要員ID, プロジェクト, チーム目標, 区分, ループ, len(要員一覧), logger,
                    前サイクル改善,
                ):
                    成功数 += 1
            except Exception:
                logger.exception(f"改善ループ({区分})の作成に失敗しました: 要員ID={要員ID}")
        logger.info(f"改善ループ({区分})の投入を終えました: 成功 {成功数}/{len(要員一覧)} 件")
        if not 成功数 and not team_pdca_db.ループ区分一覧(プロジェクト, ループ, 区分):
            # 1件もレコードを作れていないと、次の分にまた同じ段が投入されて堂々巡りになる
            sub_pdca__common.実行不能を記録(
                区分, プロジェクト, チーム目標, ループ,
                f"{len(要員一覧)}名すべての投入に失敗しました", logger,
            )
        return 0 if 成功数 else 1
    except Exception as exc:
        logger.exception("改善ループの投入処理に失敗しました")
        sub_pdca__common.投入失敗を記録(
            区分, プロジェクト, チーム目標, f"投入処理エラー: {exc}", logger
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
