# Memory System Specification

> 当前版本：**Phase 02 — Memory Types & Lifecycle**
>
> 本文定义 Memory System 的核心数据模型、生命周期模型、存储抽象和服务边界。
> 它与 [Memory System Roadmap](./memory-system-roadmap.md) 配套使用：Roadmap
> 说明学习顺序，本文说明当前阶段的设计契约。

## 1. 目标与范围

Phase 02 的目标是在 Phase 01 Memory Core 的基础上，建立 Memory 的类型体系
与生命周期模型，并以 `MemoryService` 作为唯一的业务入口。

本阶段包含：

- `MemoryType` 标准类型集合与开放的 `type` 字段
- `MemoryStatus` 生命周期状态与明确的转换规则
- 与状态正交的遗忘维度（`forgotten_at`）
- `MemoryService` 领域操作：remember / get / list / recall / update /
  forget / unforget / archive / restore / supersede / delete
- `supersede()` 的后继创建与双向血缘

本阶段不包含：

- Embedding、Vector Search、Keyword Search、Retrieval、Ranking、RAG
- Memory Extraction 与 Memory Consolidation
- PostgreSQL、pgvector、Redis、MCP、Agent Runtime 集成
- 复杂 Temporal Reasoning、Conflict Resolution、Forgetting Policy

## 2. 架构分层

Memory System 采用三层结构：

```text
Agent
  │
  ↓
MemoryService       ← Memory 业务逻辑与生命周期策略
  │
  ↓
MemoryStore         ← 持久化抽象
  └── InMemoryStore
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
- 生命周期状态与转换规则独立定义在 `lifecycle` 模块中，模型与存储不感知
  转换策略。
- 具体 Store 可以替换，而不应改变上层 Service API。

## 3. MemoryType 与 MemoryStatus

### 3.1 MemoryType

`MemoryType` 是 Memory 的标准类型集合，定义为 `enum.StrEnum`：

| 成员 | 值 | 含义 |
| --- | --- | --- |
| `WORKING` | `"working"` | 当前 Agent Run 所需的临时上下文 |
| `EPISODIC` | `"episodic"` | 具体事件、经历及其时间与上下文 |
| `SEMANTIC` | `"semantic"` | 稳定的事实、知识与偏好 |
| `PROCEDURAL` | `"procedural"` | 执行某类任务的经验或规则 |

`MemoryItem.type` 保持**开放字符串字段**：

- 接受 `MemoryType` 成员（`StrEnum` 成员与字符串相等比较成立）。
- 也接受任意非空字符串，不排斥标准集合之外的自定义类型。
- 默认值 `"fact"` 是 Phase 01 遗留的 legacy 默认，不属于标准集合；
  保留它以避免破坏既有调用方，后续阶段再决定是否迁移（见 §8）。

Phase 01 spec §9.1 的约束继续有效：类型体系可扩展，不硬编码成封闭枚举。

### 3.2 MemoryStatus

`MemoryStatus` 是 MemoryItem 在 Store 中可能处于的生命周期状态，定义为
`enum.StrEnum`：

| 成员 | 值 | 含义 |
| --- | --- | --- |
| `ACTIVE` | `"active"` | 正常参与 recall / list 的当前状态 |
| `SUPERSEDED` | `"superseded"` | 已被后继 Memory 替代，保留供追溯 |
| `ARCHIVED` | `"archived"` | 主动归档，不再参与常规使用，可恢复 |

**删除不是状态。** `delete()` 是 Store 操作（物理移除），被删除的
Memory 不在 Store 中，因此不存在"已删除状态"的对象。`SUPERSEDED` 与
`ARCHIVED` 的 Memory 仍保留在 Store 中、可通过 `get()` / `list()` 查询；
被删除的 Memory 则物理消失、不可恢复。

`MemoryItem.status` 严格校验：必须是 `MemoryStatus` 成员，默认
`ACTIVE`。`remember()` 不暴露 `status` 参数，新建 Memory 恒为 `ACTIVE`。

## 4. MemoryItem

### 4.1 数据结构

```text
MemoryItem
├── identity
│   └── id
├── content
│   └── content
├── classification
│   ├── type          # 开放字符串，标准集合为 MemoryType
│   ├── source
│   └── status        # MemoryStatus，Phase 02 新增
├── temporal
│   ├── created_at
│   ├── updated_at
│   ├── valid_from    # 原 valid_at，Phase 02 重命名
│   ├── valid_until   # Phase 02 新增；None 表示仍然有效
│   └── forgotten_at  # Phase 02 新增；遗忘维度，与 status 正交
├── importance
├── metadata
└── provenance
```

### 4.2 字段契约

| 字段 | 类型 | 默认值 | 约束与含义 |
| --- | --- | --- | --- |
| `id` | `str` | UUID | Memory 的稳定身份；更新时不可改变 |
| `content` | `str` | 必填 | Memory 的主要内容，不能是空字符串或纯空白 |
| `type` | `str` | `"fact"` | Memory 分类；接受 `MemoryType` 成员或任意非空字符串 |
| `source` | `str \| None` | `None` | Memory 的直接来源，例如 `conversation`、`tool` 或 `user` |
| `status` | `MemoryStatus` | `ACTIVE` | 生命周期状态；只能通过 Service 的转换方法变更 |
| `created_at` | `datetime` | 当前 UTC 时间 | 创建时间，必须带时区 |
| `updated_at` | `datetime` | 等于 `created_at` | 最近一次变更时间，必须不早于 `created_at` |
| `valid_from` | `datetime \| None` | `None` | 事实开始有效的时间；与记录创建时间分开 |
| `valid_until` | `datetime \| None` | `None` | 事实失效时间；`None` 表示仍然有效 |
| `forgotten_at` | `datetime \| None` | `None` | 被遗忘的时刻；`None` 表示未遗忘 |
| `importance` | `float` | `0.5` | 归一化重要性（价值），取值范围 `0` 到 `1`；**不表示是否被遗忘** |
| `metadata` | `Mapping[str, str]` | `{}` | 可扩展业务属性；仅接受字符串键值，以不可变快照保存 |
| `provenance` | `Mapping[str, str]` | `{}` | 来源与血缘追踪（如会话 ID、`supersedes` / `superseded_by`），以不可变快照保存 |

### 4.3 不变性

`MemoryItem` 是不可变对象。更新通过创建一个保留原 `id` 和 `created_at`
的新对象完成，再交给 `MemoryStore.update()` 替换旧对象。

除 Phase 01 已有校验外，Phase 02 新增：

- `status` 必须是 `MemoryStatus` 成员。
- `forgotten_at` 为 `None` 或 timezone-aware `datetime`（归一化为 UTC）。
- `valid_from` 与 `valid_until` 同时存在时，必须满足
  `valid_from <= valid_until`。

### 4.4 时间约定

- 所有时间必须是 timezone-aware `datetime`，进入模型后统一转换为 UTC。
- `updated_at` 初始等于 `created_at`。
- Service 的所有变更操作自动刷新 `updated_at`。

## 5. 生命周期

### 5.1 状态转换规则

```text
   ACTIVE ── supersede() ──→ SUPERSEDED（终态）
      │
      └── archive() ───→ ARCHIVED ── restore() ──→ ACTIVE
