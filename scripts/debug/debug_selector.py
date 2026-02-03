#!/usr/bin/env python3
"""
Debug script to understand the database selector and filtering logic
"""

import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from variable_selector import _database_selector
from dataset_knowledge import tmp_topic_st, rev_topic_dict
from langchain_openai import ChatOpenAI
from utility_functions import environment_setup, embedding_fun_openai

def debug_database_selector():
    """Debug the database selector functionality"""
    print("=" * 60)
    print("DEBUGGING DATABASE SELECTOR")
    print("=" * 60)
    
    # Setup
    llm = ChatOpenAI(model="gpt-4o-mini")
    
    print(f"Available topic string (tmp_topic_st):")
    print(f"  {tmp_topic_st}")
    print()
    
    print(f"Available topic IDs in rev_topic_dict:")
    print(f"  {list(rev_topic_dict.keys())}")
    print()
    
    # Test queries
    test_queries = [
        "Show me variables about education and culture",
        "education",
        "culture",
        "identity and values",
        "medio ambiente",
        "all datasets"
    ]
    
    for query in test_queries:
        print(f"Testing query: '{query}'")
        try:
            selected_topics = _database_selector(query, tmp_topic_st, llm)
            print(f"  Selected topics: {selected_topics}")
        except Exception as e:
            print(f"  Error: {e}")
        print()

def debug_retrieval():
    """Debug the actual retrieval process"""
    print("=" * 60)
    print("DEBUGGING RETRIEVAL PROCESS")
    print("=" * 60)
    
    # Setup
    client, db_f1 = environment_setup(embedding_fun_openai)
    
    # Test with a known working topic
    test_topic_ids = ['IDE']  # We know this exists from our debug
    
    print(f"Testing retrieval with topic IDs: {test_topic_ids}")
    
    # Query for questions only
    result = db_f1.query(
        query_embeddings=[embedding_fun_openai(["test query"])[0]],
        n_results=10,
        where={"type": {"$eq": "question"}}
    )
    
    [tmp_res_ids] = result['ids']
    [tmp_res_distances] = result['distances']
    
    print(f"Found {len(tmp_res_ids)} question documents")
    print("Sample IDs:")
    for i, doc_id in enumerate(tmp_res_ids[:5]):
        print(f"  {i+1}. {doc_id}")
    
    # Test filtering
    filtered_ids = []
    for doc_id in tmp_res_ids:
        id_parts = doc_id.split('__')
        if len(id_parts) > 0:
            qid_part = id_parts[0]
            if any(f"|{topic_id}" in qid_part for topic_id in test_topic_ids):
                filtered_ids.append(doc_id)
    
    print(f"\nAfter filtering for topics {test_topic_ids}: {len(filtered_ids)} documents")
    print("Filtered IDs:")
    for i, doc_id in enumerate(filtered_ids[:5]):
        print(f"  {i+1}. {doc_id}")

if __name__ == "__main__":
    debug_database_selector()
    print("\n")
    debug_retrieval()
