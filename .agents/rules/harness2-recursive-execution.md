# GOLDEN RULE — MANDATORY HARNESS² EXECUTION & HUMAN-ON-THE-LOOP (HOTL) PROTOCOL

> **Reference Research**: Google Cloud AI Research & Northwestern University — *Harness²: Recursive Agent Harnessing for an Open World* (arXiv:2610.14224).

---

## 1. The Core Philosophy: Fixed Model Weights, Mutable Harness

Model weights (Gemini, Claude, GPT) are fixed at inference time. Agent performance, reliability, and precision depend entirely on the **execution harness**:
- Multi-step structured recursive loops (Propose -> Probe -> Compose).
- Automated invariant verification gates prior to any deliverable.
- Knowledge graph tools for token-efficient codebase understanding.
- Autonomous self-healing execution without human babysitting.

In this repository (`TradingAgents`), **every single agent prompt, feature implementation, and bugfix MUST pass through the Harness² protocol**.

---

## 2. Strict Prohibition of Human-in-the-Loop (HITL) Anti-Patterns

The user operates strictly **Human-on-the-Loop (HOTL)** as an executive supervisor who defines goals, constraints, and business intent.

### FORBIDDEN (Human-in-the-Loop Anti-Patterns):
1. **Never ask trivial steering questions**: Do not ask the user for file paths, variable names, syntax preferences, or obvious next steps.
2. **Never push unverified code**: Never write untested code and ask the user to "test it and let me know if it works".
3. **Never delegate error triage to the human**: If a compiler, lint, syntax, or test check fails, do NOT paste the stack trace and ask the user how to fix it. **Self-heal autonomously**.
4. **Never rely on synthetic mocks**: Do not use hardcoded fallback numbers or fake returns masking broken live data connectors.

### MANDATORY (Human-on-the-Loop Operating Standard):
- **Autonomous End-to-End Ownership**: The agent designs the plan, probes the environment, executes the changes, self-heals any errors, verifies all gates, and reports high-level verified results to the human.
- **Verification Proofs**: Every completed task must provide concrete verification evidence (Harness² gate pass, AST parse, Ruff lint).

---

## 3. Level 1: Task-Level Recursion (Propose ──> Probe ──> Compose)

For every task or user prompt, the agent must execute the three-phase loop:

```
[ Incoming Prompt / Intent ]
             │
             ▼
      1. PROPOSE
  - Hypothesize architecture & blast radius
  - Identify invariant constraints (TradingAgents graph state, zero dead models, zero mocks)
             │
             ▼
      2. PROBE (Contrastive Probing)
  - Query knowledge graph (code-review-graph / graphify) to minimize token consumption
  - Inspect AST, types, schemas, and live repository files
  - Validate hypotheses against live reality without assuming synthetic truth
             │
             ▼
      3. COMPOSE (Execute & Self-Heal)
  - Implement complete, production-grade modifications
  - Run verification gates: `python scripts/harness/harness_pipeline.py --verify`
  - If any gate fails: recursively diagnose and self-heal
             │
             ▼
[ Verified Execution Outcome ]
```

---

## 4. Level 2: Harnessing-Level Recursion (Meta-Evolution & Distillation)

After completing every task:
1. **Extract Meta-Learnings**: What unexpected edge case, API quirk, or domain nuance was discovered?
2. **Codify into Repository Memory**:
   - Update `.agents/rules/` if a general constraint was discovered.
   - Update `.agents/skills/` if a reusable workflow or tool pattern was identified.
   - Run `python scripts/harness/harness_pipeline.py --distill` to synchronize `.agents/harness2_state.json`.
3. **Future Immunity**: Subsequent agent sessions start with compounded, permanent intelligence.

---

## 5. Mandatory Verification Command

Before reporting any task complete, the agent MUST run:
```bash
python scripts/harness/harness_pipeline.py --verify
```
All 6 core gates must pass:
1. **Python AST & Syntax Compilation Gate**
2. **LLM Model & Provider Policy Gate**
3. **TradingAgents Architecture & Invariants Gate**
4. **Zero-Mock & Financial Grounding Gate**
5. **Code Quality & Lint Gate (Ruff)**
6. **Knowledge Graph & Token Minimization Gate**
