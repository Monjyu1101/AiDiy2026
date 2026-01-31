# -*- coding: utf-8 -*-

# ------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
# This software is licensed under the MIT License.
# https://github.com/monjyu1101
# Thank you for keeping the rules.
# ------------------------------------------------

from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from models1.A会話履歴 import A会話履歴
from crud1.utils import create_audit_fields, update_audit_fields
from typing import Optional, List


def create_会話履歴(
    db: Session,
    ソケットID: str,
    シーケンス: int,
    チャンネル: int,
    メッセージ識別: str,
    メッセージ内容: Optional[str] = None,
    ファイル名: Optional[str] = None,
    サムネイル画像: Optional[str] = None,
    認証情報: dict = None
) -> A会話履歴:
    """会話履歴を作成"""
    audit_fields = create_audit_fields(認証情報)

    db_record = A会話履歴(
        ソケットID=ソケットID,
        シーケンス=シーケンス,
        チャンネル=チャンネル,
        メッセージ識別=メッセージ識別,
        メッセージ内容=メッセージ内容,
        ファイル名=ファイル名,
        サムネイル画像=サムネイル画像,
        **audit_fields
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record


def get_会話履歴(db: Session, ソケットID: str, シーケンス: int) -> Optional[A会話履歴]:
    """会話履歴を1件取得"""
    return db.query(A会話履歴).filter(
        and_(
            A会話履歴.ソケットID == ソケットID,
            A会話履歴.シーケンス == シーケンス
        )
    ).first()


def get_会話履歴_by_socket(
    db: Session,
    ソケットID: str,
    チャンネル: Optional[int] = None,
    limit: int = 100
) -> List[A会話履歴]:
    """ソケットIDで会話履歴を取得（チャンネル指定可能）"""
    query = db.query(A会話履歴).filter(A会話履歴.ソケットID == ソケットID)

    if チャンネル is not None:
        query = query.filter(A会話履歴.チャンネル == チャンネル)

    return query.order_by(desc(A会話履歴.シーケンス)).limit(limit).all()


def get_next_sequence(db: Session, ソケットID: str) -> int:
    """次のシーケンス番号を取得"""
    max_seq = db.query(A会話履歴.シーケンス).filter(
        A会話履歴.ソケットID == ソケットID
    ).order_by(desc(A会話履歴.シーケンス)).first()

    return (max_seq[0] + 1) if max_seq else 1


def update_会話履歴(
    db: Session,
    ソケットID: str,
    シーケンス: int,
    メッセージ内容: Optional[str] = None,
    ファイル名: Optional[str] = None,
    サムネイル画像: Optional[str] = None,
    認証情報: dict = None
) -> Optional[A会話履歴]:
    """会話履歴を更新"""
    db_record = get_会話履歴(db, ソケットID, シーケンス)
    if not db_record:
        return None

    audit_fields = update_audit_fields(認証情報)

    if メッセージ内容 is not None:
        db_record.メッセージ内容 = メッセージ内容
    if ファイル名 is not None:
        db_record.ファイル名 = ファイル名
    if サムネイル画像 is not None:
        db_record.サムネイル画像 = サムネイル画像

    for key, value in audit_fields.items():
        setattr(db_record, key, value)

    db.commit()
    db.refresh(db_record)
    return db_record


def delete_会話履歴(db: Session, ソケットID: str, シーケンス: int) -> bool:
    """会話履歴を削除"""
    db_record = get_会話履歴(db, ソケットID, シーケンス)
    if not db_record:
        return False

    db.delete(db_record)
    db.commit()
    return True


def delete_会話履歴_by_socket(db: Session, ソケットID: str) -> int:
    """ソケットIDに紐づく会話履歴を全削除"""
    count = db.query(A会話履歴).filter(A会話履歴.ソケットID == ソケットID).count()
    db.query(A会話履歴).filter(A会話履歴.ソケットID == ソケットID).delete()
    db.commit()
    return count
