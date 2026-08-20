#!/usr/bin/env python3
"""Deterministic routing-policy state for the local-first experiment."""

from dataclasses import dataclass, field
from enum import StrEnum


class RoutingPolicy(StrEnum):
    LOCAL_ONLY = "local-only"
    CLOUD_ONLY = "cloud-only"
    LOCAL_FIRST = "local-first"


class BackendKind(StrEnum):
    LOCAL = "local"
    CLOUD = "cloud"


class FallbackTrigger(StrEnum):
    HARD_TIMEOUT = "hard_timeout"
    ATTEMPT_BUDGET_EXHAUSTED = "attempt_budget_exhausted"
    VERIFICATION_PLATEAU = "verification_plateau"
    BACKEND_FAILURE = "backend_failure"
    NO_MATERIAL_PATCH = "no_material_patch"
    PUBLIC_VERIFICATION_FAILED = "public_verification_failed"


class PolicyViolation(RuntimeError):
    pass


@dataclass(frozen=True)
class PolicyTransition:
    sequence: int
    source: BackendKind
    destination: BackendKind
    trigger: FallbackTrigger


@dataclass
class RoutingState:
    policy: RoutingPolicy
    transitions: list[PolicyTransition] = field(default_factory=list)

    @property
    def fallback_active(self) -> bool:
        return bool(self.transitions)

    def authorize(self, backend: BackendKind) -> None:
        allowed = {
            RoutingPolicy.LOCAL_ONLY: {BackendKind.LOCAL},
            RoutingPolicy.CLOUD_ONLY: {BackendKind.CLOUD},
            RoutingPolicy.LOCAL_FIRST: (
                {BackendKind.CLOUD} if self.fallback_active else {BackendKind.LOCAL}
            ),
        }[self.policy]
        if backend not in allowed:
            raise PolicyViolation(
                f"backend {backend} is forbidden by {self.policy} in current state"
            )

    def trigger_fallback(self, trigger: FallbackTrigger) -> PolicyTransition:
        if self.policy is not RoutingPolicy.LOCAL_FIRST:
            raise PolicyViolation(f"{self.policy} does not permit fallback")
        if self.transitions:
            raise PolicyViolation("local-first fallback may occur only once")
        transition = PolicyTransition(
            sequence=1,
            source=BackendKind.LOCAL,
            destination=BackendKind.CLOUD,
            trigger=trigger,
        )
        self.transitions.append(transition)
        return transition
