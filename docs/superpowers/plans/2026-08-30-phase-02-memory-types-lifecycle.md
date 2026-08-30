# Phase 02 — Memory Types & Lifecycle 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 按 spec（`docs/memory-system-spec.md`，Phase 02 版本）实现 MemoryType/MemoryStatus、生命周期转换、遗忘维度（`forgotten_at`）与 `MemoryService` 领域操作（get/list/archive/restore/unforget/supersede）。

**Architecture:** 新增 `agent_lab/memory/lifecycle.py`（枚举 + 转换规则），扩展 `models.py`（status / valid_from / valid_until / forgotten_at），`service.py` 承载全部领域操作；`store.py` / `in_memory.py` 不变。依赖单向：Service → Store / Models / Lifecycle。

**Tech Stack:** Python 3.12+ 标准库（`enum.StrEnum`、`dataclasses`、`unittest`），零第三方依赖。

**Spec:** `docs/memory-system-spec.md`（commits `3830e4b` / `34b4dbb` / `1ba81e1`），已获用户批准。spec 优先于本计划——若实现中发现冲突，停下与用户确认。

---

## 环境说明

- 本机当前没有 `uv`（README 的标准流程是 `./scripts/check.sh`）。计划中的命令统一使用 `python3 -m unittest ...`（系统 Python 3.13，项目零依赖，等价有效）。若执行时 `uv` 可用，优先用 `./scripts/check.sh` 作为最终验证。
- 所有命令在仓库根目录 `/Users/chenrunhuan/work/repo/agent-lab` 执行。
- 执行前可按 `superpowers:using-git-worktrees` 创建隔离工作区；spec 提交已在 `main` 上，实现提交同样落在当前分支即可。

## 文件结构

| 文件 | 动作 | 职责 |
| --- | --- | --- |
| `agent_lab/memory/lifecycle.py` | 新建 | `MemoryType`、`MemoryStatus`、转换表与校验 |
| `agent_lab/memory/models.py` | 修改 | `MemoryItem` 新增 status / valid_from / valid_until / forgotten_at，重命名 valid_at |
| `agent_lab/memory/service.py` | 修改 | get / list / recall / update / forget / unforget / archive / restore / supersede |
| `agent_lab/memory/__init__.py` | 修改 | 导出 MemoryType / MemoryStatus |
| `agent_lab/__init__.py` | 修改 | 顶层重导出 |
| `tests/memory/test_lifecycle.py` | 新建 | 枚举与 MemoryItem 新契约测试 |
| `tests/memory/test_service.py` | 修改 | 服务层测试（含 Phase 01 契约更新与回滚测试） |
| `tests/test_imports.py` | 修改 | 公共 API 导入测试 |
| `README.md` | 修改 | roadmap 第 2 条对齐 Phase 02 |

---

### Task 1: lifecycle 枚举与导出

**Files:**
- Create: `agent_lab/memory/lifecycle.py`
- Modify: `agent_lab/memory/__init__.py`（整文件替换）
- Modify: `agent_lab/__init__.py`（整文件替换）
- Modify: `tests/test_imports.py`（整文件替换）
- Test: `tests/memory/test_lifecycle.py`（新建，先写枚举部分）

- [ ] **Step 1: 写失败测试**

创建 `tests/memory/test_lifecycle.py`：

```python
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
```

- [ ] **Step 2: 运行验证失败**

Run: `python3 -m unittest tests.memory.test_lifecycle -v`
Expected: FAIL — `ImportError: cannot import name 'MemoryStatus' from 'agent_lab.memory'`

- [ ] **Step 3: 实现 lifecycle.py**

创建 `agent_lab/memory/lifecycle.py`：

```python
"""Memory type and lifecycle status definitions for Phase 02."""

from __future__ import annotations

from enum import StrEnum


class MemoryType(StrEnum):
    """Standard memory types; ``MemoryItem.type`` also accepts open strings."""

    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"


class MemoryStatus(StrEnum):
    """Lifecycle states a memory can hold while present in a store.

    Deletion is a store operation, not a state: deleted memories are
    physically removed, so no DELETED member exists.
    """

    ACTIVE = "active"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


_TRANSITIONS: dict[MemoryStatus, frozenset[MemoryStatus]] = {
    MemoryStatus.ACTIVE: frozenset(
        {MemoryStatus.SUPERSEDED, MemoryStatus.ARCHIVED}
    ),
    MemoryStatus.SUPERSEDED: frozenset(),
    MemoryStatus.ARCHIVED: frozenset({MemoryStatus.ACTIVE}),
}


def is_valid_transition(current: MemoryStatus, target: MemoryStatus) -> bool:
    """Return whether ``current -> target`` is an allowed status change."""

    return target in _TRANSITIONS[current]
```

- [ ] **Step 4: 更新导出**

