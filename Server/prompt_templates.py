from typing import Dict, Any, Optional

class ClosedWorldPrompts:
    
    @staticmethod
    def financial_analysis_prompt(user_query: str, data: Dict[str, Any]) -> str:
        """
        Closed-world prompt that prevents AI hallucination by strictly limiting responses to provided data
        """
        return f"""
You are a financial data presenter. Your ONLY job is to present the data provided to you.

STRICT RULES:
1. NEVER invent, estimate, or guess any financial data
2. ONLY use the exact data provided below
3. If data is missing, explicitly state "Data not available"
4. Do not provide analysis beyond what the data shows
5. Do not make predictions or recommendations

USER QUERY: {user_query}

PROVIDED DATA:
{format_data_for_prompt(data)}

RESPONSE REQUIREMENTS:
- Present only the factual data provided
- Use clear, professional language
- If asked about missing data, respond: "This information is not available in the current dataset"
- Format numbers clearly with appropriate currency symbols
- Include data source and timestamp when available

Your response:"""

    @staticmethod
    def stock_data_prompt(symbol: str, stock_data: Dict[str, Any]) -> str:
        """Specific prompt for stock data presentation"""
        return f"""
Present the following stock data for {symbol}. Use ONLY the provided information:

DATA PROVIDED:
{format_data_for_prompt(stock_data)}

INSTRUCTIONS:
- Present data in a clear, structured format
- Include all available metrics
- State "Not available" for any missing fields
- Do not calculate or derive additional metrics
- Include source and timestamp if provided

Format as: Current Price, High, Low, Volume, Change (if available)
"""

def format_data_for_prompt(data: Dict[str, Any]) -> str:
    """Format data dictionary for prompt inclusion"""
    if not data:
        return "No data provided"
    
    formatted = []
    for key, value in data.items():
        if value is not None:
            formatted.append(f"- {key}: {value}")
        else:
            formatted.append(f"- {key}: Not available")
    
    return "\n".join(formatted)

def validate_ai_response(response: str, source_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate AI response doesn't contain hallucinated data"""
    validation = {
        'is_valid': True,
        'issues': [],
        'confidence': 1.0
    }
    
    # Check for common hallucination patterns
    hallucination_indicators = [
        'approximately', 'estimated', 'around', 'roughly', 
        'typically', 'usually', 'generally', 'based on trends'
    ]
    
    response_lower = response.lower()
    for indicator in hallucination_indicators:
        if indicator in response_lower:
            validation['issues'].append(f"Potential hallucination indicator: '{indicator}'")
            validation['confidence'] -= 0.2
    
    if validation['confidence'] < 0.5:
        validation['is_valid'] = False
    
    return validation