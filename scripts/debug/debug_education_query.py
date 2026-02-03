#!/usr/bin/env python3
"""
Debug script to investigate the education query issue.
Tests the specific query "What do Mexicans think about education?" step by step.
"""

import os
import sys
from utility_functions import environment_setup, embedding_fun_openai, get_answer
from variable_selector import _variable_selector, _database_selector, retrieve_by_type_and_topics, enrich_query_for_implications
from dataset_knowledge import tmp_topic_st, rev_topic_dict

# Set up models
mod_alto = 'gpt-4.1-2025-04-14' 
mod_bajo = 'gpt-4.1-nano-2025-04-14'
mod_med = 'gpt-4.1-mini-2025-04-14'

def debug_education_query():
    """Debug the education query step by step"""
    
    print("=== DEBUG: Education Query Analysis ===")
    
    # Set up ChromaDB
    client, db_f1 = environment_setup(embedding_fun_openai)
    
    # Test query
    user_query = "What do Mexicans think about education?"
    print(f"🔍 Query: {user_query}")
    
    # Step 1: Test query enrichment
    print("\n--- Step 1: Query Enrichment ---")
    enriched_query = enrich_query_for_implications(user_query)
    print(f"📝 Enriched query: {enriched_query}")
    
    # Step 2: Test topic selection
    print("\n--- Step 2: Topic Selection ---")
    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(model=mod_med, temperature=0.2)
    
    selected_topics = _database_selector(user_query, tmp_topic_st, llm)
    print(f"📊 Selected topics: {selected_topics}")
    print(f"📋 Topic meanings: {[rev_topic_dict.get(t, 'Unknown') for t in selected_topics]}")
    
    # Step 3: Test embedding and retrieval
    print("\n--- Step 3: Embedding and Retrieval ---")
    query_emb = embedding_fun_openai([enriched_query])[0]
    print(f"🔢 Query embedding dimension: {len(query_emb)}")
    
    # Test retrieval with different topic sets
    print("\n   Testing with selected topics:")
    tmp_dist_dict = retrieve_by_type_and_topics(
        db_f1, 
        query_emb, 
        topic_ids=selected_topics,
        type_lst=["question", "summary", "implications"],
        n_results=20
    )
    
    print(f"   Results per type:")
    for doc_type, results in tmp_dist_dict.items():
        print(f"   - {doc_type}: {len(results)} results")
        if results:
            # Show a few sample IDs and their distances
            sample_items = list(results.items())[:3]
            for doc_id, distance in sample_items:
                print(f"     • {doc_id}: {distance:.3f}")
    
    print("\n   Testing with ALL topics:")
    tmp_dist_dict_all = retrieve_by_type_and_topics(
        db_f1, 
        query_emb, 
        topic_ids=None,  # All topics
        type_lst=["question", "summary", "implications"],
        n_results=20
    )
    
    print(f"   Results per type (all topics):")
    for doc_type, results in tmp_dist_dict_all.items():
        print(f"   - {doc_type}: {len(results)} results")
        if results:
            # Show a few sample IDs and their distances
            sample_items = list(results.items())[:3]
            for doc_id, distance in sample_items:
                print(f"     • {doc_id}: {distance:.3f}")
    
    # Step 4: Look for education-related questions specifically
    print("\n--- Step 4: Education Content Analysis ---")
    
    # Check if there are any education-related documents in the database
    print("   Searching for education-related content...")
    
    # Query for education-related content directly
    education_query_emb = embedding_fun_openai(["education school teaching learning academic"])[0]
    
    education_results = retrieve_by_type_and_topics(
        db_f1,
        education_query_emb,
        topic_ids=None,  # Search all topics
        type_lst=["question"],
        n_results=50
    )
    
    print(f"   Education-related questions found: {len(education_results['question'])}")
    
    if education_results['question']:
        print("   Top education-related questions:")
        for i, (doc_id, distance) in enumerate(list(education_results['question'].items())[:5]):
            # Get the actual content
            doc_content = db_f1.get(ids=[f"{doc_id}__question"])
            if doc_content and doc_content['documents']:
                content = doc_content['documents'][0][:200] + "..." if len(doc_content['documents'][0]) > 200 else doc_content['documents'][0]
                print(f"   {i+1}. {doc_id} (dist: {distance:.3f})")
                print(f"      Content: {content}")
    
    # Step 5: Full variable selection test
    print("\n--- Step 5: Full Variable Selection Test ---")
    
    try:
        selected_topics, tmp_pre_res_dict, tmp_grade_dict = _variable_selector(
            user_query, 
            tmp_topic_st, 
            llm, 
            top_vals=10
        )
        
        print(f"✅ Variable selection completed successfully")
        print(f"📊 Selected topics: {selected_topics}")
        print(f"📋 Retrieved documents: {len(tmp_pre_res_dict)}")
        print(f"🎯 Graded variables: {len(tmp_grade_dict)}")
        
        if tmp_grade_dict:
            print("   Top graded variables:")
            for var_id, grade_info in list(tmp_grade_dict.items())[:5]:
                grade = list(grade_info.keys())[0] if grade_info else 0
                explanation = list(grade_info.values())[0] if grade_info else "No explanation"
                print(f"   - {var_id}: Grade {grade}")
                print(f"     {explanation}")
        
    except Exception as e:
        print(f"❌ Variable selection failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_education_query()
