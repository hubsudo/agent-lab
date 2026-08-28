import unittest

from agent_lab.memory import InMemoryStore, MemoryItem


class InMemoryStoreTests(unittest.TestCase):
    def test_add_and_get_memory_item(self):
        store = InMemoryStore()
        item = MemoryItem(content="User prefers concise answers", kind="preference")

        store.add(item)

        self.assertEqual(store.get(item.id), item)

    def test_list_returns_items_in_insertion_order(self):
        store = InMemoryStore()
        first = MemoryItem(content="first", kind="fact")
        second = MemoryItem(content="second", kind="fact")

        store.add(first)
        store.add(second)

        self.assertEqual(store.list(), [first, second])

    def test_delete_removes_existing_item_and_is_idempotent(self):
        store = InMemoryStore()
        item = MemoryItem(content="temporary", kind="fact")
        store.add(item)

        self.assertTrue(store.delete(item.id))
        self.assertIsNone(store.get(item.id))
        self.assertFalse(store.delete(item.id))

    def test_add_rejects_duplicate_ids(self):
        store = InMemoryStore()
        item = MemoryItem(content="one", id="memory-1")
        store.add(item)

        with self.assertRaises(ValueError):
            store.add(MemoryItem(content="two", id="memory-1"))

    def test_update_replaces_item_without_changing_its_position(self):
        store = InMemoryStore()
        first = MemoryItem(content="first")
        second = MemoryItem(content="second")
        store.add(first)
        store.add(second)

        updated = MemoryItem(content="updated", id=first.id)
        self.assertEqual(store.update(updated), updated)
        self.assertEqual(store.list(), [updated, second])

    def test_update_requires_an_existing_item(self):
        store = InMemoryStore()

        with self.assertRaises(KeyError):
            store.update(MemoryItem(content="missing", id="missing"))


if __name__ == "__main__":
    unittest.main()
