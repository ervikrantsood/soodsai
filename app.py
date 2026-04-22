from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from authlib.integrations.flask_client import OAuth
from authlib.common.security import generate_token
from data_fetcher import get_market_data, get_fundamentals
from sentiment import get_ticker_sentiment, get_expanded_news
from ai_brain import analyze_market_conditions, get_related_topics, ask_ai_chat, get_ai_recommendations, generate_diversified_portfolio
import yfinance as yf
import os
import traceback
import math
import requests
import sqlite3
from datetime import datetime, timedelta
import re
from config import GEMINI_API_KEYS, SERVER_PORT

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "sood_ai_ultra_secret_888")
app.permanent_session_lifetime = timedelta(days=30)

# Global Telemetry for Admin
AI_CALL_COUNT = 0

@app.route('/admin/api_stats')
@login_required
def api_stats():
    if current_user.id != 'admin@soodsai.com':
        return jsonify({"error": "Unauthorized"}), 403
    return jsonify({
        "calls_made": AI_CALL_COUNT,
        "daily_limit": 1500 * len(GEMINI_API_KEYS), # Estimate
        "keys_mounted": len(GEMINI_API_KEYS)
    })

# Token Protection: Local Keyword filter to save AI tokens
FINANCIAL_KEYWORDS = [
    'stock', 'market', 'price', 'nifty', 'crypto', 'bitcoin', 'share', 'buy', 'sell', 
    'trade', 'bull', 'bear', 'profit', 'loss', 'portfolio', 'invest', 'ticker', 
    'dividend', 'ipo', 'nasdaq', 'sensex', 'bank', 'economy', 'finance', 'exit', 'entry'
]

def is_financial_query(text):
    if re.search(r'\b[A-Z]{2,6}\b', text): return True
    lowered = text.lower()
    for word in FINANCIAL_KEYWORDS:
        if re.search(r'\b' + re.escape(word) + r'\b', lowered): return True
    return False

