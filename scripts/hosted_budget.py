#!/usr/bin/env python3
"""Conservative hosted-request bounds for a hard campaign spending cap."""

import math


def worst_case_request_cost(
    *,
    maximum_input_tokens: int,
    maximum_output_tokens: int,
    input_usd_per_million_tokens: float,
    output_usd_per_million_tokens: float,
) -> float:
    if maximum_input_tokens <= 0 or maximum_output_tokens <= 0:
        raise ValueError("token limits must be positive")
    if input_usd_per_million_tokens < 0 or output_usd_per_million_tokens < 0:
        raise ValueError("token prices cannot be negative")
    return (
        maximum_input_tokens * input_usd_per_million_tokens
        + maximum_output_tokens * output_usd_per_million_tokens
    ) / 1_000_000


def maximum_requests_for_remaining_budget(
    *,
    remaining_usd: float,
    maximum_input_tokens: int,
    maximum_output_tokens: int,
    input_usd_per_million_tokens: float,
    output_usd_per_million_tokens: float,
) -> int:
    if remaining_usd <= 0:
        return 0
    request_cost = worst_case_request_cost(
        maximum_input_tokens=maximum_input_tokens,
        maximum_output_tokens=maximum_output_tokens,
        input_usd_per_million_tokens=input_usd_per_million_tokens,
        output_usd_per_million_tokens=output_usd_per_million_tokens,
    )
    if request_cost <= 0:
        raise ValueError("worst-case request cost must be positive")
    return math.floor(remaining_usd / request_cost)
