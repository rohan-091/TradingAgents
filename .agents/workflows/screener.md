---
name: screener
description: Generate complete Equity Research Report and Updated Thesis (.docx) from any Screener.in company URL using browser automation and advanced Gemini.
---

# Workflow: Screener.in Equity Research

Generate two institutional Word documents (`.docx`) from any Indian company's Screener.in profile:

1. **Run via CLI**:
   ```bash
   python scripts/run_screener_research.py --url https://www.screener.in/company/{CODE}/ --model gemini-3.8-flash
   ```

2. **Run programmatically**:
   ```python
   from tradingagents.agents import create_screener_equity_researcher
   from tradingagents.llm_clients.factory import create_llm_client

   llm = create_llm_client("google", "gemini-3.8-flash").get_llm()
   researcher = create_screener_equity_researcher(llm=llm, output_dir="./reports")
   result = researcher("https://www.screener.in/company/500570/")
   print(result.equity_report_path, result.thesis_doc_path)
   ```

3. **Outputs Generated**:
   - `{Company_Name}_Equity_Research_Report.docx`
   - `{Company_Name}_Updated_Thesis.docx`
