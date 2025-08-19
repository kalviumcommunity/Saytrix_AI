import os
from flask import Flask, request, jsonify
from google import genai
from google.genai import types
from dotenv import load_dotenv
import yfinance as yf

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)

# Initialize Gemini client
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY not set in environment variables.")
client = genai.Client(api_key=GEMINI_API_KEY)

def get_stock_context(symbol):
    try:
        stock = yf.Ticker(symbol)
        info = stock.info

        current_price = info.get("currentPrice", "N/A")
        high_52 = info.get("fiftyTwoWeekHigh", "N/A")
        low_52 = info.get("fiftyTwoWeekLow", "N/A")

        context = f"""
Stock: {symbol}
Current price: ₹{current_price}
52-week high/low: ₹{high_52}/₹{low_52}
Recent news: [Headlines not included in this demo]
Technical indicators: [RSI, MACD, etc.]
"""
        return context
    except Exception as e:
        return f"Could not fetch stock data for {symbol}. Error: {str(e)}"

@app.route("/one-shot-analysis", methods=["POST"])
def one_shot_analysis():
    """One-Shot Prompting Implementation for Stock Analysis"""
    data = request.get_json(force=True)
    symbol = data.get("symbol")
    query = data.get("query", "Analyze this stock")

    if not symbol:
        return jsonify({"error": "Missing 'symbol' in request."}), 400

    rag_context = get_stock_context(symbol)

    # ONE-SHOT PROMPTING IMPLEMENTATION
    # Providing a single, comprehensive example to guide the AI's response format
    
    one_shot_prompt = f"""
You are Saytrix AI, a financial analyst. Analyze stocks using this EXACT format:

**EXAMPLE ANALYSIS:**
User Query: "Should I invest in RELIANCE?"
Stock Data: RELIANCE - Current: ₹2,450, 52W High: ₹2,800, 52W Low: ₹2,100

Response:
📊 **STOCK OVERVIEW**
RELIANCE is trading at ₹2,450, down 12.5% from its 52-week high of ₹2,800. The stock shows consolidation near support levels.

📈 **TECHNICAL ANALYSIS**
- Support: ₹2,400 (strong)
- Resistance: ₹2,600 (immediate)
- RSI: 45 (neutral zone)
- Trend: Sideways with bullish undertone

💰 **FUNDAMENTAL INSIGHTS**
- Market Cap: ₹16.5L Cr
- P/E Ratio: 12.8x (reasonable)
- Debt-to-Equity: 0.35 (healthy)
- Revenue Growth: 8.2% YoY

⚠️ **RISK ASSESSMENT**
- Oil price volatility impact
- Regulatory changes in telecom
- Market sentiment dependency

🎯 **RECOMMENDATION**
BUY for long-term (12+ months)
Target: ₹2,800-3,000
Stop Loss: ₹2,300
Allocation: 5-8% of portfolio

**NOW ANALYZE:**
User Query: "{query}"
Stock Data: {rag_context}

Provide analysis in the EXACT same format as the example above.
"""

    generate_content_config = types.GenerateContentConfig(
        temperature=0.2,  # Very low for consistent format following
        top_p=0.7,
        max_output_tokens=1500
    )
    
    contents = [types.Content(role="user", parts=[types.Part(text=one_shot_prompt)])]

    response_text = ""
    try:
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=contents,
            config=generate_content_config
        )
        response_text = response.output_text if response.output_text else ""
        return jsonify({"result": response_text, "method": "one-shot"})
    except Exception as e:
        return jsonify({"result": "", "error": str(e)}), 500

