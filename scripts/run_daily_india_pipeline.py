#!/usr/bin/env python3
"""Daily Automated Pre-Market Pipeline for Indian Equities Paper Trading.

Workflow:
1. Portfolio Health & Risk Exits (+8% Take Profit, -3% Stop Loss)
2. Quantitative Funnel Screening (Watchlist -> Top 3 Candidates)
3. Multi-Agent Trade Selection & Position Allocation
4. Dual Execution (OpenAlgo AMO + portfolio_inr.json Ledger)
5. Comprehensive Daily Markdown & HTML Reporting
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.filter_india_top3 import CandidateScore, get_top_candidates
from tradingagents.execution.exit_manager import ExitActionResult, PositionExitManager
from tradingagents.execution.openalgo_client import OpenAlgoClient, parse_symbol_and_exchange

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DailyIndiaPipeline")


def generate_reports(
    date_str: str,
    exits: list[ExitActionResult],
    top3: list[CandidateScore],
    new_buys: list[dict[str, Any]],
    portfolio_state: dict[str, Any],
    output_dir: Path,
) -> tuple[Path, Path]:
    """Generate Markdown and HTML daily summary reports."""
    output_dir.mkdir(parents=True, exist_ok=True)
    md_file = output_dir / f"daily_summary_{date_str}.md"
    html_file = output_dir / f"daily_summary_{date_str}.html"

    # Build Markdown Content
    lines = [
        f"# Daily Paper Trading Summary - {date_str} (NSE/BSE)",
        "",
        "## 1. Portfolio Health & Morning Risk Exits",
    ]

    if not exits:
        lines.append("- *No open positions required liquidation today.*")
    else:
        lines.append("| Ticker | Entry | Exit | Return % | Realized P&L (INR) | Action |")
        lines.append("|---|---|---|---|---|---|")
        for e in exits:
            lines.append(
                f"| `{e.ticker}` | ₹{e.entry_price:,.2f} | ₹{e.current_price:,.2f} | {e.return_pct:+.2f}% | ₹{e.realized_pnl:+,.2f} | **{e.action}** |"
            )

    lines.extend([
        "",
        "## 2. Quantitative Funnel Screening (Top 3 Candidates)",
        "",
        "| Rank | Ticker | Company | Price (INR) | Score | RSI | ROCE % | P/E | Key Signals |",
        "|---|---|---|---|---|---|---|---|---|",
    ])
    for idx, c in enumerate(top3, 1):
        roce_s = f"{c.roce:.1f}%" if c.roce is not None else "N/A"
        pe_s = f"{c.stock_pe:.1f}" if c.stock_pe is not None else "N/A"
        sigs = "; ".join(c.rationale)
        lines.append(
            f"| #{idx} | `{c.ticker}` | {c.company_name} | ₹{c.current_price:,.2f} | {c.total_score:.1f}/100 | {c.rsi} | {roce_s} | {pe_s} | {sigs} |"
        )

    lines.extend([
        "",
        "## 3. Dispatched Pre-Market Orders (AMO / OpenAlgo)",
        "",
    ])
    if not new_buys:
        lines.append("- *No new positions opened today (cash limits or risk criteria).*")
    else:
        lines.append("| Ticker | Exchange | Action | Qty | Order Type | Target Price | Stop Loss | OpenAlgo Status |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for b in new_buys:
            order_res = b.get("order_res", {})
            status_text = order_res.get("status", "dispatched")
            lines.append(
                f"| `{b['ticker']}` | {b['exchange']} | **{b['action']}** | {b['quantity']} | AMO CNC | ₹{b['target_price']:,.2f} | ₹{b['stop_loss']:,.2f} | `{status_text}` |"
            )

    cash = portfolio_state.get("cash", 0.0)
    positions = portfolio_state.get("positions", [])
    lines.extend([
        "",
        "## 4. Current Ledger Balance",
        "",
        f"- **Available Cash:** ₹{cash:,.2f} INR",
        f"- **Active Positions:** {len(positions)}",
    ])
    if positions:
        for p in positions:
            lines.append(
                f"  - `{p['ticker']}`: {p['quantity']} units @ ₹{p.get('average_price', 0.0):,.2f}"
            )

    md_content = "\n".join(lines) + "\n"
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(md_content)

    # Basic HTML version
    html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Daily Summary - {date_str}</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 40px; background: #0f172a; color: #f8fafc; }}
h1, h2 {{ color: #38bdf8; }}
table {{ border-collapse: collapse; width: 100%; margin: 20px 0; background: #1e293b; border-radius: 8px; overflow: hidden; }}
th, td {{ padding: 12px 16px; text-align: left; border-bottom: 1px solid #334155; }}
th {{ background: #0284c7; color: white; }}
tr:hover {{ background: #334155; }}
code {{ background: #0f172a; padding: 2px 6px; border-radius: 4px; color: #38bdf8; }}
</style>
</head>
<body>
<h1>Daily Paper Trading Summary - {date_str} (NSE/BSE)</h1>
<h2>Portfolio Cash: Rs. {cash:,.2f} | Open Positions: {len(positions)}</h2>
<pre style="background: #1e293b; padding: 20px; border-radius: 8px; white-space: pre-wrap;">{md_content}</pre>
</body>
</html>
"""
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    return md_file, html_file