替换 `agent_lab/memory/__init__.py` 全文：

```python
from .in_memory import InMemoryStore
from .lifecycle import MemoryStatus, MemoryType
from .models import MemoryItem
from .service import MemoryService
from .store import MemoryStore

__all__ = [
    "InMemoryStore",
    "MemoryItem",
    "MemoryService",
    "MemoryStatus",
    "MemoryStore",
    "MemoryType",
]
```

替换 `agent_lab/__init__.py` 全文：

```python
"""Learning primitives for AI agent systems."""

from .memory import (
    InMemoryStore,
    MemoryItem,
    MemoryService,
    MemoryStatus,
    MemoryStore,
    MemoryType,
)

__all__ = [
    "InMemoryStore",
    "MemoryItem",
    "MemoryService",
    "MemoryStatus",
    "MemoryStore",
    "MemoryType",
]
```

替换 `tests/test_imports.py` 全文：

```python
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
```

- [ ] **Step 5: 运行验证通过**

Run: `python3 -m unittest tests.memory.test_lifecycle tests.test_imports -v`
Expected: PASS（6 个测试）

- [ ] **Step 6: 全量回归**

Run: `python3 -m unittest discover -s tests -v`
Expected: OK，全部通过（Phase 01 测试不受影响）

- [ ] **Step 7: Commit**

```bash
git add agent_lab/memory/lifecycle.py agent_lab/memory/__init__.py agent_lab/__init__.py tests/test_imports.py tests/memory/test_lifecycle.py
git commit -m "feat: MemoryType and MemoryStatus lifecycle enums"
```

---

### Task 2: MemoryItem 扩展（status / valid_from / valid_until / forgotten_at）

`valid_at` 重命名为 `valid_from` 并新增 `valid_until`、`forgotten_at`、`status`。service 的机械重命名随本任务完成，保证全量测试始终绿色（除被更新的那一条断言）。

**Files:**
- Modify: `agent_lab/memory/models.py`（整文件替换）
- Modify: `agent_lab/memory/lifecycle.py`（`_TRANSITIONS` 只读化，评审建议）
- Modify: `agent_lab/memory/service.py:25-33`（`_UPDATABLE_FIELDS`）、`service.py:51`、`service.py:64`（valid_at → valid_from）
- Modify: `tests/memory/test_service.py:25`
- Test: `tests/memory/test_lifecycle.py`（追加模型测试）

- [ ] **Step 1: 更新既有断言 + 写失败测试**

`tests/memory/test_service.py:25` 的 `self.assertIsNone(item.valid_at)` 改为：

```python
        self.assertIsNone(item.valid_from)
```

在 `tests/memory/test_lifecycle.py` 中，将 import 头改为：

```python
import unittest
from datetime import datetime, timedelta, timezone

from agent_lab.memory import MemoryItem, MemoryStatus, MemoryType
```

并追加测试类（放在 `MemoryStatusTests` 之后、`if __name__` 之前）：

```python
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
```

- [ ] **Step 2: 运行验证失败**

Run: `python3 -m unittest tests.memory.test_lifecycle -v`
Expected: FAIL — `TypeError: status must be a MemoryStatus member` 之前先出现 AttributeError/TypeError（无 status 字段、无 forgotten_at 等）

- [ ] **Step 3: 重写 models.py**

整文件替换 `agent_lab/memory/models.py`：

