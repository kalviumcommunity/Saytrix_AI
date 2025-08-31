from datetime import datetime
from typing import Dict, Any, List
import json
import os
from database import db

class CostMonitor:
    def __init__(self):
        # Simple usage tracking (no actual costs for free tier)
        self.usage_logs = db.db.usage_logs
    
    def log_gemini_usage(self, user_id: str, conversation_id: str, input_tokens: int, output_tokens: int, model: str = 'gemini_pro') -> int:
        """Log Gemini API usage (free tier tracking)"""
        log_entry = {
            'user_id': user_id,
            'conversation_id': conversation_id,
            'service': 'gemini',
            'model': model,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': input_tokens + output_tokens,
            'timestamp': datetime.now()
        }
        
        self.usage_logs.insert_one(log_entry)
        return input_tokens + output_tokens
    
    def log_api_usage(self, user_id: str, service: str, endpoint: str, success: bool = True) -> int:
        """Log external API usage (free tier tracking)"""
        log_entry = {
            'user_id': user_id,
            'service': service,
            'endpoint': endpoint,
            'success': success,
            'timestamp': datetime.now()
        }
        
        self.usage_logs.insert_one(log_entry)
        return 1
    
    def get_user_usage(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get usage summary for a user (free tier)"""
        from datetime import timedelta
        
        start_date = datetime.now() - timedelta(days=days)
        
        pipeline = [
            {
                '$match': {
                    'user_id': user_id,
                    'timestamp': {'$gte': start_date}
                }
            },
            {
                '$group': {
                    '_id': '$service',
                    'api_calls': {'$sum': 1},
                    'total_tokens': {'$sum': '$total_tokens'}
                }
            }
        ]
        
        results = list(self.usage_logs.aggregate(pipeline))
        total_calls = sum(r['api_calls'] for r in results)
        total_tokens = sum(r.get('total_tokens', 0) for r in results)
        
        return {
            'user_id': user_id,
            'period_days': days,
            'total_api_calls': total_calls,
            'total_tokens': total_tokens,
            'breakdown': results,
            'generated_at': datetime.now().isoformat()
        }
    
    def get_system_costs(self, days: int = 7) -> Dict[str, Any]:
        """Get system-wide cost analytics"""
        from datetime import timedelta
        
        start_date = datetime.now() - timedelta(days=days)
        
        pipeline = [
            {
                '$match': {
                    'timestamp': {'$gte': start_date}
                }
            },
            {
                '$group': {
                    '_id': {
                        'service': '$service',
                        'date': {'$dateToString': {'format': '%Y-%m-%d', 'date': '$timestamp'}}
                    },
                    'daily_cost': {'$sum': '$total_cost'},
                    'daily_calls': {'$sum': 1}
                }
            },
            {
                '$sort': {'_id.date': -1}
            }
        ]
        
        results = list(self.cost_logs.aggregate(pipeline))
        
        # Calculate totals
        total_cost = sum(r['daily_cost'] for r in results if 'daily_cost' in r)
        total_calls = sum(r['daily_calls'] for r in results)
        
        # Get top users by cost
        user_pipeline = [
            {
                '$match': {
                    'timestamp': {'$gte': start_date}
                }
            },
            {
                '$group': {
                    '_id': '$user_id',
                    'user_cost': {'$sum': '$total_cost'},
                    'user_calls': {'$sum': 1}
                }
            },
            {
                '$sort': {'user_cost': -1}
            },
            {
                '$limit': 10
            }
        ]
        
        top_users = list(self.cost_logs.aggregate(user_pipeline))
        
        return {
            'period_days': days,
            'total_cost': round(total_cost, 4),
            'total_api_calls': total_calls,
            'average_cost_per_call': round(total_cost / total_calls, 6) if total_calls > 0 else 0,
            'daily_breakdown': results,
            'top_users': top_users,
            'generated_at': datetime.now().isoformat()
        }
    
    def export_cost_report(self, days: int = 30) -> str:
        """Export detailed cost report to JSON file"""
        report = self.get_system_costs(days)
        
        filename = f"cost_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join('reports', filename)
        
        # Create reports directory if it doesn't exist
        os.makedirs('reports', exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        return filepath

# Global cost monitor instance
cost_monitor = CostMonitor()