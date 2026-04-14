import time
import os
from data_fetcher import get_market_data
from sentiment import get_ticker_sentiment
from ai_brain import analyze_market_conditions
from dotenv import load_dotenv

load_dotenv()

def run_trading_bot(ticker="USO"):
    print(f"=== Starting AI Trading Bot for {ticker} ===")
    
    # Enter Buy Price and Quantity
    buy_price_input = input("Enter your Buy Price (Press Enter to skip): ")
    try:
        buy_price = float(buy_price_input) if buy_price_input else 0.0
    except ValueError:
        buy_price = 0.0
        print("Invalid buy price, ignoring.")

    quantity_input = input("Enter your Quantity (Press Enter to skip): ")
    try:
        quantity = float(quantity_input) if quantity_input else 0.0
    except ValueError:
        quantity = 0.0
        print("Invalid quantity, ignoring.")

    while True:
        # 1. Fetch Technical Data
        df = get_market_data(ticker)
        if df is None or len(df) < 1:
            print("Trying again in 60 seconds...")
            time.sleep(60)
            continue
            
        last_row = df.iloc[-1]
        
        # Casting to float explicitly to fix yfinance MultiIndex/Series errors
        current_price = float(last_row['Close'])
        indicators = {
            "EMA_9": round(float(last_row['EMA_9']), 3),
            "EMA_21": round(float(last_row['EMA_21']), 3),
            "EMA_200": round(float(last_row['EMA_200']), 3),
            "RSI": round(float(last_row['RSI']), 2),
            "VWAP": round(float(last_row['VWAP']), 3)
        }
        
        # 2. Fetch News Sentiment
        news_headlines = get_ticker_sentiment(ticker)
        news_summaries = "\n".join([f"- {n['title']} (Source: {n['publisher']})" for n in news_headlines])

        # 3. AI Analysis
        print("\nSending data to AI for Analysis...")
        # Now passing buy_price and quantity for personalized advice
        analysis = analyze_market_conditions(ticker, current_price, indicators, news_summaries, buy_price, quantity)
        
        # 4. Display Result
        print("\n" + "="*40)
        print(f"AI ANALYSIS FOR {ticker}")
        print(f"TIME: {last_row.name}")
        print(f"PRICE: {current_price:.2f}")
        
        if buy_price > 0:
            pnl = ((current_price - buy_price) / buy_price) * 100
            print(f"YOUR POSITION: {pnl:+.2f}% (Price: {buy_price}, Qty: {quantity})")
            
        print("-"*40)
        print(analysis)
        print("="*40)
        
        print("\nNext check in 5 minutes. (Ctrl+C to stop)")
        time.sleep(300) # Wait 5 minutes for next candle

if __name__ == "__main__":
    ticker_choice = input("Enter ticker to track (default: USO): ").upper() or "USO"
    run_trading_bot(ticker_choice)
