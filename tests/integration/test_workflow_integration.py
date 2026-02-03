"""
Test the complete agent workflow with detailed analysis integration.
"""

import sys
sys.path.append('/Users/salvadorVMA/Google Drive/01 Proyectos/2025/navegador')

def test_full_workflow():
    """Test the complete workflow from query to detailed analysis"""
    try:
        from agent import create_agent
        from langchain_core.messages import HumanMessage
        
        print("🔧 Creating agent...")
        agent = create_agent(enable_persistence=False)
        
        print("📝 Testing detailed analysis query...")
        
        # Initialize state
        initial_state = {
            "messages": [HumanMessage(content="What patterns exist in Mexican cultural identity?")],
            "intent": "",
            "user_query": "",
            "original_query": "",
            "dataset": ["all"], 
            "selected_variables": [],
            "analysis_type": "detailed_report",
            "user_approved": False,
            "analysis_result": {}
        }
        
        # Test intent detection
        print("🎯 Testing intent detection...")
        result = agent.invoke(initial_state)
        
        print(f"✅ Workflow completed!")
        print(f"   Final state keys: {list(result.keys())}")
        print(f"   Number of messages: {len(result.get('messages', []))}")
        print(f"   Intent detected: {result.get('intent', 'none')}")
        
        # Check if analysis was triggered
        if 'analysis_result' in result:
            analysis = result['analysis_result']
            print(f"   Analysis executed: {bool(analysis)}")
            if analysis:
                print(f"   Analysis success: {analysis.get('success', False)}")
                print(f"   Analysis type: {analysis.get('analysis_type', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Full workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_detailed_analysis():
    """Test just the detailed analysis with real variables"""
    try:
        from run_analysis import run_analysis
        
        print("🔬 Testing detailed analysis with real variables...")
        
        # Use some real variable IDs that should exist in the database
        real_variables = ["p1_1a_1|IDE", "p2_1a_1|IDE", "p3_1|IDE"]
        user_query = "What do these variables tell us about Mexican identity?"
        
        result = run_analysis(
            analysis_type="detailed_report",
            selected_variables=real_variables,
            user_query=user_query
        )
        
        print(f"✅ Detailed analysis completed!")
        print(f"   Success: {result.get('success', False)}")
        print(f"   Has report: {'formatted_report' in result}")
        
        if result.get('success', False):
            report = result.get('formatted_report', '')
            print(f"   Report length: {len(report)} characters")
            print(f"   Sample from report: {report[:200]}...")
        else:
            print(f"   Error: {result.get('error', 'Unknown error')}")
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ Simple detailed analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Testing Complete Workflow Integration")
    print("=" * 50)
    
    print("\n1️⃣ Testing simple detailed analysis...")
    test1 = test_simple_detailed_analysis()
    
    print("\n2️⃣ Testing full agent workflow...")  
    test2 = test_full_workflow()
    
    print("\n" + "=" * 50)
    print("📊 FINAL SUMMARY")
    print("=" * 50)
    
    if test1:
        print("✅ Detailed analysis integration: WORKING")
    else:
        print("❌ Detailed analysis integration: FAILED")
        
    if test2:
        print("✅ Full agent workflow: WORKING") 
    else:
        print("❌ Full agent workflow: FAILED")
    
    if test1 and test2:
        print("\n🎉 Integration is complete and working!")
        print("The agent can now generate real detailed reports using the notebook logic.")
    else:
        print("\n⚠️  Some issues remain. Check the errors above.")