```python
"""Core data models for the memory system.

The model deliberately uses plain Python types so it can be shared by an
in-memory store today and database-backed stores later.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from math import isfinite
from types import MappingProxyType
from typing import Mapping
from uuid import uuid4

from .lifecycle import MemoryStatus


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _normalise_datetime(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _copy_attributes(
    value: Mapping[str, str] | None,
    field_name: str,
) -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise TypeError(f"{field_name} must be a mapping of strings")

    copied = dict(value)
    if not all(
        isinstance(key, str) and isinstance(item, str)
        for key, item in copied.items()
    ):
        raise TypeError(f"{field_name} must contain only string keys and values")
    return copied


@dataclass(frozen=True, slots=True, init=False)
class MemoryItem:
    """A backend-agnostic, immutable unit of agent memory.

    ``MemoryItem`` is immutable so store implementations can safely treat an
    update as replacing one value with another. ``kind`` remains accepted as
    a constructor alias for the original Phase 00 skeleton; ``type`` is the
    canonical field going forward.
    """

    content: str
    type: str = "fact"
    source: str | None = None
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    forgotten_at: datetime | None = None
    status: MemoryStatus = MemoryStatus.ACTIVE
    importance: float = 0.5
    metadata: Mapping[str, str] = field(default_factory=dict)
    provenance: Mapping[str, str] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))

    def __init__(
        self,
        content: str,
        *,
        type: str = "fact",
        source: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        valid_from: datetime | None = None,
        valid_until: datetime | None = None,
        forgotten_at: datetime | None = None,
        status: MemoryStatus = MemoryStatus.ACTIVE,
        importance: float = 0.5,
        metadata: Mapping[str, str] | None = None,
        provenance: Mapping[str, str] | None = None,
        id: str | None = None,
        kind: str | None = None,
    ) -> None:
        if kind is not None:
            if type != "fact" and type != kind:
                raise ValueError("type and kind must match when both are provided")
            type = kind

        if not isinstance(content, str) or not content.strip():
            raise ValueError("content must be a non-empty string")
        if not isinstance(type, str) or not type.strip():
            raise ValueError("type must be a non-empty string")
        if source is not None and (not isinstance(source, str) or not source.strip()):
            raise ValueError("source must be a non-empty string when provided")
        if id is not None and (not isinstance(id, str) or not id.strip()):
            raise ValueError("id must be a non-empty string when provided")
        if not isinstance(importance, (int, float)) or isinstance(importance, bool):
            raise TypeError("importance must be a number between 0 and 1")
        if not isfinite(importance) or not 0 <= importance <= 1:
            raise ValueError("importance must be between 0 and 1")
        if not isinstance(status, MemoryStatus):
            raise TypeError("status must be a MemoryStatus member")

        normalised_created_at = _normalise_datetime(
            created_at or _utc_now(), "created_at"
        )
        normalised_updated_at = _normalise_datetime(
            updated_at or normalised_created_at, "updated_at"
        )
        if normalised_updated_at < normalised_created_at:
            raise ValueError("updated_at must not be earlier than created_at")

        normalised_valid_from = (
            _normalise_datetime(valid_from, "valid_from")
            if valid_from is not None
            else None
        )
        normalised_valid_until = (
            _normalise_datetime(valid_until, "valid_until")
            if valid_until is not None
            else None
        )
        if (
            normalised_valid_from is not None
            and normalised_valid_until is not None
            and normalised_valid_until < normalised_valid_from
        ):
            raise ValueError("valid_until must not be earlier than valid_from")

        normalised_forgotten_at = (
            _normalise_datetime(forgotten_at, "forgotten_at")
            if forgotten_at is not None
            else None
        )

        object.__setattr__(self, "content", content)
        object.__setattr__(self, "type", type)
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "created_at", normalised_created_at)
        object.__setattr__(self, "updated_at", normalised_updated_at)
        object.__setattr__(self, "valid_from", normalised_valid_from)
        object.__setattr__(self, "valid_until", normalised_valid_until)
        object.__setattr__(self, "forgotten_at", normalised_forgotten_at)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "importance", float(importance))
        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(_copy_attributes(metadata, "metadata")),
        )
        object.__setattr__(
            self,
            "provenance",
            MappingProxyType(_copy_attributes(provenance, "provenance")),
        )
        object.__setattr__(self, "id", id or str(uuid4()))

    @property
    def kind(self) -> str:
        """Backward-compatible alias for the pre-Phase 01 field name."""

        return self.type
```

- [ ] **Step 3b: 加固 lifecycle._TRANSITIONS（Task 1 评审建议）**

`agent_lab/memory/lifecycle.py`：imports 区加入：

```python
from types import MappingProxyType
```

将 `_TRANSITIONS` 的声明与字典字面量替换为（`is_valid_transition` 不变）：

```python
_TRANSITIONS: MappingProxyType[MemoryStatus, frozenset[MemoryStatus]] = MappingProxyType(
    {
        MemoryStatus.ACTIVE: frozenset(
            {MemoryStatus.SUPERSEDED, MemoryStatus.ARCHIVED}
        ),
        MemoryStatus.SUPERSEDED: frozenset(),
        MemoryStatus.ARCHIVED: frozenset({MemoryStatus.ACTIVE}),
    }
)
```

- [ ] **Step 4: service.py 机械重命名**

`agent_lab/memory/service.py` 三处修改：

`_UPDATABLE_FIELDS`（原 25-33 行）替换为：

```python
    _UPDATABLE_FIELDS = {
        "content",
        "type",
        "source",
        "valid_from",
        "valid_until",
        "importance",
        "metadata",
        "provenance",
    }
```

`remember()` 签名中的 `valid_at: datetime | None = None,` 改为：

```python
        valid_from: datetime | None = None,
```

`remember()` 构造调用中的 `valid_at=valid_at,` 改为：

```python
            valid_from=valid_from,
```

- [ ] **Step 5: 运行验证通过**

Run: `python3 -m unittest discover -s tests -v`
Expected: OK，全部通过

- [ ] **Step 6: Commit**

