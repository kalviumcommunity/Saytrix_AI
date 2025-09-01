from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import os
from dotenv import load_dotenv
from functions import execute_function, get_stock_context
from database import db
from auth import auth_manager, require_auth
from cost_monitor import cost_monitor
import logging
import uuid
import re

# Enhanced Gemini Integration
try:
    import google.generativeai as genai
    
    class EnhancedGeminiChat:
        def __init__(self):
            api_key = os.getenv('GEMINI_API_KEY')
            if api_key:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                self.available = True
            else:
                self.available = False
        
        def get_response(self, message: str, stock_data: dict = None) -> str:
            if not self.available:
                return self._fallback_response(message, stock_data)
            
            try:
                system_prompt = f"""You are Saytrix AI, a financial assistant. STRICT RULES:
1. ONLY use data provided below - NEVER invent numbers
2. If data missing, say "Data not available"
3. Be helpful but factual only
4. Format responses professionally

USER MESSAGE: {message}

PROVIDED DATA: {self._format_data(stock_data) if stock_data else 'No stock data provided'}

Respond helpfully using ONLY the provided information:"""

                response = self.model.generate_content(system_prompt)
                return response.text
            except Exception as e:
                logging.error(f"Gemini error: {e}")
                return self._fallback_response(message, stock_data)
        
        def _format_data(self, data: dict) -> str:
            if not data or 'error' in data:
                return "No valid stock data"
            return f"Symbol: {data.get('symbol')}, Price: ₹{data.get('current_price')}, High: ₹{data.get('high')}, Low: ₹{data.get('low')}, Volume: {data.get('volume')}"
        
        def _fallback_response(self, message: str, stock_data: dict = None) -> str:
            words = set(re.findall(r'\b\w+\b', message.lower()))
            
            if stock_data and 'error' not in stock_data:
                return f"📊 **{stock_data.get('symbol')} Live Data**\n\n**Price:** ₹{stock_data.get('current_price')}\n**High:** ₹{stock_data.get('high')}\n**Low:** ₹{stock_data.get('low')}\n**Volume:** {stock_data.get('volume')}"
            
            if any(w in words for w in ['hi', 'hello', 'hey']):
                return "Hello! I'm Saytrix AI, your financial assistant. Ask me about stocks, portfolio management, or market insights!"
            
            if 'portfolio' in words:
                return "💼 Use the Portfolio Calculator in the sidebar to manage your investments and calculate P&L."
            
            if any(w in words for w in ['market', 'nifty', 'sensex']):
                return "📈 Check the live market widgets in the sidebar for current market data and trends."
            
            if any(w in words for w in ['stock', 'share', 'price']):
                return "📊 I can help you get stock prices! Try asking about specific stocks or use the sidebar tools!"
            
            return f"I can help with stock analysis, portfolio management, and market insights. Try asking about specific stocks or use the sidebar tools!"

    gemini_chat = EnhancedGeminiChat()
    
except ImportError:
    gemini_chat = None
    print("Gemini API not available - using fallback mode")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, 
     origins=['https://saytrix.netlify.app', 'http://localhost:3000'],
     supports_credentials=True,
     allow_headers=['Content-Type', 'Authorization'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
)

# Authentication Routes
@app.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    
    if not all([email, password, name]):
        return jsonify({'error': 'Email, password, and name are required'}), 400
    
    result = db.create_user(email, password, name)
    if 'error' in result:
        return jsonify(result), 400
    
    token = auth_manager.generate_token(result['user_id'])
    return jsonify({
        'message': 'Registration successful',
        'token': token,
        'user': {'user_id': result['user_id'], 'name': name, 'email': email}
    })

@app.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400
    
    user = db.authenticate_user(email, password)
    if 'error' in user:
        return jsonify(user), 401
    
    token = auth_manager.generate_token(user['user_id'])
    return jsonify({
        'message': 'Login successful',
        'token': token,
        'user': user
    })

@app.route('/auth/verify', methods=['GET'])
@require_auth
def verify_token():
    return jsonify({'valid': True, 'user_id': request.user_id})

# User session modes - using database for persistence
class UserModeManager:
    def __init__(self):
        self.modes = {}
    
    def set_mode(self, user_id, mode):
        self.modes[user_id] = mode
        try:
            db.save_user_mode(user_id, mode)
        except:
            pass
    
    def get_mode(self, user_id):
        try:
            mode = db.get_user_mode(user_id)
            if mode:
                self.modes[user_id] = mode
                return mode
        except:
            pass
        return self.modes.get(user_id, None)
    
    def clear_mode(self, user_id):
        self.modes[user_id] = None
        try:
            db.save_user_mode(user_id, None)
        except:
            pass

user_mode_manager = UserModeManager()

# Track user activity for auto-reset
user_last_activity = {}

