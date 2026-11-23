"""
Auditing screener.in ground-truth data for SME candidates under Harness² protocol.
"""
import urllib.request
import time
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

symbols = [
    ('544310', 'YASHHV', 'Yash Highvoltage Ltd'),
    ('544150', 'KPGEL', 'KP Green Engineering Ltd'),
    ('SPCL', 'SPCL', 'Shivalic Power Control Ltd'),
    ('GGBL', 'GGBL', 'Ganesh Green Bharat Ltd'),
    ('EFFWA', 'EFFWA', 'Effwa Infra & Research Ltd'),
    ('RULKA', 'RULKA', 'Rulka Electricals Ltd'),
    ('WINSOL', 'WINSOL', 'Winsol Engineers Ltd'),
    ('544186', 'KRONOX', 'Kronox Lab Sciences Ltd'),
    ('544222', 'AFCOM', 'Afcom Holdings Ltd'),
    ('543620', 'INA', 'Insolation Energy Ltd'),
    ('SAHAJSOLAR', 'SAHAJSOLAR', 'Sahaj Solar Ltd')
]

results = {}

for sym, short_code, name in symbols:
    url = f"https://www.screener.in/company/{sym}/"
    print(f"Fetching screener for {short_code} ({sym})...", flush=True)
    time.sleep(2.5) # respect rate limit
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode('utf-8', errors='ignore')
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract ratios
            ratios = {}
            for li in soup.find_all('li', class_=re.compile(r'flex.*')):
                name_span = li.find('span', class_='name')
                val_span = li.find('span', class_='value') or li.find('span', class_='number')
                if name_span and val_span:
                    k = name_span.text.strip().replace('\u20b9', '').strip()
                    v = val_span.text.strip().replace('\u20b9', '').strip()
                    ratios[k] = v
            
            # Extract Shareholding Pattern Table
            shareholding = {}
            sh_section = soup.find('section', id='shareholding')
            if sh_section:
                table = sh_section.find('table', class_='data-table')
                if table:
                    headers_th = [th.text.strip() for th in table.find_all('th') if th.text.strip()]
                    for tr in table.find_all('tr'):
                        tds = tr.find_all('td')
                        if len(tds) > 1:
                            row_name = tds[0].text.strip().replace('+', '').strip()
                            vals = [td.text.strip() for td in tds[1:]]
                            shareholding[row_name] = dict(zip(headers_th[-len(vals):], vals))
            
            # Extract Profit & Loss / Compounded Growth
            sales_growth = {}
            profit_growth = {}
            ranges_table = soup.find('table', class_='ranges-table')
            
            results[short_code] = {
                'screener_symbol': sym,
                'name': name,
                'screener_url': url,
                'ratios': ratios,
                'shareholding': shareholding
            }
            print(f"SUCCESS: {short_code} | MCap: {ratios.get('Market Cap')} Cr | Price: {ratios.get('Current Price')} | ROCE: {ratios.get('ROCE')}% | ROE: {ratios.get('ROE')}%", flush=True)
    except Exception as e:
        print(f"ERROR: {short_code} -> {e}", flush=True)

out_file = Path("scratch/screener_audited_data.json")
out_file.parent.mkdir(parents=True, exist_ok=True)
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print(f"Audit saved to {out_file}", flush=True)
