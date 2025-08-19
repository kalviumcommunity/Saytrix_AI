import json
import requests
from datetime import datetime
from typing import Dict, List, Any
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

class SaytrixEvaluationPipeline:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.gemini_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        
    def get_test_dataset(self) -> List[Dict]:
        """Financial dataset with 5 samples designed for comprehensive evaluation"""
        return [
            {
                "id": "test_001",
                "symbol": "INFY",
                "query": "Summarize Infosys stock performance over the last month",
                "method": "chain-of-thought-analysis",
                "expected_output": "Comprehensive analysis with step-by-step reasoning covering price movement, technical indicators, and performance metrics",
                "expected_criteria": {
                    "accuracy_of_financial_data": True,
                    "completeness_of_analysis": True,
                    "clarity_and_formatting": True,
                    "relevance_to_query": True,
                    "structured_output_usage": True
                },
                "scenario": "RAG retrieval and performance analysis"
            },
            {
                "id": "test_002", 
                "symbol": "RELIANCE",
                "query": "Compare Reliance and TCS based on P/E and sentiment",
                "method": "dynamic-analysis",
                "user_type": "advanced",
                "expected_output": "Detailed comparative analysis with P/E ratios, sentiment scores, and professional insights",
                "expected_criteria": {
                    "accuracy_of_financial_data": True,
                    "completeness_of_analysis": True,
                    "clarity_and_formatting": True,
                    "relevance_to_query": True,
                    "structured_output_usage": True
                },
                "scenario": "Function calling and comparative analysis"
            },
            {
                "id": "test_003",
                "symbol": "HDFCBANK",
                "query": "What are the key earnings highlights for HDFC Bank?",
                "method": "one-shot-analysis", 
                "expected_output": "Structured earnings summary with key financial metrics and highlights",
                "expected_criteria": {
                    "accuracy_of_financial_data": True,
                    "completeness_of_analysis": True,
                    "clarity_and_formatting": True,
                    "relevance_to_query": True,
                    "structured_output_usage": True
                },
                "scenario": "Structured output and earnings analysis"
            },
            {
                "id": "test_004",
                "symbol": "ICICIBANK",
                "query": "Is ICICI Bank undervalued based on current ratios?",
                "method": "multi-shot-analysis",
                "expected_output": "Valuation analysis with ratio comparison and undervaluation assessment",
                "expected_criteria": {
                    "accuracy_of_financial_data": True,
                    "completeness_of_analysis": True,
                    "clarity_and_formatting": True,
                    "relevance_to_query": True,
                    "structured_output_usage": True
                },
                "scenario": "Reasoning and valuation analysis"
            },
            {
                "id": "test_005",
                "symbol": "PORTFOLIO",
                "query": "Generate a portfolio risk summary for three holdings: RELIANCE, INFY, HDFC",
                "method": "dynamic-analysis",
                "user_type": "general",
                "expected_output": "Comprehensive portfolio risk analysis with diversification metrics and risk scores",
                "expected_criteria": {
                    "accuracy_of_financial_data": True,
                    "completeness_of_analysis": True,
                    "clarity_and_formatting": True,
                    "relevance_to_query": True,
                    "structured_output_usage": True
                },
                "scenario": "Portfolio analysis and risk assessment"
            }
        ]

    def create_judge_prompt(self, test_case: Dict, model_output: str) -> str:
        """Create judge prompt designed for comprehensive financial analysis evaluation"""
        
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
"""
        
        # Add specific criteria for this test case
        for criterion, expected in test_case['expected_criteria'].items():
            judge_prompt += f"- {criterion.replace('_', ' ').title()}: "
        
        judge_prompt += f"""

**OVERALL ASSESSMENT:**
- Total Score (5-25): Sum of all 5 criteria scores
- Pass/Fail: Pass if total score >= 15
- Brief Justification: Explain the scoring rationale

