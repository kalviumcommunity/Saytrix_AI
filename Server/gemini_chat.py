import google.generativeai as genai
import os
from typing import List, Dict, Any
from prompt_templates import ClosedWorldPrompts
from cost_monitor import cost_monitor
import logging

logger = logging.getLogger(__name__)

class GeminiChatManager:
    def __init__(self):
        # Configure Gemini API
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
    
    def get_financial_response(self, user_message: str, conversation_history: List[Dict], stock_data: Dict = None) -> str:
        """Generate AI response with conversation memory and financial context"""
        
        # Build system prompt with financial context
        system_prompt = """You are Saytrix AI, an expert financial assistant. You have access to real-time market data and conversation history.

RULES:
1. Use conversation history to maintain context
2. Only use provided stock data - never invent numbers
3. Be helpful, accurate, and professional
4. If data is missing, clearly state it's unavailable
5. Remember previous discussions in this conversation

CAPABILITIES:
- Real-time stock analysis
- Portfolio management
- Market insights
- Financial education"""

        # Add stock data context if provided
        if stock_data and 'error' not in stock_data:
            system_prompt += f"\n\nCURRENT STOCK DATA:\n{self._format_stock_data(stock_data)}"
        
        # Prepare conversation for Gemini
        chat_history = []
        
        # Add system message
        chat_history.append({
            "role": "user",
            "parts": [system_prompt]
        })
        chat_history.append({
            "role": "model", 
            "parts": ["I understand. I'm Saytrix AI, ready to help with financial analysis using real data and conversation context."]
        })
        
        # Add conversation history
        chat_history.extend(conversation_history)
        
        # Add current user message
        chat_history.append({
            "role": "user",
            "parts": [user_message]
        })
        
        try:
            # Start chat with history
            chat = self.model.start_chat(history=chat_history[:-1])  # Exclude current message
            
            # Generate response
            response = chat.send_message(user_message)
            
            # Log usage and cost (estimate token count)
            input_tokens = len(user_message.split()) * 1.3  # Rough estimate
            output_tokens = len(response.text.split()) * 1.3  # Rough estimate
            
            # Extract user_id from conversation context if available
            user_id = conversation_history[0].get('user_id', 'unknown') if conversation_history else 'unknown'
            conversation_id = 'default'
            
            cost = cost_monitor.log_gemini_usage(
                user_id=user_id,
                conversation_id=conversation_id,
                input_tokens=int(input_tokens),
                output_tokens=int(output_tokens)
            )
            
            logger.info(f"Gemini API call cost: ${cost:.6f} for user {user_id}")
            
            return response.text
            
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            return f"I apologize, but I'm experiencing technical difficulties. Please try again. Error: {str(e)}"
    
    def _format_stock_data(self, stock_data: Dict[str, Any]) -> str:
        """Format stock data for prompt context"""
        if 'error' in stock_data:
            return "No stock data available"
        
        formatted = f"Symbol: {stock_data.get('symbol', 'N/A')}\n"
        formatted += f"Current Price: {stock_data.get('current_price', 'N/A')}\n"
        formatted += f"High: {stock_data.get('high', 'N/A')}\n"
        formatted += f"Low: {stock_data.get('low', 'N/A')}\n"
        formatted += f"Volume: {stock_data.get('volume', 'N/A')}\n"
        formatted += f"Change: {stock_data.get('change', 'N/A')}\n"
        formatted += f"Source: {stock_data.get('source', 'N/A')}\n"
        formatted += f"Timestamp: {stock_data.get('timestamp', 'N/A')}"
        
        return formatted

# Global chat manager
gemini_chat = GeminiChatManager()