#!/usr/bin/env python3
"""
Compare simultaneous vs separate retrieval methods
"""

import os
import sys
from utility_functions import environment_setup, embedding_fun_openai
from variable_selector import (
    _variable_selector, retrieve_by_type_and_topics, retrieve_all_types_simultaneously,
    enrich_query_for_implications, _database_selector
)
from dataset_knowledge import tmp_topic_st, rev_topic_dict

# Set up models
mod_alto = 'gpt-4.1-2025-04-14' 
mod_bajo = 'gpt-4.1-nano-2025-04-14'
mod_med = 'gpt-4.1-mini-2025-04-14'

def compare_retrieval_methods():
    """Compare separate vs simultaneous retrieval methods"""
    
    print("=== COMPARISON: Separate vs Simultaneous Retrieval ===")
    
    # Set up ChromaDB
    client, db_f1 = environment_setup(embedding_fun_openai)
    
    # Test query
    user_query = "What do Mexicans think about education?"
    print(f"🔍 Query: {user_query}")
    
    # Get enriched query and embedding
    enriched_query = enrich_query_for_implications(user_query)
    query_emb = embedding_fun_openai([enriched_query])[0]
    print(f"📝 Enriched query: {enriched_query[:100]}...")
    
    # Topic selection
    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(model=mod_med, temperature=0.2)
    selected_topics = _database_selector(user_query, tmp_topic_st, llm)
    print(f"📊 Selected topics: {selected_topics}")
    
    print(f"\n--- Method 1: Separate Queries Per Type ---")
    
    # Test separate queries
    import time
    start_time = time.time()
    
    separate_results = retrieve_by_type_and_topics(
        db_f1,
        query_emb,
        topic_ids=selected_topics,
        type_lst=["question", "summary", "implications"],
        n_results=20
    )
    
    separate_time = time.time() - start_time
    print(f"⏱️ Time taken: {separate_time:.2f} seconds")
    
    # Analyze results
    print(f"📊 Results per type (separate):")
    for doc_type, results in separate_results.items():
        print(f"   - {doc_type}: {len(results)} results")
        if results:
            # Show distance range
            distances = list(results.values())
            print(f"     Distance range: {min(distances):.3f} - {max(distances):.3f}")
            
            # Show top 3 results
            top_3 = list(results.items())[:3]
            for doc_id, distance in top_3:
                qid = doc_id.split('__')[0]
                print(f"     • {qid}: {distance:.3f}")
    
    print(f"\n--- Method 2: Simultaneous Query for All Types ---")
    
    # Test simultaneous query
    start_time = time.time()
    
    simultaneous_results = retrieve_all_types_simultaneously(
        db_f1,
        query_emb,
        topic_ids=selected_topics,
        type_lst=["question", "summary", "implications"],
        n_results=20
    )
    
    simultaneous_time = time.time() - start_time
    print(f"⏱️ Time taken: {simultaneous_time:.2f} seconds")
    
    # Analyze results
    print(f"📊 Results per type (simultaneous):")
    for doc_type, results in simultaneous_results.items():
        print(f"   - {doc_type}: {len(results)} results")
        if results:
            # Show distance range
            distances = list(results.values())
            print(f"     Distance range: {min(distances):.3f} - {max(distances):.3f}")
            
            # Show top 3 results
            top_3 = list(results.items())[:3]
            for doc_id, distance in top_3:
                qid = doc_id.split('__')[0]
                print(f"     • {qid}: {distance:.3f}")
    
    print(f"\n--- Comparison Summary ---")
    print(f"⏱️ Speed:")
    print(f"   - Separate queries: {separate_time:.2f}s")
    print(f"   - Simultaneous query: {simultaneous_time:.2f}s")
    print(f"   - Speedup: {separate_time/simultaneous_time:.1f}x")
    
    print(f"📊 Result counts:")
    separate_total = sum(len(results) for results in separate_results.values())
    simultaneous_total = sum(len(results) for results in simultaneous_results.values())
    print(f"   - Separate queries: {separate_total} total results")
    print(f"   - Simultaneous query: {simultaneous_total} total results")
    
    print(f"🎯 Quality comparison:")
    for doc_type in ["question", "summary", "implications"]:
        sep_count = len(separate_results.get(doc_type, {}))
        sim_count = len(simultaneous_results.get(doc_type, {}))
        print(f"   - {doc_type}: {sep_count} vs {sim_count}")
        
        # Compare overlap in top results
        if sep_count > 0 and sim_count > 0:
            sep_top_ids = set(list(separate_results[doc_type].keys())[:10])
            sim_top_ids = set(list(simultaneous_results[doc_type].keys())[:10])
            overlap = len(sep_top_ids.intersection(sim_top_ids))
            print(f"     Overlap in top 10: {overlap}/10 ({overlap*10}%)")
    
    print(f"\n--- Testing Full Variable Selection ---")
    
    # Test full variable selection with both methods
    print(f"🧪 Testing separate queries method:")
    try:
        start_time = time.time()
        topic_ids_1, vars_dict_1, grade_dict_1 = _variable_selector(
            user_query, tmp_topic_st, llm, top_vals=10, use_simultaneous_retrieval=False
        )
        separate_full_time = time.time() - start_time
        print(f"   ✅ Success: {len(vars_dict_1)} vars, {len(grade_dict_1)} graded")
        print(f"   ⏱️ Time: {separate_full_time:.2f}s")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    print(f"🧪 Testing simultaneous query method:")
    try:
        start_time = time.time()
        topic_ids_2, vars_dict_2, grade_dict_2 = _variable_selector(
            user_query, tmp_topic_st, llm, top_vals=10, use_simultaneous_retrieval=True
        )
        simultaneous_full_time = time.time() - start_time
        print(f"   ✅ Success: {len(vars_dict_2)} vars, {len(grade_dict_2)} graded")
        print(f"   ⏱️ Time: {simultaneous_full_time:.2f}s")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

if __name__ == "__main__":
    compare_retrieval_methods()
