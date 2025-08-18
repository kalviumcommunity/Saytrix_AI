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

if __name__ == "__main__":
    app.run(debug=True)