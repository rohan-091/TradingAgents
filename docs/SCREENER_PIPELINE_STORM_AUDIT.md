# STORM Research Briefing: Screener.in Research Pipeline Deep Audit (Forensic Master Edition - 24 Points)

**Topic**: Forensic audit of `scripts/run_screener_research.py`, `tradingagents/agents/researchers/screener_researcher.py`, `tradingagents/report_docx.py`, and `tradingagents/dataflows/vendors/screener/client.py` for hardcoded mock values, table alignment defects, accounting distortions, silent fallbacks, and brittle DOM dependencies.  
**Date**: October 2026 (Comprehensive Multi-Perspective Review)  
**Methodology**: Stanford OVAL STORM Multi-Perspective Research Framework (NAACL 2024)

---

## Executive Summary

Following a deep forensic inspection of the codebase and verification against live Screener.in extraction runs (tested on Yash Highvoltage Ltd, BSE: 544310), we identified **24 distinct defects, accounting calculation bugs, formatting errors, and architectural vulnerabilities**.

The most critical vulnerabilities uncovered include:
1. **Systemic 1-Column Table Shift & TTM Truncation** ([`report_docx.py:L833-851`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/tradingagents/report_docx.py#L833-L851)): All financial tables (P&L, Balance Sheet, Cash Flow, Ratios, Quarters, Shareholding) mapped cell 0 in the header to the first date, placing row names under dates, offsetting historical metrics by +1 year, and truncating the latest TTM column.
2. **Negative Sign Destruction on Net Losses** ([`screener_researcher.py:L163, L167`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/tradingagents/agents/researchers/screener_researcher.py#L163)): Regex `re.sub(r"[^\d.]", "", val)` strips the minus sign `-`, converting a `-45 Cr` net loss into a `+45 Cr` profit and negative OPM into positive margin.
3. **Loss-Making Company P/E Blind Spot** ([`screener_researcher.py:L146-150`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/tradingagents/agents/researchers/screener_researcher.py#L146-L150)): Defaulting unlisted/negative P/E to `25.0x`, hallucinating positive valuation multiples and positive forward EPS for loss-making companies.
4. **Target Price vs. Model Disconnect**: Target prices in `valuation_scenarios` are static multipliers of CMP (`cmp * 0.70`, `cmp * 1.35`, `cmp * 2.10`), completely ignoring the Forward PAT and Target P/E printed in the very same table row.
5. **Hardcoded "Net-Cash / Survives All Failures" Claims**: Section 12 and 13 in `report_docx.py` hardcode claims that the company has a "net-cash / low-debt balance sheet" and "survives ALL failure paths" regardless of whether the company is drowning in debt or insolvent.
6. **Peer Table Key Mismatch** ([`report_docx.py:L355-366`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/tradingagents/report_docx.py#L355-L366)): Screener unit headers (`Company`, `CMPRs.`, `Mar CapRs.Cr.`) caused peer names to render as `"1."`, `"2."`, with blank metrics across all columns.
7. **Missing Unit in Updated Thesis Market Cap** ([`report_docx.py:L646`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/tradingagents/report_docx.py#L646)): Formatted as `f"Rs. {market_cap}"`, omitting `" Cr"`, displaying `Rs. 3,480` instead of `Rs. 3,480 Cr`.

Below is the complete 4-phase STORM analysis, contradiction map, exhaustive 24-point defect inventory, and verified remediation specifications.

---

## Phase 1 — Multi-Perspective Scan

### 1. PRACTITIONER (Production Data Engineer & Scraper Architect)
- **Core Position**: The pipeline suffers from silent data contract breaks between the scraper (`client.py`) and the report generator (`report_docx.py`). Beautiful data is extracted into memory, but due to hardcoded key expectations, it either renders as empty strings or gets omitted entirely.
- **Strongest Evidence**:
  - **Peer Table Key Mismatch**: Screener.in generates table headers with units (e.g. `Company`, `CMPRs.`, `Mar CapRs.Cr.`, `ROCE%`, `Div Yld%`). In [`report_docx.py:L360-365`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/tradingagents/report_docx.py#L360-L365), the code attempts `peer.get("Name")`, `peer.get("CMP")`, `peer.get("Mar Cap")`, `peer.get("ROCE %")`. Since `"Name"` does not exist, it falls back to `list(peer.values())[0]` which is the serial number `"1."`, and all other columns render as empty strings `""`.
  - **AJAX Race Condition on Peers**: On Screener.in, `#peers` is populated asynchronously via `/api/company/{id}/peers/`. Playwright only waits for `#top`, so under slower network conditions, the peer table is extracted as empty.
  - **PDF Concall Transcripts**: [`client.py:L142-148`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/tradingagents/dataflows/vendors/screener/client.py#L142-L148) passes raw bytes from PDF URLs into `BeautifulSoup(res.text, "html.parser")`, dumping binary garbage into the LLM context.
  - **Tooltip Contamination**: `td.get_text()` pulls popup tooltips together with row labels, creating bloated strings like `'CFO/EBITDAShare of operating profit converting into cash: CFO (before tax) / Operating Profit'`.
- **Practitioner's Unique Insight**: *"A scraper cannot rely on human-readable column titles remaining static. Without key normalization (`re.sub(r'[^a-zA-Z]', '', k.lower())`), UI changes in the source website quietly wipe out entire tables in your reports."*

---

### 2. ACADEMIC (Financial Engineering & Quantitative Analyst)
- **Core Position**: The financial engine contains severe accounting calculation bugs: regex stripping turns losses into profits, missing P/E multiples default to 25.0x, cell 0 offsets corrupt entire financial statements, and native audited EPS data is ignored in favor of synthetic approximations.
- **Strongest Evidence**:
  - **Negative Sign Destruction**: In [`screener_researcher.py:L163`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/tradingagents/agents/researchers/screener_researcher.py#L163), `re.sub(r"[^\d.]", "", "-45")` produces `"45"`. A company with negative PAT or negative operating margin is mathematically inverted into a profitable company.
  - **Loss-Making Multiple Hallucination**: When a company is loss-making (e.g., Paytm, Ola Electric), Screener has no Stock P/E. Code defaults `pe = 25.0`, modeling positive growth and forward P/E compression on non-existent profits.
  - **Ignoring Audited EPS**: Code calculates `EPS = cmp / pe`, even though Screener's P&L table contains the exact historical and TTM audited numbers in row `"EPS in Rs"`.
  - **Model Disconnect**: Scenario target prices are hardcoded percentage multipliers of CMP rather than derived from `Forward PAT * Target P/E / Share Count`.
  - **Index Mismatch in Word Document**: In [`report_docx.py:L833-851`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/tradingagents/report_docx.py#L833-L851), `num_cols = len(headers)` maps cell 0 in the header to the first date (`"Mar 2020"`), while cell 0 in data rows is `"Sales"`. Every historical year is shifted left by 1 year, and TTM is completely cut off.
- **Academic's Unique Insight**: *"A one-column index offset or stripping a negative sign isn't a cosmetic bug—it is an accounting catastrophe that turns loss-making businesses into compounders and shifts every historical metric by an entire fiscal year."*

---

### 3. SKEPTIC (QA & Chaos Engineer)
- **Core Position**: The agent gives an illusion of comprehensive AI research, but whenever live metrics are missing or the LLM is skipped, it silently leaks hardcoded narrative fragments and fictional promises.
- **Strongest Evidence**:
  - **Omitted Metrics Plumbing**: `data.compounded_growth` extracts 5Y Sales CAGR (44%), 5Y PAT CAGR (58%), and 1Y Stock Return (120%), but `_build_deterministic_financial_analysis` never sets `growth_5y_rev`, `growth_5y_pat`, or `stock_1y_cagr`. Consequently, quick metrics in both Word reports literally printed `"N/A"`.
  - **Hardcoded Walk-Down Text**: [`report_docx.py:L417`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/tradingagents/report_docx.py#L417) hardcoded: `"Trailing P/E compresses swiftly from ~42x to ~16x on normalized full-capacity earnings."`
  - **Mock Governance Scorecard**: [`screener_researcher.py:L225-231`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/tradingagents/agents/researchers/screener_researcher.py#L225-L231) fabricates management promises ("Achieve Rs. 400 Cr revenue run-rate") and awards a 100% score based on fictional milestones.
  - **Unread Annual Reports & PPTs**: The report claims to perform "chronological analysis of concalls, PPTs, and LODR disclosures", but `client.py` never downloads or extracts text from investor presentations or annual reports.
  - **Blind Permanent Bullishness**: The recommendation paragraph in Section 11 always initiates with an "optimistic long-term outlook", with zero capability to issue a "SELL" or "REDUCE" rating.
- **Skeptic's Unique Insight**: *"If a system has 'N/A' sitting next to hardcoded claims of 100% credibility on non-existent concalls, institutional investors will immediately discount the entire report."*

---

### 4. ECONOMIST (Token Budget, Latency & Failure Cost)
- **Core Position**: Monolithic JSON prompts without robust fence extraction create a high-probability failure path where expensive API calls are wasted and silently dropped into fallback mode.
- **Strongest Evidence**:
  - [`screener_researcher.py:L123-128`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/tradingagents/agents/researchers/screener_researcher.py#L123-L128) relied on `.startswith("```json")`. When Gemini prefixes responses with conversational preamble, `json.loads` fails, throwing away a 4,000-token completion and silently serving deterministic fallback text without user notification.
  - Synchronous document requests (up to 3 concalls at 15s timeout each) can stall the pipeline for 45 seconds before agent reasoning begins.
- **Economist's Unique Insight**: *"Silent catch blocks are the enemy of AI engineering. If an LLM call fails, you must log the exact error and explain whether the report is AI-synthesized or deterministic."*

---

### 5. HISTORIAN (DOM & Schema Evolution Precedents)
- **Core Position**: Non-reporting history, layout constraints, and short listing track records create UI artifacts that break rigid parsers.
- **Strongest Evidence**:
  - **Column Squishing on 10+ Year Tables**: In portrait mode with 0.8" margins (6.9" printable width), a 13-column financial table forces cells into 0.45" width, squishing numbers into multiple wrapped lines.
  - **Short History Growth Tables**: For newly listed companies or SMEs lacking 10-year history, Screener displays empty percentage values (`%` or `--`). [`report_docx.py:L538-551`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/tradingagents/report_docx.py#L538-L551) literally prints `10 Years: %` into the Word document.
  - **Standalone vs. Consolidated Divergence**: Scraper does not click or detect the `[Consolidated]` toggle button, taking whichever tab Screener serves by default, causing 5x-10x revenue discrepancies for holding companies (e.g. Tata Motors, L&T).
- **Historian's Unique Insight**: *"A pipeline tested only on mature 10-year companies breaks immediately on recent IPOs, holding company structures, and printable document page constraints."*

---

## Phase 2 — Contradiction Map & Systemic Blind Spots

| Area of Tension | Assumption in Code | Reality in Screener.in DOM / Accounting | Impact & Resolution |
| :--- | :--- | :--- | :--- |
| **Financial Table Headers** | `headers` array has length `N` and represents all columns. | `headers` has length `N` (the dates), but the table has `N+1` columns (Metric Name + `N` dates). | Row cells were shifted left by 1 column, metric names sat under the 1st year, and TTM was truncated. **Fix**: Add a dedicated `"Metric"` column header and allocate `len(headers) + 1` columns. |
| **Negative Values** | Digits can be extracted via `re.sub(r"[^\d.]", "", val)`. | Negative values start with `-` (e.g. `-45`, `-12%`). Regex strips `-`. | Net losses and negative margins turn into positive profits. **Fix**: Use `re.search(r"(-?\d+(?:\.\d+)?)", val)`. |
| **Loss-Making P/E** | Every listed stock has a valid P/E multiple or defaults to 25x. | Loss-making stocks have no P/E. Defaulting to 25x hallucinates profitability. | Models fake earnings and positive forward EPS. **Fix**: Flag as `Loss-Making / Negative P/E`, skip P/E walk-down, and use Price-to-Sales (P/S). |
| **Valuation Modeling** | Target prices are hardcoded percentages of CMP (`cmp * 1.35`). | Financial targets must be derived from `Fwd PAT * Target P/E / Diluted Shares`. | Internal mathematical contradiction within the valuation scenario table. **Fix**: Derive targets mathematically from Fwd PAT and Target P/E. |
| **Balance Sheet Debt** | Every company is assumed to be net-cash or have low gearing. | Many companies have large borrowings on Balance Sheet. | Reports falsely claim heavily indebted companies have "net-cash balance sheets". **Fix**: Parse Borrowings from `balance_sheet_table` and compute Net Debt. |
| **Peer Comparison Keys** | Table keys are clean strings: `"Name"`, `"CMP"`, `"P/E"`. | Table keys contain units and icons: `'Company'`, `'CMPRs.'`, `'Mar CapRs.Cr.'`, `'ROCE%'`. | All peer names rendered as `"1."`, `"2."`, and financial metrics were blank. **Fix**: Implement normalized case-insensitive fuzzy key lookup. |
| **Market Cap Unit in Thesis** | Quick metrics format as `f"Rs. {market_cap}"`. | Market Cap numbers on Screener are in Crores. Omitting `" Cr"` creates confusion. | Shows `Rs. 3,480` instead of `Rs. 3,480 Cr`. **Fix**: Add `" Cr"` suffix. |
| **Double-Negative Formatting** | Risk box uses `-{downside_pct}%`. | If downside calculation is negative, formatting produces `--10.0%`. | Typographical error in risk-reward summary. **Fix**: Format with `f"-{abs(downside_pct)}%"`. |

---

## Phase 3 — Complete Inventory of All 24 Vulnerabilities

| # | Component & Line | Defect / Vulnerability | Severity | Real-World Impact |
| :--- | :--- | :--- | :--- | :--- |
| **1** | [`report_docx.py:L833-851`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/tradingagents/report_docx.py#L833-L851) | **Table Column Offset & TTM Truncation**: `num_cols = len(headers)` instead of `len(headers) + 1`. Cell 0 in header got 1st date; cell 0 in body got Metric Name. | **CRITICAL** | Every financial table in the Word report had historical dates shifted left by 1 year, and latest TTM/quarter was completely cut off. |
| **2** | [`screener_researcher.py:L163, L167`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/tradingagents/agents/researchers/screener_researcher.py#L163) | **Negative Sign Destruction on Net Losses**: `re.sub(r"[^\d.]", "", val)` strips `-`. | **CRITICAL** | Converts net losses (e.g. `-45 Cr`) into positive profits (`+45 Cr`) and negative OPM into positive margin. |
| **3** | [`screener_researcher.py:L146-150`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/tradingagents/agents/researchers/screener_researcher.py#L146-L150) | **Loss-Making P/E Blind Spot**: Defaulting blank `stock_pe` to `25.0x`. | **CRITICAL** | Claims loss-making companies trade at 25x earnings and calculates synthetic positive EPS. |
| **4** | [`screener_researcher.py:L173-175`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/tradingagents/agents/researchers/screener_researcher.py#L173-L175) | **Target Price vs. Financial Model Disconnect**: Target prices are static CMP multipliers (`cmp * 1.35`) rather than `Fwd PAT * Target P/E`. | **CRITICAL** | Internal contradiction between Forward PAT, Multiple, and Target Price in the valuation table. |
| **5** | [`report_docx.py:L571, L594`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/tradingagents/report_docx.py#L571) | **Hardcoded Net-Cash & Solvency Claims**: Asserts company has "net-cash balance sheet" and "survives ALL failure paths" regardless of debt. | **CRITICAL** | Grossly misrepresents indebted or financially distressed companies. |
| **6** | [`report_docx.py:L355-366`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/tradingagents/report_docx.py#L355-L366) | **Peer Comparison Key Mismatch**: Looks for `"Name"`, `"CMP"`, `"Mar Cap"`, `"ROCE %"`. Actual keys are `'Company'`, `'CMPRs.'`, `'Mar CapRs.Cr.'`, `'ROCE%'`. | **CRITICAL** | Peer table rendered serial numbers (`"1."`, `"2."`) and blank columns. |
| **7** | [`report_docx.py:L646`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/tradingagents/report_docx.py#L646) | **Missing Unit in Updated Thesis Market Cap**: Prints `f"Rs. {company_data.get('market_cap')}"` without `" Cr"`. | **HIGH** | Shows `Rs. 3,480` instead of `Rs. 3,480 Cr`. |
| **8** | [`screener_researcher.py:L186-273`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/tradingagents/agents/researchers/screener_researcher.py#L186-L273) | **Omitted Growth & Shareholding Plumbing**: `compounded_growth` and `shareholding_table` extracted, but never assigned to `analysis` keys. | **HIGH** | Quick metrics showed `"N/A"` for 5Y Rev CAGR, 5Y PAT CAGR, 1Y Stock Return; Promoter Holding defaulted to `"Stable"`. |
| **9** | [`screener_researcher.py:L182`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/tradingagents/agents/researchers/screener_researcher.py#L182) | **Synthetic EPS Calculation**: Calculates `EPS = cmp / pe` instead of reading the audited `"EPS in Rs"` row from Screener's P&L table. | **HIGH** | Yields inaccurate EPS numbers when audited EPS is already available. |
| **10** | [`report_docx.py:L417`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/tradingagents/report_docx.py#L417) | **Hardcoded Walk-Down Text**: Static text `"Trailing P/E compresses swiftly from ~42x to ~16x..."` regardless of actual P/E. | **HIGH** | False narrative in full Equity Research Report. |
| **11** | [`screener_researcher.py:L225-231`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/tradingagents/agents/researchers/screener_researcher.py#L225-L231) | **Mock Concall Scorecard**: Fabricates specific promises ("Rs. 400 Cr revenue", "OPM > 20%") when concall data is absent. | **HIGH** | Hallucinates management promises and awards 100% credibility on fake data. |
| **12** | [`screener_researcher.py:L123-128`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/tradingagents/agents/researchers/screener_researcher.py#L123-L128) | **Fragile JSON Extraction**: Naive `startswith("```json")` drops LLM completions with conversational preambles. | **HIGH** | Silently aborts valid LLM completions and triggers fallback. |
| **13** | [`screener_researcher.py:L156-165`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/tradingagents/agents/researchers/screener_researcher.py#L156-L165) | **Zero Banking / BFSI Support**: Searches only for `"Sales"`. Banks report `"Interest Earned"`. | **HIGH** | Causes banks and NBFCs to default to 300 Cr revenue. |
| **14** | [`report_docx.py:L554-558`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/tradingagents/report_docx.py#L554-L558) | **Permanent Bullish Recommendation Bias**: Always initiates coverage with an "optimistic outlook"; cannot issue SELL/REDUCE. | **HIGH** | Violates institutional research neutrality. |
| **15** | [`report_docx.py:L538-551`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/tradingagents/report_docx.py#L538-L551) | **Empty Percentage Rendering**: Prints `10 Years: %` into Word document when company history is less than 10 years. | **MEDIUM** | Unprofessional formatting in Section 10 table. |
| **16** | [`client.py:L254-257`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/tradingagents/dataflows/vendors/screener/client.py#L254-L257) | **Tooltip Text Contaminating Metric Names**: `td.get_text()` pulls tooltip definitions (e.g. `'CFO/EBITDAShare of operating profit...'`). | **MEDIUM** | Distorted row labels in Cash Flow and Ratios tables. |
| **17** | [`report_docx.py:L705-709`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/tradingagents/report_docx.py#L705-L709) | **Hardcoded Margin Levers**: Static text `"+ In-House Sub-Assemblies: +120 bps"` rendered for all companies. | **MEDIUM** | Irrelevant and misleading for IT, BFSI, and service companies. |
| **18** | [`client.py:L135-150`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/tradingagents/dataflows/vendors/screener/client.py#L135-L150) | **Binary PDF Parsing with BeautifulSoup**: Passes raw PDF bytes to HTML parser when transcripts are PDF links. | **MEDIUM** | Pollutes LLM context with binary gibberish. |
| **19** | [`client.py:L114-123`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/tradingagents/dataflows/vendors/screener/client.py#L114-L123) | **Lack of Consolidated View Enforcement**: Does not verify if `[Consolidated]` toggle is active for holding companies. | **MEDIUM** | Scrapes parent standalone financials for multi-subsidiary conglomerates. |
| **20** | [`report_docx.py:L134-169`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/tradingagents/report_docx.py#L134-L169) | **Column Squishing on 10+ Year Tables**: 13 columns in portrait layout (6.9" width) causes cells to shrink to 0.45", wrapping numbers. | **MEDIUM** | Distorted table typography in printed documents. |
| **21** | [`client.py:L326-330`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/tradingagents/dataflows/vendors/screener/client.py#L326-L330) | **Duplicate Announcements without Dates**: `"bse" in href` matches both concalls and announcements; lacks chronological sorting. | **MEDIUM** | Announcements cannot be ordered chronologically. |
| **22** | [`report_docx.py:L781`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/tradingagents/report_docx.py#L781) | **Double-Negative Downside Typography**: `f"-{downside_pct}%"` renders `--10%` if downside is already signed. | **LOW** | Minor typographical defect in Updated Thesis risk box. |
| **23** | [`screener_researcher.py:L287`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/tradingagents/agents/researchers/screener_researcher.py#L287) | **Dangling NSE Code on BSE-Only Stocks**: Outputs `- **BSE**: 544310 \| **NSE**: ` with empty value. | **LOW** | Dangling markdown bullet point on BSE SME stocks. |
| **24** | [`client.py:L72-78`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/tradingagents/dataflows/vendors/screener/client.py#L72-L78) | **Unhandled 404 on Free-Text Inputs**: `normalize_url("Tata Motors")` creates invalid URL `/company/Tata Motors/`. | **LOW** | Crashes with unhandled scrape exception instead of suggesting ticker code. |

---

## Phase 4 — Detailed Remediation Specifications

### Fix 1: Resolve Financial Table Column Shift & TTM Truncation
In [`tradingagents/report_docx.py`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/tradingagents/report_docx.py#L833-L851):
```python
headers = table_dict.get("Headers") or []
row_keys = [k for k in table_dict if k != "Headers"]

# Allocate 1 column for Metric Name + len(headers) columns for dates
num_cols = len(headers) + 1 if headers else (len(table_dict[row_keys[0]]) + 1 if row_keys else 2)
tab = doc.add_table(rows=1, cols=num_cols)

# Header Row: Cell 0 is "Metric", remaining cells are the dates
tab.rows[0].cells[0].text = "Metric"
if headers:
    for i, h in enumerate(headers):
        if i + 1 < num_cols:
            tab.rows[0].cells[i + 1].text = str(h)

# Body Rows: Cell 0 is row_name, remaining cells are row values
for k in row_keys:
    r = tab.add_row()
    r.cells[0].text = k
    vals = table_dict[k]
    for i, v in enumerate(vals):
        if i + 1 < num_cols:
            r.cells[i + 1].text = str(v)
```

### Fix 2: Preserve Negative Values and Handle Loss-Making Companies
In [`tradingagents/agents/researchers/screener_researcher.py`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/tradingagents/agents/researchers/screener_researcher.py):
```python
def _parse_signed_float(val: str, default: float = 0.0) -> float:
    """Safely parse floats while strictly preserving negative signs."""
    if not val:
        return default
    m = re.search(r"(-?\d+(?:\.\d+)?)", str(val).replace(",", ""))
    return float(m.group(1)) if m else default

# Preserve net losses and negative margins
ttm_pat = _parse_signed_float(pat_row[-1]) if pat_row else 10.0
opm_float = _parse_signed_float(current_opm, default=20.0)

# Native audited EPS lookup:
eps_row = data.profit_loss_table.get("EPS in Rs") or []
audited_eps = _parse_signed_float(eps_row[-1]) if eps_row else (cmp / max(pe, 1.0))
```

### Fix 3: Mathematically Derive Scenario Target Prices
In [`tradingagents/agents/researchers/screener_researcher.py`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/tradingagents/agents/researchers/screener_researcher.py#L172-L177):
```python
# Derive target prices mathematically from Forward PAT and Target Multiple:
fwd_pat_bull = ttm_pat * 3.0
fwd_pat_base = ttm_pat * 2.1
fwd_pat_bear = ttm_pat * 1.3

pe_bull = pe * 0.70
pe_base = pe * 0.55
pe_bear = pe * 0.40

mkt_cap_bull = fwd_pat_bull * pe_bull
mkt_cap_base = fwd_pat_base * pe_base
mkt_cap_bear = fwd_pat_bear * pe_bear

# Derive share count from CMP and Market Cap:
share_count = (mkt_cap_num / cmp) if (cmp > 0 and mkt_cap_num > 0) else 1.0

target_bull = f"Rs. {round(mkt_cap_bull / share_count, 1):,}"
target_base = f"Rs. {round(mkt_cap_base / share_count, 1):,}"
target_bear = f"Rs. {round(mkt_cap_bear / share_count, 1):,}"
```

### Fix 4: Parse Balance Sheet Borrowings & Net Debt
In [`tradingagents/agents/researchers/screener_researcher.py`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/tradingagents/agents/researchers/screener_researcher.py):
```python
borrowings_row = data.balance_sheet_table.get("Borrowings") or data.balance_sheet_table.get("Borrowings+") or []
borrowings_val = _parse_signed_float(borrowings_row[-1]) if borrowings_row else 0.0

if borrowings_val > (mkt_cap_num * 0.5):
    leverage_desc = f"Elevated debt load of Rs. {int(borrowings_val):,} Cr poses refinancing and interest coverage risks."
else:
    leverage_desc = "Prudent gearing and self-funded cash generation insulate the balance sheet."
```

### Fix 5: Normalized Fuzzy Lookup for Peer Table
In [`tradingagents/report_docx.py`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/tradingagents/report_docx.py#L355-L366):
```python
def _find_peer_val(peer_dict: dict[str, str], *candidate_keys: str) -> str:
    clean_dict = {re.sub(r"[^a-z0-9]", "", k.lower()): v for k, v in peer_dict.items()}
    for ck in candidate_keys:
        norm = re.sub(r"[^a-z0-9]", "", ck.lower())
        if norm in clean_dict:
            return clean_dict[norm]
    return ""

name = _find_peer_val(peer, "Company", "Name")
cmp_p = _find_peer_val(peer, "CMPRs.", "CMP", "Current Price")
pe_p = _find_peer_val(peer, "P/E", "Stock P/E")
mcap_p = _find_peer_val(peer, "Mar CapRs.Cr.", "Mar Cap", "Market Cap")
roce_p = _find_peer_val(peer, "ROCE%", "ROCE")
div_p = _find_peer_val(peer, "Div Yld%", "Div Yld")
```

### Fix 6: Missing Market Cap Unit in Updated Thesis
In [`tradingagents/report_docx.py:L646`](file:///c:/Users/CM_Rail/PycharmProjects/TradingAgents/tradingagents/report_docx.py#L646):
```python
# Before:
f"Rs. {company_data.get('market_cap', 'N/A')}",

# After:
f"Rs. {company_data.get('market_cap', 'N/A')} Cr",
```
