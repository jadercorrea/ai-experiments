"""Translate the experiment's OpenAI-compatible surface to Bedrock Converse."""

from __future__ import annotations

import hashlib
import json
from typing import Mapping


STOP_REASON_MAP = {
    "end_turn": "stop",
    "stop_sequence": "stop",
    "tool_use": "tool_calls",
    "max_tokens": "length",
    "content_filtered": "content_filter",
    "guardrail_intervened": "content_filter",
}


def _text_blocks(content: object) -> list[dict[str, str]]:
    if content is None or content == "":
        return []
    if isinstance(content, str):
        return [{"text": content}]
    if not isinstance(content, list):
        raise ValueError("message content must be text or a list of text blocks")
    blocks = []
    for item in content:
        if not isinstance(item, dict):
            raise ValueError("message content blocks must be JSON objects")
        block_type = item.get("type")
        if block_type not in {"text", "input_text", "output_text"}:
            raise ValueError(f"unsupported OpenAI content block: {block_type}")
        text = item.get("text")
        if not isinstance(text, str):
            raise ValueError("text content block must contain a string")
        blocks.append({"text": text})
    return blocks


def _tool_uses(message: Mapping[str, object]) -> list[dict[str, object]]:
    blocks = []
    for call in message.get("tool_calls") or []:
        if not isinstance(call, dict) or call.get("type", "function") != "function":
            raise ValueError("only OpenAI function tool calls are supported")
        function = call.get("function")
        if not isinstance(function, dict):
            raise ValueError("tool call function must be a JSON object")
        arguments = function.get("arguments", "{}")
        try:
            parsed_arguments = json.loads(arguments) if isinstance(arguments, str) else arguments
        except json.JSONDecodeError as error:
            raise ValueError("tool arguments must be a valid JSON object") from error
        if not isinstance(parsed_arguments, dict):
            raise ValueError("tool arguments must be a valid JSON object")
        call_id = call.get("id")
        name = function.get("name")
        if not isinstance(call_id, str) or not isinstance(name, str):
            raise ValueError("tool calls require string id and function name")
        blocks.append(
            {
                "toolUse": {
                    "toolUseId": call_id,
                    "name": name,
                    "input": parsed_arguments,
                }
            }
        )
    return blocks


def _append_message(
    messages: list[dict[str, object]], role: str, content: list[dict[str, object]]
) -> None:
    if not content:
        return
    if messages and messages[-1]["role"] == role:
        existing = messages[-1]["content"]
        if isinstance(existing, list):
            existing.extend(content)
            return
    messages.append({"role": role, "content": content})


def _translate_messages(
    source: object,
) -> tuple[list[dict[str, str]], list[dict[str, object]]]:
    if not isinstance(source, list):
        raise ValueError("messages must be a JSON array")
    system = []
    messages: list[dict[str, object]] = []
    for message in source:
        if not isinstance(message, dict):
            raise ValueError("messages must contain JSON objects")
        role = message.get("role")
        if role in {"system", "developer"}:
            system.extend(_text_blocks(message.get("content")))
        elif role == "user":
            _append_message(messages, "user", _text_blocks(message.get("content")))
        elif role == "assistant":
            content: list[dict[str, object]] = list(
                _text_blocks(message.get("content"))
            )
            content.extend(_tool_uses(message))
            _append_message(messages, "assistant", content)
        elif role == "tool":
            call_id = message.get("tool_call_id")
            if not isinstance(call_id, str):
                raise ValueError("tool results require a string tool_call_id")
            result_content = _text_blocks(message.get("content"))
            _append_message(
                messages,
                "user",
                [
                    {
                        "toolResult": {
                            "toolUseId": call_id,
                            "content": result_content or [{"text": ""}],
                        }
                    }
                ],
            )
        else:
            raise ValueError(f"unsupported OpenAI message role: {role}")
    return system, messages


def _translate_tools(
    source: object, tool_choice: object
) -> dict[str, object] | None:
    if tool_choice == "none":
        return None
    if source is None:
        return None
    if not isinstance(source, list):
        raise ValueError("tools must be a JSON array")
    tools = []
    for tool in source:
        if not isinstance(tool, dict) or tool.get("type") != "function":
            raise ValueError("only OpenAI function tools are supported")
        function = tool.get("function")
        if not isinstance(function, dict) or not isinstance(function.get("name"), str):
            raise ValueError("function tools require a name")
        schema = function.get("parameters") or {"type": "object"}
        if not isinstance(schema, dict):
            raise ValueError("function tool parameters must be a JSON schema object")
        spec: dict[str, object] = {
            "name": function["name"],
            "inputSchema": {"json": schema},
        }
        if isinstance(function.get("description"), str) and function["description"]:
            spec["description"] = function["description"]
        tools.append({"toolSpec": spec})
    config: dict[str, object] = {"tools": tools}
    if tool_choice is None or tool_choice == "auto":
        config["toolChoice"] = {"auto": {}}
    elif tool_choice == "required":
        config["toolChoice"] = {"any": {}}
    elif isinstance(tool_choice, dict):
        function = tool_choice.get("function")
        if tool_choice.get("type") != "function" or not isinstance(function, dict):
            raise ValueError("unsupported OpenAI tool_choice")
        name = function.get("name")
        if not isinstance(name, str):
            raise ValueError("specific tool choice requires a function name")
        config["toolChoice"] = {"tool": {"name": name}}
    else:
        raise ValueError("unsupported OpenAI tool_choice")
    return config


