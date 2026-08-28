"""Business façade for the Phase 01 memory core."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from typing import Mapping

from .models import MemoryItem
from .store import MemoryStore


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MemoryService:
    """Apply memory policies while keeping persistence behind ``MemoryStore``.

    Phase 01 intentionally provides exact filtering only. Relevance search,
    ranking, extraction, and consolidation strategies are introduced in later
    phases without changing this façade's dependency on ``MemoryStore``.
    """

    _UPDATABLE_FIELDS = {
        "content",
        "type",
        "source",
        "valid_at",
        "importance",
        "metadata",
        "provenance",
    }

    def __init__(self, store: MemoryStore) -> None:
        self._store = store

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
        valid_at: datetime | None = None,
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
            valid_at=valid_at,
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
        """Return active memories using stable, exact Phase 01 filters.

        ``importance == 0`` is the Phase 01 soft-forgotten marker. The item
        remains in the store and can be restored with ``update``.
        """

        if limit is not None and limit < 0:
            raise ValueError("limit must be non-negative")

        items = self._store.list()
        if not include_forgotten:
            items = [item for item in items if item.importance > 0]
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
        """Soft-forget a memory by setting its importance to zero."""

        return self.update(item_id, importance=0.0)

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
