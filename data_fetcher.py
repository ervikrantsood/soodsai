import yfinance as yf
import pandas as pd
import numpy as np

def get_market_data(ticker="USO", perspective="Intraday"):
    """
    Fetches data based on perspective:
    - Intraday: 1d period, 1m interval
    - 1 Week: 5d period, 15m interval
    - 1 Month: 1mo period, 30m or 1d interval
    - 52 Weeks: 1y period, 1d interval
    """
    period_map = {
        "Intraday": ("1d", "1m"),
        "1 Week": ("5d", "15m"),
        "1 Month": ("1mo", "1d"),
        "52 Weeks": ("1y", "1d")
    }
    period, interval = period_map.get(perspective, ("1d", "1m"))
    
    print(f"Fetching {perspective} data for {ticker} (Period: {period}, Interval: {interval})...")
    data = yf.download(ticker, period=period, interval=interval, auto_adjust=True, prepost=True)
    
    if data.empty:
        # Fallback for tickers that might not support prepost or specific intervals
        data = yf.download(ticker, period=period, interval=interval, auto_adjust=True)
        if data.empty:
            print("Error: No data fetched.")
            return None, "$"

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    # Calculate Indicators
    data['EMA_9'] = data['Close'].ewm(span=9, adjust=False).mean()
    data['EMA_21'] = data['Close'].ewm(span=21, adjust=False).mean()
    data['EMA_200'] = data['Close'].ewm(span=200, adjust=False).mean()

    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))

    typical_price = (data['High'] + data['Low'] + data['Close']) / 3
    tpv = typical_price * data['Volume']
    # Anchored VWAP is mainly for intraday; for longer periods, we'll just use a rolling VWAP or standard Cumulative
    data['VWAP'] = tpv.cumsum() / data['Volume'].cumsum()

    # Detect Currency
    currency_symbol = "$"
    try:
        t_obj = yf.Ticker(ticker)
        curr = t_obj.info.get('currency', 'USD')
        if curr == 'INR':
            currency_symbol = "₹"
    except:
        pass

    return data, currency_symbol

def calculate_soods_signals(data):
    """
    Computes Soods-Signals (Technical Badges) based on standard math.
    Zero AI cost.
    """
    signals = []
    if data is None or data.empty or len(data) < 20: 
        return signals
    
    last = data.iloc[-1]
    
    # RSI Signals
    if 'RSI' in last:
        if last['RSI'] < 30: signals.append("RSI OVERSOLD")
        elif last['RSI'] > 70: signals.append("RSI OVERBOUGHT")
    
    # Volume Spike (Last vol > 2x Avg 20-day Vol)
    if 'Volume' in data.columns:
        avg_vol = data['Volume'].rolling(window=20).mean().iloc[-1]
        if last['Volume'] > (avg_vol * 1.5):
            signals.append("VOL SPIKE")
            
    # Momentum Cross (9 EMA crossing 21 EMA)
    if 'EMA_9' in data.columns and 'EMA_21' in data.columns:
        prev = data.iloc[-2]
        if prev['EMA_9'] <= prev['EMA_21'] and last['EMA_9'] > last['EMA_21']:
            signals.append("GOLDEN CROSS")
        elif prev['EMA_9'] >= prev['EMA_21'] and last['EMA_9'] < last['EMA_21']:
            signals.append("BEAR DROP")

    return signals

def get_fundamentals(ticker):
    """
    Fetches key fundamental metrics for a given ticker.
    """
    try:
        t_obj = yf.Ticker(ticker)
        info = t_obj.info
        
        # Extract specific relevant fields
        fundamentals = {
            "Market Cap": info.get('marketCap'),
            "P/E Ratio": info.get('trailingPE'),
            "Forward P/E": info.get('forwardPE'),
            "EPS": info.get('trailingEps'),
            "Revenue Growth": info.get('revenueGrowth'),
            "Profit Margin": info.get('profitMargins'),
            "Dividend Yield": info.get('dividendYield'),
            "Dividend Rate": info.get('dividendRate'),
            "52-Week High": info.get('fiftyTwoWeekHigh'),
            "52-Week Low": info.get('fiftyTwoWeekLow'),
            "Sector": info.get('sector'),
            "Industry": info.get('industry'),
            "Volume": info.get('volume'),
            "Avg Vol": info.get('averageVolume'),
            "Beta": info.get('beta')
        }
        return fundamentals
    except Exception as e:
        print(f"Error fetching fundamentals for {ticker}: {e}")
        return None

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

