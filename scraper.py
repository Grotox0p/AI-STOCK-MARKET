#!/usr/bin/env python3
"""
scraper.py

Fetches the current Nifty 50 constituents and writes them to nifty50_today.csv.

Strategy:
1) Try to download NSE's official CSV (recommended).
2) If that fails, try to scrape the NiftyIndices page.
3) If that fails, as a last resort parse Wikipedia's NIFTY 50 page.

Requires: requests, pandas, beautifulsoup4
Install: pip install requests pandas beautifulsoup4
"""

import sys
import time
import csv
from io import StringIO

import requests
import pandas as pd
from bs4 import BeautifulSoup

OUTFILE = "nifty50_today.csv"

# Official CSV URL observed on NSE site
NSE_CSV_URL = "https://nsearchives.nseindia.com/content/indices/ind_nifty50list.csv"
NSE_HOME = "https://www.nseindia.com"

# Fallback pages
NIFTYINDICES_URL = "https://www.niftyindices.com/indices/equity/broad-based-indices/nifty--50"
WIKIPEDIA_URL = "https://en.wikipedia.org/wiki/NIFTY_50"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": NSE_HOME,
}

def save_df(df, path=OUTFILE):
    """Save dataframe to CSV with a small header and timestamp."""
    df.to_csv(path, index=False)
    print(f"Saved {len(df)} rows to {path}")

def try_nse_csv(session):
    """Try to download the official CSV from NSE archives endpoint."""
    print("Trying official NSE CSV:", NSE_CSV_URL)
    # First hit home to get cookies
    session.get(NSE_HOME, headers=HEADERS, timeout=10)
    # Wait briefly (helps if the server expects some session setup)
    time.sleep(0.5)
    resp = session.get(NSE_CSV_URL, headers={**HEADERS, "Referer": NSE_HOME}, timeout=15)
    if resp.status_code == 200 and resp.text.strip():
        # Attempt to parse CSV with pandas
        try:
            df = pd.read_csv(StringIO(resp.text))
            # Normalize column names
            df.columns = [c.strip() for c in df.columns]
            print("Downloaded CSV from NSE successfully.")
            return df
        except Exception as e:
            print("Failed to parse NSE CSV:", e)
            # still return None to try other methods
    else:
        print(f"NSE CSV request returned status {resp.status_code}")
    return None

def try_niftyindices():
    """Try to scrape constituents from niftyindices.com page."""
    print("Trying NiftyIndices page:", NIFTYINDICES_URL)
    resp = requests.get(NIFTYINDICES_URL, headers=HEADERS, timeout=15)
    if resp.status_code != 200:
        print("NiftyIndices fetch failed with status", resp.status_code)
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    # Find tables on the page - many index pages have a constituents table
    table = soup.find("table")
    if not table:
        print("No table found on NiftyIndices page.")
        return None

    # Parse the table
    rows = []
    headers = [th.get_text(strip=True) for th in table.find_all("th")]
    for tr in table.find_all("tr"):
        cols = [td.get_text(strip=True) for td in tr.find_all("td")]
        if cols:
            rows.append(cols)

    if not rows:
        print("No rows found in table.")
        return None

    try:
        df = pd.DataFrame(rows, columns=headers[: len(rows[0])])
        print("Parsed constituents from NiftyIndices.")
        return df
    except Exception as e:
        print("Error building DataFrame from NiftyIndices:", e)
        # fallback: try to create DataFrame with generic columns
        df = pd.DataFrame(rows)
        return df

def try_wikipedia():
    """Parse Wikipedia NIFTY 50 page as a last resort."""
    print("Trying Wikipedia fallback:", WIKIPEDIA_URL)
    resp = requests.get(WIKIPEDIA_URL, headers=HEADERS, timeout=15)
    if resp.status_code != 200:
        print("Wikipedia fetch failed with status", resp.status_code)
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    # Find the table that likely contains constituents (search for 'Constituents' or similar)
    tables = soup.find_all("table", {"class": "wikitable"})
    for table in tables:
        # Basic heuristic: table has 50+ rows or header contains 'Company' or 'Symbol'
        text = table.get_text().lower()
        if "company" in text or "symbol" in text or len(table.find_all("tr")) >= 50:
            # parse this table
            rows = []
            headers = [th.get_text(strip=True) for th in table.find_all("th")]
            for tr in table.find_all("tr"):
                cols = [td.get_text(strip=True) for td in tr.find_all("td")]
                if cols:
                    rows.append(cols)
            if rows:
                try:
                    df = pd.DataFrame(rows, columns=headers[: len(rows[0])])
                    print("Parsed constituents from Wikipedia.")
                    return df
                except Exception:
                    return pd.DataFrame(rows)
    print("No suitable table found on Wikipedia.")
    return None

def main():
    session = requests.Session()
    session.headers.update(HEADERS)

    # 1) Try official CSV from NSE
    try:
        df = try_nse_csv(session)
    except Exception as e:
        print("NSE CSV attempt raised:", e)
        df = None

    # 2) Fallback to NiftyIndices
    if df is None:
        try:
            df = try_niftyindices()
        except Exception as e:
            print("NiftyIndices attempt raised:", e)
            df = None

    # 3) Last resort: Wikipedia
    if df is None:
        try:
            df = try_wikipedia()
        except Exception as e:
            print("Wikipedia attempt raised:", e)
            df = None

    if df is None:
        print("All methods failed. Please open a browser and download manually from the NSE 'Nifty 50' page.")
        sys.exit(2)

    # Optional: do minimal cleaning: keep only first two obvious columns if table is messy
    # Try to guess useful columns
    if df.shape[1] >= 2:
        # Common columns names: Company, Symbol, Industry
        # Normalize column names if possible
        cols = [c.lower() for c in df.columns]
        # If there's a 'symbol' or 'code' column, ensure it's present
        # Save the full DataFrame anyway
    else:
        # If only one column, try to split by whitespace (best-effort)
        df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

    save_df(df, OUTFILE)
    print("Done. If you need specific columns (symbol, isin, industry), tell me and I can adapt the script.")

if __name__ == "__main__":
    main()

