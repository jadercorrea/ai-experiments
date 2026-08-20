import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from hosted_budget import (  # noqa: E402
    maximum_requests_for_remaining_budget,
    worst_case_request_cost,
)


class HostedBudgetTest(unittest.TestCase):
    def test_worst_case_cost_uses_locked_context_and_output_limits(self) -> None:
        self.assertAlmostEqual(
            worst_case_request_cost(
                maximum_input_tokens=65_536,
                maximum_output_tokens=64_000,
                input_usd_per_million_tokens=3.0,
                output_usd_per_million_tokens=15.0,
            ),
            1.156608,
        )

    def test_request_cap_cannot_exceed_remaining_campaign_budget(self) -> None:
        cap = maximum_requests_for_remaining_budget(
            remaining_usd=41.15705,
            maximum_input_tokens=65_536,
            maximum_output_tokens=64_000,
            input_usd_per_million_tokens=3.0,
            output_usd_per_million_tokens=15.0,
        )

        self.assertEqual(cap, 35)
        self.assertLessEqual(cap * 1.156608, 41.15705)
        self.assertGreater((cap + 1) * 1.156608, 41.15705)

    def test_exhausted_budget_allows_no_cloud_requests(self) -> None:
        cap = maximum_requests_for_remaining_budget(
            remaining_usd=0,
            maximum_input_tokens=65_536,
            maximum_output_tokens=64_000,
            input_usd_per_million_tokens=3.0,
            output_usd_per_million_tokens=15.0,
        )
        self.assertEqual(cap, 0)


if __name__ == "__main__":
    unittest.main()
