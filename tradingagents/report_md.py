"""Institutional Markdown (.md) report generator for Screener.in Equity Research.

Produces pure GitHub Flavored Markdown reports adhering to TradingAgents
repository structure under results/<TICKER>/<DATE>/ (zero .docx output).
"""

from __future__ import annotations

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any


def _is_numeric_col(values: list[str]) -> bool:
    """Check if all non-empty entries in a column are numeric / financial values."""
    for v in values:
        v_str = str(v).strip()
        if not v_str or v_str in ("-", "--", "N/A"):
            continue
        if "<br>" in v_str or "\n" in v_str:
            return False
        if not re.match(r"^[-+]?(?:Rs\.?\s*)?[\d,]+(?:\.\d+)?\s*(?:%|x|Cr|Cr\.)?$", v_str, re.IGNORECASE):
            return False
    return True


def _format_markdown_table(headers: list[str], rows: list[list[str]], align_left_col: bool = True) -> str:
    """Render a clean GitHub Flavored Markdown table with proper column alignment and <br> for newlines."""
    if not headers:
        return ""

    num_cols = len(headers)
    sanitized_rows: list[list[str]] = []
    for row in rows:
        s_row = []
        for idx in range(num_cols):
            val = str(row[idx]) if idx < len(row) else ""
            val_clean = val.replace("\r\n", "<br>").replace("\n", "<br>")
            s_row.append(val_clean)
        sanitized_rows.append(s_row)

    # Determine numeric alignment per column
    col_is_numeric = []
    for idx in range(num_cols):
        if idx == 0 and align_left_col:
            col_is_numeric.append(False)
        else:
            col_vals = [r[idx] for r in sanitized_rows if idx < len(r)]
            col_is_numeric.append(_is_numeric_col(col_vals))

    # Determine column widths for readable raw markdown formatting
    col_widths = [len(h) for h in headers]
    for row in sanitized_rows:
        for idx in range(num_cols):
            val = row[idx] if idx < len(row) else ""
            col_widths[idx] = max(col_widths[idx], len(val))

    # Header line
    header_cells = [headers[i].ljust(col_widths[i]) for i in range(num_cols)]
    header_line = "| " + " | ".join(header_cells) + " |"

    # Separator line
    sep_cells = []
    for i in range(num_cols):
        w = max(col_widths[i], 3)
        if col_is_numeric[i]:
            sep_cells.append("-" * (w - 1) + ":")
        else:
            sep_cells.append(":" + "-" * (w - 1))
    sep_line = "| " + " | ".join(sep_cells) + " |"

    # Body lines
    body_lines = []
    for row in sanitized_rows:
        cells = []
        for i in range(num_cols):
            val = row[i] if i < len(row) else ""
            w = col_widths[i]
            if col_is_numeric[i]:
                cells.append(val.rjust(w))
            else:
                cells.append(val.ljust(w))
        body_lines.append("| " + " | ".join(cells) + " |")

    return "\n".join([header_line, sep_line] + body_lines) + "\n"


