#!/usr/bin/env python3
"""Debug script to investigate variable selection issues"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_variable_selection():
    """Debug the variable selection process step by step"""
    try:
        from variable_selector import (
            _variable_selector, enrich_query_for_implications, 
            _database_selector, retrieve_by_type_and_topics,
            client, db_f1, embedding_fun_openai
        )
        from dataset_knowledge import tmp_topic_st, rev_topic_dict
        from langchain_openai import ChatOpenAI
        
        # Test query
        user_query = "quiero saber qué piensan los mexicanos sobre la educación"
        
        print("🔍 DEBUGGING VARIABLE SELECTION")
        print("=" * 60)
        print(f"Original query: '{user_query}'")
        
        # Step 1: Query enrichment
        enriched_query = enrich_query_for_implications(user_query)
        print(f"\n1️⃣ ENRICHED QUERY:")
        print(f"   {enriched_query}")
        
        # Step 2: Database selection
        llm = ChatOpenAI(model="gpt-4o-mini")
        topic_ids = _database_selector(user_query, tmp_topic_st, llm)
        print(f"\n2️⃣ SELECTED TOPICS:")
        print(f"   Topic IDs: {topic_ids}")
        print(f"   Available topics: {list(rev_topic_dict.keys())}")
        
        # Step 3: Embedding
        print(f"\n3️⃣ EMBEDDING QUERY...")
        query_emb = embedding_fun_openai([enriched_query])[0]
        print(f"   Embedding vector length: {len(query_emb)}")
        print(f"   First 5 values: {query_emb[:5]}")
        
        # Step 4: Test individual type queries
        print(f"\n4️⃣ TESTING INDIVIDUAL TYPE QUERIES:")
        type_lst = ["question", "summary", "implications"]
        
        for doc_type in type_lst:
            print(f"\n   Testing type: {doc_type}")
            
            # Query ChromaDB directly for this type
            tmp_res_q = db_f1.query(
                query_embeddings=[query_emb],
                n_results=20,  # Small number for debugging
                where={"type": {"$eq": doc_type}}
            )
            
            [tmp_res_ids] = tmp_res_q['ids']
            [tmp_res_distances] = tmp_res_q['distances']
            
            print(f"   Raw results: {len(tmp_res_ids)} documents")
            if tmp_res_ids:
                print(f"   Sample IDs: {tmp_res_ids[:3]}")
                print(f"   Sample distances: {tmp_res_distances[:3]}")
            
            # Filter by topics
            filtered_ids = []
            filtered_distances = []
            
            for i, doc_id in enumerate(tmp_res_ids):
                id_parts = doc_id.split('__')
                if len(id_parts) > 0:
                    qid_part = id_parts[0]
                    # Check if any of the topic_ids is in the QID part
                    if any(f"|{topic_id}" in qid_part for topic_id in topic_ids):
                        filtered_ids.append(doc_id)
                        filtered_distances.append(tmp_res_distances[i])
                        if len(filtered_ids) >= 10:  # Limit for debugging
                            break
            
            print(f"   After topic filtering: {len(filtered_ids)} documents")
            if filtered_ids:
                print(f"   Filtered IDs: {filtered_ids[:3]}")
        
        # Step 5: Test the full retrieval function
        print(f"\n5️⃣ TESTING FULL RETRIEVAL:")
        tmp_dist_dict = retrieve_by_type_and_topics(
            db_f1, 
            query_emb, 
            topic_ids=topic_ids,
            type_lst=type_lst,
            n_results=10
        )
        
        for doc_type, results in tmp_dist_dict.items():
            print(f"   {doc_type}: {len(results)} results")
            if results:
                sample_ids = list(results.keys())[:3]
                print(f"   Sample IDs: {sample_ids}")
        
        # Step 6: Check what happens in the grading process
        print(f"\n6️⃣ CHECKING GRADING PROCESS:")
        
        # Get documents for grading
        tmp_list = []
        for doc_type in type_lst:
            for doc_id in list(tmp_dist_dict[doc_type].keys())[:5]:  # Just first 5 for debugging
                base_id = doc_id.split('__')[0]
                tmp_list.append(f"{base_id}__{doc_type}")
        
        print(f"   Document IDs for grading: {len(tmp_list)}")
        if tmp_list:
            print(f"   Sample: {tmp_list[:3]}")
            
            # Try to retrieve these documents
            try:
                result_by_ids = db_f1.get(ids=tmp_list)
                print(f"   Retrieved documents: {len(result_by_ids.get('ids', []))}")
                if result_by_ids.get('documents'):
                    print(f"   Sample document: {result_by_ids['documents'][0][:100]}...")
            except Exception as e:
                print(f"   Error retrieving documents: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_variable_selection()
