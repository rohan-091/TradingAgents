"""Tests for Screener Markdown document generator (.md)."""

import os
import tempfile
from pathlib import Path

import pytest

from tradingagents.report_md import ScreenerMarkdownGenerator, _format_markdown_table


@pytest.fixture
def mock_company_and_analysis():
    company = {
        "company_name": "Zen Technologies Ltd",
        "bse_code": "533339",
        "nse_code": "ZENTEC",
        "current_price": "1,450",
        "market_cap": "12,250",
        "high_low": "1,600 / 720",
        "stock_pe": "55.0",
        "book_value": "115",
        "dividend_yield": "0.15",
        "roce": "35.5",
        "roe": "28.0",
        "face_value": "1.0",
        "about_text": "Zen Technologies designs and manufactures combat training simulators and counter-drone systems.",
        "key_points": ["Leader in anti-drone systems with extensive defense patents."],
        "peers_table": [
            {"Name": "Bharat Electronics", "CMP": "305", "P/E": "45.0", "Mar Cap": "2,20,000", "ROCE %": "32.0", "Div Yld %": "0.70"},
            {"Name": "Data Patterns", "CMP": "2,850", "P/E": "65.0", "Mar Cap": "16,000", "ROCE %": "24.0", "Div Yld %": "0.25"},
        ],
        "profit_loss_table": {
            "Headers": ["Mar 2023", "Mar 2024", "TTM"],
            "Sales": ["161", "430", "580"],
            "Operating Profit": ["50", "150", "220"],
            "Net Profit": ["38", "120", "175"],
        },
        "balance_sheet_table": {
            "Headers": ["Mar 2023", "Mar 2024"],
            "Equity Capital": ["8", "8"],
            "Reserves": ["310", "430"],
            "Borrowings": ["10", "5"],
        },
        "cash_flows_table": {
            "Headers": ["Mar 2023", "Mar 2024"],
            "Cash from Operating": ["42", "110"],
        },
        "ratios_table": {
            "Headers": ["Mar 2023", "Mar 2024"],
            "ROCE %": ["25%", "35%"],
        },
        "quarters_table": {
            "Headers": ["Jun 2024", "Sep 2024", "Dec 2024"],
            "Sales": ["120", "150", "180"],
        },
        "shareholding_table": {
            "Headers": ["Dec 2023", "Dec 2024"],
            "Promoters": ["57.4%", "55.2%"],
        },
        "compounded_growth": {
            "Compounded Sales Growth": {"5 Years:": "32%", "TTM:": "45%"},
            "Compounded Profit Growth": {"5 Years:": "48%", "TTM:": "62%"},
            "Stock Price CAGR": {"1 Year:": "140%"},
            "Return on Equity": {"5 Years:": "28%"},
        },
    }

    analysis = {
        "industry": "Aerospace & Defense",
        "core_product": "Combat Simulators & Anti-Drone Systems",
        "executive_summary_paragraphs": [
            "Zen Technologies demonstrates strong operating leverage driven by expanding domestic defense budgets."
        ],
        "moat_points": [
            ["Proprietary IP", "Holds over 150 patents in training simulator architectures."],
            ["High Switching Costs", "Armed forces training protocols built around Zen platforms."],
        ],
        "recent_strategic_actions": "Setting up new subsidiary for Middle East exports.",
        "tam_industry_context": "Domestic anti-drone market expected to grow at 30% CAGR through 2030.",
        "bull_points": [
            ["Export Headroom", "Tripling order pipeline across friendly nations."],
            ["High-Margin AMC", "Simulators transition to recurring software support contracts."],
        ],
        "bear_points": [
            ["Lumpy Defense Procurement", "Quarterly revenues subject to Ministry of Defense milestone clearances."],
        ],
        "valuation_scenarios": [
            ["Bull Case", "1,200", "42.0%", "380", "50.0x", "19,000", "Rs. 2,250"],
            ["Base Case", "950", "38.0%", "280", "40.0x", "11,200", "Rs. 1,600"],
            ["Bear Case", "700", "30.0%", "160", "28.0x", "4,480", "Rs. 950"],
        ],
        "management_insights": [
            ["Order Book Scaling", "Active bids exceed Rs. 2,000 Cr across simulator tenders.", "Provides 3-year revenue visibility."],
        ],
        "pe_walk_down": [
            ["Metric", "TTM", "FY+1E", "FY+2E", "FY+3E"],
            ["P/E Multiple", "55.0x", "38.2x", "26.5x", "19.8x"],
        ],
        "promise_scorecard": [
            ["Concall", "Nov 2024", "Export subsidiary setup", "UAE entity registered", "Q4 FY25", "Incorporated", "DELIVERED"],
        ],
        "credibility_summary": "Management has consistently delivered on order book and margin guidance.",
        "qualitative_management_assessment": "First-generation technocrat promoter with deep domain engineering expertise.",
        "flags": [
            ["Zero Debt", "Working capital cycle elongation during scale-up"],
        ],
        "priced_in": ["Defense sector rerating"],
        "not_priced_in": ["Anti-drone export monetization"],
        "pricing_verdict": "Compelling opportunity for long-term compounding in defense electronics.",
        "catalysts": ["Export contract wins", "Army simulator trials"],
        "risks": ["MoD budget reallocation"],
        "macro_risk_assessment": "Supported by positive indigenization lists banning defense simulator imports.",
        "munger_inversion": [
            ("1. What if defense capex freezes?", "Revenue drop", "Order backlog provides 2-year floor", "10%"),
        ],
        "target_bear": "Rs. 950",
        "target_base": "Rs. 1,600",
        "target_bull": "Rs. 2,250",
    }

    return company, analysis