```

| 当前状态 | 操作 | 结果状态 |
| --- | --- | --- |
| `ACTIVE` | `supersede()` | `SUPERSEDED` |
| `ACTIVE` | `archive()` | `ARCHIVED` |
| `ARCHIVED` | `restore()` | `ACTIVE` |
| `SUPERSEDED` | — | 终态；仅可被 `delete()` 物理移除 |
| `ARCHIVED` | `delete()` | 物理移除（删除是 Store 操作，不是状态转换） |

规则：

- `SUPERSEDED` 是终态，不能回到 `ACTIVE`，也不能再被 archive。
- `restore()` 仅适用于 `ARCHIVED`；`supersede()` 与 `archive()` 仅适用于
  `ACTIVE`。
- 违反转换规则的操作抛出 `ValueError`。
- 状态不能通过 `update()` 直接修改（`TypeError`）；状态变更只能通过上述
  领域操作完成。
- `delete()` 可作用于 Store 中任意状态的 Memory，物理移除后不可恢复。

### 5.2 遗忘维度（与状态正交）

遗忘是独立于生命周期的第二个维度，由 `forgotten_at` 表达：

| 操作 | 效果 | 状态限制 |
| --- | --- | --- |
| `forget()` | 设置 `forgotten_at` | 无（任意状态均可） |
| `unforget()` | 清除 `forgotten_at` | 无（任意状态均可） |

规则：

- `forget()` / `unforget()` **不改变** `status`。
- `restore()` **不改变** `forgotten_at`。两个维度完全独立：一个 ARCHIVED
  且被遗忘的 Memory，`unforget()` 后仍是 ARCHIVED；`restore()` 后回到
  ACTIVE，但若曾被遗忘则仍保持遗忘状态。
- 被遗忘的 Memory 默认不参与 `recall()` 与 `list()`（见 §7），但仍保留
  在 Store 中，可通过 `unforget()` 恢复。
- 重复 `forget()` 会刷新 `forgotten_at`。

### 5.3 语义区分

- **SUPERSEDED ≠ 删除**：被替代的 Memory 保留在 Store 中，`id`、内容与
  血缘（provenance）可查，是 Consolidation 与审计的基础。
- **ARCHIVED ≠ 删除**：归档的 Memory 可 `restore()` 回 ACTIVE；被删除的
  Memory 物理消失，不可恢复。

## 6. MemoryStore

`MemoryStore` 是所有持久化实现必须遵守的最小接口，Phase 02 保持不变：

```python
class MemoryStore(Protocol):
    def add(self, item: MemoryItem) -> MemoryItem: ...
    def get(self, item_id: str) -> MemoryItem | None: ...
    def update(self, item: MemoryItem) -> MemoryItem: ...
    def delete(self, item_id: str) -> bool: ...
    def list(self) -> list[MemoryItem]: ...
