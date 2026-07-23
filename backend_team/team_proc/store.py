# -*- coding: utf-8 -*-

from __future__ import annotations

import asyncio
import random
from copy import deepcopy
from datetime import datetime
from threading import RLock
from uuid import uuid4

from . import persona_catalog, team_db

状態候補 = ("作業中", "相談中", "瞑想中", "移動中")
作業候補 = (
    "要件を小さなタスクへ分解中",
    "既存コードの影響範囲を調査中",
    "実装案を組み立て中",
    "テストケースを追加中",
    "レビューコメントを整理中",
    "次のタスクを自主選択中",
)
雑談候補 = (
    "この実装、もう少し軽くできそう",
    "瞑想を終えたら一緒にレビューしよう",
    "さっきの発見、共有しておいたよ",
    "次はどのタスクを拾う？",
)

色候補 = ("#5bd9ff", "#9d91ff", "#5ce3a1", "#ff8fc2", "#ffd078", "#78afff", "#d893ff", "#74e9dc")


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


class TeamStore:
    """仮実装用のインメモリチーム状態。DB永続化は次段階で追加する。"""

    def __init__(self) -> None:
        self._lock = RLock()
        self._simulation_enabled = True
        self._revision = 0
        self._agents: list[dict] = []
        self._activities: list[dict] = []
        self.reload_members(record_activity=False)
        self._record("admin", "AIチームの見守りを開始しました", "#5bd9ff")

    def _record(self, name: str, content: str, color: str) -> None:
        self._revision += 1
        self._activities.insert(0, {
            "活動ID": uuid4().hex,
            "発生日時": now_iso(),
            "エージェント名": name,
            "内容": content,
            "色": color,
        })
        del self._activities[50:]

    def _add_member(
        self,
        member: dict,
        index: int,
        state: str = "召喚中",
        record_activity: bool = True,
        member_type: str = "DB",
    ) -> dict:
        name = str(member["要員名"])
        role = str(member["役割"])
        color = 色候補[index % len(色候補)]
        agent = {
            "エージェントID": str(member["要員ID"]),
            "エージェント名": name,
            "要員種別": member_type,
            "役割": role,
            "人格情報": str(member["人格情報"]),
            "色": color,
            "状態": state,
            "作業内容": 作業候補[index % len(作業候補)] if state == "作業中" else "次の行動を考えています",
            "ひとこと": 雑談候補[index % len(雑談候補)] if state == "相談中" else "",
            "位置": (
                {"x": 0.3, "y": 0.66, "z": 5.35}
                if state == "召喚中"
                else {"x": 0.0, "y": 0.66, "z": 0.0}
            ),
            "更新日時": now_iso(),
        }
        self._agents.append(agent)
        if record_activity:
            self._record(name, f"{role}エージェントを召喚しました", color)
        return agent

    def reload_members(self, record_activity: bool = True) -> None:
        with self._lock:
            members = team_db.list_members()
            member_ids = {str(member["要員ID"]) for member in members}
            self._agents = [
                agent
                for agent in self._agents
                if agent.get("要員種別") != "DB"
                or agent["エージェントID"] in member_ids
            ]
            current = {
                agent["エージェントID"]: agent
                for agent in self._agents
                if agent.get("要員種別") == "DB"
            }
            for index, member in enumerate(members):
                member_id = str(member["要員ID"])
                if member_id not in current:
                    state = "作業中" if member_id == team_db.ADMIN_ID else "召喚中"
                    self._add_member(
                        member,
                        index,
                        state,
                        record_activity,
                        member_type="DB",
                    )
                else:
                    current[member_id]["エージェント名"] = str(member["要員名"])
                    current[member_id]["役割"] = str(member["役割"])
                    current[member_id]["人格情報"] = str(member["人格情報"])

    def snapshot(self) -> dict:
        self.reload_members()
        with self._lock:
            return {
                "revision": self._revision,
                "シミュレーション中": self._simulation_enabled,
                "エージェント": deepcopy(self._agents),
                "活動": deepcopy(self._activities[:10]),
                "集計": {
                    "召喚数": len(self._agents),
                    "作業中": sum(a["状態"] == "作業中" for a in self._agents),
                    "相談中": sum(a["状態"] == "相談中" for a in self._agents),
                    "瞑想中": sum(a["状態"] == "瞑想中" for a in self._agents),
                },
            }

    def list_agents(self) -> list[dict]:
        self.reload_members()
        with self._lock:
            return deepcopy(self._agents)

    def list_activities(self, limit: int) -> list[dict]:
        with self._lock:
            return deepcopy(self._activities[:limit])

    def summon(self, member_id: str, requested_role: str = "") -> dict:
        if not member_id.strip():
            raise ValueError("召喚する要員を選択してください")
        member = persona_catalog.get_persona(member_id)
        if member is None:
            raise ValueError("personaフォルダに対象要員が見つかりません")
        del requested_role
        with self._lock:
            if any(
                agent["エージェントID"] == member["要員ID"]
                for agent in self._agents
            ):
                raise ValueError("対象要員は既に召喚されています")
            member = team_db.upsert_persona_member(
                member,
                {
                    "利用者ID": "system",
                    "利用者名": "システム",
                    "端末ID": "backend_team",
                },
            )
            return deepcopy(
                self._add_member(
                    member,
                    len(self._agents),
                    state="召喚中",
                    member_type="DB",
                )
            )

    def expel(self, member_id: str) -> dict:
        member_id = member_id.strip()
        if member_id == team_db.ADMIN_ID:
            raise ValueError("admin要員は排除できません")
        with self._lock:
            agent = next(
                (
                    row
                    for row in self._agents
                    if row["エージェントID"] == member_id
                ),
                None,
            )
            if agent is None:
                raise KeyError(member_id)
            item = team_db.disable_member(
                member_id,
                {
                    "利用者ID": "system",
                    "利用者名": "システム",
                    "端末ID": "backend_team",
                },
            )
            self._agents = [
                row
                for row in self._agents
                if row["エージェントID"] != member_id
            ]
            self._record(
                agent["エージェント名"],
                "チーム空間から排除しました",
                agent["色"],
            )
            return item

    def update_state(self, agent_id: str, state: str, content: str = "", comment: str = "") -> dict:
        if state not in (*状態候補, "召喚中"):
            raise ValueError(f"未対応の状態です: {state}")
        with self._lock:
            agent = next((row for row in self._agents if row["エージェントID"] == agent_id), None)
            if agent is None:
                raise KeyError(agent_id)
            agent["状態"] = state
            agent["作業内容"] = content.strip() or self._default_content(state)
            agent["ひとこと"] = comment.strip() or (random.choice(雑談候補) if state == "相談中" else "")
            agent["更新日時"] = now_iso()
            self._record(agent["エージェント名"], f"{state}: {agent['作業内容']}", agent["色"])
            return deepcopy(agent)

    def set_simulation(self, enabled: bool) -> bool:
        with self._lock:
            self._simulation_enabled = enabled
            self._revision += 1
            return self._simulation_enabled

    def _default_content(self, state: str) -> str:
        return {
            "作業中": random.choice(作業候補),
            "相談中": "仲間とアイデア交換",
            "瞑想中": "静かに思考と文脈を整理中",
            "移動中": "オフィスを気ままに移動中",
            "召喚中": "雑談エリアでチームに合流中",
        }[state]

    def tick(self) -> None:
        with self._lock:
            if not self._simulation_enabled or not self._agents:
                return
            agent = random.choice(self._agents)
            state = random.choices(状態候補, weights=(48, 20, 14, 18), k=1)[0]
            self.update_state(agent["エージェントID"], state)


store = TeamStore()


async def simulation_loop(logger) -> None:
    logger.info("backend_team モックシミュレーションを開始しました")
    try:
        while True:
            await asyncio.sleep(8)
            store.tick()
    except asyncio.CancelledError:
        logger.info("backend_team モックシミュレーションを停止しました")
        raise
