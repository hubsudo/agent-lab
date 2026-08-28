# Memory System Specification

> 当前版本：**Phase 01 — Memory Core**
>
> 本文定义 Memory System 的核心数据模型、存储抽象和服务边界。它与
> [Memory System Roadmap](./memory-system-roadmap.md) 配套使用：Roadmap
> 说明学习顺序，本文说明当前阶段的设计契约。

## 1. 目标与范围

Phase 01 的目标是建立一个可以持续演进的 Memory Core，而不是实现完整的
RAG 或 Agent Memory 产品。

本阶段包含：

- 可扩展的 `MemoryItem` 数据模型
- 与具体数据库无关的 `MemoryStore` 接口
- 标准库实现的 `InMemoryStore`
- 承载 Memory 业务语义的 `MemoryService`
- 可执行的 CRUD、更新、遗忘和基础过滤测试

本阶段不包含：

- Embedding、Vector DB 或全文检索
- LLM 驱动的 Memory Extraction
- 相关性排序、Reranking 或 Hybrid Retrieval
- Deduplication、Conflict Resolution 或 Summarization
- PostgreSQL、pgvector 和 Agent Runtime 集成

## 2. 架构分层

Memory System 采用三层结构：

```text
Agent
  │
  ↓
MemoryService       ← Memory 业务逻辑
  │
  ↓
MemoryStore         ← 持久化抽象
  ├── InMemoryStore
  ├── PostgresStore
  └── VectorStore
```

依赖方向必须保持单向：

```text
Agent / Application
          ↓
    MemoryService
          ↓
     MemoryStore
          ↓
    Storage Backend
```

约束：

- `MemoryItem` 不依赖 Agent Framework、ORM 或数据库 SDK。
- `MemoryStore` 只处理 MemoryItem 的存取，不实现业务策略。
- `MemoryService` 不直接访问数据库，只依赖 `MemoryStore`。
- 具体 Store 可以替换，而不应改变上层 Service API。

## 3. MemoryItem

### 3.1 数据结构

```text
MemoryItem
├── identity
│   └── id
├── content
│   └── content
├── classification
│   ├── type
│   └── source
├── temporal
│   ├── created_at
│   ├── updated_at
│   └── valid_at
├── importance
│   └── importance
├── metadata
└── provenance
```

### 3.2 字段契约

| 字段 | 类型 | 默认值 | 约束与含义 |
| --- | --- | --- | --- |
| `id` | `str` | UUID | Memory 的稳定身份；更新时不可改变 |
| `content` | `str` | 必填 | Memory 的主要内容，不能是空字符串或纯空白 |
| `type` | `str` | `"fact"` | Memory 分类；Phase 01 使用开放字符串，不提前绑定枚举 |
| `source` | `str \| None` | `None` | Memory 的直接来源，例如 `conversation`、`tool` 或 `user` |
| `created_at` | `datetime` | 当前 UTC 时间 | 创建时间，必须带时区 |
| `updated_at` | `datetime` | 等于 `created_at` | 最近一次变更时间，必须不早于 `created_at` |
| `valid_at` | `datetime \| None` | `None` | 事实开始有效的时间；与记录创建时间分开 |
| `importance` | `float` | `0.5` | 归一化重要性，取值范围为 `0` 到 `1` |
| `metadata` | `Mapping[str, str]` | `{}` | 可扩展业务属性；Phase 01 仅接受字符串键值，并以不可变快照保存 |
| `provenance` | `Mapping[str, str]` | `{}` | 来源追踪信息，例如会话 ID、消息 ID 或提取器版本，并以不可变快照保存 |

### 3.3 不可变性

`MemoryItem` 是不可变对象。更新通过创建一个保留原 `id` 和
`created_at` 的新对象完成，再交给 `MemoryStore.update()` 替换旧对象。

这样可以避免调用方在 Store 外部悄悄修改已经保存的 Memory，并为未来的
版本化、审计和并发控制保留空间。

### 3.4 时间约定

- 所有时间必须是 timezone-aware `datetime`。
- 进入模型后统一转换为 UTC。
- `updated_at` 初始等于 `created_at`。
- Service 更新 Memory 时自动刷新 `updated_at`。

## 4. MemoryStore

`MemoryStore` 是所有持久化实现必须遵守的最小接口：

```python
class MemoryStore(Protocol):
    def add(self, item: MemoryItem) -> MemoryItem: ...
    def get(self, item_id: str) -> MemoryItem | None: ...
    def update(self, item: MemoryItem) -> MemoryItem: ...
    def delete(self, item_id: str) -> bool: ...
    def list(self) -> list[MemoryItem]: ...
```

### 4.1 方法语义

| 方法 | 语义 | 失败行为 |
| --- | --- | --- |
| `add(item)` | 保存一个新 Memory，并返回该对象 | `id` 已存在时抛出 `ValueError` |
| `get(item_id)` | 按稳定 ID 获取 Memory | 不存在时返回 `None` |
| `update(item)` | 用同 ID 的新对象替换已有 Memory | ID 不存在时抛出 `KeyError` |
| `delete(item_id)` | 永久删除 Memory | 删除不存在的 ID 返回 `False` |
| `list()` | 返回当前 Memory 的快照 | 返回新列表，不暴露 Store 内部容器 |

### 4.2 InMemoryStore

`InMemoryStore` 是 Phase 01 的参考实现，使用 Python `dict` 保存数据。

它提供以下保证：

