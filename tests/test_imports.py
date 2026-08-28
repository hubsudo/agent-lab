import unittest

from agent_lab import InMemoryStore, MemoryItem, MemoryService, MemoryStore


class PublicApiTests(unittest.TestCase):
    def test_public_memory_api_is_importable(self):
        self.assertIsNotNone(InMemoryStore)
        self.assertIsNotNone(MemoryItem)
        self.assertIsNotNone(MemoryService)
        self.assertIsNotNone(MemoryStore)


if __name__ == "__main__":
    unittest.main()
