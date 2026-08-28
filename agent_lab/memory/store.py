from typing import Protocol, runtime_checkable

from .models import MemoryItem


@runtime_checkable
class MemoryStore(Protocol):
    """Persistence boundary for memory items.

    Implementations own storage concerns only. Business policies such as
    forgetting and consolidation belong in ``MemoryService``.
    """

    def add(self, item: MemoryItem) -> MemoryItem: ...

    def get(self, item_id: str) -> MemoryItem | None: ...

    def update(self, item: MemoryItem) -> MemoryItem: ...

    def delete(self, item_id: str) -> bool: ...

    def list(self) -> list[MemoryItem]: ...