# Database Initialization
def init_db():
    conn = sqlite3.connect('sood_ai.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS logs 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, ticker TEXT, strategy TEXT, timestamp DATETIME)''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_meta
                 (user_id TEXT PRIMARY KEY, last_ticker TEXT, favorite_stocks TEXT, 
                  market_preference TEXT DEFAULT 'Both', 
                  ribbon_speed TEXT DEFAULT '80s')''')
    c.execute('''CREATE TABLE IF NOT EXISTS global_configs 
                 (key TEXT PRIMARY KEY, value TEXT)''')
    c.execute("INSERT OR IGNORE INTO global_configs (key, value) VALUES ('terminal_layout', 'left-volatility-portal,main-terminal-area,home-news-portal')")
    
    try: c.execute("ALTER TABLE user_meta ADD COLUMN market_preference TEXT DEFAULT 'Both'")
    except: pass
    try: c.execute("ALTER TABLE user_meta ADD COLUMN ribbon_speed TEXT DEFAULT '80s'")
    except: pass
    
    conn.commit()
    conn.close()

init_db()

# Authentication Setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for('login'))

# OAuth Setup
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID', ''),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET', ''),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)

local_users = {
    "admin@soodsai.com": {"password": "admin", "name": "Kingpin Admin"}
}

class User(UserMixin):
    def __init__(self, id, name, market_preference="Both", ribbon_speed="80s"):
        self.id = id
        self.name = name
        self.market_preference = market_preference
        self.ribbon_speed = ribbon_speed

@login_manager.user_loader
def load_user(user_id):
    if user_id in local_users:
        conn = sqlite3.connect('sood_ai.db')
        c = conn.cursor()
        c.execute("SELECT market_preference, ribbon_speed FROM user_meta WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        pref = row[0] if row else "Both"
        speed = row[1] if row and row[1] else "80s"
        conn.close()
        return User(user_id, local_users[user_id].get("name", "User"), market_preference=pref, ribbon_speed=speed)
    return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if email in local_users and local_users[email]['password'] == password:
            user = load_user(email)
            session.permanent = True
            login_user(user, remember=True)
            return redirect(url_for('index'))
        return redirect(url_for('login', error="Invalid credentials."))
    return render_template('auth.html')

@app.route('/signup', methods=['POST'])
def signup():
    email = request.form.get('email')
    password = request.form.get('password')
    name = request.form.get('name')
    if email in local_users: return redirect(url_for('login', error="User already exists."))
    local_users[email] = {"password": password, "name": name}
    user = User(email, name)
    session.permanent = True
    login_user(user, remember=True)
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/login/google')
def login_google():
    redirect_uri = url_for('authorize_google', _external=True)
    try: return google.authorize_redirect(redirect_uri)
    except: return redirect(url_for('login', error="Google Auth failed."))

@app.route('/authorize/google')
def authorize_google():
    token = google.authorize_access_token()
    user_info = google.parse_id_token(token, None)
    email = user_info['email']
    name = user_info.get('name', 'Trader')
    if email not in local_users: local_users[email] = {"password": "OAUTH_LOGIN", "name": name}
    user = load_user(email)
    session.permanent = True
    login_user(user, remember=True)
    return redirect(url_for('index'))

def safe_float(val):
    try:
        f_val = float(val)
        if math.isnan(f_val) or math.isinf(f_val): return 0.0
        return f_val
    except: return 0.0

@app.route('/')
@login_required
def index():
    last_ticker = ""
    return render_template('index.html', user=current_user)

@app.route('/suggest', methods=['GET'])
@login_required
def suggest():
    q = request.args.get('q', '').strip()
    if not q or len(q) < 2: return jsonify([])
    try:
        # Using a fast heuristic search for common tickers
        import yfinance as yf
        results = yf.Search(q, max_results=8).quotes
        matches = []
        for r in results:
            sym = r.get('symbol')
            name = r.get('shortname') or r.get('longname') or sym
            if sym: matches.append({"symbol": sym, "name": name})
        return jsonify(matches)
    except: return jsonify([])

@app.route('/fetch_raw_data', methods=['POST'])
@login_required
def fetch_raw_data():
    try:
        data = request.json
        ticker = data.get('symbol', 'BTC-USD').upper()
        perspective = data.get('perspective', 'Retail')
        df, currency = get_market_data(ticker, perspective)
        if df is None or df.empty: return jsonify({"error": f"Symbol '{ticker}' not found."}), 404
        last_row = df.iloc[-1]
        current_price = safe_float(last_row['Close'])
        prev_close = safe_float(df.iloc[-2]['Close']) if len(df) > 1 else current_price
        change_pct = ((current_price - prev_close) / prev_close) * 100 if prev_close else 0
        
        fundamentals = get_fundamentals(ticker)
        indicators = {
            "EMA_9": round(safe_float(last_row['EMA_9']), 3),
            "EMA_21": round(safe_float(last_row['EMA_21']), 3),
            "EMA_200": round(safe_float(last_row['EMA_200']), 3),
            "RSI": round(safe_float(last_row['RSI']), 2),
            "VWAP": round(safe_float(last_row['VWAP']), 3)
        }
        news_headlines = get_ticker_sentiment(ticker)
        news_summaries = "\n".join([f"- {n['title']}" for n in news_headlines[:3]])
        from data_fetcher import calculate_soods_signals
        signals = calculate_soods_signals(df)
        
        return jsonify({
            "ticker": ticker, 
            "price": f"{current_price:.2f}", 
            "prev_close": f"{prev_close:.2f}",
            "change_pct": round(change_pct, 2),
            "currency": currency,
            "time": last_row.name.strftime('%Y-%m-%d %H:%M'), "indicators": indicators,
            "fundamentals": fundamentals, "news": (news_headlines or [])[:5],
            "news_summaries": news_summaries,
            "signals": signals
        })
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/analyze', methods=['POST'])
@login_required
def analyze():
    try:
        data = request.json
        ticker = data.get('symbol', 'USO').strip().upper()
        lang = data.get('lang', 'Hinglish')
        perspective = data.get('perspective', 'Intraday')
        strategy_mode = data.get('strategy_mode', 'Exit')
        buy_price = safe_float(data.get('buy_price'))
        quantity = safe_float(data.get('quantity'))
        capital = data.get('capital', 0)
        risk = data.get('risk', 'Moderate')
        duration = data.get('duration', 'Intraday (1 Day)')

        try:
            conn = sqlite3.connect('sood_ai.db')
            c = conn.cursor()
            c.execute("INSERT INTO logs (user_id, ticker, strategy, timestamp) VALUES (?, ?, ?, ?)", 
                      (current_user.id, ticker, strategy_mode, datetime.now()))
            c.execute("INSERT OR REPLACE INTO user_meta (user_id, last_ticker) VALUES (?, ?)", 
                      (current_user.id, ticker))
            c.execute("SELECT ticker FROM logs WHERE user_id = ? ORDER BY timestamp DESC LIMIT 5", (current_user.id,))
            history = [r[0] for r in c.fetchall()]
            conn.commit(); conn.close()
            user_history_context = f"User's recent history: {', '.join(history)}"
        except: user_history_context = ""
        
        df, currency = get_market_data(ticker, perspective)
        if df is None or df.empty: return jsonify({"error": f"Symbol '{ticker}' not found."}), 404
            
        last_row = df.iloc[-1]
        current_price = safe_float(last_row['Close'])
        fundamentals = get_fundamentals(ticker)
        indicators = {
            "EMA_9": round(safe_float(last_row['EMA_9']), 3),
            "EMA_21": round(safe_float(last_row['EMA_21']), 3),
            "EMA_200": round(safe_float(last_row['EMA_200']), 3),
            "RSI": round(safe_float(last_row['RSI']), 2),
            "VWAP": round(safe_float(last_row['VWAP']), 3)
        }
        
        capital = data.get('capital', 0)
        risk = data.get('risk', 'Moderate')
        duration = data.get('duration', 'Intraday (1 Day)')
        
        news_headlines = get_ticker_sentiment(ticker)
        news_summaries = "\n".join([f"- {n['title']}" for n in news_headlines[:3]])
        related_topics = get_related_topics(ticker)
        expanded_pulse = get_expanded_news(related_topics)
        social_context = ""
        for i, pulse in enumerate(expanded_pulse):
            social_context += f"Pulse {i+1} [{pulse['sentiment']}]: {pulse['content']} "
        social_context += "Related checks: " + ", ".join([f"{e['topic']}: {e['content']}" for e in expanded_pulse])
        
        const_query = data.get('query', '')
        final_social_context = f"Question: {const_query}\n{social_context}\n{user_history_context}"

        analysis = analyze_market_conditions(
            ticker, current_price, indicators, news_summaries, 
            buy_price, quantity, social_sentiment=final_social_context, 
            lang=lang, perspective=perspective, strategy_mode=strategy_mode, 
            fundamentals=fundamentals, capital=capital, risk=risk, duration=duration
        )
        
        pnl_val = ((current_price - buy_price) / buy_price) * 100 if buy_price > 0 else 0
        # Update Telemetry
        if "[ACTION:" in analysis:
            global AI_CALL_COUNT
            AI_CALL_COUNT += 1
            
        return jsonify({
            "ticker": ticker, "price": f"{current_price:.2f}", "currency": currency,
            "time": last_row.name.strftime('%Y-%m-%d %H:%M'), "pnl": f"{pnl_val:+.2f}%",
            "social_pulse": social_context, "expanded_pulse": expanded_pulse,
            "analysis": analysis, "news": (news_headlines or [])[:5],
            "indicators": indicators, "fundamentals": fundamentals, "strategy_mode": strategy_mode
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        ticker = data.get('symbol', 'USO')
        question = data.get('question', '')
        if not is_financial_query(question): return jsonify({"answer": "I specialize only in financial intelligence."})
        answer = ask_ai_chat(ticker, data.get('price', 0), question, data.get('indicators', {}), data.get('social_pulse', ''), data.get('lang', 'English'))
        return jsonify({"answer": answer})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/update_user_settings', methods=['POST'])
@login_required
def update_user_settings():
    try:
        data = request.json
        pref = data.get('market_preference')
        conn = sqlite3.connect('sood_ai.db')
        c = conn.cursor()
        if pref:
            current_user.market_preference = pref
            c.execute("INSERT OR REPLACE INTO user_meta (user_id, last_ticker, market_preference) VALUES (?, (SELECT last_ticker FROM user_meta WHERE user_id=?), ?)", (current_user.id, current_user.id, pref))
        conn.commit(); conn.close()
        return jsonify({"status": "success"})
    except: return jsonify({"error": "Failed"}), 500

@app.route('/generate_portfolio', methods=['POST'])
def portfolio():
    try:
        data = request.json
        picks = generate_diversified_portfolio(float(data.get('capital', 100000)), data.get('lang', 'English'), data.get('risk_level', 'Balanced'))
        results = []
        for p in picks:
            try:
                symbol = p['symbol'].upper()
                if symbol == 'CASH': curr_price = 1.0
                else:
                    t = yf.Ticker(symbol)
                    h = t.history(period="1d")
                    curr_price = float(h['Close'].iloc[-1]) if not h.empty else 0
                results.append({**p, "price": round(curr_price, 2)})
            except: results.append({**p, "price": 0})
        return jsonify(results)
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/recommendations')
@login_required
def recommendations():
    try: return jsonify(get_ai_recommendations(request.args.get('lang', 'English'), market=current_user.market_preference))
    except: return jsonify([])

@app.route('/search_ticker')
def search_ticker():
    query = request.args.get('q', '').strip()
    if len(query) < 1: return jsonify([])
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Referer': 'https://finance.yahoo.com/'
        }
        res = requests.get(f"https://query1.finance.yahoo.com/v1/finance/search?q={query}&quotesCount=10", headers=headers, timeout=5)
        suggestions = [{"symbol": q.get('symbol'), "name": q.get('shortname') or q.get('longname'), "exchange": q.get('exchDisp')} for q in res.json().get('quotes', [])]
        return jsonify(suggestions)
    except: return jsonify([])

@app.route('/global_news')
def global_news():
    try:
        from sentiment import get_global_news
        return jsonify(get_global_news(market=current_user.market_preference if current_user.is_authenticated else "Both"))
    except: return jsonify([])

@app.route('/market_snapshot')
def market_snapshot():
    try:
        from data_fetcher import get_market_snapshot
        return jsonify(get_market_snapshot(market=current_user.market_preference if current_user.is_authenticated else "Both"))
    except: return jsonify({})

@app.route('/top_movers')
def top_movers():
    try:
        from data_fetcher import get_top_movers
        return jsonify(get_top_movers(market=current_user.market_preference if current_user.is_authenticated else "Both"))
    except: return jsonify({"gainers": [], "losers": []})

@app.route('/get_global_layout')
def get_global_layout():
    try:
        conn = sqlite3.connect('sood_ai.db'); c = conn.cursor()
        c.execute("SELECT value FROM global_configs WHERE key='terminal_layout'")
        m = c.fetchone()
        c.execute("SELECT value FROM global_configs WHERE key='hub_layout'")
        h = c.fetchone()
        c.execute("SELECT value FROM global_configs WHERE key='dimensions'")
        d = c.fetchone()
        c.execute("SELECT value FROM global_configs WHERE key='sub_layout'")
        s = c.fetchone()
        c.execute("SELECT value FROM global_configs WHERE key='refresh_intervals'")
        i = c.fetchone()
        conn.close()
        return jsonify({
            "layout": m[0] if m else "left-volatility-portal,main-terminal-area,home-news-portal",
            "hub_layout": h[0] if h else "hero-section,ai-search-container,scanning-status-bar,ai-general-portal,result-section",
            "dimensions": d[0] if d else "{}",
            "sub_layout": s[0] if s else "{}",
            "refresh_intervals": i[0] if i else "{}"
        })
    except: return jsonify({"layout": "left-volatility-portal,main-terminal-area,home-news-portal", "hub_layout": "", "dimensions": "{}", "sub_layout": "{}", "refresh_intervals": "{}"})

@app.route('/update_global_layout', methods=['POST'])
@login_required
def update_global_layout():
    if current_user.id != 'admin@soodsai.com': return jsonify({"error": "Admin Required"}), 403
    data = request.json
    conn = sqlite3.connect('sood_ai.db'); c = conn.cursor()
    if data.get('layout'): c.execute("INSERT OR REPLACE INTO global_configs (key, value) VALUES ('terminal_layout', ?)", (data['layout'],))
    if data.get('hub_layout'): c.execute("INSERT OR REPLACE INTO global_configs (key, value) VALUES ('hub_layout', ?)", (data['hub_layout'],))
    if data.get('dimensions'): c.execute("INSERT OR REPLACE INTO global_configs (key, value) VALUES ('dimensions', ?)", (data['dimensions'],))
    if data.get('sub_layout'): c.execute("INSERT OR REPLACE INTO global_configs (key, value) VALUES ('sub_layout', ?)", (data['sub_layout'],))
    if data.get('refresh_intervals'): c.execute("INSERT OR REPLACE INTO global_configs (key, value) VALUES ('refresh_intervals', ?)", (data['refresh_intervals'],))
    conn.commit(); conn.close()
    return jsonify({"success": True})
@app.route('/api/pulse/social', methods=['GET'])
@login_required
def api_pulse_social():
    try:
        from ai_brain import get_related_topics
        ticker = request.args.get('ticker', 'USO')
        related_topics = get_related_topics(ticker)
        expanded_pulse = get_expanded_news(related_topics)
        return jsonify(expanded_pulse)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/live_price', methods=['GET'])
@login_required
def api_live_price():
    try:
        ticker = request.args.get('ticker', 'USO').upper()
        t = yf.Ticker(ticker)
        current_price = None
        info = t.info
        
        if info:
            current_price = info.get('currentPrice') or info.get('regularMarketPrice')
            prev_close = info.get('previousClose')
            
        if not current_price:
            fast_data = t.history(period="5d")
            if not fast_data.empty:
                current_price = float(fast_data['Close'].iloc[-1])
                prev_close = float(fast_data['Close'].iloc[-2]) if len(fast_data) > 1 else current_price
        
        if not current_price:
            return jsonify({"price": "N/A"})
            
        currency = info.get('currency', 'USD') if info else 'USD'
        curr_map = {'USD': '$', 'INR': '₹', 'EUR': '€', 'GBP': '£'}
        sym = curr_map.get(currency, currency + ' ')
        
        change_pct = 0
        if prev_close:
            change_pct = ((current_price - prev_close) / prev_close) * 100

        return jsonify({
            "price": f"{sym}{current_price:.2f}",
            "change_pct": round(change_pct, 2),
            "direction": "up" if change_pct >= 0 else "down"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/insider_trades', methods=['GET'])
@login_required
def api_insider_trades():
    try:
        ticker = request.args.get('ticker', 'AAPL').upper()
        from data_fetcher import get_insider_trades
        return jsonify(get_insider_trades(ticker))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/fear_greed', methods=['GET'])
@login_required
def api_fear_greed():
    try:
        import requests
        res = requests.get('https://api.alternative.me/fng/')
        return jsonify(res.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=SERVER_PORT)
