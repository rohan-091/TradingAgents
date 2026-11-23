# Harness² Autonomous Execution & Human-on-the-Loop Protocol

> **Reference**: Google Cloud AI Research & Northwestern University — *Harness²: Recursive Agent Harnessing for an Open World* (arXiv:2610.14224).

All Claude and AI operations in `TradingAgents` MUST follow the two levels of recursive harnessing to maintain **Human-on-the-Loop (HOTL)** autonomy:

## 1. Zero Human-in-the-Loop Babysitting
- The human operates strictly as executive supervisor.
- Never ask trivial questions or request human debugging of compiler/test errors.
- Self-heal autonomously.

## 2. Minimum Token Consumption Mandate
- ALWAYS query the knowledge graph (`code-review-graph` / `graphify`) BEFORE file scanning.
- Use `semantic_search_nodes`, `query_graph`, and `get_review_context`.
- Never dump entire files into context when a targeted slice is sufficient.

## 3. Level 1: Task-Level Recursion (Propose -> Probe -> Compose)
- **Propose**: Analyze constraints (Zero-Mock financial feeds, model provider policy, graph state topology).
- **Probe**: Contrastive validation against files, types, and schemas before editing.
- **Compose**: Implement complete code and run `python scripts/harness/harness_pipeline.py --verify`.

## 4. Level 2: Harnessing-Level Recursion (Meta-Evolution)
- Extract meta-learnings and distill into repository memory.
- Run `python scripts/harness/harness_pipeline.py --distill`.