```bash
git add agent_lab/memory/models.py agent_lab/memory/service.py tests/memory/test_lifecycle.py tests/memory/test_service.py
git commit -m "feat: expand MemoryItem with status, forgotten_at, and valid interval"
```

---

### Task 3: forget 迁移到 forgotten_at + unforget

规范语义：`forget()` 设置 `forgotten_at`，不再修改 `importance`；`unforget()` 清除；重复 `forget()` 刷新；`unforget()` 幂等。`recall()` 叠加 canonical 过滤（ACTIVE + 未遗忘）并保留 legacy 的 `importance > 0`。

**Files:**
- Modify: `agent_lab/memory/service.py`（imports、`recall()` 整方法替换、`forget()` 整方法替换并新增 `unforget()` 与 `_require()`）
- Test: `tests/memory/test_service.py`

- [ ] **Step 1: 写失败测试**

`tests/memory/test_service.py` 中，用下面的测试**整体替换** `test_forget_is_reversible_and_delete_is_permanent`：

```python
    def test_forget_and_unforget_are_reversible_without_touching_importance(self):
        item = self.service.remember("temporary", importance=0.7)

        forgotten = self.service.forget(item.id)
        self.assertIsNotNone(forgotten.forgotten_at)
        self.assertEqual(forgotten.importance, 0.7)
        self.assertIs(self.store.get(item.id), forgotten)
        self.assertNotIn(forgotten.id, [i.id for i in self.service.recall()])
        self.assertIn(
            forgotten.id,
            [i.id for i in self.service.recall(include_forgotten=True)],
        )

        restored = self.service.unforget(item.id)
        self.assertIsNone(restored.forgotten_at)
        self.assertEqual(self.service.recall(), [restored])

        self.assertTrue(self.service.delete(item.id))
        self.assertIsNone(self.store.get(item.id))
```

在 `MemoryServiceTests` 类末尾追加：

```python
    def test_unforget_is_idempotent(self):
        item = self.service.remember("stable")

        unchanged = self.service.unforget(item.id)
        self.assertIsNone(unchanged.forgotten_at)
        self.assertEqual(unchanged.updated_at, item.updated_at)

    def test_repeated_forget_refreshes_forgotten_at(self):
        item = self.service.remember("again")
        first = self.service.forget(item.id)
        second = self.service.forget(item.id)
        self.assertGreaterEqual(second.forgotten_at, first.forgotten_at)

    def test_forget_and_unforget_require_existing_items(self):
        with self.assertRaises(KeyError):
            self.service.forget("missing")
        with self.assertRaises(KeyError):
            self.service.unforget("missing")
```

- [ ] **Step 2: 运行验证失败**

Run: `python3 -m unittest tests.memory.test_service -v`
Expected: FAIL — `AttributeError: 'MemoryService' object has no attribute 'unforget'`；且 `test_forget_and_unforget_are_reversible...` 断言 `importance == 0.7` 失败（当前 forget 置 0）

- [ ] **Step 3: 实现**

`agent_lab/memory/service.py`：

imports 区（`from .store import MemoryStore` 之前）新增：

```python
from .lifecycle import MemoryStatus
```

在 `__init__` 之后新增辅助方法：

```python
    def _require(self, item_id: str) -> MemoryItem:
        current = self._store.get(item_id)
        if current is None:
            raise KeyError(f"memory item not found: {item_id}")
        return current
```

整方法替换 `recall()`：

```python
    def recall(
        self,
        *,
        type: str | None = None,
        source: str | None = None,
        include_forgotten: bool = False,
        limit: int | None = None,
    ) -> list[MemoryItem]:
        """Agent-facing candidate fetch: Phase 01 compat plus basic filters.

        Filters are deterministic only: status ACTIVE, not forgotten, and
        the legacy ``importance > 0`` marker from Phase 01 (scheduled for
        removal in Phase 09). No similarity, ranking, or recency here.
        """

        if limit is not None and limit < 0:
            raise ValueError("limit must be non-negative")

        items = self._store.list()
        items = [item for item in items if item.status == MemoryStatus.ACTIVE]
        if not include_forgotten:
            items = [item for item in items if item.forgotten_at is None]
        items = [item for item in items if item.importance > 0]
        if type is not None:
            items = [item for item in items if item.type == type]
        if source is not None:
            items = [item for item in items if item.source == source]
        if limit is not None:
            items = items[:limit]
        return items
```

整方法替换 `forget()` 并新增 `unforget()`（原 `forget()` 删除）：

```python
    def forget(self, item_id: str) -> MemoryItem:
        """Mark a memory forgotten; the canonical marker is ``forgotten_at``.

        Repeated calls refresh the marker. Importance and status are
        untouched — importance expresses value, not forgetting.
        """

        current = self._require(item_id)
        now = _utc_now()
        updated = replace(current, forgotten_at=now, updated_at=now)
        return self._store.update(updated)

    def unforget(self, item_id: str) -> MemoryItem:
        """Clear the forgotten marker; idempotent for non-forgotten items."""

        current = self._require(item_id)
        if current.forgotten_at is None:
            return current
        updated = replace(current, forgotten_at=None, updated_at=_utc_now())
        return self._store.update(updated)
```

