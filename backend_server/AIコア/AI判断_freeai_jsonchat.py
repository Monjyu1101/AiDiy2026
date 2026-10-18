"""FreeAI設定キーを優先し、Geminiと同じJSON判断を実行する。"""
from AIコア.AI判断共通 import FREEAI_DECISION_MODEL
from AIコア.AI判断_gemini_jsonchat import DecisionAI as GeminiDecisionAI


class DecisionAI(GeminiDecisionAI):
    key_fields = ("freeai_key_id", "gemini_key_id")

    async def 実行(self, request, model, config, client):
        return await super().実行(request, FREEAI_DECISION_MODEL, config, client)
