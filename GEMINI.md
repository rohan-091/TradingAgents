# Project Guidelines: TradingAgents

# GOLDEN RULE — MANDATORY HARNESS² EXECUTION & HUMAN-ON-THE-LOOP (HOTL) PROTOCOL
- **Mandatory Harness² Execution (Google Research arXiv:2610.14224)**:
  - Every agent prompt, feature addition, refactoring, and bug fix MUST pass through the two levels of recursive agent harnessing:
    1. **Level 1 (Task-Level Recursion: Propose -> Probe -> Compose)**:
       - **Propose**: Formulate hypothesis, inspect architectural constraints (TradingAgents graph state schema, agent roles, zero-mock market data, zero dead models), and define verification goals.
       - **Probe**: Contrastive validation against AST, files, schemas, and live repository reality via Knowledge Graph before making changes.
       - **Compose**: Implement complete, robust code and run `python scripts/harness/harness_pipeline.py --verify`.
    2. **Level 2 (Harnessing-Level Recursion: Meta-Evolution & Knowledge Distillation)**:
       - Codify discovered edge cases and lessons into repository rules/skills and run `python scripts/harness/harness_pipeline.py --distill`.
- **Absolute Prohibition of Human-in-the-Loop (HITL) Anti-Patterns**:
  - The human operates strictly **Human-on-the-Loop (HOTL)** (defining goals, setting constraints, reviewing verified deliverables).
  - Under NO circumstances may the agent ask trivial steering questions, request syntax decisions from the user, push unverified code, or paste compiler/lint errors asking the human how to fix them.
  - The agent owns 100% autonomous execution, self-healing, and end-to-end verification.

# MINIMUM TOKEN USAGE MANDATE
- **Knowledge Graph First**: Always query `code-review-graph` MCP tools (`semantic_search_nodes`, `query_graph`, `get_review_context`) BEFORE using Grep/Glob/Read. The graph is faster, costs up to 85% fewer tokens, and provides structural context that raw file scanning cannot.
- **Targeted File Inspection**: Use slice notation (`StartLine`/`EndLine`) when viewing files. Never load massive files into prompt context unnecessarily.
- **AST-Only Updates**: Run `code-review-graph update` or `graphify extract . --code-only` for local AST updates without LLM API overhead.

<!-- code-review-graph MCP tools -->
## MCP Tools: code-review-graph

**IMPORTANT: This project has a knowledge graph. ALWAYS use the
code-review-graph MCP tools BEFORE using Grep/Glob/Read to explore
the codebase.** The graph is faster, cheaper (fewer tokens), and gives
you structural context (callers, dependents, test coverage) that file
scanning cannot.

### When to use graph tools FIRST

- **Exploring code**: `semantic_search_nodes` or `query_graph` instead of Grep
- **Understanding impact**: `get_impact_radius` instead of manually tracing imports
- **Code review**: `detect_changes` + `get_review_context` instead of reading entire files
- **Finding relationships**: `query_graph` with callers_of/callees_of/imports_of/tests_for
- **Architecture questions**: `get_architecture_overview` + `list_communities`

Fall back to Grep/Glob/Read **only** when the graph doesn't cover what you need.

### Key Tools

| Tool | Use when |
|------|----------|
| `detect_changes` | Reviewing code changes — gives risk-scored analysis |
| `get_review_context` | Need source snippets for review — token-efficient |
| `get_impact_radius` | Understanding blast radius of a change |
| `get_affected_flows` | Finding which execution paths are impacted |
| `query_graph` | Tracing callers, callees, imports, tests, dependencies |
| `semantic_search_nodes` | Finding functions/classes by name or keyword |
| `get_architecture_overview` | Understanding high-level codebase structure |
| `refactor_tool` | Planning renames, finding dead code |

### Mandatory Verification Command
```bash
python scripts/harness/harness_pipeline.py --verify
```
All 6 core gates must pass cleanly before any task is considered complete.
