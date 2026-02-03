"""
Test script to verify that the JSON fix functions work correctly.
"""

from fix_transversal_json import fix_json_format
import json

def test_trailing_comma_fix():
    # Test case from the error we saw
    test_json = """{
  "TOPIC_SUMMARIES": {
    "CULTURA POLITICA": "Los resultados de la encuesta indican un notable consenso entre los encuestados sobre temas políticos clave, como se evidencia en las preguntas p12|mock y p78|mock. Esta alineación sugiere un interés en la participación cívica y la concienciación política, lo que puede informar a analistas y estrategas en la identificación de preocupaciones de los votantes y el desarrollo de estrategias de compromiso. Además, la alta proporción de respuestas de 'no sabe/no contesta' crea oportunidades para que los partidos políticos aborden las incertidumbres y fomenten una mayor participación política entre un electorado potencialmente desvinculado.",
    "GOBIERNO Y RELIGION": "Los hallazgos de la encuesta resaltan la percepción pública acerca de la gobernanza democrática y el papel de la Iglesia en la dinámica política, reflejando preocupaciones clave para los expertos en 'cultura política.' Las respuestas a las preguntas p35 y p84_6 muestran una tendencia hacia el descontento público con ciertos aspectos de la gobernanza democrática, sugiriendo que podrían ser necesarias reformas políticas. Además, las percepciones sobre la influencia de la Iglesia pueden moldear la participación cívica y las decisiones políticas, lo que ofrece a investigadores y formuladores de políticas una comprensión más clara de la opinión pública para adaptar sus iniciativas.",
    "ESTABILIDAD POLITICA Y ECONOMIA": "Los resultados de la encuesta revelan una dicotomía significativa en la opinión pública respecto a la estabilidad política y el papel del gobierno en actividades económicas, como se refleja en las respuestas a las preguntas p3 y p57_3. Mientras que una parte de la población muestra una visión favorable hacia ciertas intervenciones gubernamentales, otra parte expresa un fuerte desacuerdo, lo que sugiere una falta de consenso que podría afectar las percepciones de estabilidad y efectividad política. Esta retroalimentación polarizada indica la necesidad de que los interesados adopten estrategias matizadas que aborden estas perspectivas diversas.",
  },
  "TOPIC_SUMMARY": "La encuesta revela un consenso significativo en temas políticos clave, como se observa en las respuestas a preguntas p12|mock, p78|mock y p35. La percepción pública también muestra descontento con ciertos aspectos de la gobernanza democrática y el papel de la Iglesia, lo que sugiere que se requieren reformas políticas. Además, hay una notable división en opiniones sobre la estabilidad política y el papel del gobierno en la economía, lo que resalta la necesidad de estrategias políticas que consideren estos puntos de vista diversos.",
  "QUERY_ANSWER": "Los resultados de la encuesta sugieren que existe un consenso notable sobre asuntos políticos, así como un descontento con la gobernanza democrática. Además, la polarización sobre el papel del gobierno en la economía indica que se requieren enfoques estratégicos para abordar estas discrepancias." 
}"""

    # Fix the JSON
    fixed_json = fix_json_format(test_json)
    
    # Try to parse the fixed JSON
    try:
        parsed = json.loads(fixed_json)
        print("✅ JSON successfully fixed and parsed")
        return True
    except json.JSONDecodeError as e:
        print(f"❌ JSON fix failed: {e}")
        return False

if __name__ == "__main__":
    # Run the tests
    print("Testing JSON fix functions...")
    test_trailing_comma_fix()
