NIFTY 50 Intraday Momentum Analyzer
This project fetches the latest NIFTY 50 stock list dynamically and performs intraday momentum analysis using live 1‑minute OHLC data from Yahoo Finance.
It identifies the Top 5 Gainers and Top 5 Losers based on percentage change from today's open price.

The project contains two Python scripts:

1. scraper.py
Dynamically fetches the latest NIFTY 50 constituents.

Tries multiple data sources (in order):
Official NSE CSV
NiftyIndices.com
Wikipedia (fallback)
Saves output to nifty50_today.csv
(Contains columns like symbol, company, etc. depending on source structure)

3. analysis.py
Reads nifty50_today.csv
Converts stock symbols into Yahoo Finance format (e.g., RELIANCE.NS)
Fetches 1‑minute intraday OHLC data for today
Computes:
Opening price
Current (latest) price
Percentage change
Volume (latest 1-minute candle)
Prints:
Top 5 Gainers
Top 5 Losers
