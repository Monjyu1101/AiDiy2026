# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101
# -------------------------------------------------------------------------

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

import apps_schema as schemas
import deps
import apps_models as models
from log_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/apps/V商品推移表", tags=["V商品推移表"])

# ==================================================
# Pydantic Schemas for this router
# ==================================================

class TransitionRequest(BaseModel):
    開始日付: str  # YYYY-MM-DD
    終了日付: str  # YYYY-MM-DD


class 日付範囲Request(BaseModel):
    開始日付: Optional[str] = None
    終了日付: Optional[str] = None

class DayData(BaseModel):
    日付: str
    入庫数量: int = 0
    出庫数量: int = 0
    棚卸数量: Optional[int] = None
    推定在庫: int = 0
    入庫最終更新日時: Optional[str] = None
    出庫最終更新日時: Optional[str] = None
    棚卸最終更新日時: Optional[str] = None

class ProductTransitionData(BaseModel):
    商品ID: str
    商品名: str
    日別データ: List[DayData]

class TransitionResponse(schemas.ResponseBase):
    data: Dict[str, Any]

# ==================================================
# Endpoints
# ==================================================

@router.post("/一覧", response_model=TransitionResponse)
def list_transition(
    request: TransitionRequest,
    db: Session = Depends(deps.get_db),
    current_user: models.C利用者 = Depends(deps.get_現在利用者)
):
    try:
        start_date_str = request.開始日付
        end_date_str = request.終了日付
        
        # 1. 全商品取得
        products = db.query(models.M商品).all()
        # 商品ID順にソート
        products.sort(key=lambda x: x.商品ID)
        product_map = {p.商品ID: p.商品名 for p in products}
        
        # 2. 全トランザクション取得（効率のため全件取得してからメモリで処理）
        # ※データ量が膨大になった場合はSQLで期間絞り込みと集計を行うべきですが、
        #   在庫推移計算のためには期間前のデータも必要なため、今回は全件取得方式を採用
        inbounds = db.query(models.T商品入庫).all()
        outbounds = db.query(models.T商品出庫).all()
        inventories = db.query(models.T商品棚卸).all()
        
        # 3. 日付リスト生成
        date_list = []
        curr = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        
        while curr <= end:
            date_list.append(curr.strftime("%Y-%m-%d"))
            curr += timedelta(days=1)
            
        # 4. 商品ごとに集計
        result_data = []
        
        for pid, pname in product_map.items():
            # この商品のトランザクションを抽出
            p_inbounds = [x for x in inbounds if x.商品ID == pid]
            p_outbounds = [x for x in outbounds if x.商品ID == pid]
            p_inventories = [x for x in inventories if x.商品ID == pid]
            
            # 全イベントをフラットな辞書リストに変換
            events = []
            for x in p_inbounds:
                events.append({"date": x.入庫日, "type": "in", "qty": int(x.入庫数量 or 0), "updated": x.更新日時})
            for x in p_outbounds:
                events.append({"date": x.出庫日, "type": "out", "qty": int(x.出庫数量 or 0), "updated": x.更新日時})
            for x in p_inventories:
                events.append({"date": x.棚卸日, "type": "inv", "qty": int(x.実棚数量 or 0), "updated": x.更新日時})
                
            # 日付順、同日の場合は 入庫 -> 出庫 -> 棚卸 の順とする
            # typeの優先度: in(1), out(2), inv(3)
            type_order = {"in": 1, "out": 2, "inv": 3}
            events.sort(key=lambda x: (x["date"], type_order[x["type"]]))
            
            # 初期在庫計算（開始日より前のイベントを処理）
            current_stock = 0
            
            # 開始日より前のイベントのみ処理
            # 文字列比較で判定 (YYYY-MM-DD形式前提)
            for ev in events:
                if ev["date"] < start_date_str:
                    if ev["type"] == "in":
                        current_stock += ev["qty"]
                    elif ev["type"] == "out":
                        current_stock -= ev["qty"]
                    elif ev["type"] == "inv":
                        current_stock = ev["qty"] # 棚卸で強制上書き
            
            # 期間内の日別データ作成
            product_daily_data = []
            
            for d_str in date_list:
                # その日のイベントを取得
                days_events = [e for e in events if e["date"] == d_str]
                
                # 集計
                in_qty = sum(e["qty"] for e in days_events if e["type"] == "in")
                out_qty = sum(e["qty"] for e in days_events if e["type"] == "out")
                inv_event = next((e for e in reversed(days_events) if e["type"] == "inv"), None) # 同日に複数あれば最後を採用
                
                # 更新日時（最新のもの）
                in_updated = max([e["updated"] for e in days_events if e["type"] == "in"], default=None)
                out_updated = max([e["updated"] for e in days_events if e["type"] == "out"], default=None)
                inv_updated = inv_event["updated"] if inv_event else None
                
                # 在庫推移計算
                current_stock += in_qty
                current_stock -= out_qty
                
                # 棚卸があれば上書き
                inv_qty = None
                if inv_event:
                    current_stock = inv_event["qty"]
                    inv_qty = inv_event["qty"]
                    
                product_daily_data.append(DayData(
                    日付=d_str,
                    入庫数量=in_qty,
                    出庫数量=out_qty,
                    棚卸数量=inv_qty,
                    推定在庫=current_stock,
                    入庫最終更新日時=in_updated,
                    出庫最終更新日時=out_updated,
                    棚卸最終更新日時=inv_updated
                ))
            
            result_data.append(ProductTransitionData(
                商品ID=pid,
                商品名=pname,
                日別データ=product_daily_data
            ))
            
        return TransitionResponse(
            status="OK",
            message=f"商品推移データを取得しました（期間: {start_date_str}〜{end_date_str}）",
            data={
                "日付リスト": date_list,
                "商品推移データ": result_data
            }
        )
        
    except Exception as e:
        logger.exception("V商品推移表 取得エラー: %s", e)
        return TransitionResponse(
            status="NG",
            message=f"データ取得中にエラーが発生しました: {str(e)}",
            data={}
        )


@router.post("/最終更新日時", response_model=schemas.ResponseBase)
def get_transition_last_modified(
    request: 日付範囲Request,
    db: Session = Depends(deps.get_db),
    current_user: models.C利用者 = Depends(deps.get_現在利用者)
):
    if not request.開始日付 or not request.終了日付:
        return schemas.ResponseBase(
            status="NG",
            message="開始日付と終了日付を指定してください",
            error={"code": "MISSING_PARAMS"}
        )

    入庫最終更新日時 = db.query(func.max(models.T商品入庫.更新日時)).filter(
        func.date(models.T商品入庫.入庫日).between(request.開始日付, request.終了日付)
    ).scalar()
    出庫最終更新日時 = db.query(func.max(models.T商品出庫.更新日時)).filter(
        func.date(models.T商品出庫.出庫日).between(request.開始日付, request.終了日付)
    ).scalar()
    棚卸最終更新日時 = db.query(func.max(models.T商品棚卸.更新日時)).filter(
        func.date(models.T商品棚卸.棚卸日).between(request.開始日付, request.終了日付)
    ).scalar()

    候補リスト = [値 for 値 in [入庫最終更新日時, 出庫最終更新日時, 棚卸最終更新日時] if 値 is not None]
    if not 候補リスト:
        最終更新日時 = None
    else:
        最終更新日時 = max(候補リスト)

    return schemas.ResponseBase(
        status="OK",
        message="最終更新日時を取得しました",
        data={"最終更新日時": 最終更新日時}
    )

