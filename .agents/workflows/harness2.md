---
name: harness2
description: Mandatory Harness² recursive execution workflow (Propose -> Probe -> Compose) ensuring autonomous Human-on-the-Loop operation.
---

# Workflow: Harness² Autonomous Execution

Execute tasks under the **Harness² (arXiv:2610.14224)** protocol for autonomous **Human-on-the-Loop (HOTL)** operation:

1. **Propose**: Analyze the request, identify architectural constraints (TradingAgents state schema, LLM provider policies, zero mock data).
2. **Probe**: Contrastive validation against repository files using knowledge graph MCP tools first to minimize token usage.
3. **Compose**: Implement complete changes, run `python scripts/harness/harness_pipeline.py --verify`, and self-heal any failures autonomously.
4. **Distill**: Run `python scripts/harness/harness_pipeline.py --distill` to commit meta-learnings into repository memory.