- [ ] **Step 4: 运行验证通过**

Run: `python3 -m unittest discover -s tests -v`
Expected: OK，全部通过（Phase 01 的 `test_recall_supports_exact_filters_and_excludes_forgotten` 无需改动即通过：forget 现在设置 forgotten_at，recall 默认照旧排除）

- [ ] **Step 5: Commit**

```bash
git add agent_lab/memory/service.py tests/memory/test_service.py
git commit -m "feat: migrate forget semantics to forgotten_at with unforget"
```

---

### Task 4: archive / restore 转换与 update 门控

**Files:**
- Modify: `agent_lab/memory/service.py`（imports、`update()` 插入门控、新增 `_transition()` / `archive()` / `restore()`）
- Modify: `tests/memory/test_lifecycle.py`（追加转换表直接测试，Task 1 评审建议）
- Test: `tests/memory/test_service.py`

- [ ] **Step 1: 写失败测试**

`tests/memory/test_service.py`：

import 头第二行改为（加入 `MemoryStatus`）：

```python
from agent_lab.memory import InMemoryStore, MemoryItem, MemoryService, MemoryStatus
```

在 `MemoryServiceTests` 类末尾追加：

```python
    def test_archive_and_restore_transition_active_memories(self):
        item = self.service.remember("archival candidate")

        archived = self.service.archive(item.id)
        self.assertIs(archived.status, MemoryStatus.ARCHIVED)
        self.assertNotIn(archived.id, [i.id for i in self.service.recall()])

        restored = self.service.restore(item.id)
        self.assertIs(restored.status, MemoryStatus.ACTIVE)
        self.assertEqual(self.service.recall(), [restored])

    def test_restore_does_not_touch_forgotten_marker(self):
        item = self.service.remember("archived and forgotten")
        self.service.archive(item.id)
        self.service.forget(item.id)

        restored = self.service.restore(item.id)
        self.assertIs(restored.status, MemoryStatus.ACTIVE)
        self.assertIsNotNone(restored.forgotten_at)
        self.assertNotIn(restored.id, [i.id for i in self.service.recall()])

    def test_invalid_lifecycle_transitions_are_rejected(self):
        item = self.service.remember("subject")
        self.service.archive(item.id)

        with self.assertRaises(ValueError):
            self.service.archive(item.id)
        with self.assertRaises(ValueError):
            self.service.restore(self.service.remember("never archived").id)
        with self.assertRaises(KeyError):
            self.service.archive("missing")
        with self.assertRaises(KeyError):
            self.service.restore("missing")

    def test_update_is_restricted_to_active_memories(self):
        item = self.service.remember("subject")
        self.service.archive(item.id)

        with self.assertRaises(ValueError):
            self.service.update(item.id, content="edited")
        with self.assertRaises(TypeError):
            self.service.update(
                self.service.remember("active one").id,
                status=MemoryStatus.ARCHIVED,
            )
        with self.assertRaises(TypeError):
            self.service.update(
                self.service.remember("active two").id,
                forgotten_at=datetime.now(timezone.utc),
            )
```

并在 `tests/memory/test_lifecycle.py` 的 `MemoryStatusTests` 类中追加：

```python
    def test_transition_table_rules(self):
        self.assertTrue(
            is_valid_transition(MemoryStatus.ACTIVE, MemoryStatus.SUPERSEDED)
        )
        self.assertTrue(
            is_valid_transition(MemoryStatus.ACTIVE, MemoryStatus.ARCHIVED)
        )
        self.assertTrue(
            is_valid_transition(MemoryStatus.ARCHIVED, MemoryStatus.ACTIVE)
        )
        self.assertFalse(
            is_valid_transition(MemoryStatus.SUPERSEDED, MemoryStatus.ACTIVE)
        )
        self.assertFalse(
            is_valid_transition(MemoryStatus.SUPERSEDED, MemoryStatus.ARCHIVED)
        )
```

同时将该文件 import 头改为：

```python
from agent_lab.memory import MemoryItem, MemoryStatus, MemoryType
from agent_lab.memory.lifecycle import is_valid_transition
```

- [ ] **Step 2: 运行验证失败**

Run: `python3 -m unittest tests.memory.test_service -v`
Expected: FAIL — `AttributeError: 'MemoryService' object has no attribute 'archive'`

- [ ] **Step 3: 实现**

`agent_lab/memory/service.py`：

imports 区加入 `is_valid_transition`（与 Task 3 的 MemoryStatus 导入合并为）：

