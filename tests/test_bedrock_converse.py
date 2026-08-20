import json
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from bedrock_converse import (  # noqa: E402
    bedrock_to_openai,
    openai_to_bedrock,
)


class BedrockConverseTest(unittest.TestCase):
    def test_translates_openai_tool_conversation_to_converse(self) -> None:
        request = {
            "model": "client-model",
            "messages": [
                {"role": "system", "content": "Follow repository instructions."},
                {"role": "user", "content": "Inspect the file."},
                {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "id": "call-1",
                            "type": "function",
                            "function": {
                                "name": "read_file",
                                "arguments": '{"path":"main.py"}',
                            },
                        }
                    ],
                },
                {
                    "role": "tool",
                    "tool_call_id": "call-1",
                    "content": "print('hello')",
                },
            ],
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "read_file",
                        "description": "Read one file.",
                        "parameters": {
                            "type": "object",
                            "required": ["path"],
                            "properties": {"path": {"type": "string"}},
                        },
                    },
                }
            ],
            "tool_choice": {
                "type": "function",
                "function": {"name": "read_file"},
            },
            "max_completion_tokens": 512,
            "temperature": 0,
            "stream": True,
        }

        translated = openai_to_bedrock(request, maximum_output_tokens=256)

        self.assertEqual(
            translated["system"], [{"text": "Follow repository instructions."}]
        )
        self.assertEqual(translated["inferenceConfig"]["maxTokens"], 256)
        self.assertEqual(translated["inferenceConfig"]["temperature"], 0)
        self.assertEqual(
            translated["toolConfig"]["toolChoice"], {"tool": {"name": "read_file"}}
        )
        self.assertEqual(
            translated["messages"][1]["content"][0]["toolUse"],
            {
                "toolUseId": "call-1",
                "name": "read_file",
                "input": {"path": "main.py"},
            },
        )
        self.assertEqual(
            translated["messages"][2]["content"][0]["toolResult"]["toolUseId"],
            "call-1",
        )
        self.assertNotIn("model", translated)
        self.assertNotIn("stream", translated)

    def test_rejects_malformed_tool_arguments(self) -> None:
        request = {
            "messages": [
                {
                    "role": "assistant",
                    "tool_calls": [
                        {
                            "id": "call-1",
                            "type": "function",
                            "function": {"name": "read_file", "arguments": "{"},
                        }
                    ],
                }
            ]
        }

        with self.assertRaisesRegex(ValueError, "valid JSON object"):
            openai_to_bedrock(request, maximum_output_tokens=256)

    def test_normalizes_converse_tool_response_for_openai_client(self) -> None:
        response = {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {"text": "Checking."},
                        {
                            "toolUse": {
                                "toolUseId": "tool-123",
                                "name": "read_file",
                                "input": {"path": "main.py"},
                            }
                        },
                    ],
                }
            },
            "stopReason": "tool_use",
            "usage": {
                "inputTokens": 120,
                "outputTokens": 18,
                "totalTokens": 138,
                "cacheReadInputTokens": 80,
            },
            "metrics": {"latencyMs": 321},
        }

        body, content_type = bedrock_to_openai(
            response,
            model="us.anthropic.claude-sonnet-4-6",
            stream=False,
        )
        normalized = json.loads(body)

        self.assertEqual(content_type, "application/json")
        self.assertEqual(normalized["model"], "us.anthropic.claude-sonnet-4-6")
        self.assertEqual(normalized["choices"][0]["finish_reason"], "tool_calls")
        self.assertEqual(
            normalized["choices"][0]["message"]["tool_calls"][0]["function"],
            {"name": "read_file", "arguments": '{"path":"main.py"}'},
        )
        self.assertEqual(normalized["usage"]["prompt_tokens"], 120)
        self.assertEqual(
            normalized["usage"]["prompt_tokens_details"]["cached_tokens"], 80
        )

    def test_normalizes_converse_response_as_openai_sse(self) -> None:
        response = {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [{"text": "done"}],
                }
            },
            "stopReason": "end_turn",
            "usage": {"inputTokens": 10, "outputTokens": 2, "totalTokens": 12},
        }

        body, content_type = bedrock_to_openai(
            response,
            model="us.anthropic.claude-sonnet-4-6",
            stream=True,
        )

        self.assertEqual(content_type, "text/event-stream")
        self.assertTrue(body.endswith(b"data: [DONE]\n\n"))
        documents = [
            json.loads(line.removeprefix(b"data: "))
            for line in body.splitlines()
            if line.startswith(b"data: {")
        ]
        self.assertEqual(documents[0]["choices"][0]["delta"]["content"], "done")
        self.assertEqual(documents[1]["choices"][0]["finish_reason"], "stop")
        self.assertEqual(documents[1]["usage"]["total_tokens"], 12)


if __name__ == "__main__":
    unittest.main()
