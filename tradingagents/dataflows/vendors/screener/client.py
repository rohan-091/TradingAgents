"""Screener.in browser automation and data extraction client."""

from __future__ import annotations

import contextlib
import logging
import re
from dataclasses import asdict, dataclass, field
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from tradingagents.dataflows.errors import VendorError

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


class ScreenerScrapeError(VendorError):
    """Raised when extraction from Screener.in fails."""


@dataclass
class ScreenerCompanyData:
    """Extracted financial tables, metrics, and documents from Screener.in."""

    company_name: str = ""
    bse_code: str = ""
    bse_symbol: str = ""
    nse_code: str = ""
    url: str = ""
    current_price: str = ""
    market_cap: str = ""
    high_low: str = ""
    stock_pe: str = ""
    book_value: str = ""
    dividend_yield: str = ""
    roce: str = ""
    roe: str = ""
    face_value: str = ""
    about_text: str = ""
    key_points: list[str] = field(default_factory=list)
    peers_table: list[dict[str, str]] = field(default_factory=list)
    quarters_table: dict[str, list[str]] = field(default_factory=dict)
    profit_loss_table: dict[str, list[str]] = field(default_factory=dict)
    compounded_growth: dict[str, dict[str, str]] = field(default_factory=dict)
    balance_sheet_table: dict[str, list[str]] = field(default_factory=dict)
    cash_flows_table: dict[str, list[str]] = field(default_factory=dict)
    ratios_table: dict[str, list[str]] = field(default_factory=dict)
    shareholding_table: dict[str, list[str]] = field(default_factory=dict)
    pros: list[str] = field(default_factory=list)
    cons: list[str] = field(default_factory=list)
    concalls: list[dict[str, str]] = field(default_factory=list)
    annual_reports: list[dict[str, str]] = field(default_factory=list)
    announcements: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ScreenerBrowserClient:
    """Client for navigating and extracting complete company data from Screener.in."""

    def __init__(self, timeout_seconds: int = 30):
        self.timeout_seconds = timeout_seconds

    def normalize_url(self, query_or_url: str) -> str:
        """Resolve a company ticker, BSE code, or full URL to a screener company URL."""
        query_or_url = query_or_url.strip()
        if query_or_url.startswith("http://") or query_or_url.startswith("https://"):
            return query_or_url
        clean_code = re.sub(r"\s+", "", query_or_url.strip("/").split("/")[-1].upper())
        return f"https://www.screener.in/company/{clean_code}/"

    def fetch_company_data(
        self,
        query_or_url: str,
        use_playwright: bool = True,
        fetch_document_contents: bool = True,
    ) -> ScreenerCompanyData:
        """Fetch and extract all company metrics, tables, and documents."""
        target_url = self.normalize_url(query_or_url)
        html_content = ""

        if use_playwright:
            try:
                html_content = self._fetch_via_playwright(target_url)
            except Exception as e:
                logger.warning(
                    "Playwright navigation failed (%s); falling back to direct HTTP request.",
                    e,
                )

        if not html_content:
            html_content = self._fetch_via_requests(target_url)

        data = self.parse_screener_html(html_content, base_url=target_url)

        if fetch_document_contents and data.concalls:
            self._enrich_concall_transcripts(data)

        return data

    def _fetch_via_playwright(self, url: str) -> str:
        """Use headless Playwright Chromium to navigate, click tabs, and fetch rendered HTML."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent=USER_AGENT)
            page.set_default_timeout(self.timeout_seconds * 1000)
            page.goto(url, wait_until="domcontentloaded")
            # Ensure dynamic elements are settled
            with contextlib.suppress(Exception):
                page.wait_for_selector("#top", timeout=5000)
            # Wait for peers table loaded via AJAX
            with contextlib.suppress(Exception):
                page.wait_for_selector("#peers table", timeout=5000)
            content = page.content()
            browser.close()
            return content

    def _fetch_via_requests(self, url: str) -> str:
        """Fetch static HTML via requests with headers."""
        headers = {"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"}
        try:
            resp = requests.get(url, headers=headers, timeout=self.timeout_seconds)
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            raise ScreenerScrapeError(f"Failed to fetch {url} from Screener.in: {e}") from e

    def _enrich_concall_transcripts(self, data: ScreenerCompanyData, max_transcripts: int = 3):
        """Fetch transcript text for the most recent concalls."""
        headers = {"User-Agent": USER_AGENT}
        for item in data.concalls[:max_transcripts]:
            t_url = item.get("transcript_url")
            if t_url and not item.get("transcript_text"):
                # If transcript points directly to a PDF file, skip binary HTML parsing
                if t_url.lower().endswith(".pdf"):
                    item["transcript_text"] = "[PDF Transcript available at linked URL]"
                    continue
                try:
                    res = requests.get(t_url, headers=headers, timeout=12)
                    content_type = res.headers.get("Content-Type", "").lower()
                    if "application/pdf" in content_type:
                        item["transcript_text"] = "[PDF Transcript available at linked URL]"
                        continue
                    if res.status_code == 200:
                        soup = BeautifulSoup(res.text, "html.parser")
                        body = soup.find("article") or soup.find("pre") or soup.find("div", class_="body") or soup.body
                        if body:
                            item["transcript_text"] = body.get_text(separator="\n", strip=True)[:40000]
                except Exception as e:
                    logger.debug("Could not fetch transcript from %s: %s", t_url, e)

    def parse_screener_html(self, html: str, base_url: str = "https://www.screener.in") -> ScreenerCompanyData:
        """Parse raw HTML into structured ScreenerCompanyData."""
        soup = BeautifulSoup(html, "html.parser")
        page_title = soup.title.get_text(strip=True).lower() if soup.title else ""
        if "just a moment" in page_title or soup.find(id="challenge-running"):
            raise ScreenerScrapeError(
                "Encountered Cloudflare anti-bot verification page on Screener.in. Try using Playwright or check network connection."
            )

        data = ScreenerCompanyData(url=base_url)

        # Company Name & Codes
        name_elem = soup.find("h1")
        if name_elem:
            # Strip badges like <span class="badge">SME</span> while preserving company name span
            for badge in name_elem.find_all(class_=lambda c: c and "badge" in c):
                badge.decompose()
            for small in name_elem.find_all("small"):
                small.decompose()
            data.company_name = " ".join(name_elem.get_text(separator=" ", strip=True).split())

        text_all = soup.get_text()
        bse_match = re.search(r"BSE(?:\s*-\s*SME)?:\s*(\d+)", text_all, re.IGNORECASE)
        if bse_match:
            data.bse_code = bse_match.group(1)

        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "bseindia.com" in href:
                bse_link_match = re.search(r"/stock-share-price/[^/]+/([A-Za-z0-9]+)/(\d{6})", href)
                if bse_link_match:
                    data.bse_symbol = bse_link_match.group(1)
                    if not data.bse_code:
                        data.bse_code = bse_link_match.group(2)
            elif "nseindia.com" in href:
                nse_link_match = re.search(r"symbol=([A-Za-z0-9\-]+)", href)
                if nse_link_match and not data.nse_code:
                    data.nse_code = nse_link_match.group(1)

        nse_match = re.search(r"NSE:\s*([A-Za-z0-9\-]+)", text_all)
        if nse_match and not data.nse_code:
            data.nse_code = nse_match.group(1)

        def _clean_metric(v: str) -> str:
            return v.replace("₹", "").replace("\u20b9", "").replace("Cr.", "").replace("Cr", "").strip()

        # Top Ratios / Header Metrics Box
        top_ratios = soup.find("ul", id="top-ratios")
        if top_ratios:
            for li in top_ratios.find_all("li"):
                name = li.find("span", class_="name")
                val = li.find("span", class_="value") or li.find("span", class_="number")
                if not name or not val:
                    continue
                label = name.get_text(strip=True).lower()
                raw_num = val.get_text(strip=True)
                clean_num = _clean_metric(raw_num)

                if "current price" in label:
                    data.current_price = clean_num
                elif "market cap" in label:
                    data.market_cap = clean_num
                elif "high / low" in label or "high/low" in label:
                    data.high_low = clean_num
                elif "stock p/e" in label or label == "p/e":
                    data.stock_pe = clean_num.replace("x", "")
                elif "book value" in label:
                    data.book_value = clean_num
                elif "dividend yield" in label:
                    data.dividend_yield = clean_num.replace("%", "")
                elif "roce" in label:
                    data.roce = clean_num.replace("%", "")
                elif "roe" in label:
                    data.roe = clean_num.replace("%", "")
                elif "face value" in label:
                    data.face_value = clean_num

        # About & Key Points
        about_div = soup.find("div", class_="about")
        if about_div:
            about_text = about_div.get_text(separator=" ", strip=True)
            data.about_text = re.sub(r"\s+", " ", about_text)

        commentary = soup.find("div", class_="commentary") or soup.find("div", id="commentary")
        if commentary:
            for p in commentary.find_all(["p", "li"]):
                pt = p.get_text(strip=True)
                if pt and len(pt) > 15:
                    data.key_points.append(pt)

        # Pros and Cons
        pros_div = soup.find("div", class_="pros")
        if pros_div:
            data.pros = [li.get_text(strip=True) for li in pros_div.find_all("li")]
        cons_div = soup.find("div", class_="cons")
        if cons_div:
            data.cons = [li.get_text(strip=True) for li in cons_div.find_all("li")]

        # Financial Tables Extraction Helper
        def parse_table_section(section_id: str) -> dict[str, list[str]]:
            sec = soup.find("section", id=section_id)
            if not sec:
                return {}
            table = sec.find("table")
            if not table:
                return {}
            result: dict[str, list[str]] = {}
            # Parse header
            thead = table.find("thead")
            headers: list[str] = []
            if thead:
                headers = [th.get_text(strip=True) for th in thead.find_all("th") if th.get_text(strip=True)]
                if headers:
                    result["Headers"] = headers

            tbody = table.find("tbody") or table
            for row in tbody.find_all("tr"):
                # Strip tooltip/helper spans so row names are not contaminated
                for tip in row.find_all(class_=re.compile(r"tooltip|info|help", re.I)):
                    tip.decompose()
                cells = [td.get_text(" ", strip=True) for td in row.find_all(["td", "th"])]
                if len(cells) > 1:
                    row_name = re.sub(r"[\+:]+$", "", cells[0]).strip()
                    result[row_name] = cells[1:]
            return result

        data.quarters_table = parse_table_section("quarters")
        data.profit_loss_table = parse_table_section("profit-loss")
        data.balance_sheet_table = parse_table_section("balance-sheet")
        data.cash_flows_table = parse_table_section("cash-flow")
        data.ratios_table = parse_table_section("ratios")
        data.shareholding_table = parse_table_section("shareholding")

        # Compounded Growth tables
        pl_sec = soup.find("section", id="profit-loss")
        if pl_sec:
            for c_table in pl_sec.find_all("table", class_="ranges-table"):
                th = c_table.find("th")
                if not th:
                    continue
                title = th.get_text(strip=True)
                group: dict[str, str] = {}
                for tr in c_table.find_all("tr")[1:]:
                    tds = tr.find_all("td")
                    if len(tds) == 2:
                        group[tds[0].get_text(strip=True)] = tds[1].get_text(strip=True)
                if group:
                    data.compounded_growth[title] = group

        # Peer Comparison
        peers_sec = soup.find("section", id="peers")
        if peers_sec:
            p_table = peers_sec.find("table")
            if p_table:
                p_headers = [th.get_text(strip=True) for th in p_table.find_all("th")]
                for tr in p_table.find_all("tr")[1:]:
                    tds = [td.get_text(strip=True) for td in tr.find_all("td")]
                    if len(tds) >= 4 and p_headers:
                        row_dict = {
                            p_headers[i] if i < len(p_headers) else f"col_{i}": tds[i]
                            for i in range(len(tds))
                        }
                        data.peers_table.append(row_dict)

        # Documents Section (#documents)
        doc_sec = soup.find("section", id="documents")
        if doc_sec:
            # Concalls
            for a in doc_sec.find_all("a"):
                href = a.get("href", "")
                text = a.get_text(strip=True)
                full_url = urljoin(base_url, href)

                if "concall" in href.lower() or "transcript" in text.lower() or "concall" in text.lower():
                    # check if already added
                    parent_text = a.parent.get_text(" ", strip=True) if a.parent else ""
                    date_match = re.search(r"([A-Za-z]{3}\s*\d{4}|\d{2}/\d{4}|\d{4})", parent_text)
                    doc_date = date_match.group(1) if date_match else "Recent"
                    entry = {
                        "date": doc_date,
                        "title": text or "Concall Transcript",
                        "transcript_url": full_url,
                        "transcript_text": "",
                        "ppt_url": "",
                        "ai_summary": "",
                    }
                    data.concalls.append(entry)
                elif "annual" in href.lower() or "annual report" in text.lower():
                    data.annual_reports.append({
                        "title": text or "Annual Report",
                        "url": full_url,
                    })
                elif "announcement" in href.lower() or "announcement" in text.lower() or "bse" in href.lower():
                    data.announcements.append({
                        "title": text or "Material Announcement",
                        "url": full_url,
                    })

        return data


def extract_screener_data(query_or_url: str, use_playwright: bool = True) -> ScreenerCompanyData:
    """Convenience helper to extract complete company data from Screener.in."""
    client = ScreenerBrowserClient()
    return client.fetch_company_data(query_or_url, use_playwright=use_playwright)
