# Memory System Roadmap

> Agent Lab 当前主攻方向：**Agent Memory System**
>
> 本文定义学习范围、架构边界与演进路线，作为后续实验与实现的约束。

## 1. 目标

构建一个可独立于具体 Agent Framework 的 Memory System，逐步理解并实现：

- Memory 生命周期
- 短期记忆与长期记忆
- Episodic / Semantic / Procedural Memory
- Memory Extraction
- Retrieval
- Memory Consolidation
- Forgetting / Update / Delete
- Memory Evaluation
- 与 Agent Runtime 集成

最终形成：

```text
User
  ↓
Agent Runtime
  ├── Memory Read
  │      ↓
  │   Retrieval
  │      ↓
  │   Context
  │
  ├── LLM / Tools
  │
  └── Memory Write
         ↓
      Extraction
         ↓
      Memory Store
```

## 2. 架构边界

### 2.1 Memory System 负责

- Memory 数据模型
- Memory 生命周期
- Memory 写入与更新
- Memory 检索
- 过滤与排序
- 去重、合并与压缩
- 遗忘与删除
- Memory Evaluation
- Storage 抽象

### 2.2 Memory System 不负责

以下能力属于 Agent Runtime 或其他基础设施：

- Agent Loop
- Tool Calling
- Handoff
- Agent Planning
- LLM Provider
- MCP Runtime
- Agent 权限系统

原则：Memory 是 Agent 的基础能力，但不是 Agent Runtime 本身。

## 3. 核心抽象

Memory System 的核心数据流：

```text
Memory
  ↓
MemoryStore
  ↓
Retrieval
  ↓
Memory Processing
  ↓
Agent Context
```

核心接口建议保持稳定：

- `Memory`
- `MemoryStore`
- `Retriever`
- `MemoryExtractor`
- `MemoryConsolidator`
- `MemoryEvaluator`

Storage 与 Memory Logic 必须解耦：

```text
MemoryStore
├── InMemoryStore
├── PostgresMemoryStore
└── VectorMemoryStore
```

上层 Memory Logic 不应依赖具体数据库。

## 4. Memory 分类

第一阶段不强制绑定某一种分类体系，逐步验证不同 Memory 类型的实际价值。

目标覆盖：

```text
Memory
├── Working Memory
├── Short-Term Memory
├── Episodic Memory
├── Semantic Memory
└── Procedural Memory
```

### Working Memory

当前 Agent Run 所需的临时上下文。

### Short-Term Memory

短周期会话信息，重点研究生命周期与上下文窗口管理。

### Episodic Memory

记录具体事件、经历及其时间和上下文。

### Semantic Memory

从多个事件中抽取的稳定事实、知识与用户偏好。

### Procedural Memory

描述 Agent 应如何执行某类任务的经验或规则。

## 5. 学习路线

### Phase 01 — Basic Memory

#### 目标

- 定义 `MemoryItem`
- 定义 `MemoryStore`
- 实现 In-Memory Store
- 实现 CRUD
- 建立测试体系

#### 产出

- `MemoryItem`
- `MemoryStore`
- `InMemoryStore`
- `MemoryService`

详细设计见 [Memory System Specification](./memory-system-spec.md)。

### Phase 02 — Memory Types & Lifecycle

#### 目标

- 建立标准 Memory 类型集合，同时保持 `type` 字段开放可扩展
- 定义 Memory 生命周期状态与状态转换规则
- 将遗忘建模为与状态正交的独立维度
- 以 `MemoryService` 领域操作承载生命周期

#### 产出

- `MemoryType`（WORKING / EPISODIC / SEMANTIC / PROCEDURAL，`type` 字段开放）
- `MemoryStatus`（ACTIVE / SUPERSEDED / ARCHIVED；删除是操作而非状态）
- Lifecycle 转换规则与校验
- `forgotten_at` 遗忘维度（forget / unforget）
- `MemoryService` 扩展：get / list / archive / restore / unforget / supersede

说明：Roadmap 初稿中的 `MemoryMetadata` 类型化类与 `MemoryLifecycle`
独立产物，经 Phase 02 设计评审后调整——`metadata` 保持 `Mapping[str, str]`，
生命周期由 `MemoryStatus` 与转换规则承载。详见
[Memory System Specification](./memory-system-spec.md)。

### Phase 03 — Conversation Memory

#### 目标

