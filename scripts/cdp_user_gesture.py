import asyncio
import json
import sys
import urllib.request

import websockets


async def evaluate(ws_url: str, expression: str) -> dict:
    async with websockets.connect(ws_url, max_size=8 * 1024 * 1024) as ws:
        msg = {
            "id": 1,
            "method": "Runtime.evaluate",
            "params": {
                "expression": expression,
                "userGesture": True,
                "awaitPromise": False,
                "returnByValue": True,
            },
        }
        await ws.send(json.dumps(msg))
        while True:
            raw = await ws.recv()
            data = json.loads(raw)
            if data.get("id") == 1:
                return data


def find_ws_url(tab_id: str) -> str:
    resp = urllib.request.urlopen("http://localhost:9222/json")
    pages = json.loads(resp.read())
    for p in pages:
        if p.get("id") == tab_id:
            return p["webSocketDebuggerUrl"]
    raise SystemExit(f"tab not found: {tab_id}")


def main() -> None:
    tab_id = sys.argv[1]
    expression = sys.argv[2]
    ws_url = find_ws_url(tab_id)
    result = asyncio.run(evaluate(ws_url, expression))
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
