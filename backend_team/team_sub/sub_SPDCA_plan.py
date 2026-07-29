# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""目標ループ（S → P → D → C → A）の P（計画）を投入するサブプロセス。

直前のS（相談）が全件「済」または「エラー」になった後、Sの「済」レコードに
保存されたまとめ内容を1つの実行計画へ取りまとめる。担当は、成功したSを作った要員から
ランダムに1名選ぶ。全Sがエラーの場合はS参加者から選び、目標を基に計画を作らせる。
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
from team_proc import team_pdca_db

# 前段の完了確認、Aチーム作業・Aチーム改善の作成とタスク投入は全区分で同じ処理を使う
import sub_SPDCA__common


def 計画要員を選ぶ(S一覧: list[dict], 成功一覧: list[dict]) -> str:
    """成功したSの作成者、全件エラーならS参加者から担当をランダムに選ぶ。"""
    対象 = 成功一覧 or S一覧
    候補 = sorted({str(row.get("要員ID", "")).strip() for row in 対象 if str(row.get("要員ID", "")).strip()})
    if not 候補:
        raise RuntimeError("計画を担当できるS参加要員がありません")
    return random.choice(候補)


def 単一相談を計画へ引き継ぐ(Sレコード: dict, logger) -> bool:
    """成功Sが1件なら、その内容を完了済みPへupsertしてAIタスクを省略する。"""
    Pレコード = team_pdca_db.単一計画upsert(Sレコード)
    改善ID = str(Pレコード.get("改善ID", ""))
    if not 改善ID:
        raise RuntimeError("単一相談からPへのupsertに失敗しました")
    logger.info(
        f"目標ループ(P)は単一相談を直接引き継ぎました: 改善ID={改善ID} "
        f"プロジェクト={Pレコード.get('プロジェクト', '')} "
        f"ループ={Pレコード.get('ループ', '')} 要員ID={Pレコード.get('要員ID', '')}"
    )
    return True


def プロンプト生成_計画(
    要員ID: str,
    プロジェクト: str,
    チーム目標: str,
    成功一覧: list[dict],
) -> str:
    if 成功一覧:
        相談内容 = "\n\n".join(
            f"### 相談 {番号}（要員: {row.get('要員ID', '')}）\n"
            f"{str(row.get('まとめ内容', '')).strip() or '（まとめ内容なし）'}"
            for 番号, row in enumerate(reversed(成功一覧), start=1)
        )
    else:
        相談内容 = "S（相談）は全件エラーとなり、利用できるまとめ内容はありません。チーム目標とプロジェクトの現状から計画してください。"

    return f"""AIチーム改善のP（計画）として、相談結果を1つの実行計画へ取りまとめてください。

担当要員: {要員ID}
プロジェクト: {プロジェクト}
チーム目標: {チーム目標}

## S（相談）で得られたまとめ内容

{相談内容}

## 作成する計画

- 複数の相談内容を比較し、共通点・相違点・優先順位を整理する
- チーム目標へ最も効果が高い取り組みを選び、実施順序を決める
- 各ステップについて「目的」「対象」「具体的な作業」「完了条件」「注意点」を明記する
- 後続のD（実行）がそのまま着手できる具体性を持たせる

## 厳守事項: この段階では調査と計画づくりだけを行うこと

ここは計画（P）の段で、実行（D）は後の段です。計画の裏付けを取るための
ファイル読み取り、検索、ログ確認などの**調査は自由に行ってよい**が、
次の操作は理由を問わず**一切行わないこと**。

- ソースコード・設定ファイル・ドキュメントの作成、編集、削除、リネーム
- ビルド、テスト実行、インストール、デプロイ、サーバーの起動や停止
- git のコミット、ブランチ操作、その他リポジトリの状態を変える操作
- 環境やデータベースを変更するコマンドの実行

「小さな修正だから」「ついでに直せるから」という判断も不可です。
実施すべき変更は、着手せずに計画のステップとして文章で書いてください。
"""


def 計画を投入(
    要員ID: str,
    プロジェクト: str,
    チーム目標: str,
    ループ: int,
    成功一覧: list[dict],
    logger,
) -> bool:
    """Pは相談の成功レコード全件を計画材料にするため、まとめ内容の連結を自前で作る。"""
    return sub_SPDCA__common.段を投入(
        "P",
        要員ID,
        プロジェクト,
        チーム目標,
        ループ,
        プロンプト生成_計画(要員ID, プロジェクト, チーム目標, 成功一覧),
        logger,
    )


def main() -> int:
    setup_logging("sub_SPDCA_plan")
    logger = get_logger("team_sub_SPDCA_plan")
    プロジェクト = ""
    チーム目標 = ""
    try:
        if len(sys.argv) < 2:
            raise ValueError("使い方: python sub_SPDCA_plan.py <temp/pdca/入力JSON>")
        入力パス = Path(sys.argv[1]).resolve()
        with 入力パス.open("r", encoding="utf-8-sig") as f:
            項目 = json.load(f)
        プロジェクト = str(項目.get("プロジェクト", "")).strip()
        チーム目標 = str(項目.get("チーム目標", "")).strip()
        区分 = str(項目.get("PDCA区分", "")).strip() or "P"
        if not プロジェクト or not チーム目標 or 区分 != "P":
            raise ValueError("入力JSONにPのプロジェクトとチーム目標がありません")

        # Sの完了確認はD・C・Aと同じ共通処理を使う（成功が複数ある点だけPの扱いが違う）
        ループ, S一覧, 成功一覧 = sub_SPDCA__common.前段結果を取得(プロジェクト, "S")
        if len(成功一覧) == 1:
            return 0 if 単一相談を計画へ引き継ぐ(成功一覧[0], logger) else 1
        要員ID = 計画要員を選ぶ(S一覧, 成功一覧)
        logger.info(
            f"目標ループ(P)を開始します: プロジェクト={プロジェクト} "
            f"ループ={ループ} 要員ID={要員ID} 相談結果={len(成功一覧)}件"
        )
        return 0 if 計画を投入(
            要員ID, プロジェクト, チーム目標, ループ, 成功一覧, logger
        ) else 1
    except Exception as exc:
        logger.exception("目標ループ(P)の投入処理に失敗しました")
        sub_SPDCA__common.投入失敗を記録(
            "P", プロジェクト, チーム目標, f"投入処理エラー: {exc}", logger
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
