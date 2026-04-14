import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from ai_brain import analyze_market_conditions
import config

def diagnostic():
    print(f"Loaded config.GEMINI_API_KEYS: {len(config.GEMINI_API_KEYS)} keys found.")
    for i, k in enumerate(config.GEMINI_API_KEYS):
        print(f"Key {i+1}: {k[:6]}...{k[-4:]}")

    # Mock data
    ticker = "USO"
    price = 70.0
    indicators = {"EMA_9": 69, "EMA_21": 68, "EMA_200": 65, "RSI": 45, "VWAP": 68.5}
    news = "Oil prices steady as demand rises."
    
    print("\nAttempting AI analysis...")
    try:
        result = analyze_market_conditions(ticker, price, indicators, news)
        print("\n--- FINAL RESULT ---")
        # Ensure we can print UTF-8 characters on Windows console
        sys.stdout.buffer.write(result.encode('utf-8'))
        sys.stdout.write('\n')
    except Exception as e:
        print(f"\n[DIAGNOSTIC CRASH]: {e}")

if __name__ == "__main__":
    diagnostic()
