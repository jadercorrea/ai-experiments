#!/usr/bin/env python3
"""Restricted OpenAI-compatible inference gateway for controlled experiments."""

import argparse
import hashlib
import json
import os
import pathlib
import socketserver
import sys
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Mapping
from urllib.parse import quote, urlsplit

from bedrock_converse import bedrock_to_openai, openai_to_bedrock
from keychain_secrets import read_bearer_authorization, read_keychain_secret

from routing_policy import (
    BackendKind,
    FallbackTrigger,
    RoutingPolicy,
    RoutingState,
)


ALLOWED_PATHS = frozenset({"/v1/chat/completions", "/v1/responses"})
MAX_REQUEST_BYTES = 8 * 1024 * 1024
MAX_RESPONSE_BYTES = 64 * 1024 * 1024
RATE_LIMIT_HEADERS = frozenset(
    {
        "retry-after",
        "x-ratelimit-limit-requests",
        "x-ratelimit-limit-tokens",
        "x-ratelimit-remaining-requests",
        "x-ratelimit-remaining-tokens",
        "x-ratelimit-reset-requests",
        "x-ratelimit-reset-tokens",
    }
)


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self,
        request: object,
        file_pointer: object,
        code: int,
        message: str,
        headers: object,
        new_url: str,
    ) -> None:
        return None


