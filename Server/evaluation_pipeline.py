import json
import requests
from datetime import datetime
from typing import Dict, List, Any
import os
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai import types

load_dotenv()

class SaytrixEvaluationPipeline:
    def __init__(self):
        # Use an environment variable for the base URL for better security and flexibility
        self.base_url = os.getenv('FLASK_BASE_URL', "http://localhost:5000")
        
        gemini_api_key = os.environ.get("GEMINI_API_KEY")
        if not gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY not set in environment variables.")
        self.gemini_client = genai.Client(api_key=gemini_api_key)
    
    def _log_token_usage(self, response: types.GenerateContentResponse, label: str):
        """Helper function to log token usage for consistency."""
        input_tokens = getattr(response.usage_metadata, 'prompt_token_count', 0)
        output_tokens = getattr(response.usage_metadata, 'candidates_token_count', 0)
        total_tokens = input_tokens + output_tokens
        
        print(f"🔢 TOKENS USED - {label}:")
        print(f"  Input Tokens: {input_tokens}")
        print(f"  Output Tokens: {output_tokens}")
        print(f"  Total Tokens: {total_tokens}")
        print(f"  Estimated Cost: ${total_tokens * 0.000002:.6f}")

        return total_tokens

    def get_test_dataset(self) -> List[Dict]:
        """Financial dataset with 5 samples designed for comprehensive evaluation"""
        return [
            {
                "id": "test_001", "symbol": "INFY", "query": "Summarize Infosys stock performance over the last month",
                "method": "chain-of-thought-analysis",
                "expected_output": "Comprehensive analysis with step-by-step reasoning covering price movement, technical indicators, and performance metrics",
                "expected_criteria": {
                    "accuracy_of_financial_data": True, "completeness_of_analysis": True, "clarity_and_formatting": True,
                    "relevance_to_query": True, "structured_output_usage": True
                }, "scenario": "RAG retrieval and performance analysis"
            },
            {
                "id": "test_002", "symbol": "RELIANCE", "query": "Compare Reliance and TCS based on P/E and sentiment",
                "method": "dynamic-analysis", "user_type": "advanced",
                "expected_output": "Detailed comparative analysis with P/E ratios, sentiment scores, and professional insights",
                "expected_criteria": {
                    "accuracy_of_financial_data": True, "completeness_of_analysis": True, "clarity_and_formatting": True,
                    "relevance_to_query": True, "structured_output_usage": True
                }, "scenario": "Function calling and comparative analysis"
            },
            {
                "id": "test_003", "symbol": "HDFCBANK", "query": "What are the key earnings highlights for HDFC Bank?",
                "method": "one-shot-analysis", 
                "expected_output": "Structured earnings summary with key financial metrics and highlights",
                "expected_criteria": {
                    "accuracy_of_financial_data": True, "completeness_of_analysis": True, "clarity_and_formatting": True,
                    "relevance_to_query": True, "structured_output_usage": True
                }, "scenario": "Structured output and earnings analysis"
            },
            {
                "id": "test_004", "symbol": "ICICIBANK", "query": "Is ICICI Bank undervalued based on current ratios?",
                "method": "multi-shot-analysis",
                "expected_output": "Valuation analysis with ratio comparison and undervaluation assessment",
                "expected_criteria": {
                    "accuracy_of_financial_data": True, "completeness_of_analysis": True, "clarity_and_formatting": True,
                    "relevance_to_query": True, "structured_output_usage": True
                }, "scenario": "Reasoning and valuation analysis"
            },
            {
                "id": "test_005", "symbol": "PORTFOLIO", "query": "Generate a portfolio risk summary for three holdings: RELIANCE, INFY, HDFC",
                "method": "dynamic-analysis", "user_type": "general",
                "expected_output": "Comprehensive portfolio risk analysis with diversification metrics and risk scores",
                "expected_criteria": {
                    "accuracy_of_financial_data": True, "completeness_of_analysis": True, "clarity_and_formatting": True,
                    "relevance_to_query": True, "structured_output_usage": True
                }, "scenario": "Portfolio analysis and risk assessment"
            }
        ]

    def create_judge_prompt(self, test_case: Dict, model_output: str) -> str:
        """Create judge prompt designed for comprehensive financial analysis evaluation"""
        criteria_validation_text = "".join(
            f"- {criterion.replace('_', ' ').title()}: "
            for criterion in test_case['expected_criteria'].keys()
        )
        
        judge_prompt = f"""
You are an expert financial evaluator. Compare the model's response with the expected output and evaluate its quality.
**TEST CASE DETAILS:**
- Stock Symbol: {test_case['symbol']}
- User Query: "{test_case['query']}"
- Expected Output: "{test_case['expected_output']}"
- Method Used: {test_case['method']}
- Scenario: {test_case['scenario']}
- User Type: {test_case.get('user_type', 'general')}
**MODEL OUTPUT TO EVALUATE:**
{model_output}
**EVALUATION CRITERIA:**
Score the response from 1 to 5 based on:
**1. ACCURACY OF FINANCIAL DATA (1-5)**
- Are the financial metrics, ratios, and data points correct?
- Is the information up-to-date and relevant?
- Are calculations and comparisons accurate?
**2. COMPLETENESS OF ANALYSIS (1-5)**
- Does it address all aspects of the user query?
- Are key financial concepts covered comprehensively?
- Is the analysis thorough for the given scenario?
**3. CLARITY AND FORMATTING (1-5)**
- Is the response well-structured and easy to read?
- Are tables, charts, and JSON properly formatted?
- Is the language appropriate for the user type?
**4. RELEVANCE TO USER QUERY (1-5)**
- Does it directly answer what was asked?
- Is the focus aligned with user intent?
- Are recommendations contextually appropriate?
**5. USE OF STRUCTURED OUTPUT (1-5)**
- Are tables, charts, and structured formats used effectively?
- Is JSON formatting correct when required?
- Does it enhance readability and usability?
**SPECIFIC CRITERIA VALIDATION:**
For each criterion below, respond with YES/NO:
{criteria_validation_text}
**OVERALL ASSESSMENT:**
- Total Score (5-25): Sum of all 5 criteria scores
- Pass/Fail: Pass if total score >= 15
- Brief Justification: Explain the scoring rationale
**RESPONSE FORMAT:**
Provide your evaluation in this exact JSON format:
{{
    "accuracy_financial_data": <1-5>, "completeness_analysis": <1-5>, "clarity_formatting": <1-5>,
    "relevance_to_query": <1-5>, "structured_output_usage": <1-5>,
    "criteria_validation": {{
        "accuracy_of_financial_data": "YES/NO", "completeness_of_analysis": "YES/NO", "clarity_and_formatting": "YES/NO",
        "relevance_to_query": "YES/NO", "structured_output_usage": "YES/NO"
    }},
    "total_score": <5-25>,
    "pass_fail": "PASS/FAIL",
    "justification": "<brief_explanation_of_scoring>"
}}"""
        return judge_prompt

    def call_model_endpoint(self, test_case: Dict) -> Dict:
        """Call the appropriate model endpoint"""
        endpoint = f"{self.base_url}/{test_case['method']}"
        payload = {"symbol": test_case['symbol'], "query": test_case['query']}
        if 'user_type' in test_case:
            payload['user_type'] = test_case['user_type']
        
        try:
            response = requests.post(endpoint, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to call endpoint: {e}"}

    def evaluate_with_judge(self, test_case: Dict, model_output: str) -> Dict:
        """Use judge prompt to evaluate model output"""
        judge_prompt = self.create_judge_prompt(test_case, model_output)
        
        try:
            generate_config = types.GenerateContentConfig(
                temperature=0.1,  # Tightly controlled for consistent evaluation
                top_p=0.8,
                max_output_tokens=1500
            )
            print(f"🌡️ JUDGE TEMPERATURE: 0.1 (Deterministic evaluation mode)")
            contents = [types.Content(role="user", parts=[types.Part(text=judge_prompt)])]
            response = self.gemini_client.models.generate_content(
                model="gemini-1.5-pro", # Use a stable and powerful model for judging
                contents=contents,
                generation_config=generate_config
            )
            self._log_token_usage(response, "Judge Evaluation")
            response_text = response.text
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start != -1 and json_end != -1:
                json_str = response_text[json_start:json_end]
                evaluation_result = json.loads(json_str)
                evaluation_result['token_usage'] = self._get_tokens_from_response(response)
                return evaluation_result
            else:
                return {"error": "Could not parse judge response"}
        except Exception as e:
            return {"error": f"Judge evaluation failed: {str(e)}"}

    def _get_tokens_from_response(self, response: types.GenerateContentResponse) -> Dict[str, int]:
        """Extracts token counts from a Gemini response object."""
        input_tokens = getattr(response.usage_metadata, 'prompt_token_count', 0)
        output_tokens = getattr(response.usage_metadata, 'candidates_token_count', 0)
        total_tokens = input_tokens + output_tokens
        return {'input_tokens': input_tokens, 'output_tokens': output_tokens, 'total_tokens': total_tokens}

    def run_single_test(self, test_case: Dict) -> Dict:
        """Enhanced single test execution with detailed pipeline tracking"""
        print(f"  🔄 Executing {test_case['method']}...")
        model_response = self.call_model_endpoint(test_case)
        
        if "error" in model_response:
            print(f"  ❌ Model execution failed: {model_response['error']}")
            return {
                "test_id": test_case['id'], "status": "FAILED", "error": model_response['error'],
                "model_output": None, "evaluation": None, "pipeline_stage": "model_execution"
            }
        
        model_output = model_response.get('result', '')
        print(f"  ✅ Model response generated ({len(model_output)} chars)")
        
        print(f"  🧠 Running judge evaluation...")
        evaluation = self.evaluate_with_judge(test_case, model_output)
        
        if "error" in evaluation:
            print(f"  ⚠️ Judge evaluation failed: {evaluation['error']}")
            return {
                "test_id": test_case['id'], "status": "PARTIAL", "model_output": model_output,
                "model_token_usage": model_response.get('token_usage', {}), "evaluation": evaluation,
                "test_case": test_case, "pipeline_stage": "judge_evaluation"
            }
        
        total_tokens = (model_response.get('token_usage', {}).get('total_tokens', 0) + 
                        evaluation.get('token_usage', {}).get('total_tokens', 0))
        
        return {
            "test_id": test_case['id'], "status": "COMPLETED", "model_output": model_output,
            "model_token_usage": model_response.get('token_usage', {}), "evaluation": evaluation,
            "test_case": test_case, "pipeline_stage": "completed",
            "total_test_tokens": total_tokens,
            "execution_summary": {
                "model_method": test_case['method'], "response_length": len(model_output),
                "judge_score": evaluation.get('total_score', 0), "pass_status": evaluation.get('pass_fail', 'UNKNOWN')
            }
        }

    def run_evaluation_pipeline(self) -> Dict:
        """Enhanced evaluation pipeline with detailed testing framework explanation"""
        print("🚀 Starting Saytrix AI Evaluation Pipeline")
        print("📋 PIPELINE ARCHITECTURE:")
        print("   1️⃣ Load Test Dataset (5 Financial Scenarios)")
        print("   2️⃣ Execute Model Endpoints (4 Prompting Methods)")
        print("   3️⃣ Judge Evaluation (AI-powered Assessment)")
        print("   4️⃣ Results Analysis (Scoring & Feedback)")
        print("   5️⃣ Report Generation (JSON + Summary)")
        print("=" * 70)
        
        test_dataset = self.get_test_dataset()
        results = []
        total_tokens_pipeline = 0
        
        print("\n🧪 EXECUTING TEST CASES:")
        for i, test_case in enumerate(test_dataset, 1):
            print(f"\n[{i}/{len(test_dataset)}] Testing: {test_case['scenario']}")
            result = self.run_single_test(test_case)
            results.append(result)
            total_tokens_pipeline += result.get('total_test_tokens', 0)
            
            if result['status'] == 'COMPLETED' and result['evaluation']:
                eval_data = result['evaluation']
                status, score = eval_data.get('pass_fail', 'UNKNOWN'), eval_data.get('total_score', 0)
                print(f"  ✅ Result: {status} (Score: {score}/25)")
                print(f"  📈 Breakdown: Accuracy({eval_data.get('accuracy_financial_data', 0)}) | "
                      f"Completeness({eval_data.get('completeness_analysis', 0)}) | "
                      f"Clarity({eval_data.get('clarity_formatting', 0)}) | "
                      f"Relevance({eval_data.get('relevance_to_query', 0)}) | "
                      f"Structure({eval_data.get('structured_output_usage', 0)})")
                feedback = eval_data.get('justification', "N/A")[:100]
                print(f"  💬 Judge Feedback: {feedback}...")
            else:
                print(f"  ❌ FAILED: {result.get('error', 'Unknown error')}")
        
        print("\n📊 GENERATING EVALUATION REPORT...")
        summary = self.generate_summary_report(results)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"saytrix_evaluation_{timestamp}.json"
        
        evaluation_report = {
            "pipeline_info": {
                "timestamp": timestamp, "total_test_cases": len(test_dataset),
                "methods_tested": list(set(t['method'] for t in test_dataset)),
                "evaluation_framework": "AI Judge with 5-Criteria Scoring",
                "pass_threshold": "15/25 (60%)"
            },
            "token_usage": {
                "total_pipeline_tokens": total_tokens_pipeline,
                "estimated_cost": f"${total_tokens_pipeline * 0.000002:.6f}"
            },
            "summary": summary, "detailed_results": results,
            "methodology": {
                "dataset_design": "5 financial scenarios covering RAG, function calling, structured output, reasoning",
                "judge_criteria": ["Accuracy of Financial Data", "Completeness of Analysis", "Clarity and Formatting", "Relevance to Query", "Structured Output Usage"],
                "scoring_system": "1-5 scale per criterion (5-25 total)",
                "evaluation_model": "Gemini 1.5 Pro with temperature 0.1"
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(evaluation_report, f, indent=2)
        
        print("\n" + "=" * 70)
        print("🎯 FINAL EVALUATION RESULTS")
        print("=" * 70)
        print(f"📊 Test Cases Executed: {summary['total_tests']}")
        print(f"✅ Passed (≥15/25): {summary['passed_tests']}")
        print(f"❌ Failed (<15/25): {summary['failed_tests']}")
        print(f"📈 Success Rate: {summary['success_rate']:.1f}%")
        print(f"🎯 Average Score: {summary['average_score']:.1f}/25")
        print(f"💰 Total Tokens Used: {total_tokens_pipeline}")
        print(f"💵 Estimated Cost: ${total_tokens_pipeline * 0.000002:.6f}")
        print(f"📄 Report Saved: {filename}")
        
        method_performance = {}
        for result in results:
            if result['status'] == 'COMPLETED' and result['evaluation']:
                method = result['test_case']['method']
                score = result['evaluation'].get('total_score', 0)
                if method not in method_performance:
                    method_performance[method] = []
                method_performance[method].append(score)
        
        print("\n🔍 METHOD PERFORMANCE ANALYSIS:")
        for method, scores in method_performance.items():
            avg_score = sum(scores) / len(scores) if scores else 0
            print(f"  {method}: {avg_score:.1f}/25 avg ({len(scores)} tests)")
        
        return evaluation_report

    def generate_summary_report(self, results: List[Dict]) -> Dict:
        """Generate summary statistics"""
        total_tests = len(results)
        completed_tests = [r for r in results if r['status'] == 'COMPLETED']
        passed_tests = []
        scores = []
        
        for result in completed_tests:
            if result['evaluation'] and 'pass_fail' in result['evaluation']:
                if result['evaluation']['pass_fail'] == 'PASS':
                    passed_tests.append(result)
                if 'total_score' in result['evaluation']:
                    scores.append(result['evaluation']['total_score'])
        
        return {
            "total_tests": total_tests, "completed_tests": len(completed_tests),
            "passed_tests": len(passed_tests), "failed_tests": total_tests - len(passed_tests),
            "success_rate": (len(passed_tests) / total_tests * 100) if total_tests > 0 else 0,
            "average_score": sum(scores) / len(scores) if scores else 0,
            "score_distribution": {
                "min": min(scores) if scores else 0,
                "max": max(scores) if scores else 0,
                "scores": scores
            }
        }

if __name__ == "__main__":
    print("🎥 SAYTRIX AI EVALUATION PIPELINE - ENHANCED VERSION")
    print("=" * 80)
    
    pipeline = SaytrixEvaluationPipeline()
    
    print("\n📋 COMPREHENSIVE DATASET OVERVIEW:")
    dataset = pipeline.get_test_dataset()
    for i, test in enumerate(dataset, 1):
        print(f"{i}. SCENARIO: {test['scenario']}")
        print(f"  Query: '{test['query']}'")
        print(f"  Method: {test['method']}")
        print(f"  Expected: {test['expected_output'][:60]}...")
        print(f"  Criteria: {len(test['expected_criteria'])} validation points")
        print()
    
    print("🧠 ENHANCED JUDGE PROMPT FRAMEWORK:")
    print("  📊 5-Dimensional Scoring System (1-5 each):")
    print("  1️⃣ Accuracy of Financial Data")
    print("  2️⃣ Completeness of Analysis")
    print("  3️⃣ Clarity and Formatting")
    print("  4️⃣ Relevance to User Query")
    print("  5️⃣ Use of Structured Output")
    print("  🎯 Pass Threshold: 15/25 (60%)")
    print("  🤖 Judge Model: Gemini 1.5 Pro (Temperature: 0.1 for consistency)")
    
    print("\n🔧 TESTING PIPELINE ARCHITECTURE:")
    print("  Phase 1: Dataset Loading & Validation")
    print("  Phase 2: Model Endpoint Execution (with token tracking)")
    print("  Phase 3: AI Judge Evaluation (5-criteria assessment)")
    print("  Phase 4: Results Aggregation & Analysis")
    print("  Phase 5: Report Generation & Performance Insights")
    
    print("\n🚀 EXECUTING COMPREHENSIVE EVALUATION PIPELINE...")
    
    results = pipeline.run_evaluation_pipeline()
    
    print("\n🎓 EVALUATION PIPELINE INSIGHTS:")
    print("  ✅ End-to-End Testing")
    print("  ✅ Multi-Method Analysis")
    print("  ✅ Cost Optimization")
    print("  ✅ Quality Assurance")
    print("  ✅ Scalable Framework")
    
    print("\n📚 WHAT THIS DEMONSTRATES:")
    print("  🎯 Systematic evaluation methodology")
    print("  🔍 Detailed pipeline operation explanation")
    print("  📊 Comprehensive results analysis")
    print("  💡 Performance optimization insights")
    print("  🚀 Production-ready evaluation framework")