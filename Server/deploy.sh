#!/bin/bash

# Production deployment script for Saytrix AI

echo "🚀 Starting Saytrix AI Production Deployment..."

# Create necessary directories
mkdir -p logs reports

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Build frontend
echo "🏗️ Building frontend..."
cd ../client
npm install
npm run build
cd ../Server

# Set up environment variables (create .env file)
if [ ! -f .env ]; then
    echo "⚠️ Creating .env file template..."
    cat > .env << EOL
# MongoDB Configuration (Free Tier)
MONGODB_URI=mongodb+srv://kakihari03_db_user:k3hug21t1QIbZxmL@cluster0.9le6evn.mongodb.net/

# API Keys (Free Tiers)
GEMINI_API_KEY=your_free_gemini_api_key_here
ALPHA_VANTAGE_API_KEY=your_free_alpha_vantage_key_here

# Security
JWT_SECRET_KEY=saytrix_ai_free_secret_key_2024

# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False
EOL
    echo "⚠️ Please update .env with your free API keys!"
    echo "📝 Get free Gemini API key: https://makersuite.google.com/app/apikey"
    echo "📝 Get free Alpha Vantage key: https://www.alphavantage.co/support/#api-key"
fi

# Start Gunicorn server
echo "🔥 Starting Gunicorn server..."
gunicorn --config gunicorn.conf.py wsgi:app

echo "✅ Deployment complete!"
echo "🌐 Backend running on http://localhost:5000"
echo "📊 Configure Nginx to serve frontend and proxy API calls"