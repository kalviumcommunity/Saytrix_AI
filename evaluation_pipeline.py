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
        """Enhanced single test execution with detailed pipeline tracking"""
        
        # Step 1: Model Endpoint Execution
        print(f"   🔄 Executing {test_case['method']}...")
        model_response = self.call_model_endpoint(test_case)
        
        if "error" in model_response:
            print(f"   ❌ Model execution failed: {model_response['error']}")
            return {
                "test_id": test_case['id'],
                "status": "FAILED",
                "error": model_response['error'],
                "model_output": None,
                "evaluation": None,
                "pipeline_stage": "model_execution"
            }
        
        model_output = model_response.get('result', '')
        model_tokens = model_response.get('token_usage', {})
        
        print(f"   ✅ Model response generated ({len(model_output)} chars)")
        if model_tokens:
            print(f"   📊 Model tokens: {model_tokens.get('total_tokens', 0)}")
        
        # Step 2: Judge Evaluation
        print(f"   🧠 Running judge evaluation...")
        evaluation = self.evaluate_with_judge(test_case, model_output)
        
        if "error" in evaluation:
            print(f"   ⚠️ Judge evaluation failed: {evaluation['error']}")
            return {
                "test_id": test_case['id'],
                "status": "PARTIAL",
                "model_output": model_output,
                "model_token_usage": model_tokens,
                "evaluation": evaluation,
                "test_case": test_case,
                "pipeline_stage": "judge_evaluation"
            }
        
        judge_tokens = evaluation.get('token_usage', {})
        if judge_tokens:
            print(f"   📊 Judge tokens: {judge_tokens.get('total_tokens', 0)}")
        
        # Step 3: Results Compilation
        total_tokens = (model_tokens.get('total_tokens', 0) + 
                       judge_tokens.get('total_tokens', 0))
        
        return {
            "test_id": test_case['id'],
            "status": "COMPLETED",
            "model_output": model_output,
            "model_token_usage": model_tokens,
            "evaluation": evaluation,
            "test_case": test_case,
            "pipeline_stage": "completed",
            "total_test_tokens": total_tokens,
            "execution_summary": {
                "model_method": test_case['method'],
                "response_length": len(model_output),
                "judge_score": evaluation.get('total_score', 0),
                "pass_status": evaluation.get('pass_fail', 'UNKNOWN')
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
            print(f"\n[{i}/5] Testing: {test_case['scenario']}")
            print(f"   Query: '{test_case['query']}'")
            print(f"   Method: {test_case['method']}")
            print(f"   Expected: {test_case['expected_output'][:50]}...")
            
            # Step 1: Call Model Endpoint
            print("   🔄 Calling model endpoint...")
            result = self.run_single_test(test_case)
            results.append(result)
            
            # Step 2: Display Results
            if result['status'] == 'COMPLETED' and result['evaluation']:
                eval_data = result['evaluation']
                status = eval_data.get('pass_fail', 'UNKNOWN')
                score = eval_data.get('total_score', 0)
                
                # Track tokens if available
                if 'token_usage' in eval_data:
                    tokens = eval_data['token_usage']['total_tokens']
                    total_tokens_pipeline += tokens
                    print(f"   📊 Tokens Used: {tokens}")
                
                print(f"   ✅ Result: {status} (Score: {score}/25)")
                
                # Show detailed scoring
                if 'accuracy_financial_data' in eval_data:
                    print(f"   📈 Breakdown: Accuracy({eval_data.get('accuracy_financial_data', 0)}) | "
                          f"Completeness({eval_data.get('completeness_analysis', 0)}) | "
                          f"Clarity({eval_data.get('clarity_formatting', 0)}) | "
                          f"Relevance({eval_data.get('relevance_to_query', 0)}) | "
                          f"Structure({eval_data.get('structured_output_usage', 0)})")
                
                # Show key feedback
                if 'justification' in eval_data:
                    feedback = eval_data['justification'][:100]
                    print(f"   💬 Judge Feedback: {feedback}...")
            else:
                print(f"   ❌ FAILED: {result.get('error', 'Unknown error')}")
        
        # Step 3: Generate Comprehensive Summary
        print("\n📊 GENERATING EVALUATION REPORT...")
        summary = self.generate_summary_report(results)
        
        # Step 4: Save Results with Enhanced Metadata
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"saytrix_evaluation_{timestamp}.json"
        
        evaluation_report = {
            "pipeline_info": {
                "timestamp": timestamp,
                "total_test_cases": len(test_dataset),
                "methods_tested": list(set([t['method'] for t in test_dataset])),
                "evaluation_framework": "AI Judge with 5-Criteria Scoring",
                "pass_threshold": "15/25 (60%)"
            },
            "token_usage": {
                "total_pipeline_tokens": total_tokens_pipeline,
                "estimated_cost": f"${total_tokens_pipeline * 0.000002:.6f}"
            },
            "summary": summary,
            "detailed_results": results,
            "methodology": {
                "dataset_design": "5 financial scenarios covering RAG, function calling, structured output, reasoning",
                "judge_criteria": ["Accuracy of Financial Data", "Completeness of Analysis", "Clarity and Formatting", "Relevance to Query", "Structured Output Usage"],
                "scoring_system": "1-5 scale per criterion (5-25 total)",
                "evaluation_model": "Gemini 2.5 Pro with temperature 0.1"
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(evaluation_report, f, indent=2)
        
        # Step 5: Display Comprehensive Results
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
        
        # Method Performance Breakdown
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
            print(f"   {method}: {avg_score:.1f}/25 avg ({len(scores)} tests)")
        
        print("\n🎥 VIDEO EXPLANATION POINTS COVERED:")
        print("   ✅ Dataset Structure: 5 financial scenarios explained")
        print("   ✅ Judge Prompt Design: 5-criteria scoring system")
        print("   ✅ Testing Framework: End-to-end pipeline operation")
        print("   ✅ Token Usage: Cost tracking and optimization")
        print("   ✅ Results Analysis: Comprehensive scoring breakdown")
        
        return {
            "summary": summary,
            "results": results,
            "report_file": filename,
            "pipeline_metadata": evaluation_report["pipeline_info"],
            "method_performance": method_performance
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
    # Enhanced Video Script Implementation: Comprehensive Evaluation Pipeline
    print("🎥 SAYTRIX AI EVALUATION PIPELINE - ENHANCED VERSION")
    print("📊 Comprehensive Testing Framework with Detailed Pipeline Explanation")
    print("🧠 5 Financial Scenarios × 4 Prompting Methods × AI Judge Evaluation")
    print("🔢 Token Usage Tracking & Cost Analysis")
    print("📈 Method Performance Comparison & Optimization Insights")
    print("=" * 80)
    
    pipeline = SaytrixEvaluationPipeline()
    
    # Enhanced dataset overview with expected outcomes
    print("\n📋 COMPREHENSIVE DATASET OVERVIEW:")
    dataset = pipeline.get_test_dataset()
    for i, test in enumerate(dataset, 1):
        print(f"{i}. SCENARIO: {test['scenario']}")
        print(f"   Query: '{test['query']}'")
        print(f"   Method: {test['method']}")
        print(f"   Expected: {test['expected_output'][:60]}...")
        print(f"   Criteria: {len(test['expected_criteria'])} validation points")
        print()
    
    print("🧠 ENHANCED JUDGE PROMPT FRAMEWORK:")
    print("   📊 5-Dimensional Scoring System (1-5 each):")
    print("   1️⃣ Accuracy of Financial Data - Correctness of metrics & calculations")
    print("   2️⃣ Completeness of Analysis - Comprehensive coverage of query aspects")
    print("   3️⃣ Clarity and Formatting - Structure, readability, appropriate language")
    print("   4️⃣ Relevance to User Query - Direct alignment with user intent")
    print("   5️⃣ Use of Structured Output - Tables, charts, JSON formatting")
    print("   🎯 Pass Threshold: 15/25 (60%) - Ensures quality standards")
    print("   🤖 Judge Model: Gemini 2.5 Pro (Temperature: 0.1 for consistency)")
    
    print("\n🔧 TESTING PIPELINE ARCHITECTURE:")
    print("   Phase 1: Dataset Loading & Validation")
    print("   Phase 2: Model Endpoint Execution (with token tracking)")
    print("   Phase 3: AI Judge Evaluation (5-criteria assessment)")
    print("   Phase 4: Results Aggregation & Analysis")
    print("   Phase 5: Report Generation & Performance Insights")
    
    print("\n🚀 EXECUTING COMPREHENSIVE EVALUATION PIPELINE...")
    
    results = pipeline.run_evaluation_pipeline()
    
    print("\n🎓 EVALUATION PIPELINE INSIGHTS:")
    print("   ✅ End-to-End Testing: Complete workflow validation")
    print("   ✅ Multi-Method Analysis: Comparative performance assessment")
    print("   ✅ Cost Optimization: Token usage and efficiency tracking")
    print("   ✅ Quality Assurance: Consistent evaluation standards")
    print("   ✅ Scalable Framework: Ready for production deployment")
    
    print("\n📚 WHAT THIS DEMONSTRATES:")
    print("   🎯 Systematic evaluation methodology")
    print("   🔍 Detailed pipeline operation explanation")
    print("   📊 Comprehensive results analysis")
    print("   💡 Performance optimization insights")
    print("   🚀 Production-ready evaluation framework")
