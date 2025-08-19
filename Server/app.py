import os
from flask import Flask, request, jsonify
from google import genai
from google.genai import types
from dotenv import load_dotenv
import yfinance as yf
import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize Gemini client
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY not set in environment variables.")
client = genai.Client(api_key=GEMINI_API_KEY)

def get_stock_context(symbol):
    """Enhanced stock data retrieval with market context"""
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        hist = stock.history(period="1mo")
        
        current_price = info.get("currentPrice", "N/A")
        high_52 = info.get("fiftyTwoWeekHigh", "N/A")
        low_52 = info.get("fiftyTwoWeekLow", "N/A")
        pe_ratio = info.get("trailingPE", "N/A")
        market_cap = info.get("marketCap", "N/A")
        
        # Calculate price change
        if len(hist) > 1:
            price_change = ((hist['Close'][-1] - hist['Close'][-2]) / hist['Close'][-2]) * 100
        else:
            price_change = 0
            
        # Determine market condition
        if current_price != "N/A" and high_52 != "N/A" and low_52 != "N/A":
            price_position = (current_price - low_52) / (high_52 - low_52) * 100
            if price_position > 80:
                market_condition = "near_high"
            elif price_position < 20:
                market_condition = "near_low"
            else:
                market_condition = "mid_range"
        else:
            market_condition = "unknown"

        context = {
            "symbol": symbol,
            "current_price": current_price,
            "high_52": high_52,
            "low_52": low_52,
            "pe_ratio": pe_ratio,
            "market_cap": market_cap,
            "price_change": round(price_change, 2),
            "market_condition": market_condition,
            "price_position": round(price_position, 1) if 'price_position' in locals() else "N/A"
        }
        return context
    except Exception as e:
        return {"error": f"Could not fetch stock data for {symbol}. Error: {str(e)}"}

def create_dynamic_prompt(symbol, query, context, user_type="general"):
    """Dynamic prompt generation based on context and user type"""
    
    # Determine analysis complexity based on query
    if any(word in query.lower() for word in ["technical", "chart", "rsi", "macd", "support", "resistance"]):
        analysis_type = "technical_focused"
    elif any(word in query.lower() for word in ["fundamental", "pe", "revenue", "profit", "earnings"]):
        analysis_type = "fundamental_focused"
    elif any(word in query.lower() for word in ["buy", "sell", "invest", "recommendation"]):
        analysis_type = "recommendation_focused"
    else:
        analysis_type = "comprehensive"
    
    # Determine urgency based on market condition
    if context.get("market_condition") == "near_high":
        urgency = "high_risk"
    elif context.get("market_condition") == "near_low":
        urgency = "opportunity"
    else:
        urgency = "normal"
    
    # Base prompt structure
    base_prompt = f"""
You are Saytrix AI, an expert financial analyst. Analyze {symbol} dynamically based on current market conditions.

**CURRENT MARKET CONTEXT:**
- Stock: {symbol}
- Price: ₹{context.get('current_price', 'N/A')}
- 52W Range: ₹{context.get('low_52', 'N/A')} - ₹{context.get('high_52', 'N/A')}
- Market Position: {context.get('market_condition', 'unknown')} ({context.get('price_position', 'N/A')}% of range)
- Recent Change: {context.get('price_change', 0)}%
- P/E Ratio: {context.get('pe_ratio', 'N/A')}
"""

    # Dynamic sections based on analysis type
    if analysis_type == "technical_focused":
        prompt_focus = """
**ANALYSIS FOCUS: TECHNICAL**
Provide detailed technical analysis including:
- Chart patterns and trend analysis
- Key support and resistance levels
- Technical indicators (RSI, MACD, Moving averages)
- Entry and exit points
- Risk management levels
"""
    elif analysis_type == "fundamental_focused":
        prompt_focus = """
**ANALYSIS FOCUS: FUNDAMENTAL**
Provide detailed fundamental analysis including:
- Valuation metrics and ratios
- Business model and competitive position
- Financial health and growth prospects
- Industry comparison
- Long-term investment thesis
"""
    elif analysis_type == "recommendation_focused":
        prompt_focus = """
**ANALYSIS FOCUS: INVESTMENT RECOMMENDATION**
Provide clear investment guidance including:
- Buy/Hold/Sell recommendation with rationale
- Target price and timeline
- Risk assessment and mitigation
- Portfolio allocation suggestion
- Alternative investment options
"""
    else:
        prompt_focus = """
**ANALYSIS FOCUS: COMPREHENSIVE**
Provide balanced analysis covering:
- Technical and fundamental insights
- Risk-reward assessment
- Market context and timing
- Clear actionable recommendations
"""

    # Dynamic urgency and tone based on market condition
    if urgency == "high_risk":
        tone_instruction = """
**TONE: CAUTIOUS**
The stock is near 52-week highs. Use cautious language, emphasize risk management, and consider profit-booking opportunities.
"""
    elif urgency == "opportunity":
        tone_instruction = """
**TONE: OPPORTUNISTIC**
The stock is near 52-week lows. Look for value opportunities, but assess if it's a falling knife or genuine value.
"""
    else:
        tone_instruction = """
**TONE: BALANCED**
The stock is in mid-range. Provide balanced analysis focusing on fundamentals and technical setup.
"""

    # User type customization
    if user_type == "beginner":
        complexity_instruction = """
**COMPLEXITY: BEGINNER-FRIENDLY**
Use simple language, explain technical terms, provide educational context, and focus on basic concepts.
"""
    elif user_type == "advanced":
        complexity_instruction = """
**COMPLEXITY: ADVANCED**
Use professional terminology, provide detailed analysis, include advanced metrics, and assume market knowledge.
"""
    else:
        complexity_instruction = """
**COMPLEXITY: INTERMEDIATE**
Balance technical accuracy with accessibility, explain key concepts briefly, and provide actionable insights.
"""

    # Response format
    format_instruction = """
**RESPONSE FORMAT:**
📊 **DYNAMIC OVERVIEW**
- Current market position and key insights
- Context-specific observations

📈 **FOCUSED ANALYSIS**
- Analysis tailored to query type and market condition
- Relevant technical or fundamental insights

⚠️ **CONTEXTUAL RISKS**
- Risks specific to current market position
- Timing and market condition considerations

🎯 **ADAPTIVE RECOMMENDATION**
- Recommendation adjusted for market condition
- Specific action items and timeline

**USER QUERY:** "{query}"

Provide analysis that adapts to the current market condition, query focus, and responds with appropriate urgency and complexity.
"""

    return base_prompt + prompt_focus + tone_instruction + complexity_instruction + format_instruction