@dataclass(frozen=True)
class Upstream:
    base_url: str
    authorization: str | None = None
    api_format: str = "openai-compatible"
    maximum_output_tokens: int | None = None

    def __post_init__(self) -> None:
        parsed = urlsplit(self.base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("upstream must be an absolute HTTP(S) URL")
        if parsed.query or parsed.fragment or parsed.username or parsed.password:
            raise ValueError(
                "upstream URL cannot contain credentials, query, or fragment"
            )
        if self.api_format not in {"openai-compatible", "bedrock-converse"}:
            raise ValueError(f"unsupported upstream API format: {self.api_format}")
        if self.api_format == "bedrock-converse" and (
            self.maximum_output_tokens is None or self.maximum_output_tokens <= 0
        ):
            raise ValueError(
                "Bedrock Converse upstream requires a positive output-token limit"
            )


@dataclass(frozen=True)
class GatewayConfig:
    run_id: str
    policy: RoutingPolicy
    local: Upstream
    cloud: Upstream
    evidence_path: pathlib.Path
    timeout_seconds: float = 120.0
    allowed_models: frozenset[str] = frozenset()
    local_model: str | None = None
    cloud_model: str | None = None
    maximum_cloud_requests: int | None = None
    initial_fallback_trigger: FallbackTrigger | None = None

    def __post_init__(self) -> None:
        if not self.run_id or any(character.isspace() for character in self.run_id):
            raise ValueError("run_id must be non-empty and contain no whitespace")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if self.local_model is not None and not self.local_model:
            raise ValueError("local_model cannot be empty")
        if self.cloud_model is not None and not self.cloud_model:
            raise ValueError("cloud_model cannot be empty")
        if self.maximum_cloud_requests is not None and self.maximum_cloud_requests < 0:
            raise ValueError("maximum_cloud_requests cannot be negative")
        if (
            self.initial_fallback_trigger is not None
            and self.policy is not RoutingPolicy.LOCAL_FIRST
        ):
            raise ValueError("initial fallback is valid only for local-first")


@dataclass(frozen=True)
class GatewayResponse:
    status: int
    headers: Mapping[str, str]
    body: bytes


def verify_model_inventory(lock: Mapping[str, object], inventory: list[dict]) -> None:
    expected_name = lock["provider_model"]
    expected_digest = str(lock["manifest_digest"]).removeprefix("sha256:")
    matching = [model for model in inventory if model.get("name") == expected_name]
    if len(matching) != 1:
        raise ValueError(f"locked model is not uniquely installed: {expected_name}")
    actual_digest = matching[0].get("digest")
    if actual_digest != expected_digest:
        raise ValueError(
            f"model digest mismatch for {expected_name}: "
            f"expected {expected_digest}, got {actual_digest}"
        )


def verify_runtime_version(lock: Mapping[str, object], actual_version: str) -> None:
    expected_version = lock["version"]
    if lock["name"] != "Ollama" or actual_version != expected_version:
        raise ValueError(
            f"runtime mismatch: expected Ollama {expected_version}, got {actual_version}"
        )


def requires_local_runtime(
    policy: RoutingPolicy,
    *,
    initial_fallback_trigger: FallbackTrigger | None = None,
) -> bool:
    """Return whether a treatment is permitted to contact local inference."""
    return policy is not RoutingPolicy.CLOUD_ONLY and initial_fallback_trigger is None


class EvidenceLog:
    def __init__(
        self, path: pathlib.Path, *, run_id: str, policy: RoutingPolicy
    ) -> None:
        self.path = path
        self.run_id = run_id
        self.policy = policy
        self._lock = threading.Lock()
        self._sequence = 0
        self._previous_hash: str | None = None
        path.parent.mkdir(parents=True, exist_ok=True)
        self._resume()

    def _resume(self) -> None:
        if not self.path.exists():
            return
        previous_hash = None
        for expected_sequence, line in enumerate(
            self.path.read_text(encoding="utf-8").splitlines(), 1
        ):
            record = json.loads(line)
            claimed_hash = record.pop("event_sha256", None)
            canonical = json.dumps(
                record, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            ).encode()
            calculated_hash = hashlib.sha256(canonical).hexdigest()
            valid = (
                claimed_hash == calculated_hash
                and record.get("sequence") == expected_sequence
                and record.get("previous_event_sha256") == previous_hash
                and record.get("run_id") == self.run_id
                and record.get("policy") == self.policy.value
            )
            if not valid:
                raise ValueError(
                    f"invalid evidence chain at sequence {expected_sequence}"
                )
            self._sequence = expected_sequence
            previous_hash = claimed_hash
        self._previous_hash = previous_hash

    def append(self, event: str, **fields: object) -> None:
        with self._lock:
            self._sequence += 1
            record = {
                "schema_version": "ai-experiments.gateway-event/v1",
                "sequence": self._sequence,
                "run_id": self.run_id,
                "timestamp_utc": datetime.now(UTC).isoformat(),
                "event": event,
                "policy": self.policy.value,
                "previous_event_sha256": self._previous_hash,
                **fields,
            }
            canonical = json.dumps(
                record, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            ).encode()
            event_hash = hashlib.sha256(canonical).hexdigest()
            record["event_sha256"] = event_hash
            line = json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
            descriptor = os.open(
                self.path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600
            )
            try:
                os.write(descriptor, line.encode())
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            self._previous_hash = event_hash


class Gateway:
    def __init__(self, config: GatewayConfig) -> None:
        self.config = config
        self.routing = RoutingState(config.policy)
        self.events = EvidenceLog(
            config.evidence_path, run_id=config.run_id, policy=config.policy
        )
        self._restore_or_record_initial_fallback()
        self._budget_lock = threading.Lock()
        self._cloud_requests = self._count_recorded_cloud_requests()

    def _restore_or_record_initial_fallback(self) -> None:
        trigger = self.config.initial_fallback_trigger
        if trigger is None:
            return
        transitions = []
        if self.config.evidence_path.exists():
            transitions = [
                event
                for line in self.config.evidence_path.read_text(
                    encoding="utf-8"
                ).splitlines()
                if (event := json.loads(line)).get("event") == "policy_transition"
            ]
        if transitions:
            if len(transitions) != 1 or transitions[0].get("trigger") != trigger.value:
                raise ValueError("evidence contains a conflicting policy transition")
            self.routing.trigger_fallback(trigger)
            return
        transition = self.routing.trigger_fallback(trigger)
        self.events.append(
            "policy_transition",
            source=transition.source.value,
            destination=transition.destination.value,
            trigger=transition.trigger.value,
        )

    def _count_recorded_cloud_requests(self) -> int:
        if not self.config.evidence_path.exists():
            return 0
        return sum(
            1
            for line in self.config.evidence_path.read_text(
                encoding="utf-8"
            ).splitlines()
            if (
                (event := json.loads(line)).get("backend") == BackendKind.CLOUD.value
                and event.get("event") in {"inference", "inference_failed"}
            )
        )

    def _authorize_cloud_request(
        self, *, request_sha256: str, client_request_bytes: int
    ) -> GatewayResponse | None:
        maximum = self.config.maximum_cloud_requests
        if maximum is None:
            return None
        with self._budget_lock:
            if self._cloud_requests >= maximum:
                self.events.append(
                    "hosted_budget_exhausted",
                    backend=BackendKind.CLOUD.value,
                    request_sha256=request_sha256,
                    client_request_bytes=client_request_bytes,
                    maximum_cloud_requests=maximum,
                )
                body = json.dumps({"error": "hosted request budget exhausted"}).encode()
                return GatewayResponse(
                    429, {"Content-Type": "application/json"}, body
                )
            self._cloud_requests += 1
        return None

    def _active_backend(self) -> BackendKind:
        if self.config.policy is RoutingPolicy.CLOUD_ONLY:
            return BackendKind.CLOUD
        if self.routing.fallback_active:
            return BackendKind.CLOUD
        return BackendKind.LOCAL

    def _upstream(self, backend: BackendKind) -> Upstream:
        return self.config.local if backend is BackendKind.LOCAL else self.config.cloud

    @staticmethod
    def _response_metadata(response_body: bytes) -> dict[str, object]:
        documents = []
        try:
            documents.append(json.loads(response_body))
        except (UnicodeDecodeError, json.JSONDecodeError):
            for line in response_body.splitlines():
                if not line.startswith(b"data: ") or line == b"data: [DONE]":
                    continue
                try:
                    documents.append(json.loads(line.removeprefix(b"data: ")))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    continue

        metadata: dict[str, object] = {}
        tool_names = set()
        for document in documents:
            if not isinstance(document, dict):
                continue
            usage = document.get("usage") or {}
            if model := document.get("model"):
                metadata["model"] = model
            if fingerprint := document.get("system_fingerprint"):
                metadata["system_fingerprint"] = fingerprint
            if service_tier := document.get("service_tier"):
                metadata["service_tier"] = service_tier
            input_tokens = usage.get("prompt_tokens", usage.get("input_tokens"))
            output_tokens = usage.get("completion_tokens", usage.get("output_tokens"))
            prompt_details = usage.get("prompt_tokens_details") or {}
            cached_tokens = prompt_details.get("cached_tokens")
            if input_tokens is not None:
                metadata["input_tokens"] = input_tokens
            if output_tokens is not None:
                metadata["output_tokens"] = output_tokens
            if cached_tokens is not None:
                metadata["cached_input_tokens"] = cached_tokens
            for choice in document.get("choices") or []:
                if finish_reason := choice.get("finish_reason"):
                    metadata["finish_reason"] = finish_reason
                message = choice.get("message") or choice.get("delta") or {}
                for tool_call in message.get("tool_calls") or []:
                    if name := (tool_call.get("function") or {}).get("name"):
                        tool_names.add(name)
        if tool_names:
            metadata["tool_names"] = sorted(tool_names)
        return metadata

    def _request(
        self,
        *,
        backend: BackendKind,
        path: str,
        body: bytes,
        stream: bool,
        request_sha256: str,
        client_request_bytes: int,
    ) -> GatewayResponse:
        self.routing.authorize(backend)
        upstream = self._upstream(backend)
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "ai-experiments-gateway/1",
        }
        if upstream.authorization:
            headers["Authorization"] = upstream.authorization
        request = urllib.request.Request(
            upstream.base_url.rstrip("/") + path,
            data=body,
            headers=headers,
            method="POST",
        )
        started = time.monotonic()
        try:
            opener = urllib.request.build_opener(NoRedirectHandler())
            with opener.open(request, timeout=self.config.timeout_seconds) as response:
                upstream_response_body = response.read(MAX_RESPONSE_BYTES + 1)
                if len(upstream_response_body) > MAX_RESPONSE_BYTES:
                    raise RuntimeError("upstream response exceeds size limit")
                status = response.status
                response_headers = {
                    "Content-Type": response.headers.get(
                        "Content-Type", "application/json"
                    )
                }
                provider_rate_limits = {
                    name.lower(): value
                    for name, value in response.headers.items()
                    if name.lower() in RATE_LIMIT_HEADERS
                }
        except urllib.error.HTTPError as error:
            with error:
                upstream_response_body = error.read(MAX_RESPONSE_BYTES + 1)
                status = error.code
                response_headers = {"Content-Type": "application/json"}
                provider_rate_limits = {
                    name.lower(): value
                    for name, value in error.headers.items()
                    if name.lower() in RATE_LIMIT_HEADERS
                }
            if len(upstream_response_body) > MAX_RESPONSE_BYTES:
                raise RuntimeError("upstream response exceeds size limit")
        response_body = upstream_response_body
        if 200 <= status < 300 and upstream.api_format == "bedrock-converse":
            try:
                provider_document = json.loads(upstream_response_body)
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise RuntimeError("Bedrock response must be valid JSON") from error
            if not isinstance(provider_document, dict):
                raise RuntimeError("Bedrock response must be a JSON object")
            response_body, content_type = bedrock_to_openai(
                provider_document,
                model=self.config.cloud_model or "",
                stream=stream,
            )
            response_headers = {"Content-Type": content_type}
        latency_ms = round((time.monotonic() - started) * 1000)
        event = "inference" if 200 <= status < 300 else "inference_failed"
        response_metadata = self._response_metadata(response_body)
        if provider_rate_limits:
            response_metadata["provider_rate_limits"] = provider_rate_limits
        self.events.append(
            event,
            backend=backend.value,
            request_sha256=request_sha256,
            client_request_bytes=client_request_bytes,
            upstream_request_sha256=hashlib.sha256(body).hexdigest(),
            upstream_request_bytes=len(body),
            upstream_response_sha256=hashlib.sha256(upstream_response_body).hexdigest(),
            upstream_response_bytes=len(upstream_response_body),
            response_sha256=hashlib.sha256(response_body).hexdigest(),
            response_bytes=len(response_body),
            status_code=status,
            latency_ms=latency_ms,
            **response_metadata,
        )
        return GatewayResponse(status, response_headers, response_body)

    def _backend_request(
        self,
        *,
        client_path: str,
        request_document: Mapping[str, object],
        backend: BackendKind,
    ) -> tuple[str, bytes, bool]:
        upstream = self._upstream(backend)
        stream = request_document.get("stream") is True
        if upstream.api_format == "bedrock-converse":
            if client_path != "/v1/chat/completions":
                raise ValueError(
                    "Bedrock Converse adapter supports Chat Completions only"
                )
            if not self.config.cloud_model:
                raise ValueError("Bedrock Converse requires a locked cloud model")
            translated = openai_to_bedrock(
                request_document,
                maximum_output_tokens=upstream.maximum_output_tokens or 0,
            )
            body = json.dumps(
                translated, separators=(",", ":"), ensure_ascii=False
            ).encode()
            model_path = quote(self.config.cloud_model, safe="")
            return f"/model/{model_path}/converse", body, stream
        return client_path, self._backend_body(request_document, backend), stream

    def _backend_body(
        self, request_document: Mapping[str, object], backend: BackendKind
    ) -> bytes:
        target_model = (
            self.config.local_model
            if backend is BackendKind.LOCAL
            else self.config.cloud_model
        )
        if target_model is None:
            return json.dumps(
                request_document, separators=(",", ":"), ensure_ascii=False
            ).encode()
        rewritten = dict(request_document)
        rewritten["model"] = target_model
        if backend is BackendKind.CLOUD and isinstance(rewritten.get("messages"), list):
            rewritten["messages"] = [
                (
                    {key: value for key, value in message.items() if key != "reasoning_content"}
                    if isinstance(message, dict)
                    else message
                )
                for message in rewritten["messages"]
            ]
        return json.dumps(
            rewritten, separators=(",", ":"), ensure_ascii=False
        ).encode()

    def forward(
        self, path: str, body: bytes, _client_headers: Mapping[str, str]
    ) -> GatewayResponse:
        if path not in ALLOWED_PATHS:
            raise ValueError(f"unsupported inference path: {path}")
        if len(body) > MAX_REQUEST_BYTES:
            raise ValueError("request exceeds size limit")
        try:
            request_document = json.loads(body)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("request body must be valid JSON") from error
        if not isinstance(request_document, dict):
            raise ValueError("request body must be a JSON object")
        requested_model = request_document.get("model")
        if (
            self.config.allowed_models
            and requested_model not in self.config.allowed_models
        ):
            raise ValueError(
                f"model is not part of the locked treatment: {requested_model}"
            )

        request_sha256 = hashlib.sha256(body).hexdigest()
        backend = self._active_backend()
        if backend is BackendKind.CLOUD:
            denied = self._authorize_cloud_request(
                request_sha256=request_sha256,
                client_request_bytes=len(body),
            )
            if denied is not None:
                return denied
        upstream_path, upstream_body, stream = self._backend_request(
            client_path=path,
            request_document=request_document,
            backend=backend,
        )
        try:
            response = self._request(
                backend=backend,
                path=upstream_path,
                body=upstream_body,
                stream=stream,
                request_sha256=request_sha256,
                client_request_bytes=len(body),
            )
        except (OSError, TimeoutError, RuntimeError) as error:
            self.events.append(
                "inference_failed",
                backend=backend.value,
                request_sha256=request_sha256,
                client_request_bytes=len(body),
                upstream_request_sha256=hashlib.sha256(upstream_body).hexdigest(),
                upstream_request_bytes=len(upstream_body),
                error_type=type(error).__name__,
            )
            response = None

        if response is None:
            return GatewayResponse(502, {"Content-Type": "application/json"}, b"{}")
        return response


