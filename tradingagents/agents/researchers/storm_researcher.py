"""STORM (Stanford OVAL NAACL 2024) Multi-Perspective Research Agent for TradingAgents."""

from __future__ import annotations

from typing import Any

from tradingagents.agents.context import (
    get_instrument_context_from_state,
    get_language_instruction,
    report_or_absent,
)


def create_storm_researcher(llm: Any):
    """Create a STORM multi-perspective research node for the TradingAgents workflow.

    Implements Stanford OVAL's STORM method (NAACL 2024) across 4 structured phases:
    1. Multi-Perspective Scan (Practitioner, Academic, Skeptic, Economist, Historian)
    2. Contradiction Map (conflicts, evidence weights, crux question, consensus, blind spots)
    3. Synthesis Briefing (60s executive summary, 5 findings, hidden connection, action directive, frontier question)
    4. Peer Review & Self-Critique (confidence scores, weakest link, bias check, missing perspective, grade)
    """

    def storm_node(state: dict) -> dict:
        topic = state.get("company_of_interest") or state.get("research_topic") or "the target instrument"
        asset_type = state.get("asset_type", "stock")
        target_label = "stock" if asset_type == "stock" else "asset"

        market_research_report = report_or_absent(state.get("market_report"), "market")
        sentiment_report = report_or_absent(state.get("sentiment_report"), "sentiment")
        news_report = report_or_absent(state.get("news_report"), "news")
        fundamentals_report = report_or_absent(state.get("fundamentals_report"), "fundamentals")
        instrument_context = get_instrument_context_from_state(state)
        user_role = state.get("user_role", "Portfolio Manager")

        prompt = f"""You are the STORM Researcher Agent, an elite investigative research engine implementing Stanford OVAL's STORM method (Synthesis of Topic Outlines through Retrieval and Multi-perspective Question Asking, NAACL 2024).

Your objective is to conduct deep, rigorous, multi-perspective research on {topic} ({target_label}) using the 4-phase STORM framework. Avoid superficial summaries. Synthesize empirical data, map direct contradictions, uncover hidden incentives and blind spots, and deliver decision-grade intelligence.

---

### Phase 1 — Multi-Perspective Scan
Simulate 5 distinct expert perspectives on {topic}:
1. PRACTITIONER: Works on the frontlines daily. Focus on execution realities, operational friction, supply chain or customer-level truths academics overlook.
2. ACADEMIC: Evaluates long-term empirical data and peer-reviewed literature. Identifies where empirical evidence contradicts popular sentiment.
3. SKEPTIC: Contrarian stress-tester. What is the strongest bear/failure thesis? What critical assumptions are proponents ignoring?
4. ECONOMIST: Follows the money, capital allocation, unit economics, margin sustainability, and macroeconomic incentives.
5. HISTORIAN: Analyzes historical parallels, past market cycles, analogous technological or industry shifts, and lessons learned.

For each perspective, provide:
- Core Position (maximum 2 sentences)
- Strongest Empirical Evidence
- One Unique Insight only this perspective would voice

---

### Phase 2 — Contradiction Map
1. Direct Contradictions: Where do perspectives directly clash? State specific claims.
2. Evidence Weighting: Which perspective has the strongest vs. weakest empirical grounding? Why?
3. Crux Question: What single question, if answered, would resolve the biggest contradiction?
4. Universal Consensus: What do ALL perspectives agree on? (High probability of truth).
5. Blind Spot: What did NONE of the perspectives address? (Highest alpha opportunity).

---

### Phase 3 — Synthesis Briefing
1. One-Paragraph Executive Summary: Nuanced 60-second brief for a senior executive.
2. 5 Key Findings: Ranked by reliability (1-5), noting supporting vs. challenging perspectives.
3. Hidden Connection: One non-obvious systemic linkage revealed across all 5 viewpoints.
4. Actionable Directive: Specific recommendation tailored for the {user_role}.
5. Frontier Question: The one forward-looking question that could alter the entire thesis.

---

### Phase 4 — Peer Review & Self-Critique
1. Confidence Scores: Score each of the 5 findings from 1-10 with epistemic rationale.
2. Weakest Link: The finding with lowest confidence and the exact data needed to verify/falsify it.
3. Bias Check: Identify any perspective that was overrepresented.
4. Missing Perspective: What 6th domain angle would significantly shift the conclusion?
5. Overall Grade: Stanford peer-review grade (A-F) with constructive critique.

---

Grounding Resources Available:
{instrument_context}
Market Research Report: {market_research_report}
Sentiment Analysis: {sentiment_report}
Latest News & World Affairs: {news_report}
Fundamentals: {fundamentals_report}
""" + get_language_instruction()

        response = llm.invoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)

        return {"storm_report": content}

    return storm_node


def run_storm_research(
    llm: Any,
    topic: str,
    context: str = "",
    user_role: str = "Portfolio Manager",
) -> str:
    """Run standalone STORM multi-perspective research on an arbitrary topic.

    Args:
        llm: LangChain compatible chat model or invoker.
        topic: Topic, company, ticker, or strategic question to investigate.
        context: Optional background data, report snippets, or market context.
        user_role: Role of the decision maker (e.g. Portfolio Manager, CEO, Trader).

    Returns:
        The complete 4-phase STORM research briefing as a formatted string.
    """
    node = create_storm_researcher(llm)
    result = node({
        "company_of_interest": topic,
        "asset_type": "stock",
        "market_report": context,
        "sentiment_report": "",
        "news_report": "",
        "fundamentals_report": "",
        "user_role": user_role,
    })
    return result["storm_report"]
