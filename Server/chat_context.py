class ChatContext:
    def __init__(self):
        self.active_mode = None
        self.user_sessions = {}
    
    def set_mode(self, user_id, mode):
        """Set active mode for user session"""
        self.user_sessions[user_id] = mode
        
    def get_mode(self, user_id):
        """Get current active mode for user"""
        return self.user_sessions.get(user_id, None)
    
    def clear_mode(self, user_id):
        """Clear active mode"""
        self.user_sessions[user_id] = None

# Global context manager
chat_context = ChatContext()