@app.route("/chain-of-thought-analysis", methods=["POST"])
def chain_of_thought_analysis():
    """Chain of Thought Prompting - Step-by-step reasoning for stock analysis"""
    data = request.get_json(force=True)
    symbol = data.get("symbol")
    query = data.get("query", "Should I invest in this stock?")

    if not symbol:
        return jsonify({"error": "Missing 'symbol' in request."}), 400

    context = get_stock_context(symbol)
    if "error" in context:
        return jsonify({"error": context["error"]}), 500

    # CHAIN OF THOUGHT PROMPTING IMPLEMENTATION
    # Forces AI to show step-by-step reasoning process
    
    cot_prompt = f"""
You are Saytrix AI, a financial analyst. Analyze {symbol} using CHAIN OF THOUGHT reasoning.

**STOCK DATA:**
- Symbol: {symbol}
- Current Price: ₹{context.get('current_price')}
- 52W High: ₹{context.get('high_52')}
- 52W Low: ₹{context.get('low_52')}
- P/E Ratio: {context.get('pe_ratio')}
- Recent Change: {context.get('price_change')}%
- Market Position: {context.get('market_condition')}

**USER QUESTION:** "{query}"

**INSTRUCTIONS:** Show your complete reasoning process step-by-step. Think through each aspect systematically.

**CHAIN OF THOUGHT ANALYSIS:**

🧠 **STEP 1: DATA INTERPRETATION**
Let me first understand what the numbers tell us:
- Current price vs 52W range analysis
- P/E ratio evaluation
- Recent price movement assessment
- Market position implications

📈 **STEP 2: TECHNICAL REASONING**
Now I'll analyze the technical aspects:
- Where is the stock in its trading range?
- What does the recent price change indicate?
- Is this a good entry/exit point technically?
- What are the key support/resistance levels?

💰 **STEP 3: FUNDAMENTAL REASONING**
Next, let me evaluate the fundamentals:
- Is the P/E ratio reasonable for this stock?
- How does it compare to industry averages?
- What does the valuation suggest?
- Are there any red flags in the metrics?

⚠️ **STEP 4: RISK ASSESSMENT**
Now I need to consider the risks:
- What risks does the current market position present?
- How volatile has the stock been?
- What external factors could affect it?
- What's the risk-reward ratio?

🎯 **STEP 5: LOGICAL CONCLUSION**
Based on my step-by-step analysis:
- Weighing all the factors I've considered
- Connecting the technical and fundamental insights
- Considering the risk-reward balance
- Arriving at a logical recommendation

**IMPORTANT:** Show your reasoning for each step. Explain WHY you reach each conclusion. Connect each step to the next logically.

Start your analysis now, thinking through each step carefully and showing your complete thought process.
"""

    generate_content_config = types.GenerateContentConfig(
        temperature=0.3,  # Balanced for logical reasoning
        top_p=0.8,
        max_output_tokens=2500  # More space for detailed reasoning
    )
    
    contents = [types.Content(role="user", parts=[types.Part(text=cot_prompt)])]

    try:
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=contents,
            config=generate_content_config
        )
        response_text = response.output_text if response.output_text else ""
        
        return jsonify({
            "result": response_text,
            "method": "chain-of-thought",
            "reasoning_steps": 5,
            "context": {
                "symbol": symbol,
                "market_condition": context.get("market_condition"),
                "analysis_type": "step-by-step reasoning"
            }
        })
    except Exception as e:
        return jsonify({"result": "", "error": str(e)}), 500

