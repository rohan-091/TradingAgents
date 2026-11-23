---
name: screener-equity-research
description: Use when generating institutional Equity Research Reports and Updated Investment Thesis Word documents (.docx) from any Screener.in company profile. Requires browser access to parse tables, concall transcripts, annual reports, and announcements.
---

# Screener.in Equity Research Skill

## Overview
Automates institutional coverage initiation and updated thesis generation from any company profile on [Screener.in](https://www.screener.in/). Employs browser automation (Playwright or headless HTTP) to extract all primary financial statements and deep-read secondary documents (concalls, PPTs, annual reports) to audit management delivery and reverse-engineer valuation pricing.

## Workflow

1. **Extraction**:
   - Navigate to `https://www.screener.in/company/{BSE_CODE}/` or `{TICKER}`.
   - Extract header metrics, peer comparisons, quarterly and annual P&L, balance sheets, cash flows, ratios, shareholding, and pros/cons.
   - Access `#documents` to collect and read concall transcripts, investor presentations, annual reports, and material corporate announcements.

2. **Forensic Analysis**:
   - Construct the chronological **Management Promise Tracker** (Promise made, date, target, deadline, actual outcome, verdict).
   - Compute the **Management Credibility Score**.
   - Execute the **"What's Priced In vs. What's Not"** framework (market implied growth rate, 5-6 priced in, 5-6 unpriced catalysts).
   - Run the **Munger Inversion** ("Invert, Always Invert" across 6-7 failure paths with probability weights).
   - Formulate 3-year forward valuation scenarios (Bull, Base, Bear) and forward P/E walk-down.

3. **Deliverable Generation**:
   Execute the automated document generator:
   ```bash
   python scripts/run_screener_research.py --url https://www.screener.in/company/{CODE}/ --model gemini-3.8-flash
   ```
   Outputs:
   - `{Company_Name}_Equity_Research_Report.docx`
   - `{Company_Name}_Updated_Thesis.docx`
