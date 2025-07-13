"""
Test script to verify that the transversal analysis runs correctly with our fixes.
This runs just enough of the detailed analysis to test the JSON parsing.
"""

import sys
from detailed_analysis_optimized import get_transversal_analysis_optimized

def test_transversal_analysis():
    """Test the transversal analysis with a simple example"""
    
    # Sample expert statements (simplified for testing)
    test_statements = """
    * Los resultados de la encuesta indican un notable consenso entre los encuestados sobre temas políticos clave, como se evidencia en las preguntas p12|mock (58% apoyan) y p78|mock (62% en contra). Esta alineación sugiere un interés en la participación cívica.
    
    * Los hallazgos de la encuesta resaltan la percepción pública acerca de la gobernanza democrática y el papel de la Iglesia en la dinámica política, reflejando preocupaciones clave para los expertos en 'cultura política.' Las respuestas a las preguntas p35 (43% desaprobación) y p84_6 (38% acuerdo) muestran una tendencia hacia el descontento público.
    
    * Los resultados de la encuesta revelan una dicotomía significativa en la opinión pública respecto a la estabilidad política y el papel del gobierno en actividades económicas, como se refleja en las respuestas a las preguntas p3 (52% favorable) y p57_3 (47% en desacuerdo).
    """
    
    # Test query
    test_query = "¿Qué indica la encuesta sobre la cultura política y el papel del gobierno?"
    
    print("Running transversal analysis test...")
    try:
        # Run the transversal analysis
        result = get_transversal_analysis_optimized(
            tmp_smry_st=test_statements,
            user_query=test_query
        )
        
        # Check if we have the expected keys in the result
        if all(k in result for k in ['TOPIC_SUMMARIES', 'TOPIC_SUMMARY', 'QUERY_ANSWER']):
            print("✅ Transversal analysis successful!")
            print("\nTOPIC SUMMARIES:")
            for topic, summary in result['TOPIC_SUMMARIES'].items():
                print(f"  - {topic}: {summary[:100]}...")
                
            print("\nTOPIC SUMMARY:")
            print(result['TOPIC_SUMMARY'][:150] + "...")
            
            print("\nQUERY ANSWER:")
            print(result['QUERY_ANSWER'])
            return True
        else:
            print(f"❌ Missing expected keys in result. Found: {list(result.keys())}")
            return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    success = test_transversal_analysis()
    sys.exit(0 if success else 1)