```

### 6.1 方法语义

| 方法 | 语义 | 失败行为 |
| --- | --- | --- |
| `add(item)` | 保存一个新 Memory，并返回该对象 | `id` 已存在时抛出 `ValueError` |
| `get(item_id)` | 按稳定 ID 获取 Memory | 不存在时返回 `None` |
| `update(item)` | 用同 ID 的新对象替换已有 Memory | ID 不存在时抛出 `KeyError` |
| `delete(item_id)` | 永久删除 Memory | 删除不存在的 ID 返回 `False` |
| `list()` | 返回当前 Memory 的快照 | 返回新列表，不暴露 Store 内部容器 |

### 6.2 InMemoryStore

`InMemoryStore` 仍是 Phase 02 唯一的 Store 参考实现，使用 Python `dict`
保存数据，Phase 01 的全部保证不变：

- 按插入顺序返回 `list()` 结果。
- 不允许 `add()` 静默覆盖相同 ID 的对象。
- `delete()` 是幂等的。
- `update()` 不改变对象在列表中的位置。

未来的数据库实现必须保持相同的上层语义。

## 7. MemoryService

`MemoryService` 是 Agent 或应用层使用的业务入口：

```text
MemoryService
├── remember()      # 创建（恒为 ACTIVE）
├── get()           # 按 id 精确获取
├── list()          # 状态/类型/来源过滤的列表
├── recall()        # Phase 01 兼容入口（见 §8）
├── update()        # 修改 ACTIVE Memory 的业务字段
├── forget() / unforget()     # 遗忘维度
├── archive() / restore()     # 生命周期维度
├── supersede()     # 替代并创建后继
├── delete()        # 物理删除
└── consolidate()   # Phase 08 入口，当前抛 NotImplementedError
```

### 7.1 `remember()`

```python
remember(
    content,
    *,
    type="fact",
    source=None,
    created_at=None,
    valid_from=None,
    importance=0.5,
    metadata=None,
    provenance=None,
    id=None,
) -> MemoryItem
```

创建并保存 `MemoryItem`。新建 Memory 恒为 `status=ACTIVE`、
`valid_until=None`、`forgotten_at=None`，不暴露对应参数。`type` 接受
`MemoryType` 成员或任意非空字符串。

### 7.2 `get()` / `list()` / `recall()`

```python
get(item_id) -> MemoryItem | None
list(*, status=MemoryStatus.ACTIVE, type=None, source=None,
     include_forgotten=False, limit=None) -> list[MemoryItem]
recall(*, type=None, source=None, include_forgotten=False,
       limit=None) -> list[MemoryItem]
