from .models import MemoryItem


class InMemoryStore:
    """Ordered in-memory implementation of the ``MemoryStore`` contract."""

    def __init__(self) -> None:
        self._items: dict[str, MemoryItem] = {}

    def add(self, item: MemoryItem) -> MemoryItem:
        if item.id in self._items:
            raise ValueError(f"memory item already exists: {item.id}")
        self._items[item.id] = item
        return item

    def get(self, item_id: str) -> MemoryItem | None:
        return self._items.get(item_id)

    def update(self, item: MemoryItem) -> MemoryItem:
        if item.id not in self._items:
            raise KeyError(f"memory item not found: {item.id}")
        self._items[item.id] = item
        return item

    def delete(self, item_id: str) -> bool:
        return self._items.pop(item_id, None) is not None

    def list(self) -> list[MemoryItem]:
        return list(self._items.values())
