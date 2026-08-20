import hashlib
import json
import pathlib
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from inference_gateway import Gateway, GatewayConfig, Upstream  # noqa: E402
from inference_gateway import requires_local_runtime  # noqa: E402
from inference_gateway import verify_model_inventory, verify_runtime_version  # noqa: E402
from routing_policy import FallbackTrigger, RoutingPolicy  # noqa: E402


class _UpstreamHandler(BaseHTTPRequestHandler):
    calls: list[dict] = []
    response_status = 200
    response_body = b'{"choices":[{"message":{"content":"ok"}}]}'
    redirect_to: str | None = None

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        type(self).calls.append(
            {
                "path": self.path,
                "body": body,
                "authorization": self.headers.get("Authorization"),
                "user_agent": self.headers.get("User-Agent"),
            }
        )
        self.send_response(type(self).response_status)
        if type(self).redirect_to:
            self.send_header("Location", type(self).redirect_to)
        self.send_header("Content-Type", "application/json")
        self.send_header("x-ratelimit-limit-tokens", "250000")
        self.send_header("x-ratelimit-remaining-tokens", "249000")
        self.end_headers()
        self.wfile.write(type(self).response_body)

    def log_message(self, _format: str, *args: object) -> None:
        return


class FakeUpstream:
    def __init__(
        self,
        *,
        status: int = 200,
        body: bytes | None = None,
        redirect_to: str | None = None,
    ) -> None:
        handler = type("Handler", (_UpstreamHandler,), {})
        handler.calls = []
        handler.response_status = status
        handler.redirect_to = redirect_to
        if body is not None:
            handler.response_body = body
        self.handler = handler
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    @property
    def url(self) -> str:
        host, port = self.server.server_address
        return f"http://{host}:{port}"

    def __enter__(self) -> "FakeUpstream":
        self.thread.start()
        return self

    def __exit__(self, *args: object) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()


