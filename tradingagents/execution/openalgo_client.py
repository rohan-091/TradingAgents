"""OpenAlgo API client for order execution and paper trading."""

from __future__ import annotations

import logging
import os
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


def parse_symbol_and_exchange(ticker: str, default_exchange: str = "NSE") -> tuple[str, str]:
    """Parse ticker symbol and exchange from format such as RELIANCE.NS or 500325.BO."""
    ticker_clean = ticker.strip().upper()
    if ticker_clean.endswith(".NS"):
        return ticker_clean[:-3], "NSE"
    if ticker_clean.endswith(".BO"):
        return ticker_clean[:-3], "BSE"
    return ticker_clean, default_exchange


class OpenAlgoClient:
    """HTTP client for communicating with a local or remote OpenAlgo instance."""

    def __init__(self, base_url: str | None = None, api_key: str | None = None, timeout: int = 10):
        self.base_url = (
            base_url if base_url is not None else (os.getenv("OPENALGO_BASE_URL") or "http://127.0.0.1:5000")
        ).rstrip("/")
        self.api_key = api_key if api_key is not None else (os.getenv("OPENALGO_API_KEY") or "")
        self.timeout = timeout

    def ping(self) -> bool:
        """Check connection and authentication status with OpenAlgo."""
        try:
            url = f"{self.base_url}/api/v1/ping/"
            resp = requests.post(url, json={"apikey": self.api_key}, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "success":
                    return True
            # Fallback to funds endpoint check
            funds = self.get_funds()
            return funds.get("status") == "success"
        except Exception as e:
            logger.warning(f"Failed to ping OpenAlgo: {e}")
            return False

    def get_funds(self) -> dict[str, Any]:
        """Fetch live funds/cash balances from OpenAlgo (paper/analyze or live)."""
        if not self.api_key:
            return {"availablecash": 20000000.0, "status": "simulated"}
        url = f"{self.base_url}/api/v1/funds/"
        try:
            resp = requests.post(url, json={"apikey": self.api_key}, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                funds_data = data.get("data", {})
                return {
                    "availablecash": float(funds_data.get("availablecash", 0.0)),
                    "totalpnl": float(funds_data.get("totalpnl", 0.0)),
                    "utiliseddebits": float(funds_data.get("utiliseddebits", 0.0)),
                    "mode": data.get("mode", "unknown"),
                    "status": "success",
                }
            return {"availablecash": 20000000.0, "status": "error", "message": resp.text}
        except Exception as e:
            logger.error(f"Error fetching funds from OpenAlgo: {e}")
            return {"availablecash": 20000000.0, "status": "error", "message": str(e)}

    def get_holdings(self) -> list[dict[str, Any]]:
        """Fetch settled Demat delivery holdings from OpenAlgo."""
        if not self.api_key:
            return []
        url = f"{self.base_url}/api/v1/holdings/"
        try:
            resp = requests.post(url, json={"apikey": self.api_key}, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                raw_holdings = data.get("holdings", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
                active = []
                for h in raw_holdings:
                    qty = float(h.get("quantity", 0))
                    if qty > 0:
                        sym = h.get("symbol", "")
                        exch = h.get("exchange", "NSE")
                        suffix = ".BO" if exch == "BSE" else ".NS"
                        active.append({
                            "ticker": f"{sym}{suffix}" if not sym.endswith((".NS", ".BO")) else sym,
                            "symbol": sym,
                            "exchange": exch,
                            "quantity": qty,
                            "average_price": float(h.get("average_price", 0.0)),
                            "ltp": float(h.get("ltp", 0.0)),
                            "pnl": float(h.get("pnl", 0.0)),
                        })
                return active
            return []
        except Exception as e:
            logger.error(f"Error fetching holdings from OpenAlgo: {e}")
            return []

    def get_positions(self, include_holdings: bool = True) -> list[dict[str, Any]]:
        """Fetch current open positions and settled delivery holdings from OpenAlgo."""
        if not self.api_key:
            return []
        url = f"{self.base_url}/api/v1/positionbook/"
        active_map: dict[str, dict[str, Any]] = {}
        try:
            resp = requests.post(url, json={"apikey": self.api_key}, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                positions = data.get("data", [])
                for p in positions:
                    qty = float(p.get("quantity", 0))
                    if qty > 0:
                        sym = p.get("symbol", "")
                        exch = p.get("exchange", "NSE")
                        suffix = ".BO" if exch == "BSE" else ".NS"
                        ticker = f"{sym}{suffix}" if not sym.endswith((".NS", ".BO")) else sym
                        active_map[ticker] = {
                            "ticker": ticker,
                            "symbol": sym,
                            "exchange": exch,
                            "quantity": qty,
                            "average_price": float(p.get("average_price", 0.0)),
                            "ltp": float(p.get("ltp", 0.0)),
                            "pnl": float(p.get("pnl", 0.0)),
                        }
        except Exception as e:
            logger.error(f"Error fetching positions from OpenAlgo: {e}")

        # In Indian markets, CNC delivery positions move from positionbook into holdings end-of-day
        if include_holdings:
            holdings = self.get_holdings()
            for h in holdings:
                ticker = h["ticker"]
                if ticker not in active_map:
                    active_map[ticker] = h

        return list(active_map.values())

    def place_order(
        self,
        symbol: str,
        action: str,
        quantity: float,
        exchange: str = "NSE",
        pricetype: str = "MARKET",
        product: str = "CNC",
        price: float = 0.0,
        strategy: str = "TradingAgents-Paper",
    ) -> dict[str, Any]:
        """Place an order (regular or AMO pre-market) through OpenAlgo."""
        if not self.api_key:
            return {
                "status": "simulated",
                "message": "No OPENALGO_API_KEY configured; simulated locally.",
                "orderid": f"SIM-{symbol}-{action}",
            }

        url = f"{self.base_url}/api/v1/placeorder/"
        payload = {
            "apikey": self.api_key,
            "strategy": strategy,
            "exchange": exchange,
            "symbol": symbol,
            "action": action.upper(),
            "quantity": int(quantity),
            "pricetype": pricetype,
            "product": product,
            "price": price,
        }

        try:
            resp = requests.post(url, json=payload, timeout=self.timeout)
            data = resp.json()
            if resp.status_code in (200, 201) and data.get("status") == "success":
                logger.info(f"OpenAlgo order placed successfully: {payload}")
                return data
            logger.warning(f"OpenAlgo order rejected: {resp.status_code} - {data}")
            return {
                "status": "error",
                "code": resp.status_code,
                "message": data.get("message", "Order failed"),
                "data": data,
            }
        except Exception as e:
            logger.error(f"Error calling OpenAlgo placeorder: {e}")
            return {"status": "error", "message": str(e)}

    def place_gtt_oco_order(
        self,
        symbol: str,
        quantity: float,
        stop_loss_trigger: float,
        stop_loss_limit: float,
        target_trigger: float,
        target_limit: float,
        exchange: str = "NSE",
        product: str = "CNC",
        action: str = "SELL",
        strategy: str = "TradingAgents-GTT",
    ) -> dict[str, Any]:
        """Place an exchange-side GTT OCO (One-Cancels-Other) target & stop-loss trigger in OpenAlgo."""
        if not self.api_key:
            return {
                "status": "simulated",
                "trigger_id": f"SIM-GTT-{symbol}",
                "message": "No OPENALGO_API_KEY configured; simulated locally.",
            }

        url = f"{self.base_url}/api/v1/placegttorder/"
        payload = {
            "apikey": self.api_key,
            "strategy": strategy,
            "trigger_type": "OCO",
            "exchange": exchange,
            "symbol": symbol,
            "action": action.upper(),
            "product": product,
            "quantity": int(quantity),
            "pricetype": "LIMIT",
            "price": round(target_trigger, 2),
            "triggerprice_sl": round(stop_loss_trigger, 2),
            "stoploss": round(stop_loss_limit, 2),
            "triggerprice_tg": round(target_trigger, 2),
            "target": round(target_limit, 2),
        }

        try:
            resp = requests.post(url, json=payload, timeout=self.timeout)
            data = resp.json()
            if resp.status_code in (200, 201) and data.get("status") == "success":
                logger.info(f"OpenAlgo GTT OCO trigger placed successfully: {data.get('trigger_id')}")
                return data
            logger.warning(f"OpenAlgo GTT placement rejected: {resp.status_code} - {data}")
            return {
                "status": "error",
                "code": resp.status_code,
                "message": data.get("message", "GTT placement failed"),
                "data": data,
            }
        except Exception as e:
            logger.error(f"Error calling OpenAlgo placegttorder: {e}")
            return {"status": "error", "message": str(e)}

    def get_gtt_orderbook(self) -> list[dict[str, Any]]:
        """Fetch all active GTT orders from OpenAlgo."""
        if not self.api_key:
            return []
        url = f"{self.base_url}/api/v1/gttorderbook/"
        try:
            resp = requests.post(url, json={"apikey": self.api_key}, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("data", [])
            return []
        except Exception as e:
            logger.error(f"Error fetching GTT orderbook from OpenAlgo: {e}")
            return []