def openai_to_bedrock(
    request: Mapping[str, object], *, maximum_output_tokens: int
) -> dict[str, object]:
    """Convert one Chat Completions request into a bounded Converse request."""
    if maximum_output_tokens <= 0:
        raise ValueError("maximum_output_tokens must be positive")
    if request.get("n", 1) != 1:
        raise ValueError("Bedrock Converse adapter supports exactly one completion")
    system, messages = _translate_messages(request.get("messages"))
    requested_tokens = request.get(
        "max_completion_tokens", request.get("max_tokens", maximum_output_tokens)
    )
    if not isinstance(requested_tokens, int) or requested_tokens <= 0:
        raise ValueError("completion token limit must be a positive integer")
    inference: dict[str, object] = {
        "maxTokens": min(requested_tokens, maximum_output_tokens)
    }
    if "temperature" in request:
        inference["temperature"] = request["temperature"]
    if "top_p" in request:
        inference["topP"] = request["top_p"]
    if "stop" in request:
        stop = request["stop"]
        inference["stopSequences"] = [stop] if isinstance(stop, str) else stop
    translated: dict[str, object] = {
        "messages": messages,
        "inferenceConfig": inference,
    }
    if system:
        translated["system"] = system
    tool_config = _translate_tools(request.get("tools"), request.get("tool_choice"))
    if tool_config:
        translated["toolConfig"] = tool_config
    return translated


def _openai_document(
    response: Mapping[str, object], *, model: str
) -> dict[str, object]:
    output = response.get("output") or {}
    message = output.get("message") or {} if isinstance(output, dict) else {}
    content = message.get("content") or [] if isinstance(message, dict) else []
    text_parts = []
    tool_calls = []
    for block in content:
        if not isinstance(block, dict):
            continue
        if isinstance(block.get("text"), str):
            text_parts.append(block["text"])
        tool_use = block.get("toolUse")
        if isinstance(tool_use, dict):
            tool_calls.append(
                {
                    "id": tool_use.get("toolUseId"),
                    "type": "function",
                    "function": {
                        "name": tool_use.get("name"),
                        "arguments": json.dumps(
                            tool_use.get("input") or {},
                            sort_keys=True,
                            separators=(",", ":"),
                        ),
                    },
                }
            )
    openai_message: dict[str, object] = {
        "role": "assistant",
        "content": "".join(text_parts) or None,
    }
    if tool_calls:
        openai_message["tool_calls"] = tool_calls
    usage = response.get("usage") or {}
    if not isinstance(usage, dict):
        usage = {}
    cached = usage.get("cacheReadInputTokens", 0) or 0
    canonical = json.dumps(response, sort_keys=True, separators=(",", ":")).encode()
    return {
        "id": f"bedrock-{hashlib.sha256(canonical).hexdigest()[:24]}",
        "object": "chat.completion",
        "created": 0,
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": openai_message,
                "finish_reason": STOP_REASON_MAP.get(
                    response.get("stopReason"), response.get("stopReason")
                ),
            }
        ],
        "usage": {
            "prompt_tokens": usage.get("inputTokens"),
            "completion_tokens": usage.get("outputTokens"),
            "total_tokens": usage.get("totalTokens"),
            "prompt_tokens_details": {"cached_tokens": cached},
        },
    }


def bedrock_to_openai(
    response: Mapping[str, object], *, model: str, stream: bool
) -> tuple[bytes, str]:
    """Normalize a Converse response into Chat Completions JSON or SSE."""
    document = _openai_document(response, model=model)
    if not stream:
        return (
            json.dumps(document, separators=(",", ":"), ensure_ascii=False).encode(),
            "application/json",
        )
    choice = document["choices"][0]
    message = choice["message"]
    delta = dict(message)
    first = {
        **{key: document[key] for key in ("id", "object", "created", "model")},
        "object": "chat.completion.chunk",
        "choices": [{"index": 0, "delta": delta, "finish_reason": None}],
    }
    final = {
        **{key: document[key] for key in ("id", "object", "created", "model")},
        "object": "chat.completion.chunk",
        "choices": [
            {"index": 0, "delta": {}, "finish_reason": choice["finish_reason"]}
        ],
        "usage": document["usage"],
    }
    events = [first, final]
    body = b"".join(
        b"data: "
        + json.dumps(event, separators=(",", ":"), ensure_ascii=False).encode()
        + b"\n\n"
        for event in events
    )
    return body + b"data: [DONE]\n\n", "text/event-stream"
