import yfinance as yf

def get_ticker_sentiment(ticker="USO"):
    """
    Fetches the latest news headlines for the given ticker from Yahoo Finance,
    falling back to Google News RSS if empty.
    """
    print(f"Fetching news sentiment for {ticker}...")
    headlines = []
    try:
        t = yf.Ticker(ticker)
        news = t.news
        if news:
            for item in news[:5]:
                title = item.get("title", "").strip()
                if not title:
                    continue  # Skip corrupt/empty items
                    
                sent = "neutral"
                lower_title = title.lower()
                if any(w in lower_title for w in ["up", "surge", "gain", "rise", "bull", "buy", "profit"]): sent = "bullish"
                elif any(w in lower_title for w in ["down", "tumble", "drop", "fall", "bear", "sell", "loss", "crash"]): sent = "bearish"
                
                headlines.append({
                    "title": title,
                    "publisher": item.get("publisher", "Yahoo Finance"),
                    "link": item.get("link", f"https://finance.yahoo.com/quote/{ticker}"),
                    "sentiment": sent
                })
    except Exception as e:
        print(f"yFinance news failed: {e}")

    # Fallback to Google News RSS if Yahoo returned blanks
    if not headlines:
        try:
            import requests
            import xml.etree.ElementTree as ET
            url = f"https://news.google.com/rss/search?q={ticker}+stock+market+news&hl=en-US&gl=US&ceid=US:en"
            res = requests.get(url, timeout=5)
            if res.ok:
                root = ET.fromstring(res.text)
                items = root.findall('.//item')
                for item in items[:5]:
                    title_elem = item.find('title')
                    if title_elem is None or not title_elem.text.strip():
                        continue
                    
                    title = title_elem.text.strip()
                    source_elem = item.find('source')
                    source = source_elem.text if source_elem is not None else "Google News"
                    link_elem = item.find('link')
                    link = link_elem.text if link_elem is not None else ""
                    
                    sent = "neutral"
                    lower_title = title.lower()
                    if any(w in lower_title for w in ["up", "surge", "gain", "rise", "bull", "buy", "profit"]): sent = "bullish"
                    elif any(w in lower_title for w in ["down", "tumble", "drop", "fall", "bear", "sell", "loss", "crash"]): sent = "bearish"
                    
                    headlines.append({
                        "title": title,
                        "publisher": source,
                        "link": link,
                        "sentiment": sent
                    })
        except Exception as e:
            print(f"Google News fallback failed: {e}")
            
    return headlines

def get_ticker_news(ticker):
    """
    Fetches raw headlines specifically for a SINGLE ticker/company.
    Ensures the AI doesn't mix up global news with the target stock.
    """
    import requests
    import xml.etree.ElementTree as ET
    
    print(f"DEBUG: Isolating Intel for Ticker: {ticker}...")
    headlines = []
    try:
        # Search Google News specifically for this ticker
        url = f"https://news.google.com/rss/search?q={ticker}+stock+market+news&hl=en-US&gl=US&ceid=US:en"
        res = requests.get(url, timeout=5)
        if res.ok:
            root = ET.fromstring(res.text)
            items = root.findall('.//item')
            for item in items[:5]: # Max 5 specific headlines
                headlines.append(item.find('title').text)
    except Exception as e:
        print(f"ticker news failed for {ticker}: {e}")
        
    return " | ".join(headlines) if headlines else "No recent headlines found for this specific ticker."

def get_global_news(market="Both"):
    """
    Fetches hot breaking news via High-Velocity RSS for maximum speed and zero hangs.
    """
    import requests
    import xml.etree.ElementTree as ET
    
    print(f"--- INITIATING HIGH-SPEED RSS SYNC ({market.upper()}) ---")
    
    queries = []
    if market == "Both": queries = ["S&P 500 Market", "Nifty 50 News"]
    elif market == "India": queries = ["Nifty 50", "Sensex Market"]
    elif market == "US": queries = ["Nasdaq 100", "S&P 500"]

    headlines = []
    # Set localization for Google News RSS
    geo_params = "&hl=en-US&gl=US&ceid=US:en"
    if market == "India":
        geo_params = "&hl=en-IN&gl=IN&ceid=IN:en"

    for q in queries:
        try:
            print(f"DEBUG: Tapping RSS for '{q}'...")
            url = f"https://news.google.com/rss/search?q={q.replace(' ', '+')}{geo_params}"
            res = requests.get(url, timeout=5)
            if res.ok:
                root = ET.fromstring(res.text)
                items = root.findall('.//item')
                for item in items[:3]:
                    pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
                    # Simple date formatting if needed, or just pass raw RSS date
                    headlines.append({
                        "title": item.find('title').text,
                        "link": item.find('link').text,
                        "publisher": item.find('source').text if item.find('source') is not None else "NEWS",
                        "source": q,
                        "timestamp": pub_date
                    })
        except Exception as e:
            print(f"CRITICAL: RSS Tap failed for {q}: {e}")
            continue

    print(f"--- RSS SYNC COMPLETE: {len(headlines)} HEADLINES ---")
    return headlines

import datetime
import random

def get_expanded_news(topics):
    """
    Simulates checking multiple 'X' related topics by fetching news/context for each.
    'topics' is now a list of dicts: [{'topic': '...', 'sentiment': '...'}]
    """
    results = []
    current_time = datetime.datetime.now()
    
    for item in topics[:6]:
        # Handle both list of dicts and list of strings
        if isinstance(item, dict):
            topic = item.get('topic', 'Market Update')
            predicted_sentiment = item.get('sentiment', 'neutral').lower()
        else:
            topic = str(item)
            predicted_sentiment = "neutral"
        
        print(f"Checking Pulse for: {topic}...")
        offset = random.randint(5, 120) 
        ts = (current_time - datetime.timedelta(minutes=offset)).strftime("%b %d, %H:%M")
        
        try:
            link = f"https://x.com/search?q={topic.replace(' ', '%20')}"
            
            # Content generation based on sentiment to avoid inconsistency
            if predicted_sentiment == "bullish":
                content = f"X discussions show strong accumulation for {topic}. Institutional interest peaking."
            elif predicted_sentiment == "bearish":
                content = f"Caution advised for {topic}. Negative volume spikes and bearish signals on X."
            else:
                content = f"Monitoring global X trends for '{topic}'. Stabilizing volume with neutral outlook."

            # If topic looks like a ticker, try yfinance
            if len(topic) <= 5 and topic.isupper():
                news = get_ticker_sentiment(topic)
                if news:
                    # Use yfinance news but Gemini sentiment check
                    results.append({"topic": topic, "content": news[0]['title'], "type": "TICKER", "time": ts, "link": news[0]['link'], "sentiment": news[0]['sentiment']})
                else:
                    results.append({"topic": topic, "content": content, "type": "DISCUSSION", "time": ts, "link": link, "sentiment": predicted_sentiment})
            else:
                results.append({"topic": topic, "content": content, "type": "EVENT", "time": ts, "link": link, "sentiment": predicted_sentiment})
        except:
             continue
    return results

if __name__ == "__main__":
    # Test fetch
    news_items = get_ticker_sentiment("USO")
    for news in news_items:
        print(f"\n- {news['title']} ({news['publisher']})")
