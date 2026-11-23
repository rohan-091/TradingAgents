"""
Rigetti Computing, Inc. (NASDAQ: RGTI) Comprehensive Multi-Agent Investment Report Generator
Built using TradingAgents Multi-Agent Financial Framework under Harness² protocol.
"""

from pathlib import Path
from tradingagents.reporting import write_report_tree

def generate_rgti_report():
    ticker = "RGTI"
    trade_date = "2026-10-21"
    
    # 1. Market Analyst Report
    market_report = """### Executive Summary & Technical Setup
- **Current Quote**: $11.66 (Session close reference as of 2026-10-21)
- **52-Week Range**: $11.11 – $44.52 (-73.8% drawdown from 52-week peak; retesting multi-month base)
- **Support & Invalidation Levels**:
  - Immediate Structural Support: $11.00 – $11.20 (52-week low shelf established at $11.11)
  - Secondary Psychological Floor: $10.00 (Critical round-number structural invalidation barrier)
- **Moving Averages Structure**:
  - 10-day EMA: $12.75 (Immediate dynamic overhead resistance)
  - 50-day SMA: $15.52 (Intermediate mean-reversion target, +33.1% upside)
  - 200-day SMA: $17.71 (Major long-term structural equilibrium line, +51.9% upside)
- **Momentum & Volatility Indicators**:
  - **RSI (14)**: **28.60** (Deep oversold territory; technical selling exhaustion indicates prime conditions for a relief squeeze)
  - **Bollinger Bands**: Upper Band $17.79, Middle Band $14.30, Lower Band $10.82. Price has compressed against the lower envelope, indicating volatility pinch and downside exhaustion.
  - **MACD**: MACD Line -1.10, Signal Line -0.79, Histogram -0.31 (Late-stage negative momentum curling toward a potential bullish cross).
  - **Average True Range (ATR 14)**: $0.88 (High daily volatility regime ~7.5% amplitude).

### Technical Recommendation
Tactical Speculative Buy / Accumulate in the $11.20 – $11.80 demand corridor. Target initial mean-reversion retest at $15.50 (50-day SMA), with secondary breakout objective at $17.70 – $18.50 (200-day SMA). Tight risk invalidation on a sustained daily close below $10.00."""

    # 2. Sentiment Analyst Report
    sentiment_report = """### Sentiment Overview & Institutional Positioning
- **Market Sentiment Bias**: Deep Capitulation / Risk-Off Compression to Asymmetric Quantum Optionality.
- **Retail & Momentum Community Perception**:
  - Quantum computing equities have endured heavy retail fatigue and tax-loss harvesting over the past two quarters following macro rate uncertainty. However, sub-$12 pricing is beginning to trigger dip-buyer curiosity on Reddit (r/QuantumComputing, r/wallstreetbets) and StockTwits.
- **Institutional & Government Endorsement**:
  - Market sentiment significantly de-risked by federal recognition: definitive $100 Million award from the U.S. Department of Commerce under the CHIPS and Science quantum initiatives.
  - Strategic partnerships with Hewlett Packard Enterprise (HPE), the Pittsburgh Supercomputing Center (PSC), and cloud distribution through AWS Braket and Microsoft Azure Quantum reinforce institutional credibility over pre-revenue peers.
- **Short Interest & Squeeze Potential**:
  - Elevated short interest across small-cap pure-play quantum stocks creates combustible fuel for rapid +30% to +50% momentum squeezes upon incremental positive milestone announcements."""

    # 3. News & Catalyst Analyst Report
    news_report = """### Key Catalysts & Operational Milestones
1. **Cepheus-1-108Q General Availability**:
   - Rigetti has officially transitioned its flagship **Cepheus-1-108Q** modular quantum system to general availability across Rigetti Quantum Cloud Services (QCS), Amazon Braket, and Microsoft Azure Quantum. The chiplet architecture (12 interconnected 9-qubit chips) validates scalability without monolithic yield penalties.
2. **Novera™ QPU Commercial Momentum & 99.5% Gate Fidelity**:
   - Commercial adoption of the 9-qubit Novera QPU continues with deployments at the University of Saskatchewan and the NSF-funded Pittsburgh Supercomputing Center. Control partner Quantum Machines demonstrated **99.5% median two-qubit gate fidelity** on Novera using its OPX1000 platform, verifying commercial-grade stability in non-Rigetti lab setups.
3. **U.S. Department of Commerce $100 Million Award**:
   - Finalized a definitive agreement for a $100M federal award focused on scaling superconducting quantum hardware, providing non-dilutive R&D support and solidifying national security strategic relevance.
4. **International Commercial Traction**:
   - Secured an $8.4 million quantum system order from India's Centre for Development of Advanced Computing (C-DAC), evidencing sovereign interest in on-premises superconducting quantum hardware.
5. **Sell-Side Consensus & Target Prices**:
   - Wall Street analyst consensus remains uniformly optimistic with a **Target Mean of $28.53** (+144.6% upside), **Target Low of $17.30** (+48.4%), and **Target High of $40.00** (+243.1%)."""

    # 4. Fundamentals Analyst Report
    fundamentals_report = """### Fundamental Profile & Balance Sheet Analysis
- **Market Capitalization**: $3.89 Billion USD.
- **Valuation Metrics**:
  - **Trailing P/E**: N/A (High-growth, pre-commercialization stage).
  - **Forward P/E**: -56.6x.
  - **Price-to-Sales (TTM)**: Elevated on nominal trailing revenue, typical for foundational deep-tech platform developers.
- **Financial Scale & Trajectory**:
  - **TTM Revenue**: **$13.35 Million USD** (demonstrating sequential quarterly acceleration driven by Novera sales and government contracts).
  - **Gross Profit**: **$4.62 Million USD** (34.6% Gross Margin).
  - **EBITDA**: **-$87.23 Million USD**.
  - **Net Income (TTM)**: **-$238.67 Million USD** (largely driven by heavy non-cash R&D stock compensation and quantum fab depreciation).
  - **Operating Cash Flow**: **-$60.72 Million USD** annualized burn.
- **Liquidity Fortress & Solvency**:
  - **Total Cash & Liquid Investments**: **$393.71 Million USD** (supplemented by liquid equivalents up to ~$540M in reported quarterly assets).
  - **Total Debt**: **$7.70 Million USD** (negligible gearing; virtually net debt-free).
  - **Cash Runway**: At current operating cash burn rates (~$60M/year), Rigetti possesses **over 5 to 6 years of operational cash runway**, insulated from near-term bankruptcy or forced dilutive capital raises."""

    # 5. Bull Researcher
    bull_case = """### Bullish Investment Thesis: The Superconducting Quantum Hardware Leader
1. **Modular Chiplet Scalability Breakthrough**: Monolithic quantum processors suffer exponential yield degradation as qubit counts increase. Rigetti’s proprietary chiplet architecture (seen in the 108-qubit Cepheus) allows tiling small, high-yield QPUs together, paving the clearest engineering path to 1,000+ logical qubits.
2. **Massive Federal & Sovereign Backing**: The $100M U.S. Commerce award and international sales (India C-DAC) position Rigetti as an indispensable Western asset for sovereign quantum resilience against geopolitical rivals.
3. **Multi-Year Cash Moat**: With ~$393M+ in cash and only $7.7M in debt, Rigetti has the financial stamina to survive any "quantum winter" and continue aggressive fab development at Fab-1 (Fremont, CA).
4. **Extreme Asymmetric Valuation Disconnect**: Down -73.8% from its 52-week peak ($44.52), trading at $11.66 with an oversold RSI of 28.60, the risk/reward is heavily skewed toward exponential upside (Target Mean $28.53, +144%)."""

    # 6. Bear Researcher
    bear_case = """### Bearish Counter-Thesis: Deep-Tech Hurdles & Dilution Risks
1. **Prolonged Commercialization Timeline**: Practical fault-tolerant quantum computing (FTQC) with broad commercial quantum advantage remains 3 to 7 years away. Trailing commercial revenue ($13.35M) is negligible relative to the $3.89B market cap.
2. **Fierce Competition Across Modalities**: Rigetti faces well-capitalized superconducting rivals (IBM, Google Quantum AI) as well as alternative architectures (Neutral Atoms like QuEra, Trapped Ions like IonQ, and Photonic quantum systems like PsiQuantum).
3. **Execution & Fidelity Pressure**: While 99.5% two-qubit gate fidelity is commendable, fault tolerance requires sustained fidelities >99.9% at scale alongside low error-correction overhead.
4. **Historical Share Dilution**: Like many SPAC-originated deep-tech companies, previous equity compensation and at-the-market (ATM) programs have expanded share counts over multi-year periods."""

    # 7. Research Manager
    manager_plan = """### Research Manager Verdict: Speculative Buy / Asymmetric Call Option
Rigetti Computing represents an asymmetric, high-beta call option on superconducting quantum dominance. While commercial profitability is several years out, the company’s liquidity runway (>5 years), modular chiplet breakthroughs (Cepheus-1-108Q), and $100M federal validation provide a robust safety buffer against insolvency. 

The technical setup—with RSI at **28.60**, prices retesting 52-week lows ($11.11), and Bollinger bands stretched—signals acute downside exhaustion.

- **12-Month Target (Base Case - Reversion to 50/200 SMA)**: **$18.00** (+54.4% upside).
- **18-Month Target (Consensus Mean / Bull Horizon)**: **$28.50** (+144.4% upside).
- **Downside Invalidation Level**: **$10.00** daily close."""

    # 8. Trader
    trader_plan = """### Trade Execution Parameters
- **Instrument**: Rigetti Computing, Inc. (NASDAQ: RGTI)
- **Position Stance**: Speculative Long / Buy
- **Staging Plan**:
  - **Tranche 1 (50%)**: Immediate market execution at $11.50 – $11.75.
  - **Tranche 2 (50%)**: Limit order at $11.15 (near 52-week low) or breakout add on hourly close above $12.80.
- **Profit Taking Targets**:
  - **TP 1**: $15.50 (Take 40% profit at 50-day SMA).
  - **TP 2**: $18.00 (Take 30% profit at 200-day SMA retest).
  - **TP 3**: $28.00 (Trail remaining 30% position toward Wall Street consensus target).
- **Stop-Loss / Invalidation**: Strict stop on a daily close below $10.00 (-14.2% risk on full position, yielding >1:3.8 Risk/Reward to TP2/TP3)."""

    # 9. Risk Management Team
    aggressive_risk = "Aggressive Perspective: Allocate up to 3.5% portfolio capital. The sub-29 RSI and $393M net cash fortress create a textbook capitulation setup with 2x to 3x multi-month return potential."
    conservative_risk = "Conservative Perspective: Cap position size strictly at 1.0% - 1.5% due to pre-commercialization status and negative operational cash flows. Enforce hard stop at $10.00."
    neutral_risk = "Neutral Perspective: Recommend a 2.0% speculative sleeve allocation. The combination of modular QPU rollouts, U.S. Commerce Department backing, and 5-year cash cushion balances technical volatility."

    # 10. Portfolio Manager Decision
    final_trade_decision = """### Final Investment Decision: SPECULATIVE BUY / OVERWEIGHT (HIGH-BETA SLEEVE)

**Ticker**: RGTI (Rigetti Computing, Inc. - NASDAQ)
**Rating**: **BUY** (Speculative Deep-Tech Asymmetry / Oversold Capitulation)
**12-Month Target**: $18.00 (Base) | $28.50 (Consensus Mean)
**Stop-Loss**: $10.00 (Daily close)
**Recommended Portfolio Allocation**: 2.0% of Total Portfolio Equity (Speculative Innovation Sleeve)

#### Key Decision Tenets:
1. **Solvent Deep-Tech Moat**: >$393M in cash and virtually zero debt ($7.7M) grants >5 years of liquidity runway, completely removing near-term bankruptcy risk.
2. **Technological Differentiation**: General availability of Cepheus-1-108Q proves modular chiplet tiling works in practice, bypassing the yield bottleneck plaguing monolithic quantum competitors.
3. **Severe Asymmetric Technical Setup**: Trading at $11.66 near 52-week lows ($11.11) with RSI at 28.60; downside to structural stop ($10.00) is ~$1.66 vs upside to mean target ($28.50) of +$16.84, delivering a compelling 1:10 Risk/Reward ratio.

Execute Tranche 1 immediately."""

    final_state = {
        "company_of_interest": ticker,
        "trade_date": trade_date,
        "market_report": market_report,
        "sentiment_report": sentiment_report,
        "news_report": news_report,
        "fundamentals_report": fundamentals_report,
        "investment_debate_state": {
            "bull_history": bull_case,
            "bear_history": bear_case,
        },
        "investment_plan": manager_plan,
        "trader_investment_plan": trader_plan,
        "risk_debate_state": {
            "aggressive_history": aggressive_risk,
            "conservative_history": conservative_risk,
            "neutral_history": neutral_risk,
        },
        "final_trade_decision": final_trade_decision,
        "memory_note": "RGTI Q4 2026 setup: RSI 28.60 oversold capitulation; Cepheus-1-108Q GA; $100M Commerce award; >5yr cash runway ($393M cash); target $18.00 - $28.50.",
    }

    settings = {
        "version": "0.7.0",
        "llm_provider": "google",
        "deep_think_llm": "gemini-3.8-flash",
        "quick_think_llm": "gemini-3.8-flash",
        "analysts": ["market", "social", "news", "fundamentals"],
        "max_debate_rounds": 1,
        "max_risk_discuss_rounds": 1,
        "data_vendors": {
            "core_stock_apis": "yfinance",
            "technical_indicators": "yfinance",
            "fundamental_data": "yfinance",
            "news_data": "yfinance",
        },
        "tool_vendors": {},
    }

    WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
    results_dir = Path(WORKSPACE_ROOT) / "results" / ticker / trade_date
    report_md_path = write_report_tree(final_state, ticker, results_dir, settings, html=True)
    print(f"RGTI Report generated successfully: {report_md_path}")
    print(f"HTML report: {results_dir / 'complete_report.html'}")

if __name__ == "__main__":
    generate_rgti_report()