@app.route("/dynamic-analysis", methods=["POST"])
def dynamic_analysis():
    """Dynamic Prompting - Adapts to market conditions and query type"""
    data = request.get_json(force=True)
    symbol = data.get("symbol")
    query = data.get("query", "Analyze this stock")
    user_type = data.get("user_type", "general")

    if not symbol:
        return jsonify({"error": "Missing 'symbol' in request."}), 400

    context = get_stock_context(symbol)
    if "error" in context:
        return jsonify({"error": context["error"]}), 500

    # Detect query focus
    if any(word in query.lower() for word in ["technical", "chart", "support", "resistance"]):
        focus = "technical"
    elif any(word in query.lower() for word in ["fundamental", "pe", "revenue", "profit"]):
        focus = "fundamental" 
    elif any(word in query.lower() for word in ["buy", "sell", "invest", "recommendation"]):
        focus = "recommendation"
    else:
        focus = "comprehensive"

    # Adaptive temperature based on market condition
    if context.get("market_condition") == "near_high":
        temperature = 0.2
        tone = "CAUTIOUS - Stock near 52W high, emphasize risk management"
    elif context.get("market_condition") == "near_low":
        temperature = 0.4
        tone = "OPPORTUNISTIC - Stock near 52W low, assess value opportunity"
    else:
        temperature = 0.3
        tone = "BALANCED - Stock in mid-range, provide neutral analysis"

    dynamic_prompt = f"""
You are Saytrix AI. Analyze {symbol} with DYNAMIC adaptation:

**CURRENT CONTEXT:**
- Stock: {symbol} at ₹{context.get('current_price')}
- Position: {context.get('market_condition')} ({context.get('price_position')}% of 52W range)
- Recent Change: {context.get('price_change')}%
- Query Focus: {focus.upper()}
- User Level: {user_type.upper()}

**DYNAMIC INSTRUCTIONS:**
{tone}

**ADAPTIVE FOCUS:**
{"Focus heavily on technical analysis, charts, and trading levels." if focus == "technical" else
 "Focus on fundamentals, valuation, and business metrics." if focus == "fundamental" else
 "Focus on clear buy/sell/hold recommendation with rationale." if focus == "recommendation" else
 "Provide comprehensive analysis covering all aspects."}

**USER COMPLEXITY:**
{"Use simple language and explain terms for beginners." if user_type == "beginner" else
 "Use professional terminology for advanced users." if user_type == "advanced" else
 "Balance technical accuracy with accessibility."}

**RESPONSE FORMAT:**
📊 **DYNAMIC OVERVIEW**
- Market position and context-specific insights

📈 **ADAPTIVE ANALYSIS**
- Analysis tailored to query focus and market condition

⚠️ **CONTEXTUAL RISKS**
- Risks specific to current market position

🎯 **SMART RECOMMENDATION**
- Recommendation adapted to market condition and user query

**USER QUERY:** "{query}"

Adapt your entire response tone, focus, and recommendations to match the current market condition and user's specific needs.
"""

    generate_content_config = types.GenerateContentConfig(
        temperature=temperature,
        top_p=0.8,
        max_output_tokens=2000
    )
    
    contents = [types.Content(role="user", parts=[types.Part(text=dynamic_prompt)])]

    try:
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=contents,
            config=generate_content_config
        )
        response_text = response.output_text if response.output_text else ""
        
        return jsonify({
            "result": response_text,
            "method": "dynamic",
            "adaptations": {
                "market_condition": context.get("market_condition"),
                "query_focus": focus,
                "temperature_used": temperature,
                "user_type": user_type,
                "tone_applied": tone.split(" - ")[0]
            }
        })
    except Exception as e:
        return jsonify({"result": "", "error": str(e)}), 500

@app.route("/one-shot-analysis", methods=["POST"])
def one_shot_analysis():
    """One-Shot Prompting - Single example for format consistency"""
    data = request.get_json(force=True)
    symbol = data.get("symbol")
    query = data.get("query", "Analyze this stock")

    if not symbol:
        return jsonify({"error": "Missing 'symbol' in request."}), 400

    context = get_stock_context(symbol)
    if "error" in context:
        return jsonify({"error": context["error"]}), 500

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
Stock Data: {symbol} - Current: ₹{context.get('current_price')}, 52W High: ₹{context.get('high_52')}, 52W Low: ₹{context.get('low_52')}