class GatewayHandler(BaseHTTPRequestHandler):
    gateway: Gateway

    def do_POST(self) -> None:  # noqa: N802
        try:
            content_type = self.headers.get_content_type()
            if content_type != "application/json":
                raise ValueError("Content-Type must be application/json")
            length = int(self.headers.get("Content-Length", "-1"))
            if length < 0 or length > MAX_REQUEST_BYTES:
                raise ValueError("request exceeds size limit")
            response = self.gateway.forward(
                self.path, self.rfile.read(length), dict(self.headers.items())
            )
        except ValueError as error:
            payload = json.dumps({"error": str(error)}).encode()
            response = GatewayResponse(
                400, {"Content-Type": "application/json"}, payload
            )
        self.send_response(response.status)
        for name, value in response.headers.items():
            self.send_header(name, value)
        self.send_header("Content-Length", str(len(response.body)))
        self.end_headers()
        self.wfile.write(response.body)

    def log_message(self, _format: str, *args: object) -> None:
        return


class ThreadingUnixHTTPServer(
    socketserver.ThreadingMixIn, socketserver.UnixStreamServer
):
    daemon_threads = True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--listen", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--unix-socket", type=pathlib.Path)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--policy", type=RoutingPolicy, required=True)
    parser.add_argument("--local-url", required=True)
    parser.add_argument("--cloud-url", required=True)
    parser.add_argument("--cloud-authorization-file", type=pathlib.Path)
    parser.add_argument("--cloud-keychain-service")
    parser.add_argument("--cloud-keychain-account")
    parser.add_argument("--cloud-authorization-stdin", action="store_true")
    parser.add_argument("--evidence", type=pathlib.Path, required=True)
    parser.add_argument("--timeout-seconds", type=float, default=120)
    parser.add_argument("--model-lock", type=pathlib.Path, required=True)
    parser.add_argument("--model-role", default="local_coding")
    parser.add_argument("--cloud-model-role", default="cloud_coding")
    parser.add_argument("--maximum-cloud-requests", type=int)
    parser.add_argument("--initial-fallback-trigger", type=FallbackTrigger)
    args = parser.parse_args()
    cloud_authorization = None
    authorization_sources = sum(
        bool(value)
        for value in (
            args.cloud_authorization_file,
            args.cloud_keychain_service,
            args.cloud_authorization_stdin,
        )
    )
    if authorization_sources > 1:
        parser.error("cloud authorization sources are mutually exclusive")
    if bool(args.cloud_keychain_service) != bool(args.cloud_keychain_account):
        parser.error("both cloud Keychain service and account are required")
    if args.cloud_authorization_file:
        cloud_authorization = args.cloud_authorization_file.read_text(
            encoding="utf-8"
        ).strip()
    elif args.cloud_keychain_service:
        cloud_authorization = "Bearer " + read_keychain_secret(
            args.cloud_keychain_service, args.cloud_keychain_account
        )
    elif args.cloud_authorization_stdin:
        cloud_authorization = read_bearer_authorization(sys.stdin.buffer)
    with args.model_lock.open(encoding="utf-8") as lock_file:
        model_lock = json.load(lock_file)
    locked_model = model_lock["models"][args.model_role]
    cloud_model = model_lock["models"].get(args.cloud_model_role)
    if args.policy is not RoutingPolicy.LOCAL_ONLY and cloud_model is None:
        parser.error(f"missing cloud model role: {args.cloud_model_role}")
    if requires_local_runtime(
        args.policy, initial_fallback_trigger=args.initial_fallback_trigger
    ):
        with urllib.request.urlopen(  # noqa: S310 - operator configuration
            args.local_url.rstrip("/") + "/api/version",
            timeout=args.timeout_seconds,
        ) as response:
            runtime_version = json.load(response)["version"]
        verify_runtime_version(model_lock["runtime"], runtime_version)
        with urllib.request.urlopen(  # noqa: S310 - operator configuration
            args.local_url.rstrip("/") + "/api/tags",
            timeout=args.timeout_seconds,
        ) as response:
            inventory = json.load(response)["models"]
        verify_model_inventory(locked_model, inventory)
    config = GatewayConfig(
        run_id=args.run_id,
        policy=args.policy,
        local=Upstream(args.local_url),
        cloud=Upstream(
            args.cloud_url,
            cloud_authorization,
            api_format=(cloud_model or {}).get("api_format", "openai-compatible"),
            maximum_output_tokens=(cloud_model or {}).get("max_completion_tokens"),
        ),
        evidence_path=args.evidence,
        timeout_seconds=args.timeout_seconds,
        allowed_models=frozenset({locked_model["provider_model"]}),
        local_model=locked_model["provider_model"],
        cloud_model=cloud_model["provider_model"] if cloud_model else None,
        maximum_cloud_requests=args.maximum_cloud_requests,
        initial_fallback_trigger=args.initial_fallback_trigger,
    )
    handler = type(
        "ConfiguredGatewayHandler", (GatewayHandler,), {"gateway": Gateway(config)}
    )
    if args.unix_socket:
        if args.unix_socket.exists():
            parser.error(f"Unix socket already exists: {args.unix_socket}")
        server = ThreadingUnixHTTPServer(str(args.unix_socket), handler)
        print(f"gateway listening on {args.unix_socket}")
    else:
        server = ThreadingHTTPServer((args.listen, args.port), handler)
        print(
            f"gateway listening on {server.server_address[0]}:{server.server_address[1]}"
        )
    server.serve_forever()


if __name__ == "__main__":
    main()
