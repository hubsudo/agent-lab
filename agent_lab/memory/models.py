"""Core data models for the memory system.

The model deliberately uses plain Python types so it can be shared by an
in-memory store today and database-backed stores later.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from math import isfinite
from types import MappingProxyType
from typing import Mapping
from uuid import uuid4

from .lifecycle import MemoryStatus


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _normalise_datetime(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _copy_attributes(
    value: Mapping[str, str] | None,
    field_name: str,
) -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise TypeError(f"{field_name} must be a mapping of strings")

    copied = dict(value)
    if not all(
        isinstance(key, str) and isinstance(item, str)
        for key, item in copied.items()
    ):
        raise TypeError(f"{field_name} must contain only string keys and values")
    return copied


@dataclass(frozen=True, slots=True, init=False)
class MemoryItem:
    """A backend-agnostic, immutable unit of agent memory.

    ``MemoryItem`` is immutable so store implementations can safely treat an
    update as replacing one value with another. ``kind`` remains accepted as
    a constructor alias for the original Phase 00 skeleton; ``type`` is the
    canonical field going forward.
    """

    content: str
    type: str = "fact"
    source: str | None = None
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    forgotten_at: datetime | None = None
    status: MemoryStatus = MemoryStatus.ACTIVE
    importance: float = 0.5
    metadata: Mapping[str, str] = field(default_factory=dict)
    provenance: Mapping[str, str] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))

    def __init__(
        self,
        content: str,
        *,
        type: str = "fact",
        source: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        valid_from: datetime | None = None,
        valid_until: datetime | None = None,
        forgotten_at: datetime | None = None,
        status: MemoryStatus = MemoryStatus.ACTIVE,
        importance: float = 0.5,
        metadata: Mapping[str, str] | None = None,
        provenance: Mapping[str, str] | None = None,
        id: str | None = None,
        kind: str | None = None,
    ) -> None:
        if kind is not None:
            if type != "fact" and type != kind:
                raise ValueError("type and kind must match when both are provided")
            type = kind

        if not isinstance(content, str) or not content.strip():
            raise ValueError("content must be a non-empty string")
        if not isinstance(type, str) or not type.strip():
            raise ValueError("type must be a non-empty string")
        if source is not None and (not isinstance(source, str) or not source.strip()):
            raise ValueError("source must be a non-empty string when provided")
        if id is not None and (not isinstance(id, str) or not id.strip()):
            raise ValueError("id must be a non-empty string when provided")
        if not isinstance(importance, (int, float)) or isinstance(importance, bool):
            raise TypeError("importance must be a number between 0 and 1")
        if not isfinite(importance) or not 0 <= importance <= 1:
            raise ValueError("importance must be between 0 and 1")
        if not isinstance(status, MemoryStatus):
            raise TypeError("status must be a MemoryStatus member")

        normalised_created_at = _normalise_datetime(
            created_at or _utc_now(), "created_at"
        )
        normalised_updated_at = _normalise_datetime(
            updated_at or normalised_created_at, "updated_at"
        )
        if normalised_updated_at < normalised_created_at:
            raise ValueError("updated_at must not be earlier than created_at")

        normalised_valid_from = (
            _normalise_datetime(valid_from, "valid_from")
            if valid_from is not None
            else None
        )
        normalised_valid_until = (
            _normalise_datetime(valid_until, "valid_until")
            if valid_until is not None
            else None
        )
        if (
            normalised_valid_from is not None
            and normalised_valid_until is not None
            and normalised_valid_until < normalised_valid_from
        ):
            raise ValueError("valid_until must not be earlier than valid_from")

        normalised_forgotten_at = (
            _normalise_datetime(forgotten_at, "forgotten_at")
            if forgotten_at is not None
            else None
        )

        object.__setattr__(self, "content", content)
        object.__setattr__(self, "type", type)
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "created_at", normalised_created_at)
        object.__setattr__(self, "updated_at", normalised_updated_at)
        object.__setattr__(self, "valid_from", normalised_valid_from)
        object.__setattr__(self, "valid_until", normalised_valid_until)
        object.__setattr__(self, "forgotten_at", normalised_forgotten_at)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "importance", float(importance))
        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(_copy_attributes(metadata, "metadata")),
        )
        object.__setattr__(
            self,
            "provenance",
            MappingProxyType(_copy_attributes(provenance, "provenance")),
        )
        object.__setattr__(self, "id", id or str(uuid4()))

    @property
    def kind(self) -> str:
        """Backward-compatible alias for the pre-Phase 01 field name."""

        return self.type
