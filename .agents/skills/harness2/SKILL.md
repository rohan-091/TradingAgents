---
name: harness2
description: Mandatory Harness² recursive execution engine protocol (Propose -> Probe -> Compose) ensuring autonomous Human-on-the-Loop operation.
allowed-tools:
- run_command
- view_file
- write_to_file
- replace_file_content
- multi_replace_file_content
- grep_search
- list_dir
---

# Harness² Recursive Execution Protocol

> Reference: *Harness²: Recursive Agent Harnessing for an Open World* (arXiv:2610.14224, Google Cloud AI Research & Northwestern University).

This skill guides any agent operating in `TradingAgents` through the mandatory **Harness²** protocol to achieve autonomous **Human-on-the-Loop (HOTL)** operation without human babysitting.

---

## 1. Golden Rules of Human-on-the-Loop (HOTL)

1. **The Human is Executive Supervisor**: The human sets intent, goals, and architectural requirements.
2. **The Agent Owns Execution & Verification**:
   - Never ask trivial questions or ask the human to write boilerplate.
   - Never present unverified code.
   - If a compile error, lint error, or test failure occurs, **self-heal immediately** using recursive probing.
   - Strictly honor all repository golden rules (Zero-Mock mandate, model provider policy, graph invariant preservation).
   - Use the **Knowledge Graph FIRST** (`code-review-graph` / `graphify`) to minimize token consumption.

---

## 2. Execution Workflow

### Step 1: Propose
- Parse the user's intent.
- Formulate the architecture and determine affected boundaries:
  - Which TradingAgents modules are touched? (`agents/`, `graph/`, `dataflows/`, `llm_clients/`).
  - Are model references up to date (no deprecated models)?
  - Are financial calculations grounded in live market feeds (no mock data fallback masking errors)?
- Plan verification criteria.

### Step 2: Probe (Contrastive Probing)
- Validate assumptions using knowledge graph tools (`semantic_search_nodes`, `query_graph`, `get_impact_radius`) rather than large text dumps.
- Probe edge cases and environmental variables (`.env`, Python 3.12 compatibility).
- Run baseline verification:
  ```bash
  python scripts/harness/harness_pipeline.py --verify
  ```

### Step 3: Compose & Self-Heal
- Write clean, complete code (no truncated placeholders or TODOs).
- Run automated verification:
  ```bash
  python scripts/harness/harness_pipeline.py --verify
  ```
- If any check fails, do NOT stop and ask the user. Analyze the failure, apply the fix, and re-probe until all 6 gates pass cleanly.

### Step 4: Distill Meta-Learnings
- After verification passes, run:
  ```bash
  python scripts/harness/harness_pipeline.py --distill
  ```
- If an unexpected edge case or architectural insight was uncovered, record it in `.agents/rules/` so future agent runs inherit the insight.

---

## 3. Verification Commands Reference

| Command | Purpose |
|---|---|
| `python scripts/harness/harness_pipeline.py --verify` | Run all 6 Harness² verification gates. |
| `python scripts/harness/harness_pipeline.py --distill` | Synchronize meta-evolution state into `.agents/harness2_state.json`. |
| `python scripts/harness/harness_pipeline.py --all` | Run complete verification + meta-distillation in one pass. |
| `ruff check tradingagents cli` | Fast lint check. |
