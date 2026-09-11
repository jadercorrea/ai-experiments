import json
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = (
    ROOT / "experiments" / "coding-agents" / "semantic-ir" / "2026-08-26"
)
INVALID = EXPERIMENT / "observations" / "single-shot-representations-001"
VALID = EXPERIMENT / "observations" / "single-shot-representations-002"
sys.path.insert(0, str(ROOT / "scripts"))

from build_artifact_lock import sha256, verify_lock  # noqa: E402


def read_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_events(path: pathlib.Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
    ]


class SemanticSingleShotObservationTest(unittest.TestCase):
    def test_first_observation_retains_abi_failure(self) -> None:
        invalidation = read_json(INVALID / "invalidation.json")
        response = read_json(
            INVALID / "arms" / "json_ir" / "evidence" / "response.json"
        )
        arguments = json.loads(
            response["choices"][0]["message"]["tool_calls"][0]["function"][
                "arguments"
            ]
        )

        self.assertEqual(
            invalidation["message"],
            "semantic submission rejected: reserved source name: capabilities",
        )
        self.assertEqual(invalidation["completed_arms"], ["source"])
        self.assertEqual(
            [
                parameter["name"]
                for parameter in arguments["program"]["function"]["parameters"]
            ],
            ["rawId", "capabilities"],
        )

    def test_valid_observation_has_one_passing_request_per_arm(self) -> None:
        result = read_json(VALID / "result.json")

        self.assertTrue(result["valid_comparison"])
        for arm_name in ("source", "json_ir", "compact_ir"):
            arm = result["arms"][arm_name]
            self.assertEqual(arm["usage"]["provider_requests"], 1)
            self.assertEqual(arm["submission_attempts"], 1)
            self.assertTrue(arm["public_evaluation"]["passed"])
            self.assertTrue(arm["hidden_evaluation"]["passed"])
            events = [
                event
                for event in read_events(
                    VALID
                    / "arms"
                    / arm_name
                    / "evidence"
                    / "gateway-events.jsonl"
                )
                if event["event"] == "inference"
            ]
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0]["input_tokens"], arm["usage"]["input_tokens"])
            self.assertEqual(
                events[0]["output_tokens"], arm["usage"]["output_tokens"]
            )
            self.assertEqual(events[0]["model"], "us.anthropic.claude-sonnet-4-6")

    def test_messages_are_identical_and_tools_are_forced(self) -> None:
        requests = {
            arm: read_json(VALID / "arms" / arm / "evidence" / "request.json")
            for arm in ("source", "json_ir", "compact_ir")
        }

        self.assertEqual(requests["source"]["messages"], requests["json_ir"]["messages"])
        self.assertEqual(
            requests["source"]["messages"], requests["compact_ir"]["messages"]
        )
        for request in requests.values():
            self.assertEqual(len(request["tools"]), 1)
            self.assertEqual(
                request["tool_choice"]["function"]["name"],
                request["tools"][0]["function"]["name"],
            )
            self.assertNotIn("hidden.test.ts", json.dumps(request))

    def test_checked_measurements_match_retained_result(self) -> None:
        arms = read_json(VALID / "result.json")["arms"]

        self.assertEqual(arms["source"]["usage"]["total_tokens"], 2_009)
        self.assertEqual(arms["json_ir"]["usage"]["total_tokens"], 4_487)
        self.assertEqual(arms["compact_ir"]["usage"]["total_tokens"], 2_022)
        self.assertEqual(arms["source"]["usage"]["output_tokens"], 258)
        self.assertEqual(arms["compact_ir"]["usage"]["output_tokens"], 116)
        self.assertEqual(
            arms["compact_ir"]["materialization"]["transport_bytes"], 175
        )

    def test_valid_observation_retains_exact_executable_sources(self) -> None:
        result = read_json(VALID / "result.json")
        frozen = VALID / "frozen-sources"

        self.assertEqual(
            result["runner_sha256"],
            sha256(frozen / "scripts" / "single_shot_comparison.py"),
        )
        self.assertEqual(result["protocol_sha256"], sha256(VALID / "protocol.json"))

    def test_observation_trees_are_locked(self) -> None:
        for observation in (INVALID, VALID):
            self.assertEqual(
                verify_lock(
                    observation, observation / "publication" / "artifact-lock.json"
                ),
                [],
            )


if __name__ == "__main__":
    unittest.main()