@app.route("/analyze-stock", methods=["POST"])
def analyze_stock():
    data = request.get_json(force=True)
    symbol = data.get("symbol")
    query = data.get("query", "Give me a summary and analysis of this stock.")

    if not symbol:
        return jsonify({"error": "Missing 'symbol' in request."}), 400

    rag_context = get_stock_context(symbol)

    # RTFC Framework Implementation
    # R = Role, T = Task, F = Format, C = Context
    
    system_prompt = f"""
**ROLE**: You are Saytrix AI, an expert financial analyst and AI assistant specializing in Indian and global stock markets. You have deep expertise in technical analysis, fundamental analysis, market sentiment, and portfolio management.

**TASK**: Analyze the provided stock data and respond to user queries with:
1. Comprehensive stock analysis using real-time data
2. Technical and fundamental insights
3. Risk assessment and investment recommendations
4. Market context and comparative analysis
5. Actionable investment advice based on user's query

**FORMAT**: Structure your response as follows:
📊 **STOCK OVERVIEW**
- Current market status and key metrics
- Price movement analysis

📈 **TECHNICAL ANALYSIS**
- Support/resistance levels
- Technical indicators interpretation
- Trend analysis

💰 **FUNDAMENTAL INSIGHTS**
- Company performance metrics
- Industry comparison
- Growth prospects

⚠️ **RISK ASSESSMENT**
- Investment risks and opportunities
- Market volatility factors

🎯 **RECOMMENDATION**
- Clear buy/hold/sell guidance
- Target price and timeline
- Portfolio allocation suggestions

**CONTEXT**: Use the following real-time market data for analysis:
{rag_context}

Always provide data-driven insights, cite specific numbers from the context, and explain your reasoning clearly. Adapt your analysis complexity based on the user's query sophistication.
"""

    user_prompt = f"""
**USER REQUEST**:
Stock Symbol: {symbol}
Specific Query: "{query}"

**INSTRUCTIONS**: 
Analyze the above stock based on the provided context and respond to the specific user query. Ensure your response is:
- Accurate and data-driven
- Tailored to the user's specific question
- Actionable and practical
- Professional yet accessible

If the query is general, provide a comprehensive analysis. If specific (e.g., "Should I buy?", "What's the target price?"), focus on that aspect while providing supporting context.
"""

    # Enhanced configuration for better financial analysis
    tools = [types.Tool(googleSearch=types.GoogleSearch())]
    generate_content_config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=-1),
        tools=tools,
        temperature=0.3,  # Lower temperature for more consistent financial advice
        top_p=0.8,       # Focused responses
        max_output_tokens=2048  # Comprehensive analysis
    )
    contents = [
        types.Content(role="model", parts=[types.Part(text=system_prompt)]),
        types.Content(role="user", parts=[types.Part(text=user_prompt)])
    ]

    response_text = ""
    try:
        for chunk in client.models.generate_content_stream(
            model="gemini-2.5-pro",
            contents=contents,
            config=generate_content_config
        ):
            if chunk.text:
                response_text += chunk.text

        if not response_text.strip():
            response = client.models.generate_content(
                model="gemini-2.5-pro",
                contents=contents,
                config=generate_content_config
            )
            response_text = response.output_text if response.output_text else ""

        return jsonify({"result": response_text})
    except Exception as e:
        return jsonify({"result": "", "error": str(e)}), 500

