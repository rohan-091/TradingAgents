#!/usr/bin/env python3
"""Deterministic funnel screener for Indian equities (NSE/BSE).

Filters a watchlist down to the top 3 best-positioned candidates using
rapid quantitative analysis (momentum, trend, volume, and Screener.in metrics)
before passing them to the multi-agent deliberation council.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yfinance as yf

from tradingagents.dataflows.vendors.screener.client import extract_screener_data

logger = logging.getLogger(__name__)


@dataclass
class CandidateScore:
    ticker: str
    company_name: str
    current_price: float
    rsi: float
    sma20: float
    sma50: float
    above_sma20: bool
    above_sma50: bool
    pct_change_5d: float
    volume_ratio: float
    roce: float | None
    stock_pe: float | None
    total_score: float
    rationale: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def compute_rsi(series: pd.Series, period: int = 14) -> float:
    """Compute the 14-period Relative Strength Index."""
    if len(series) < period + 1:
        return 50.0
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -1 * delta.clip(upper=0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()

    rs = avg_gain / (avg_loss + 1e-9)
    rsi_series = 100 - (100 / (1 + rs))
    val = rsi_series.dropna().iloc[-1]
    return float(val) if not np.isnan(val) else 50.0


def score_single_stock(ticker: str) -> CandidateScore | None:
    """Fetch technicals and fundamentals for a single ticker and compute opportunity score."""
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="60d")
        if hist.empty or len(hist) < 20:
            logger.warning(f"Insufficient history for {ticker}")
            return None

        closes = hist["Close"]
        current_price = float(closes.iloc[-1])
        sma20 = float(closes.rolling(20).mean().iloc[-1])
        sma50 = float(closes.rolling(min(50, len(closes))).mean().iloc[-1])
        above_sma20 = current_price >= sma20
        above_sma50 = current_price >= sma50

        # 5-day momentum
        p_5d_ago = float(closes.iloc[-5]) if len(closes) >= 5 else current_price
        pct_change_5d = ((current_price - p_5d_ago) / p_5d_ago) * 100.0

        # RSI (14)
        rsi = compute_rsi(closes, period=14)

        # Volume ratio (latest volume vs 20d average)
        volumes = hist["Volume"]
        avg_vol = float(volumes.rolling(20).mean().iloc[-1]) if len(volumes) >= 20 else 1.0
        latest_vol = float(volumes.iloc[-1])
        vol_ratio = (latest_vol / avg_vol) if avg_vol > 0 else 1.0

        # Base scoring
        score = 0.0
        rationale: list[str] = []

        # Trend scoring
        if above_sma20:
            score += 20.0
            rationale.append("Price > 20 SMA")
        if above_sma50:
            score += 15.0
            rationale.append("Price > 50 SMA")

        # RSI sweet-spot: 45 to 65 indicates bullish momentum without being overbought (>70)
        if 45.0 <= rsi <= 65.0:
            score += 25.0
            rationale.append(f"Healthy Bullish RSI ({rsi:.1f})")
        elif rsi < 35.0:
            score += 10.0
            rationale.append(f"Oversold Bounce Potential ({rsi:.1f})")

        # Volume confirmation
        if vol_ratio >= 1.2:
            score += 15.0
            rationale.append(f"Volume Spike ({vol_ratio:.1f}x)")

        # Short-term momentum positive
        if pct_change_5d > 0:
            score += min(15.0, pct_change_5d * 3.0)
            rationale.append(f"5D Momentum +{pct_change_5d:.1f}%")

        # Screener.in extraction for Indian equities
        base_symbol = ticker.replace(".NS", "").replace(".BO", "")
        company_name = base_symbol
        roce_val = None
        pe_val = None

        try:
            screener_data = extract_screener_data(base_symbol, use_playwright=False)
            if screener_data.company_name:
                company_name = screener_data.company_name
            if screener_data.roce:
                try:
                    roce_clean = float(screener_data.roce.replace("%", "").replace(",", "").strip())
                    roce_val = roce_clean
                    if roce_clean >= 15.0:
                        score += 15.0
                        rationale.append(f"High ROCE ({roce_clean:.1f}%)")
                except ValueError:
                    pass

            if screener_data.stock_pe:
                try:
                    pe_clean = float(screener_data.stock_pe.replace(",", "").strip())
                    pe_val = pe_clean
                    if 0 < pe_clean <= 35.0:
                        score += 10.0
                        rationale.append(f"Reasonable P/E ({pe_clean:.1f})")
                except ValueError:
                    pass
        except Exception as e:
            logger.debug(f"Screener lookup skipped for {ticker}: {e}")

        return CandidateScore(
            ticker=ticker,
            company_name=company_name,
            current_price=round(current_price, 2),
            rsi=round(rsi, 1),
            sma20=round(sma20, 2),
            sma50=round(sma50, 2),
            above_sma20=above_sma20,
            above_sma50=above_sma50,
            pct_change_5d=round(pct_change_5d, 2),
            volume_ratio=round(vol_ratio, 2),
            roce=roce_val,
            stock_pe=pe_val,
            total_score=round(score, 1),
            rationale=rationale,
        )
    except Exception as e:
        logger.error(f"Error evaluating {ticker}: {e}")
        return None


def get_top_candidates(
    watchlist_path: str | Path = "watchlist_india.json",
    top_n: int = 3,
) -> list[CandidateScore]:
    """Load watchlist, evaluate all tickers, and return the top N scored candidates."""
    path = Path(watchlist_path)
    if not path.exists():
        raise FileNotFoundError(f"Watchlist file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        config = json.load(f)

    tickers: list[str] = config.get("tickers", [])
    scores: list[CandidateScore] = []

    for ticker in tickers:
        res = score_single_stock(ticker)
        if res:
            scores.append(res)

    scores.sort(key=lambda s: s.total_score, reverse=True)
    return scores[:top_n]


if __name__ == "__main__":
    import sys

    # Configure UTF-8 output for Windows console
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("Running Top-3 Indian Funnel Screener...")
    top3 = get_top_candidates("watchlist_india.json", top_n=3)
    print(f"\nSuccessfully selected Top {len(top3)} Candidates:\n")
    for idx, c in enumerate(top3, 1):
        print(
            f"#{idx} {c.ticker} ({c.company_name}) - Score: {c.total_score}/100 | "
            f"Price: Rs. {c.current_price:,.2f} | RSI: {c.rsi} | ROCE: {c.roce}%"
        )
        print(f"   Signals: {', '.join(c.rationale)}\n")
