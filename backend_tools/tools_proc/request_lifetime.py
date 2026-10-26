"""HTTP 呼び出し元の切断に合わせて、所有する処理を終了する。"""

import asyncio


class ClientDisconnected(Exception):
    """呼び出し元の切断。実行処理の障害とは区別する。"""


async def run_until_disconnect(request, operation):
    """本文読取後に使用し、切断・取消時は処理の finally 完了まで待つ。"""
    async def watch_disconnect():
        while True:
            if await request.is_disconnected():
                return
            await asyncio.sleep(0.25)

    worker = asyncio.create_task(operation)
    watcher = asyncio.create_task(watch_disconnect())
    try:
        done, _ = await asyncio.wait(
            (worker, watcher), return_when=asyncio.FIRST_COMPLETED
        )
        if worker in done:
            return await worker
        await watcher
        raise ClientDisconnected("HTTP 呼び出し元が切断されました")
    finally:
        for task in (worker, watcher):
            if not task.done():
                task.cancel()
        await asyncio.gather(worker, watcher, return_exceptions=True)
