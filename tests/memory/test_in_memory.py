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


if __name__ == "__main__":
    unittest.main()
