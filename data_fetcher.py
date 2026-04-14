import yfinance as yf
import pandas as pd
import numpy as np

def get_market_data(ticker="USO", interval="1m", period="1d"):
    """
    Fetches intraday data for the given ticker and calculates indicators manually
    (Removing the pandas-ta dependency for maximum stability).
    """
    print(f"Fetching data for {ticker}...")
    # auto_adjust=True to avoid warnings and ensure consistent 'Close' column
    # prepost=True ensures we see Pre-Market and After-Hours price movements
    data = yf.download(ticker, period=period, interval=interval, auto_adjust=True, prepost=True)
    
    if data.empty:
        print("Error: No data fetched.")
        return None

    # Fix: yfinance 0.2.x+ often returns a MultiIndex. We flatten it.
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    # 1. EMA Calculations (Standard math)
    data['EMA_9'] = data['Close'].ewm(span=9, adjust=False).mean()
    data['EMA_21'] = data['Close'].ewm(span=21, adjust=False).mean()
    data['EMA_200'] = data['Close'].ewm(span=200, adjust=False).mean()

    # 2. RSI Calculation
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))

    # 3. VWAP Calculation (Intraday anchored)
    typical_price = (data['High'] + data['Low'] + data['Close']) / 3
    tpv = typical_price * data['Volume']
    data['VWAP'] = tpv.cumsum() / data['Volume'].cumsum()

    return data

if __name__ == "__main__":
    # Test fetch
    df = get_market_data("USO")
    if df is not None:
        last_row = df.iloc[-1]
        print("\n--- Latest Analysis for USO ---")
        # Ensure we cast to float to avoid format errors
        price = float(last_row['Close'])
        ema9 = float(last_row['EMA_9'])
        ema21 = float(last_row['EMA_21'])
        vwap = float(last_row['VWAP'])
        rsi = float(last_row['RSI'])
        
        print(f"Price: {price:.2f}")
        print(f"EMA 9: {ema9:.2f} | EMA 21: {ema21:.2f}")
        print(f"VWAP: {vwap:.2f}")
        print(f"RSI: {rsi:.2f}")
