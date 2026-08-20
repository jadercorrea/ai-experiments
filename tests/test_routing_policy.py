import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from routing_policy import (  # noqa: E402
    BackendKind,
    FallbackTrigger,
    PolicyViolation,
    RoutingPolicy,
    RoutingState,
)


class RoutingPolicyTest(unittest.TestCase):
    def test_local_only_rejects_cloud(self) -> None:
        state = RoutingState(RoutingPolicy.LOCAL_ONLY)
        with self.assertRaises(PolicyViolation):
            state.authorize(BackendKind.CLOUD)

    def test_cloud_only_rejects_local(self) -> None:
        state = RoutingState(RoutingPolicy.CLOUD_ONLY)
        with self.assertRaises(PolicyViolation):
            state.authorize(BackendKind.LOCAL)

    def test_local_first_requires_registered_trigger_before_cloud(self) -> None:
        state = RoutingState(RoutingPolicy.LOCAL_FIRST)
        state.authorize(BackendKind.LOCAL)
        with self.assertRaises(PolicyViolation):
            state.authorize(BackendKind.CLOUD)

        transition = state.trigger_fallback(FallbackTrigger.HARD_TIMEOUT)
        state.authorize(BackendKind.CLOUD)

        self.assertEqual(transition.sequence, 1)
        self.assertEqual(transition.trigger, FallbackTrigger.HARD_TIMEOUT)

    def test_local_first_can_fallback_only_once(self) -> None:
        state = RoutingState(RoutingPolicy.LOCAL_FIRST)
        state.trigger_fallback(FallbackTrigger.ATTEMPT_BUDGET_EXHAUSTED)
        with self.assertRaises(PolicyViolation):
            state.trigger_fallback(FallbackTrigger.VERIFICATION_PLATEAU)

    def test_other_policies_cannot_fallback(self) -> None:
        for policy in (RoutingPolicy.LOCAL_ONLY, RoutingPolicy.CLOUD_ONLY):
            with self.subTest(policy=policy):
                state = RoutingState(policy)
                with self.assertRaises(PolicyViolation):
                    state.trigger_fallback(FallbackTrigger.BACKEND_FAILURE)


if __name__ == "__main__":
    unittest.main()