**RESPONSE FORMAT:**
Provide your evaluation in this exact JSON format:
{{
    "accuracy_financial_data": <1-5>,
    "completeness_analysis": <1-5>, 
    "clarity_formatting": <1-5>,
    "relevance_to_query": <1-5>,
    "structured_output_usage": <1-5>,
    "criteria_validation": {{
        "accuracy_of_financial_data": "YES/NO",
        "completeness_of_analysis": "YES/NO",
        "clarity_and_formatting": "YES/NO",
        "relevance_to_query": "YES/NO",
        "structured_output_usage": "YES/NO"
    }},
    "total_score": <5-25>,
    "pass_fail": "PASS/FAIL",
    "justification": "<brief_explanation_of_scoring>"
}}
"""
        return judge_prompt

    def call_model_endpoint(self, test_case: Dict) -> Dict:
        """Call the appropriate model endpoint"""
        endpoint = f"{self.base_url}/{test_case['method']}"
        
        payload = {
            "symbol": test_case['symbol'],
            "query": test_case['query']
        }
        
        if 'user_type' in test_case:
            payload['user_type'] = test_case['user_type']
            
        try:
            response = requests.post(endpoint, json=payload, timeout=30)
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def evaluate_with_judge(self, test_case: Dict, model_output: str) -> Dict:
        """Use judge prompt to evaluate model output"""
        judge_prompt = self.create_judge_prompt(test_case, model_output)
        
        try:
            generate_config = types.GenerateContentConfig(
                temperature=0.1, 
                top_p=0.8,
                max_output_tokens=1500
            )
            
            contents = [types.Content(role="user", parts=[types.Part(text=judge_prompt)])]
            
            response = self.gemini_client.models.generate_content(
                model="gemini-2.5-pro",
                contents=contents,
                config=generate_config
            )
            
            # Token usage logging for judge evaluation
            input_tokens = response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else 0
            output_tokens = response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else 0
            total_tokens = input_tokens + output_tokens
            
            print(f"🔢 TOKENS USED - Judge Evaluation:")
            print(f"   Input Tokens: {input_tokens}")
            print(f"   Output Tokens: {output_tokens}")
            print(f"   Total Tokens: {total_tokens}")
            print(f"   Estimated Cost: ${total_tokens * 0.000002:.6f}")
            
            # Extract JSON from response
            response_text = response.output_text
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_str = response_text[json_start:json_end]
                evaluation_result = json.loads(json_str)
                evaluation_result['token_usage'] = {
                    'input_tokens': input_tokens,
                    'output_tokens': output_tokens,
                    'total_tokens': total_tokens
                }
                return evaluation_result
            else:
                return {"error": "Could not parse judge response"}
                
        except Exception as e:
            return {"error": f"Judge evaluation failed: {str(e)}"}

    def run_single_test(self, test_case: Dict) -> Dict:
        """Run a single test case"""
        print(f"Running test {test_case['id']}: {test_case['scenario']}")
        
        # Call model endpoint
        model_response = self.call_model_endpoint(test_case)
        
        if "error" in model_response:
            return {
                "test_id": test_case['id'],
                "status": "FAILED",
                "error": model_response['error'],
                "model_output": None,
                "evaluation": None
            }
        
        model_output = model_response.get('result', '')
        
        # Evaluate with judge
        evaluation = self.evaluate_with_judge(test_case, model_output)
        
        return {
            "test_id": test_case['id'],
            "status": "COMPLETED",
            "model_output": model_output,
            "evaluation": evaluation,
            "test_case": test_case
        }

    def run_evaluation_pipeline(self) -> Dict:
        """Run complete evaluation pipeline"""
        print("🚀 Starting Saytrix AI Evaluation Pipeline")
        print("=" * 50)
        
        test_dataset = self.get_test_dataset()
        results = []
        
        for test_case in test_dataset:
            result = self.run_single_test(test_case)
            results.append(result)
            
            # Print immediate feedback
            if result['status'] == 'COMPLETED' and result['evaluation']:
                eval_data = result['evaluation']
                status = eval_data.get('pass_fail', 'UNKNOWN')
                score = eval_data.get('overall_score', 0)
                print(f"✅ {result['test_id']}: {status} (Score: {score}/100)")
            else:
                print(f"❌ {result['test_id']}: FAILED")
        
        # Generate summary report
        summary = self.generate_summary_report(results)
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"evaluation_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump({
                "timestamp": timestamp,
                "summary": summary,
                "detailed_results": results
            }, f, indent=2)
        
        print("\n" + "=" * 50)
        print("📊 EVALUATION SUMMARY")
        print("=" * 50)
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed_tests']}")
        print(f"Failed: {summary['failed_tests']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Average Score: {summary['average_score']:.1f}/100")
        print(f"Results saved to: {filename}")
        
        return {
            "summary": summary,
            "results": results,
            "report_file": filename
        }

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
                if 'overall_score' in result['evaluation']:
                    scores.append(result['evaluation']['overall_score'])
        
        return {
            "total_tests": total_tests,
            "completed_tests": len(completed_tests),
            "passed_tests": len(passed_tests),
            "failed_tests": total_tests - len(passed_tests),
            "success_rate": (len(passed_tests) / total_tests * 100) if total_tests > 0 else 0,
            "average_score": sum(scores) / len(scores) if scores else 0,
            "score_distribution": {
                "min": min(scores) if scores else 0,
                "max": max(scores) if scores else 0,
                "scores": scores
            }
        }

if __name__ == "__main__":
    # Video Script Implementation: Evaluation Pipeline for Saytrix AI
    print("🎥 Saytrix AI Evaluation Pipeline - As Featured in Video")
    print("📊 Testing 5 Financial Scenarios with Judge Prompt Evaluation")
    print("🧠 Demonstrating RAG, Function Calling, Structured Output & Reasoning")
    print("🔢 Token Usage Tracking: Monitor AI costs and efficiency")
    print("=" * 70)
    
    pipeline = SaytrixEvaluationPipeline()
    
    # Display dataset overview (as shown in video)
    print("\n📋 DATASET OVERVIEW (5 Test Cases):")
    dataset = pipeline.get_test_dataset()
    for i, test in enumerate(dataset, 1):
        print(f"{i}. {test['query']} [{test['method']}]")
    
    print("\n🧠 JUDGE PROMPT PARAMETERS:")
    print("- Accuracy of Financial Data (1-5)")
    print("- Completeness of Analysis (1-5)")
    print("- Clarity and Formatting (1-5)")
    print("- Relevance to User Query (1-5)")
    print("- Use of Structured Output (1-5)")
    print("- Pass Threshold: 15/25 (60%)")
    
    print("\n🧪 RUNNING EVALUATION PIPELINE...")
    print("📊 Token usage will be logged for each AI call\n")
    
    results = pipeline.run_evaluation_pipeline()
    
    # Calculate total token usage across all tests
    total_tokens_used = 0
    for result in results['results']:
        if result['status'] == 'COMPLETED':
            # Model tokens
            model_response = result.get('model_output', '')
            # Judge tokens (if available in evaluation)
            if result.get('evaluation') and 'token_usage' in result['evaluation']:
                total_tokens_used += result['evaluation']['token_usage']['total_tokens']
    
    print(f"\n💰 TOTAL EVALUATION COST SUMMARY:")
    print(f"   Total Tokens Used: {total_tokens_used}")
    print(f"   Estimated Total Cost: ${total_tokens_used * 0.000002:.6f}")
    print("\n✅ Evaluation Complete! Check results file for detailed analysis.")
