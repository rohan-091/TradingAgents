# 🇮🇳 TradingAgents — Indian Equities & OpenAlgo Paper Trading Variant

> **For AI Agents & Developers:** This document serves as the complete, self-contained handoff guide to set up, operate, and extend this custom variant of [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents).

---

## 1. Executive Summary & Purpose

This fork (`rohan-091/TradingAgents`, branch `feat/custom-agents`) transforms the original US-equity research framework into an **automated, production-grade daily paper trading system tailored specifically for Indian Equities (NSE/BSE)**.

### What Was Built:
1. **501-Stock Universe (NIFTY 500 / BSE 500):** Built a full Indian equities watchlist (`watchlist_india.json`) covering all major liquid large-, mid-, and small-cap stocks.
2. **2-Stage Vectorized Funnel Screener:**
   - **Stage 1 (Vectorized Technical Screen):** Downloads chunked batch daily candles for 501 stocks via `yfinance` in **0.45 seconds**, computing RSI(14), 20/50 SMA momentum, 5-day return %, and 20-day volume expansion. Filters down to the Top 15 breakout finalists.
   - **Stage 2 (Deep Fundamental Audit):** Queries Screener.in without paid API keys to extract ROCE %, P/E ratio, and debt metrics, outputting the **Top 3 high-conviction candidates** (total scan runtime: ~35–45 seconds).
3. **OpenAlgo REST API Paper Trading Bridge:** Implemented `OpenAlgoClient` (`tradingagents/execution/openalgo_client.py`) connecting to a local OpenAlgo gateway instance (`http://127.0.0.1:5000`) operating in Zerodha Sandbox/Analyze paper trading mode.
4. **Position Exit Manager:** Implemented `PositionExitManager` (`tradingagents/execution/exit_manager.py`) executing automated morning risk exits:
   - **$+8.0\%$ Take-Profit (TP)**
   - **$-3.0\%$ Stop-Loss (SL)**
5. **The Golden Rule Risk Management:**
   - **Max 0.05% per order** (₹10,000 INR on a ₹2 Crore portfolio).
   - **Max 0.25% gross market exposure** at any given moment (₹50,000 INR total in market).
   - **$\ge 99.75\%$ safe cash reserve** (₹1,99,50,000 INR).
   - Automated order size clamp & circuit breaker halting buys when exposure reaches 0.25%.
6. **Zero External Paid LLM Cost:** Designed to run with zero OpenAI/Anthropic billings by offloading qualitative reasoning to Antigravity session quota and quantitative screening to fast local vectorized math.

---

## 2. System Architecture

```
                  ┌──────────────────────────────────────────────┐
                  │ 501 Indian Equities (NIFTY 500 / BSE 500)     │
                  └───────────────────────┬──────────────────────┘
                                          │
                                          ▼
                [Stage 1: Vectorized Technical Screening (0.45s)]
                RSI 14, 20/50 SMA, 5-Day Momentum, Volume Spike
                                          │
                                          ▼ Top 15 Finalists
                [Stage 2: Screener.in Fundamental Extraction]
                ROCE > 15%, Reasonable P/E, Low Debt Audit
                                          │
                                          ▼ Top 3 Finalists
┌────────────────────────────────────────────────────────────────────────┐
│ Daily Orchestrator (scripts/run_daily_india_pipeline.py @ 08:45 AM)    │
│                                                                        │
│  1. Sync Funds & Positions with OpenAlgo (₹2 Cr Base)                  │
│  2. Evaluate Open Positions (+8% Take Profit, -3% Stop Loss)           │
│  3. Enforce Golden Rule (0.05% order cap, 0.25% gross exposure cap)    │
│  4. Dispatch AMO CNC Orders to OpenAlgo REST API                       │
│  5. Generate Markdown & HTML Morning Reports                           │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
       ┌─────────────────────────────────────────────────────────┐
       │ OpenAlgo Gateway (http://127.0.0.1:5000)                │
       │ Mode: 'analyze' (Zerodha Sandbox DB: sandbox.db)        │
       │ Capital: ₹2,00,00,000.00 INR (₹2 Crore)                 │
       └─────────────────────────────────────────────────────────┘
```