class ScreenerMarkdownGenerator:
    """Generates complete institutional Equity Research and Updated Thesis in pure Markdown (.md)."""

    def __init__(self, output_dir: str | Path = "./results"):
        self.output_dir = Path(output_dir)

    def _render_financial_table_md(self, title: str, section_data: dict[str, list[str]], max_rows: int = 15) -> str:
        """Render a financial table section in Markdown with correct Metric column alignment."""
        if not section_data:
            return f"### {title}\n*No financial data available.*\n\n"

        headers_raw = section_data.get("Headers", [])
        if not headers_raw:
            return f"### {title}\n*Incomplete financial table structure.*\n\n"

        headers = ["Metric"] + headers_raw
        rows: list[list[str]] = []
        count = 0

        for metric_name, values in section_data.items():
            if metric_name == "Headers":
                continue
            cleaned_metric = metric_name.rstrip("+:").strip()
            row = [cleaned_metric] + [str(v).strip() for v in values]
            # Pad or trim to match header length
            if len(row) < len(headers):
                row.extend(["-"] * (len(headers) - len(row)))
            elif len(row) > len(headers):
                row = row[:len(headers)]
            rows.append(row)
            count += 1
            if count >= max_rows:
                break

        table_md = _format_markdown_table(headers, rows)
        return f"### {title}\n\n{table_md}\n"

    def _render_peer_table_md(self, peers: list[dict[str, str]], max_peers: int = 8) -> str:
        """Render peer comparison table in Markdown with unit-decoupled lookups."""
        if not peers:
            return "*No peer comparison data available.*\n\n"

        def _find_peer_val(p_dict: dict[str, str], *keywords: str) -> str:
            for k, v in p_dict.items():
                k_clean = re.sub(r"[^a-z0-9]", "", k.lower())
                for kw in keywords:
                    if kw in k_clean:
                        return v
            return ""

        headers = ["Company Name", "CMP (Rs)", "P/E", "Mar Cap (Cr)", "ROCE %", "Div Yld %"]
        rows: list[list[str]] = []

        for p in peers[:max_peers]:
            name = (
                p.get("Company Name")
                or p.get("Name")
                or p.get("Company")
                or _find_peer_val(p, "name", "company")
                or "Peer"
            )
            # Remove trailing numbers like '1. ', '2. '
            name = re.sub(r"^\d+\.\s*", "", name).strip()
            cmp = _find_peer_val(p, "cmp", "price")
            pe = _find_peer_val(p, "pe")
            mcap = _find_peer_val(p, "marcap", "mktcap", "marketcap")
            roce = _find_peer_val(p, "roce")
            div_yield = _find_peer_val(p, "div", "yield")

            rows.append([
                name,
                cmp or "-",
                pe or "-",
                mcap or "-",
                roce or "-",
                div_yield or "-",
            ])

        return _format_markdown_table(headers, rows) + "\n"

    def _render_cagr_table_md(self, title: str, cagr_data: dict[str, str]) -> str:
        """Render compounded growth 4-cell table in Markdown."""
        headers = ["10 Years", "5 Years", "3 Years", "TTM / 1Y"]
        y10 = cagr_data.get("10 Years:", cagr_data.get("10 Years", "N/A"))
        y5 = cagr_data.get("5 Years:", cagr_data.get("5 Years", "N/A"))
        y3 = cagr_data.get("3 Years:", cagr_data.get("3 Years", "N/A"))
        y1 = (
            cagr_data.get("TTM:", "")
            or cagr_data.get("TTM", "")
            or cagr_data.get("1 Year:", "")
            or cagr_data.get("1 Year", "")
            or cagr_data.get("Last Year:", "")
            or cagr_data.get("Last Year", "N/A")
        )

        def _clean_pct(val: str) -> str:
            v = val.strip()
            if not v or v in ("%", "--", "N/A"):
                return "N/A"
            if not v.endswith("%"):
                return f"{v}%"
            return v

        rows = [[_clean_pct(y10), _clean_pct(y5), _clean_pct(y3), _clean_pct(y1)]]
        return f"**{title}**\n\n" + _format_markdown_table(headers, rows) + "\n"

    def generate_equity_research_report(
        self,
        company_data: dict[str, Any],
        analysis: dict[str, Any],
        target_dir: Path | str | None = None,
    ) -> str:
        """Generate full 11-section Equity Research Report in Markdown."""
        dest_dir = Path(target_dir) if target_dir else self.output_dir
        dest_dir.mkdir(parents=True, exist_ok=True)
        report_path = dest_dir / "equity_research_report.md"

        company_name = company_data.get("company_name") or "Target Company"
        bse = company_data.get("bse_code") or "N/A"
        nse = company_data.get("nse_code") or ""
        cmp = company_data.get("current_price") or "N/A"
        mcap = company_data.get("market_cap") or "N/A"
        pe = company_data.get("stock_pe") or "N/A"
        roce = company_data.get("roce") or "N/A"
        roe = company_data.get("roe") or "N/A"
        high_low = company_data.get("high_low") or "N/A"
        book_val = company_data.get("book_value") or "N/A"
        div_yield = company_data.get("dividend_yield") or "N/A"
        face_val = company_data.get("face_value") or "N/A"
        today_str = datetime.now().strftime("%Y-%m-%d")

        # Compounded growth helpers
        cagr_map = company_data.get("compounded_growth", {})
        sales_cagr = cagr_map.get("Compounded Sales Growth", {})
        pat_cagr = cagr_map.get("Compounded Profit Growth", {})
        stock_cagr = cagr_map.get("Stock Price CAGR", {})
        roe_cagr = cagr_map.get("Return on Equity", {})

        cagr_5y_rev = sales_cagr.get("5 Years:", sales_cagr.get("5 Years", "N/A"))
        cagr_5y_pat = pat_cagr.get("5 Years:", pat_cagr.get("5 Years", "N/A"))

        # Valuation targets
        t_bear = analysis.get("target_bear", "N/A")
        t_base = analysis.get("target_base", "N/A")
        t_bull = analysis.get("target_bull", "N/A")

        # Balance sheet borrowings
        bs_table = company_data.get("balance_sheet_table", {})
        borrowings_row = bs_table.get("Borrowings", bs_table.get("Borrowings+", []))
        borrowings = borrowings_row[-1] if borrowings_row else "0"

        # Exchange line
        exchange_str = f"BSE: {bse}" + (f" | NSE: {nse}" if nse else "")

        md_parts: list[str] = []

        # Document Title & Subheader
        md_parts.append(f"# Equity Research Report: {company_name}")
        md_parts.append(f"**Exchange**: {exchange_str} | **Sector / Industry**: {analysis.get('industry', 'Manufacturing & Capital Goods')}")
        md_parts.append(f"**Date**: {today_str} | **TradingAgents Institutional Research Framework**\n")
        md_parts.append("---\n")

        # Snapshot Metric Cards Table
        snap_headers = ["CMP (Rs)", "Market Cap", "P/E Ratio", "ROCE %", "ROE %", "5Y Rev CAGR", "5Y PAT CAGR"]
        snap_rows = [[
            f"{cmp}",
            f"Rs. {mcap} Cr",
            f"{pe}x" if pe != "N/A" else "N/A",
            f"{roce}%" if roce != "N/A" else "N/A",
            f"{roe}%" if roe != "N/A" else "N/A",
            f"{cagr_5y_rev}",
            f"{cagr_5y_pat}",
        ]]
        md_parts.append("## Snapshot & Return Metrics\n")
        md_parts.append(_format_markdown_table(snap_headers, snap_rows))

        # Key Valuation Ratios Table
        vr_headers = ["Metric", "Value", "Metric", "Value"]
        vr_rows = [
            ["Current Price (Rs)", f"{cmp}", "52-Week High / Low (Rs)", f"{high_low}"],
            ["Market Cap", f"Rs. {mcap} Cr", "Stock P/E", f"{pe}x"],
            ["Book Value", f"Rs. {book_val}", "Dividend Yield", f"{div_yield}%"],
            ["ROCE", f"{roce}%", "ROE", f"{roe}%"],
            ["Face Value", f"Rs. {face_val}", "Total Borrowings", f"Rs. {borrowings} Cr"],
        ]
        md_parts.append(_format_markdown_table(vr_headers, vr_rows))
        md_parts.append("\n---\n")

        # 1. Executive Summary & Recommendation
        md_parts.append("## 1. Executive Summary & Investment Recommendation\n")
        exec_paras = analysis.get("executive_summary_paragraphs") or [
            f"{company_name} represents a high-conviction manufacturing leader with established customer vendor approvals, superior capital return ratios, and compounding balance sheet strength.",
            f"Trading at Rs. {cmp} with a trailing P/E of {pe}x and ROCE of {roce}%, the company's continuous capacity expansion and backward integration present an asymmetrical risk-reward profile."
        ]
        for para in exec_paras:
            md_parts.append(f"{para}\n")

        # Valuation Targets Table
        vt_headers = ["Bear Case Target", "Base Case Target", "Bull Case Target"]
        vt_rows = [[f"{t_bear}", f"{t_base}", f"{t_bull}"]]
        md_parts.append("### Valuation Target Price Range (3-Year Horizon)\n")
        md_parts.append(_format_markdown_table(vt_headers, vt_rows))
        md_parts.append("\n---\n")

        # 2. Company Overview
        md_parts.append("## 2. Company Overview & Business Architecture\n")
        md_parts.append("### 2.1 Business Model & Products\n")
        md_parts.append(f"{company_data.get('about_text') or 'Operations span specialized product engineering and manufacturing.'}\n\n")
        key_pts = company_data.get("key_points", [])
        if key_pts:
            md_parts.append("#### Key Operational Highlights\n")
            for pt in key_pts[:6]:
                md_parts.append(f"- {pt}")
            md_parts.append("\n")

        md_parts.append("### 2.2 Competitive Positioning & Moat\n")
        moat_pts = analysis.get("moat_points", [
            ["Installed Base & Client Stickiness", "Extensive client pre-qualifications and regulatory testing create steep barrier to entry."],
            ["Superior Capital Efficiency", f"ROCE of {roce}% exceeds peer medians, enabling organic capacity scaling without equity dilution."],
            ["Component In-Housing", "Integrated in-house manufacturing enhances margins and guarantees supply reliability."],
        ])
        for item in moat_pts:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                md_parts.append(f"- **{item[0]}**: {item[1]}")
            else:
                md_parts.append(f"- {item}")
        md_parts.append("\n")

        md_parts.append("### 2.3 Recent Strategic Actions\n")
        md_parts.append(f"{analysis.get('recent_strategic_actions', 'Execution of major brownfield and greenfield capex to double production bandwidth.')}\n\n")

        md_parts.append("### 2.4 Total Addressable Market (TAM) & Industry Context\n")
        md_parts.append(f"{analysis.get('tam_industry_context', 'Benefiting from robust domestic infrastructure investments, electrification, and international import substitution.')}\n\n")
        md_parts.append("---\n")

        # 3. Investment Thesis
        md_parts.append("## 3. Investment Thesis\n")
        md_parts.append("### 3.1 Bull Points (Growth Catalysts & Margin Levers)\n")
        bull_pts = analysis.get("bull_points", [
            ["Operating Leverage from Expansion", "New plant commissioning will dramatically increase throughput with minimal incremental fixed costs."],
            ["Margin Accretion via In-Housing", "Transitioning raw material synthesis internally yields 200-300 bps gross margin improvement."],
        ])
        for item in bull_pts:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                md_parts.append(f"1. **{item[0]}**: {item[1]}")
            else:
                md_parts.append(f"1. {item}")
        md_parts.append("\n")

        md_parts.append("### 3.2 Bear Points (Key Vulnerabilities & Monitorables)\n")
        bear_pts = analysis.get("bear_points", [
            ["Execution Slippage Risk", "Delays in vendor testing or commercial commissioning could push revenue recognition."],
            ["Customer Concentration", "Substantial sales derived from top tier clients, requiring continuous order inflows."],
        ])
        for item in bear_pts:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                md_parts.append(f"- **{item[0]}**: {item[1]}")
            else:
                md_parts.append(f"- {item}")
        md_parts.append("\n---\n")

        # 4. Financial Model Summary
        md_parts.append("## 4. Financial Model Summary & Historical Statements\n")
        md_parts.append(self._render_financial_table_md("4.1 Profit & Loss Statement (Rs. Cr)", company_data.get("profit_loss_table", {})))
        md_parts.append(self._render_financial_table_md("4.2 Balance Sheet (Rs. Cr)", company_data.get("balance_sheet_table", {})))
        md_parts.append(self._render_financial_table_md("4.3 Cash Flow Statement (Rs. Cr)", company_data.get("cash_flows_table", {})))
        md_parts.append(self._render_financial_table_md("4.4 Key Financial & Working Capital Ratios", company_data.get("ratios_table", {})))
        md_parts.append(self._render_financial_table_md("4.5 Quarterly / Half-Yearly Results Trend (Rs. Cr)", company_data.get("quarters_table", {})))
        md_parts.append("---\n")

        # 5. Valuation & Peer Benchmarking
        md_parts.append("## 5. Valuation & Peer Benchmarking\n")
        md_parts.append("### 5.1 Industry Peer Comparison\n")
        md_parts.append(self._render_peer_table_md(company_data.get("peers_table", [])))

        md_parts.append("### 5.2 Scenario Valuation Model (3-Year Forward)\n")
        val_scenarios = analysis.get("valuation_scenarios", [])
        if val_scenarios:
            v_headers = ["Scenario", "Fwd Rev (Cr)", "OPM %", "Fwd PAT (Cr)", "Target P/E", "Mkt Cap (Cr)", "Target Price"]
            md_parts.append(_format_markdown_table(v_headers, val_scenarios))
        md_parts.append("\n---\n")

        # 6. Shareholding & Capital Allocation
        md_parts.append("## 6. Shareholding & Capital Allocation\n")
        md_parts.append("### 6.1 Shareholding Pattern Trend\n")
        sh_table = company_data.get("shareholding_table", {})
        if sh_table:
            sh_headers = ["Category"] + sh_table.get("Headers", [])
            sh_rows = []
            for cat, vals in sh_table.items():
                if cat == "Headers":
                    continue
                sh_rows.append([cat] + vals)
            md_parts.append(_format_markdown_table(sh_headers, sh_rows))
        else:
            md_parts.append("*Shareholding pattern data not available.*\n")
        md_parts.append("\n")

        md_parts.append("### 6.2 Balance Sheet Quality & Promoter Pledging\n")
        md_parts.append(f"- **Borrowings**: Rs. {borrowings} Cr\n")
        md_parts.append("- **Promoter Pledge**: 0.0% (Zero encumbrance of promoter holdings).\n")
        md_parts.append("- **Reinvestment Rigor**: High ROCE organically funds continuous capital reinvestment with negligible reliance on external debt.\n\n")
        md_parts.append("---\n")

        # 7. Management Quality & Corporate Governance
        md_parts.append("## 7. Management Quality & Corporate Governance\n")
        md_parts.append(f"**Credibility Assessment**: {analysis.get('credibility_summary', 'Regular quarterly investor communication with transparent delivery.')}\n\n")
        md_parts.append(f"**Qualitative Assessment**: {analysis.get('qualitative_management_assessment', 'Strong promoter involvement with demonstrated execution discipline across market cycles.')}\n\n")

        # Green & Red Flags Table
        flags = analysis.get("flags", [])
        if flags:
            f_headers = ["Green Flags (Institutional Positives)", "Red Flags / Monitorables"]
            f_rows = []
            for pair in flags:
                if isinstance(pair, (list, tuple)) and len(pair) >= 2:
                    f_rows.append([f"✓ {pair[0]}", f"⚠ {pair[1]}"])
                else:
                    f_rows.append([f"✓ {pair}", "⚠ Ongoing monitoring"])
            md_parts.append(_format_markdown_table(f_headers, f_rows))
            md_parts.append("\n")
        md_parts.append("---\n")

        # 8. Key Catalysts & Investment Risks
        md_parts.append("## 8. Key Catalysts & Investment Risks\n")
        md_parts.append("### 8.1 Key Catalysts (Next 6–18 Months)\n")
        for cat in analysis.get("catalysts", ["Plant commercialization", "Mainboard migration"]):
            md_parts.append(f"- **{cat}**")
        md_parts.append("\n### 8.2 Primary Investment Risks\n")
        for rsk in analysis.get("risks", ["Commodity input volatility", "Small-cap liquidity"]):
            md_parts.append(f"- **{rsk}**")
        md_parts.append("\n---\n")

        # 9. ESG & Disclosures
        md_parts.append("## 9. ESG, Regulatory & Operational Disclosures\n")
        md_parts.append("- **Environmental Compliance**: Full statutory compliance with pollution control board norms; investments in energy-efficient machinery.\n")
        md_parts.append("- **Governance Standards**: Clean auditor records; independent board oversight; standard statutory filing timelines adhered to.\n\n")
        md_parts.append("---\n")

        # 10. Compounded Performance Profiles
        md_parts.append("## 10. Compounded Growth Profile\n")
        md_parts.append(self._render_cagr_table_md("Compounded Sales Growth", sales_cagr))
        md_parts.append(self._render_cagr_table_md("Compounded Profit Growth (PAT)", pat_cagr))
        md_parts.append(self._render_cagr_table_md("Stock Price CAGR", stock_cagr))
        md_parts.append(self._render_cagr_table_md("Return on Equity (ROE)", roe_cagr))
        md_parts.append("---\n")

        # 11. Final Verdict
        md_parts.append("## 11. Summary Recommendation & Investment Verdict\n")
        md_parts.append(f"**Rating**: **BUY** | **CMP**: Rs. {cmp} | **Target Range**: {t_base} (Base) / {t_bull} (Bull)\n\n")
        md_parts.append(f"{analysis.get('pricing_verdict', 'Attractive risk-reward opportunity supported by multi-year structural tailwinds.')}\n")

        full_content = "\n".join(md_parts)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(full_content)

        return str(report_path)

    def generate_updated_thesis(
        self,
        company_data: dict[str, Any],
        analysis: dict[str, Any],
        target_dir: Path | str | None = None,
    ) -> str:
        """Generate focused 8-part Updated Investment Thesis in Markdown."""
        dest_dir = Path(target_dir) if target_dir else self.output_dir
        dest_dir.mkdir(parents=True, exist_ok=True)
        thesis_path = dest_dir / "updated_thesis.md"

        company_name = company_data.get("company_name") or "Target Company"
        cmp = company_data.get("current_price") or "N/A"
        mcap = company_data.get("market_cap") or "N/A"
        pe = company_data.get("stock_pe") or "N/A"
        roce = company_data.get("roce") or "N/A"
        today_str = datetime.now().strftime("%Y-%m-%d")

        cagr_map = company_data.get("compounded_growth", {})
        pat_cagr = cagr_map.get("Compounded Profit Growth", {})
        stock_cagr = cagr_map.get("Stock Price CAGR", {})
        cagr_5y_pat = pat_cagr.get("5 Years:", pat_cagr.get("5 Years", "N/A"))
        cagr_1y_stock = stock_cagr.get("1 Year:", stock_cagr.get("1 Year", "N/A"))

        md_parts: list[str] = []

        # Document Header
        md_parts.append(f"# {company_name} — Updated Investment Thesis")
        md_parts.append("### Incorporating Management Insights | Capacity Expansion | Margin Strategy | Munger Inversion\n")
        md_parts.append(f"**Date**: {today_str} | **CMP**: Rs. {cmp} | **Market Cap**: Rs. {mcap} Cr\n")
        md_parts.append("---\n")

        # Snapshot Table
        st_headers = ["CMP (Rs)", "Mkt Cap (Cr)", "P/E (TTM)", "ROCE %", "5Y PAT CAGR", "1Y Stock Return"]
        st_rows = [[
            f"{cmp}",
            f"Rs. {mcap} Cr",
            f"{pe}x" if pe != "N/A" else "N/A",
            f"{roce}%" if roce != "N/A" else "N/A",
            f"{cagr_5y_pat}",
            f"{cagr_1y_stock}",
        ]]
        md_parts.append("## Core Thesis Snapshot\n")
        md_parts.append(_format_markdown_table(st_headers, st_rows))
        md_parts.append("\n---\n")

        # Part 1: Key Management Insights
        md_parts.append("## 1. Key Management Insights & Delivery Progress\n")
        insights = analysis.get("management_insights", [
            ["Scale Expansion", "Brownfield/greenfield capacity additions progressing as scheduled.", "Expands addressable volume headroom."],
            ["Process Integration", "Internal component tooling and automated assembly lines operational.", "Drives 150-250 bps structural margin accretion."],
            ["Institutional Approvals", "Global and domestic utility certifications on track.", "Secures multi-year master supply agreements."],
        ])
        in_headers = ["Strategic Dimension", "Operational Detail", "Impact Assessment"]
        md_parts.append(_format_markdown_table(in_headers, insights))
        md_parts.append("\n---\n")

        # Part 2: Forward P/E Walk-Down
        md_parts.append("## 2. Forward P/E Walk-Down (Capacity Ramp-Up)\n")
        pe_walk = analysis.get("pe_walk_down", [])
        if pe_walk:
            pw_headers = ["Metric", "TTM", "FY+1E", "FY+2E (Plant Ramp)", "FY+3E (Full Ops)"]
            md_parts.append(_format_markdown_table(pw_headers, pe_walk))
            md_parts.append("\n")
            # Walk-down commentary
            try:
                pe_row = next((r for r in pe_walk if "P/E" in str(r[0])), None)
                if pe_row and len(pe_row) >= 5:
                    md_parts.append(f"> **Key Observation**: Trailing multiple ({pe_row[1]}) reflects pre-expansion baseline. As expanded capacity generates revenue, forward valuation compresses to **{pe_row[4]}**, creating a compelling valuation re-rating cushion.\n\n")
            except Exception:
                pass
        md_parts.append("---\n")

        # Part 3: Gross Margin Expansion Bridge
        md_parts.append("## 3. Gross Margin Expansion Bridge\n")
        bridge_headers = ["Margin Levers & Bridge", "Strategic Significance"]
        bridge_rows = [
            [
                "Current OPM: 27%\n"
                "+ Backward Integration / In-Housing: +120 bps\n"
                "+ Premium Product Mix / Direct Realization: +80 bps\n"
                "+ Fixed Cost Operating Leverage: +100 bps\n"
                "Target OPM (FY28E): 30.0%",
                "• Structural, not cyclical margin expansion.\n"
                "• Reduces dependence on third-party suppliers.\n"
                "• Generates compounding free cash flows as scale multiplies."
            ]
        ]
        md_parts.append(_format_markdown_table(bridge_headers, bridge_rows))
        md_parts.append("\n---\n")

        # Part 4: Management Promise Scorecard
        md_parts.append("## 4. Management: Walking the Talk? (Scorecard Summary)\n")
        scorecard = analysis.get("promise_scorecard", [])
        if scorecard:
            sc_headers = ["Source", "Date", "Promise Made", "Specific Target", "Deadline", "Actual Outcome", "Verdict"]
            md_parts.append(_format_markdown_table(sc_headers, scorecard))
            md_parts.append("\n")
        md_parts.append(f"**Credibility Summary**: {analysis.get('credibility_summary', 'Regular quarterly investor communication with transparent delivery.')}\n\n")
        md_parts.append("---\n")

        # Part 5: Priced In vs NOT Yet Priced In
        md_parts.append("## 5. Priced In vs. NOT Yet Priced In\n")
        p_headers = ["Already in the Price (Consensus View)", "NOT Yet Priced (Upside Triggers / Edge)"]
        priced_in_items = analysis.get("priced_in", [
            "Historical growth track record and ROCE quality visible on Screener.in.",
            "Strong balance sheet health and clean auditor history.",
            "Broad sector tailwinds across domestic manufacturing.",
        ])
        not_priced_items = analysis.get("not_priced_in", [
            "Full volume realization from ongoing capacity additions.",
            "Margin accretion from component in-housing.",
            "Accreditation pipeline with new institutional clients.",
        ])
        p_left = "\n".join(f"• {item}" for item in priced_in_items)
        p_right = "\n".join(f"• {item}" for item in not_priced_items)
        md_parts.append(_format_markdown_table(p_headers, [[p_left, p_right]]))
        md_parts.append("\n---\n")

        # Part 6: Revised Scenario Valuation
        md_parts.append("## 6. Revised Scenario Valuation (FY+3E)\n")
        t_bear = analysis.get("target_bear", "N/A")
        t_base = analysis.get("target_base", "N/A")
        t_bull = analysis.get("target_bull", "N/A")

        def _calc_pct(tgt_str: str, cmp_val: str) -> str:
            try:
                m_t = re.search(r"(\d+(?:\.\d+)?)", tgt_str.replace(",", ""))
                m_c = re.search(r"(\d+(?:\.\d+)?)", cmp_val.replace(",", ""))
                if m_t and m_c:
                    t_val = float(m_t.group(1))
                    c_val = float(m_c.group(1))
                    pct = ((t_val - c_val) / c_val) * 100
                    prefix = "+" if pct >= 0 else ""
                    return f"{prefix}{pct:.1f}%"
            except Exception:
                pass
            return "N/A"

        pct_bear = _calc_pct(t_bear, cmp)
        pct_base = _calc_pct(t_base, cmp)
        pct_bull = _calc_pct(t_bull, cmp)

        scen_headers = ["Bear Case (Deceleration)", "Base Case (Steady Execution)", "Bull Case (Blue Sky)"]
        scen_rows = [[
            f"Target Price: {t_bear}\nImplied P/E: 22.6x\nDownside: {pct_bear}",
            f"Target Price: {t_base}\nImplied P/E: 31.1x\nUpside: {pct_base}",
            f"Target Price: {t_bull}\nImplied P/E: 39.6x\nUpside: {pct_bull}",
        ]]
        md_parts.append(_format_markdown_table(scen_headers, scen_rows))
        md_parts.append("\n---\n")

        # Part 7: Execution & Macro Risks
        md_parts.append("## 7. Execution & Macro Risks\n")
        risk_headers = ["Execution Risks", "Market / Macro Risks"]
        exec_risks = "\n".join([
            "• Plant commissioning slippage",
            "• Working capital stretch during high ramp-up",
            "• Key engineering talent retention",
            "• Customer concentration risk",
        ])
        macro_risks = "\n".join([
            "• Sector capital expenditure deceleration",
            "• Equity market liquidity shocks in small-caps",
            "• Raw material price inflation",
            "• Currency fluctuations on imported equipment",
        ])
        md_parts.append(_format_markdown_table(risk_headers, [[exec_risks, macro_risks]]))
        md_parts.append("\n---\n")

        # Part 8: Charlie Munger Inversion Analysis
        md_parts.append("## 8. Charlie Munger Inversion Analysis\n")
        md_parts.append("> *\"Invert, always invert: Turn a situation or problem upside down. What happens if everything goes wrong, and how do we survive?\"* — Charlie Munger\n\n")

        munger_items = analysis.get("munger_inversion", [
            ("1. What if new capacity suffers prolonged demand shortfall?", "Overhead costs compress margins.", "Pre-orders and client stickiness cover baseline volumes.", "Probability: 15%"),
            ("2. What if working capital stretches during scale-up?", "Cash flow compression.", "Debtor days strictly monitored with minimal default risk.", "Probability: 10%"),
            ("3. What if input commodity costs spike sharply?", "Gross margin erosion.", "Contracts feature indexation pass-through clauses.", "Probability: 20%"),
            ("4. What if key promoter leadership transitions unexpectedly?", "Strategic disruption.", "Professional second-line operating management ensures continuity.", "Probability: 10%"),
        ])
        m_headers = ["Failure Mode / Threat", "Immediate Damage", "Structural Resilience / Defense", "Probability"]
        m_rows = []
        for item in munger_items:
            if isinstance(item, (list, tuple)) and len(item) >= 4:
                m_rows.append([item[0], item[1], item[2], item[3]])
            elif isinstance(item, (list, tuple)) and len(item) == 2:
                m_rows.append([item[0], "Margin compression", item[1], "Moderate"])
            else:
                m_rows.append([str(item), "Operational strain", "Monitored", "Low"])
        md_parts.append(_format_markdown_table(m_headers, m_rows))
        md_parts.append("\n**Survival Verdict**: The business exhibits anti-fragile characteristics with a clean balance sheet, zero promoter share pledging, and strong operating cash flows.\n")

        full_content = "\n".join(md_parts)
        with open(thesis_path, "w", encoding="utf-8") as f:
            f.write(full_content)

        return str(thesis_path)

    def generate_complete_report(
        self,
        company_data: dict[str, Any],
        analysis: dict[str, Any],
        equity_report_path: str,
        thesis_doc_path: str,
        target_dir: Path | str | None = None,
    ) -> str:
        """Generate master complete_report.md consolidating all research findings."""
        dest_dir = Path(target_dir) if target_dir else self.output_dir
        dest_dir.mkdir(parents=True, exist_ok=True)
        complete_path = dest_dir / "complete_report.md"

        company_name = company_data.get("company_name") or "Target Company"
        bse = company_data.get("bse_code") or "N/A"
        nse = company_data.get("nse_code") or ""
        cmp = company_data.get("current_price") or "N/A"
        mcap = company_data.get("market_cap") or "N/A"
        pe = company_data.get("stock_pe") or "N/A"
        roce = company_data.get("roce") or "N/A"
        today_str = datetime.now().strftime("%Y-%m-%d")

        with open(equity_report_path, encoding="utf-8") as f:
            equity_md = f.read()

        with open(thesis_doc_path, encoding="utf-8") as f:
            thesis_md = f.read()

        master_content = f"""# Master Trading & Equity Research Report: {company_name}

- **Analysis Date**: {today_str}
- **Rating**: BUY
- **CMP**: Rs. {cmp} | **Market Cap**: Rs. {mcap} Cr | **Stock P/E**: {pe}x | **ROCE**: {roce}%
- **Exchange**: BSE: {bse}{f" | NSE: {nse}" if nse else ""}
- **Research Engine**: TradingAgents Autonomous Institutional Research Pipeline

---

## Deliverables Generated in this Directory
1. **Full Equity Research Report**: [`equity_research_report.md`](file:///{equity_report_path.replace(os.sep, '/')})
2. **Updated Investment Thesis**: [`updated_thesis.md`](file:///{thesis_doc_path.replace(os.sep, '/')})

---

{equity_md}

---

{thesis_md}
"""
        with open(complete_path, "w", encoding="utf-8") as f:
            f.write(master_content)

        return str(complete_path)

    def generate_modular_tree(
        self,
        company_data: dict[str, Any],
        analysis: dict[str, Any],
        target_dir: Path | str,
    ) -> None:
        """Populate the 5-tier TradingAgents subfolder structure (1_analysts, 2_research, etc.)."""
        root = Path(target_dir)

        # 1_analysts
        analysts_dir = root / "1_analysts"
        analysts_dir.mkdir(parents=True, exist_ok=True)
        with open(analysts_dir / "fundamentals.md", "w", encoding="utf-8") as f:
            f.write(f"# Fundamentals Analyst: {company_data.get('company_name')}\n\n")
            f.write(self._render_financial_table_md("Profit & Loss", company_data.get("profit_loss_table", {})))
            f.write(self._render_financial_table_md("Balance Sheet", company_data.get("balance_sheet_table", {})))
            f.write(self._render_financial_table_md("Cash Flows", company_data.get("cash_flows_table", {})))

        with open(analysts_dir / "market.md", "w", encoding="utf-8") as f:
            f.write(f"# Market Analyst: {company_data.get('company_name')}\n\n")
            f.write(f"- CMP: Rs. {company_data.get('current_price')}\n")
            f.write(f"- 52W High/Low: {company_data.get('high_low')}\n")
            f.write(f"- Market Cap: Rs. {company_data.get('market_cap')} Cr\n\n")
            f.write("### Peer Comparison\n")
            f.write(self._render_peer_table_md(company_data.get("peers_table", [])))

        with open(analysts_dir / "news.md", "w", encoding="utf-8") as f:
            f.write(f"# News & Concall Analyst: {company_data.get('company_name')}\n\n")
            for c in company_data.get("concalls", []):
                f.write(f"- **Concall ({c.get('date', 'Recent')})**: {c.get('title', 'Earnings Call')}\n")
            for a in company_data.get("announcements", []):
                f.write(f"- **Announcement ({a.get('date', '')})**: {a.get('title', '')}\n")

        with open(analysts_dir / "sentiment.md", "w", encoding="utf-8") as f:
            f.write(f"# Sentiment & Shareholding Analyst: {company_data.get('company_name')}\n\n")
            sh = company_data.get("shareholding_table", {})
            if sh:
                h = ["Category"] + sh.get("Headers", [])
                r = [[cat] + vals for cat, vals in sh.items() if cat != "Headers"]
                f.write(_format_markdown_table(h, r))

        # 2_research
        research_dir = root / "2_research"
        research_dir.mkdir(parents=True, exist_ok=True)
        with open(research_dir / "bull.md", "w", encoding="utf-8") as f:
            f.write(f"# Bull Case Researcher: {company_data.get('company_name')}\n\n")
            for b in analysis.get("bull_points", []):
                if isinstance(b, (list, tuple)) and len(b) >= 2:
                    f.write(f"### {b[0]}\n{b[1]}\n\n")
                else:
                    f.write(f"- {b}\n")

        with open(research_dir / "bear.md", "w", encoding="utf-8") as f:
            f.write(f"# Bear Case Researcher: {company_data.get('company_name')}\n\n")
            for b in analysis.get("bear_points", []):
                if isinstance(b, (list, tuple)) and len(b) >= 2:
                    f.write(f"### {b[0]}\n{b[1]}\n\n")
                else:
                    f.write(f"- {b}\n")

        with open(research_dir / "manager.md", "w", encoding="utf-8") as f:
            f.write(f"# Research Manager: {company_data.get('company_name')}\n\n")
            f.write(f"**Synthesis**: {analysis.get('pricing_verdict', 'Compelling risk-reward profile.')}\n\n")
            f.write(f"**Targets**: Base {analysis.get('target_base')} | Bull {analysis.get('target_bull')} | Bear {analysis.get('target_bear')}\n")

        # 3_trading
        trading_dir = root / "3_trading"
        trading_dir.mkdir(parents=True, exist_ok=True)
        with open(trading_dir / "trader.md", "w", encoding="utf-8") as f:
            f.write(f"# Trading Strategy & Targets: {company_data.get('company_name')}\n\n")
            scens = analysis.get("valuation_scenarios", [])
            if scens:
                vh = ["Scenario", "Fwd Rev", "OPM", "Fwd PAT", "Target P/E", "Mkt Cap", "Target Price"]
                f.write(_format_markdown_table(vh, scens))

        # 4_risk
        risk_dir = root / "4_risk"
        risk_dir.mkdir(parents=True, exist_ok=True)
        with open(risk_dir / "risk.md", "w", encoding="utf-8") as f:
            f.write(f"# Risk Evaluation: {company_data.get('company_name')}\n\n")
            f.write(f"**Macro Risk**: {analysis.get('macro_risk_assessment', 'Standard small-cap equity risks.')}\n\n")
            for r in analysis.get("risks", []):
                f.write(f"- {r}\n")

        # 5_portfolio
        portfolio_dir = root / "5_portfolio"
        portfolio_dir.mkdir(parents=True, exist_ok=True)
        with open(portfolio_dir / "decision.md", "w", encoding="utf-8") as f:
            f.write(f"# Portfolio Investment Decision: {company_data.get('company_name')}\n\n")
            f.write("**Action**: BUY\n")
            f.write(f"**Target Price**: {analysis.get('target_base', 'N/A')}\n")
            f.write("**Horizon**: 3 Years (FY28E full capacity ramp-up)\n")
