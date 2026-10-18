import asyncio
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import AsyncMock, patch

import httpx
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from AIコア.AI判断 import Decision, PROVIDERS, Provider
from AIコア.AI判断共通 import DecisionError, DecisionRequest, validate_answers


QUESTIONS = [
    {"type": "predicate", "name": "damage", "instructions": "破損がありますか？"},
    {"type": "choice", "name": "route", "instructions": "担当は？", "choices": [{"value": "support"}, {"value": "billing"}]},
    {"type": "score", "name": "severity", "instructions": "重大度は？", "levels": [{"label": "low"}, {"label": "high"}]},
]
ANSWERS = [
    {"type": "predicate", "name": "damage", "probability": .8},
    {"type": "choice", "name": "route", "choice": "support", "probabilities": [{"value": "support", "probability": .8}, {"value": "billing", "probability": .2}], "confidence": .7},
    {"type": "score", "name": "severity", "score": .8, "probabilities": [{"value": 0, "label": "low", "probability": .2}, {"value": 1, "label": "high", "probability": .8}], "confidence": .7},
]


def request(**kwargs):
    return DecisionRequest(input="商品が破損しています", questions=copy.deepcopy(QUESTIONS), **kwargs)


def sse(answers=ANSWERS, *, kind="response.completed", status="completed", text=None):
    event = {"type": kind, "response": {"status": status, "output": [{"type": "message", "content": [{"type": "output_text", "text": text if text is not None else json.dumps({"answers": answers})}]}], "usage": {"input_tokens": 10}}}
    return httpx.Response(200, content="event: " + kind + "\ndata: " + json.dumps(event) + "\n\n")