```

- `get()` 返回任意状态、包含被遗忘的 Memory；未命中返回 `None`。
- `list()` 默认返回 `ACTIVE` 且未被遗忘的 Memory；`status=None` 表示
  不过滤状态（`SUPERSEDED` / `ARCHIVED` 也会返回）；`status` 传具体值时
  精确匹配。`include_forgotten=True` 包含 `forgotten_at` 非空的条目。
- `recall()` 等价于 `list(status=ACTIVE, ...)` 并叠加 legacy 过滤
  `importance > 0`（见 §8）。它不提供 `status` 参数，保持 Phase 01
  签名。
- `type` / `source` 为精确匹配过滤器；返回顺序与 Store 的 `list()` 顺序
  一致；`limit` 为非负整数，负数抛出 `ValueError`。

接口边界：

- `list()` 是**结构化浏览 / 管理接口**：按 `status`、`type`、`source`
  等确定性条件列出条目，服务于管理与诊断场景。
- `recall()` 是**面向 Agent 的候选 Memory 获取接口**：Phase 02 只承担
  Phase 01 兼容查询加 status / 遗忘基础过滤，不承担真正的 Retrieval
  职责。
- 两个接口都不得引入 semantic similarity、ranking、recency score、
  importance ranking；这些属于后续 Retrieval 阶段（Phase 06 / 07）。

### 7.3 `update()`

```python
update(item_id, **changes) -> MemoryItem
```

允许更新：`content`、`type`、`source`、`valid_from`、`valid_until`、
`importance`、`metadata`、`provenance`（`kind` 作为 `type` 的兼容别名
继续接受）。

规则：

- `id`、`created_at`、`updated_at` 不能由调用方直接修改；有实际变更时
  Service 自动刷新 `updated_at`。
- `status` 与 `forgotten_at` 不在白名单内（`TypeError`）——状态变更必须
  走转换方法，遗忘必须走 `forget()` / `unforget()`。
- 仅 `status=ACTIVE` 的 Memory 可被 `update()`；其余状态抛
  `ValueError`（`ARCHIVED` 可先 `restore()`；`SUPERSEDED` 是终态，不可
  再修改）。

### 7.4 `forget()` 与 `unforget()`

```python
forget(item_id) -> MemoryItem
unforget(item_id) -> MemoryItem
```

- `forget()` 将 `forgotten_at` 设置为当前时间并刷新 `updated_at`；
  `importance` 与 `status` 不变。重复调用会刷新 `forgotten_at`。
- `unforget()` 清除 `forgotten_at`；对未遗忘的 Memory 是幂等操作
  （直接返回当前对象，不刷新 `updated_at`）。
- Memory 不存在时两者抛出 `KeyError`。

### 7.5 `archive()` 与 `restore()`

```python
archive(item_id) -> MemoryItem
restore(item_id) -> MemoryItem
```

- `archive()` 将 `ACTIVE` Memory 转为 `ARCHIVED`；对非 ACTIVE 状态抛
  `ValueError`。
- `restore()` 将 `ARCHIVED` Memory 转回 `ACTIVE`；对非 ARCHIVED 状态抛
  `ValueError`。不改变 `forgotten_at`。
- Memory 不存在时抛出 `KeyError`。

### 7.6 `supersede()`

`supersede()` 是完整的领域操作，不是单纯的状态修改：

```python
supersede(item_id, content, **overrides) -> MemoryItem
```

步骤（领域原子性）：

1. 读取旧 Memory：不存在抛 `KeyError`；`status != ACTIVE` 抛
   `ValueError`（非法转换）。
2. 以当前时间 `t` 创建后继 MemoryItem：
   - 全新 `id`，`created_at = updated_at = t`；
   - `content` 使用新值；
   - `status = ACTIVE`，`forgotten_at = None`（不继承）；
   - `type`、`source`、`importance`、`metadata` 继承旧值，可被
     `overrides` 覆盖；
   - `provenance` **不继承**，初始为 `{"supersedes": old_id}`；
     `overrides` 提供的 provenance 与之合并，但 `"supersedes"` 键不可被
     覆盖；
   - `valid_from` 默认 `t`（新事实从替代时刻起有效），`valid_until`
     默认 `None`（当前有效），均可被 `overrides` 覆盖。
3. `store.add(new)`。
4. 更新旧 Memory：`status = SUPERSEDED`、`updated_at = t`、`provenance`
   合并 `{"superseded_by": new.id}`；若旧 `valid_until` 为空则闭合为
   `t`（旧事实的有效区间随替代结束）。
5. 返回后继 Memory。

`overrides` 白名单：`type`、`source`、`importance`、`metadata`、
`provenance`、`valid_from`、`valid_until`；未知键抛 `TypeError`。

原子性：`supersede()` 必须具有原子领域语义。实现采用**预校验 + 可回滚
补偿**：先完成全部校验，再 `add()` 后继、再 `update()` 旧条目；若
`update()` 失败，必须回滚刚创建的后继（将其从 Store 中删除）并重新抛出
异常，保证失败不留下半完成的替代状态。真正的持久化事务随 Phase 10 的
PostgreSQL Store 实现，Service 层接口不变。

### 7.7 `delete()`

```python
delete(item_id) -> bool
```

物理删除，作用于 Store 中任意状态的 Memory；删除不存在的 ID 返回
`False`。语义与 Phase 01 一致。

### 7.8 `consolidate()`

Phase 02 只声明 `consolidate()` 入口，不实现默认合并策略。调用时明确抛出
`NotImplementedError`。`supersede()` 建立的 provenance 血缘是 Phase 08
Consolidation 的输入之一。

## 8. 兼容性与 Legacy 行为

Phase 02 对 Phase 01 契约的变更与保留清单：

| 项 | 处理 |
| --- | --- |
| `valid_at` → `valid_from` | 完全重命名，不保留兼容别名；受影响的 Phase 01 测试同步更新 |
| `forget()` 的 importance=0 语义 | 已迁移到 `forgotten_at`；`forget()` 不再修改 `importance`，恢复使用 `unforget()` |
| `recall()` 的 `importance > 0` 过滤 | 保留为 legacy 兼容（Phase 01 存在以 importance=0 表达遗忘的数据）；标记为待移除，Phase 09 Forgetting 时清理 |
| 默认 `type="fact"` | 保留为 legacy 默认值；不属于 `MemoryType` 标准集合 |
| `kind` 别名 | 继续作为 `type` 的兼容别名 |
| `MemoryStatus` 不含 `DELETED` | 删除是 Store 操作而非状态（Phase 02 指令中的四状态枚举据此调整） |

除上表外，Phase 01 行为保持不变：`InMemoryStore` 语义、`update()` 白名单
机制、`delete()` 物理删除、`consolidate()` 延迟。

## 9. 代码布局

```text
agent_lab/
└── memory/
    ├── __init__.py    # 公共导出
    ├── lifecycle.py   # MemoryType / MemoryStatus / 转换规则（Phase 02 新增）
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
    ├── test_lifecycle.py   # Phase 02 新增
    └── test_service.py