@app.route("/multi-shot-analysis", methods=["POST"])
def multi_shot_analysis():
    """Multi-Shot Prompting Implementation for Stock Analysis"""
    data = request.get_json(force=True)
    symbol = data.get("symbol")
    query = data.get("query", "Analyze this stock")

    if not symbol:
        return jsonify({"error": "Missing 'symbol' in request."}), 400

    rag_context = get_stock_context(symbol)

    # MULTI-SHOT PROMPTING IMPLEMENTATION
    # Providing multiple examples to teach complex patterns and nuanced responses
    
    multi_shot_prompt = f"""
You are Saytrix AI, a financial analyst. Learn from these examples to provide nuanced stock analysis:

**EXAMPLE 1 - BULLISH STOCK:**
User Query: "Should I buy HDFC Bank?"
Stock Data: HDFC - Current: ₹1,650, 52W High: ₹1,700, 52W Low: ₹1,200, P/E: 18x, Growth: 15%

Response:
📊 **STOCK OVERVIEW**
HDFC Bank trades near 52W high at ₹1,650, showing strong momentum with 37% gains from lows.

📈 **TECHNICAL ANALYSIS**
- Trend: Strong uptrend with higher highs
- RSI: 65 (bullish but not overbought)
- Support: ₹1,600 (recent breakout level)

💰 **FUNDAMENTAL INSIGHTS**
- P/E: 18x (reasonable for banking sector)
- ROE: 16.8% (excellent)
- NPA: 1.2% (best-in-class)

⚠️ **RISK ASSESSMENT**
- Low credit risk due to strong underwriting
- Interest rate sensitivity moderate

🎯 **RECOMMENDATION**
STRONG BUY - Target: ₹1,800 (12M)
Allocation: 8-10% of portfolio

**EXAMPLE 2 - BEARISH STOCK:**
User Query: "What about Paytm stock?"
Stock Data: PAYTM - Current: ₹450, 52W High: ₹1,950, 52W Low: ₹440, P/E: -ve, Revenue decline: -8%

Response:
📊 **STOCK OVERVIEW**
Paytm trades near 52W lows at ₹450, down 77% from highs amid profitability concerns.

📈 **TECHNICAL ANALYSIS**
- Trend: Severe downtrend with lower lows
- RSI: 25 (oversold but no reversal signs)
- Resistance: ₹550 (major overhead supply)

💰 **FUNDAMENTAL INSIGHTS**
- P/E: Negative (loss-making)
- Revenue: Declining 8% YoY
- Cash burn: High operational losses

⚠️ **RISK ASSESSMENT**
- High execution risk in competitive fintech
- Regulatory uncertainties persist

🎯 **RECOMMENDATION**
AVOID - Wait for business turnaround
No allocation recommended

**EXAMPLE 3 - NEUTRAL STOCK:**
User Query: "How is ITC performing?"
Stock Data: ITC - Current: ₹420, 52W High: ₹480, 52W Low: ₹380, P/E: 22x, Dividend: 5.2%

Response:
📊 **STOCK OVERVIEW**
ITC trades in middle range at ₹420, showing sideways movement with steady dividend yield.

📈 **TECHNICAL ANALYSIS**
- Trend: Range-bound between ₹380-480
- RSI: 50 (neutral territory)
- Pattern: Consolidation phase

💰 **FUNDAMENTAL INSIGHTS**
- P/E: 22x (fair valuation)
- Dividend yield: 5.2% (attractive)
- Cigarette business stable but declining

⚠️ **RISK ASSESSMENT**
- ESG concerns limit re-rating potential
- Diversification efforts showing mixed results

🎯 **RECOMMENDATION**
HOLD - Dividend play for conservative investors
Allocation: 3-5% for income focus

**NOW ANALYZE:**
User Query: "{query}"
Stock Data: {rag_context}

Based on the examples above, provide analysis matching the appropriate tone (bullish/bearish/neutral) for the stock's actual condition.
"""

    generate_content_config = types.GenerateContentConfig(
        temperature=0.4,  # Slightly higher for nuanced responses
        top_p=0.8,
        max_output_tokens=1800
    )
    
    contents = [types.Content(role="user", parts=[types.Part(text=multi_shot_prompt)])]

    response_text = ""
    try:
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=contents,
            config=generate_content_config
        )
        response_text = response.output_text if response.output_text else ""
        return jsonify({"result": response_text, "method": "multi-shot"})
    except Exception as e:
        return jsonify({"result": "", "error": str(e)}), 500

@app.route("/compare-methods", methods=["GET"])
def compare_methods():
    """Compare One-Shot vs Multi-Shot vs RTFC Framework responses"""
    return jsonify({
        "methods": {
            "one_shot": {
                "description": "Single example-driven prompting",
                "endpoint": "/one-shot-analysis",
                "benefits": ["Consistent format", "Simple setup", "Fast responses"]
            },
            "multi_shot": {
                "description": "Multiple examples for nuanced responses",
                "endpoint": "/multi-shot-analysis", 
                "benefits": ["Contextual tone", "Pattern learning", "Adaptive responses"]
            },
            "rtfc": {
                "description": "Role-Task-Format-Context framework", 
                "endpoint": "/analyze-stock",
                "benefits": ["Comprehensive analysis", "Context-aware", "Flexible responses"]
            }
        }
    })

@app.route("/test-all-methods", methods=["POST"])
def test_all_methods():
    """Test all three prompting methods with the same stock"""
    data = request.get_json(force=True)
    symbol = data.get("symbol", "RELIANCE")
    
    return jsonify({
        "symbol": symbol,
        "endpoints": {
            "one_shot": f"/one-shot-analysis",
            "multi_shot": f"/multi-shot-analysis", 
            "rtfc": f"/analyze-stock"
        },
        "sample_request": {
            "symbol": symbol,
            "query": "Should I invest in this stock?"
        }
    })

if __name__ == "__main__":
    app.run(debug=True)