# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101
# -------------------------------------------------------------------------

from typing import Optional, Dict

from sqlalchemy.orm import Session

import apps_models as models
import apps_schema as schemas
from apps_crud.utils import create_audit_fields, update_audit_fields


def get_M商品構成(db: Session, 商品ID: str):
    """商品IDで商品構成を取得"""
    return (
        db.query(models.M商品構成)
        .filter(models.M商品構成.商品ID == 商品ID)
        .order_by(models.M商品構成.明細番号)
        .all()
    )


def get_M商品構成一覧(db: Session):
    """全商品構成を取得"""
    return (
        db.query(models.M商品構成.商品ID)
        .distinct()
        .order_by(models.M商品構成.商品ID)
        .all()
    )


def get_M商品構成明細一覧(db: Session, 商品ID: str):
    """指定商品の構成明細を取得"""
    return (
        db.query(models.M商品構成)
        .filter(models.M商品構成.商品ID == 商品ID, models.M商品構成.明細番号 > 0)
        .order_by(models.M商品構成.明細番号)
        .all()
    )


def _build_明細一覧(db: Session, 明細一覧, 生産ロット: float):
    明細行一覧 = [item for item in 明細一覧 if item.明細番号 > 0]
    if not 明細行一覧:
        return []

    構成商品ID一覧 = list({item.構成商品ID for item in 明細行一覧 if item.構成商品ID})
    商品マップ = {
        item.商品ID: item
        for item in db.query(models.M商品).filter(models.M商品.商品ID.in_(構成商品ID一覧)).all()
    }

    result = []
    for item in 明細行一覧:
        構成商品 = 商品マップ.get(item.構成商品ID)
        構成数量 = 0.0
        if item.構成数量分母:
            構成数量 = float(item.構成数量分子) / float(item.構成数量分母) * float(生産ロット)

        result.append({
            "明細番号": item.明細番号,
            "構成商品ID": item.構成商品ID,
            "構成商品名": 構成商品.商品名 if 構成商品 else None,
            "構成数量分子": float(item.構成数量分子),
            "構成数量分母": float(item.構成数量分母),
            "構成数量": 構成数量,
            "構成単位": 構成商品.単位 if 構成商品 else None,
            "構成商品備考": item.構成商品備考,
        })

    return result


def build_M商品構成_data(db: Session, 商品構成一覧):
    """レスポンス用の商品構成データを組み立てる"""
    if not 商品構成一覧:
        return None

    見出し = next((item for item in 商品構成一覧 if item.明細番号 == 0), 商品構成一覧[0])
    商品 = db.query(models.M商品).filter(models.M商品.商品ID == 見出し.商品ID).first()

    return {
        "商品ID": 見出し.商品ID,
        "商品名": 商品.商品名 if 商品 else None,
        "単位": 商品.単位 if 商品 else None,
        "生産ロット": float(見出し.生産ロット),
        "商品構成備考": 見出し.商品構成備考,
        "有効": bool(見出し.有効),
        "明細一覧": _build_明細一覧(db, 商品構成一覧, 見出し.生産ロット),
        "登録日時": 見出し.登録日時,
        "登録利用者ID": 見出し.登録利用者ID,
        "登録利用者名": 見出し.登録利用者名,
        "登録端末ID": 見出し.登録端末ID,
        "更新日時": 見出し.更新日時,
        "更新利用者ID": 見出し.更新利用者ID,
        "更新利用者名": 見出し.更新利用者名,
        "更新端末ID": 見出し.更新端末ID,
    }


def _create_レコード一覧(
    db: Session,
    商品ID: str,
    生産ロット: float,
    商品構成備考: Optional[str],
    有効: bool,
    明細一覧: list[schemas.M商品構成明細Base],
    監査項目: Dict,
):
    db.add(
        models.M商品構成(
            商品ID=商品ID,
            明細番号=0,
            生産ロット=生産ロット,
            商品構成備考=商品構成備考,
            構成商品ID=None,
            構成数量分子=None,
            構成数量分母=None,
            構成商品備考=None,
            有効=有効,
            **監査項目,
        )
    )

    for 明細 in 明細一覧:
        db.add(
            models.M商品構成(
                商品ID=商品ID,
                明細番号=明細.明細番号,
                生産ロット=生産ロット,
                商品構成備考=商品構成備考,
                構成商品ID=明細.構成商品ID,
                構成数量分子=明細.構成数量分子,
                構成数量分母=明細.構成数量分母,
                構成商品備考=明細.構成商品備考,
                有効=有効,
                **監査項目,
            )
        )


def create_M商品構成(
    db: Session,
    商品構成: schemas.M商品構成Create,
    認証情報: Optional[Dict] = None,
):
    """商品構成を作成"""
    audit = create_audit_fields(認証情報)
    _create_レコード一覧(
        db,
        商品構成.商品ID,
        商品構成.生産ロット,
        商品構成.商品構成備考,
        商品構成.有効,
        商品構成.明細一覧,
        audit,
    )
    db.commit()
    return get_M商品構成(db, 商品構成.商品ID)


def update_M商品構成(
    db: Session,
    商品ID: str,
    商品構成: schemas.M商品構成Update,
    認証情報: Optional[Dict] = None,
):
    """商品構成を更新"""
    既存一覧 = get_M商品構成(db, 商品ID)
    if not 既存一覧:
        return None

    見出し = next((item for item in 既存一覧 if item.明細番号 == 0), 既存一覧[0])
    生産ロット = 商品構成.生産ロット if 商品構成.生産ロット is not None else 見出し.生産ロット
    商品構成備考 = 商品構成.商品構成備考 if 商品構成.商品構成備考 is not None else 見出し.商品構成備考
    有効 = 商品構成.有効 if 商品構成.有効 is not None else 見出し.有効
    明細一覧 = 商品構成.明細一覧 if 商品構成.明細一覧 is not None else [
        schemas.M商品構成明細Base(
            明細番号=item.明細番号,
            構成商品ID=item.構成商品ID,
            構成数量分子=item.構成数量分子,
            構成数量分母=item.構成数量分母,
            構成商品備考=item.構成商品備考,
        )
        for item in 既存一覧
        if item.明細番号 > 0
    ]

    監査項目 = {
        "登録日時": 見出し.登録日時,
        "登録利用者ID": 見出し.登録利用者ID,
        "登録利用者名": 見出し.登録利用者名,
        "登録端末ID": 見出し.登録端末ID,
        **update_audit_fields(認証情報),
    }

    db.query(models.M商品構成).filter(models.M商品構成.商品ID == 商品ID).delete(synchronize_session=False)
    db.flush()
    db.expunge_all()
    _create_レコード一覧(db, 商品ID, 生産ロット, 商品構成備考, 有効, 明細一覧, 監査項目)
    db.commit()
    return get_M商品構成(db, 商品ID)


def delete_M商品構成(db: Session, 商品ID: str, 認証情報: Optional[Dict] = None):
    """商品構成を無効化"""
    db_商品構成一覧 = get_M商品構成(db, 商品ID)
    if not db_商品構成一覧:
        return None

    audit = update_audit_fields(認証情報)
    for item in db_商品構成一覧:
        item.有効 = False
        for key, value in audit.items():
            setattr(item, key, value)

    db.commit()
    return get_M商品構成(db, 商品ID)
