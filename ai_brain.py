from google import genai
from config import GEMINI_API_KEYS

def analyze_market_conditions(ticker, current_price, indicators, news, buy_price=0, quantity=0, social_sentiment="", lang="Hinglish"):
    """
    V3 Logic: Structured Tags, Predictive Analysis, and Social Pulse integration.
    Supports multiple languages: Hinglish, English, Hindi, Tamil, Malayalam.
    Uses the new google-genai SDK.
    """
    valid_keys = [k for k in GEMINI_API_KEYS if k and k.strip()]
    if not valid_keys:
        return "ERROR: Missing Gemini API Keys. Set them in config.py."

    position_info = ""
    if buy_price > 0:
        pnl = ((current_price - buy_price) / buy_price) * 100
        position_info = f"User position: Buy at {buy_price}, Qty {quantity}, PnL {pnl:.2f}%."

    prompt = (
        f"You are a professional Intraday AI Trading Strategist. Language: {lang}. "
        f"If Hinglish, use funny Hindi-English mix slang. "
        f"MANDATORY: You MUST include these 3 tags in your response: "
        f"[ACTION: STRONG_BUY/BUY/HOLD/SELL/STRONG_SELL/BOOK_PROFIT], "
        f"[FUNNY_SIGNAL: a creative localized one-liner about the action], "
        f"[MANTRA: a funny loading message for next time]. "
        f"After tags, structure your response as follows EXCLUSIVELY: "
        f"### MARKET MOOD: [Short insight] "
        f"### INTRADAY PREDICTION: [Price levels] "
        f"### ANALYSIS RATIONALE: "
        f"1. RATIONALE: [Main reasoning] "
        f"2. [Point 2] "
        f"3. [Point 3] "
        f"4. [Point 4] "
        f"### FINAL STRATEGIC ADVICE: [One clear, bold closing advice line] "
        f"IMPORTANT: No extra newlines after '###' or '1.'. "
        f"Ticker: {ticker}, Price: {current_price}. "
        f"Indicators: EMA9={indicators.get('EMA_9')}, EMA21={indicators.get('EMA_21')}, "
        f"EMA200={indicators.get('EMA_200')}, RSI={indicators.get('RSI')}, VWAP={indicators.get('VWAP')}. "
        f"Social Sentiment: {social_sentiment}. {position_info}"
    )

    # Models to try (ordered by preference).
    # Using confirmed names from the environment's models.list()
    models_to_try = [
        'gemini-2.0-flash', 
        'gemini-2.5-flash',
        'gemini-3-flash-preview',
        'gemini-flash-latest'
    ]

    for api_key in valid_keys:
        client = genai.Client(api_key=api_key)
        
        for model_name in models_to_try:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                if response and response.text:
                    return response.text
            except Exception as e:
                error_str = str(e).upper()
                print(f"[Key {api_key[:6]}...] Model {model_name} failed: {str(e)}")
                
                # If this specific key is exhausted for this model, try the NEXT model for the same key
                if 'RESOURCE_EXHAUSTED' in error_str or '429' in error_str:
                    print(f"-> Key {api_key[:6]} limit reached for {model_name}. Trying next model/key.")
                    continue 
                
                if 'NOT_FOUND' in error_str or 'NOT FOUND' in error_str:
                    # Model might not be available for this specific key
                    continue
                
                # For other errors, we might still want to try the next model or next key
                continue

    # If we get here, ALL keys and models failed
    return (
        "[ACTION: HOLD] "
        "[FUNNY_SIGNAL: Bhai sab API keys ki limit khatam ho gayi aaj!] "
        "[MANTRA: Free tier ka limit ghabra gaya...] "
        "⚠️ All provided Gemini API keys have exhausted their quota. "
        "Update the keys in config.py or wait for the daily quota reset."
    )
