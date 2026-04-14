import yfinance as yf

def get_ticker_sentiment(ticker="USO"):
    """
    Fetches the latest news headlines for the given ticker from Yahoo Finance.
    """
    print(f"Fetching news sentiment for {ticker}...")
    t = yf.Ticker(ticker)
    news = t.news
    
    headlines = []
    if news:
        for item in news[:5]: # Take top 5 news items
            headlines.append({
                "title": item.get("title"),
                "publisher": item.get("publisher"),
                "summary": item.get("summary", "No summary available")
            })
    
    return headlines

if __name__ == "__main__":
    # Test fetch
    news_items = get_ticker_sentiment("USO")
    for news in news_items:
        print(f"\n- {news['title']} ({news['publisher']})")