```python
from .lifecycle import MemoryStatus, is_valid_transition
```

`update()` 中，将：

```python
        current = self._store.get(item_id)
        if current is None:
            raise KeyError(f"memory item not found: {item_id}")
        if not changes:
            return current
```

替换为：

```python
        current = self._store.get(item_id)
        if current is None:
            raise KeyError(f"memory item not found: {item_id}")
        if current.status != MemoryStatus.ACTIVE:
            raise ValueError("only ACTIVE memories can be updated")
        if not changes:
            return current
```

在 `unforget()` 之后新增：

```python
    def _transition(self, item_id: str, target: MemoryStatus) -> MemoryItem:
        current = self._require(item_id)
        if not is_valid_transition(current.status, target):
            raise ValueError(
                f"invalid lifecycle transition: {current.status} -> {target}"
            )
        updated = replace(current, status=target, updated_at=_utc_now())
        return self._store.update(updated)

    def archive(self, item_id: str) -> MemoryItem:
        """ACTIVE -> ARCHIVED."""

        return self._transition(item_id, MemoryStatus.ARCHIVED)

    def restore(self, item_id: str) -> MemoryItem:
        """ARCHIVED -> ACTIVE; does not touch the forgotten marker."""

        return self._transition(item_id, MemoryStatus.ACTIVE)
```

- [ ] **Step 4: 运行验证通过**

Run: `python3 -m unittest discover -s tests -v`
Expected: OK，全部通过

- [ ] **Step 5: Commit**

```bash
git add agent_lab/memory/service.py tests/memory/test_service.py tests/memory/test_lifecycle.py
git commit -m "feat: archive/restore lifecycle transitions and update gating"
```

---

### Task 5: service 的 get() 与 list()

**Files:**
- Modify: `agent_lab/memory/service.py`（新增 `get()` / `list()`）
- Test: `tests/memory/test_service.py`

- [ ] **Step 1: 写失败测试**

`tests/memory/test_service.py` 在 `MemoryServiceTests` 类末尾追加：

```python
    def test_get_returns_items_in_any_state(self):
        item = self.service.remember("findable")
        self.assertIs(self.service.get(item.id), item)
        self.assertIsNone(self.service.get("missing"))

    def test_list_defaults_to_active_and_not_forgotten(self):
        active = self.service.remember("active")
        archived = self.service.remember("archived")
        self.service.archive(archived.id)
        forgotten = self.service.remember("forgotten")
        self.service.forget(forgotten.id)

        self.assertEqual([item.id for item in self.service.list()], [active.id])
        self.assertEqual(
            [item.id for item in self.service.list(status=None)],
            [active.id, archived.id, forgotten.id],
        )
        self.assertEqual(
            [item.id for item in self.service.list(status=MemoryStatus.ARCHIVED)],
            [archived.id],
        )
        self.assertEqual(
            [item.id for item in self.service.list(include_forgotten=True)],
            [active.id, forgotten.id],
        )

    def test_list_supports_filters_and_limit(self):
        first = self.service.remember("a", type="preference")
        self.service.remember("b", type="fact")
        self.service.remember("c", source="profile")

        self.assertEqual(self.service.list(type="preference"), [first])
        self.assertEqual(len(self.service.list(source="profile")), 1)
        self.assertEqual(self.service.list(limit=1)[0].id, first.id)
        with self.assertRaises(ValueError):
            self.service.list(limit=-1)
```

- [ ] **Step 2: 运行验证失败**

Run: `python3 -m unittest tests.memory.test_service -v`
Expected: FAIL — `AttributeError: 'MemoryService' object has no attribute 'get'`

- [ ] **Step 3: 实现**

`agent_lab/memory/service.py` 在 `recall()` 之后新增：

```python
    def get(self, item_id: str) -> MemoryItem | None:
        """Return a memory in any state, or ``None`` when missing."""

        return self._store.get(item_id)

    def list(
        self,
        *,
        status: MemoryStatus | None = MemoryStatus.ACTIVE,
        type: str | None = None,
        source: str | None = None,
        include_forgotten: bool = False,
        limit: int | None = None,
    ) -> list[MemoryItem]:
        """Structured browsing/management view over stored memories."""

        if limit is not None and limit < 0:
            raise ValueError("limit must be non-negative")

        items = self._store.list()
        if status is not None:
            items = [item for item in items if item.status == status]
        if not include_forgotten:
            items = [item for item in items if item.forgotten_at is None]
        if type is not None:
            items = [item for item in items if item.type == type]
        if source is not None:
            items = [item for item in items if item.source == source]
        if limit is not None:
            items = items[:limit]
        return items
```

- [ ] **Step 4: 运行验证通过**

Run: `python3 -m unittest discover -s tests -v`
Expected: OK，全部通过

