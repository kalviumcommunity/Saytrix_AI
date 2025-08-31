#!/usr/bin/env python3
"""
Simple server starter for development
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import and run the app
from app import app

if __name__ == "__main__":
    print("🚀 Starting Saytrix AI Server...")
    print("📊 Backend running on http://localhost:5000")
    print("🔧 Make sure to update .env with your API keys")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )