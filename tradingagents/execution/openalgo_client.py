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
                return data.get("status") == "success"
            return False
        except Exception as e:
            logger.warning(f"Failed to ping OpenAlgo: {e}")
            return False

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
