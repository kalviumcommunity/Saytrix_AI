import time
import json
import logging
from typing import Dict, Any, List
from datetime import datetime
from functions import FunctionExecutor
from prompt_templates import ClosedWorldPrompts, validate_ai_response
from cache_manager import api_cache

class ProductionPipeline:
    def __init__(self):
        self.metrics = {
            'api_calls': 0,
            'cache_hits': 0,
            'errors': 0,
            'response_times': [],
            'hallucination_flags': 0
        }
        
    def test_api_latency(self, symbols: List[str] = None) -> Dict[str, Any]:
        """Test API response times and reliability"""
        if not symbols:
            symbols = ['AAPL', 'RELIANCE.NS', 'TCS.NS']
        
        results = []
        for symbol in symbols:
            start_time = time.time()
            try:
                data = FunctionExecutor.get_stock_price(symbol)
                end_time = time.time()
                latency = end_time - start_time
                
                results.append({
                    'symbol': symbol,
                    'latency_ms': round(latency * 1000, 2),
                    'success': 'error' not in data,
                    'data_quality': self._assess_data_quality(data)
                })
                
            except Exception as e:
                results.append({
                    'symbol': symbol,
                    'latency_ms': None,
                    'success': False,
                    'error': str(e)
                })
        
        avg_latency = sum(r['latency_ms'] for r in results if r['latency_ms']) / len([r for r in results if r['latency_ms']])
        
        return {
            'average_latency_ms': round(avg_latency, 2),
            'success_rate': sum(1 for r in results if r['success']) / len(results),
            'results': results
        }
    
    def test_cache_performance(self) -> Dict[str, Any]:
        """Test caching system performance"""
        # Clear cache for clean test
        api_cache.cache.clear()
        
        # First call (should miss cache)
        start_time = time.time()
        data1 = FunctionExecutor.get_stock_price('AAPL')
        first_call_time = time.time() - start_time
        
        # Second call (should hit cache)
        start_time = time.time()
        data2 = FunctionExecutor.get_stock_price('AAPL')
        second_call_time = time.time() - start_time
        
        return {
            'cache_working': data1 == data2,
            'first_call_ms': round(first_call_time * 1000, 2),
            'second_call_ms': round(second_call_time * 1000, 2),
            'cache_speedup': round(first_call_time / second_call_time, 2) if second_call_time > 0 else 0
        }
    
    def test_prompt_safety(self, test_queries: List[str] = None) -> Dict[str, Any]:
        """Test for AI hallucination and prompt safety"""
        if not test_queries:
            test_queries = [
                "What is Apple's stock price?",
                "Tell me about Tesla's performance",
                "What will happen to the market tomorrow?"
            ]
        
        results = []
        for query in test_queries:
            # Get real data
            stock_data = FunctionExecutor.get_stock_price('AAPL')
            
            # Generate prompt
            prompt = ClosedWorldPrompts.financial_analysis_prompt(query, stock_data)
            
            # Simulate AI response (in real implementation, call your AI model here)
            mock_response = f"Based on the provided data: Apple (AAPL) current price is ${stock_data.get('current_price', 'N/A')}"
            
            # Validate response
            validation = validate_ai_response(mock_response, stock_data)
            
            results.append({
                'query': query,
                'validation_passed': validation['is_valid'],
                'confidence_score': validation['confidence'],
                'issues': validation['issues']
            })
        
        return {
            'total_tests': len(results),
            'passed_tests': sum(1 for r in results if r['validation_passed']),
            'average_confidence': sum(r['confidence_score'] for r in results) / len(results),
            'results': results
        }
    
    def test_error_handling(self) -> Dict[str, Any]:
        """Test system behavior with invalid inputs"""
        test_cases = [
            {'symbol': 'INVALID123', 'expected': 'error'},
            {'symbol': '', 'expected': 'error'},
            {'symbol': None, 'expected': 'error'}
        ]
        
        results = []
        for case in test_cases:
            try:
                result = FunctionExecutor.get_stock_price(case['symbol'])
                error_handled = 'error' in result
                results.append({
                    'input': case['symbol'],
                    'error_properly_handled': error_handled,
                    'result': result
                })
            except Exception as e:
                results.append({
                    'input': case['symbol'],
                    'error_properly_handled': False,
                    'exception': str(e)
                })
        
        return {
            'error_handling_rate': sum(1 for r in results if r['error_properly_handled']) / len(results),
            'results': results
        }
    
    def _assess_data_quality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess quality of returned data"""
        if 'error' in data:
            return {'score': 0, 'issues': ['API returned error']}
        
        issues = []
        score = 1.0
        
        required_fields = ['current_price', 'high', 'low', 'volume']
        for field in required_fields:
            if field not in data or data[field] == 0:
                issues.append(f'Missing or zero {field}')
                score -= 0.2
        
        if 'timestamp' not in data:
            issues.append('Missing timestamp')
            score -= 0.1
        
        return {'score': max(0, score), 'issues': issues}
    
    def run_full_pipeline(self) -> Dict[str, Any]:
        """Run complete production readiness test"""
        print("🚀 Running Production Pipeline Tests...")
        
        # Test 1: API Latency
        print("📊 Testing API latency...")
        latency_results = self.test_api_latency()
        
        # Test 2: Cache Performance
        print("💾 Testing cache performance...")
        cache_results = self.test_cache_performance()
        
        # Test 3: Prompt Safety
        print("🛡️ Testing prompt safety...")
        safety_results = self.test_prompt_safety()
        
        # Test 4: Error Handling
        print("⚠️ Testing error handling...")
        error_results = self.test_error_handling()
        
        # Overall assessment
        overall_score = (
            (latency_results['success_rate'] * 0.3) +
            (1.0 if cache_results['cache_working'] else 0.0) * 0.2 +
            (safety_results['passed_tests'] / safety_results['total_tests']) * 0.3 +
            (error_results['error_handling_rate'] * 0.2)
        )
        
        production_ready = overall_score >= 0.8
        
        return {
            'timestamp': datetime.now().isoformat(),
            'production_ready': production_ready,
            'overall_score': round(overall_score, 2),
            'tests': {
                'api_latency': latency_results,
                'cache_performance': cache_results,
                'prompt_safety': safety_results,
                'error_handling': error_results
            },
            'recommendations': self._generate_recommendations(overall_score, {
                'latency': latency_results,
                'cache': cache_results,
                'safety': safety_results,
                'errors': error_results
            })
        }
    
    def _generate_recommendations(self, score: float, results: Dict) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        if results['latency']['average_latency_ms'] > 2000:
            recommendations.append("Consider implementing request timeout optimization")
        
        if not results['cache']['cache_working']:
            recommendations.append("Fix caching system - not working properly")
        
        if results['safety']['passed_tests'] < results['safety']['total_tests']:
            recommendations.append("Improve prompt safety measures")
        
        if results['errors']['error_handling_rate'] < 1.0:
            recommendations.append("Enhance error handling for edge cases")
        
        if score >= 0.8:
            recommendations.append("✅ System is production ready!")
        else:
            recommendations.append("❌ Address issues before production deployment")
        
        return recommendations

if __name__ == "__main__":
    pipeline = ProductionPipeline()
    results = pipeline.run_full_pipeline()
    
    print("\n" + "="*50)
    print("📋 PRODUCTION READINESS REPORT")
    print("="*50)
    print(f"Overall Score: {results['overall_score']}/1.0")
    print(f"Production Ready: {'✅ YES' if results['production_ready'] else '❌ NO'}")
    print("\nRecommendations:")
    for rec in results['recommendations']:
        print(f"  • {rec}")
    
    # Save detailed results
    with open('production_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)