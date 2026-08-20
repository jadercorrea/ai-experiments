import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from local_first_policy import (  # noqa: E402
    LocalStageOutcome,
    RouteDecision,
    decide_route,
    router_report,
)
from routing_policy import FallbackTrigger  # noqa: E402


class LocalFirstPolicyTest(unittest.TestCase):
    def test_accepts_only_normal_material_publicly_verified_patch(self) -> None:
        outcome = LocalStageOutcome(
            timed_out=False,
            agent_exit_code=0,
            material_patch=True,
            public_test_exit_codes=(0, 0),
            inference_failures=0,
        )

        decision = decide_route(outcome)

        self.assertEqual(decision.route, RouteDecision.ACCEPT_LOCAL)
        self.assertIsNone(decision.trigger)

    def test_timeout_escalates_before_other_signals(self) -> None:
        outcome = LocalStageOutcome(
            timed_out=True,
            agent_exit_code=None,
            material_patch=False,
            public_test_exit_codes=(),
            inference_failures=1,
        )

        decision = decide_route(outcome)

        self.assertEqual(decision.route, RouteDecision.ESCALATE_CLOUD)
        self.assertEqual(decision.trigger, FallbackTrigger.HARD_TIMEOUT)

    def test_backend_failure_escalates(self) -> None:
        outcome = LocalStageOutcome(False, 1, True, (0,), 1)
        self.assertEqual(
            decide_route(outcome).trigger,
            FallbackTrigger.BACKEND_FAILURE,
        )

    def test_empty_patch_escalates(self) -> None:
        outcome = LocalStageOutcome(False, 0, False, (), 0)
        self.assertEqual(
            decide_route(outcome).trigger,
            FallbackTrigger.NO_MATERIAL_PATCH,
        )

    def test_public_verification_failure_escalates(self) -> None:
        outcome = LocalStageOutcome(False, 0, True, (0, 1), 0)
        self.assertEqual(
            decide_route(outcome).trigger,
            FallbackTrigger.PUBLIC_VERIFICATION_FAILED,
        )

    def test_router_report_contains_signals_but_not_local_patch_content(self) -> None:
        outcome = LocalStageOutcome(False, 0, True, (1,), 0)
        report = router_report(decide_route(outcome), outcome)

        self.assertEqual(report["decision"], "escalate_cloud")
        self.assertEqual(report["trigger"], "public_verification_failed")
        self.assertEqual(report["local_stage"]["public_test_exit_codes"], [1])
        self.assertNotIn("patch", report)


if __name__ == "__main__":
    unittest.main()
