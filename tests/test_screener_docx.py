"""Tests for Screener Word document generator (.docx)."""

import os
import tempfile

import pytest
from docx import Document

from tradingagents.report_docx import ScreenerDocxGenerator


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
            "Compounded Sales Growth": {"5 Years:": "32%", "3 Years:": "68%", "TTM:": "85%"},
            "Compounded Profit Growth": {"5 Years:": "45%", "3 Years:": "110%", "TTM:": "95%"},
        },
    }

    analysis = {
        "industry": "Aerospace & Defense",
        "core_product": "Combat Simulators & Anti-Drone Systems",
        "growth_5y_rev": "32%",
        "growth_5y_pat": "45%",
        "executive_summary_paragraphs": [
            "Zen Technologies is India's leading combat simulator and counter-drone defense system manufacturer.",
            "Strong revenue visibility is anchored by an unexecuted order book exceeding Rs. 1,400 Cr.",
        ],
        "bull_points": [
            ("Order Book Acceleration", "Unexecuted order backlog covers over 2.5x trailing twelve-month revenue."),
            ("Counter-Drone Leadership", "Pioneering indigenous anti-drone detection and soft/hard kill platforms."),
        ],
        "bear_points": [
            ("Lumpiness in Government Procurement", "Defense budgetary cycles can result in lumpy quarterly dispatch milestones."),
        ],
        "valuation_scenarios": [
            ("Bull Case", "1,200", "38.0%", "350", "50.0x", "17,500", "Rs. 2,050"),
            ("Base Case", "950", "35.0%", "260", "40.0x", "10,400", "Rs. 1,220"),
            ("Bear Case", "750", "30.0%", "180", "28.0x", "5,040", "Rs. 590"),
        ],
        "pe_walk_down": [
            ("Revenue (Rs. Cr)", "580", "800", "1,100", "1,450"),
            ("OPM %", "35.0%", "36.0%", "37.0%", "37.5%"),
            ("PAT (Rs. Cr)", "175", "230", "325", "430"),
            ("EPS (Rs)", "20.6", "27.0", "38.2", "50.5"),
            ("Implied P/E at CMP", "70.4x", "53.7x", "38.0x", "28.7x"),
        ],
        "promise_scorecard": [
            ("Concall", "Oct 2024", "Export Order", "Secure export orders > Rs. 100 Cr", "Q3 FY25", "Delivered Rs. 140 Cr export order", "DELIVERED"),
            ("Concall", "Jan 2025", "Facility Expansion", "Commission Hyderabad robotics lab", "Q4 FY25", "Civil work completed", "ON TRACK"),
        ],
        "credibility_summary": "Promises Delivered / On Track: 2 out of 2 = 100.0%.",
        "flags": [
            ("Rapid conversion of order book into operating cash flow.", "Working capital requirements during heavy export shipments."),
        ],
        "priced_in": [
            "Visible defense budget allocations and Atmanirbhar Bharat push.",
            "Current 35%+ ROCE quality reflected in trailing multiple.",
        ],
        "not_priced_in": [
            "Global export pipeline across Middle East and North Africa.",
            "Software recurring AMC revenues as installed base expands.",
        ],
        "negative_surprises": [
            "Delays in client acceptance testing.",
        ],
        "pricing_verdict": "Valuation is justified by explosive order book conversion and global export expansion.",
        "catalysts": [
            "Large international contract award.",
            "Mainboard migration.",
        ],
        "risks": [
            "Defense procurement pacing.",
        ],
        "macro_risk_assessment": "Insulated from global consumer slowdown due to sovereign defense spending priority.",
        "munger_inversion": [
            ("1. What if sovereign defense procurement is delayed?", "Billings pushed back.", "However: Multi-year contracts with milestone advance payments.", "Probability: 15%"),
            ("2. What if competitors replicate anti-drone algorithms?", "Price pressure.", "However: 155+ patents and military field validations build moat.", "Probability: 10%"),
        ],
        "target_bear": "Rs. 590",
        "target_base": "Rs. 1,220",
        "target_bull": "Rs. 2,050",
    }
    return company, analysis


@pytest.mark.unit
def test_generate_equity_research_report_docx(mock_company_and_analysis):
    company, analysis = mock_company_and_analysis
    with tempfile.TemporaryDirectory() as tmpdir:
        generator = ScreenerDocxGenerator(output_dir=tmpdir)
        path = generator.generate_equity_research_report(company, analysis)

        assert os.path.isfile(path)
        assert path.endswith("Equity_Research_Report.docx")

        # Verify it can be read by python-docx and has required sections
        doc = Document(path)
        text_all = "\n".join(p.text for p in doc.paragraphs)
        assert "EQUITY RESEARCH" in text_all
        assert "Zen Technologies Ltd" in text_all
        assert "1. Executive Summary" in text_all
        assert "13. Munger Inversion" in text_all
        assert len(doc.tables) >= 5


@pytest.mark.unit
def test_generate_updated_thesis_docx(mock_company_and_analysis):
    company, analysis = mock_company_and_analysis
    with tempfile.TemporaryDirectory() as tmpdir:
        generator = ScreenerDocxGenerator(output_dir=tmpdir)
        path = generator.generate_updated_thesis(company, analysis)

        assert os.path.isfile(path)
        assert path.endswith("Updated_Thesis.docx")

        doc = Document(path)
        text_all = "\n".join(p.text for p in doc.paragraphs)
        assert "Updated Investment Thesis" in text_all
        assert "Zen Technologies Ltd" in text_all
        assert "Forward P/E Walk-Down" in text_all
        assert len(doc.tables) >= 4
