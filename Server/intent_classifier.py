import re

def is_greeting(text):
    """Check if text is a greeting, not a stock symbol"""
    greetings = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening']
    text_lower = text.lower().strip()
    
    # Direct greeting match
    if text_lower in greetings:
        return True
    
    # Greeting with punctuation
    if re.match(r'^(hi|hello|hey)[!.]*$', text_lower):
        return True
        
    return False

def should_lookup_stock(text):
    """Determine if text should trigger stock lookup"""
    if is_greeting(text):
        return False
    
    # Only lookup if it looks like a stock symbol (2-5 chars, mostly uppercase)
    text_clean = text.strip()
    if len(text_clean) >= 2 and len(text_clean) <= 5 and text_clean.isupper():
        return True
        
    return False