---

## 3. Directory Layout & Key Files

```
TradingAgents/
├── watchlist_india.json                   # 501 Nifty 500 tickers & Golden Rule config
├── portfolio_inr.json                     # Persistent local portfolio ledger
├── results/                               # Daily Markdown & HTML summary reports
├── scripts/
│   ├── filter_india_top3.py               # 2-stage hierarchical funnel screener
│   └── run_daily_india_pipeline.py        # End-to-end daily automated runner
├── tradingagents/
│   ├── dataflows/vendors/screener/
│   │   └── client.py                      # Screener.in extraction client
│   └── execution/
│       ├── openalgo_client.py             # OpenAlgo REST API client (Zerodha paper trading)
│       └── exit_manager.py                # +8% TP / -3% SL portfolio exit manager
└── tests/
    ├── test_india_execution.py            # Unit tests for Indian execution, Golden Rule & exits
    ├── test_screener_browser.py           # Unit tests for Screener.in integration
    └── test_screener_docx.py              # Unit tests for Word doc reports
```

---

## 4. Environment & Dependency Setup

### Step 1: Install `uv` and Create Virtual Environment
We recommend using `uv` for blazing-fast package management:

```powershell
# In PowerShell (Windows)
cd C:\Users\CM_Rail\PycharmProjects\TradingAgents

# Create virtualenv with Python 3.12+
uv venv .venv --python 3.12

# Activate virtualenv
.venv\Scripts\activate
```

### Step 2: Install TradingAgents in Editable Mode
```powershell
uv pip install -e ".[dev]"
uv pip install python-docx
```

### Step 3: Configure Environment Variables (`.env`)
Create or edit `.env` in the root of `TradingAgents`:

```ini
# OpenAlgo Gateway Config
OPENALGO_API_KEY=721e63f44a4286a5e1dc260df88210a2a67370f9b81d7c62b8119ec26ed3e238
OPENALGO_HOST=http://127.0.0.1:5000

# Optional: LangSmith / Tracing
# LANGCHAIN_TRACING_V2=false
```

---

## 5. OpenAlgo Gateway Integration Setup

OpenAlgo acts as the broker abstraction layer. In this variant, OpenAlgo runs locally in **Analyze Mode** (Paper Trading sandbox with Zerodha syntax).

### Step 1: Locate and Start OpenAlgo
OpenAlgo is installed alongside this project at `C:\Users\CM_Rail\PycharmProjects\algotrading`.

```powershell
# In a separate terminal session
cd C:\Users\CM_Rail\PycharmProjects\algotrading

# Activate OpenAlgo virtual environment (if applicable) and start server
python app.py
```
OpenAlgo will start on `http://127.0.0.1:5000`.

### Step 2: Verify OpenAlgo Health & Broker Status
You can test the connectivity using curl or python:

```powershell
curl -X POST http://127.0.0.1:5000/api/v1/ping/ `
  -H "Content-Type: application/json" `
  -d '{"apikey": "721e63f44a4286a5e1dc260df88210a2a67370f9b81d7c62b8119ec26ed3e238"}'
```
**Expected Response:**
```json
{
  "status": "success",
  "broker": "zerodha",
  "message": "Ping successful"
}
```

### Step 3: Paper Capital Rebase (₹2,00,00,000 / ₹2 Crore)
The default OpenAlgo sandbox starting balance is ₹1 Crore. To rebase to ₹2 Crore:

```python
# Run inside algotrading directory
from database.sandbox_db import SandboxDatabase
from sandbox.fund_manager import SandboxFundManager

db = SandboxDatabase()
fund_mgr = SandboxFundManager(db)
fund_mgr.rebase_starting_capital(20000000.0)
print("Rebased OpenAlgo paper capital to 20,000,000.00 INR")
```

---

## 6. Risk Management & The Golden Rule

The risk profile is configured in `watchlist_india.json`:

```json
{
  "market": "INDIA",
  "default_exchange": "NSE",
  "max_order_capital_pct": 0.05,
  "max_market_exposure_pct": 0.25,
  "allocation_per_trade_inr": 10000.0,
  "max_open_positions": 5,
  "take_profit_pct": 8.0,
  "stop_loss_pct": 3.0
}
```

### Mathematical Enforcement:
- **Total Capital:** ₹2,00,00,000.00 (₹2 Crore)
- **Order Budget:** $\text{Capital} \times 0.05\% = \mathbf{₹10,000.00\text{ INR per trade}}$
- **Gross Exposure Ceiling:** $\text{Capital} \times 0.25\% = \mathbf{₹50,000.00\text{ INR total}}$
- **Safe Cash Floor:** $\mathbf{\ge 99.75\%}$ ($\ge ₹1,99,50,000.00\text{ INR}$)
- **Max Positions:** 5 positions $\times$ ₹10,000 = ₹50,000 total exposure.
- **Circuit Breaker:** If existing market exposure is ₹50,000, `run_daily_india_pipeline.py` immediately logs `GOLDEN RULE CAP` and blocks all new orders until existing positions are exited.

---

## 7. How to Run the Pipeline

### Daily Pre-Market Run (08:45 AM IST)
Execute the daily runner:

```powershell
python scripts/run_daily_india_pipeline.py
```

### What Happens Automatically:
1. **Syncs Ledger:** Connects to OpenAlgo port 5000, fetches live `availablecash` and open positions, and updates `portfolio_inr.json`.
2. **Evaluates Morning Exits:** Fetches latest market quotes for all open positions. Dispatches **SELL** orders for any stock hitting $+8\%$ TP or $-3\%$ SL.
3. **Screens 501 Stocks:** Runs vectorized technical filter (0.45s) &rarr; Screener.in fundamental scoring &rarr; Selects Top 3 candidates.
4. **Calculates Position Size:** Applies Golden Rule (0.05% order cap and remaining room under 0.25% gross exposure cap).
5. **Dispatches AMO Orders:** Sends After-Market Orders (`product="CNC"`, `pricetype="MARKET"`) via OpenAlgo so they execute cleanly when the market opens at 09:15 AM IST.
6. **Generates Reports:** Outputs Markdown and HTML summary reports in `results/daily_summary_<DATE>.md`.

---

## 8. Running the Test Suite

Verify everything is working using pytest:

```powershell
# Run Indian execution, Golden Rule & exit tests
uv run pytest tests/test_india_execution.py -v

# Run Screener scraper tests
uv run pytest -k "screener or storm" -v
```
All tests should pass cleanly.

---

## 9. Intraday Price Monitoring Options

1. **Current (Daily Pre-Market Batch):** `PositionExitManager` queries daily closing/opening prices at 08:45 AM IST before market open to evaluate $+8\%$ TP and $-3\%$ SL.
2. **Live Tick-by-Tick GTT OCO (Recommended for Intraday):**
   - Zerodha & OpenAlgo support GTT OCO (Good-Till-Triggered / One-Cancels-Other) via `POST /api/v1/placegttorder/`.
   - Attaching GTT triggers during the buy order offloads all real-time tick-by-tick monitoring to the exchange/broker engine with **no need to keep your PC or script running**.

---

## 10. Handoff Notes for the Next Agent

- **Active Branch:** Always work on `feat/custom-agents`. Upstream tracking remote is `upstream` (`https://github.com/TauricResearch/TradingAgents.git`). Fork remote is `origin` (`https://github.com/rohan-091/TradingAgents.git`).
- **OpenAlgo API Key:** Stored in `.env` as `OPENALGO_API_KEY`.
- **Pre-Market Timing:** Indian equity markets (NSE/BSE) trade Monday–Friday from 09:15 to 15:30 IST. Any order submitted before 09:15 AM must be an **AMO** (After Market Order).
- **Delisted / Inactive Tickers:** The screener handles ticker null-values and splits gracefully (`closes.dropna().shape[0] >= 20`).
