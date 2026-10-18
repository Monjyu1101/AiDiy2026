import copy
import json
import unittest
from unittest.mock import patch

import httpx
from test_decisions import ANSWERS, Decision, DecisionError, request
from AIコア.AI判断共通 import FREEAI_DECISION_MODEL


def envelope(text=None, **kwargs):
    return {"candidates": [{"finishReason": "STOP", "content": {"parts": [
        {"thought": True, "text": "private reasoning"},
        {"text": text if text is not None else json.dumps({"answers": ANSWERS})},
    ]}}], "usageMetadata": {"promptTokenCount": 10}, **kwargs}


class GeminiDecisionTests(unittest.IsolatedAsyncioTestCase):
    async def test_both_providers_request_schema_answers_and_preferred_credentials(self):
        for name, key in (("freeai_chat", "freeai_key_id"), ("gemini_chat", "gemini_key_id")):
            calls = []
            def handler(req):
                calls.append(req)
                self.assertEqual(req.headers["x-goog-api-key"], key + "-fixture")
                self.assertEqual(str(req.url), "https://generativelanguage.googleapis.com/v1beta/models/" + (FREEAI_DECISION_MODEL if name == "freeai_chat" else "custom") + ":generateContent")
                body = json.loads(req.content)
                self.assertEqual(body["generationConfig"]["responseMimeType"], "application/json")
                self.assertIn("answers", body["generationConfig"]["responseJsonSchema"]["properties"])
                self.assertEqual(body["contents"][0]["role"], "user")
                for kind in ("predicate", "choice", "score"):
                    self.assertIn(kind, body["systemInstruction"]["parts"][0]["text"])
                return httpx.Response(200, json=envelope())
            service = Decision(config={"freeai_key_id": "freeai_key_id-fixture", "gemini_key_id": "gemini_key_id-fixture"}, transport=httpx.MockTransport(handler))
            result = await service.実行(request(model=name + "/custom"))
            self.assertEqual(result["data"]["ai_name"], name)
            self.assertEqual(result["data"]["answers"], ANSWERS)
            self.assertEqual(result["data"]["usage"], {"promptTokenCount": 10})
            self.assertEqual(len(calls), 1)

    async def test_key_fallback_and_missing_keys(self):
        for name, primary, other in (("freeai_chat", "freeai_key_id", "gemini_key_id"), ("gemini_chat", "gemini_key_id", "freeai_key_id")):
            calls = []
            def handler(req):
                calls.append(req)
                self.assertEqual(req.headers["x-goog-api-key"], "fallback-fixture")
                return httpx.Response(200, json=envelope())
            service = Decision(config={primary: "<unset>", other: "fallback-fixture"}, transport=httpx.MockTransport(handler))
            await service.実行(request(ai_name=name))
            service._config = {primary: "<unset>", other: '""'}
            with self.assertRaises(DecisionError):
                await service.実行(request(ai_name=name))
            self.assertEqual(len(calls), 1)

    async def test_messages_and_inline_image_are_translated_without_external_fetch(self):
        from AIコア.AI判断共通 import DecisionRequest
        def handler(req):
            contents = json.loads(req.content)["contents"]
            self.assertEqual(contents[0], {"role": "user", "parts": [{"text": "evidence"}]})
            self.assertEqual(contents[1]["parts"], [{"text": "image"}, {"inlineData": {"mimeType": "image/png", "data": "aGVsbG8="}}])
            return httpx.Response(200, json=envelope())
        value = request(ai_name="gemini_chat").model_dump()
        value["input"] = [{"role": "user", "content": "evidence"}, {"role": "user", "content": [{"type": "input_text", "text": "image"}, {"type": "input_image", "image_url": "data:image/png;base64,aGVsbG8="}]}]
        service = Decision(config={"gemini_key_id": "fixture"}, transport=httpx.MockTransport(handler))
        self.assertEqual((await service.実行(DecisionRequest.model_validate(value)))["status"], "OK")

    async def test_malformed_envelopes_and_answers_fail_closed(self):
        malformed = [None, [], {}, {"candidates": []}, {"candidates": [None]},
                     envelope(promptFeedback={"blockReason": "SAFETY"})]
        for finish in (None, "MAX_TOKENS", "SAFETY"):
            body = envelope(); body["candidates"][0]["finishReason"] = finish; malformed.append(body)
        for text in ("[]", "{}", "bad json", "```json\n{}\n```", '{"answers":null}'):
            malformed.append(envelope(text))
        for field, value in (("probability", True), ("probability", ".8"), ("name", "wrong")):
            answers = copy.deepcopy(ANSWERS); answers[0][field] = value
            malformed.append(envelope(json.dumps({"answers": answers})))
        body = envelope(); body["candidates"][0]["content"]["parts"] = [{"inlineData": {}}]; malformed.append(body)
        for name in ("freeai_chat", "gemini_chat"):
            for body in malformed:
                with self.subTest(name=name, body=body):
                    service = Decision(config={"gemini_key_id": "fixture"}, transport=httpx.MockTransport(lambda req: httpx.Response(200, json=body) if body is not None else httpx.Response(200, content="null")))
                    with self.assertRaises(DecisionError):
                        await service.実行(request(ai_name=name))

    async def test_http_errors_and_timeouts_do_not_retry_or_leak(self):
        for name in ("freeai_chat", "gemini_chat"):
            for code in (401, 429, 500, "timeout"):
                calls = []
                def handler(req):
                    calls.append(req)
                    if code == "timeout":
                        raise httpx.ReadTimeout("secret fixture", request=req)
                    return httpx.Response(code, text="secret fixture")
                service = Decision(config={"gemini_key_id": "secret fixture"}, transport=httpx.MockTransport(handler))
                with self.assertRaises(DecisionError) as error:
                    await service.実行(request(ai_name=name))
                self.assertNotIn("secret fixture", str(error.exception))
                self.assertEqual(len(calls), 1)

    async def test_startup_checks_include_both_google_methods(self):
        calls = []
        def handler(req):
            calls.append(req)
            answer = {"type": "choice", "name": "greeting", "choice": "挨拶", "probabilities": [{"value": "挨拶", "probability": 1}, {"value": "その他", "probability": 0}], "confidence": 1}
            return httpx.Response(200, json=envelope(json.dumps({"answers": [answer]})))
        service = Decision(config={"gemini_key_id": "fixture"}, transport=httpx.MockTransport(handler))
        with patch("AIコア.AI判断_openai_jsonchat.oauth_headers", side_effect=DecisionError("no oauth")):
            status = await service.check_availability()
        self.assertTrue(status["freeai_chat"]["ok"])
        self.assertTrue(status["gemini_chat"]["ok"])
        self.assertFalse(status["openai_decisions"]["ok"])
        self.assertEqual(len(calls), 2)

    def test_auto_order_and_explicit_config_model_precedence(self):
        service = Decision(config={})
        order = ["openai_oauth", "freeai_chat", "openai_decisions", "gemini_chat"]
        for index, name in enumerate(order):
            service.availability = {key: {"ok": True} for key in order[index:]}
            self.assertEqual(service.resolve(request(), {})[0], name)
        config = {"DECISION_AI_NAME": "freeai_chat", "DECISION_AI_MODEL": "common", "DECISION_FREEAI_MODEL": "provider"}
        self.assertEqual(service.resolve(request(), config), ("freeai_chat", FREEAI_DECISION_MODEL))
        self.assertEqual(service.resolve(request(ai_model="explicit"), config), ("freeai_chat", FREEAI_DECISION_MODEL))
        config["DECISION_AI_MODEL"] = "auto"
        self.assertEqual(service.resolve(request(), config), ("freeai_chat", FREEAI_DECISION_MODEL))

    async def test_freeai_fixed_model_overrides_all_inputs_and_config_but_not_other_methods(self):
        config = {"DECISION_AI_NAME": "freeai_chat", "DECISION_AI_MODEL": "wrong-common", "DECISION_FREEAI_MODEL": "wrong-provider", "freeai_key_id": "fixture"}
        calls = []
        def handler(req):
            calls.append(req)
            self.assertEqual(req.url.path, "/v1beta/models/" + FREEAI_DECISION_MODEL + ":generateContent")
            self.assertEqual(json.loads(req.content)["generationConfig"]["responseMimeType"], "application/json")
            return httpx.Response(200, json=envelope())
        service = Decision(config=config, transport=httpx.MockTransport(handler))
        for params in ({}, {"ai_name": "freeai_chat", "model": "wrong"}, {"model": "freeai_chat/wrong"}, {"ai_model": "wrong"}, {"ai_name": "freeai_chat", "model": "auto"}):
            result = await service.実行(request(**params))
            self.assertEqual(result["data"]["ai_model"], FREEAI_DECISION_MODEL)
        shown = next(row for row in service.get_config()["providers"] if row["ai_name"] == "freeai_chat")
        self.assertEqual(shown["fixed_model"], FREEAI_DECISION_MODEL)
        self.assertEqual(shown["default_model"], FREEAI_DECISION_MODEL)
        for name in ("gemini_chat", "openai_oauth", "openai_decisions"):
            self.assertEqual(service.resolve(request(ai_name=name, ai_model="explicit"), config), (name, "explicit"))
        from AIコア.AI判断_freeai_jsonchat import DecisionAI
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            await DecisionAI().実行(request(), "wrong-direct", config, client)
        self.assertEqual(len(calls), 6)
