from flask import Flask, render_template, request, jsonify
from data_fetcher import get_market_data
from sentiment import get_ticker_sentiment
from ai_brain import analyze_market_conditions
import os
import traceback
import math
from config import GEMINI_API_KEYS, SERVER_PORT

app = Flask(__name__)

# Verify API Keys on Start
if not GEMINI_API_KEYS:
    print("WARNING: No GEMINI_API_KEYS found in config.py or api_keys.py!")

def get_social_sentiment(ticker):
    if ticker == "USO":
        return "X Sentiment: Extremely Bearish. Retailers betting against the surge in oil prices."
    return "X Sentiment: Neutral/Mixed."

def safe_float(val):
    """Helper to convert NumPy/Pandas values to JSON-safe floats."""
    try:
        f_val = float(val)
        if math.isnan(f_val) or math.isinf(f_val):
            return 0.0
        return f_val
    except:
        return 0.0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    return "OK", 200

@app.route('/analyze', methods=['POST'])
def analyze():
    ticker = "USO"
    try:
        data = request.json
        ticker = data.get('symbol', 'USO').strip().upper()
        lang = data.get('lang', 'Hinglish')
        
        try:
            buy_price = float(data.get('buy_price') or 0)
            quantity = float(data.get('quantity') or 0)
        except:
            buy_price = 0
            quantity = 0

        print(f"--- ANALYZING: {ticker} ({lang}) ---")
        
        df = get_market_data(ticker)
        if df is None or df.empty:
            return jsonify({"error": f"Symbol '{ticker}' not found."}), 404
            
        last_row = df.iloc[-1]
        current_price = safe_float(last_row['Close'])
        
        indicators = {
            "EMA_9": round(safe_float(last_row['EMA_9']), 3),
            "EMA_21": round(safe_float(last_row['EMA_21']), 3),
            "EMA_200": round(safe_float(last_row['EMA_200']), 3),
            "RSI": round(safe_float(last_row['RSI']), 2),
            "VWAP": round(safe_float(last_row['VWAP']), 3)
        }
        
        news_headlines = get_ticker_sentiment(ticker)
        news_summaries = "\n".join([f"- {n['title']}" for n in news_headlines[:3]])
        social_sentiment = get_social_sentiment(ticker)

        analysis = analyze_market_conditions(ticker, current_price, indicators, news_summaries, buy_price, quantity, social_sentiment, lang)
        
        pnl_val = 0
        if buy_price > 0:
            pnl_val = ((current_price - buy_price) / buy_price) * 100

        return jsonify({
            "ticker": ticker,
            "price": f"{current_price:.2f}",
            "time": last_row.name.strftime('%Y-%m-%d %H:%M'),
            "pnl": f"{pnl_val:+.2f}%",
            "social_pulse": social_sentiment,
            "analysis": analysis,
            "news": (news_headlines or [])[:5],
            "indicators": indicators
        })
        
    except Exception as e:
        print(f"!!! CRITICAL SERVER ERROR FOR {ticker} !!!")
        traceback.print_exc()
        return jsonify({"error": f"Internal System Error: {str(e)}"}), 500

if __name__ == '__main__':
    # For local testing
    app.run(debug=True, host='0.0.0.0', port=SERVER_PORT)