- 保存 Conversation
- 保存 Message
- 管理 Session
- 研究上下文窗口限制

#### 产出

- `Conversation`
- `Message`
- `Session`
- `ConversationMemory`

### Phase 04 — Memory Extraction

#### 目标

研究如何从对话中识别值得长期保存的信息。

```text
Conversation
    ↓
Candidate Memories
    ↓
Validation
    ↓
Persist
```

#### 重点

- 从对话中提取事实
- 判断是否值得记忆
- 去除无价值信息
- 处理冲突信息

### Phase 05 — Semantic Memory

#### 目标

建立从 Episodic Memory 到 Semantic Memory 的转换：

```text
Events
  ↓
Extraction
  ↓
Facts
  ↓
Semantic Memory
```

#### 重点

- Fact
- Entity
- Attribute
- Preference
- Relationship
- Temporal Validity

### Phase 06 — Retrieval

#### 目标

实现基础 Memory Retrieval Pipeline：

```text
Query
  ↓
Candidate Retrieval
  ↓
Filtering
  ↓
Ranking
  ↓
Relevant Memories
```

#### 逐步比较

- Keyword Retrieval
- Vector Retrieval
- Metadata Filtering
- Hybrid Retrieval
- Reranking

### Phase 07 — Hybrid Retrieval

#### 目标

组合多种检索信号：

```text
Keyword
   +
Vector
   +
Metadata
   +
Recency
   +
Importance
```

形成统一 Retrieval Pipeline。

#### 重点

- Relevance
- Recency
- Importance
- Diversity
- User / Entity Filtering

### Phase 08 — Memory Consolidation

#### 目标

研究 Memory 如何从大量事件逐步形成稳定知识。

```text
Raw Memories
     ↓
Deduplication
     ↓
Conflict Resolution
     ↓
Summarization
     ↓
Consolidation
     ↓
Long-Term Memory
```

#### 重点

- 合并重复 Memory
- 更新旧事实
- 解决事实冲突
- 压缩历史信息

### Phase 09 — Forgetting & Evaluation

#### 目标

研究完整 Memory 生命周期：

```text
Remember
   ↓
Update
   ↓
Consolidate
   ↓
Forget
   ↓
Delete
```

同时建立 Memory Evaluation。

#### 核心指标

- Retrieval Recall
- Retrieval Precision
- Relevance
- Freshness
- Memory Accuracy
- Context Utility

### Phase 10 — Persistent Storage

#### 目标

将 In-Memory Store 替换为持久化实现。

第一阶段推荐：

- PostgreSQL
- pgvector

架构：

```text
Memory Logic
     ↓
MemoryStore Interface
     ↓
PostgresMemoryStore
     ├── PostgreSQL
     └── pgvector
```

Storage 实现不应改变上层 Memory API。

### Phase 11 — Agent Integration

#### 目标

最后再将 Memory System 接入 Agent Runtime。

```text
                Agent
                  │
        ┌─────────┴─────────┐
        ↓                   ↓
   Memory Read         Memory Write
        │                   │
        ↓                   ↓
   Retrieval           Extraction
        │                   │
        └─────────┬─────────┘
                  ↓
             Memory System
```

Agent Runtime 通过稳定接口使用 Memory：

```text
read()
write()
update()
delete()
search()
```

Agent Runtime 不应直接操作 Memory 数据库。

## 6. 最终目标架构

```text
                    Agent Runtime
                          │
             ┌────────────┴────────────┐
             ↓                         ↓
        Memory Read              Memory Write
             │                         │
             ↓                         ↓
        Retrieval                 Extraction
             │                         │
      ┌──────┼──────┐                  ↓
      ↓      ↓      ↓             Validation
   Keyword Vector Metadata             │
      │      │      │                  ↓
      └──────┼──────┘             Memory Store
             ↓                         │
          Ranking                     ↓
             │                  ┌─────┴─────┐
             ↓                  ↓           ↓
      Relevant Memories      PostgreSQL   Vector
             │
             ↓
       Agent Context
```

## 7. Memory 生命周期

Memory 不只是简单的 CRUD，而是一个完整生命周期：

```text
Input
  ↓
Candidate
  ↓
Extraction
  ↓
Validation
  ↓
Store
  ↓
Retrieve
  ↓
Use
  ↓
Update / Consolidate
  ↓
Forget / Delete
```

其中：

