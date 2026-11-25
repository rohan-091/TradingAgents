#!/usr/bin/env python3
"""Hourly Status Monitor & Risk Watchdog for TradingAgents (Indian Equities & OpenAlgo).

Checks every hour:
1. OpenAlgo Gateway health on http://127.0.0.1:5000
2. Live funds, cash reserve, and Golden Rule compliance (Cash >= 99.75%, Exposure <= 0.25%)
3. Active positions with real-time LTP, P&L, and distance to Take-Profit (+8%) & Stop-Loss (-3%)
4. Optional automated exit execution if any position breaches TP or SL boundaries
5. Appends snapshot to results/hourly_monitor.log and outputs Markdown summary
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

import yfinance as yf
from tradingagents.execution.exit_manager import PositionExitManager
from tradingagents.execution.openalgo_client import OpenAlgoClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("HourlyMonitor")


def run_hourly_check(
    portfolio_path: str = "portfolio_inr.json",
    results_dir: str = "results",
    auto_exit: bool = True,
    take_profit_pct: float = 8.0,
    stop_loss_pct: float = 3.0,
) -> dict[str, Any]:
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    client = OpenAlgoClient()
    openalgo_online = client.ping()

    res_dir = Path(results_dir)
    res_dir.mkdir(parents=True, exist_ok=True)
    log_file = res_dir / "hourly_monitor.log"

    # Step 1: Query Funds & Open Positions
    live_funds: dict[str, Any] = {}
    live_positions: list[dict[str, Any]] = []

    if openalgo_online:
        live_funds = client.get_funds()
        live_positions = client.get_positions()
        available_cash = float(live_funds.get("availablecash", 0.0))
        utilised_debits = float(live_funds.get("utiliseddebits", 0.0))
        total_pnl = float(live_funds.get("totalpnl", 0.0))
    else:
        # Fallback to local portfolio ledger if OpenAlgo gateway is offline
        p_path = Path(portfolio_path)
        if p_path.exists():
            with open(p_path, "r", encoding="utf-8") as f:
                p_data = json.load(f)
            available_cash = float(p_data.get("cash", 20000000.0))
            live_positions = p_data.get("positions", [])
        else:
            available_cash = 20000000.0
        utilised_debits = sum(
            float(p.get("quantity", 0.0)) * float(p.get("average_price", 0.0)) for p in live_positions
        )
        total_pnl = 0.0

    # Step 2: Position Analysis with Live LTP
    analyzed_positions: list[dict[str, Any]] = []
    current_market_value = 0.0
    exit_alerts: list[str] = []

    for p in live_positions:
        ticker = p.get("ticker", "")
        if not ticker and "symbol" in p:
            ticker = f"{p['symbol']}.NS"
        qty = float(p.get("quantity", 0.0))
        avg_price = float(p.get("average_price", 0.0))

        # Get LTP
        ltp = float(p.get("ltp", avg_price))
        if ltp <= 0 or ltp == avg_price:
            try:
                t = yf.Ticker(ticker)
                h = t.history(period="1d")
                if not h.empty:
                    ltp = float(h["Close"].iloc[-1])
            except Exception:
                ltp = avg_price

        position_val = qty * ltp
        current_market_value += position_val

        ret_pct = ((ltp - avg_price) / avg_price * 100.0) if avg_price > 0 else 0.0
        unrealized_pnl = (ltp - avg_price) * qty

        tp_price = round(avg_price * (1.0 + (take_profit_pct / 100.0)), 2)
        sl_price = round(avg_price * (1.0 - (stop_loss_pct / 100.0)), 2)
        dist_to_tp = ((tp_price - ltp) / ltp) * 100.0
        dist_to_sl = ((ltp - sl_price) / ltp) * 100.0

        status = "NORMAL"
        if ret_pct >= take_profit_pct:
            status = "TAKE_PROFIT_TRIGGERED"
            exit_alerts.append(f"🎯 {ticker} hit TP (+{ret_pct:.2f}% >= +{take_profit_pct}%)")
        elif ret_pct <= -stop_loss_pct:
            status = "STOP_LOSS_TRIGGERED"
            exit_alerts.append(f"🛑 {ticker} hit SL ({ret_pct:.2f}% <= -{stop_loss_pct}%)")

        analyzed_positions.append({
            "ticker": ticker,
            "quantity": qty,
            "average_price": round(avg_price, 2),
            "ltp": round(ltp, 2),
            "current_value": round(position_val, 2),
            "return_pct": round(ret_pct, 2),
            "unrealized_pnl": round(unrealized_pnl, 2),
            "target_price": tp_price,
            "stop_loss": sl_price,
            "distance_to_tp_pct": round(dist_to_tp, 2),
            "distance_to_sl_pct": round(dist_to_sl, 2),
            "status": status,
        })

    # Step 3: Golden Rule Calculations
    total_capital = available_cash + current_market_value
    if total_capital <= 0:
        total_capital = 20000000.0

    exposure_pct = (current_market_value / total_capital) * 100.0
    cash_pct = (available_cash / total_capital) * 100.0
    golden_rule_exposure_ok = exposure_pct <= 0.25
    golden_rule_cash_ok = cash_pct >= 99.75

    # Step 4: Optional Auto-Exit Execution
    exited_trades: list[dict[str, Any]] = []
    if auto_exit and exit_alerts:
        logger.info(f"Triggering Exit Manager for alerts: {exit_alerts}")
        exit_mgr = PositionExitManager(
            portfolio_path=portfolio_path,
            take_profit_pct=take_profit_pct,
            stop_loss_pct=stop_loss_pct,
            openalgo_client=client,
        )
        actions = exit_mgr.evaluate_and_exit_positions()
        for act in actions:
            if act.action in ("SELL_TP", "SELL_SL"):
                exited_trades.append(act.to_dict())

    # Step 5: Log Snapshot
    snapshot = {
        "timestamp": now_str,
        "openalgo_status": "ONLINE" if openalgo_online else "OFFLINE",
        "total_capital": round(total_capital, 2),
        "available_cash": round(available_cash, 2),
        "market_exposure": round(current_market_value, 2),
        "exposure_pct": round(exposure_pct, 3),
        "cash_pct": round(cash_pct, 3),
        "golden_rule_exposure_ok": golden_rule_exposure_ok,
        "golden_rule_cash_ok": golden_rule_cash_ok,
        "active_positions_count": len(analyzed_positions),
        "positions": analyzed_positions,
        "exit_alerts": exit_alerts,
        "exited_trades": exited_trades,
    }

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(snapshot) + "\n")

    return snapshot


def format_markdown_summary(snapshot: dict[str, Any]) -> str:
    lines = [
        f"### 🕒 Hourly Trading Status Check ({snapshot['timestamp']})",
        "",
        f"- **OpenAlgo Gateway:** `{'🟢 ONLINE' if snapshot['openalgo_status'] == 'ONLINE' else '🔴 OFFLINE'}` (port 5000)",
        f"- **Total Capital:** ₹{snapshot['total_capital']:,.2f} INR",
        f"- **Available Cash:** ₹{snapshot['available_cash']:,.2f} INR (**{snapshot['cash_pct']:.2f}%** | Min 99.75% {'✅' if snapshot['golden_rule_cash_ok'] else '⚠️'})",
        f"- **Gross Market Exposure:** ₹{snapshot['market_exposure']:,.2f} INR (**{snapshot['exposure_pct']:.2f}%** | Max 0.25% {'✅' if snapshot['golden_rule_exposure_ok'] else '⚠️'})",
        f"- **Active Positions:** {snapshot['active_positions_count']}",
        "",
    ]

    positions = snapshot.get("positions", [])
    if not positions:
        lines.append("*No open positions currently held.*")
    else:
        lines.append("| Ticker | Qty | Avg Buy | LTP | Value | P&L % | Unrealized P&L | Target (+8%) | Stop (-3%) | Status |")
        lines.append("|---|---|---|---|---|---|---|---|---|---|")
        for p in positions:
            pnl_sign = "+" if p["unrealized_pnl"] >= 0 else ""
            ret_sign = "+" if p["return_pct"] >= 0 else ""
            lines.append(
                f"| `{p['ticker']}` | {int(p['quantity'])} | ₹{p['average_price']:,.2f} | ₹{p['ltp']:,.2f} | "
                f"₹{p['current_value']:,.2f} | {ret_sign}{p['return_pct']:.2f}% | ₹{pnl_sign}{p['unrealized_pnl']:,.2f} | "
                f"₹{p['target_price']:,.2f} | ₹{p['stop_loss']:,.2f} | `{p['status']}` |"
            )

    if snapshot.get("exit_alerts"):
        lines.append("")
        lines.append("#### 🚨 Risk Alerts & Actions:")
        for alert in snapshot["exit_alerts"]:
            lines.append(f"- {alert}")

    if snapshot.get("exited_trades"):
        lines.append("")
        lines.append("#### 📤 Auto-Executed Exits:")
        for ex in snapshot["exited_trades"]:
            lines.append(f"- **{ex['ticker']}**: {ex['action']} at ₹{ex['current_price']} (P&L: ₹{ex['realized_pnl']:+,.2f})")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Hourly Status Monitor for Indian Equities Paper Trading")
    parser.add_argument("--portfolio", default="portfolio_inr.json", help="Path to portfolio ledger")
    parser.add_argument("--results-dir", default="results", help="Directory for hourly logs")
    parser.add_argument("--no-auto-exit", action="store_true", help="Disable automatic exit order execution")
    parser.add_argument("--tp", type=float, default=8.0, help="Take-profit percentage")
    parser.add_argument("--sl", type=float, default=3.0, help="Stop-loss percentage")

    args = parser.parse_args()
    snapshot = run_hourly_check(
        portfolio_path=args.portfolio,
        results_dir=args.results_dir,
        auto_exit=not args.no_auto_exit,
        take_profit_pct=args.tp,
        stop_loss_pct=args.sl,
    )
    print("\n" + format_markdown_summary(snapshot))


if __name__ == "__main__":
    main()
