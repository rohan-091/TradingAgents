"""Tests for Screener.in browser client and HTML table parsing."""

import pytest

from tradingagents.dataflows.vendors.screener.client import (
    ScreenerBrowserClient,
    ScreenerCompanyData,
)

SAMPLE_SCREENER_HTML = """
<!DOCTYPE html>
<html>
<head><title>Tata Motors Ltd financial results</title></head>
<body>
  <h1>Tata Motors Ltd</h1>
  <div class="company-links">BSE: 500570 | NSE: TATAMOTORS</div>
  <ul id="top-ratios">
    <li><span class="name">Market Cap</span><span class="value">3,50,000</span></li>
    <li><span class="name">Current Price</span><span class="value">950</span></li>
    <li><span class="name">High / Low</span><span class="value">1050 / 650</span></li>
    <li><span class="name">Stock P/E</span><span class="value">18.5</span></li>
    <li><span class="name">Book Value</span><span class="value">280</span></li>
    <li><span class="name">Dividend Yield</span><span class="value">0.85</span></li>
    <li><span class="name">ROCE</span><span class="value">21.2</span></li>
    <li><span class="name">ROE</span><span class="value">24.5</span></li>
    <li><span class="name">Face Value</span><span class="value">2.0</span></li>
  </ul>
  <div class="about">Tata Motors is a leading global automobile manufacturer producing commercial and passenger vehicles.</div>
  <div class="pros"><ul><li>Company has delivered good profit growth of 25% CAGR over last 5 years</li></ul></div>
  <div class="cons"><ul><li>Tax rate seems low</li></ul></div>
  <section id="profit-loss">
    <table>
      <thead>
        <tr><th></th><th>Mar 2022</th><th>Mar 2023</th><th>Mar 2024</th><th>TTM</th></tr>
      </thead>
      <tbody>
        <tr><td>Sales</td><td>2,78,454</td><td>3,45,967</td><td>4,37,928</td><td>4,45,000</td></tr>
        <tr><td>Expenses</td><td>2,53,650</td><td>3,14,150</td><td>3,80,000</td><td>3,85,000</td></tr>
        <tr><td>Operating Profit</td><td>24,804</td><td>31,817</td><td>57,928</td><td>60,000</td></tr>
        <tr><td>OPM %</td><td>9%</td><td>9%</td><td>13%</td><td>13%</td></tr>
        <tr><td>Net Profit</td><td>-11,441</td><td>2,414</td><td>31,399</td><td>33,000</td></tr>
      </tbody>
    </table>
  </section>
  <section id="peers">
    <table>
      <thead>
        <tr><th>Name</th><th>CMP</th><th>P/E</th><th>Mar Cap</th><th>ROCE %</th><th>Div Yld %</th></tr>
      </thead>
      <tbody>
        <tr><td>Mahindra &amp; Mahindra</td><td>2850</td><td>28.5</td><td>3,40,000</td><td>18.2</td><td>0.75</td></tr>
        <tr><td>Maruti Suzuki</td><td>12500</td><td>26.0</td><td>3,90,000</td><td>19.5</td><td>1.10</td></tr>
      </tbody>
    </table>
  </section>
  <section id="documents">
    <div class="concalls">
      <div>
        <span>Jan 2025</span>
        <a href="/concall/transcript/12345/">Transcript</a>
        <a href="/concall/ppt/12345/">PPT</a>
      </div>
    </div>
    <div class="annual-reports">
      <a href="/annual/report/2024/">Annual Report 2024</a>
    </div>
  </section>
</body>
</html>
"""


@pytest.mark.unit
def test_screener_client_normalize_url():
    client = ScreenerBrowserClient()
    assert client.normalize_url("500570") == "https://www.screener.in/company/500570/"
    assert client.normalize_url("tatamotors") == "https://www.screener.in/company/TATAMOTORS/"
    assert client.normalize_url("https://www.screener.in/company/TATAMOTORS/consolidated/") == (
        "https://www.screener.in/company/TATAMOTORS/consolidated/"
    )


@pytest.mark.unit
def test_parse_screener_html_metrics():
    client = ScreenerBrowserClient()
    data: ScreenerCompanyData = client.parse_screener_html(SAMPLE_SCREENER_HTML)

    assert data.company_name == "Tata Motors Ltd"
    assert data.bse_code == "500570"
    assert data.nse_code == "TATAMOTORS"
    assert data.current_price == "950"
    assert data.stock_pe == "18.5"
    assert data.market_cap == "3,50,000"
    assert data.roce == "21.2"
    assert data.roe == "24.5"
    assert "Tata Motors is a leading" in data.about_text
    assert len(data.pros) == 1
    assert len(data.cons) == 1


@pytest.mark.unit
def test_parse_screener_html_tables_and_documents():
    client = ScreenerBrowserClient()
    data: ScreenerCompanyData = client.parse_screener_html(SAMPLE_SCREENER_HTML)

    # Check P&L table
    assert "Sales" in data.profit_loss_table
    assert data.profit_loss_table["Sales"] == ["2,78,454", "3,45,967", "4,37,928", "4,45,000"]
    assert "OPM %" in data.profit_loss_table

    # Check Peers
    assert len(data.peers_table) == 2
    assert data.peers_table[0]["Name"] == "Mahindra & Mahindra"

    # Check Documents
    assert len(data.concalls) >= 1
    assert "transcript" in data.concalls[0]["transcript_url"]
    assert len(data.annual_reports) >= 1
