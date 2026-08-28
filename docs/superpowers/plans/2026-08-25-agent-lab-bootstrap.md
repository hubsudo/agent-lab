# Agent Lab Bootstrap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a GitHub-ready, uv-managed Agent learning lab optimized for memory-system experiments and reproducible setup on other computers.

**Architecture:** Keep project dependencies declared in `pyproject.toml` and exact versions in `uv.lock`; keep source code under `agent_lab`, experiments separate from reusable code, and provide shell scripts for bootstrap and environment checks. The initial memory implementation is intentionally minimal and dependency-light so storage/retrieval backends can be added later without coupling the learning lab to a framework.

**Tech Stack:** Python 3.12, uv, Pydantic, OpenAI Agents SDK, pytest, pytest-asyncio, python-dotenv, Git.

**Spec:** User-approved chat design for a scalable `agent-lab` learning repository focused initially on memory systems.

## Global Constraints

- Python version: 3.12.
- Dependency management: uv with committed `uv.lock`.
- Never commit `.venv`, `.env`, API keys, or machine-specific files.
- Memory abstractions must not depend on a specific vector database or Agent framework.
- New computers should be recoverable with Git + uv and one setup command.

---

### Task 1: Repository and project configuration

**Files:**
- Create: `pyproject.toml`
- Create: `.python-version`
- Create: `.gitignore`
- Create: `.env.example`
- Create: `README.md`
- Create: `scripts/setup.sh`
- Create: `scripts/check.sh`

- [ ] Define the uv project, Python floor, runtime dependencies, and test configuration.
- [ ] Add reproducible setup/check scripts.
- [ ] Document clone/setup/run/test workflow.

### Task 2: Memory core

**Files:**
- Create: `agent_lab/memory/models.py`
- Create: `agent_lab/memory/store.py`
- Create: `agent_lab/memory/in_memory.py`
- Create: `agent_lab/memory/__init__.py`
- Test: `tests/memory/test_in_memory.py`

**Interfaces:**
- `MemoryItem`: immutable Pydantic model with `content`, `kind`, `metadata` and generated `id`/`created_at`.
- `MemoryStore`: protocol exposing `add`, `get`, `delete`, and `list`.
- `InMemoryStore`: deterministic starter implementation for experiments.

- [ ] Write tests for add/get/list/delete behavior.
- [ ] Run tests and verify they fail before implementation.
- [ ] Implement the smallest store satisfying the tests.
- [ ] Run tests again and refactor only while green.

### Task 3: Package ergonomics and first experiment

**Files:**
- Create: `agent_lab/__init__.py`
- Create: `experiments/memory/01_basic/main.py`
- Create: `tests/test_imports.py`

- [ ] Expose the memory primitives cleanly from the package.
- [ ] Add a tiny executable memory experiment.
- [ ] Verify package imports and experiment execution.

### Task 4: Lock, validate, and GitHub handoff

**Files:**
- Create: `uv.lock`
- Create: `.gitkeep` files only where empty directories need preservation.

- [ ] Run `uv lock` and `uv sync`.
- [ ] Run the full test suite.
- [ ] Run setup/check validation in a clean environment where practical.
- [ ] Inspect Git status to ensure secrets and `.venv` are excluded.
- [ ] Create an initial local Git commit; do not push without explicit repository/credential instructions.
