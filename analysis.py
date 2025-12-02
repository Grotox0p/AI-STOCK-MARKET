# analysis.py
import pandas as pd
import yfinance as yf
import time
import math
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

NIFTY_CSV = "nifty50_today.csv"

def read_symbols():
    df = pd.read_csv(NIFTY_CSV)
    if "Symbol" not in df.columns:
        print("nifty50.csv missing 'Symbol' Column")
        sys.exit(1)
    symbols = df['Symbol'].astype(str).tolist()
    return symbols, df.set_index('Symbol')['Company Name'].to_dict()

def fetch_symbol_data(ticker, company_name=None):
    """
    Fetch today's 1m intraday history via yfinance.
    Returns dict: {'Symbol':..., 'Company':..., 'open':..., 'current':..., 'pct':..., 'volume':...}
    """
    # Normalize to Yahoo ticker for NSE
    if not ticker.endswith(".NS"):
        yticker = ticker + ".NS"
    else:
        yticker = ticker

    try:
        tk = yf.Ticker(yticker)
        # use period=1d, interval=1m to get today intraday
        hist = tk.history(period="1d", interval="1m", actions=False, prepost=False)
        if hist is None or hist.empty:
            return None

        # ensure sorted
        hist = hist.sort_index()
        # opening price = first row 'Open'
        open_price = float(hist['Open'].iloc[0])
        # current price = last close
        last_row = hist.iloc[-1]
        current_price = float(last_row['Close'])
        # volume for latest candle (intraday volume for that minute). If you want cumulative volume you can sum
        current_volume = int(last_row['Volume']) if not math.isnan(last_row['Volume']) else 0
        pct_change = (current_price - open_price) / open_price * 100 if open_price != 0 else 0.0

        return {
            "symbol": ticker,
            "company": company_name or "",
            "open": open_price,
            "current": current_price,
            "pct": round(pct_change, 4),
            "volume": current_volume
        }
    except Exception as e:
        # handle per-symbol errors gracefully
        # print(f"Error fetching {yticker}: {e}")
        return None

def main():
    symbols, company_map = read_symbols()
    results = []

    # We'll use limited concurrency to avoid triggering remote throttling
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(fetch_symbol_data, s, company_map.get(s, "")): s for s in symbols}
        for fut in as_completed(futures):
            res = fut.result()
            if res:
                results.append(res)
            # small sleep not strictly necessary with ThreadPool but OK
            time.sleep(0.05)

    if not results:
        print("No data fetched. Exiting.")
        sys.exit(1)

    df = pd.DataFrame(results)
    # remove any NaNs
    df = df.dropna(subset=["pct"])

    # sort by percentage change
    gainers = df.sort_values("pct", ascending=False).head(5)
    losers = df.sort_values("pct", ascending=True).head(5)

    # print formatted output
    print("\nTop 5 Gainers:")
    for i, row in enumerate(gainers.itertuples(), 1):
        print(f"Stock {i}: {row.symbol} ({row.company}) - {row.pct}% - Volume: {row.volume}")

    print("\nTop 5 Losers:")
    for i, row in enumerate(losers.itertuples(), 1):
        print(f"Stock {i}: {row.symbol} ({row.company}) - {row.pct}% - Volume: {row.volume}")

if __name__ == "__main__":
    main()