class InferenceGatewayTest(unittest.TestCase):
    def _gateway(
        self,
        *,
        policy: RoutingPolicy,
        local_url: str,
        cloud_url: str,
        evidence: pathlib.Path,
        cloud_api_format: str = "openai-compatible",
        cloud_model: str = "openai/gpt-oss-120b",
        maximum_cloud_requests: int | None = None,
        initial_fallback_trigger: FallbackTrigger | None = None,
    ) -> Gateway:
        return Gateway(
            GatewayConfig(
                run_id="run-001",
                policy=policy,
                local=Upstream(base_url=local_url),
                cloud=Upstream(
                    base_url=cloud_url,
                    authorization="Bearer secret",
                    api_format=cloud_api_format,
                    maximum_output_tokens=256,
                ),
                evidence_path=evidence,
                timeout_seconds=2,
                allowed_models=frozenset({"qwen3-coder:locked"}),
                local_model="qwen3-coder:locked",
                cloud_model=cloud_model,
                maximum_cloud_requests=maximum_cloud_requests,
                initial_fallback_trigger=initial_fallback_trigger,
            )
        )

    def test_local_first_initial_fallback_routes_cloud_and_is_restart_safe(self) -> None:
        with (
            tempfile.TemporaryDirectory() as directory,
            FakeUpstream() as local,
            FakeUpstream() as cloud,
        ):
            evidence = pathlib.Path(directory) / "events.jsonl"
            first = self._gateway(
                policy=RoutingPolicy.LOCAL_FIRST,
                local_url=local.url,
                cloud_url=cloud.url,
                evidence=evidence,
                initial_fallback_trigger=FallbackTrigger.NO_MATERIAL_PATCH,
            )
            first.forward(
                "/v1/chat/completions", b'{"model":"qwen3-coder:locked"}', {}
            )
            restarted = self._gateway(
                policy=RoutingPolicy.LOCAL_FIRST,
                local_url=local.url,
                cloud_url=cloud.url,
                evidence=evidence,
                initial_fallback_trigger=FallbackTrigger.NO_MATERIAL_PATCH,
            )
            restarted.forward(
                "/v1/chat/completions", b'{"model":"qwen3-coder:locked"}', {}
            )

            self.assertEqual(local.handler.calls, [])
            self.assertEqual(len(cloud.handler.calls), 2)
            events = [json.loads(line) for line in evidence.read_text().splitlines()]
            transitions = [
                event for event in events if event["event"] == "policy_transition"
            ]
            self.assertEqual(len(transitions), 1)
            self.assertEqual(transitions[0]["trigger"], "no_material_patch")
            self.assertEqual(transitions[0]["source"], "local")
            self.assertEqual(transitions[0]["destination"], "cloud")

    def test_initial_fallback_is_valid_only_for_local_first(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                self._gateway(
                    policy=RoutingPolicy.CLOUD_ONLY,
                    local_url="http://127.0.0.1:1",
                    cloud_url="http://127.0.0.1:2",
                    evidence=pathlib.Path(directory) / "events.jsonl",
                    initial_fallback_trigger=FallbackTrigger.BACKEND_FAILURE,
                )

    def test_cloud_request_cap_survives_gateway_restart(self) -> None:
        with (
            tempfile.TemporaryDirectory() as directory,
            FakeUpstream() as local,
            FakeUpstream() as cloud,
        ):
            evidence = pathlib.Path(directory) / "events.jsonl"
            first = self._gateway(
                policy=RoutingPolicy.CLOUD_ONLY,
                local_url=local.url,
                cloud_url=cloud.url,
                evidence=evidence,
                maximum_cloud_requests=1,
            )
            first.forward(
                "/v1/chat/completions", b'{"model":"qwen3-coder:locked"}', {}
            )
            restarted = self._gateway(
                policy=RoutingPolicy.CLOUD_ONLY,
                local_url=local.url,
                cloud_url=cloud.url,
                evidence=evidence,
                maximum_cloud_requests=1,
            )

            denied = restarted.forward(
                "/v1/chat/completions", b'{"model":"qwen3-coder:locked"}', {}
            )

            self.assertEqual(denied.status, 429)
            self.assertEqual(len(cloud.handler.calls), 1)
            events = [json.loads(line) for line in evidence.read_text().splitlines()]
            self.assertEqual(events[-1]["event"], "hosted_budget_exhausted")
            self.assertEqual(events[-1]["maximum_cloud_requests"], 1)

    def test_cloud_bedrock_converse_adapter_preserves_openai_surface(self) -> None:
        bedrock_body = json.dumps(
            {
                "output": {
                    "message": {
                        "role": "assistant",
                        "content": [
                            {
                                "toolUse": {
                                    "toolUseId": "tool-1",
                                    "name": "record_admission",
                                    "input": {"status": "accepted"},
                                }
                            }
                        ],
                    }
                },
                "stopReason": "tool_use",
                "usage": {
                    "inputTokens": 42,
                    "outputTokens": 8,
                    "totalTokens": 50,
                },
                "metrics": {"latencyMs": 100},
            }
        ).encode()
        with (
            tempfile.TemporaryDirectory() as directory,
            FakeUpstream() as local,
            FakeUpstream(body=bedrock_body) as cloud,
        ):
            evidence = pathlib.Path(directory) / "events.jsonl"
            gateway = self._gateway(
                policy=RoutingPolicy.CLOUD_ONLY,
                local_url=local.url,
                cloud_url=cloud.url,
                evidence=evidence,
                cloud_api_format="bedrock-converse",
                cloud_model="us.anthropic.claude-sonnet-4-6",
            )
            client_body = json.dumps(
                {
                    "model": "qwen3-coder:locked",
                    "messages": [{"role": "user", "content": "Use the tool."}],
                    "tools": [
                        {
                            "type": "function",
                            "function": {
                                "name": "record_admission",
                                "parameters": {"type": "object"},
                            },
                        }
                    ],
                    "tool_choice": {
                        "type": "function",
                        "function": {"name": "record_admission"},
                    },
                    "max_completion_tokens": 512,
                    "stream": False,
                }
            ).encode()

            response = gateway.forward("/v1/chat/completions", client_body, {})

            self.assertEqual(response.status, 200)
            self.assertEqual(
                cloud.handler.calls[0]["path"],
                "/model/us.anthropic.claude-sonnet-4-6/converse",
            )
            forwarded = json.loads(cloud.handler.calls[0]["body"])
            self.assertNotIn("model", forwarded)
            self.assertEqual(forwarded["inferenceConfig"]["maxTokens"], 256)
            normalized = json.loads(response.body)
            self.assertEqual(normalized["model"], "us.anthropic.claude-sonnet-4-6")
            self.assertEqual(
                normalized["choices"][0]["message"]["tool_calls"][0]["function"][
                    "name"
                ],
                "record_admission",
            )
            event = json.loads(evidence.read_text(encoding="utf-8"))
            self.assertEqual(event["model"], "us.anthropic.claude-sonnet-4-6")
            self.assertEqual(event["input_tokens"], 42)
            self.assertEqual(event["output_tokens"], 8)
            self.assertEqual(len(event["upstream_response_sha256"]), 64)

    def test_local_only_routes_only_to_local_and_redacts_prompts(self) -> None:
        with (
            tempfile.TemporaryDirectory() as directory,
            FakeUpstream() as local,
            FakeUpstream() as cloud,
        ):
            evidence = pathlib.Path(directory) / "events.jsonl"
            gateway = self._gateway(
                policy=RoutingPolicy.LOCAL_ONLY,
                local_url=local.url,
                cloud_url=cloud.url,
                evidence=evidence,
            )
            body = b'{"model":"qwen3-coder:locked","messages":[{"content":"private prompt"}]}'
            response = gateway.forward("/v1/chat/completions", body, {})

            self.assertEqual(response.status, 200)
            self.assertEqual(len(local.handler.calls), 1)
            self.assertEqual(cloud.handler.calls, [])
            event_text = evidence.read_text(encoding="utf-8")
            self.assertNotIn("private prompt", event_text)
            event = json.loads(event_text)
            self.assertEqual(event["backend"], "local")
            self.assertEqual(len(event["request_sha256"]), 64)

    def test_cloud_only_uses_gateway_managed_authorization(self) -> None:
        with (
            tempfile.TemporaryDirectory() as directory,
            FakeUpstream() as local,
            FakeUpstream() as cloud,
        ):
            gateway = self._gateway(
                policy=RoutingPolicy.CLOUD_ONLY,
                local_url=local.url,
                cloud_url=cloud.url,
                evidence=pathlib.Path(directory) / "events.jsonl",
            )
            gateway.forward(
                "/v1/chat/completions",
                b'{"model":"qwen3-coder:locked"}',
                {"Authorization": "Bearer untrusted-client-value"},
            )

            self.assertEqual(local.handler.calls, [])
            self.assertEqual(cloud.handler.calls[0]["authorization"], "Bearer secret")
            self.assertEqual(
                cloud.handler.calls[0]["user_agent"], "ai-experiments-gateway/1"
            )

    def test_cloud_only_rewrites_locked_client_model_for_hosted_backend(self) -> None:
        with (
            tempfile.TemporaryDirectory() as directory,
            FakeUpstream() as local,
            FakeUpstream() as cloud,
        ):
            gateway = self._gateway(
                policy=RoutingPolicy.CLOUD_ONLY,
                local_url=local.url,
                cloud_url=cloud.url,
                evidence=pathlib.Path(directory) / "events.jsonl",
            )
            client_body = b'{"model":"qwen3-coder:locked","messages":[]}'
            gateway.forward(
                "/v1/chat/completions",
                client_body,
                {},
            )

            forwarded = json.loads(cloud.handler.calls[0]["body"])
            self.assertEqual(forwarded["model"], "openai/gpt-oss-120b")
            event = json.loads(
                (pathlib.Path(directory) / "events.jsonl").read_text(encoding="utf-8")
            )
            upstream_body = cloud.handler.calls[0]["body"]
            self.assertEqual(event["client_request_bytes"], len(client_body))
            self.assertEqual(event["upstream_request_bytes"], len(upstream_body))
            self.assertEqual(
                event["upstream_request_sha256"],
                hashlib.sha256(upstream_body).hexdigest(),
            )
            self.assertNotEqual(
                event["request_sha256"], event["upstream_request_sha256"]
            )

    def test_local_only_preserves_locked_local_model(self) -> None:
        with (
            tempfile.TemporaryDirectory() as directory,
            FakeUpstream() as local,
            FakeUpstream() as cloud,
        ):
            gateway = self._gateway(
                policy=RoutingPolicy.LOCAL_ONLY,
                local_url=local.url,
                cloud_url=cloud.url,
                evidence=pathlib.Path(directory) / "events.jsonl",
            )
            gateway.forward(
                "/v1/chat/completions",
                b'{"model":"qwen3-coder:locked","messages":[]}',
                {},
            )

            forwarded = json.loads(local.handler.calls[0]["body"])
            self.assertEqual(forwarded["model"], "qwen3-coder:locked")

    def test_cloud_removes_nonportable_reasoning_content_from_history(self) -> None:
        with (
            tempfile.TemporaryDirectory() as directory,
            FakeUpstream() as local,
            FakeUpstream() as cloud,
        ):
            gateway = self._gateway(
                policy=RoutingPolicy.CLOUD_ONLY,
                local_url=local.url,
                cloud_url=cloud.url,
                evidence=pathlib.Path(directory) / "events.jsonl",
            )
            body = json.dumps(
                {
                    "model": "qwen3-coder:locked",
                    "messages": [
                        {
                            "role": "assistant",
                            "content": "",
                            "reasoning_content": "private chain of thought",
                        }
                    ],
                }
            ).encode()
            gateway.forward("/v1/chat/completions", body, {})

            forwarded = json.loads(cloud.handler.calls[0]["body"])
            self.assertNotIn("reasoning_content", forwarded["messages"][0])

    def test_records_model_and_usage_without_response_content(self) -> None:
        response_body = json.dumps(
            {
                "model": "local-model@digest",
                "choices": [{"message": {"content": "private answer"}}],
                "usage": {"prompt_tokens": 21, "completion_tokens": 8},
            }
        ).encode()
        with (
            tempfile.TemporaryDirectory() as directory,
            FakeUpstream(body=response_body) as local,
            FakeUpstream() as cloud,
        ):
            evidence = pathlib.Path(directory) / "events.jsonl"
            gateway = self._gateway(
                policy=RoutingPolicy.LOCAL_ONLY,
                local_url=local.url,
                cloud_url=cloud.url,
                evidence=evidence,
            )
            gateway.forward(
                "/v1/chat/completions", b'{"model":"qwen3-coder:locked"}', {}
            )

            event_text = evidence.read_text(encoding="utf-8")
            event = json.loads(event_text)
            self.assertNotIn("private answer", event_text)
            self.assertEqual(event["model"], "local-model@digest")
            self.assertEqual(event["input_tokens"], 21)
            self.assertEqual(event["output_tokens"], 8)

    def test_records_hosted_fingerprint_cache_and_service_tier(self) -> None:
        response_body = json.dumps(
            {
                "model": "openai/gpt-oss-120b",
                "system_fingerprint": "fp_immutable-if-provider-supports-it",
                "service_tier": "on_demand",
                "choices": [{"message": {"content": "private answer"}}],
                "usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 7,
                    "prompt_tokens_details": {"cached_tokens": 80},
                },
            }
        ).encode()
        with (
            tempfile.TemporaryDirectory() as directory,
            FakeUpstream() as local,
            FakeUpstream(body=response_body) as cloud,
        ):
            evidence = pathlib.Path(directory) / "events.jsonl"
            gateway = self._gateway(
                policy=RoutingPolicy.CLOUD_ONLY,
                local_url=local.url,
                cloud_url=cloud.url,
                evidence=evidence,
            )
            gateway.forward(
                "/v1/chat/completions", b'{"model":"qwen3-coder:locked"}', {}
            )

            event = json.loads(evidence.read_text(encoding="utf-8"))
            self.assertEqual(event["cached_input_tokens"], 80)
            self.assertEqual(
                event["system_fingerprint"],
                "fp_immutable-if-provider-supports-it",
            )
            self.assertEqual(event["service_tier"], "on_demand")
            self.assertEqual(
                event["provider_rate_limits"]["x-ratelimit-limit-tokens"],
                "250000",
            )

    def test_cloud_only_does_not_require_a_local_runtime(self) -> None:
        self.assertFalse(requires_local_runtime(RoutingPolicy.CLOUD_ONLY))
        self.assertTrue(requires_local_runtime(RoutingPolicy.LOCAL_ONLY))
        self.assertTrue(requires_local_runtime(RoutingPolicy.LOCAL_FIRST))
        self.assertFalse(
            requires_local_runtime(
                RoutingPolicy.LOCAL_FIRST,
                initial_fallback_trigger=FallbackTrigger.HARD_TIMEOUT,
            )
        )

    def test_records_stream_tool_names_without_arguments_or_content(self) -> None:
        response_body = b"\n".join(
            [
                b'data: {"model":"qwen","choices":[{"delta":{"content":"secret"}}]}',
                b'data: {"choices":[{"delta":{"tool_calls":[{"function":{"name":"read","arguments":"private path"}}]},"finish_reason":"tool_calls"}],"usage":{"prompt_tokens":5,"completion_tokens":2}}',
                b"data: [DONE]",
            ]
        )
        with (
            tempfile.TemporaryDirectory() as directory,
            FakeUpstream(body=response_body) as local,
            FakeUpstream() as cloud,
        ):
            evidence = pathlib.Path(directory) / "events.jsonl"
            gateway = self._gateway(
                policy=RoutingPolicy.LOCAL_ONLY,
                local_url=local.url,
                cloud_url=cloud.url,
                evidence=evidence,
            )
            gateway.forward(
                "/v1/chat/completions", b'{"model":"qwen3-coder:locked"}', {}
            )

            event_text = evidence.read_text(encoding="utf-8")
            event = json.loads(event_text)
            self.assertNotIn("secret", event_text)
            self.assertNotIn("private path", event_text)
            self.assertEqual(event["model"], "qwen")
            self.assertEqual(event["tool_names"], ["read"])
            self.assertEqual(event["finish_reason"], "tool_calls")

    def test_event_chain_resumes_across_gateway_restart(self) -> None:
        with (
            tempfile.TemporaryDirectory() as directory,
            FakeUpstream() as local,
            FakeUpstream() as cloud,
        ):
            evidence = pathlib.Path(directory) / "events.jsonl"
            first = self._gateway(
                policy=RoutingPolicy.LOCAL_ONLY,
                local_url=local.url,
                cloud_url=cloud.url,
                evidence=evidence,
            )
            first.forward("/v1/chat/completions", b'{"model":"qwen3-coder:locked"}', {})
            second = self._gateway(
                policy=RoutingPolicy.LOCAL_ONLY,
                local_url=local.url,
                cloud_url=cloud.url,
                evidence=evidence,
            )
            second.forward(
                "/v1/chat/completions", b'{"model":"qwen3-coder:locked"}', {}
            )

            events = [json.loads(line) for line in evidence.read_text().splitlines()]
            self.assertEqual([event["sequence"] for event in events], [1, 2])
            self.assertEqual(
                events[1]["previous_event_sha256"], events[0]["event_sha256"]
            )

    def test_local_first_gateway_restart_starts_a_new_local_stage(self) -> None:
        with (
            tempfile.TemporaryDirectory() as directory,
            FakeUpstream(status=503) as local,
            FakeUpstream() as cloud,
        ):
            evidence = pathlib.Path(directory) / "events.jsonl"
            first = self._gateway(
                policy=RoutingPolicy.LOCAL_FIRST,
                local_url=local.url,
                cloud_url=cloud.url,
                evidence=evidence,
            )
            first.forward("/v1/chat/completions", b'{"model":"qwen3-coder:locked"}', {})
            restarted = self._gateway(
                policy=RoutingPolicy.LOCAL_FIRST,
                local_url=local.url,
                cloud_url=cloud.url,
                evidence=evidence,
            )
            restarted.forward(
                "/v1/chat/completions", b'{"model":"qwen3-coder:locked"}', {}
            )

            self.assertEqual(len(local.handler.calls), 2)
            self.assertEqual(len(cloud.handler.calls), 0)

    def test_local_first_backend_failure_requires_clean_runner_escalation(self) -> None:
        with (
            tempfile.TemporaryDirectory() as directory,
            FakeUpstream(status=503) as local,
            FakeUpstream() as cloud,
        ):
            evidence = pathlib.Path(directory) / "events.jsonl"
            gateway = self._gateway(
                policy=RoutingPolicy.LOCAL_FIRST,
                local_url=local.url,
                cloud_url=cloud.url,
                evidence=evidence,
            )
            body = b'{"model":"qwen3-coder:locked"}'
            response = gateway.forward("/v1/chat/completions", body, {})

            self.assertEqual(response.status, 503)
            self.assertEqual(len(local.handler.calls), 1)
            self.assertEqual(len(cloud.handler.calls), 0)
            events = [json.loads(line) for line in evidence.read_text().splitlines()]
            self.assertEqual([event["event"] for event in events], ["inference_failed"])

    def test_client_error_is_recorded_as_failed_inference(self) -> None:
        with (
            tempfile.TemporaryDirectory() as directory,
            FakeUpstream(status=403) as local,
            FakeUpstream() as cloud,
        ):
            evidence = pathlib.Path(directory) / "events.jsonl"
            gateway = self._gateway(
                policy=RoutingPolicy.LOCAL_ONLY,
                local_url=local.url,
                cloud_url=cloud.url,
                evidence=evidence,
            )
            gateway.forward(
                "/v1/chat/completions", b'{"model":"qwen3-coder:locked"}', {}
            )

            event = json.loads(evidence.read_text(encoding="utf-8"))
            self.assertEqual(event["event"], "inference_failed")

    def test_rejects_paths_outside_openai_compatible_surface(self) -> None:
        with (
            tempfile.TemporaryDirectory() as directory,
            FakeUpstream() as local,
            FakeUpstream() as cloud,
        ):
            gateway = self._gateway(
                policy=RoutingPolicy.LOCAL_ONLY,
                local_url=local.url,
                cloud_url=cloud.url,
                evidence=pathlib.Path(directory) / "events.jsonl",
            )
            with self.assertRaises(ValueError):
                gateway.forward("/api/pull", b"{}", {})

            self.assertEqual(local.handler.calls, [])
            self.assertEqual(cloud.handler.calls, [])

    def test_rejects_model_outside_lock(self) -> None:
        with (
            tempfile.TemporaryDirectory() as directory,
            FakeUpstream() as local,
            FakeUpstream() as cloud,
        ):
            gateway = self._gateway(
                policy=RoutingPolicy.LOCAL_ONLY,
                local_url=local.url,
                cloud_url=cloud.url,
                evidence=pathlib.Path(directory) / "events.jsonl",
            )
            with self.assertRaises(ValueError):
                gateway.forward(
                    "/v1/chat/completions", b'{"model":"qwen3-coder:latest"}', {}
                )
            self.assertEqual(local.handler.calls, [])

    def test_rejects_non_object_json(self) -> None:
        with (
            tempfile.TemporaryDirectory() as directory,
            FakeUpstream() as local,
            FakeUpstream() as cloud,
        ):
            gateway = self._gateway(
                policy=RoutingPolicy.LOCAL_ONLY,
                local_url=local.url,
                cloud_url=cloud.url,
                evidence=pathlib.Path(directory) / "events.jsonl",
            )
            with self.assertRaises(ValueError):
                gateway.forward("/v1/chat/completions", b"[]", {})

    def test_does_not_follow_upstream_redirects(self) -> None:
        with (
            tempfile.TemporaryDirectory() as directory,
            FakeUpstream() as target,
            FakeUpstream(status=302, redirect_to="placeholder") as redirect,
            FakeUpstream() as cloud,
        ):
            redirect.handler.redirect_to = target.url + "/captured"
            gateway = self._gateway(
                policy=RoutingPolicy.LOCAL_ONLY,
                local_url=redirect.url,
                cloud_url=cloud.url,
                evidence=pathlib.Path(directory) / "events.jsonl",
            )
            response = gateway.forward(
                "/v1/chat/completions",
                b'{"model":"qwen3-coder:locked"}',
                {},
            )

            self.assertEqual(response.status, 302)
            self.assertEqual(target.handler.calls, [])

    def test_model_inventory_requires_exact_locked_digest(self) -> None:
        lock = {
            "provider_model": "qwen3-coder:30b-a3b-q4_K_M",
            "manifest_digest": "sha256:" + "a" * 64,
        }
        inventory = [
            {
                "name": "qwen3-coder:30b-a3b-q4_K_M",
                "digest": "a" * 64,
            }
        ]
        verify_model_inventory(lock, inventory)
        inventory[0]["digest"] = "b" * 64
        with self.assertRaises(ValueError):
            verify_model_inventory(lock, inventory)

    def test_runtime_version_must_match_lock(self) -> None:
        verify_runtime_version({"name": "Ollama", "version": "0.32.5"}, "0.32.5")
        with self.assertRaises(ValueError):
            verify_runtime_version({"name": "Ollama", "version": "0.32.5"}, "0.33.0")


if __name__ == "__main__":
    unittest.main()
