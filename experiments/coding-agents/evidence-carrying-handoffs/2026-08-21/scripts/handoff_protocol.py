#!/usr/bin/env python3
"""Validate deterministic handoff schemas and evidence references."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
from typing import Any, Iterable

import jsonschema


EXPERIMENT_ROOT = pathlib.Path(__file__).resolve().parents[1]
PROTOCOL_ROOT = EXPERIMENT_ROOT / "protocol"
PROHIBITED_PAYLOAD_FIELDS = {
    "chain_of_thought",
    "reasoning",
    "reasoning_content",
    "thinking",
    "thoughts",
}
EVIDENCE_COLLECTIONS = (
    "files_inspected",
    "commands_run",
    "observations",
    "hypotheses_rejected",
    "unresolved_failures",
    "redactions",
)


class ProtocolValidationError(ValueError):
    """Raised when cross-artifact protocol invariants fail."""


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def event_content_sha256(event: dict[str, Any]) -> str:
    digest_input = copy.deepcopy(event)
    digest_input.pop("content_sha256", None)
    return canonical_sha256(digest_input)


def _walk_keys(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for key, nested in value.items():
            yield key
            yield from _walk_keys(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _walk_keys(nested)


def validate_event_semantics(event: dict[str, Any]) -> None:
    prohibited = sorted(
        PROHIBITED_PAYLOAD_FIELDS.intersection(_walk_keys(event["payload"]))
    )
    if prohibited:
        raise ProtocolValidationError(
            f"prohibited field in normalized payload: {', '.join(prohibited)}"
        )

    if event["phase"] == "hidden_evaluation" and event["visibility"] != "restricted":
        raise ProtocolValidationError(
            "hidden evaluator events must remain restricted from participants and publication"
        )

    linguistic_metadata = event["linguistic_metadata"]
    primary_language = linguistic_metadata["primary_language"]
    detected_languages = linguistic_metadata["detected_languages"]
    mixed_language = linguistic_metadata["mixed_language"]
    if mixed_language != (len(detected_languages) > 1):
        raise ProtocolValidationError(
            f"inconsistent language mixing metadata: {event['event_id']}"
        )
    if primary_language == "und" and detected_languages:
        raise ProtocolValidationError(
            f"undetermined primary language has detected languages: {event['event_id']}"
        )
    if primary_language != "und" and primary_language not in detected_languages:
        raise ProtocolValidationError(
            f"primary language is absent from detected languages: {event['event_id']}"
        )

    if event["content_sha256"] != event_content_sha256(event):
        raise ProtocolValidationError(
            f"event content digest mismatch: {event['event_id']}"
        )


def _referenced_event_ids(bundle: dict[str, Any]) -> set[str]:
    references: set[str] = set()
    for collection in EVIDENCE_COLLECTIONS:
        for item in bundle[collection]:
            references.update(item["evidence_refs"])
    return references


def validate_bundle_semantics(
    bundle: dict[str, Any],
    events: Iterable[dict[str, Any]],
    *,
    verify_bundle_digest: bool = True,
) -> None:
    language_policy = bundle["language_policy"]
    realization_language = language_policy["realization_language"]
    trace_languages = set(language_policy["trace_languages"])
    sender_output_language = language_policy["sender_output_language"]
    if sender_output_language not in trace_languages:
        raise ProtocolValidationError(
            "sender output language is absent from trace language policy"
        )
    for collection in (
        "observations",
        "hypotheses_rejected",
        "unresolved_failures",
    ):
        for item in bundle[collection]:
            realization_languages = [
                realization["language"] for realization in item["realizations"]
            ]
            if len(realization_languages) != len(set(realization_languages)):
                raise ProtocolValidationError(
                    f"duplicate realization language in {collection}"
                )
            if realization_language not in realization_languages:
                raise ProtocolValidationError(
                    f"{collection} omits declared realization language: "
                    f"{realization_language}"
                )

    events_by_id: dict[str, dict[str, Any]] = {}
    for event in events:
        validate_event_semantics(event)
        linguistic_metadata = event["linguistic_metadata"]
        undeclared_languages = set(
            linguistic_metadata["detected_languages"]
        ).difference(trace_languages)
        if undeclared_languages:
            raise ProtocolValidationError(
                "event language is absent from trace language policy: "
                f"{event['event_id']} ({', '.join(sorted(undeclared_languages))})"
            )
        if (
            language_policy["mixed_language_policy"] == "reject"
            and linguistic_metadata["mixed_language"]
        ):
            raise ProtocolValidationError(
                f"mixed-language event rejected by policy: {event['event_id']}"
            )
        event_id = event["event_id"]
        if event_id in events_by_id:
            raise ProtocolValidationError(f"duplicate event id: {event_id}")
        events_by_id[event_id] = event

    catalog: dict[str, str] = {}
    for evidence in bundle["integrity"]["evidence"]:
        event_id = evidence["event_id"]
        if event_id in catalog:
            raise ProtocolValidationError(f"duplicate evidence catalog id: {event_id}")
        catalog[event_id] = evidence["content_sha256"]

    references = _referenced_event_ids(bundle)
    unknown = sorted(references.difference(events_by_id))
    if unknown:
        raise ProtocolValidationError(
            f"unknown evidence reference(s): {', '.join(unknown)}"
        )

    missing_catalog = sorted(references.difference(catalog))
    if missing_catalog:
        raise ProtocolValidationError(
            f"evidence reference missing from integrity catalog: {', '.join(missing_catalog)}"
        )

    for event_id, recorded_digest in catalog.items():
        event = events_by_id.get(event_id)
        if event is None:
            raise ProtocolValidationError(
                f"catalog references unknown evidence: {event_id}"
            )
        if recorded_digest != event["content_sha256"]:
            raise ProtocolValidationError(f"evidence digest mismatch: {event_id}")

    if verify_bundle_digest:
        digest_input = copy.deepcopy(bundle)
        recorded_digest = digest_input["integrity"].pop("bundle_sha256")
        if recorded_digest != canonical_sha256(digest_input):
            raise ProtocolValidationError("bundle digest mismatch")


def _load_json(path: pathlib.Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _load_jsonl(path: pathlib.Path) -> list[dict[str, Any]]:
    events = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise ProtocolValidationError(
                    f"invalid JSONL at {path}:{line_number}: {error.msg}"
                ) from error
    return events


def validate_files(bundle_path: pathlib.Path, events_path: pathlib.Path) -> None:
    bundle_schema = _load_json(PROTOCOL_ROOT / "handoff-bundle-v1.schema.json")
    event_schema = _load_json(PROTOCOL_ROOT / "normalized-event-v1.schema.json")
    bundle = _load_json(bundle_path)
    events = _load_jsonl(events_path)

    event_validator = jsonschema.Draft202012Validator(
        event_schema,
        format_checker=jsonschema.FormatChecker(),
    )
    for event in events:
        event_validator.validate(event)
    jsonschema.Draft202012Validator(bundle_schema).validate(bundle)
    validate_bundle_semantics(bundle, events)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=pathlib.Path)
    parser.add_argument("events", type=pathlib.Path)
    args = parser.parse_args()
    validate_files(args.bundle, args.events)
    print("handoff protocol validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