def run_pipeline(
    watchlist_path: str = "watchlist_india.json",
    portfolio_path: str = "portfolio_inr.json",
    results_dir: str = "results",
) -> dict[str, Any]:
    """Execute the daily end-to-end paper trading pipeline."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    logger.info(f"=== Starting Daily Indian Paper Trading Pipeline: {date_str} ===")

    # Load configuration
    with open(watchlist_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    allocation_per_trade = float(config.get("allocation_per_trade_inr", 50000.0))
    max_positions = int(config.get("max_open_positions", 5))
    take_profit_pct = float(config.get("take_profit_pct", 8.0))
    stop_loss_pct = float(config.get("stop_loss_pct", 3.0))

    openalgo_client = OpenAlgoClient()
    openalgo_online = openalgo_client.ping()
    logger.info(f"OpenAlgo connection on port 5000: {'ONLINE (zerodha)' if openalgo_online else 'OFFLINE (simulating)'}")

    # Step 1: Evaluate & Exit Existing Positions
    logger.info("Step 1: Running Portfolio Health & Exit Manager (+8% TP, -3% SL)...")
    exit_manager = PositionExitManager(
        portfolio_path=portfolio_path,
        take_profit_pct=take_profit_pct,
        stop_loss_pct=stop_loss_pct,
        openalgo_client=openalgo_client,
    )
    exits = exit_manager.evaluate_and_exit_positions()
    if exits:
        for e in exits:
            logger.info(f"Position evaluated: {e.ticker} -> {e.action} (return: {e.return_pct:+.2f}%)")

    # Step 2: Screen Watchlist down to Top 3 Candidates
    logger.info("Step 2: Scoring Watchlist and Selecting Top 3 Candidates...")
    top3 = get_top_candidates(watchlist_path=watchlist_path, top_n=3)
    for idx, c in enumerate(top3, 1):
        logger.info(f"Top Candidate #{idx}: {c.ticker} ({c.company_name}) - Score: {c.total_score}")

    # Step 3: Multi-Agent Trade Decision & Order Execution
    logger.info("Step 3: Determining New Trade Allocations...")
    portfolio = exit_manager.load_portfolio()
    cash = float(portfolio.get("cash", 0.0))
    active_positions = portfolio.get("positions", [])
    held_tickers = {p["ticker"].upper() for p in active_positions}

    new_buys: list[dict[str, Any]] = []

    for candidate in top3:
        # Check if already held
        if candidate.ticker.upper() in held_tickers:
            logger.info(f"Skipping {candidate.ticker}: Already held in portfolio.")
            continue

        # Check max open positions
        if len(active_positions) >= max_positions:
            logger.info(f"Maximum open positions ({max_positions}) reached. No new trades.")
            break

        # Check cash availability
        if cash < allocation_per_trade * 0.8:
            logger.info(f"Insufficient cash (Rs. {cash:,.2f}) for new allocation. Skipping {candidate.ticker}.")
            break

        # High-conviction threshold: Score >= 70
        if candidate.total_score >= 70.0 and candidate.current_price > 0:
            qty = max(1, int(allocation_per_trade / candidate.current_price))
            sym, exch = parse_symbol_and_exchange(candidate.ticker)
            target_price = round(candidate.current_price * (1.0 + (take_profit_pct / 100.0)), 2)
            stop_loss = round(candidate.current_price * (1.0 - (stop_loss_pct / 100.0)), 2)

            logger.info(f"Dispatching AMO BUY order for {candidate.ticker}: qty={qty} @ Rs. {candidate.current_price:,.2f}")
            order_res = openalgo_client.place_order(
                symbol=sym,
                exchange=exch,
                action="BUY",
                quantity=qty,
                pricetype="MARKET",
                product="CNC",
                strategy="TradingAgents-Daily",
            )

            # Update local ledger
            trade_cost = qty * candidate.current_price
            cash -= trade_cost
            new_pos = {
                "ticker": candidate.ticker,
                "quantity": float(qty),
                "average_price": candidate.current_price,
            }
            active_positions.append(new_pos)
            held_tickers.add(candidate.ticker.upper())

            new_buys.append({
                "ticker": candidate.ticker,
                "exchange": exch,
                "action": "BUY",
                "quantity": qty,
                "price": candidate.current_price,
                "target_price": target_price,
                "stop_loss": stop_loss,
                "order_res": order_res,
            })

    # Save final portfolio state
    portfolio["cash"] = round(cash, 2)
    portfolio["positions"] = active_positions
    exit_manager.save_portfolio(portfolio)

    # Step 4: Generate Reports
    md_file, html_file = generate_reports(
        date_str=date_str,
        exits=exits,
        top3=top3,
        new_buys=new_buys,
        portfolio_state=portfolio,
        output_dir=Path(results_dir),
    )
    logger.info(f"Saved daily markdown report: {md_file}")
    logger.info(f"Saved daily HTML report: {html_file}")

    return {
        "date": date_str,
        "exits": [e.to_dict() for e in exits],
        "top3": [c.to_dict() for c in top3],
        "new_buys": new_buys,
        "portfolio": portfolio,
        "report_md": str(md_file),
        "report_html": str(html_file),
    }


if __name__ == "__main__":
    import sys

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Run Daily Indian Paper Trading Pipeline")
    parser.add_argument("--watchlist", default="watchlist_india.json", help="Path to watchlist JSON")
    parser.add_argument("--portfolio", default="portfolio_inr.json", help="Path to portfolio ledger JSON")
    parser.add_argument("--results-dir", default="results", help="Directory for daily reports")

    args = parser.parse_args()
    summary = run_pipeline(
        watchlist_path=args.watchlist,
        portfolio_path=args.portfolio,
        results_dir=args.results_dir,
    )
    print("\n" + "=" * 60)
    print("DAILY INDIAN PAPER TRADING PIPELINE COMPLETE")
    print(f"Report: {summary['report_md']}")
    print(f"HTML:   {summary['report_html']}")
    print("=" * 60)
