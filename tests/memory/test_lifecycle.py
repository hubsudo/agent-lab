import unittest
from datetime import datetime, timedelta, timezone

from agent_lab.memory import MemoryItem, MemoryStatus, MemoryType


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


class MemoryItemLifecycleTests(unittest.TestCase):
    def test_status_defaults_to_active_and_is_strict(self):
        item = MemoryItem(content="active memory")
        self.assertIs(item.status, MemoryStatus.ACTIVE)

        with self.assertRaises(TypeError):
            MemoryItem(content="bad", status="active")
        with self.assertRaises(TypeError):
            MemoryItem(content="bad", status="deleted")

    def test_type_accepts_enum_members_and_open_strings(self):
        self.assertEqual(
            MemoryItem(content="a", type=MemoryType.EPISODIC).type, "episodic"
        )
        self.assertEqual(MemoryItem(content="b", type="preference").type, "preference")
        self.assertEqual(MemoryItem(content="c").type, "fact")

    def test_forgotten_at_is_normalised_to_utc(self):
        local = datetime(2026, 8, 30, 12, tzinfo=timezone(timedelta(hours=8)))
        item = MemoryItem(content="f", forgotten_at=local)
        self.assertEqual(
            item.forgotten_at, datetime(2026, 8, 30, 4, tzinfo=timezone.utc)
        )

    def test_valid_interval_must_be_ordered(self):
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        end = datetime(2026, 6, 1, tzinfo=timezone.utc)
        item = MemoryItem(content="interval", valid_from=start, valid_until=end)
        self.assertEqual(item.valid_from, start)
        self.assertEqual(item.valid_until, end)

        with self.assertRaises(ValueError):
            MemoryItem(content="inverted", valid_from=end, valid_until=start)

    def test_valid_at_field_no_longer_exists(self):
        with self.assertRaises(TypeError):
            MemoryItem(
                content="legacy", valid_at=datetime(2026, 1, 1, tzinfo=timezone.utc)
            )


if __name__ == "__main__":
    unittest.main()
