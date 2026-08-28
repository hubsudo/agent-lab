# agent-lab

A reproducible Python/uv learning lab for AI Agent systems.

**Current focus:** memory systems — storage, retrieval, consolidation, context injection, and evaluation.

## Philosophy

This repository is deliberately small at the beginning. Reusable abstractions live in `agent_lab`; experiments live in `experiments/`; tests describe behavior. Add infrastructure only when an experiment needs it.

## Requirements

- Git
- [uv](https://docs.astral.sh/uv/)
- Python 3.12 (uv can install/manage it)

## New computer: one-time setup

```bash
git clone <YOUR_GITHUB_REPO_URL>
cd agent-lab
./scripts/setup.sh
```

After setup:

```bash
uv run python -m unittest discover -s tests -v
PYTHONPATH=. uv run python experiments/memory/01_basic/main.py
```

`uv.lock` is committed so dependency resolution is reproducible. `.venv/` and `.env` are intentionally ignored. The core template intentionally starts with zero third-party Python dependencies; add Agent/RAG infrastructure only when the corresponding experiment needs it (for example, `uv add openai-agents`).

## Layout

```text
agent-lab/
├── agent_lab/           # reusable learning code
│   └── memory/              # memory abstractions and starter stores
├── experiments/             # isolated learning experiments
├── tests/                   # executable specifications
├── scripts/                 # bootstrap and environment checks
├── pyproject.toml           # project/dependency declaration
├── uv.lock                  # exact dependency resolution
├── .python-version          # Python 3.12
└── .env.example             # secret template
```

## Learning roadmap

1. Basic memory model and CRUD
2. Short-term vs. long-term memory
3. Memory extraction from conversations
4. Semantic retrieval and embeddings
5. Hybrid retrieval and reranking
6. Memory consolidation / summarization
7. Context-window injection strategies
8. Memory evaluation
9. PostgreSQL + pgvector backend
10. Agent integration and production patterns

## Git workflow

Commit source, tests, configuration, `uv.lock`, and documentation. Never commit API keys or `.env`.

Before a commit:

```bash
./scripts/check.sh
git status --short
```