class DecisionContractTests(unittest.TestCase):
    def test_auto_prefers_healthy_oauth_then_native(self):
        service = Decision(config={})
        config = {"DECISION_AI_NAME": "auto", "DECISION_OAUTH_MODEL": "oauth-model", "DECISION_OPENAI_MODEL": "native-model"}
        for oauth_ok, native_ok, expected in ((True, True, ("openai_oauth", "oauth-model")), (True, False, ("openai_oauth", "oauth-model")), (False, True, ("openai_decisions", "native-model"))):
            service.availability = {"openai_oauth": {"ok": oauth_ok}, "openai_decisions": {"ok": native_ok}}
            for params in ({}, {"ai_name": "auto", "ai_model": "auto"}, {"model": ""}, {"ai_model": "AUTO"}):
                with self.subTest(oauth=oauth_ok, native=native_ok, params=params):
                    self.assertEqual(service.resolve(request(**params), config), expected)
        service.availability["openai_oauth"]["ok"] = True
        self.assertEqual(service.resolve(request(model="openai_decisions/auto"), config), ("openai_decisions", "native-model"))
        self.assertEqual(service.resolve(request(ai_name="openai_decisions", ai_model="auto"), config), ("openai_decisions", "native-model"))

    def test_configured_defaults_and_explicit_overrides(self):
        config = {"DECISION_AI_NAME": "openai_decisions", "DECISION_AI_MODEL": "configured-model"}
        service = Decision(config=config)
        service.availability = {"openai_oauth": {"ok": True, "model": "m"}, "openai_decisions": {"ok": True, "model": "m"}}
        cases = [
            ({}, ("openai_decisions", "configured-model")),
            ({"ai_name": "auto", "model": "auto"}, ("openai_decisions", "configured-model")),
            ({"ai_name": "openai_oauth"}, ("openai_oauth", "configured-model")),
            ({"ai_model": "explicit"}, ("openai_decisions", "explicit")),
            ({"model": "explicit"}, ("openai_decisions", "explicit")),
            ({"model": "openai_oauth/explicit"}, ("openai_oauth", "explicit")),
            ({"model": "openai_oauth/auto"}, ("openai_oauth", "configured-model")),
        ]
        for params, expected in cases:
            with self.subTest(params=params):
                self.assertEqual(service.resolve(request(**params), config), expected)
        self.assertEqual(service.get_config()["configured_defaults"], {
            **config, **dict.fromkeys(("DECISION_OPENAI_MODEL", "DECISION_OAUTH_MODEL", "DECISION_GEMINI_MODEL", "DECISION_FREEAI_MODEL"), "configured-model")})
        self.assertEqual(service.get_config()["default_model"], "openai_decisions/configured-model")

    def test_missing_and_auto_settings_keep_legacy_model_fallback(self):
        service = Decision(config={})
        for value in (None, "", "auto", "AUTO", "  auto  "):
            config = {"DECISION_AI_NAME": value, "DECISION_AI_MODEL": value, "DECISION_OAUTH_MODEL": "legacy"}
            self.assertEqual(service.resolve(request(), config), ("openai_oauth", "legacy"))
        self.assertEqual(service.get_config()["configured_defaults"], {'DECISION_AI_NAME': 'auto', 'DECISION_OPENAI_MODEL': 'auto', 'DECISION_OAUTH_MODEL': 'auto', 'DECISION_GEMINI_MODEL': 'auto', 'DECISION_FREEAI_MODEL': 'auto'})

    def test_configured_provider_does_not_silently_fall_back(self):
        service = Decision(config={})
        service.availability = {"openai_oauth": {"ok": True}, "openai_decisions": {"ok": False}}
        self.assertEqual(service.resolve(request(), {"DECISION_AI_NAME": "openai_decisions"})[0], "openai_decisions")
        with self.assertRaises(DecisionError):
            service.resolve(request(), {"DECISION_AI_NAME": "unknown"})

    def test_default_model_aliases_never_reach_api(self):
        service = Decision(config={})
        for alias in ("auto", "AUTO", ""):
            self.assertEqual(service.resolve(request(model="openai_oauth/auto"), {"DECISION_OAUTH_MODEL": alias}), ("openai_oauth", "gpt-6-luna"))

    def test_selection_and_defaults(self):
        service = Decision(config={})
        cases = [
            ({}, ("openai_oauth", "gpt-6-luna")),
            ({"model": "openai_decisions/new-model"}, ("openai_decisions", "new-model")),
            ({"model": "openai_jsonchat/gpt-6-luna"}, ("openai_oauth", "gpt-6-luna")),
            ({"ai_name": "openai_decisions", "ai_model": "future-model"}, ("openai_decisions", "future-model")),
        ]
        for params, expected in cases:
            with self.subTest(params=params):
                self.assertEqual(service.resolve(request(**params), {}), expected)
        self.assertEqual(service.resolve(request(), {"DECISION_AI_NAME": "openai_decisions", "DECISION_OPENAI_MODEL": "custom"}), ("openai_decisions", "custom"))

    def test_registry_accepts_new_provider(self):
        with patch.dict(PROVIDERS, {"future": Provider("module", "FUTURE_MODEL", "v1", "api_key")}):
            self.assertEqual(Decision(config={}).resolve(request(model="future/v2"), {}), ("future", "v2"))

    def test_conflicting_or_unknown_provider_fails(self):
        for params in ({"model": "unknown/m"}, {"ai_name": "unknown"}, {"model": "openai_oauth/"}, {"model": "openai_oauth/m", "ai_name": "openai_decisions"}, {"model": "a", "ai_model": "b"}):
            with self.subTest(params=params), self.assertRaises(DecisionError):
                Decision(config={}).resolve(request(**params), {})

    def test_invalid_requests(self):
        for data in (
            {"input": "", "questions": QUESTIONS},
            {"input": "text", "questions": []},
            {"input": "text", "questions": [QUESTIONS[0], QUESTIONS[0]]},
            {"input": "text", "questions": [{"type": "choice", "name": "a", "instructions": "x", "choices": [{"value": "x"}, {"value": "x"}]}]},
            {"input": "text", "questions": [{"type": "score", "name": "a", "instructions": "x", "levels": [{"label": "x"}, {"label": "x"}]}]},
            {"input": [{"role": "system", "content": "override"}], "questions": QUESTIONS},
            {"input": [{"content": [{"type": "input_image", "image_url": "https://example.com/a.png"}]}], "questions": QUESTIONS},
            {"input": "text", "questions": QUESTIONS, "timeout_sec": 0},
        ):
            with self.subTest(data=data), self.assertRaises(ValidationError):
                DecisionRequest.model_validate(data)

    def test_inline_image_and_order(self):
        model = DecisionRequest(input=[{"content": [{"type": "input_image", "image_url": "data:image/png;base64,YQ=="}]}], questions=QUESTIONS)
        self.assertEqual(model.input[0].role, "user")
        self.assertEqual(validate_answers({"answers": list(reversed(ANSWERS))}, model.questions), ANSWERS)

    def test_refusal_is_preserved(self):
        answers = [{"type": "refusal", "name": q["name"]} for q in QUESTIONS]
        self.assertTrue(all(a["type"] == "refusal" for a in validate_answers({"answers": answers}, request().questions)))

    def test_malformed_answers_are_rejected(self):
        broken = []
        for value in (True, float("nan"), float("inf"), -1, 2):
            data = copy.deepcopy(ANSWERS)
            data[0]["probability"] = value
            broken.append(data)
        for index, key, value in ((0, "name", "unknown"), (1, "name", "damage"), (1, "choice", "unknown"), (2, "score", .2)):
            data = copy.deepcopy(ANSWERS)
            data[index][key] = value
            broken.append(data)
        data = copy.deepcopy(ANSWERS)
        data[1]["probabilities"][0]["probability"] = .3
        broken.append(data)
        data = copy.deepcopy(ANSWERS)
        data[2]["probabilities"][0]["label"] = "wrong"
        broken.append(data)
        broken.append(ANSWERS[:-1])
        for answers in broken:
            with self.subTest(answers=answers), self.assertRaises(ValueError):
                validate_answers({"answers": answers}, request().questions)

    def test_config_never_exposes_credentials(self):
        config = Decision(config={"openai_key_id": "secret-token"}).get_config()
        self.assertNotIn("secret-token", json.dumps(config))