```

## 10. Phase 02 验收标准

- [ ] `MemoryType` 定义 WORKING / EPISODIC / SEMANTIC / PROCEDURAL，
      `type` 字段保持开放字符串。
- [ ] `MemoryStatus` 定义 ACTIVE / SUPERSEDED / ARCHIVED；删除是操作
      而非状态。
- [ ] 生命周期转换规则明确并由 Service 校验；非法转换与直接修改状态
      均被拒绝。
- [ ] `forgotten_at` 遗忘维度与状态正交；`forget()` / `unforget()` 可逆
      且不影响 `importance` 与 `status`。
- [ ] `MemoryService` 提供 remember / get / list / recall / update /
      forget / unforget / archive / restore / supersede / delete /
      consolidate。
- [ ] `MemoryService` 仅通过 `MemoryStore` 访问存储。
- [ ] `InMemoryStore` 仍是唯一 Store 实现，Phase 01 语义不变。
- [ ] `supersede()` 原子创建后继并建立双向 provenance 血缘与 valid 区间
      闭合；`update()` 失败时回滚后继，不留下半状态。
- [ ] 测试覆盖：Memory Type、Lifecycle、update、supersede、archive、
      forget、非法状态转换、provenance、temporal fields。
- [ ] 除 §8 显式清单外不破坏 Phase 01 行为。
- [ ] spec / roadmap / README 与实际实现一致。

## 11. 后续演进约束

1. Phase 03 增加 Conversation、Message 和 Session，通过 `source` 与
   `provenance` 关联来源，不向 `MemoryItem` 增加顶层实体字段。
2. Phase 04 增加 Extraction 层，不让 LLM 调用渗入 `MemoryStore` 或
   `MemoryService`。
3. Phase 05 的 Temporal Validity 在 `valid_from` / `valid_until` 之上
   构建，不再重命名字段。
4. Phase 08 的 Consolidation 可消费 `supersede()` 建立的 provenance
   血缘（`supersedes` / `superseded_by`）。
5. Phase 09 的 Forgetting 引入遗忘策略，并移除 `recall()` 的
   `importance > 0` legacy 过滤。
6. Phase 10 通过新的 Store 实现接入 PostgreSQL + pgvector，保持
   Service 依赖的接口稳定，并引入真正的事务语义。
7. Phase 11 最后接入 Agent Runtime，Agent 不直接访问数据库。
