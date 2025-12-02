NIFTY 50 Intraday Momentum Analyzer
This project fetches the latest NIFTY 50 stock list dynamically and performs intraday momentum analysis using live 1‑minute OHLC data from Yahoo Finance.
It identifies the Top 5 Gainers and Top 5 Losers based on percentage change from today's open price.

The project contains two Python scripts:

scraper.py dynamically fetches the latest NIFTY 50 constituents. It attempts to retrieve the data from multiple sources in order: the official NSE CSV, NiftyIndices.com, and Wikipedia as a fallback. The script saves the result to nifty50_today.csv, which contains columns such as symbol, company name, and others depending on the structure of the source.

analysis.py reads the nifty50_today.csv file and converts each stock symbol into the Yahoo Finance format (for example, RELIANCE.NS). It then fetches today's 1-minute intraday OHLC data and computes the opening price, the latest price, the percentage change, and the volume of the most recent 1-minute candle. Finally, it prints the Top 5 gainers and the Top 5 losers.

MY Output
<img width="850" height="372" alt="Screenshot 2025-12-02 162410" src="https://github.com/user-attachments/assets/0e57af78-904e-4e01-9b0c-b8821ffea3ef" />