class DecisionProviderTests(unittest.IsolatedAsyncioTestCase):
    async def test_unavailable_auto_does_not_call_network(self):
        service = Decision(config={}, transport=httpx.MockTransport(lambda req: self.fail("network should not be called")))
        service.availability = {"openai_oauth": {"ok": False}, "openai_decisions": {"ok": False}}
        with self.assertRaisesRegex(DecisionError, "現在利用不可"):
            await service.実行(request(model="auto"))

    async def test_native_decisions_request_and_common_result(self):
        def handler(req):
            self.assertEqual(str(req.url), "https://api.openai.com/v1/decisions")
            self.assertEqual(req.headers["Authorization"], "Bearer test-api-key")
            payload = json.loads(req.content)
            self.assertEqual(set(payload), {"model", "input", "questions"})
            self.assertEqual(payload["model"], "future-model")
            return httpx.Response(200, json={"answers": ANSWERS})
        service = Decision(config={"openai_key_id": "test-api-key"}, transport=httpx.MockTransport(handler))
        result = await service.実行(request(model="openai_decisions/future-model"))
        self.assertEqual(result["data"]["answers"], ANSWERS)
        self.assertEqual(result["data"]["method"], "decisions_api")

    async def test_oauth_schema_stream_without_content_type(self):
        def handler(req):
            self.assertEqual(str(req.url), "https://chatgpt.com/backend-api/codex/responses")
            self.assertEqual(req.headers["Authorization"], "Bearer oauth-test")
            payload = json.loads(req.content)
            self.assertTrue(payload["text"]["format"]["strict"])
            self.assertEqual(payload["text"]["format"]["type"], "json_schema")
            self.assertFalse(payload["store"])
            self.assertTrue(payload["stream"])
            self.assertNotIn("tools", payload)
            return sse()
        service = Decision(config={}, transport=httpx.MockTransport(handler))
        with patch("AIコア.AI判断_openai_jsonchat.oauth_headers", return_value={"Authorization": "Bearer oauth-test"}):
            result = await service.実行(request())
        self.assertEqual(result["data"]["answers"], ANSWERS)
        self.assertEqual(result["data"]["method"], "responses_json_schema")

    async def test_completed_without_repeated_text_uses_stream_deltas(self):
        text = json.dumps({"answers": ANSWERS})
        events = [
            {"type": "response.output_text.delta", "delta": text[:20]},
            {"type": "response.output_text.delta", "delta": text[20:]},
            {"type": "response.completed", "response": {"status": "completed", "output": []}},
        ]
        response = httpx.Response(200, content="".join("data: " + json.dumps(event) + "\n\n" for event in events))
        with patch("AIコア.AI判断_openai_jsonchat.oauth_headers", return_value={"Authorization": "Bearer test"}):
            result = await Decision(config={}, transport=httpx.MockTransport(lambda req: response)).実行(request())
        self.assertEqual(result["data"]["answers"], ANSWERS)

    async def test_stream_errors_and_invalid_json_fail_closed(self):
        responses = [sse(kind="response.failed"), sse(kind="response.incomplete"), sse(status="incomplete"), sse(text="not json"), sse(text="[]"), httpx.Response(200, content='data: {"type":"response.output_text.delta","delta":"partial"}\n\n'), sse(answers=[])]
        with patch("AIコア.AI判断_openai_jsonchat.oauth_headers", return_value={"Authorization": "Bearer test"}):
            for response in responses:
                with self.subTest(response=response), self.assertRaises(DecisionError):
                    await Decision(config={}, transport=httpx.MockTransport(lambda req: response)).実行(request())

    async def test_http_errors_hide_body_credentials(self):
        for provider in ("openai_decisions", "openai_oauth"):
            for status in (401, 403, 429, 500):
                with self.subTest(provider=provider, status=status):
                    service = Decision(config={"openai_key_id": "secret"}, transport=httpx.MockTransport(lambda req: httpx.Response(status, json={"error": "secret"})))
                    with patch("AIコア.AI判断_openai_jsonchat.oauth_headers", return_value={"Authorization": "Bearer secret"}), self.assertRaises(DecisionError) as caught:
                        await service.実行(request(ai_name=provider))
                    self.assertNotIn("secret", str(caught.exception))

    async def test_missing_key_does_not_call_network(self):
        def handler(req):
            self.fail("network should not be called")
        with self.assertRaises(DecisionError):
            await Decision(config={}, transport=httpx.MockTransport(handler)).実行(request(ai_name="openai_decisions"))

    async def test_timeout_is_reported(self):
        def handler(req):
            raise httpx.ReadTimeout("private request data")
        with self.assertRaisesRegex(DecisionError, "タイムアウト"):
            await Decision(config={"openai_key_id": "test"}, transport=httpx.MockTransport(handler)).実行(request(ai_name="openai_decisions"))

    async def test_cancel_is_propagated(self):
        async def handler(req):
            raise asyncio.CancelledError()
        with self.assertRaises(asyncio.CancelledError):
            await Decision(config={"openai_key_id": "test"}, transport=httpx.MockTransport(handler)).実行(request(ai_name="openai_decisions"))


