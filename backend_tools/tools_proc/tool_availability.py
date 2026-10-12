"""接続先の登録を維持したまま、起動チェックの利用可否を伝える。"""


def availability_status(label: str, checks: dict) -> dict:
    available = [name for name, info in checks.items() if info.get("ok")]
    unavailable = [name for name, info in checks.items() if not info.get("ok")]
    if available:
        message = f"{label} 利用可能: {', '.join(available)}"
        if unavailable:
            message += f"。現在利用不可: {', '.join(unavailable)}"
    else:
        message = f"現在利用不可：{label} の起動チェックに成功した実行機能がありません。設定・依存ツール・認証を確認して再起動してください。"
    return {"status": "OK" if available else "NG", "available": bool(available), "message": message}
