import unittest
from datetime import datetime, timedelta, timezone

from agent_lab.memory import InMemoryStore, MemoryItem, MemoryService


class MemoryItemTests(unittest.TestCase):
    def test_model_contains_extensible_core_fields(self):
        source_metadata = {"workspace": "agent-lab"}
        source_provenance = {"conversation_id": "conversation-1"}
        item = MemoryItem(
            content="User prefers concise answers",
            type="preference",
            source="conversation",
            importance=0.8,
            metadata=source_metadata,
            provenance=source_provenance,
        )

        self.assertTrue(item.id)
        self.assertEqual(item.type, "preference")
        self.assertEqual(item.source, "conversation")
        self.assertEqual(item.metadata, source_metadata)
        self.assertEqual(item.provenance, source_provenance)
        self.assertIsNone(item.valid_at)
        self.assertIsNotNone(item.created_at.tzinfo)
        self.assertEqual(item.created_at.tzinfo, timezone.utc)
        self.assertEqual(item.updated_at, item.created_at)

        source_metadata["changed"] = "outside"
        source_provenance["changed"] = "outside"
        self.assertNotIn("changed", item.metadata)
        self.assertNotIn("changed", item.provenance)

    def test_metadata_and_provenance_are_immutable_snapshots(self):
        item = MemoryItem(
            content="stable",
            metadata={"key": "value"},
            provenance={"source_id": "source-1"},
        )

        with self.assertRaises(TypeError):
            item.metadata["key"] = "changed"
        with self.assertRaises(TypeError):
            item.provenance["source_id"] = "changed"

    def test_kind_is_a_backward_compatible_alias_for_type(self):
        item = MemoryItem(content="legacy", kind="preference")

        self.assertEqual(item.type, "preference")
        self.assertEqual(item.kind, "preference")

    def test_datetimes_are_normalised_to_utc(self):
        local_time = datetime(2026, 8, 28, 12, tzinfo=timezone(timedelta(hours=8)))
        item = MemoryItem(content="scheduled", created_at=local_time)

        self.assertEqual(item.created_at, datetime(2026, 8, 28, 4, tzinfo=timezone.utc))

    def test_model_rejects_invalid_core_values(self):
        with self.assertRaises(ValueError):
            MemoryItem(content="   ")
        with self.assertRaises(ValueError):
            MemoryItem(content="invalid", importance=1.1)
        with self.assertRaises(ValueError):
            MemoryItem(content="invalid", created_at=datetime.now())


class MemoryServiceTests(unittest.TestCase):
    def setUp(self):
        self.store = InMemoryStore()
        self.service = MemoryService(self.store)

    def test_remember_creates_and_persists_a_memory(self):
        item = self.service.remember(
            "User likes Python",
            type="preference",
            source="conversation",
            metadata={"topic": "programming"},
            provenance={"message_id": "message-1"},
        )

        self.assertIs(self.store.get(item.id), item)
        self.assertEqual(self.service.recall(), [item])

    def test_recall_supports_exact_filters_and_excludes_forgotten(self):
        preference = self.service.remember(
            "User likes Python", type="preference", source="conversation"
        )
        self.service.remember("User is in Shanghai", type="fact", source="profile")
        forgotten = self.service.remember("Temporary context", type="context")
        self.service.forget(forgotten.id)

        self.assertEqual(self.service.recall(type="preference"), [preference])
        self.assertEqual(self.service.recall(source="profile")[0].type, "fact")
        self.assertNotIn(forgotten.id, [item.id for item in self.service.recall()])
        self.assertIn(
            forgotten.id,
            [item.id for item in self.service.recall(include_forgotten=True)],
        )

    def test_update_preserves_identity_and_creation_time(self):
        item = self.service.remember("old", importance=0.4)

        updated = self.service.update(
            item.id,
            content="new",
            type="fact",
            metadata={"updated": "yes"},
        )

        self.assertEqual(updated.id, item.id)
        self.assertEqual(updated.created_at, item.created_at)
        self.assertGreaterEqual(updated.updated_at, item.updated_at)
        self.assertEqual(updated.content, "new")
        self.assertEqual(updated.metadata, {"updated": "yes"})

    def test_update_rejects_identity_and_unknown_changes(self):
        item = self.service.remember("stable")

        with self.assertRaises(TypeError):
            self.service.update(item.id, id="new-id")
        with self.assertRaises(TypeError):
            self.service.update(item.id, unknown="value")

    def test_forget_is_reversible_and_delete_is_permanent(self):
        item = self.service.remember("temporary", importance=0.7)

        forgotten = self.service.forget(item.id)
        self.assertEqual(forgotten.importance, 0.0)
        self.assertIs(self.store.get(item.id), forgotten)

        restored = self.service.update(item.id, importance=0.6)
        self.assertEqual(self.service.recall(), [restored])
        self.assertTrue(self.service.delete(item.id))
        self.assertIsNone(self.store.get(item.id))

    def test_missing_items_and_invalid_limits_are_reported(self):
        with self.assertRaises(KeyError):
            self.service.update("missing", content="value")
        with self.assertRaises(KeyError):
            self.service.forget("missing")
        with self.assertRaises(ValueError):
            self.service.recall(limit=-1)

    def test_consolidation_is_explicitly_deferred(self):
        with self.assertRaises(NotImplementedError):
            self.service.consolidate()


if __name__ == "__main__":
    unittest.main()
