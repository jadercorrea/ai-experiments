#!/usr/bin/env python3
"""Protocol-v1 semantics with cohort-total observation lexicalization."""

from __future__ import annotations

from typing import Any

from representational_confirmatory_protocol_v1 import ReducedConfirmatorySession
from representational_observation_codec_v1 import (
    decode_observation,
    encode_observation,
)


class LexicallyTotalReducedConfirmatorySession(ReducedConfirmatorySession):
    """Keep protocol-v1 state semantics while selecting the v1 observation codec."""

    def _inspect(self, handles: list[Any]) -> dict[str, Any]:
        canonical = self._store.inspect(handles)
        return encode_observation(
            canonical,
            lexicon=self._condition.lexicon,
            packaging=self._condition.packaging,
        )

    def decode_condition_observation(
        self, realization: dict[str, Any]
    ) -> dict[str, Any]:
        return decode_observation(
            realization,
            lexicon=self._condition.lexicon,
            packaging=self._condition.packaging,
        )