- **Extraction**：从原始信息中识别潜在 Memory
- **Validation**：判断 Memory 是否有效、有价值
- **Store**：持久化
- **Retrieve**：根据当前任务寻找相关 Memory
- **Use**：注入 Agent Context
- **Update**：修正已有 Memory
- **Consolidate**：合并多个 Memory
- **Forget**：降低重要性或移除
- **Delete**：显式删除

## 8. 工程原则

### 8.1 Framework Agnostic

Memory System 不绑定：

- OpenAI Agents SDK
- LangChain
- LlamaIndex
- Anthropic SDK

这些框架只能作为调用方。

### 8.2 Interface First

优先定义稳定接口：

- `Memory`
- `MemoryStore`
- `Retriever`
- `MemoryExtractor`
- `MemoryConsolidator`
- `MemoryEvaluator`

再实现具体版本。

### 8.3 Experiment First

新概念优先进入：

`experiments/memory/`

用于验证设计。

概念稳定后，再沉淀到：

`agent_lab/memory/`

原则：

```text
Experiment
    ↓
Validation
    ↓
Abstraction
    ↓
Production-oriented Implementation
```

### 8.4 Test First

Memory 核心行为必须有测试覆盖。

重点测试：

- CRUD
- Retrieval
- Ranking
- Deduplication
- Conflict Resolution
- Consolidation
- Forgetting
- Evaluation

### 8.5 Storage Independence

业务逻辑不得直接依赖：

- PostgreSQL
- Redis
- Vector DB
- 具体 ORM

统一通过 `MemoryStore` 等抽象访问 Storage。

### 8.6 Evaluation Driven

任何 Retrieval、Extraction、Consolidation 策略的优化，都应该尽可能通过 Evaluation 验证。

不能只依据 Demo 效果判断方案优劣。

### 8.7 Minimal Dependencies

学习阶段优先使用：

```text
Python Standard Library
        ↓
必要基础依赖
        ↓
具体 Agent / RAG / Storage 依赖
```

不提前引入大量框架。

引入依赖必须有明确学习或实验目的。

## 9. 项目目录建议

```text
agent-lab/
│
├── agent_lab/
│   ├── core/
│   ├── memory/
│   └── utils/
│
├── experiments/
│   └── memory/
│       ├── 01_basic/
│       ├── 02_memory_types/
│       ├── 03_conversation/
│       ├── 04_extraction/
│       ├── 05_semantic/
│       ├── 06_retrieval/
│       ├── 07_hybrid_retrieval/
│       ├── 08_consolidation/
│       ├── 09_evaluation/
│       ├── 10_persistence/
│       └── 11_agent_integration/
│
├── tests/
│   └── memory/
│
├── docs/
│   └── memory-system-roadmap.md
│
├── scripts/
│
├── pyproject.toml
├── uv.lock
├── .python-version
├── .env.example
└── README.md
```

## 10. 项目演进方向

```text
In-Memory
    ↓
Memory Model
    ↓
Conversation Memory
    ↓
Extraction
    ↓
Semantic Memory
    ↓
Retrieval
    ↓
Hybrid Retrieval
    ↓
Consolidation
    ↓
Evaluation
    ↓
PostgreSQL + pgvector
    ↓
Agent Integration
    ↓
Production Memory System
```

Memory System 完成基础建设后，再向其他 Agent 系统能力扩展：

```text
                    Agent System
                         │
          ┌──────────────┼──────────────┐
          ↓              ↓              ↓
       Memory           RAG        Agent Runtime
          │                             │
          └──────────────┬──────────────┘
                         ↓
                       MCP
                         ↓
                    Multi-Agent
                         ↓
                     Evaluation
                         ↓
                  Harness / Sandbox
```

## 11. 学习优先级

当前阶段遵循：

```text
Memory Fundamentals
        ↓
Memory Architecture
        ↓
Retrieval
        ↓
Memory Extraction
        ↓
Memory Consolidation
        ↓
Evaluation
        ↓
Persistence
        ↓
Agent Integration
```

暂不以以下内容作为主要学习目标：

- Framework API
- Prompt Tricks
- 大量第三方组件
- 复杂 Multi-Agent

## 12. 核心原则

- 先理解 Memory 机制，再引入框架。
- 先建立可测试的抽象，再追求生产级实现。
- 先通过实验验证设计，再沉淀通用能力。
- Memory System 与 Agent Runtime 解耦。
- 所有关键策略都应能够被 Evaluation 验证。
