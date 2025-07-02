#!/usr/bin/env python3
"""
Debug script to test filtering with actual topic IDs that exist in the results
"""

import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utility_functions import environment_setup, embedding_fun_openai

def test_filtering_with_existing_topics():
    """Test filtering with topic IDs that actually exist in the results"""
    print("=" * 60)
    print("TESTING FILTERING WITH EXISTING TOPICS")
    print("=" * 60)
    
    # Setup
    client, db_f1 = environment_setup(embedding_fun_openai)
    
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
    
    # Extract unique topic IDs from the results
    unique_topics = set()
    for doc_id in tmp_res_ids:
        id_parts = doc_id.split('__')
        if len(id_parts) > 0:
            qid_part = id_parts[0]
            # Extract topic from pattern like 'p15_5|EDU'
            if '|' in qid_part:
                topic = qid_part.split('|')[1]
                unique_topics.add(topic)
    
    print(f"\nUnique topics found in results: {sorted(unique_topics)}")
    
    # Test filtering with each topic
    for topic in sorted(unique_topics):
        print(f"\nTesting filtering for topic: {topic}")
        
        filtered_ids = []
        for doc_id in tmp_res_ids:
            id_parts = doc_id.split('__')
            if len(id_parts) > 0:
                qid_part = id_parts[0]
                if f"|{topic}" in qid_part:
                    filtered_ids.append(doc_id)
        
        print(f"  Found {len(filtered_ids)} documents for topic {topic}")
        if filtered_ids:
            print(f"  Sample: {filtered_ids[0]}")

if __name__ == "__main__":
    test_filtering_with_existing_topics()
