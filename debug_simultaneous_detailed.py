#!/usr/bin/env python3
"""
Debug the simultaneous retrieval method
"""

import os
import sys
from utility_functions import environment_setup, embedding_fun_openai
from variable_selector import enrich_query_for_implications, _database_selector
from dataset_knowledge import tmp_topic_st, rev_topic_dict

# Set up models
mod_med = 'gpt-4.1-mini-2025-04-14'

def debug_simultaneous_retrieval():
    """Debug why simultaneous retrieval only returns implications"""
    
    print("=== DEBUG: Simultaneous Retrieval ===")
    
    # Set up ChromaDB
    client, db_f1 = environment_setup(embedding_fun_openai)
    
    # Test query
    user_query = "What do Mexicans think about education?"
    print(f"🔍 Query: {user_query}")
    
    # Get enriched query and embedding
    enriched_query = enrich_query_for_implications(user_query)
    query_emb = embedding_fun_openai([enriched_query])[0]
    
    # Topic selection
    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(model=mod_med, temperature=0.2)
    selected_topics = _database_selector(user_query, tmp_topic_st, llm)
    print(f"📊 Selected topics: {selected_topics}")
    
    type_lst = ["question", "summary", "implications"]
    n_results = 20
    
    print(f"\n--- ChromaDB Query Debug ---")
    
    # Single query for all types - exactly what the function does
    tmp_res_q = db_f1.query(
        query_embeddings=[query_emb],
        n_results=n_results * len(type_lst) * 2,  # 120 results
        where={"type": {"$in": type_lst}}
    )
    
    [tmp_res_ids] = tmp_res_q['ids']
    [tmp_res_distances] = tmp_res_q['distances']
    
    print(f"📋 Total results retrieved: {len(tmp_res_ids)}")
    
    # Analyze what we got
    print(f"\n--- Analyzing Retrieved Results ---")
    
    type_count = {}
    topic_count = {}
    topic_type_count = {}
    
    for i, doc_id in enumerate(tmp_res_ids):
        # Extract parts
        id_parts = doc_id.split('__')
        if len(id_parts) == 2:
            qid_part, doc_type = id_parts
            
            # Count by type
            type_count[doc_type] = type_count.get(doc_type, 0) + 1
            
            # Extract topic
            topic = None
            for t_id in selected_topics:
                if f"|{t_id}" in qid_part:
                    topic = t_id
                    break
            
            # Count by topic
            if topic:
                topic_count[topic] = topic_count.get(topic, 0) + 1
                key = f"{topic}_{doc_type}"
                topic_type_count[key] = topic_type_count.get(key, 0) + 1
    
    print(f"📊 Results by type:")
    for doc_type in type_lst:
        count = type_count.get(doc_type, 0)
        print(f"   - {doc_type}: {count}")
    
    print(f"📊 Results by topic:")
    for topic in selected_topics:
        count = topic_count.get(topic, 0)
        print(f"   - {topic}: {count}")
    
    print(f"📊 Results by topic + type:")
    for topic in selected_topics:
        for doc_type in type_lst:
            key = f"{topic}_{doc_type}"
            count = topic_type_count.get(key, 0)
            print(f"   - {topic} {doc_type}: {count}")
    
    print(f"\n--- Manual Filtering Process ---")
    
    # Group results by type and filter by topic_ids - replicate the function logic
    tmp_dist_dict = {doc_type: {} for doc_type in type_lst}
    
    for i, doc_id in enumerate(tmp_res_ids):
        # Extract the type and QID from the document ID
        id_parts = doc_id.split('__')
        if len(id_parts) == 2:
            qid_part, doc_type = id_parts
            
            print(f"Processing: {doc_id} -> QID: {qid_part}, Type: {doc_type}")
            
            # Check if this type is in our list 
            if doc_type in type_lst:
                print(f"   ✅ Type {doc_type} is in type_lst")
                
                # Check if any of the topic_ids is in the QID part
                topic_match = False
                for topic_id in selected_topics:
                    if f"|{topic_id}" in qid_part:
                        topic_match = True
                        print(f"   ✅ Topic {topic_id} matches in {qid_part}")
                        break
                
                if topic_match:
                    # Only add if we haven't reached the limit for this type
                    current_count = len(tmp_dist_dict[doc_type])
                    if current_count < n_results:
                        tmp_dist_dict[doc_type][doc_id] = tmp_res_distances[i]
                        print(f"   ✅ Added to {doc_type} (count: {current_count + 1})")
                    else:
                        print(f"   ❌ {doc_type} limit reached ({n_results})")
                else:
                    print(f"   ❌ No topic match for {qid_part}")
            else:
                print(f"   ❌ Type {doc_type} not in {type_lst}")
    
    # Report final results
    print(f"\n--- Final Filtered Results ---")
    for doc_type in type_lst:
        results_count = len(tmp_dist_dict[doc_type])
        print(f"📋 {doc_type}: {results_count} results")
        
        if tmp_dist_dict[doc_type]:
            sample_items = list(tmp_dist_dict[doc_type].items())[:3]
            for doc_id, distance in sample_items:
                qid = doc_id.split('__')[0]
                print(f"     • {qid}: {distance:.3f}")

if __name__ == "__main__":
    debug_simultaneous_retrieval()
