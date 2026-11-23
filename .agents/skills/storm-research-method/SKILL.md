---
name: storm-research-method
description: Use when researching any topic that requires deep, multi-perspective analysis — business decisions, market research, feasibility studies, strategic questions, academic topics. Triggers when user asks research questions, feasibility questions, or "is it worth X" / "what should I do about X" type questions.
---

# STORM Research Method

## Overview

Stanford OVAL's STORM method compresses 40-60 hours of PhD-level research into 5 minutes by simulating multiple expert perspectives, mapping contradictions, synthesizing findings, and self-critiquing reliability. Published NAACL 2024 — peer reviewed, 25% more organized output than single-prompt research.

## When to Use

- User asks "is it worth X", "how should I approach Y", "research topic Z"
- Decision requires understanding multiple angles before action
- Topic has competing interests, hidden incentives, or contested evidence
- User needs actionable insight, not just summary

**When NOT to use:** Simple factual lookups, code questions, single-source data retrieval.

## The 4 Phases

### Phase 1 — Multi-Perspective Scan

Simulate 5 expert perspectives on `[TOPIC]`:

1. **PRACTITIONER** — works with this daily. What do they know that academics miss? What practical realities are ignored?
2. **ACADEMIC** — studied this for years. What does peer-reviewed evidence say? Where does evidence contradict popular belief?
3. **SKEPTIC** — thinks mainstream view is wrong. What is the strongest counterargument? What do proponents ignore?
4. **ECONOMIST** — follows the money. Who profits from current narrative? What financial incentives shape research?
5. **HISTORIAN** — has seen similar patterns before. What historical parallels exist? What can we learn from how those played out?

For each perspective: core position (2 sentences) + strongest evidence + one thing only they would say.

---

### Phase 2 — Contradiction Map

Based on the 5 perspectives:
1. Where do perspectives directly contradict each other? List each conflict with specific claims.
2. Which perspective has strongest evidence? Which weakest? Why?
3. What one question, if answered, would resolve the biggest contradiction?
4. What does EVERY perspective agree on? (This is likely true.)
5. What did NONE of the perspectives address? (This is the blind spot — often most valuable.)

---

### Phase 3 — Synthesis Briefing

1. **ONE PARAGRAPH SUMMARY** — brief a CEO who has 60 seconds and needs nuance, not headline.
2. **5 KEY FINDINGS** — ranked by reliability; note which perspectives support vs. challenge each.
3. **HIDDEN CONNECTION** — one non-obvious link that only shows up when looking at all 5 perspectives.
4. **ACTIONABLE INSIGHT** — what should someone in `[USER'S ROLE]` actually DO differently? Be specific.
5. **FRONTIER QUESTION** — the one question that, if answered, would change everything.

---

### Phase 4 — Peer Review

1. **CONFIDENCE SCORES** — rate each of the 5 key findings 1-10 for reliability. Explain each score.
2. **WEAKEST LINK** — which claim are you least confident in? What specific info would verify it?
3. **BIAS CHECK** — which perspective was overrepresented? Did one voice dominate?
4. **MISSING PERSPECTIVE** — is there a 6th angle that would change conclusions?
5. **OVERALL GRADE** — if a Stanford professor reviewed this, what grade and what to fix?

---

## Workflow

| Minute | Phase | Output |
|--------|-------|--------|
| 1 | Phase 1 | 5 expert views |
| 2-3 | Phase 2 | Contradiction map |
| 3-4 | Phase 3 | Briefing + action |
| 5 | Phase 4 | Reliability scores |

## Common Mistakes

- Skipping Phase 4 (self-critique) — this is what catches source bias
- Making all perspectives agree — force genuine tension between Skeptic and Academic
- Vague "Actionable Insight" — must be specific to user's role/situation
- Missing the "blind spot" question in Phase 2 — often the most valuable output
