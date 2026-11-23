# Harness²: Recursive Agent Harnessing Architecture

> **Reference Research**: Google Cloud AI Research & Northwestern University — *Harness²: Recursive Agent Harnessing for an Open World* (arXiv:2610.14224).

---

## 1. Executive Summary & Core Philosophy

State-of-the-art foundation model weights are fixed at inference time. Agent capabilities, reasoning depth, code quality, and operational reliability depend strictly on the **execution harness**:
- Multi-phase structured reasoning loops (Propose -> Probe -> Compose).
- Automated invariant verification gates prior to any deliverable output.
- Incremental repository knowledge graphs and token-conserving MCP tools.
- Strict Human-on-the-Loop (HOTL) protocol with zero human babysitting.

In this repository (`TradingAgents`), **every prompt, feature, refactoring, and bug fix operates under the Harness² execution protocol**.

---

## 2. Two Levels of Recursion

```
                     ┌───────────────────────────────────┐
                     │     Human-on-the-Loop (HOTL)      │
                     │  Sets High-Level Goals & Intent   │
                     └─────────────────┬─────────────────┘
                                       │
                                       ▼
+─────────────────────────────────────────────────────────────────────────────+
|                                  HARNESS²                                   |
+─────────────────────────────────────────────────────────────────────────────+
|                                                                             |
|   LEVEL 1: TASK-LEVEL RECURSION (Propose ──> Probe ──> Compose)             |
|   ─────────────────────────────────────────────────────────────             |
|   1. PROPOSE: Parse intent, model blast radius, identify domain invariants: |
|      - TradingAgents graph state schema integrity                           |
|      - Agent isolation (Market Analyst, Quant, Bull/Bear, Risk Manager)     |
|      - Zero-Mock financial data policy (live market groundedness)           |
|      - Strict model policy (zero dead or deprecated model invocations)      |
|      - Token minimization (query Knowledge Graph before Grep/Glob/Read)     |
|                                                                             |
|   2. PROBE (Contrastive Probing):                                           |
|      - Probe AST, symbols, imports, and live repository files via Graph.    |
|      - Validate edge cases and environment assumptions autonomously.        |
|      - Avoid full-corpus text dumps; use targeted slices and subgraphs.     |
|                                                                             |
|   3. COMPOSE (Autonomous Self-Healing Execution):                           |
|      - Implement drop-in, production-grade code.                            |
|      - Run automated verification gates (`python scripts/harness/harness_pipeline.py --verify`). |
|      - Self-heal compiler, lint, or test failures recursively without human |
|        intervention.                                                        |
|                                                                             |
|   LEVEL 2: HARNESSING-LEVEL RECURSION (Continuous Meta-Evolution)           |
|   ─────────────────────────────────────────────────────────────             |
|   1. Extract meta-learnings and tool quirks from the task.                  |
|   2. Codify lessons into `.agents/rules/` and `.claude/rules/`.             |
|   3. Synchronize `.agents/harness2_state.json` via `--distill`.             |
|   4. Subsequent agent sessions start with compounded repository memory.    |
|                                                                             |
+─────────────────────────────────────────────────────────────────────────────+
                                       │
                                       ▼
                     ┌───────────────────────────────────┐
                     │    Verified Deliverable Output    │
                     │      Passed All 6 Core Gates      │
                     └───────────────────────────────────┘
```

---

## 3. Mandatory Verification Gates (`python scripts/harness/harness_pipeline.py --verify`)

Every execution cycle must satisfy the 6 automated gates implemented in [`scripts/harness/harness_pipeline.py`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/scripts/harness/harness_pipeline.py):

| Gate # | Name | Verification Invariant |
|---|---|---|
| **Gate 1** | **Python AST & Compilation** | 100% clean AST parse across all python modules (`tradingagents/`, `cli/`, `tests/`, `scripts/`, `main.py`). |
| **Gate 2** | **LLM Model & Provider Policy** | Zero dead/deprecated models (e.g. `gpt-3.5-turbo-0301`, `text-davinci-003`, dead Claude/Gemini endpoints). |
| **Gate 3** | **TradingAgents Architecture** | Integrity of `TradingAgentsGraph`, agent definitions, dataflows, and llm_clients topologies. |
| **Gate 4** | **Zero-Mock Financial Grounding** | Zero static dummy numbers masking missing market data in production execution pipelines. |
| **Gate 5** | **Code Quality & Lint (Ruff)** | Zero lint regressions or syntax violations via `ruff check`. |
| **Gate 6** | **Knowledge Graph & Token Minimization** | Valid persistent knowledge graph (`graphify-out/graph.json`) and configured MCP tools (`code-review-graph`). |

---

## 4. Minimum Token Usage Architecture

Token efficiency is an operational imperative. The repository enforces:
1. **Knowledge Graph FIRST Exploration**:
   - `code-review-graph` and `graphify` indices provide structural context (callers, callees, imports, tests, communities).
   - MCP tools (`semantic_search_nodes`, `query_graph`, `get_review_context`, `detect_changes`) consume up to 85% fewer tokens than raw multi-file grep or full-file context dumps.
2. **Targeted Reading**:
   - Sliced view queries (`view_file` with `StartLine`/`EndLine`) instead of unconstrained dumps.
3. **AST-Only Updates**:
   - Graph updates (`code-review-graph update` / `graphify extract --code-only`) are local AST parsing jobs with zero LLM API cost.

---

## 5. Human-on-the-Loop (HOTL) Command Matrix

| Command | Action |
|---|---|
| `python scripts/harness/harness_pipeline.py --verify` | Run all 6 automated verification gates. |
| `python scripts/harness/harness_pipeline.py --distill` | Distill meta-learnings into repository memory state. |
| `python scripts/harness/harness_pipeline.py --all` | Run verification + distillation in one pass. |
| `code-review-graph status` | Inspect knowledge graph node, edge, and file metrics. |
| `code-review-graph update` | Incrementally refresh knowledge graph after modifications. |
| `ruff check tradingagents cli` | Run fast lint validation. |

---

## 6. Repository Policy Synchronization

The Harness² HOTL standard is bound into all platform rule surfaces:
- [`AGENTS.md`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/AGENTS.md)
- [`GEMINI.md`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/GEMINI.md)
- [`CLAUDE.md`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/CLAUDE.md)
- [`.cursorrules`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/.cursorrules)
- [`.windsurfrules`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/.windsurfrules)
- [`.agents/rules/harness2-recursive-execution.md`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/.agents/rules/harness2-recursive-execution.md)
- [`.agents/workflows/harness2.md`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/.agents/workflows/harness2.md)
- [`.agents/skills/harness2/SKILL.md`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/.agents/skills/harness2/SKILL.md)
