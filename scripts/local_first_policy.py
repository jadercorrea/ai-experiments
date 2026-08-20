#!/usr/bin/env python3
"""Frozen deterministic decision rule for the local-first calibration arm."""

from dataclasses import asdict, dataclass
from enum import StrEnum

from routing_policy import FallbackTrigger


class RouteDecision(StrEnum):
    ACCEPT_LOCAL = "accept_local"
    ESCALATE_CLOUD = "escalate_cloud"


@dataclass(frozen=True)
class LocalStageOutcome:
    timed_out: bool
    agent_exit_code: int | None
    material_patch: bool
    public_test_exit_codes: tuple[int, ...]
    inference_failures: int


@dataclass(frozen=True)
class RoutingDecision:
    route: RouteDecision
    trigger: FallbackTrigger | None


def decide_route(outcome: LocalStageOutcome) -> RoutingDecision:
    """Apply the preregistered observable-signal precedence."""
    if outcome.timed_out:
        trigger = FallbackTrigger.HARD_TIMEOUT
    elif outcome.inference_failures or outcome.agent_exit_code != 0:
        trigger = FallbackTrigger.BACKEND_FAILURE
    elif not outcome.material_patch:
        trigger = FallbackTrigger.NO_MATERIAL_PATCH
    elif not outcome.public_test_exit_codes or any(outcome.public_test_exit_codes):
        trigger = FallbackTrigger.PUBLIC_VERIFICATION_FAILED
    else:
        return RoutingDecision(RouteDecision.ACCEPT_LOCAL, None)
    return RoutingDecision(RouteDecision.ESCALATE_CLOUD, trigger)


def router_report(
    decision: RoutingDecision, outcome: LocalStageOutcome
) -> dict[str, object]:
    """Return the fixed content-free report supplied to a fresh cloud agent."""
    local_stage = asdict(outcome)
    local_stage["public_test_exit_codes"] = list(outcome.public_test_exit_codes)
    return {
        "schema_version": "ai-experiments.router-report/v1",
        "decision": decision.route.value,
        "trigger": decision.trigger.value if decision.trigger else None,
        "local_stage": local_stage,
    }
