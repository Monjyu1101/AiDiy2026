"""FreeAI設定キーを優先し、Geminiと同じJSON判断を実行する。"""
from AIコア.AI判断_gemini_jsonchat import DecisionAI as GeminiDecisionAI


class DecisionAI(GeminiDecisionAI):
    key_fields = ("freeai_key_id", "gemini_key_id")
