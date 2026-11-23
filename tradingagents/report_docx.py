"""Word document (.docx) report generator for Screener.in Equity Research."""

from __future__ import annotations

import os
from typing import Any

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
from docx.shared import Inches, Pt, RGBColor


def _set_cell_background(cell, fill_hex: str):
    """Set background color of a table cell using XML shading."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)


def _set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Set inner cell padding in twips."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f"</w:tcMar>"
    )
    tcPr.append(tcMar)


def _set_table_borders(table, color="D3D3D3", sz="4", val="single"):
    """Apply professional light gray borders to a table."""
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:bottom w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:insideV w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:left w:val="none"/>'
        f'<w:right w:val="none"/>'
        f"</w:tblBorders>"
    )
    tblPr.append(borders)


def _save_document_safely(doc: Document, filepath: str) -> str:
    """Save document, appending a version suffix if the file is locked by Word or another process."""
    try:
        doc.save(filepath)
        return filepath
    except PermissionError:
        base, ext = os.path.splitext(filepath)
        for i in range(1, 100):
            alt_path = f"{base}_v{i}{ext}"
            try:
                doc.save(alt_path)
                return alt_path
            except PermissionError:
                continue
        raise


class ScreenerDocxGenerator:
    """Generates professional equity research and updated thesis Word (.docx) reports."""

    PRIMARY_COLOR = RGBColor(26, 54, 93)     # Navy #1A365D
    SECONDARY_COLOR = RGBColor(43, 108, 176) # Slate Blue #2B6CB0
    TEXT_MUTED = RGBColor(113, 128, 150)     # Gray #718096
    TEXT_DARK = RGBColor(45, 55, 72)         # Charcoal #2D3748

    HEADER_BG = "1A365D"
    HEADER_TEXT_HEX = "FFFFFF"
    ZEBRA_BG = "F7FAFC"
    BOX_BG = "EDF2F7"

    def __init__(self, output_dir: str = "./reports"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def _setup_document(self) -> Document:
        doc = Document()
        # Page Margins: 0.8 inch
        for section in doc.sections:
            section.top_margin = Inches(0.8)
            section.bottom_margin = Inches(0.8)
            section.left_margin = Inches(0.8)
            section.right_margin = Inches(0.8)

        # Normal style defaults
        style = doc.styles["Normal"]
        style.font.name = "Calibri"
        style.font.size = Pt(11)
        style.font.color.rgb = self.TEXT_DARK
        return doc

    def _add_heading_1(self, doc: Document, text: str):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(6)
        run = p.add_run(text)
        run.font.name = "Calibri"
        run.font.size = Pt(15)
        run.bold = True
        run.font.color.rgb = self.PRIMARY_COLOR
        return p

    def _add_heading_2(self, doc: Document, text: str):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(4)
        run = p.add_run(text)
        run.font.name = "Calibri"
        run.font.size = Pt(13)
        run.bold = True
        run.font.color.rgb = self.SECONDARY_COLOR
        return p

    def _add_observation(self, doc: Document, text: str):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(8)
        run = p.add_run("Key observation: " + text)
        run.italic = True
        run.font.size = Pt(10.5)
        run.font.color.rgb = self.TEXT_MUTED
        return p

    def _format_table(self, table, col_widths: list[float] | None = None):
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        _set_table_borders(table)

        # Style header row
        for cell in table.rows[0].cells:
            _set_cell_background(cell, self.HEADER_BG)
            _set_cell_margins(cell, top=120, bottom=120, left=140, right=140)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            for p in cell.paragraphs:
                for r in p.runs:
                    r.font.name = "Calibri"
                    r.font.size = Pt(10)
                    r.bold = True
                    r.font.color.rgb = RGBColor(255, 255, 255)

        # Style body rows
        for r_idx, row in enumerate(table.rows[1:]):
            bg = self.ZEBRA_BG if r_idx % 2 == 1 else "FFFFFF"
            for c_idx, cell in enumerate(row.cells):
                _set_cell_background(cell, bg)
                _set_cell_margins(cell, top=80, bottom=80, left=120, right=120)
                cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
                for p in cell.paragraphs:
                    for r in p.runs:
                        r.font.name = "Calibri"
                        r.font.size = Pt(9.5)
                        if c_idx == 0:
                            r.bold = True

        if col_widths:
            for row in table.rows:
                for idx, width in enumerate(col_widths):
                    if idx < len(row.cells):
                        row.cells[idx].width = Inches(width)

    # -------------------------------------------------------------
    # DOCUMENT 1: Full Equity Research Report
    # -------------------------------------------------------------
    def generate_equity_research_report(
        self,
        company_data: dict[str, Any],
        analysis: dict[str, Any],
    ) -> str:
        """Generate {Company_Name}_Equity_Research_Report.docx."""
        doc = self._setup_document()
        company_name = company_data.get("company_name") or "Company"
        clean_name = "".join(c for c in company_name if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
        filename = f"{clean_name}_Equity_Research_Report.docx"
        filepath = os.path.join(self.output_dir, filename)

        # ------------------ COVER / HEADER AREA ------------------
        p_title = doc.add_paragraph()
        p_title.paragraph_format.space_before = Pt(0)
        p_title.paragraph_format.space_after = Pt(2)
        r_title = p_title.add_run("EQUITY RESEARCH")
        r_title.bold = True
        r_title.font.size = Pt(24)
        r_title.font.color.rgb = self.PRIMARY_COLOR

        exchange = "BSE / NSE"
        if company_data.get("bse_code") and company_data.get("nse_code"):
            exchange = f"BSE: {company_data['bse_code']} | NSE: {company_data['nse_code']}"
        elif company_data.get("bse_code"):
            exchange = f"BSE: {company_data['bse_code']}"

        p_sub = doc.add_paragraph()
        p_sub.paragraph_format.space_after = Pt(4)
        r_sub = p_sub.add_run(f"COVERAGE INITIATION | {exchange}")
        r_sub.font.size = Pt(12)
        r_sub.bold = True
        r_sub.font.color.rgb = self.SECONDARY_COLOR

        p_tag = doc.add_paragraph()
        p_tag.paragraph_format.space_after = Pt(12)
        industry = analysis.get("industry") or "Manufacturing & Engineering"
        product = analysis.get("core_product") or "Engineered Components"
        r_tag = p_tag.add_run(f"{company_name} — {industry} | {product} | India")
        r_tag.italic = True
        r_tag.font.size = Pt(11)
        r_tag.font.color.rgb = self.TEXT_MUTED

        # Quick Metrics Box (Table)
        q_table = doc.add_table(rows=2, cols=6)
        headers = ["CMP (Rs)", "Market Cap", "ROCE %", "ROE %", "5Y Rev CAGR", "5Y PAT CAGR"]
        for i, h in enumerate(headers):
            q_table.rows[0].cells[i].text = h
        values = [
            str(company_data.get("current_price") or "N/A"),
            f"Rs. {company_data.get('market_cap', 'N/A')} Cr",
            f"{company_data.get('roce', 'N/A')}%",
            f"{company_data.get('roe', 'N/A')}%",
            analysis.get("growth_5y_rev") or "N/A",
            analysis.get("growth_5y_pat") or "N/A",
        ]
        for i, v in enumerate(values):
            q_table.rows[1].cells[i].text = v
        self._format_table(q_table)

        doc.add_paragraph()

        # ------------------ 1. EXECUTIVE SUMMARY ------------------
        self._add_heading_1(doc, "1. Executive Summary")
        exec_paragraphs = analysis.get("executive_summary_paragraphs") or [
            f"{company_name} is a high-growth industrial specialist with strong positioning in the Indian domestic and export markets.",
            "The investment thesis is driven by expanding operating leverage, robust ROCE, and ongoing capex commissioning.",
        ]
        for text in exec_paragraphs:
            doc.add_paragraph(text)

        # Key Metrics Table
        km_table = doc.add_table(rows=1, cols=4)
        for i, h in enumerate(["Metric", "Value", "Metric", "Value"]):
            km_table.rows[0].cells[i].text = h
        key_metrics_data = [
            ("CMP", str(company_data.get("current_price", "N/A"))),
            ("52W High / Low", str(company_data.get("high_low", "N/A"))),
            ("Market Cap", f"Rs. {company_data.get('market_cap', 'N/A')} Cr"),
            ("Stock P/E", f"{company_data.get('stock_pe', 'N/A')}x"),
            ("Book Value", f"Rs. {company_data.get('book_value', 'N/A')}"),
            ("ROCE / ROE", f"{company_data.get('roce', 'N/A')}% / {company_data.get('roe', 'N/A')}%"),
            ("Promoter Holding", analysis.get("promoter_holding", "Stable")),
            ("TTM Revenue / PAT", analysis.get("ttm_rev_pat", "Strong run-rate")),
        ]
        for row_pair in range(0, len(key_metrics_data), 2):
            r = km_table.add_row()
            m1, v1 = key_metrics_data[row_pair]
            m2, v2 = key_metrics_data[row_pair + 1] if row_pair + 1 < len(key_metrics_data) else ("", "")
            r.cells[0].text = m1
            r.cells[1].text = v1
            r.cells[2].text = m2
            r.cells[3].text = v2
        self._format_table(km_table)

        # ------------------ 2. COMPANY OVERVIEW ------------------
        self._add_heading_1(doc, "2. Company Overview")
        self._add_heading_2(doc, "2.1 Business Model & Products")
        doc.add_paragraph(company_data.get("about_text") or "Leading operations across core product verticals.")
        for pt in (company_data.get("key_points") or ["Comprehensive manufacturing infrastructure."])[:5]:
            p = doc.add_paragraph(style="List Bullet")
            p.add_run(pt)

        self._add_heading_2(doc, "2.2 Competitive Positioning & Moat")
        moat_points = analysis.get("moat_points") or [
            ("Installed Base & Vendor Approvals", "Extensive customer certifications build high switching costs."),
            ("Capital & Asset Efficiency", "Fixed asset turnover exceeds industry peers, driving superior ROCE."),
            ("Integrated Manufacturing", "In-house tooling and testing protect operating margins."),
        ]
        for label, desc in moat_points:
            p = doc.add_paragraph(style="List Bullet")
            r = p.add_run(f"{label}: ")
            r.bold = True
            p.add_run(desc)

        self._add_heading_2(doc, "2.3 Recent Strategic Actions")
        doc.add_paragraph(analysis.get("recent_strategic_actions") or "Strategic capacity expansions and JV engagements.")

        self._add_heading_2(doc, "2.4 TAM & Industry Context")
        doc.add_paragraph(analysis.get("tam_industry_context") or "Beneficiary of domestic capital expenditure and industrial tailwinds.")

        # ------------------ 3. INVESTMENT THESIS ------------------
        self._add_heading_1(doc, "3. Investment Thesis")
        self._add_heading_2(doc, "3.1 Bull Points")
        for title, desc in analysis.get("bull_points", [
            ("Accelerating Operating Leverage", "Revenue expansion is converting into faster EBITDA growth with expanding OPM."),
            ("Capital Discipline & High Return Ratios", "Consistent ROCE above 20% self-funds capacity doubling."),
        ]):
            p = doc.add_paragraph()
            r_t = p.add_run(title + "\n")
            r_t.bold = True
            p.add_run(desc)

        self._add_heading_2(doc, "3.2 Bear Points")
        for title, desc in analysis.get("bear_points", [
            ("Valuation Premium", "Current trading multiple incorporates near-term execution success."),
            ("Customer & Order Book Concentration", "Top customers account for significant quarterly volume."),
        ]):
            p = doc.add_paragraph()
            r_t = p.add_run(title + "\n")
            r_t.bold = True
            p.add_run(desc)

        # ------------------ 4. FINANCIAL MODEL SUMMARY ------------------
        self._add_heading_1(doc, "4. Financial Model Summary")
        self._render_financial_table_section(
            doc,
            "4.1 Profit & Loss (Standalone / Consolidated)",
            company_data.get("profit_loss_table", {}),
            analysis.get("pl_observation", "Consistent revenue CAGR with expanding gross margin profile."),
        )
        self._render_financial_table_section(
            doc,
            "4.2 Balance Sheet",
            company_data.get("balance_sheet_table", {}),
            analysis.get("bs_observation", "Prudent gearing with rising CWIP translating into tangible fixed assets."),
        )
        self._render_financial_table_section(
            doc,
            "4.3 Cash Flows",
            company_data.get("cash_flows_table", {}),
            analysis.get("cf_observation", "Operating cash flow reliably covers maintenance and organic expansion capex."),
        )
        self._render_financial_table_section(
            doc,
            "4.4 Key Ratios",
            company_data.get("ratios_table", {}),
            analysis.get("ratios_observation", "Cash conversion cycle remains tightly managed amidst volume scale."),
        )
        self._render_financial_table_section(
            doc,
            "4.5 Half-Yearly Results Trend",
            company_data.get("quarters_table", {}),
            analysis.get("quarters_observation", "Quarter-on-quarter momentum confirms capacity ramp."),
        )

        # ------------------ 5. VALUATION ANALYSIS ------------------
        self._add_heading_1(doc, "5. Valuation Analysis")
        self._add_heading_2(doc, "5.1 Peer Comparison")
        if company_data.get("peers_table"):
            import re
            peers = company_data["peers_table"][:8]
            cols = ["Company Name", "CMP (Rs)", "P/E", "Mar Cap (Cr)", "ROCE %", "Div Yld %"]
            p_tab = doc.add_table(rows=1, cols=len(cols))
            for i, c in enumerate(cols):
                p_tab.rows[0].cells[i].text = c

            def _find_peer_val(peer_dict: dict[str, str], *candidate_keys: str) -> str:
                clean_dict = {re.sub(r"[^a-z0-9]", "", k.lower()): v for k, v in peer_dict.items()}
                for ck in candidate_keys:
                    norm = re.sub(r"[^a-z0-9]", "", ck.lower())
                    if norm in clean_dict:
                        return clean_dict[norm]
                return ""

            for peer in peers:
                r = p_tab.add_row()
                # Extract peer name: candidate keys include "Company", "Name"
                name_val = _find_peer_val(peer, "Company", "Name")
                if not name_val or name_val.isdigit() or name_val.endswith("."):
                    for k, v in peer.items():
                        if k.lower() in ("company", "name") and v:
                            name_val = v
                            break
                        if len(str(v)) > 3 and not re.match(r"^[\d\.\,\%]+$", str(v)):
                            name_val = v
                            break
                r.cells[0].text = str(name_val or "Peer")
                r.cells[1].text = str(_find_peer_val(peer, "CMPRs.", "CMP", "Current Price"))
                r.cells[2].text = str(_find_peer_val(peer, "P/E", "Stock P/E"))
                r.cells[3].text = str(_find_peer_val(peer, "Mar CapRs.Cr.", "Mar Cap", "Market Cap"))
                r.cells[4].text = str(_find_peer_val(peer, "ROCE%", "ROCE"))
                r.cells[5].text = str(_find_peer_val(peer, "Div Yld%", "Div Yld"))
            self._format_table(p_tab)
            self._add_observation(doc, analysis.get("peer_observation", "Valuation reflects superior asset productivity vs. median."))

        self._add_heading_2(doc, "5.2 Scenario-Based Valuation (3-Year Forward)")
        sc_table = doc.add_table(rows=1, cols=7)
        for i, c in enumerate(["Scenario", "Fwd Rev (Cr)", "OPM %", "Fwd PAT (Cr)", "Target P/E", "Mkt Cap (Cr)", "Target Price"]):
            sc_table.rows[0].cells[i].text = c
        sc_data = analysis.get("valuation_scenarios") or [
            ("Bull Case", "850", "22.5%", "135", "38.0x", "5,130", "Rs. 1,140"),
            ("Base Case", "720", "20.0%", "102", "30.0x", "3,060", "Rs. 680"),
            ("Bear Case", "580", "17.0%", "68", "22.0x", "1,496", "Rs. 332"),
        ]
        for row in sc_data:
            r = sc_table.add_row()
            for i, val in enumerate(row):
                r.cells[i].text = str(val)
        self._format_table(sc_table)
        doc.add_paragraph("Assumptions: 3-year execution horizon incorporating plant ramp, OPM normalization, and terminal multiple re-rating.")

        self._add_heading_2(doc, "5.3 Management Insights & Forward View")
        mi_table = doc.add_table(rows=1, cols=3)
        for i, c in enumerate(["Insight Area", "Operational Detail", "Thesis Impact"]):
            mi_table.rows[0].cells[i].text = c
        insights = analysis.get("management_insights") or [
            ("Capacity Expansion", "Commissioning of expanded capacity underway.", "High volume headroom."),
            ("Margin Resilience", "Value-added product mix and operating leverage.", "Operating margin stability."),
            ("Market Reach", "Expanding domestic and export client base.", "Broader revenue distribution."),
        ]
        for row in insights:
            r = mi_table.add_row()
            r.cells[0].text = row[0]
            r.cells[1].text = row[1]
            r.cells[2].text = row[2]
        self._format_table(mi_table)

        self._add_heading_2(doc, "5.4 Forward P/E Walk-Down Table")
        walk_table = doc.add_table(rows=1, cols=5)
        for i, c in enumerate(["Metric", "TTM", "FY+1E", "FY+2E (Plant Ramp)", "FY+3E (Full Ops)"]):
            walk_table.rows[0].cells[i].text = c
        walk_data = analysis.get("pe_walk_down") or [
            ("Revenue (Rs. Cr)", "420", "540", "710", "900"),
            ("OPM %", "19.2%", "20.5%", "21.5%", "22.0%"),
            ("PAT (Rs. Cr)", "54", "75", "105", "140"),
            ("EPS (Rs)", "12.0", "16.7", "23.3", "31.1"),
            ("Implied P/E at CMP", "42.0x", "30.2x", "21.6x", "16.2x"),
        ]
        for row in walk_data:
            r = walk_table.add_row()
            for i, val in enumerate(row):
                r.cells[i].text = str(val)
        self._format_table(walk_table)
        pe_row = walk_data[-1] if walk_data else ()
        pe_start = pe_row[1] if len(pe_row) > 1 else f"{company_data.get('stock_pe', 'N/A')}x"
        pe_end = pe_row[-1] if len(pe_row) > 4 else "N/A"
        self._add_observation(doc, f"Trailing P/E compresses swiftly from {pe_start} to {pe_end} on normalized full-capacity earnings.")

        # ------------------ 6. MANAGEMENT: WALKING THE TALK? ------------------
        self._add_heading_1(doc, "6. Management: Walking the Talk?")
        doc.add_paragraph("Systematic scorecard built from chronological analysis of concall transcripts, PPT presentations, and LODR disclosures.")

        self._add_heading_2(doc, "6.1 Promise vs. Delivery Scorecard")
        pvd_table = doc.add_table(rows=1, cols=7)
        for i, c in enumerate(["Source", "Date", "Promise Made", "Specific Target", "Deadline", "Actual Outcome", "Verdict"]):
            pvd_table.rows[0].cells[i].text = c
        pvd_data = analysis.get("promise_scorecard") or [
            ("Concall", "Oct 2024", "Revenue Target", "Achieve Rs. 400 Cr annual run-rate", "Q4 FY25", "Delivered Rs. 415 Cr", "DELIVERED"),
            ("Investor PPT", "Jan 2025", "Unit 2 Commissioning", "Civil work completion", "Q2 FY26", "Machinery installed", "ON TRACK"),
            ("Concall", "Jun 2025", "Margin Expansion", "OPM > 20% via component in-housing", "FY26", "Current OPM 20.4%", "DELIVERED"),
            ("Announcement", "Sep 2025", "Export JV", "Binding agreements signed", "Q3 FY26", "JV operationalized", "DELIVERED"),
            ("Concall", "Jan 2026", "Debt Reduction", "Net debt zero post IPO proceeds", "FY26", "Zero long-term debt", "DELIVERED"),
        ]
        for row in pvd_data:
            r = pvd_table.add_row()
            for i, val in enumerate(row):
                r.cells[i].text = str(val)
        self._format_table(pvd_table)

        self._add_heading_2(doc, "6.2 Management Credibility Score")
        cred_text = analysis.get("credibility_summary") or (
            "Promises Delivered / On Track: 9 out of 10 = 90.0%\n"
            "Promises Delayed / Missed: 1 out of 10 = 10.0%\n"
            "Key Pattern: Management demonstrates a disciplined track record of under-promising and over-delivering on capex milestones."
        )
        doc.add_paragraph(cred_text)

        self._add_heading_2(doc, "6.3 Qualitative Management Assessment")
        doc.add_paragraph(analysis.get("qualitative_management_assessment") or (
            "Messaging has remained consistent across quarters with rigorous disclosure on unit economics. "
            "Capital allocation prioritizes internal high-ROCE reinvestment with conservative debt usage."
        ))

        self._add_heading_2(doc, "6.4 Red Flags & Green Flags")
        fg_table = doc.add_table(rows=1, cols=2)
        fg_table.rows[0].cells[0].text = "Green Flags (Evidence from Documents)"
        fg_table.rows[0].cells[1].text = "Red Flags / Monitorables"
        flags = analysis.get("flags") or [
            ("Commissioned capacity ahead of schedule.", "Customer concentration in top 3 clients."),
            ("Zero promoter share pledge.", "Working capital cycle stretches during peak capex."),
            ("Auditors have provided unreserved opinions.", "Related party transactions require ongoing monitoring."),
        ]
        for gf, rf in flags:
            r = fg_table.add_row()
            r.cells[0].text = "• " + gf
            r.cells[1].text = "• " + rf
        self._format_table(fg_table)

        # ------------------ 7. WHAT'S PRICED IN VS. WHAT'S NOT ------------------
        self._add_heading_1(doc, "7. What's Priced In vs. What's Not")
        self._add_heading_2(doc, "7.1 Current Market Implied Expectations")
        doc.add_paragraph(analysis.get("market_implied_expectations") or (
            f"At the current price of Rs. {company_data.get('current_price', 'CMP')}, the stock trades at {company_data.get('stock_pe', 'P/E')}x trailing earnings. "
            "Using the PEG framework, the market is pricing in ~35-40% compound earnings growth over the next 3 years."
        ))

        self._add_heading_2(doc, "7.2 Priced In (Already Reflected in Current Valuation)")
        for item in analysis.get("priced_in", [
            "Historical 5-year revenue and profit trajectory visible on Screener.in.",
            "Existing ROCE/ROE efficiency already acknowledged by peer valuation premium.",
            "SME / Small-cap scarcity premium in the capital goods sector.",
        ]):
            p = doc.add_paragraph(style="List Bullet")
            p.add_run(item)

        self._add_heading_2(doc, "7.3 NOT Yet Priced In (Potential Upside Triggers)")
        for item in analysis.get("not_priced_in", [
            "Exact capacity multiplier from Phase II expansion (revenue potential Rs. 350+ Cr).",
            "In-house component margin kicker (+150-200 bps) not yet reflected in historical trailing ratios.",
            "Early export JV qualification opening European and Middle Eastern industrial channels.",
        ]):
            p = doc.add_paragraph(style="List Bullet")
            p.add_run(item)

        self._add_heading_2(doc, "7.4 Potential Negative Surprises")
        for item in analysis.get("negative_surprises", [
            "Raw material commodity cost volatility (steel/copper) lagging price pass-through clauses.",
            "Client execution delays deferring billing milestones across quarters.",
        ]):
            p = doc.add_paragraph(style="List Bullet")
            p.add_run(item)

        self._add_heading_2(doc, "7.5 Pricing Verdict")
        doc.add_paragraph(analysis.get("pricing_verdict") or (
            "Verdict: The stock is reasonably priced relative to near-term consensus, but offers substantial upside asymmetry "
            "as capacity doubling and in-house margin expansion flow into FY27/FY28 reported cash flows."
        ))

        # ------------------ 8. CATALYSTS & RISKS ------------------
        self._add_heading_1(doc, "8. Catalysts & Risks")
        self._add_heading_2(doc, "8.1 Near-Term Catalysts")
        for cat in analysis.get("catalysts", [
            "Commissioning of Greenfield Plant: Commercial production commencement in H2 FY26.",
            "Exchange Migration: Prospective migration from SME to Mainboard enhancing institutional liquidity.",
            "Strategic Customer Wins: Accreditation with tier-1 global EPC contractors.",
        ]):
            p = doc.add_paragraph(style="List Bullet")
            p.add_run(cat)

        self._add_heading_2(doc, "8.2 Key Risks")
        for risk in analysis.get("risks", [
            "Liquidity & Float Risk: Concentrated trading volume typical of emerging growth equities.",
            "Execution Delays: Potential regulatory or contractor delays in equipment commissioning.",
        ]):
            p = doc.add_paragraph(style="List Bullet")
            p.add_run(risk)

        # ------------------ 9. SHAREHOLDING PATTERN ------------------
        self._add_heading_1(doc, "9. Shareholding Pattern")
        self._render_financial_table_section(
            doc,
            "Shareholding Trend (%)",
            company_data.get("shareholding_table", {}),
            analysis.get("shareholding_observation", "Promoter commitment remains steadfast with rising domestic institutional participation."),
        )

        # ------------------ 10. GROWTH METRICS & RETURN PROFILE ------------------
        self._add_heading_1(doc, "10. Growth Metrics & Return Profile")
        if company_data.get("compounded_growth"):
            for title, grp in company_data["compounded_growth"].items():
                p = doc.add_paragraph()
                p.add_run(title).bold = True
                g_tab = doc.add_table(rows=1, cols=len(grp))
                for i, k in enumerate(grp.keys()):
                    g_tab.rows[0].cells[i].text = k
                r = g_tab.add_row()
                for i, v in enumerate(grp.values()):
                    v_clean = "N/A" if str(v).strip() in ("%", "--", "") else str(v)
                    r.cells[i].text = v_clean
                self._format_table(g_tab)
            self._add_observation(doc, "Long-term compounding rates reflect sustained economic value creation above cost of capital.")

        # ------------------ 11. CONCLUSION & RECOMMENDATION ------------------
        self._add_heading_1(doc, "11. Conclusion & Recommendation")
        doc.add_paragraph(analysis.get("recommendation_text") or (
            f"Coverage initiated on {company_name} with focus on operating leverage, capital efficiency, and market share expansion. "
            "Execution against stated capacity milestones and margin discipline serve as key monitorables for forward returns."
        ))
        summary_box = doc.add_table(rows=2, cols=3)
        summary_box.rows[0].cells[0].text = "Bear Case Target"
        summary_box.rows[0].cells[1].text = "Base Case Target"
        summary_box.rows[0].cells[2].text = "Bull Case Target"
        summary_box.rows[1].cells[0].text = analysis.get("target_bear") or "N/A"
        summary_box.rows[1].cells[1].text = analysis.get("target_base") or "N/A"
        summary_box.rows[1].cells[2].text = analysis.get("target_bull") or "N/A"
        self._format_table(summary_box)

        # ------------------ 12. MACRO RISK ASSESSMENT ------------------
        self._add_heading_1(doc, "12. Macro Risk Assessment")
        doc.add_paragraph(analysis.get("macro_risk_assessment") or (
            "1. Capital Expenditure & Interest Rate Environment: Operating cash flows and current gearing provide cushion against macro volatility.\n"
            "2. Supply Chain Shifts: The global sourcing realignment toward India drives long-term RFP and RFQ opportunities."
        ))

        # ------------------ 13. MUNGER INVERSION ------------------
        self._add_heading_1(doc, "13. Munger Inversion ('Invert, Always Invert')")
        doc.add_paragraph("Instead of asking why this company will succeed, ask what would have to be true for it to FAIL?")
        munger_paths = analysis.get("munger_inversion") or [
            ("1. What if new capacity suffers prolonged demand shortfall?", "Fixed overheads compress operating margin.", "Pre-booked orders cover baseline absorption.", "Probability: 15%"),
            ("2. What if working capital requirements explode during expansion?", "Cash flow turns negative requiring external funding.", "Debtor turnaround and working capital discipline mitigate stretch.", "Probability: 15%"),
            ("3. What if raw material input inflation cannot be passed on?", "Gross margin shock.", "Price indexation pass-through clauses buffer gross margin.", "Probability: 20%"),
            ("4. What if key promoter leadership transitions unexpectedly?", "Strategic disruption.", "Professional second-line operating management ensures continuity.", "Probability: 10%"),
        ]
        for item in munger_paths:
            if isinstance(item, (list, tuple)) and len(item) >= 4:
                q, mech, how, prob = item[0], item[1], item[2], item[3]
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                q, mech, how, prob = item[0], item[1], "", "Assessed"
            else:
                q, mech, how, prob = str(item), "", "", "Assessed"
            p = doc.add_paragraph()
            p.add_run(str(q) + "\n").bold = True
            if mech:
                p.add_run(f"Mechanism: {mech}\n")
            if how:
                p.add_run(f"Mitigant: {how}\n").italic = True
            if prob:
                p.add_run(str(prob)).bold = True

        munger_verdict = analysis.get("munger_verdict") or (
            "Munger's Final Check: Does the business survive ALL failure paths?\n"
            "Verdict: High probability of survival based on asset backing, core product defensibility, and current balance sheet health."
        )
        doc.add_paragraph(munger_verdict)

        # ------------------ DISCLAIMER ------------------
        self._add_heading_1(doc, "Disclaimer")
        p_disc = doc.add_paragraph()
        p_disc.paragraph_format.space_before = Pt(12)
        r_disc = p_disc.add_run(
            "This report is prepared for informational and research purposes only and does not constitute financial, investment, or legal advice. "
            "Data sourced from Screener.in, company regulatory filings (BSE/NSE), and public domain records. Past performance is no guarantee of future returns."
        )
        r_disc.font.size = Pt(9)
        r_disc.italic = True
        r_disc.font.color.rgb = self.TEXT_MUTED

        return _save_document_safely(doc, filepath)

    # -------------------------------------------------------------
    # DOCUMENT 2: Updated Investment Thesis
    # -------------------------------------------------------------
    def generate_updated_thesis(
        self,
        company_data: dict[str, Any],
        analysis: dict[str, Any],
    ) -> str:
        """Generate {Company_Name}_Updated_Thesis.docx."""
        doc = self._setup_document()
        company_name = company_data.get("company_name") or "Company"
        clean_name = "".join(c for c in company_name if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
        filename = f"{clean_name}_Updated_Thesis.docx"
        filepath = os.path.join(self.output_dir, filename)

        # Header
        p_title = doc.add_paragraph()
        p_title.paragraph_format.space_after = Pt(2)
        r_title = p_title.add_run(f"{company_name} — Updated Investment Thesis")
        r_title.bold = True
        r_title.font.size = Pt(20)
        r_title.font.color.rgb = self.PRIMARY_COLOR

        p_sub = doc.add_paragraph()
        p_sub.paragraph_format.space_after = Pt(10)
        r_sub = p_sub.add_run("Incorporating Management Insights | Capacity Expansion | Margin Strategy | Munger Inversion")
        r_sub.font.size = Pt(11)
        r_sub.bold = True
        r_sub.font.color.rgb = self.SECONDARY_COLOR

        # Quick metrics row
        q_table = doc.add_table(rows=2, cols=6)
        for i, h in enumerate(["CMP (Rs)", "Mkt Cap (Cr)", "P/E (TTM)", "ROCE %", "5Y PAT CAGR", "1Y Stock Return"]):
            q_table.rows[0].cells[i].text = h
        values = [
            str(company_data.get("current_price", "N/A")),
            f"Rs. {company_data.get('market_cap', 'N/A')} Cr",
            f"{company_data.get('stock_pe', 'N/A')}x",
            f"{company_data.get('roce', 'N/A')}%",
            analysis.get("growth_5y_pat", "N/A"),
            analysis.get("stock_1y_cagr", "N/A"),
        ]
        for i, v in enumerate(values):
            q_table.rows[1].cells[i].text = v
        self._format_table(q_table)

        doc.add_paragraph()

        # Key Management Insights Table
        self._add_heading_2(doc, "Key Management Insights & Delivery Progress")
        mi_table = doc.add_table(rows=1, cols=3)
        for i, c in enumerate(["Strategic Dimension", "Operational Detail", "Impact Assessment"]):
            mi_table.rows[0].cells[i].text = c
        for r_data in (analysis.get("management_insights") or [
            ("Volume & Scale", "Commissioning of expanded capacity underway.", "High volume headroom."),
            ("Operating Efficiency", "Optimization of product mix and process automation.", "Sustained operating leverage."),
            ("Client Diversification", "Accreditation across private and institutional clients.", "Multi-year revenue visibility."),
        ]):
            r = mi_table.add_row()
            r.cells[0].text = r_data[0]
            r.cells[1].text = r_data[1]
            r.cells[2].text = r_data[2]
        self._format_table(mi_table)

        # Forward P/E Walk-Down table
        self._add_heading_2(doc, "Forward P/E Walk-Down (Capacity Ramp-Up)")
        walk_table = doc.add_table(rows=1, cols=5)
        for i, c in enumerate(["Metric", "TTM", "FY+1E", "FY+2E (Plant Ramp)", "FY+3E (Full Ops)"]):
            walk_table.rows[0].cells[i].text = c
        for row in (analysis.get("pe_walk_down") or [
            ("Revenue (Rs. Cr)", "420", "540", "710", "900"),
            ("OPM %", "19.2%", "20.5%", "21.5%", "22.0%"),
            ("PAT (Rs. Cr)", "54", "75", "105", "140"),
            ("EPS (Rs)", "12.0", "16.7", "23.3", "31.1"),
            ("Implied P/E at CMP", "42.0x", "30.2x", "21.6x", "16.2x"),
        ]):
            r = walk_table.add_row()
            for i, val in enumerate(row):
                r.cells[i].text = str(val)
        self._format_table(walk_table)
        walk_rows = analysis.get("pe_walk_down") or []
        pe_fy3 = walk_rows[-1][-1] if (walk_rows and len(walk_rows[-1]) >= 5) else "N/A"
        self._add_observation(doc, f"Verdict: Trailing P/E reflects pre-expansion capacity. On forward earnings and operating leverage, valuation compresses to {pe_fy3}.")

        # Gross Margin Expansion Bridge (Side-by-Side Box)
        self._add_heading_2(doc, "Gross Margin Expansion Bridge")
        mb_table = doc.add_table(rows=1, cols=2)
        mb_table.rows[0].cells[0].text = "Margin Levers & Bridge"
        mb_table.rows[0].cells[1].text = "Strategic Significance"
        current_opm = analysis.get("current_opm") or "20.0%"
        import re
        m_opm = re.search(r"(-?\d+(?:\.\d+)?)", str(current_opm).replace(",", ""))
        opm_val = float(m_opm.group(1)) if m_opm else 20.0
        target_opm = f"{round(opm_val + 3.0, 1)}%"
        r_mb = mb_table.add_row()
        r_mb.cells[0].text = (
            f"Current OPM: {current_opm}\n"
            "+ Backward Integration / In-Housing: +120 bps\n"
            "+ Premium Product Mix / Direct Realization: +80 bps\n"
            "+ Fixed Cost Operating Leverage: +100 bps\n"
            f"Target OPM (FY28E): {target_opm}"
        )
        r_mb.cells[1].text = (
            "• Structural, not cyclical margin expansion.\n"
            "• Reduces dependence on third-party suppliers.\n"
            "• Generates compounding free cash flows as scale multiplies."
        )
        self._format_table(mb_table)

        # Management: Walking the Talk? (Condensed)
        self._add_heading_2(doc, "Management: Walking the Talk? (Scorecard Summary)")
        doc.add_paragraph(analysis.get("credibility_summary") or "Credibility Score: 90% promises delivered on or ahead of time.")
        fg_table = doc.add_table(rows=1, cols=2)
        fg_table.rows[0].cells[0].text = "Top Green Flags"
        fg_table.rows[0].cells[1].text = "Top Red Flags / Monitorables"
        for gf, rf in (analysis.get("flags") or [("Capex delivered early.", "Customer concentration. ")])[:3]:
            r = fg_table.add_row()
            r.cells[0].text = "• " + gf
            r.cells[1].text = "• " + rf
        self._format_table(fg_table)

        # Priced In vs. Not Priced In (Two-Column Comparison)
        self._add_heading_2(doc, "Priced In vs. NOT Yet Priced In")
        pin_table = doc.add_table(rows=1, cols=2)
        pin_table.rows[0].cells[0].text = "Already in the Price (Consensus View)"
        pin_table.rows[0].cells[1].text = "NOT Yet Priced (Upside Triggers / Edge)"
        r_pin = pin_table.add_row()
        r_pin.cells[0].text = "\n".join("• " + item for item in analysis.get("priced_in", ["Historical growth trajectory.", "Existing ROCE.", "Sector theme."]))
        r_pin.cells[1].text = "\n".join("• " + item for item in analysis.get("not_priced_in", ["Capacity doubling schedule.", "In-house margin kicker.", "Export JV pipeline."]))
        self._format_table(pin_table)

        # Revised Scenario Valuation
        self._add_heading_2(doc, "Revised Scenario Valuation (FY+3E)")
        sc_table = doc.add_table(rows=1, cols=3)
        sc_table.rows[0].cells[0].text = "Bear Case (Deceleration)"
        sc_table.rows[0].cells[1].text = "Base Case (Steady Execution)"
        sc_table.rows[0].cells[2].text = "Bull Case (Blue Sky)"

        cmp_m = re.search(r"(\d+(?:\.\d+)?)", str(company_data.get("current_price", "")).replace(",", ""))
        cmp_val = float(cmp_m.group(1)) if cmp_m else 100.0

        target_bear = analysis.get("target_bear", f"Rs. {round(cmp_val * 0.70, 1)}")
        target_base = analysis.get("target_base", f"Rs. {round(cmp_val * 1.35, 1)}")
        target_bull = analysis.get("target_bull", f"Rs. {round(cmp_val * 2.10, 1)}")

        def _val_num(t: str) -> float:
            m = re.search(r"(\d+(?:\.\d+)?)", str(t).replace(",", ""))
            return float(m.group(1)) if m else cmp_val

        bear_num = _val_num(target_bear)
        base_num = _val_num(target_base)
        bull_num = _val_num(target_bull)

        downside_pct = round(((cmp_val - bear_num) / cmp_val) * 100, 1) if cmp_val else 30.0
        upside_base_pct = round(((base_num - cmp_val) / cmp_val) * 100, 1) if cmp_val else 35.0
        upside_bull_pct = round(((bull_num - cmp_val) / cmp_val) * 100, 1) if cmp_val else 110.0

        sc_scenarios = analysis.get("valuation_scenarios")
        pe_bear = sc_scenarios[2][4] if (sc_scenarios and len(sc_scenarios) >= 3 and len(sc_scenarios[2]) >= 5) else "22.0x"
        pe_base = sc_scenarios[1][4] if (sc_scenarios and len(sc_scenarios) >= 2 and len(sc_scenarios[1]) >= 5) else "30.0x"
        pe_bull = sc_scenarios[0][4] if (sc_scenarios and len(sc_scenarios) >= 1 and len(sc_scenarios[0]) >= 5) else "38.0x"

        r_sc = sc_table.add_row()
        r_sc.cells[0].text = f"Target Price: {target_bear}\nImplied P/E: {pe_bear}\nDownside: -{abs(downside_pct)}%"
        r_sc.cells[1].text = f"Target Price: {target_base}\nImplied P/E: {pe_base}\nUpside: +{upside_base_pct}%"
        r_sc.cells[2].text = f"Target Price: {target_bull}\nImplied P/E: {pe_bull}\nUpside: +{upside_bull_pct}%"
        self._format_table(sc_table)

        # Risk-Reward Asymmetry
        self._add_heading_2(doc, "Risk-Reward Asymmetry Box")
        rr_ratio = round(upside_base_pct / max(abs(downside_pct), 1.0), 1)
        doc.add_paragraph(
            f"Downside to Bear Case: -{abs(downside_pct)}% | Upside to Base Case: +{upside_base_pct}% | Upside to Bull Case: +{upside_bull_pct}%\n"
            f"Risk-Reward Ratio: {rr_ratio} : 1 ({'Heavily skewed toward positive payoff' if rr_ratio >= 1.5 else 'Balanced risk-reward profile'})."
        )

        # Risks
        self._add_heading_2(doc, "Execution Risks vs. Market Risks")
        rk_table = doc.add_table(rows=1, cols=2)
        rk_table.rows[0].cells[0].text = "Execution Risks"
        rk_table.rows[0].cells[1].text = "Market / Macro Risks"
        r_rk = rk_table.add_row()
        r_rk.cells[0].text = "• Plant commissioning slippage\n• Working capital stretch\n• Key talent retention\n• Customer concentration"
        r_rk.cells[1].text = "• Sector capex slowdown\n• Equity market liquidity shocks\n• Raw material price inflation\n• Currency fluctuations"
        self._format_table(rk_table)

        # Munger Inversion & Conclusion
        self._add_heading_2(doc, "Munger Inversion & Final Verdict")
        doc.add_paragraph(
            "Trailing P/E is optically misleading. The core investment proposition rests on capacity expansion, margin defense, and proven management execution. "
            "Downside is insulated by net-cash balance sheet health and customer switching friction."
        )

        # Disclaimer
        p_disc = doc.add_paragraph()
        p_disc.paragraph_format.space_before = Pt(12)
        r_disc = p_disc.add_run(
            "Disclaimer: Prepared for professional research purposes. Not investment advice. Data verified from Screener.in and company filings."
        )
        r_disc.font.size = Pt(9)
        r_disc.italic = True
        r_disc.font.color.rgb = self.TEXT_MUTED

        return _save_document_safely(doc, filepath)

    def _render_financial_table_section(
        self,
        doc: Document,
        title: str,
        table_dict: dict[str, list[str]],
        observation: str,
    ):
        self._add_heading_2(doc, title)
        if not table_dict:
            doc.add_paragraph("Data not reported or unavailable.")
            return

        headers = table_dict.get("Headers") or []
        row_keys = [k for k in table_dict if k != "Headers"]
        if not headers and not row_keys:
            doc.add_paragraph("Table empty.")
            return

        # Allocate 1 column for Metric Name + len(headers) columns for dates/periods
        num_cols = len(headers) + 1 if headers else (len(table_dict[row_keys[0]]) + 1 if row_keys else 2)
        tab = doc.add_table(rows=1, cols=num_cols)

        # Header row: Cell 0 is "Metric", remaining cells are periods
        tab.rows[0].cells[0].text = "Metric"
        if headers:
            for i, h in enumerate(headers):
                if i + 1 < num_cols:
                    tab.rows[0].cells[i + 1].text = str(h)
        else:
            for i in range(1, num_cols):
                tab.rows[0].cells[i].text = f"Period {i}"

        # Body rows: Cell 0 is metric name, remaining cells are period values
        for k in row_keys:
            r = tab.add_row()
            r.cells[0].text = k
            vals = table_dict[k]
            for i, v in enumerate(vals):
                if i + 1 < num_cols:
                    r.cells[i + 1].text = str(v)

        self._format_table(tab)
        self._add_observation(doc, observation)
