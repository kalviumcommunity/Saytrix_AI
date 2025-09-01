import yfinance as yf
import requests
from typing import Dict, Any, List
from datetime import datetime
import os
from cache_manager import api_cache
from prompt_templates import ClosedWorldPrompts, validate_ai_response
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FUNCTION_SCHEMAS = [
    {
        "name": "get_stock_price",
        "description": "Get current stock price and basic information for a given symbol",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Stock symbol (e.g., RELIANCE.NS, AAPL)"
                }
            },
            "required": ["symbol"]
        }
    },
    {
        "name": "get_stock_history",
        "description": "Get historical stock price data for analysis",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Stock symbol"
                },
                "period": {
                    "type": "string",
                    "description": "Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)",
                    "enum": ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]
                }
            },
            "required": ["symbol", "period"]
        }
    },
    {
        "name": "compare_stocks",
        "description": "Compare multiple stocks side by side",
        "parameters": {
            "type": "object",
            "properties": {
                "symbols": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of stock symbols to compare"
                }
            },
            "required": ["symbols"]
        }
    },
    {
        "name": "calculate_portfolio_value",
        "description": "Calculate total portfolio value and performance",
        "parameters": {
            "type": "object",
            "properties": {
                "holdings": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string"},
                            "quantity": {"type": "number"},
                            "avg_price": {"type": "number"}
                        },
                        "required": ["symbol", "quantity", "avg_price"]
                    },
                    "description": "List of portfolio holdings"
                }
            },
            "required": ["holdings"]
        }
    },
    {
        "name": "get_market_news",
        "description": "Get latest market news for a specific stock or general market",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Stock symbol (optional, if not provided returns general market news)"
                }
            }
        }
    }
]

