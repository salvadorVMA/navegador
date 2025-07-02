#!/usr/bin/env python3
"""
Test script for improved keyword extraction
"""

import re

def extract_search_keywords(user_query: str, detected_lang: str = "es") -> str:
    """
    Extract key search terms from user query for variable retrieval.
    
    Examples:
    - "quiero saber sobre las opiniones de la salud en México" -> "salud"
    - "I want to know about attitudes about health" -> "health attitudes"
    - "tell me about corruption in government" -> "corruption government"
    """
    query_lower = user_query.lower()
    
    # More comprehensive filler patterns with better Spanish support
    filler_patterns = [
        # English fillers
        r'\bi want to know\b', r'\btell me about\b', r'\bshow me\b', r'\bfind\b',
        r'\bif mexicans?\b', r'\bwhat do mexicans?\b', r'\bhow do mexicans?\b',
        r'\babout mexicans?\b', r'\bin mexico\b', r'\bmexican people\b',
        r'\bbased on the survey about\b', r'\bfrom the survey\b', r'\bin the data\b',
        r'\baccording to\b', r'\bdo\b', r'\bdoes\b', r'\bare\b', r'\bis\b',
        r'\bopinions?\b', r'\bviews?\b', r'\bthoughts?\b', r'\battitudes?\b',
        r'\babout the\b', r'\bof the\b', r'\bin the\b', r'\bon the\b',
        
        # Spanish fillers - much more comprehensive
        r'\bquiero saber\b', r'\bquisiera saber\b', r'\bme gustaría saber\b',
        r'\bdime sobre\b', r'\bmuéstrame\b', r'\bencuentra\b', r'\bbusca\b',
        r'\bsi los mexicanos?\b', r'\bqué piensan los mexicanos?\b', r'\bcómo ven los mexicanos?\b',
        r'\bsobre los mexicanos?\b', r'\ben méxico\b', r'\bel pueblo mexicano\b',
        r'\bbasado en la encuesta sobre\b', r'\bde la encuesta\b', r'\ben los datos\b',
        r'\bsegún\b', r'\bhacen\b', r'\bhace\b', r'\bson\b', r'\bes\b',
        r'\bopiniones?\b', r'\blas opiniones?\b', r'\bpensamiento\b', r'\bactitudes?\b',
        r'\bpareceres?\b', r'\bcriterios?\b', r'\bjuicios?\b',
        # More Spanish stop words and phrases
        r'\bsobre las?\b', r'\bde las?\b', r'\ben las?\b', r'\bcon las?\b',
        r'\bsobre los?\b', r'\bde los?\b', r'\ben los?\b', r'\bcon los?\b',
        r'\bsobre la\b', r'\bde la\b', r'\ben la\b', r'\bcon la\b',
        r'\bsobre el\b', r'\bde el\b', r'\bdel\b', r'\ben el\b', r'\bcon el\b',
        r'\bque\b', r'\bcomo\b', r'\bcómo\b', r'\bpor que\b', r'\bporque\b',
        r'\bdonde\b', r'\bdónde\b', r'\bcuando\b', r'\bcuándo\b',
        r'\bcual\b', r'\bcuál\b', r'\bcuales\b', r'\bcuáles\b',
        r'\bpara\b', r'\bpor\b', r'\bcon\b', r'\bsin\b', r'\bentre\b',
        r'\bhacia\b', r'\bdesde\b', r'\bhasta\b', r'\bante\b', r'\bbajo\b',
        r'\bun\b', r'\buna\b', r'\bunos\b', r'\bunas\b', r'\bel\b', r'\bla\b', r'\blos\b', r'\blas\b'
    ]
    
    # Apply filler removal
    cleaned_query = query_lower
    for pattern in filler_patterns:
        cleaned_query = re.sub(pattern, ' ', cleaned_query)
    
    # Remove extra whitespace and punctuation
    cleaned_query = re.sub(r'[^\w\s]', ' ', cleaned_query)
    cleaned_query = ' '.join(cleaned_query.split())
    
    # Filter out remaining very short words (< 3 characters) which are usually not informative
    words = cleaned_query.split()
    meaningful_words = [word for word in words if len(word) >= 3]
    
    # If we have meaningful words, use them; otherwise fall back to original
    if meaningful_words:
        return ' '.join(meaningful_words)
    elif len(cleaned_query.strip()) >= 3:
        return cleaned_query.strip()
    else:
        return user_query.strip()

# Test cases
test_queries = [
    "quiero saber sobre las opiniones de la salud en México",
    "I want to know about attitudes about health",
    "tell me about corruption in government",
    "ok",
    "sí, proceder con el análisis",
    "quiero saber sobre las de la educación",
    "show me variables about environment"
]

print("=== Keyword Extraction Test ===")
for query in test_queries:
    result = extract_search_keywords(query)
    print(f"Original: '{query}'")
    print(f"Keywords: '{result}'")
    print("-" * 50)