- 按插入顺序返回 `list()` 结果。
- 不允许 `add()` 静默覆盖相同 ID 的对象。
- `delete()` 是幂等的。
- `update()` 不改变对象在列表中的位置。

这些行为属于 Phase 01 的可执行契约；未来的数据库实现必须尽量保持相同
的上层语义。

## 5. MemoryService

`MemoryService` 是 Agent 或应用层使用的业务入口：

```text
MemoryService
├── remember()
├── recall()
├── update()
├── forget()
├── delete()
└── consolidate()
```

### 5.1 `remember()`

```python
remember(
    content,
    *,
    type="fact",
    source=None,
    created_at=None,
    valid_at=None,
    importance=0.5,
    metadata=None,
    provenance=None,
    id=None,
) -> MemoryItem
```

负责创建并保存 `MemoryItem`，不直接暴露 Store 的内部实现。

### 5.2 `recall()`

Phase 01 的 `recall()` 只提供确定性的精确过滤，不声称已经实现语义检索：

```python
recall(
    *,
    type=None,
    source=None,
    include_forgotten=False,
    limit=None,
) -> list[MemoryItem]
```

规则：

- 默认只返回 `importance > 0` 的活跃 Memory。
- `type` 和 `source` 是精确匹配过滤器。
- 返回顺序与 Store 的 `list()` 顺序一致。
- `limit` 为非负整数时截取结果；负数抛出 `ValueError`。
- Keyword、Vector、Hybrid Retrieval 和 Ranking 留到后续阶段。

### 5.3 `update()`

```python
update(item_id, **changes) -> MemoryItem
```

允许更新：

- `content`
- `type`
- `source`
- `valid_at`
- `importance`
- `metadata`
- `provenance`

`id`、`created_at` 和 `updated_at` 不能由调用方直接修改。Service 会保留
前两者，并在有实际变更时自动设置新的 `updated_at`。

### 5.4 `forget()` 与 `delete()`

Phase 01 暂采用最小且可恢复的遗忘语义：

- `forget(item_id)` 将 `importance` 设置为 `0.0`。
- 被遗忘的 Memory 仍保留在 Store 中，可通过 `update()` 恢复重要性。
- `recall()` 默认排除被遗忘的 Memory。
- `recall(include_forgotten=True)` 可以查看被遗忘的 Memory。
- `delete(item_id)` 是永久删除，不保留 Store 记录。

未来 Phase 08 可以引入独立的生命周期状态或遗忘时间戳，但不应破坏
`delete()` 的永久删除语义。

### 5.5 `consolidate()`

Phase 01 只声明 `consolidate()` 入口，不实现默认合并策略。调用时会明确
抛出 `NotImplementedError`。

原因是 Deduplication、Conflict Resolution 和 Summarization 都需要先定义
可评估的策略；在没有策略之前自动合并会把业务假设隐藏在基础层中。

## 6. 生命周期边界

Phase 01 支持的基础生命周期如下：

```text
remember()
    ↓
MemoryItem
    ↓
Store.add()
    ↓
recall() / get()
    ↓
update() ───────┐
    ↓            │
forget() ───────┘
    ↓
delete()
```

以下能力虽然会在整体路线中出现，但不属于 Phase 01：

- 从原始对话中提取 Candidate Memory
- 根据多个 Episodic Memory 生成 Semantic Memory
- 按相关性检索或排序
- 多条 Memory 的合并、冲突解决和摘要
- 基于评测集计算 Retrieval 或 Memory 质量

## 7. 代码布局

```text
agent_lab/
└── memory/
    ├── __init__.py    # 公共导出
    ├── models.py      # MemoryItem
    ├── store.py       # MemoryStore Protocol
    ├── in_memory.py   # InMemoryStore
    └── service.py     # MemoryService
```

对应测试：

```text
tests/
└── memory/
    ├── test_in_memory.py
    └── test_service.py
```

## 8. Phase 01 验收标准

- [x] `MemoryItem` 包含 identity、content、classification、temporal、importance、metadata 和 provenance。
- [x] `MemoryItem` 不依赖第三方库，并校验核心字段不变量。
- [x] `MemoryStore` 定义 `add()`、`get()`、`update()`、`delete()` 和 `list()`。
- [x] `InMemoryStore` 覆盖 Store 的完整接口。
- [x] `MemoryService` 提供 `remember()`、`recall()`、`update()`、`forget()` 和 `delete()`。
- [x] `consolidate()` 保留入口，并明确将策略推迟到 Phase 08。
- [x] 现有实验可以通过 `MemoryService` 使用 Memory Core。
- [x] 核心行为由 `unittest` 覆盖。

## 9. 后续演进约束

进入下一阶段时，优先扩展接口和策略，不直接破坏 Phase 01 契约：

1. Phase 02 增加 Memory Types 与 Lifecycle，而不是把类型硬编码成不可扩展的枚举。
2. Phase 03 增加 Conversation、Message 和 Session，并通过 `source` 与 `provenance` 关联来源。
3. Phase 04 增加 Extraction 层，不让 LLM 调用渗入 `MemoryStore`。
4. Phase 05–09 在 Service 上扩展 Semantic Memory、Retrieval、Consolidation 和 Evaluation。
5. Phase 10 通过新的 Store 实现接入 PostgreSQL + pgvector，保持 Service 依赖的接口稳定。
6. Phase 11 最后接入 Agent Runtime，Agent 不直接访问数据库。
