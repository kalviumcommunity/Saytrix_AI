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
            price_position = 0

        context = {
            "symbol": symbol,
            "current_price": current_price,
            "high_52": high_52,
            "low_52": low_52,
            "pe_ratio": pe_ratio,
            "market_cap": market_cap,
            "price_change": round(price_change, 2),
            "market_condition": market_condition,
            "price_position": round(price_position, 1)
        }
        return context
    except Exception as e:
        return {"error": f"Could not fetch stock data for {symbol}. Error: {str(e)}"}

@app.route("/chain-of-thought-analysis", methods=["POST"])
def chain_of_thought_analysis():
    """Chain of Thought Prompting - Step-by-step reasoning"""
    data = request.get_json(force=True)
    symbol = data.get("symbol")
    query = data.get("query", "Should I invest in this stock?")

    if not symbol:
        return jsonify({"error": "Missing 'symbol' in request."}), 400

    context = get_stock_context(symbol)
    if "error" in context:
        return jsonify({"error": context["error"]}), 500

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

**IMPORTANT:** Show your reasoning for each step. Explain WHY you reach each conclusion.

Start your analysis now, thinking through each step carefully.
"""

    # TEMPERATURE UPDATE: Optimized for logical reasoning
    # Temperature 0.25 = More focused reasoning while maintaining creativity
    # TOP P UPDATE: 0.9 = Broader vocabulary for comprehensive analysis
    # TOP K UPDATE: 50 = Focused candidate pool for logical analysis
    # STOP SEQUENCES: Control output boundaries for structured analysis
    generate_content_config = types.GenerateContentConfig(
        temperature=0.25,  # Updated: Enhanced logical reasoning
        top_p=0.9,  # Updated: Expanded token selection for detailed analysis
        top_k=50,  # Updated: Controlled candidate pool for reasoning
        stop_sequences=["**END ANALYSIS**", "---", "DISCLAIMER:"],  # Updated: Structured boundaries
        max_output_tokens=2500
    )
    
    print(f"🌡️ TEMPERATURE: 0.25 | TOP P: 0.9 | TOP K: 50 | STOP: Analysis boundaries (Logical reasoning mode)")
    
    contents = [types.Content(role="user", parts=[types.Part(text=cot_prompt)])]

    try:
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=contents,
            config=generate_content_config
        )
        response_text = response.output_text if response.output_text else ""
        
        # Token usage logging
        input_tokens = response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else 0
        output_tokens = response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else 0
        total_tokens = input_tokens + output_tokens
        
        print(f"🔢 TOKENS USED - Chain of Thought Analysis:")
        print(f"   Input Tokens: {input_tokens}")
        print(f"   Output Tokens: {output_tokens}")
        print(f"   Total Tokens: {total_tokens}")
        print(f"   Estimated Cost: ${total_tokens * 0.000002:.6f}")
        
        return jsonify({
            "result": response_text,
            "method": "chain-of-thought",
            "reasoning_steps": 5,
            "token_usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens
            },
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

    # TEMPERATURE: Dynamic adaptation based on market conditions
    # TOP P: Adaptive based on market volatility
    # TOP K: Adaptive based on market conditions
    # STOP SEQUENCES: Adaptive based on analysis focus
    top_p_value = 0.95 if context.get("market_condition") == "near_low" else 0.85
    top_k_value = 80 if context.get("market_condition") == "near_low" else 40
    stop_sequences = ["**ANALYSIS COMPLETE**", "---", "Note:"] if focus == "recommendation" else ["**END SECTION**", "---", "Summary:"]
    generate_content_config = types.GenerateContentConfig(
        temperature=temperature,  # 0.2 (cautious) | 0.4 (opportunistic) | 0.3 (balanced)
        top_p=top_p_value,  # Updated: 0.95 (opportunistic) | 0.85 (cautious/balanced)
        top_k=top_k_value,  # Updated: 80 (opportunistic) | 40 (cautious/balanced)
        stop_sequences=stop_sequences,  # Updated: Focus-based boundaries
        max_output_tokens=2000
    )
    
    print(f"🌡️ TEMPERATURE: {temperature} | TOP P: {top_p_value} | TOP K: {top_k_value} | STOP: {len(stop_sequences)} sequences ({tone.split(' - ')[0].lower()} mode)")
    
    contents = [types.Content(role="user", parts=[types.Part(text=dynamic_prompt)])]

    try:
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=contents,
            config=generate_content_config
        )
        response_text = response.output_text if response.output_text else ""
        
        # Token usage logging
        input_tokens = response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else 0
        output_tokens = response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else 0
        total_tokens = input_tokens + output_tokens
        
        print(f"🔢 TOKENS USED - Dynamic Analysis:")
        print(f"   Input Tokens: {input_tokens}")
        print(f"   Output Tokens: {output_tokens}")
        print(f"   Total Tokens: {total_tokens}")
        print(f"   Estimated Cost: ${total_tokens * 0.000002:.6f}")
        
        return jsonify({
            "result": response_text,
            "method": "dynamic",
            "token_usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens
            },
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

**NOW ANALYZE:**
User Query: "{query}"
Stock Data: {symbol} - Current: ₹{context.get('current_price')}, 52W High: ₹{context.get('high_52')}, 52W Low: ₹{context.get('low_52')}, P/E: {context.get('pe_ratio')}

Based on the examples above, provide analysis matching the appropriate tone (bullish/bearish/neutral) for the stock's actual condition.
"""

    # TEMPERATURE UPDATE: Optimized for contextual adaptation
    # Temperature 0.35 = Better balance for nuanced responses
    # TOP P UPDATE: 0.88 = Balanced vocabulary for example-based learning
    # TOP K UPDATE: 60 = Balanced candidate pool for example learning
    # STOP SEQUENCES: Example-based boundaries for consistent learning
    generate_content_config = types.GenerateContentConfig(
        temperature=0.35,  # Updated: Enhanced contextual responses
        top_p=0.88,  # Updated: Optimized for multi-shot learning
        top_k=60,  # Updated: Balanced selection for pattern learning
        stop_sequences=["**EXAMPLE END**", "---", "Additional Notes:"],  # Updated: Example boundaries
        max_output_tokens=1800
    )
    
    print(f"🌡️ TEMPERATURE: 0.35 | TOP P: 0.88 | TOP K: 60 | STOP: Example boundaries (Contextual adaptation mode)")
    
    contents = [types.Content(role="user", parts=[types.Part(text=multi_shot_prompt)])]

    try:
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=contents,
            config=generate_content_config
        )
        response_text = response.output_text if response.output_text else ""
        
        # Token usage logging
        input_tokens = response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else 0
        output_tokens = response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else 0
        total_tokens = input_tokens + output_tokens
        
        print(f"🔢 TOKENS USED - Multi-Shot Analysis:")
        print(f"   Input Tokens: {input_tokens}")
        print(f"   Output Tokens: {output_tokens}")
        print(f"   Total Tokens: {total_tokens}")
        print(f"   Estimated Cost: ${total_tokens * 0.000002:.6f}")
        
        return jsonify({
            "result": response_text, 
            "method": "multi-shot",
            "token_usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens
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

    # TEMPERATURE UPDATE: Optimized for format consistency
    # Temperature 0.15 = More consistent format following
    # TOP P UPDATE: 0.75 = Focused vocabulary for consistent formatting
    # TOP K UPDATE: 30 = Strict candidate limitation for format control
    # STOP SEQUENCES: Strict format boundaries for template adherence
    generate_content_config = types.GenerateContentConfig(
        temperature=0.15,  # Updated: Enhanced format consistency
        top_p=0.75,  # Updated: Tighter control for format adherence
        top_k=30,  # Updated: Minimal candidates for format consistency
        stop_sequences=["**FORMAT END**", "---", "Disclaimer:"],  # Updated: Format boundaries
        max_output_tokens=1500
    )
    
    print(f"🌡️ TEMPERATURE: 0.15 | TOP P: 0.75 | TOP K: 30 | STOP: Format boundaries (Format consistency mode)")
    
    contents = [types.Content(role="user", parts=[types.Part(text=one_shot_prompt)])]

    try:
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=contents,
            config=generate_content_config
        )
        response_text = response.output_text if response.output_text else ""
        
        # Token usage logging
        input_tokens = response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else 0
        output_tokens = response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else 0
        total_tokens = input_tokens + output_tokens
        
        print(f"🔢 TOKENS USED - One-Shot Analysis:")
        print(f"   Input Tokens: {input_tokens}")
        print(f"   Output Tokens: {output_tokens}")
        print(f"   Total Tokens: {total_tokens}")
        print(f"   Estimated Cost: ${total_tokens * 0.000002:.6f}")
        
        return jsonify({
            "result": response_text, 
            "method": "one-shot",
            "token_usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens
            }
        })
    except Exception as e:
        return jsonify({"result": "", "error": str(e)}), 500