Provide analysis in the EXACT same format as the example above.
"""

    generate_content_config = types.GenerateContentConfig(
        temperature=0.2,
        top_p=0.7,
        max_output_tokens=1500
    )
    
    contents = [types.Content(role="user", parts=[types.Part(text=one_shot_prompt)])]

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

@app.route("/multi-shot-analysis", methods=["POST"])
def multi_shot_analysis():
    """Multi-Shot Prompting - Multiple examples for nuanced responses"""
    data = request.get_json(force=True)
    symbol = data.get("symbol")
    query = data.get("query", "Analyze this stock")

    if not symbol:
        return jsonify({"error": "Missing 'symbol' in request."}), 400

    context = get_stock_context(symbol)
    if "error" in context:
        return jsonify({"error": context["error"]}), 500

    multi_shot_prompt = f"""
You are Saytrix AI, a financial analyst. Learn from these examples to provide nuanced stock analysis:

**EXAMPLE 1 - BULLISH STOCK:**
User Query: "Should I buy HDFC Bank?"
Stock Data: HDFC - Current: ₹1,650, 52W High: ₹1,700, 52W Low: ₹1,200, P/E: 18x

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
Stock Data: PAYTM - Current: ₹450, 52W High: ₹1,950, 52W Low: ₹440, P/E: -ve

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
Stock Data: ITC - Current: ₹420, 52W High: ₹480, 52W Low: ₹380, P/E: 22x

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
Stock Data: {symbol} - Current: ₹{context.get('current_price')}, 52W High: ₹{context.get('high_52')}, 52W Low: ₹{context.get('low_52')}, P/E: {context.get('pe_ratio')}

Based on the examples above, provide analysis matching the appropriate tone (bullish/bearish/neutral) for the stock's actual condition.
"""

    generate_content_config = types.GenerateContentConfig(
        temperature=0.4,
        top_p=0.8,
        max_output_tokens=1800
    )
    
    contents = [types.Content(role="user", parts=[types.Part(text=multi_shot_prompt)])]

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

@app.route("/rtfc-analysis", methods=["POST"])
def rtfc_analysis():
    """RTFC Framework - Role, Task, Format, Context"""
    data = request.get_json(force=True)
    symbol = data.get("symbol")
    query = data.get("query", "Give me a comprehensive analysis")

    if not symbol:
        return jsonify({"error": "Missing 'symbol' in request."}), 400

    context = get_stock_context(symbol)
    if "error" in context:
        return jsonify({"error": context["error"]}), 500

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
Stock: {symbol}
Current Price: ₹{context.get('current_price')}
52-Week Range: ₹{context.get('low_52')} - ₹{context.get('high_52')}
P/E Ratio: {context.get('pe_ratio')}
Market Cap: {context.get('market_cap')}
Recent Change: {context.get('price_change')}%
Market Position: {context.get('market_condition')}

Always provide data-driven insights, cite specific numbers from the context, and explain your reasoning clearly.
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
"""

    generate_content_config = types.GenerateContentConfig(
        temperature=0.3,
        top_p=0.8,
        max_output_tokens=2048
    )
    
    contents = [
        types.Content(role="model", parts=[types.Part(text=system_prompt)]),
        types.Content(role="user", parts=[types.Part(text=user_prompt)])
    ]

    try:
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=contents,
            config=generate_content_config
        )
        response_text = response.output_text if response.output_text else ""
        return jsonify({"result": response_text, "method": "rtfc"})
    except Exception as e:
        return jsonify({"result": "", "error": str(e)}), 500

@app.route("/compare-all-methods", methods=["POST"])
def compare_all_methods():
    """Compare all four prompting methods"""
    data = request.get_json(force=True)
    symbol = data.get("symbol", "RELIANCE")
    
    return jsonify({
        "symbol": symbol,
        "available_methods": {
            "dynamic": {
                "endpoint": "/dynamic-analysis",
                "description": "Adapts to market conditions and query type",
                "parameters": ["symbol", "query", "user_type"]
            },
            "one_shot": {
                "endpoint": "/one-shot-analysis", 
                "description": "Single example for format consistency",
                "parameters": ["symbol", "query"]
            },
            "multi_shot": {
                "endpoint": "/multi-shot-analysis",
                "description": "Multiple examples for nuanced responses", 
                "parameters": ["symbol", "query"]
            },
            "rtfc": {
                "endpoint": "/rtfc-analysis",
                "description": "Role-Task-Format-Context framework",
                "parameters": ["symbol", "query"]
            }
        },
        "sample_request": {
            "symbol": symbol,
            "query": "Should I invest in this stock?",
            "user_type": "general"
        }
    })

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Saytrix AI",
        "version": "1.0.0",
        "timestamp": datetime.datetime.now().isoformat()
    })

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)