class FunctionExecutor:
    @staticmethod
    def get_stock_price(symbol: str) -> Dict[str, Any]:
        # Try yfinance first (more reliable)
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period="1d")
            
            if not hist.empty and info:
                current_price = hist['Close'].iloc[-1]
                result = {
                    "symbol": symbol,
                    "current_price": round(current_price, 2),
                    "high": round(hist['High'].iloc[-1], 2),
                    "low": round(hist['Low'].iloc[-1], 2),
                    "volume": int(hist['Volume'].iloc[-1]),
                    "market_cap": info.get('marketCap', 'N/A'),
                    "pe_ratio": info.get('trailingPE', 'N/A'),
                    "source": "Yahoo Finance",
                    "timestamp": datetime.now().isoformat()
                }
                return result
        except Exception as e:
            logger.error(f"Yahoo Finance error for {symbol}: {e}")
        
        # Try Alpha Vantage as fallback
        api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        if api_key:
            try:
                url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"
                response = requests.get(url, timeout=10)
                data = response.json()
                
                if "Global Quote" in data and data["Global Quote"]:
                    quote = data["Global Quote"]
                    result = {
                        "symbol": symbol,
                        "current_price": float(quote.get("05. price", 0)),
                        "change": float(quote.get("09. change", 0)),
                        "change_percent": quote.get("10. change percent", "0%"),
                        "high": float(quote.get("03. high", 0)),
                        "low": float(quote.get("04. low", 0)),
                        "volume": int(quote.get("06. volume", 0)),
                        "source": "Alpha Vantage",
                        "timestamp": datetime.now().isoformat()
                    }
                    return result
            except Exception as e:
                logger.error(f"Alpha Vantage API error for {symbol}: {e}")
        
        # Return mock data for demo
        mock_data = {
            "ZOMATO.NS": {"current_price": 268.45, "high": 275.20, "low": 265.10, "volume": 12500000},
            "HDFCBANK.NS": {"current_price": 1654.80, "high": 1670.25, "low": 1645.30, "volume": 8900000},
            "RELIANCE.NS": {"current_price": 2456.30, "high": 2478.90, "low": 2445.15, "volume": 15600000}
        }
        
        if symbol in mock_data:
            data = mock_data[symbol]
            return {
                "symbol": symbol,
                "current_price": data["current_price"],
                "high": data["high"],
                "low": data["low"],
                "volume": data["volume"],
                "source": "Demo Data",
                "timestamp": datetime.now().isoformat()
            }
        
        return {"error": f"No data found for {symbol}", "symbol": symbol}
    
    @staticmethod
    def get_stock_history(symbol: str, period: str) -> Dict[str, Any]:
        # Try Alpha Vantage API first
        api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        if api_key:
            try:
                url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={api_key}"
                response = requests.get(url, timeout=10)
                data = response.json()
                
                if "Time Series (Daily)" in data:
                    time_series = data["Time Series (Daily)"]
                    history_data = []
                    
                    for date, values in list(time_series.items())[:30]:  # Last 30 days
                        history_data.append({
                            "date": date,
                            "open": float(values["1. open"]),
                            "high": float(values["2. high"]),
                            "low": float(values["3. low"]),
                            "close": float(values["4. close"]),
                            "volume": int(values["5. volume"])
                        })
                    
                    return {
                        "symbol": symbol,
                        "period": period,
                        "data_points": len(history_data),
                        "history": history_data[:10],
                        "source": "Alpha Vantage"
                    }
            except:
                pass
        
        # Fallback to yfinance with multiple symbols
        symbols_to_try = [symbol, "HDFCBANK.NS", "RELIANCE.NS", "TCS.NS", "AAPL"]
        
        for sym in symbols_to_try:
            try:
                ticker = yf.Ticker(sym)
                hist = ticker.history(period=period)
                
                if not hist.empty:
                    history_data = [{
                        "date": date.strftime("%Y-%m-%d"),
                        "open": round(row['Open'], 2),
                        "high": round(row['High'], 2),
                        "low": round(row['Low'], 2),
                        "close": round(row['Close'], 2),
                        "volume": int(row['Volume'])
                    } for date, row in hist.iterrows()]
                    
                    return {
                        "symbol": sym,
                        "period": period,
                        "data_points": len(history_data),
                        "history": history_data[-10:],
                        "source": "Yahoo Finance"
                    }
            except:
                continue
        
        return {"error": f"No historical data found for {symbol}"}
    
    @staticmethod
    def compare_stocks(symbols: List[str]) -> Dict[str, Any]:
        try:
            comparison_data = []
            
            for symbol in symbols:
                stock_data = FunctionExecutor.get_stock_price(symbol)
                if "error" not in stock_data:
                    comparison_data.append(stock_data)
            
            if not comparison_data:
                return {"error": "No valid stock data found for comparison"}
            
            return {
                "comparison_count": len(comparison_data),
                "stocks": comparison_data,
                "comparison_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            return {"error": f"Failed to compare stocks: {str(e)}"}
    
    @staticmethod
    def calculate_portfolio_value(holdings: List[Dict]) -> Dict[str, Any]:
        try:
            portfolio_data = []
            total_current_value = 0
            total_invested = 0
            
            for holding in holdings:
                symbol = holding["symbol"]
                quantity = holding["quantity"]
                avg_price = holding["avg_price"]
                
                stock_data = FunctionExecutor.get_stock_price(symbol)
                if "error" not in stock_data:
                    current_price = stock_data["current_price"]
                    current_value = quantity * current_price
                    invested_value = quantity * avg_price
                    pnl = current_value - invested_value
                    pnl_percent = (pnl / invested_value) * 100 if invested_value > 0 else 0
                    
                    portfolio_data.append({
                        "symbol": symbol,
                        "quantity": quantity,
                        "avg_price": avg_price,
                        "current_price": current_price,
                        "current_value": round(current_value, 2),
                        "invested_value": round(invested_value, 2),
                        "pnl": round(pnl, 2),
                        "pnl_percent": round(pnl_percent, 2)
                    })
                    
                    total_current_value += current_value
                    total_invested += invested_value
            
            total_pnl = total_current_value - total_invested
            total_pnl_percent = (total_pnl / total_invested) * 100 if total_invested > 0 else 0
            
            return {
                "portfolio_summary": {
                    "total_invested": round(total_invested, 2),
                    "total_current_value": round(total_current_value, 2),
                    "total_pnl": round(total_pnl, 2),
                    "total_pnl_percent": round(total_pnl_percent, 2),
                    "number_of_holdings": len(portfolio_data)
                },
                "holdings": portfolio_data,
                "calculation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            return {"error": f"Failed to calculate portfolio: {str(e)}"}
    
    @staticmethod
    def get_market_news(symbol: str = None) -> Dict[str, Any]:
        api_key = os.getenv('NEWS_API_KEY')
        if api_key:
            try:
                # Use general market terms if symbol is 'market' or None
                if symbol == 'market' or symbol is None:
                    query = "stock market OR financial markets OR economy"
                else:
                    query = symbol
                    
                url = f"https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&apiKey={api_key}&pageSize=5&language=en"
                response = requests.get(url, timeout=10)
                data = response.json()
                
                if data.get("status") == "ok" and data.get("articles"):
                    news_data = [{
                        "title": article.get("title", ""),
                        "description": article.get("description", ""),
                        "url": article.get("url", ""),
                        "published": article.get("publishedAt", ""),
                        "source": article.get("source", {}).get("name", "")
                    } for article in data["articles"]]
                    
                    return {
                        "symbol": symbol or "market",
                        "news_count": len(news_data),
                        "news": news_data,
                        "source": "NewsAPI"
                    }
            except Exception as e:
                print(f"NewsAPI error: {e}")
        
        # Fallback to yfinance news
        try:
            if symbol:
                ticker = yf.Ticker(symbol)
                news = ticker.news[:3]
                news_data = [{
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "published": datetime.fromtimestamp(item.get("providerPublishTime", 0)).strftime("%Y-%m-%d") if item.get("providerPublishTime") else ""
                } for item in news]
                
                return {
                    "symbol": symbol,
                    "news_count": len(news_data),
                    "news": news_data,
                    "source": "Yahoo Finance"
                }
        except:
            pass
        
        return {"error": f"No news found for {symbol}"}

def get_stock_context(symbol: str) -> Dict[str, Any]:
    """Get stock context with price and change data"""
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    if api_key:
        try:
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if "Global Quote" in data and data["Global Quote"]:
                quote = data["Global Quote"]
                current_price = float(quote.get("05. price", 0))
                change = float(quote.get("09. change", 0))
                price_change = round((change / current_price) * 100, 2) if current_price > 0 else 0
                
                return {
                    "current_price": current_price,
                    "price_change": price_change
                }
        except:
            pass
    
    # Fallback mock data
    mock_data = {
        "NIFTY": {"current_price": 19674.25, "price_change": 0.85},
        "SENSEX": {"current_price": 66023.69, "price_change": 0.92},
        "RELIANCE.NS": {"current_price": 2456.30, "price_change": -0.45},
        "TCS.NS": {"current_price": 3789.15, "price_change": 1.23},
        "HDFCBANK.NS": {"current_price": 1654.80, "price_change": 0.67}
    }
    
    return mock_data.get(symbol, {"current_price": 0, "price_change": 0})

def execute_function(function_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    executor = FunctionExecutor()
    if hasattr(executor, function_name):
        func = getattr(executor, function_name)
        try:
            return func(**parameters)
        except Exception as e:
            return {"error": f"Function execution failed: {str(e)}"}
    else:
        return {"error": f"Function {function_name} not found"}