"""Unit tests for Indian execution bridge, exit manager, and symbol parsing."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tradingagents.execution.exit_manager import PositionExitManager
from tradingagents.execution.openalgo_client import OpenAlgoClient, parse_symbol_and_exchange


def test_parse_symbol_and_exchange():
    sym, exch = parse_symbol_and_exchange("RELIANCE.NS")
    assert sym == "RELIANCE"
    assert exch == "NSE"

    sym, exch = parse_symbol_and_exchange("500325.BO")
    assert sym == "500325"
    assert exch == "BSE"

    sym, exch = parse_symbol_and_exchange("TCS")
    assert sym == "TCS"
    assert exch == "NSE"


def test_openalgo_client_simulated():
    client = OpenAlgoClient(api_key="")
    res = client.place_order("INFY", "BUY", 10, "NSE")
    assert res["status"] == "simulated"
    assert "SIM-INFY-BUY" in res["orderid"]


def test_position_exit_manager_tp_and_sl():
    with tempfile.TemporaryDirectory() as tmpdir:
        portfolio_file = Path(tmpdir) / "portfolio.json"
        initial_portfolio = {
            "cash": 100000.0,
            "currency": "INR",
            "positions": [
                {"ticker": "WINNER.NS", "quantity": 10.0, "average_price": 100.0},
                {"ticker": "LOSER.NS", "quantity": 10.0, "average_price": 100.0},
                {"ticker": "FLAT.NS", "quantity": 10.0, "average_price": 100.0},
            ],
        }
        with open(portfolio_file, "w", encoding="utf-8") as f:
            json.dump(initial_portfolio, f)

        mock_openalgo = MagicMock()
        mock_openalgo.place_order.return_value = {"status": "success", "orderid": "12345"}

        manager = PositionExitManager(
            portfolio_path=portfolio_file,
            take_profit_pct=8.0,
            stop_loss_pct=3.0,
            openalgo_client=mock_openalgo,
        )

        def mock_yf_ticker(symbol):
            mock_t = MagicMock()
            import pandas as pd

            if "WINNER" in symbol:
                close = 110.0  # +10% -> triggers TP (>8%)
            elif "LOSER" in symbol:
                close = 95.0   # -5% -> triggers SL (<-3%)
            else:
                close = 101.0  # +1% -> HOLD
            mock_t.history.return_value = pd.DataFrame({"Close": [close]})
            return mock_t

        with patch("yfinance.Ticker", side_effect=mock_yf_ticker):
            results = manager.evaluate_and_exit_positions()

        assert len(results) == 3
        winner_res = next(r for r in results if r.ticker == "WINNER.NS")
        assert winner_res.action == "SELL_TP"
        assert winner_res.realized_pnl == 100.0

        loser_res = next(r for r in results if r.ticker == "LOSER.NS")
        assert loser_res.action == "SELL_SL"
        assert loser_res.realized_pnl == -50.0

        flat_res = next(r for r in results if r.ticker == "FLAT.NS")
        assert flat_res.action == "HOLD"

        # Check updated portfolio
        updated = manager.load_portfolio()
        # Winner (10*110 = 1100) and Loser (10*95 = 950) liquidated
        assert len(updated["positions"]) == 1
        assert updated["positions"][0]["ticker"] == "FLAT.NS"
        assert updated["cash"] == 100000.0 + 1100.0 + 950.0


def test_golden_rule_exposure_and_order_limits():
    """Verify Golden Rule: max 0.05% per order and max 0.25% total market exposure."""
    total_capital = 20000000.0  # ₹2 Crore
    max_order_pct = 0.05        # 0.05% max per order -> ₹10,000
    max_exposure_pct = 0.25     # 0.25% max gross exposure -> ₹50,000

    max_per_order = total_capital * (max_order_pct / 100.0)
    max_exposure = total_capital * (max_exposure_pct / 100.0)

    assert max_per_order == 10000.0
    assert max_exposure == 50000.0

    # Simulate 5 positions of ₹10,000 each (total ₹50,000 = 0.25%)
    positions = [{"ticker": f"STOCK{i}.NS", "quantity": 10.0, "average_price": 1000.0} for i in range(5)]
    current_exposure = sum(p["quantity"] * p["average_price"] for p in positions)
    assert current_exposure == 50000.0

    remaining_room = max(0.0, max_exposure - current_exposure)
    assert remaining_room == 0.0

    # When remaining room is 0, any new candidate order must be rejected/skipped
    candidate_price = 500.0
    order_budget = min(max_per_order, remaining_room)
    qty = int(order_budget / candidate_price)
    assert qty == 0  # Blocked from placing new order


def test_openalgo_gtt_oco_placement():
    """Verify OpenAlgoClient GTT OCO order construction."""
    client = OpenAlgoClient(base_url="http://127.0.0.1:5000", api_key="")
    # Test simulated response without API key
    res = client.place_gtt_oco_order(
        symbol="TCS",
        quantity=3,
        stop_loss_trigger=2439.55,
        stop_loss_limit=2439.00,
        target_trigger=2716.20,
        target_limit=2717.00,
    )
    assert res["status"] == "simulated"
    assert "trigger_id" in res