class DecisionAvailabilityTests(unittest.IsolatedAsyncioTestCase):
    @staticmethod
    def greeting_response():
        return {"answers": [{
            "type": "choice", "name": "greeting", "choice": "挨拶",
            "probabilities": [{"value": "挨拶", "probability": 1.0}, {"value": "その他", "probability": 0.0}],
            "confidence": 1.0,
        }]}

    async def test_common_model_is_used_for_startup_checks(self):
        models = []
        def handler(req):
            models.append(json.loads(req.content)["model"])
            if "/v1/decisions" in str(req.url):
                return httpx.Response(200, json=self.greeting_response())
            return sse(answers=self.greeting_response()["answers"])
        service = Decision(config={"openai_key_id": "test", "DECISION_AI_MODEL": "configured-model"}, transport=httpx.MockTransport(handler))
        with patch("AIコア.AI判断_openai_jsonchat.oauth_headers", return_value={"Authorization": "Bearer test"}):
            results = await service.check_availability()
        self.assertEqual(models, ["configured-model", "configured-model"])
        self.assertTrue(all(results[name]["ok"] and results[name]["model"] == "configured-model" for name in ("openai_decisions", "openai_oauth")))
        self.assertFalse(results["freeai_chat"]["ok"])
        self.assertFalse(results["gemini_chat"]["ok"])

    async def test_both_providers_execute_greeting_check(self):
        calls = []

        def handler(req):
            body = json.loads(req.content)
            calls.append((str(req.url), body))
            if req.url.host == "api.openai.com":
                self.assertEqual(body["input"], "おはよう")
                self.assertEqual(body["model"], "custom-decision-model")
                return httpx.Response(200, json=self.greeting_response())
            self.assertEqual(body["input"][0]["content"][0]["text"], "おはよう")
            self.assertEqual(body["model"], "custom-oauth-model")
            return sse(answers=self.greeting_response()["answers"])

        service = Decision(config={"openai_key_id": "test-key", "DECISION_OPENAI_MODEL": "custom-decision-model", "DECISION_OAUTH_MODEL": "custom-oauth-model"}, transport=httpx.MockTransport(handler))
        self.assertFalse(service.get_config()["availability_checked"])
        with patch("AIコア.AI判断_openai_jsonchat.oauth_headers", return_value={"Authorization": "Bearer test"}):
            results = await service.check_availability()
        self.assertEqual(len(calls), 2)
        self.assertTrue(all(results[name]["ok"] and results[name]["answer"] == "挨拶" and results[name]["checked_at"] for name in ("openai_decisions", "openai_oauth")))
        self.assertFalse(results["freeai_chat"]["ok"])
        self.assertFalse(results["gemini_chat"]["ok"])
        self.assertEqual(service.get_config()["available_models"], ["openai_decisions/custom-decision-model", "openai_oauth/custom-oauth-model"])
        results["openai_oauth"]["ok"] = False
        self.assertTrue(service.get_config()["availability"]["openai_oauth"]["ok"])

    async def test_placeholder_keys_skip_execution_but_oauth_is_checked(self):
        for key in (None, "", "  ", "< key >", "  <", '""', "“”", "''"):
            with self.subTest(key=key):
                service = Decision(config={"openai_key_id": key})
                reply = {"data": self.greeting_response()}
                with patch.object(service, "実行", new=AsyncMock(return_value=reply)) as execute:
                    results = await service.check_availability()
                self.assertFalse(results["openai_decisions"]["ok"])
                self.assertIn("未設定", results["openai_decisions"]["reason"])
                self.assertTrue(results["openai_oauth"]["ok"])
                self.assertEqual(execute.await_count, 1)
                self.assertEqual(execute.call_args.args[0].ai_name, "openai_oauth")

    async def test_failure_is_isolated_and_does_not_expose_exception_text(self):
        service = Decision(config={"openai_key_id": "secret-key"})

        async def execute(check):
            if check.ai_name == "openai_oauth":
                raise RuntimeError("secret-key")
            return {"data": self.greeting_response()}

        with patch.object(service, "実行", side_effect=execute):
            results = await service.check_availability()
        self.assertTrue(results["openai_decisions"]["ok"])
        self.assertFalse(results["openai_oauth"]["ok"])
        self.assertNotIn("secret-key", json.dumps(service.get_config()))

    async def test_wrong_answer_and_refusal_are_unavailable(self):
        for answer in ({"type": "choice", "choice": "その他"}, {"type": "refusal"}):
            service = Decision(config={})
            with patch.object(service, "実行", new=AsyncMock(return_value={"data": {"answers": [answer]}})):
                results = await service.check_availability()
            self.assertFalse(results["openai_oauth"]["ok"])
            self.assertIn("期待結果", results["openai_oauth"]["reason"])

    async def test_deadline_marks_unavailable(self):
        service = Decision(config={})

        async def execute(check):
            await asyncio.sleep(10)

        with patch.object(service, "実行", side_effect=execute):
            results = await service.check_availability(timeout_sec=1)
        self.assertFalse(results["openai_oauth"]["ok"])
        self.assertIn("タイムアウト", results["openai_oauth"]["reason"])

    async def test_invalid_config_does_not_abort_startup(self):
        service = Decision(config={})
        with patch.object(service, "_load_config", side_effect=DecisionError("設定読込エラー")), patch.object(service, "実行", new=AsyncMock()) as execute:
            results = await service.check_availability()
        execute.assert_not_awaited()
        self.assertTrue(all(not info["ok"] for info in results.values()))


if __name__ == "__main__":
    unittest.main()