@pytest.mark.unit
def test_markdown_table_formatting():
    headers = ["Metric", "2023", "2024", "TTM"]
    rows = [["Sales", "100", "150", "200"], ["Net Profit", "10", "20", "35"]]
    md = _format_markdown_table(headers, rows)

    assert "| Metric" in md
    assert ":---" in md
    assert "---:" in md
    assert "| Sales" in md
    assert "200 |" in md


@pytest.mark.unit
def test_screener_markdown_generator(mock_company_and_analysis):
    company, analysis = mock_company_and_analysis

    with tempfile.TemporaryDirectory() as tmpdir:
        generator = ScreenerMarkdownGenerator(output_dir=tmpdir)

        equity_path = generator.generate_equity_research_report(company, analysis)
        assert os.path.isfile(equity_path)
        assert equity_path.endswith(".md")

        with open(equity_path, encoding="utf-8") as f:
            content = f.read()

        assert "# Equity Research Report: Zen Technologies Ltd" in content
        assert "CMP (Rs)" in content
        assert "Rs. 12,250 Cr" in content
        assert "Bharat Electronics" in content
        assert "4.1 Profit & Loss Statement" in content
        assert "| Metric" in content

        thesis_path = generator.generate_updated_thesis(company, analysis)
        assert os.path.isfile(thesis_path)
        assert thesis_path.endswith(".md")

        with open(thesis_path, encoding="utf-8") as f:
            t_content = f.read()

        assert "# Zen Technologies Ltd" in t_content
        assert "Updated Investment Thesis" in t_content
        assert "Charlie Munger Inversion Analysis" in t_content
        assert "Bear Case (Deceleration)" in t_content
        assert "Target Price: Rs. 1,600" in t_content

        complete_path = generator.generate_complete_report(
            company, analysis, equity_path, thesis_path
        )
        assert os.path.isfile(complete_path)
        assert complete_path.endswith(".md")

        generator.generate_modular_tree(company, analysis, Path(tmpdir))
        assert os.path.isfile(Path(tmpdir) / "1_analysts" / "fundamentals.md")
        assert os.path.isfile(Path(tmpdir) / "2_research" / "bull.md")
        assert os.path.isfile(Path(tmpdir) / "3_trading" / "trader.md")
        assert os.path.isfile(Path(tmpdir) / "4_risk" / "risk.md")
        assert os.path.isfile(Path(tmpdir) / "5_portfolio" / "decision.md")
