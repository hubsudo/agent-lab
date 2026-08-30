import unittest

from agent_lab.memory import MemoryStatus, MemoryType


class MemoryTypeTests(unittest.TestCase):
    def test_standard_type_members_and_values(self):
        self.assertEqual(MemoryType.WORKING, "working")
        self.assertEqual(MemoryType.EPISODIC, "episodic")
        self.assertEqual(MemoryType.SEMANTIC, "semantic")
        self.assertEqual(MemoryType.PROCEDURAL, "procedural")

    def test_members_compare_equal_to_plain_strings(self):
        self.assertTrue(MemoryType.EPISODIC == "episodic")
        self.assertEqual(str(MemoryType.SEMANTIC), "semantic")


class MemoryStatusTests(unittest.TestCase):
    def test_status_members_and_values(self):
        self.assertEqual(MemoryStatus.ACTIVE, "active")
        self.assertEqual(MemoryStatus.SUPERSEDED, "superseded")
        self.assertEqual(MemoryStatus.ARCHIVED, "archived")

    def test_deletion_is_not_a_status(self):
        self.assertFalse(hasattr(MemoryStatus, "DELETED"))


if __name__ == "__main__":
    unittest.main()
