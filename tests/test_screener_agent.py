"""Tests for Screener Equity Researcher Agent and analysis paths."""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from tradingagents.agents import create_screener_equity_researcher
from tradingagents.dataflows.vendors.screener.client import ScreenerCompanyData


@pytest.fixture
def mock_screener_data():
    return ScreenerCompanyData(
        company_name="Premier Energies Ltd",
        bse_code="544238",
        nse_code="PREMIERENE",
        url="https://www.screener.in/company/544238/",
        current_price="1,120",
        market_cap="50,400",
        high_low="1,260 / 840",
        stock_pe="48.5",
        book_value="95",
        dividend_yield="0.0",
        roce="26.4",
        roe="31.2",
        about_text="Premier Energies is India's second largest solar cell and module manufacturer.",
        key_points=["Backward integrated solar cells manufacturer with 3 GW module capacity."],
        pros=["Company is expected to give good quarter"],
        cons=["Stock is trading at 11.8 times its book value"],
        peers_table=[
            {"Name": "Waaree Energies", "CMP": "3,100", "P/E": "52.0", "Mar Cap": "88,000", "ROCE %": "32.0", "Div Yld %": "0.0"},
        ],
        profit_loss_table={
            "Headers": ["Mar 2023", "Mar 2024", "TTM"],
            "Sales": ["1,428", "3,143", "4,200"],
            "Operating Profit": ["154", "512", "880"],
            "Net Profit": ["37", "231", "480"],
        },
        concalls=[
            {
                "date": "Oct 2024",
                "title": "Q2 FY25 Concall Transcript",
                "transcript_url": "https://www.screener.in/concall/transcript/sample/",
                "transcript_text": "Management expects 4 GW cell line commissioning by Q4 FY25 with export orders from USA.",
            }
        ],
    )


@pytest.mark.unit
def test_screener_researcher_deterministic_execution(mock_screener_data):
    with (
        tempfile.TemporaryDirectory() as tmpdir,
        patch("tradingagents.dataflows.vendors.screener.client.ScreenerBrowserClient.fetch_company_data") as mock_fetch,
    ):
        mock_fetch.return_value = mock_screener_data

        researcher = create_screener_equity_researcher(llm=None, output_dir=tmpdir)
        result = researcher("544238")

        assert result.company_data.company_name == "Premier Energies Ltd"
        assert os.path.isfile(result.equity_report_path)
        assert result.equity_report_path.endswith(".md")
        assert os.path.isfile(result.thesis_doc_path)
        assert result.thesis_doc_path.endswith(".md")
        assert os.path.isfile(result.complete_report_path)
        assert result.complete_report_path.endswith(".md")
        assert "Premier Energies Ltd" in result.markdown_report
        assert "Deliverables" in result.markdown_report
        assert "Target Price Range" in result.markdown_report


@pytest.mark.unit
def test_screener_researcher_with_llm(mock_screener_data):
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(content="""{
        "industry": "Renewable Energy & Solar",
        "core_product": "Solar Cells & Modules",
        "executive_summary_paragraphs": ["Premier Energies is expanding rapidly."],
        "moat_points": [["Scale", "3 GW module capacity"]],
        "recent_strategic_actions": "Commissioning TOPCon cell facility.",
        "tam_industry_context": "National solar addition target of 500 GW by 2030.",
        "bull_points": [["Cell In-Housing", "Reduces import reliance and boosts margins."]],
        "bear_points": [["Global Price Volatility", "Chinese solar dumping risk."]],
        "pl_observation": "Revenue more than doubled in FY24.",
        "bs_observation": "Equity base strengthened post-IPO.",
        "cf_observation": "Strong operating cash generation.",
        "ratios_observation": "Working capital improved significantly.",
        "quarters_observation": "Consecutive record quarters.",
        "peer_observation": "Trades at discount to Waaree.",
        "valuation_scenarios": [
            ["Bull Case", "6,500", "22.0%", "950", "45.0x", "42,750", "Rs. 1,650"],
            ["Base Case", "5,200", "20.0%", "720", "35.0x", "25,200", "Rs. 1,180"],
            ["Bear Case", "4,000", "16.0%", "450", "25.0x", "11,250", "Rs. 720"]
        ],
        "management_insights": [["TOPCon Line", "Commissioning underway", "+200 bps margin"]],
        "pe_walk_down": [["Revenue", "4,200", "5,500", "7,200", "9,000"]],
        "promise_scorecard": [["Concall", "Oct 2024", "4 GW cell line", "Commercial ops", "Q4 FY25", "Machinery on site", "ON TRACK"]],
        "credibility_summary": "100% on track.",
        "qualitative_management_assessment": "High execution rigor.",
        "flags": [["Rapid scale", "Raw wafer import exposure"]],
        "market_implied_expectations": "Implies 35% growth.",
        "priced_in": ["IPO liquidity"],
        "not_priced_in": ["US export margin premium"],
        "negative_surprises": ["US tariff changes"],
        "pricing_verdict": "Attractive risk-reward.",
        "catalysts": ["TOPCon commissioning"],
        "risks": ["Wafer supply chain"],
        "macro_risk_assessment": "Protected by domestic ALMM mandate.",
        "munger_inversion": [["1. What if Chinese wafer prices crash?", "Short term inventory loss", "However: Cell margins expand", "Probability: 20%"]],
        "target_bear": "Rs. 720",
        "target_base": "Rs. 1,180",
        "target_bull": "Rs. 1,650"
    }""")

    with (
        tempfile.TemporaryDirectory() as tmpdir,
        patch("tradingagents.dataflows.vendors.screener.client.ScreenerBrowserClient.fetch_company_data") as mock_fetch,
    ):
        mock_fetch.return_value = mock_screener_data

        researcher = create_screener_equity_researcher(llm=mock_llm, output_dir=tmpdir)
        result = researcher("PREMIERENE")

        assert os.path.isfile(result.equity_report_path)
        assert result.equity_report_path.endswith(".md")
        assert os.path.isfile(result.thesis_doc_path)
        assert result.thesis_doc_path.endswith(".md")
        assert os.path.isfile(result.complete_report_path)
        assert result.complete_report_path.endswith(".md")
        assert result.analysis["industry"] == "Renewable Energy & Solar"
        mock_llm.invoke.assert_called_once()
