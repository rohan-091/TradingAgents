"""
Fetch Screener.in metrics for 8 newly added SME companies under Harness² protocol.
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

companies = [
    ('544826', 'Millworks Technologies Ltd', 'https://www.screener.in/company/544826/'),
    ('544773', 'Merritronix Ltd', 'https://www.screener.in/company/544773/'),
    ('544971', 'Vans Electroengineerings Ltd', 'https://www.screener.in/company/544971/'),
    ('SPECTRAA', 'SpectraA Technology Solutions Ltd', 'https://www.screener.in/company/SPECTRAA/consolidated/'),
    ('CREDENT', 'Credent Connect N Care Ltd', 'https://www.screener.in/company/CREDENT/consolidated/'),
    ('E2ERAIL', 'E to E Transportation Infrastructure Ltd', 'https://www.screener.in/company/E2ERAIL/consolidated/'),
    ('AVIENCE', 'Avience Biomedicals Ltd', 'https://www.screener.in/company/AVIENCE/consolidated/'),
    ('TEJA', 'Teja Engineering Industries Ltd', 'https://www.screener.in/company/TEJA/')
]

data = {}

for sym, name, url in companies:
    time.sleep(2.0)
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
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
                    
            # About / Moat
            about_div = soup.find('div', class_='about')
            about = about_div.text.strip() if about_div else ''
            
            # Shareholding
            sh_data = {}
            sh_sec = soup.find('section', id='shareholding')
            if sh_sec:
                table = sh_sec.find('table', class_='data-table')
                if table:
                    for tr in table.find_all('tr'):
                        tds = tr.find_all('td')
                        if len(tds) > 1:
                            rname = tds[0].text.strip().replace('+', '').strip()
                            vals = [td.text.strip() for td in tds[1:]]
                            sh_data[rname] = vals[-1] if vals else 'N/A'
                            
            data[sym] = {
                'name': name,
                'url': url,
                'ratios': ratios,
                'about': about[:400],
                'shareholding': sh_data
            }
            mcap = ratios.get('Market Cap', 'N/A')
            cmp = ratios.get('Current Price', 'N/A')
            roce = ratios.get('ROCE', 'N/A')
            roe = ratios.get('ROE', 'N/A')
            pe = ratios.get('Stock P/E', 'N/A')
            print(f"SUCCESS: {sym} ({name}) | MCap: {mcap} Cr | CMP: {cmp} | P/E: {pe} | ROCE: {roce}% | ROE: {roe}%", flush=True)
    except Exception as e:
        print(f"ERROR: {sym} -> {e}", flush=True)

out_file = Path("scratch/new_8_screener_data.json")
out_file.parent.mkdir(parents=True, exist_ok=True)
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

print(f"Data saved to {out_file}", flush=True)
