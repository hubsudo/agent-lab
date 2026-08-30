import unittest

from agent_lab import (
    InMemoryStore,
    MemoryItem,
    MemoryService,
    MemoryStatus,
    MemoryStore,
    MemoryType,
)


class PublicApiTests(unittest.TestCase):
    def test_public_memory_api_is_importable(self):
        for export in (
            InMemoryStore,
            MemoryItem,
            MemoryService,
            MemoryStatus,
            MemoryStore,
            MemoryType,
        ):
            self.assertIsNotNone(export)


if __name__ == "__main__":
    unittest.main()