@app.route("/run-evaluation", methods=["POST"])
def run_evaluation():
    """Endpoint to trigger evaluation pipeline"""
    try:
        from evaluation_pipeline import SaytrixEvaluationPipeline
        pipeline = SaytrixEvaluationPipeline()
        results = pipeline.run_evaluation_pipeline()
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint with temperature settings info"""
    return jsonify({
        "status": "healthy",
        "service": "Saytrix AI",
        "version": "1.1.0",  # Updated version
        "timestamp": datetime.datetime.now().isoformat(),
        "available_methods": [
            "chain-of-thought-analysis",
            "dynamic-analysis", 
            "multi-shot-analysis",
            "one-shot-analysis"
        ],
        "temperature_settings": {
            "chain_of_thought": 0.25,
            "dynamic_analysis": "0.2-0.4 (adaptive)",
            "multi_shot": 0.35,
            "one_shot": 0.15
        },
        "top_p_settings": {
            "chain_of_thought": 0.9,
            "dynamic_analysis": "0.85-0.95 (adaptive)",
            "multi_shot": 0.88,
            "one_shot": 0.75
        },
        "top_k_settings": {
            "chain_of_thought": 50,
            "dynamic_analysis": "40-80 (adaptive)",
            "multi_shot": 60,
            "one_shot": 30
        },
        "stop_sequences": {
            "chain_of_thought": ["**END ANALYSIS**", "---", "DISCLAIMER:"],
            "dynamic_analysis": "Adaptive based on focus",
            "multi_shot": ["**EXAMPLE END**", "---", "Additional Notes:"],
            "one_shot": ["**FORMAT END**", "---", "Disclaimer:"]
        },
        "optimization": "Temperature, Top P, Top K, and Stop Sequences optimized for each prompting method"
    })

if __name__ == "__main__":
    print("🌡️ SAYTRIX AI - FULLY OPTIMIZED VERSION (TEMP | TOP P | TOP K | STOP)")
    print("📊 Chain of Thought: 0.25 | 0.9 | 50 | Analysis boundaries")
    print("🔄 Dynamic Analysis: 0.2-0.4 | 0.85-0.95 | 40-80 | Adaptive boundaries")
    print("📈 Multi-Shot: 0.35 | 0.88 | 60 | Example boundaries")
    print("🎯 One-Shot: 0.15 | 0.75 | 30 | Format boundaries")
    print("=" * 50)
    app.run(debug=True, host="0.0.0.0", port=5000)