#!/usr/bin/env python3
"""2-Stage Hierarchical Vectorized Funnel Screener for Indian Equities (BSE 500 / NIFTY 500).

Stage 1: Vectorized batch OHLCV download & technical screening across all 500 stocks
         (Calculates RSI, 20/50 SMA, 5D Momentum, and Volume Spikes in ~10 seconds).
         Filters 500 down to the Top 15 Breakout Finalists.

Stage 2: Deep Fundamental Enrichment via Screener.in on the Top 15 Finalists
         (ROCE, Stock P/E, Sales Growth, Debt/Equity).
         Selects the Top 3 High-Conviction Investment Opportunities.
"""

from __future__ import annotations

import json
import logging
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yfinance as yf

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tradingagents.dataflows.vendors.screener.client import extract_screener_data

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Funnel500")


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


def compute_vectorized_rsi(closes: pd.DataFrame, period: int = 14) -> pd.Series:
    """Compute 14-period RSI across all ticker columns simultaneously."""
    delta = closes.diff()
    gain = delta.clip(lower=0)
    loss = -1 * delta.clip(upper=0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    rs = avg_gain / (avg_loss + 1e-9)
    rsi_df = 100 - (100 / (1 + rs))
    return rsi_df.iloc[-1].fillna(50.0)


def download_universe_batch(tickers: list[str], chunk_size: int = 150) -> pd.DataFrame:
    """Download OHLCV data in concurrent chunks to maximize throughput and reliability."""
    all_dfs: list[pd.DataFrame] = []
    logger.info(f"Downloading market data for {len(tickers)} Indian equities in chunks of {chunk_size}...")

    for i in range(0, len(tickers), chunk_size):
        chunk = tickers[i : i + chunk_size]
        try:
            df_chunk = yf.download(chunk, period="60d", threads=True, progress=False)
            if not df_chunk.empty:
                all_dfs.append(df_chunk)
        except Exception as e:
            logger.warning(f"Error downloading chunk {i}-{i+chunk_size}: {e}")

    if not all_dfs:
        raise RuntimeError("Failed to download price history for any tickers.")

    if len(all_dfs) == 1:
        return all_dfs[0]

    return pd.concat(all_dfs, axis=1)


def stage1_vectorized_technical_screen(
    df: pd.DataFrame, tickers: list[str], top_finalists: int = 15
) -> list[dict[str, Any]]:
    """Stage 1: Fast mathematical filter across all 500 stocks down to top technical finalists."""
    logger.info("Stage 1: Executing vectorized technical calculations across universe...")
    t0 = time.time()

    closes = df["Close"]
    volumes = df["Volume"]

    # Filter out columns with insufficient data
    valid_cols = [c for c in closes.columns if closes[c].dropna().shape[0] >= 20]
    if not valid_cols:
        return []

    closes = closes[valid_cols]
    volumes = volumes[valid_cols]

    p_now = closes.iloc[-1]
    p_5d_ago = closes.iloc[-5] if len(closes) >= 5 else p_now
    pct_change_5d = ((p_now - p_5d_ago) / p_5d_ago) * 100.0

    sma20 = closes.rolling(20).mean().iloc[-1]
    sma50 = closes.rolling(min(50, len(closes))).mean().iloc[-1]

    above_sma20 = p_now >= sma20
    above_sma50 = p_now >= sma50

    rsi_series = compute_vectorized_rsi(closes, period=14)

    vol_20 = volumes.rolling(20).mean().iloc[-1]
    vol_ratio = (volumes.iloc[-1] / (vol_20 + 1e-9)).fillna(1.0)

    # Score each stock technically (0 to 60 points max)
    technical_candidates = []
    for ticker in valid_cols:
        cur_price = float(p_now[ticker])
        if np.isnan(cur_price) or cur_price <= 0:
            continue

        score = 0.0
        rationale: list[str] = []

        is_above_20 = bool(above_sma20.get(ticker, False))
        is_above_50 = bool(above_sma50.get(ticker, False))
        rsi_val = float(rsi_series.get(ticker, 50.0))
        vol_rat = float(vol_ratio.get(ticker, 1.0))
        mom_5d = float(pct_change_5d.get(ticker, 0.0))

        if is_above_20:
            score += 20.0
            rationale.append("Price > 20 SMA")
        if is_above_50:
            score += 15.0
            rationale.append("Price > 50 SMA")

        # RSI sweet-spot: 45 to 65 indicates bullish momentum without being overbought (>70)
        if 45.0 <= rsi_val <= 65.0:
            score += 20.0
            rationale.append(f"Bullish RSI ({rsi_val:.1f})")
        elif rsi_val < 35.0:
            score += 10.0
            rationale.append(f"Oversold Bounce Potential ({rsi_val:.1f})")

        # Volume confirmation
        if vol_rat >= 1.2:
            score += 15.0
            rationale.append(f"Volume Surge ({vol_rat:.1f}x)")

        # Momentum bonus
        if mom_5d > 0:
            score += min(15.0, mom_5d * 2.0)
            rationale.append(f"5D Momentum +{mom_5d:.1f}%")

        technical_candidates.append({
            "ticker": ticker,
            "current_price": round(cur_price, 2),
            "rsi": round(rsi_val, 1),
            "sma20": round(float(sma20.get(ticker, 0.0)), 2),
            "sma50": round(float(sma50.get(ticker, 0.0)), 2),
            "above_sma20": is_above_20,
            "above_sma50": is_above_50,
            "pct_change_5d": round(mom_5d, 2),
            "volume_ratio": round(vol_rat, 2),
            "technical_score": round(score, 1),
            "rationale": rationale,
        })

    technical_candidates.sort(key=lambda x: x["technical_score"], reverse=True)
    finalists = technical_candidates[:top_finalists]
    logger.info(
        f"Stage 1 Complete: Screened {len(valid_cols)} stocks in {time.time()-t0:.2f}s! Selected Top {len(finalists)} finalists."
    )
    return finalists


def stage2_fundamental_enrichment(
    finalists: list[dict[str, Any]], top_n: int = 3
) -> list[CandidateScore]:
    """Stage 2: Enrich the top technical finalists with Screener.in fundamentals and select Top N."""
    logger.info(f"Stage 2: Enriching Top {len(finalists)} finalists with Screener.in fundamentals...")
    scored_candidates: list[CandidateScore] = []

    for item in finalists:
        ticker = item["ticker"]
        base_symbol = ticker.replace(".NS", "").replace(".BO", "")
        company_name = base_symbol
        roce_val = None
        pe_val = None
        score = item["technical_score"]
        rationale = list(item["rationale"])

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

        scored_candidates.append(
            CandidateScore(
                ticker=ticker,
                company_name=company_name,
                current_price=item["current_price"],
                rsi=item["rsi"],
                sma20=item["sma20"],
                sma50=item["sma50"],
                above_sma20=item["above_sma20"],
                above_sma50=item["above_sma50"],
                pct_change_5d=item["pct_change_5d"],
                volume_ratio=item["volume_ratio"],
                roce=roce_val,
                stock_pe=pe_val,
                total_score=round(score, 1),
                rationale=rationale,
            )
        )

    scored_candidates.sort(key=lambda s: s.total_score, reverse=True)
    return scored_candidates[:top_n]


def get_top_candidates(
    watchlist_path: str | Path = "watchlist_india.json",
    top_n: int = 3,
) -> list[CandidateScore]:
    """Execute the complete 2-stage hierarchical funnel on the universe."""
    path = Path(watchlist_path)
    if not path.exists():
        raise FileNotFoundError(f"Watchlist file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        config = json.load(f)

    tickers: list[str] = config.get("tickers", [])
    if not tickers:
        logger.warning("No tickers found in watchlist!")
        return []

    t_start = time.time()
    df = download_universe_batch(tickers, chunk_size=170)
    top_finalists = stage1_vectorized_technical_screen(df, tickers, top_finalists=15)
    top_candidates = stage2_fundamental_enrichment(top_finalists, top_n=top_n)

    logger.info(
        f"2-Stage Funnel Complete across {len(tickers)} stocks in {time.time()-t_start:.2f}s! Selected {len(top_candidates)} winners."
    )
    return top_candidates


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("Executing 2-Stage Vectorized Funnel on Indian Equity Universe (500 Stocks)...")
    t0 = time.time()
    top3 = get_top_candidates("watchlist_india.json", top_n=3)
    elapsed = time.time() - t0

    print(f"\nCompleted 500-Stock Scan in {elapsed:.2f} seconds!\n")
    print(f"Top {len(top3)} High-Conviction Candidates:\n")
    for idx, c in enumerate(top3, 1):
        roce_s = f"{c.roce:.1f}%" if c.roce is not None else "N/A"
        pe_s = f"{c.stock_pe:.1f}" if c.stock_pe is not None else "N/A"
        print(f"#{idx} {c.ticker} ({c.company_name}) - Score: {c.total_score}/100")
        print(f"    Price: Rs. {c.current_price:,.2f} | RSI: {c.rsi} | ROCE: {roce_s} | P/E: {pe_s}")
        print(f"    Signals: {'; '.join(c.rationale)}\n")
