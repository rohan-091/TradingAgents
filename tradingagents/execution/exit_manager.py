"""Portfolio Position Lifecycle and Exit Manager for Indian Equities.

Enforces automated risk management rules on active positions:
- Take-Profit (+8% by default)
- Stop-Loss (-3% by default)
Routes exit sell orders via OpenAlgo and updates the local INR ledger.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yfinance as yf

from .openalgo_client import OpenAlgoClient, parse_symbol_and_exchange

logger = logging.getLogger(__name__)


@dataclass
class ExitActionResult:
    ticker: str
    quantity: float
    entry_price: float
    current_price: float
    return_pct: float
    action: str  # "SELL_TP", "SELL_SL", "HOLD"
    realized_pnl: float
    order_status: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PositionExitManager:
    """Manages active position checks, stop-loss, and take-profit enforcement."""

    def __init__(
        self,
        portfolio_path: str | Path = "portfolio_inr.json",
        take_profit_pct: float = 8.0,
        stop_loss_pct: float = 3.0,
        openalgo_client: OpenAlgoClient | None = None,
    ):
        self.portfolio_path = Path(portfolio_path)
        self.take_profit_pct = take_profit_pct
        self.stop_loss_pct = stop_loss_pct
        self.openalgo_client = openalgo_client or OpenAlgoClient()

    def load_portfolio(self) -> dict[str, Any]:
        if not self.portfolio_path.exists():
            return {"cash": 500000.0, "currency": "INR", "positions": []}
        with open(self.portfolio_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_portfolio(self, portfolio: dict[str, Any]) -> None:
        with open(self.portfolio_path, "w", encoding="utf-8") as f:
            json.dump(portfolio, f, indent=2)

    def evaluate_and_exit_positions(self) -> list[ExitActionResult]:
        """Check all active positions in the portfolio and exit those hitting TP or SL."""
        portfolio = self.load_portfolio()
        positions = portfolio.get("positions", [])
        if not positions:
            logger.info("No active positions to evaluate in portfolio.")
            return []

        remaining_positions: list[dict[str, Any]] = []
        action_results: list[ExitActionResult] = []
        cash = float(portfolio.get("cash", 0.0))

        for pos in positions:
            ticker = pos.get("ticker", "")
            quantity = float(pos.get("quantity", 0.0))
            entry_price = float(pos.get("average_price", 0.0))

            if quantity <= 0 or entry_price <= 0:
                continue

            # Fetch latest price
            current_price = entry_price
            try:
                t = yf.Ticker(ticker)
                hist = t.history(period="2d")
                if not hist.empty:
                    current_price = float(hist["Close"].iloc[-1])
            except Exception as e:
                logger.warning(f"Failed to fetch price for {ticker}: {e}; using entry price.")

            return_pct = ((current_price - entry_price) / entry_price) * 100.0
            unrealized_pnl = (current_price - entry_price) * quantity

            action = "HOLD"
            order_res = {}

            # Check Take-Profit
            if return_pct >= self.take_profit_pct:
                action = "SELL_TP"
            # Check Stop-Loss
            elif return_pct <= -self.stop_loss_pct:
                action = "SELL_SL"

            if action in ("SELL_TP", "SELL_SL"):
                sym, exch = parse_symbol_and_exchange(ticker)
                logger.info(
                    f"Triggering {action} for {ticker}: qty={quantity}, entry={entry_price}, current={current_price} ({return_pct:+.2f}%)"
                )
                order_res = self.openalgo_client.place_order(
                    symbol=sym,
                    exchange=exch,
                    action="SELL",
                    quantity=quantity,
                    pricetype="MARKET",
                    product="CNC",
                    strategy="TradingAgents-Exit",
                )
                # Liquidate into cash
                cash += (quantity * current_price)
                realized_pnl = unrealized_pnl
            else:
                remaining_positions.append(pos)
                realized_pnl = 0.0

            action_results.append(
                ExitActionResult(
                    ticker=ticker,
                    quantity=quantity,
                    entry_price=entry_price,
                    current_price=round(current_price, 2),
                    return_pct=round(return_pct, 2),
                    action=action,
                    realized_pnl=round(realized_pnl, 2),
                    order_status=order_res,
                )
            )

        # Update and save portfolio
        portfolio["cash"] = round(cash, 2)
        portfolio["positions"] = remaining_positions
        self.save_portfolio(portfolio)

        return action_results