- [ ] **Step 5: Commit**

```bash
git add agent_lab/memory/service.py tests/memory/test_service.py
git commit -m "feat: service get() and status-aware list()"
```

---

### Task 6: supersede 领域操作

**Files:**
- Modify: `agent_lab/memory/service.py`（新增 `_SUPERSEDE_OVERRIDES` 与 `supersede()`）
- Test: `tests/memory/test_service.py`

- [ ] **Step 1: 写失败测试**

`tests/memory/test_service.py` 在 `MemoryServiceTests` 类末尾追加：

```python
    def test_supersede_creates_linked_successor(self):
        old = self.service.remember(
            "User lives in Beijing",
            type="fact",
            source="conversation",
            importance=0.6,
            metadata={"topic": "home"},
            valid_from=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )

        successor = self.service.supersede(old.id, "User lives in Shanghai")

        self.assertIsNot(successor.id, old.id)
        self.assertEqual(successor.content, "User lives in Shanghai")
        self.assertIs(successor.status, MemoryStatus.ACTIVE)
        self.assertIsNone(successor.forgotten_at)
        self.assertEqual(successor.type, "fact")
        self.assertEqual(successor.source, "conversation")
        self.assertEqual(successor.importance, 0.6)
        self.assertEqual(successor.metadata, {"topic": "home"})
        self.assertEqual(successor.provenance, {"supersedes": old.id})
        self.assertGreaterEqual(successor.valid_from, old.valid_from)

        stored_old = self.store.get(old.id)
        self.assertIs(stored_old.status, MemoryStatus.SUPERSEDED)
        self.assertEqual(stored_old.provenance["superseded_by"], successor.id)
        self.assertEqual(stored_old.valid_until, successor.valid_from)

    def test_supersede_honours_overrides(self):
        old = self.service.remember("old", importance=0.6)

        successor = self.service.supersede(
            old.id,
            "new",
            type="preference",
            importance=0.9,
            metadata={"k": "v"},
        )

        self.assertEqual(successor.type, "preference")
        self.assertEqual(successor.importance, 0.9)
        self.assertEqual(successor.metadata, {"k": "v"})

    def test_supersede_rejects_invalid_requests(self):
        item = self.service.remember("subject")
        self.service.archive(item.id)

        with self.assertRaises(KeyError):
            self.service.supersede("missing", "content")
        with self.assertRaises(ValueError):
            self.service.supersede(item.id, "content")
        with self.assertRaises(TypeError):
            self.service.supersede(
                self.service.remember("active").id, "content", bogus="x"
            )

    def test_supersede_preserves_supersedes_link_against_overrides(self):
        old = self.service.remember("old")
        successor = self.service.supersede(
            old.id, "new", provenance={"supersedes": "forged"}
        )
        self.assertEqual(successor.provenance["supersedes"], old.id)
```

- [ ] **Step 2: 运行验证失败**

Run: `python3 -m unittest tests.memory.test_service -v`
Expected: FAIL — `AttributeError: 'MemoryService' object has no attribute 'supersede'`

- [ ] **Step 3: 实现**

`agent_lab/memory/service.py`，`_UPDATABLE_FIELDS` 之后新增类常量：

```python
    _SUPERSEDE_OVERRIDES = {
        "type",
        "source",
        "importance",
        "metadata",
        "provenance",
        "valid_from",
        "valid_until",
    }
```

在 `restore()` 之后新增方法：

```python
    def supersede(self, item_id: str, content: str, **overrides: object) -> MemoryItem:
        """Replace an ACTIVE memory with a successor and record lineage.

        The successor gets a new id and created_at, inherits business
        fields (overridable), and carries ``provenance["supersedes"]``.
        The old memory becomes SUPERSEDED, gains
        ``provenance["superseded_by"]``, and — if its ``valid_until`` is
        open — has it closed at the supersede time.
        """

        unsupported = set(overrides) - self._SUPERSEDE_OVERRIDES
        if unsupported:
            names = ", ".join(sorted(unsupported))
            raise TypeError(f"unsupported supersede override fields: {names}")

        current = self._require(item_id)
        if current.status != MemoryStatus.ACTIVE:
            raise ValueError(
                f"invalid lifecycle transition: {current.status} -> "
                f"{MemoryStatus.SUPERSEDED}"
            )

        now = _utc_now()
        overrides_provenance = overrides.get("provenance") or {}
        params: dict[str, object] = {
            "type": current.type,
            "source": current.source,
            "importance": current.importance,
            "metadata": current.metadata,
            "valid_from": now,
            "valid_until": None,
        }
        params.update(overrides)

        successor = MemoryItem(
            content,
            created_at=now,
            provenance={**overrides_provenance, "supersedes": current.id},
            status=MemoryStatus.ACTIVE,
            **params,  # type: ignore[arg-type]
        )
        successor = self._store.add(successor)

        superseded = replace(
            current,
            status=MemoryStatus.SUPERSEDED,
            updated_at=now,
            provenance={**current.provenance, "superseded_by": successor.id},
            valid_until=(
                current.valid_until if current.valid_until is not None else now
            ),
        )
        self._store.update(superseded)
        return successor
```

