"""Business façade for the agent-lab memory system."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from typing import Mapping

from .lifecycle import MemoryStatus
from .models import MemoryItem
from .store import MemoryStore


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MemoryService:
    """Apply memory policies while keeping persistence behind ``MemoryStore``.

    Phase 02 adds lifecycle and forgetting policies on top of exact filtering. Relevance search,
    ranking, extraction, and consolidation strategies are introduced in later
    phases without changing this façade's dependency on ``MemoryStore``.
    """

    _UPDATABLE_FIELDS = {
        "content",
        "type",
        "source",
        "valid_from",
        "valid_until",
        "importance",
        "metadata",
        "provenance",
    }

    def __init__(self, store: MemoryStore) -> None:
        self._store = store

    def _require(self, item_id: str) -> MemoryItem:
        current = self._store.get(item_id)
        if current is None:
            raise KeyError(f"memory item not found: {item_id}")
        return current

    @property
    def store(self) -> MemoryStore:
        """Expose the configured store for composition and diagnostics."""

        return self._store

    def remember(
        self,
        content: str,
        *,
        type: str = "fact",
        source: str | None = None,
        created_at: datetime | None = None,
        valid_from: datetime | None = None,
        importance: float = 0.5,
        metadata: Mapping[str, str] | None = None,
        provenance: Mapping[str, str] | None = None,
        id: str | None = None,
    ) -> MemoryItem:
        """Create a memory item and persist it through the configured store."""

        item = MemoryItem(
            content,
            type=type,
            source=source,
            created_at=created_at,
            valid_from=valid_from,
            importance=importance,
            metadata=metadata,
            provenance=provenance,
            id=id,
        )
        return self._store.add(item)

    def recall(
        self,
        *,
        type: str | None = None,
        source: str | None = None,
        include_forgotten: bool = False,
        limit: int | None = None,
    ) -> list[MemoryItem]:
        """Agent-facing candidate fetch: Phase 01 compat plus basic filters.

        The default view is deterministic only: status ACTIVE, not
        forgotten, and not hidden by the legacy ``importance > 0`` marker
        from Phase 01 (scheduled for removal in Phase 09).
        ``include_forgotten=True`` lifts both the ``forgotten_at`` filter
        and the legacy importance filter, matching Phase 01 semantics. No
        similarity, ranking, or recency here.
        """

        if limit is not None and limit < 0:
            raise ValueError("limit must be non-negative")

        items = self._store.list()
        items = [item for item in items if item.status == MemoryStatus.ACTIVE]
        if not include_forgotten:
            items = [
                item
                for item in items
                if item.forgotten_at is None and item.importance > 0
            ]
        if type is not None:
            items = [item for item in items if item.type == type]
        if source is not None:
            items = [item for item in items if item.source == source]
        if limit is not None:
            items = items[:limit]
        return items

    def update(self, item_id: str, **changes: object) -> MemoryItem:
        """Update mutable fields while preserving identity and creation time."""

        if "kind" in changes:
            if "type" in changes and changes["type"] != changes["kind"]:
                raise ValueError("type and kind must match when both are provided")
            changes["type"] = changes.pop("kind")

        unsupported = set(changes) - self._UPDATABLE_FIELDS
        if unsupported:
            names = ", ".join(sorted(unsupported))
            raise TypeError(f"unsupported memory update fields: {names}")

        current = self._store.get(item_id)
        if current is None:
            raise KeyError(f"memory item not found: {item_id}")
        if not changes:
            return current

        updated = replace(current, **changes, updated_at=_utc_now())
        return self._store.update(updated)

    def forget(self, item_id: str) -> MemoryItem:
        """Mark a memory forgotten; the canonical marker is ``forgotten_at``.

        Repeated calls refresh the marker. Importance and status are
        untouched — importance expresses value, not forgetting.
        """

        current = self._require(item_id)
        now = _utc_now()
        updated = replace(current, forgotten_at=now, updated_at=now)
        return self._store.update(updated)

    def unforget(self, item_id: str) -> MemoryItem:
        """Clear the forgotten marker; idempotent for non-forgotten items."""

        current = self._require(item_id)
        if current.forgotten_at is None:
            return current
        updated = replace(current, forgotten_at=None, updated_at=_utc_now())
        return self._store.update(updated)

    def delete(self, item_id: str) -> bool:
        """Permanently remove a memory item from the store."""

        return self._store.delete(item_id)

    def consolidate(self) -> list[MemoryItem]:
        """Declare the consolidation boundary for a later phase.

        Consolidation needs an explicit deduplication, conflict-resolution, or
        summarization policy. Phase 01 does not guess one; Phase 08 will add a
        strategy behind this stable service entry point.
        """

        raise NotImplementedError(
            "consolidation policy is intentionally deferred to Phase 08"
        )
