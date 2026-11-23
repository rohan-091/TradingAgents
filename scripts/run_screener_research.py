#!/usr/bin/env python3
"""CLI script to run browser-based Equity Research on any company from Screener.in."""

import argparse
import os
import sys

# Configure UTF-8 encoding for Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from tradingagents.agents.researchers.screener_researcher import create_screener_equity_researcher
from tradingagents.llm_clients.factory import create_llm_client


def main():
    parser = argparse.ArgumentParser(
        description="Generate Equity Research Report & Updated Thesis (.md) from Screener.in"
    )
    parser.add_argument(
        "--url",
        "-u",
        required=True,
        help="Screener.in company URL (e.g. https://www.screener.in/company/500570/) or ticker symbol/BSE code",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        default="./results",
        help="Base directory to save generated .md reports adhering to repo structure (default: ./results)",
    )
    parser.add_argument(
        "--model",
        "-m",
        default="gemini-3.8-flash",
        help="Gemini model name (default: gemini-3.8-flash)",
    )
    parser.add_argument(
        "--provider",
        "-p",
        default="google",
        help="LLM provider (default: google)",
    )
    parser.add_argument(
        "--no-playwright",
        action="store_true",
        help="Disable Playwright and use direct HTTP requests",
    )

    args = parser.parse_args()

    llm = None
    if os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"):
        try:
            client = create_llm_client(provider=args.provider, model=args.model)
            llm = client.get_llm()
            print(f"[OK] Initialized {args.provider} LLM: {args.model}")
        except Exception as e:
            print(f"[Notice] Could not initialize {args.provider} LLM ({e}). Running in deterministic financial modeling mode.")
    else:
        print("[Notice] GEMINI_API_KEY / GOOGLE_API_KEY not found in environment. Running in deterministic financial modeling mode.")

    researcher = create_screener_equity_researcher(
        llm=llm,
        output_dir=args.output_dir,
        use_playwright=not args.no_playwright,
    )

    print(f">> Navigating to Screener.in ({args.url}) with browser automation...")
    result = researcher(args.url)

    print("\n" + "=" * 60)
    print("[SUCCESS] Research Completed Successfully!")
    print(f"• Equity Research Report: {result.equity_report_path}")
    print(f"• Updated Investment Thesis: {result.thesis_doc_path}")
    print(f"• Consolidated Master Report: {result.complete_report_path}")
    print("=" * 60)
    print(result.markdown_report)


if __name__ == "__main__":
    main()