- [ ] **Step 4: 运行验证通过**

Run: `python3 -m unittest discover -s tests -v`
Expected: OK，全部通过

- [ ] **Step 5: Commit**

```bash
git add agent_lab/memory/service.py tests/memory/test_service.py
git commit -m "feat: supersede with successor creation and provenance lineage"
```

---

### Task 7: supersede 失败回滚

spec 要求预校验 + 可回滚补偿：`update(old)` 失败时删除刚创建的后继并重新抛出。

**Files:**
- Modify: `agent_lab/memory/service.py`（`supersede()` 的 update 段加 try/except）
- Test: `tests/memory/test_service.py`

- [ ] **Step 1: 写失败测试**

`tests/memory/test_service.py`，在 `if __name__ == "__main__":` 之前新增：

```python
class FlakyUpdateStore:
    """InMemoryStore wrapper whose update() can be made to fail once."""

    def __init__(self) -> None:
        self._inner = InMemoryStore()
        self.fail_next_update = False

    def add(self, item):
        return self._inner.add(item)

    def get(self, item_id):
        return self._inner.get(item_id)

    def update(self, item):
        if self.fail_next_update:
            self.fail_next_update = False
            raise RuntimeError("simulated storage failure")
        return self._inner.update(item)

    def delete(self, item_id):
        return self._inner.delete(item_id)

    def list(self):
        return self._inner.list()


class SupersedeRollbackTests(unittest.TestCase):
    def test_failed_old_update_rolls_back_successor(self):
        store = FlakyUpdateStore()
        service = MemoryService(store)
        old = service.remember("old")

        store.fail_next_update = True
        with self.assertRaises(RuntimeError):
            service.supersede(old.id, "new")

        stored_old = store.get(old.id)
        self.assertIs(stored_old.status, MemoryStatus.ACTIVE)
        self.assertIsNone(stored_old.provenance.get("superseded_by"))
        self.assertEqual(len(store.list()), 1)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行验证失败**

Run: `python3 -m unittest tests.memory.test_service.SupersedeRollbackTests -v`
Expected: FAIL — `assertEqual(len(store.list()), 1)` 实际为 2（后继未回滚）

- [ ] **Step 3: 实现**

`agent_lab/memory/service.py` 的 `supersede()` 中，将：

```python
        self._store.update(superseded)
        return successor
```

替换为：

```python
        try:
            self._store.update(superseded)
        except Exception:
            self._store.delete(successor.id)
            raise
        return successor
```

- [ ] **Step 4: 运行验证通过**

Run: `python3 -m unittest discover -s tests -v`
Expected: OK，全部通过

- [ ] **Step 5: Commit**

```bash
git add agent_lab/memory/service.py tests/memory/test_service.py
git commit -m "fix: roll back successor when supersede update fails"
```

---

### Task 8: 文档一致性与最终验证

**Files:**
- Modify: `README.md`（roadmap 第 2 条）

- [ ] **Step 1: 更新 README**

`README.md` 的 "Learning roadmap" 列表中，将：

```text
2. Short-term vs. long-term memory
```

替换为：

```text
2. Memory types, lifecycle, and supersession
```

- [ ] **Step 2: 全量验证**

Run:
```bash
python3 -m unittest discover -s tests -v
PYTHONPATH=. python3 experiments/memory/01_basic/main.py
git status --short
```
Expected: 全部测试 OK；实验输出 `[preference] The user prefers concise explanations`；工作区只有 README 的待提交改动。

若 `uv` 可用，另跑 `./scripts/check.sh`，Expected: `Memory Core check passed.`

- [ ] **Step 3: spec 验收标准核对**

对照 `docs/memory-system-spec.md` §10 逐项核对（MemoryType 开放 type、MemoryStatus 三状态、转换校验、遗忘正交、12 个 Service 方法、仅经 Store 访问、InMemoryStore 不变、supersede 血缘与回滚、测试九类覆盖、Phase 01 兼容清单、文档一致）。任何一项不满足，回到对应 Task 修复。

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: align README roadmap with Phase 02"
```

---

## 完成定义

- `python3 -m unittest discover -s tests -v` 全绿（Phase 01 + Phase 02 全部测试）
- `PYTHONPATH=. python3 experiments/memory/01_basic/main.py` 正常输出
- spec §10 验收标准全部满足
- 提交历史清晰：8 个独立 commit，每个对应一个行为单元
