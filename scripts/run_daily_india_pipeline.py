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
    golden_rule_metrics: dict[str, Any],
    output_dir: Path,
) -> tuple[Path, Path]:
    """Generate Markdown and HTML daily summary reports."""
    output_dir.mkdir(parents=True, exist_ok=True)
    md_file = output_dir / f"daily_summary_{date_str}.md"
    html_file = output_dir / f"daily_summary_{date_str}.html"

    total_cap = golden_rule_metrics.get("total_capital", 20000000.0)
    cur_exp = golden_rule_metrics.get("current_exposure", 0.0)
    exp_pct = (cur_exp / total_cap * 100.0) if total_cap > 0 else 0.0
    max_order_pct = golden_rule_metrics.get("max_order_pct", 0.05)
    max_exposure_pct = golden_rule_metrics.get("max_exposure_pct", 0.25)
    max_exp = golden_rule_metrics.get("max_exposure_inr", total_cap * (max_exposure_pct / 100.0))
    max_ord = golden_rule_metrics.get("max_per_order_inr", total_cap * (max_order_pct / 100.0))

    # Build Markdown Content
    lines = [
        f"# Daily Paper Trading Summary - {date_str} (NSE/BSE)",
        "",
        "## 🛡️ Risk Management & Golden Rule Status",
        f"- **Total Capital:** ₹{total_cap:,.2f} INR",
        f"- **Golden Rule 1 (Per-Order Cap):** Max {max_order_pct}% (₹{max_ord:,.2f} INR per trade)",
        f"- **Golden Rule 2 (Gross Exposure Cap):** Max {max_exposure_pct}% (₹{max_exp:,.2f} INR total in market)",
        f"- **Current Market Exposure:** ₹{cur_exp:,.2f} INR (**{exp_pct:.2f}%** of capital)",
        f"- **Safe Cash & Reserves:** ₹{portfolio_state.get('cash', 0.0):,.2f} INR ({(portfolio_state.get('cash', 0.0)/total_cap)*100:.2f}%)",
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

    max_order_pct = float(config.get("max_order_capital_pct", 0.05))
    max_exposure_pct = float(config.get("max_market_exposure_pct", 0.25))
    max_positions = int(config.get("max_open_positions", 5))
    take_profit_pct = float(config.get("take_profit_pct", 8.0))
    stop_loss_pct = float(config.get("stop_loss_pct", 3.0))

    openalgo_client = OpenAlgoClient()
    openalgo_online = openalgo_client.ping()
    logger.info(f"OpenAlgo connection on port 5000: {'ONLINE (zerodha)' if openalgo_online else 'OFFLINE (simulating)'}")

    # Synchronize portfolio ledger directly from OpenAlgo if online
    exit_manager = PositionExitManager(
        portfolio_path=portfolio_path,
        take_profit_pct=take_profit_pct,
        stop_loss_pct=stop_loss_pct,
        openalgo_client=openalgo_client,
    )

    if openalgo_online:
        live_funds = openalgo_client.get_funds()
        live_positions = openalgo_client.get_positions()
        logger.info(
            f"Synced live OpenAlgo ledger: Cash=Rs. {live_funds['availablecash']:,.2f} | Open Positions={len(live_positions)}"
        )
        synced_portfolio = {
            "cash": live_funds["availablecash"],
            "currency": "INR",
            "positions": [
                {
                    "ticker": p["ticker"],
                    "quantity": p["quantity"],
                    "average_price": p["average_price"],
                }
                for p in live_positions
            ],
        }
        exit_manager.save_portfolio(synced_portfolio)

    # Step 1: Evaluate & Exit Existing Positions
    logger.info("Step 1: Running Portfolio Health & Exit Manager (+8% TP, -3% SL)...")
    exits = exit_manager.evaluate_and_exit_positions()
    if exits:
        for e in exits:
            logger.info(f"Position evaluated: {e.ticker} -> {e.action} (return: {e.return_pct:+.2f}%)")

    # Step 2: Screen Watchlist down to Top 3 Candidates
    logger.info("Step 2: Scoring Watchlist and Selecting Top 3 Candidates...")
    top3 = get_top_candidates(watchlist_path=watchlist_path, top_n=3)
    for idx, c in enumerate(top3, 1):
        logger.info(f"Top Candidate #{idx}: {c.ticker} ({c.company_name}) - Score: {c.total_score}")

    # Step 3: Multi-Agent Trade Decision & Order Execution with Golden Rule
    logger.info(f"Step 3: Determining New Trade Allocations with Golden Rule ({max_order_pct}% per order, {max_exposure_pct}% max exposure)...")
    portfolio = exit_manager.load_portfolio()
    cash = float(portfolio.get("cash", 0.0))
    active_positions = portfolio.get("positions", [])
    held_tickers = {p["ticker"].upper() for p in active_positions}

    # Golden Rule Calculations
    current_exposure = sum(float(p.get("quantity", 0.0)) * float(p.get("average_price", 0.0)) for p in active_positions)
    total_capital = cash + current_exposure
    if total_capital <= 0:
        total_capital = 20000000.0  # fallback to ₹2 Crore

    max_per_order_inr = total_capital * (max_order_pct / 100.0)
    max_exposure_inr = total_capital * (max_exposure_pct / 100.0)
    remaining_exposure_room = max(0.0, max_exposure_inr - current_exposure)

    logger.info(
        f"GOLDEN RULE: Total Capital=Rs. {total_capital:,.2f} | "
        f"Max Order ({max_order_pct}%)=Rs. {max_per_order_inr:,.2f} | "
        f"Max Gross Exposure ({max_exposure_pct}%)=Rs. {max_exposure_inr:,.2f} | "
        f"Current Exposure=Rs. {current_exposure:,.2f} ({(current_exposure/total_capital)*100:.2f}%) | "
        f"Remaining Room=Rs. {remaining_exposure_room:,.2f}"
    )

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

        # Check Golden Rule: Total Market Exposure Cap
        if remaining_exposure_room <= 0:
            logger.warning(
                f"GOLDEN RULE CAP: Market exposure limit of {max_exposure_pct}% (Rs. {max_exposure_inr:,.2f}) reached. "
                f"No new orders permitted until existing positions exit."
            )
            break

        # Sizing: Capped by per-order cap and remaining room under exposure cap
        order_budget = min(max_per_order_inr, remaining_exposure_room)
        if candidate.current_price <= 0:
            continue

        qty = int(order_budget / candidate.current_price)
        if qty <= 0:
            logger.info(
                f"Skipping {candidate.ticker}: Budget Rs. {order_budget:,.2f} insufficient for share price Rs. {candidate.current_price:,.2f}"
            )
            continue

        # High-conviction threshold: Score >= 70
        if candidate.total_score >= 70.0:
            sym, exch = parse_symbol_and_exchange(candidate.ticker)
            target_price = round(candidate.current_price * (1.0 + (take_profit_pct / 100.0)), 2)
            stop_loss = round(candidate.current_price * (1.0 - (stop_loss_pct / 100.0)), 2)
            trade_cost = qty * candidate.current_price

            logger.info(
                f"Dispatching AMO BUY order for {candidate.ticker}: qty={qty} @ Rs. {candidate.current_price:,.2f} "
                f"(Cost: Rs. {trade_cost:,.2f} <= Max Rs. {max_per_order_inr:,.2f})"
            )
            order_res = openalgo_client.place_order(
                symbol=sym,
                exchange=exch,
                action="BUY",
                quantity=qty,
                pricetype="MARKET",
                product="CNC",
                strategy="TradingAgents-Daily",
            )

            # Update local ledger and exposure accounting
            cash -= trade_cost
            current_exposure += trade_cost
            remaining_exposure_room = max(0.0, max_exposure_inr - current_exposure)

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
                "allocation_inr": round(trade_cost, 2),
                "capital_pct": round((trade_cost / total_capital) * 100.0, 3),
            })

    # Save final portfolio state
    portfolio["cash"] = round(cash, 2)
    portfolio["positions"] = active_positions
    exit_manager.save_portfolio(portfolio)

    # Step 4: Generate Reports
    golden_rule_metrics = {
        "total_capital": total_capital,
        "max_order_pct": max_order_pct,
        "max_exposure_pct": max_exposure_pct,
        "max_per_order_inr": max_per_order_inr,
        "max_exposure_inr": max_exposure_inr,
        "current_exposure": current_exposure,
        "remaining_exposure_room": remaining_exposure_room,
    }
    md_file, html_file = generate_reports(
        date_str=date_str,
        exits=exits,
        top3=top3,
        new_buys=new_buys,
        portfolio_state=portfolio,
        golden_rule_metrics=golden_rule_metrics,
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