def get_market_snapshot(market="Both"):
    """
    Returns current live price and % change for major global indices based on MARKET preference.
    """
    all_indices = {
        "NIFTY 50": "^NSEI",
        "SENSEX": "^BSESN",
        "NASDAQ": "^IXIC",
        "S&P 500": "^GSPC",
        "GOLD": "GC=F"
    }
    
    # Filter targets based on user preference
    targets = {}
    if market == "Both": targets = all_indices
    elif market == "India": targets = {"NIFTY 50": "^NSEI", "SENSEX": "^BSESN", "GOLD": "GC=F"}
    elif market == "US": targets = {"NASDAQ": "^IXIC", "S&P 500": "^GSPC", "GOLD": "GC=F"}

    results = {}
    for name, sym in targets.items():
        try:
            t = yf.Ticker(sym)
            h = t.history(period="2d")
            if not h.empty:
                last_price = h['Close'].iloc[-1]
                prev_price = h['Close'].iloc[-2]
                change = ((last_price - prev_price) / prev_price) * 100
                results[name] = {
                    "price": f"{last_price:,.2f}",
                    "change": f"{change:+.2f}%",
                    "sentiment": "bull" if change >= 0 else "bear"
                }
        except: continue
    return results

def get_top_movers(market="Both"):
    """
    Fetches Top Gainers and Losers using 0 AI TOKENS.
    Optimized for high-speed batch delivery.
    """
    import yfinance as yf
    us_tickers = ["AAPL", "NVDA", "TSLA", "MSFT", "AMD", "META", "AMZN", "GOOGL", "NFLX", "COIN"]
    in_tickers = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", "SBIN.NS", "TATAMOTORS.NS", "ADANIENT.NS", "ZOMATO.NS", "ITC.NS"]
    
    selected = []
    if market == "Both": selected = us_tickers + in_tickers
    elif market == "India": selected = in_tickers
    elif market == "US": selected = us_tickers

    try:
        data = yf.download(selected, period="1mo", interval="1h", group_by="ticker", progress=False, threads=True)
        movers = []
        for ticker in selected:
            try:
                hist = data[ticker].dropna(subset=['Close'])
                if hist.empty: continue
                
                # Basic Indicators for signals
                hist['EMA_9'] = hist['Close'].ewm(span=9, adjust=False).mean()
                hist['EMA_21'] = hist['Close'].ewm(span=21, adjust=False).mean()
                delta = hist['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                # Basic check for div by zero?
                hist['RSI'] = 100 - (100 / (1 + rs))
                
                signals = calculate_soods_signals(hist)
                
                current_price = hist['Close'].iloc[-1]
                # changepct based on the download period? No, let's just use regular regular day change if possible.
                # Since we have 1mo, hist['Close'].iloc[0] is 1mo ago.
                # Let's use last vs prev row for a 1-hour change? Or fetch more and find day start?
                # For top movers, typically we want Day Change.
                # Let's use 2 days and check first close.
                day_start_price = hist['Close'].iloc[-2] if len(hist) > 1 else hist['Close'].iloc[0]
                change_pct = ((current_price - day_start_price) / day_start_price) * 100

                movers.append({
                    "symbol": ticker.replace(".NS", ""),
                    "price": round(current_price, 2),
                    "change": round(change_pct, 2),
                    "signals": signals[:2]
                })
            except: continue
        
        sorted_movers = sorted(movers, key=lambda x: x['change'], reverse=True)
        return {
            "gainers": sorted_movers[:5],
            "losers": sorted_movers[-5:][::-1]
        }
    except Exception as e:
        print(f"Movers Sync Failure: {e}")
        return {"gainers": [], "losers": []}
def get_insider_trades(ticker):
    """
    Fetches recent insider transactions for the given ticker.
    """
    try:
        t = yf.Ticker(ticker)
        # insider_transactions is a DataFrame with Date, Shares, Value, etc.
        df = t.insider_transactions
        if df is None or df.empty:
            return []
            
        # Standardize for the frontend
        # Reset index to get the 'Date' as a column, or just access it
        df = df.sort_index(ascending=False).head(10)
        trades = []
        for index, row in df.iterrows():
            date_str = index.strftime('%Y-%m-%d') if hasattr(index, 'strftime') else str(index)
            trades.append({
                "date": date_str,
                "insider": str(row.get('Insider', 'UNKNOWN')),
                "position": str(row.get('Position', 'OFFICER')),
                "text": f"{row.get('Insider', 'Insider')} sold {int(row.get('Shares', 0)):,} shares",
                "shares": int(row.get('Shares', 0)),
                "value": f"${float(row.get('Value', 0)):,.0f}",
                "type": "Sale" if str(row.get('Text', '')).lower().find('sale') != -1 else "Buy"
            })
        return trades
    except Exception as e:
        print(f"Insider Fetch Failure for {ticker}: {e}")
        return []
