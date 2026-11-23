"""Tests for STORM (Stanford OVAL NAACL 2024) multi-perspective research agent."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from tradingagents.agents import create_storm_researcher, run_storm_research
from tradingagents.agents.researchers.storm_researcher import (
    create_storm_researcher as direct_create_storm,
)


@pytest.mark.unit
def test_storm_researcher_exports():
    """Verify STORM researcher is properly exported at package levels."""
    assert callable(create_storm_researcher)
    assert callable(run_storm_research)
    assert create_storm_researcher is direct_create_storm


@pytest.mark.unit
def test_storm_node_prompt_structure_and_phases():
    """Verify prompt incorporates all 4 STORM phases and the 5 simulated perspectives."""
    captured: dict[str, str] = {}
    mock_llm = MagicMock()
    mock_llm.invoke.side_effect = lambda prompt: (
        captured.__setitem__("prompt", prompt)
        or MagicMock(content="## STORM Multi-Perspective Report\nPhase 1-4 completed.")
    )

    node = create_storm_researcher(mock_llm)
    state = {
        "company_of_interest": "NVDA",
        "asset_type": "stock",
        "market_report": "Bullish momentum in AI datacenters.",
        "sentiment_report": "High retail excitement.",
        "news_report": "New GPU architecture announced.",
        "fundamentals_report": "Gross margins above 70%.",
        "user_role": "Chief Investment Officer",
    }

    result = node(state)

    assert "storm_report" in result
    assert result["storm_report"] == "## STORM Multi-Perspective Report\nPhase 1-4 completed."

    prompt = captured["prompt"]
    # Check 5 expert perspectives
    assert "PRACTITIONER" in prompt
    assert "ACADEMIC" in prompt
    assert "SKEPTIC" in prompt
    assert "ECONOMIST" in prompt
    assert "HISTORIAN" in prompt

    # Check 4 phases
    assert "Phase 1 — Multi-Perspective Scan" in prompt
    assert "Phase 2 — Contradiction Map" in prompt
    assert "Phase 3 — Synthesis Briefing" in prompt
    assert "Phase 4 — Peer Review & Self-Critique" in prompt

    # Check context grounding
    assert "NVDA" in prompt
    assert "Chief Investment Officer" in prompt
    assert "Gross margins above 70%." in prompt


@pytest.mark.unit
def test_run_storm_research_standalone():
    """Verify standalone helper executes research for generic topic."""
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(content="Executive briefing on quantum computing.")

    output = run_storm_research(
        llm=mock_llm,
        topic="Enterprise adoption of Quantum Key Distribution",
        context="Commercial QKD networks being deployed across tier-1 financial centers.",
        user_role="Head of Risk",
    )

    assert output == "Executive briefing on quantum computing."
    mock_llm.invoke.assert_called_once()
