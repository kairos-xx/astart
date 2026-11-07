# `docs/`

Use `from astart import ...`. The `astart.semantic` and `astart._graph` trees are implementation modules; the latter is not a separate distribution.

<!-- exactus:inventory:start -->
## Directory contents

### Files

- [`API.md`](API.md) — Use `from astart import ...`. The `astart.semantic` and `astart._graph` trees are implementation modules; the latter is not a separate distribution.
- [`CONSOLIDATION.md`](CONSOLIDATION.md) — All code now lives under `src/astart/`, with one installable package and one supported top-level import API. The lexical AST, source editor, semantic solver, and graph converter are components of this distribution. The graph converter is internal to `astart._graph` and contributes verified annotation candidates to `astart.semantic` through `semantic.graph_conversion`.

### Subdirectories

- [`superpowers/`](superpowers/README.md) — > **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- \\\[ \\\]`) syntax for tracking.

<!-- exactus:inventory:end -->
