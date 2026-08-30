"""Memory type and lifecycle status definitions for Phase 02."""

from __future__ import annotations

from enum import StrEnum
from types import MappingProxyType


class MemoryType(StrEnum):
    """Standard memory types; ``MemoryItem.type`` also accepts open strings."""

    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"


class MemoryStatus(StrEnum):
    """Lifecycle states a memory can hold while present in a store.

    Deletion is a store operation, not a state: deleted memories are
    physically removed, so no DELETED member exists.
    """

    ACTIVE = "active"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


_TRANSITIONS: MappingProxyType[MemoryStatus, frozenset[MemoryStatus]] = MappingProxyType(
    {
        MemoryStatus.ACTIVE: frozenset(
            {MemoryStatus.SUPERSEDED, MemoryStatus.ARCHIVED}
        ),
        MemoryStatus.SUPERSEDED: frozenset(),
        MemoryStatus.ARCHIVED: frozenset({MemoryStatus.ACTIVE}),
    }
)


def is_valid_transition(current: MemoryStatus, target: MemoryStatus) -> bool:
    """Return whether ``current -> target`` is an allowed status change."""

    return target in _TRANSITIONS[current]
