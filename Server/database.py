from pymongo import MongoClient
from datetime import datetime
from typing import Dict, Any, List, Optional
import os
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Database:
    def __init__(self):
        # MongoDB connection
        mongo_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        self.client = MongoClient(mongo_uri)
        self.db = self.client.saytrix_ai_free
        
        # Collections
        self.users = self.db.users
        self.conversations = self.db.conversations
        self.portfolios = self.db.portfolios
    
    # User Management
    def create_user(self, email: str, password: str, name: str) -> Dict[str, Any]:
        """Create new user account"""
        if self.users.find_one({"email": email}):
            return {"error": "User already exists"}
        
        user_id = str(uuid.uuid4())
        user_data = {
            "user_id": user_id,
            "email": email,
            "name": name,
            "password_hash": generate_password_hash(password),
            "created_at": datetime.now(),
            "last_login": None
        }
        
        self.users.insert_one(user_data)
        return {"user_id": user_id, "message": "User created successfully"}
    
    def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate user login"""
        user = self.users.find_one({"email": email})
        if not user or not check_password_hash(user["password_hash"], password):
            return {"error": "Invalid credentials"}
        
        # Update last login
        self.users.update_one(
            {"email": email},
            {"$set": {"last_login": datetime.now()}}
        )
        
        return {
            "user_id": user["user_id"],
            "name": user["name"],
            "email": user["email"]
        }
    
    # Conversation Management
    def save_message(self, user_id: str, conversation_id: str, message_type: str, content: str) -> None:
        """Save message to conversation history"""
        message_data = {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "message_type": message_type,  # 'user' or 'ai'
            "content": content,
            "timestamp": datetime.now()
        }
        self.conversations.insert_one(message_data)
    
    def get_conversation_history(self, user_id: str, conversation_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get conversation history for context"""
        messages = self.conversations.find({
            "user_id": user_id,
            "conversation_id": conversation_id
        }).sort("timestamp", 1).limit(limit)
        
        return [{
            "role": "user" if msg["message_type"] == "user" else "model",
            "parts": [msg["content"]]
        } for msg in messages]
    
    def get_user_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get list of user's conversations"""
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {
                "_id": "$conversation_id",
                "last_message": {"$last": "$timestamp"},
                "message_count": {"$sum": 1},
                "preview": {"$first": "$content"}
            }},
            {"$sort": {"last_message": -1}},
            {"$limit": 10}
        ]
        
        conversations = list(self.conversations.aggregate(pipeline))
        return [{
            "conversation_id": conv["_id"],
            "last_message": conv["last_message"],
            "message_count": conv["message_count"],
            "preview": conv["preview"][:50] + "..." if len(conv["preview"]) > 50 else conv["preview"]
        } for conv in conversations]
    
    # Portfolio Management
    def save_portfolio(self, user_id: str, holdings: List[Dict[str, Any]]) -> None:
        """Save user's portfolio"""
        portfolio_data = {
            "user_id": user_id,
            "holdings": holdings,
            "updated_at": datetime.now()
        }
        
        self.portfolios.replace_one(
            {"user_id": user_id},
            portfolio_data,
            upsert=True
        )
    
    def get_portfolio(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's portfolio"""
        return self.portfolios.find_one({"user_id": user_id})
    
    # User Mode Management
    def save_user_mode(self, user_id: str, mode: str) -> None:
        """Save user's current mode"""
        try:
            self.users.update_one(
                {"user_id": user_id},
                {"$set": {"current_mode": mode, "mode_updated_at": datetime.now()}},
                upsert=True
            )
        except Exception as e:
            print(f"Error saving user mode: {e}")
    
    def get_user_mode(self, user_id: str) -> Optional[str]:
        """Get user's current mode"""
        try:
            user = self.users.find_one({"user_id": user_id})
            return user.get("current_mode") if user else None
        except Exception as e:
            print(f"Error getting user mode: {e}")
            return None

# Global database instance
db = Database()