@app.route('/chat', methods=['POST'])
@require_auth
def chat():
    data = request.get_json(force=True)
    message = data.get('message', '')
    user_id = request.user_id
    conversation_id = data.get('conversation_id') or str(uuid.uuid4())
    
    if not message:
        return jsonify({'error': 'Message is required'}), 400
    
    try:
        stock_keywords = {
            'zomato': 'ZOMATO.NS', 'reliance': 'RELIANCE.NS', 'tcs': 'TCS.NS',
            'hdfc': 'HDFCBANK.NS', 'hdfcbank': 'HDFCBANK.NS', 'infosys': 'INFY.NS', 
            'infy': 'INFY.NS', 'apple': 'AAPL', 'microsoft': 'MSFT', 'tesla': 'TSLA'
        }
        
        message_lower = message.lower()
        symbol = None
        
        words = set(re.findall(r'\b\w+\b', message_lower))
        
        for keyword, stock_symbol in stock_keywords.items():
            if keyword in words:
                symbol = stock_symbol
                break
        
        conversation_history = db.get_conversation_history(user_id, conversation_id, limit=10)
        
        db.save_message(user_id, conversation_id, 'user', message)
        
        stock_data = None
        if symbol:
            stock_data = execute_function('get_stock_price', {'symbol': symbol})
        
        try:
            if gemini_chat and gemini_chat.available:
                response_text = gemini_chat.get_response(message, stock_data)
            else:
                response_text = gemini_chat._fallback_response(message, stock_data)
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            response_text = gemini_chat._fallback_response(message, stock_data)
        
        db.save_message(user_id, conversation_id, 'ai', response_text)
        
        if symbol and stock_data and 'error' not in stock_data:
            cost_monitor.log_api_usage(user_id, 'alpha_vantage', f'/stock/{symbol}', success=True)
        elif symbol:
            cost_monitor.log_api_usage(user_id, 'alpha_vantage', f'/stock/{symbol}', success=False)
        
        return jsonify({
            'response': response_text,
            'conversation_id': conversation_id,
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id
        })
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

def detect_stock_symbol(message):
    message_upper = message.upper().strip()
    message_lower = message.lower().strip()
    
    import re
    if re.match(r'^[A-Z]{2,10}(\.NS|\.BO)?$', message_upper):
        if not message_upper.endswith(('.NS', '.BO')) and message_upper not in ['NIFTY', 'SENSEX']:
            return message_upper + '.NS'
        return message_upper
    
    stock_keywords = {
        'zomato': 'ZOMATO.NS', 'reliance': 'RELIANCE.NS', 'tcs': 'TCS.NS',
        'hdfc': 'HDFCBANK.NS', 'infosys': 'INFY.NS', 'apple': 'AAPL',
        'microsoft': 'MSFT', 'tesla': 'TSLA'
    }
    
    if message_lower in stock_keywords:
        return stock_keywords[message_lower]
    
    return message_upper if len(message_upper) >= 2 and len(message_upper) <= 10 else None

def format_stock_response(stock_data):
    if not stock_data or 'error' in stock_data:
        return "Unable to fetch stock data. Please try again."
    
    return f"📊 **{stock_data.get('symbol')} Live Data**\n\n**Price:** ₹{stock_data.get('current_price')}\n**High:** ₹{stock_data.get('high')}\n**Low:** ₹{stock_data.get('low')}\n**Volume:** {stock_data.get('volume')}"

def has_recent_activity(user_id):
    from datetime import datetime, timedelta
    last_activity = user_last_activity.get(user_id)
    if not last_activity:
        return False
    return datetime.now() - last_activity < timedelta(minutes=5)

def update_user_activity(user_id):
    user_last_activity[user_id] = datetime.now()

@app.route('/quick-action', methods=['POST'])
@require_auth
def quick_action():
    data = request.json
    action = data.get('action', '')
    user_id = request.user_id
    
    update_user_activity(user_id)
    
    # Set user mode based on action
    if action == 'stock-search':
        user_mode_manager.set_mode(user_id, 'stock_search')
        response = "🔍 **Stock Search Activated**\n\nEnter a stock symbol (e.g., RELIANCE, TCS, AAPL) to get live data."
    elif action == 'portfolio-review':
        user_mode_manager.set_mode(user_id, 'portfolio')
        response = "💼 **Portfolio Mode Activated**\n\nUse the Portfolio Calculator in the sidebar to manage your investments."
    elif action == 'market-analysis':
        user_mode_manager.set_mode(user_id, 'analysis')
        response = "📊 **Analysis Mode Activated**\n\nEnter stock symbols for detailed market analysis."
    elif action == 'news-update':
        user_mode_manager.set_mode(user_id, 'news')
        response = "📰 **News Mode Activated**\n\nCheck the News widget for latest updates or ask about specific stocks."
    else:
        response = 'Action completed successfully.'
    
    return jsonify({'response': response})

@app.route('/market-data', methods=['GET'])
def market_data():
    try:
        symbols = ["NIFTY", "SENSEX", "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS"]
        market_data_list = []
        for symbol in symbols:
            context = get_stock_context(symbol)
            if "error" not in context:
                market_data_list.append({
                    "symbol": symbol,
                    "name": symbol.replace(".NS", ""),
                    "price": f"{context['current_price']:,}",
                    "change": context['price_change']
                })
        return jsonify({"market_data": market_data_list})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/stock-analysis', methods=['POST'])
def stock_analysis():
    data = request.json
    symbol = data.get('symbol', '')
    result = execute_function('get_stock_price', {'symbol': symbol})
    return jsonify(result)

@app.route('/portfolio-calculate', methods=['POST'])
def portfolio_calculate():
    data = request.json
    holdings = data.get('holdings', [])
    result = execute_function('calculate_portfolio_value', {'holdings': holdings})
    return jsonify(result)

@app.route('/clear-mode', methods=['POST'])
@require_auth
def clear_mode():
    user_id = request.user_id
    user_mode_manager.clear_mode(user_id)
    update_user_activity(user_id)
    return jsonify({'response': 'Mode cleared. You can now use quick actions or ask general questions.'})

@app.route('/analytics/usage', methods=['GET'])
@require_auth
def get_user_usage():
    days = request.args.get('days', 30, type=int)
    usage = cost_monitor.get_user_usage(request.user_id, days)
    return jsonify(usage)

if __name__ == '__main__':
    app.run(debug=True, port=5000)