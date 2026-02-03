#!/usr/bin/env python3
"""Debug ChromaDB query with $in operator"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_chromadb_query():
    """Debug the ChromaDB query with $in operator"""
    try:
        from variable_selector import client, db_f1, embedding_fun_openai, enrich_query_for_implications
        
        user_query = "quiero saber qué piensan los mexicanos sobre la educación"
        enriched_query = enrich_query_for_implications(user_query)
        query_emb = embedding_fun_openai([enriched_query])[0]
        
        print("🔍 DEBUGGING CHROMADB $IN QUERY")
        print("=" * 50)
        
        # Test the $in query
        type_lst = ["question", "summary", "implications"]
        
        print(f"Testing $in query with types: {type_lst}")
        try:
            tmp_res_q = db_f1.query(
                query_embeddings=[query_emb],
                n_results=20,
                where={"type": {"$in": type_lst}}
            )
            
            [tmp_res_ids] = tmp_res_q['ids']
            [tmp_res_distances] = tmp_res_q['distances']
            
            print(f"✅ $in query successful: {len(tmp_res_ids)} results")
            
            # Count by type
            type_counts = {}
            for doc_id in tmp_res_ids:
                doc_type = doc_id.split('__')[1] if '__' in doc_id else 'unknown'
                type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
            
            print(f"Type distribution: {type_counts}")
            
            # Show sample IDs
            for doc_type in type_lst:
                matching_ids = [id for id in tmp_res_ids if id.endswith(f'__{doc_type}')]
                print(f"  {doc_type}: {len(matching_ids)} results")
                if matching_ids:
                    print(f"    Sample: {matching_ids[:3]}")
            
        except Exception as e:
            print(f"❌ $in query failed: {e}")
            
            # Fall back to individual queries
            print("\n🔄 Trying individual queries...")
            for doc_type in type_lst:
                try:
                    tmp_res_q = db_f1.query(
                        query_embeddings=[query_emb],
                        n_results=10,
                        where={"type": {"$eq": doc_type}}
                    )
                    
                    [tmp_res_ids] = tmp_res_q['ids']
                    print(f"  {doc_type}: {len(tmp_res_ids)} results")
                    if tmp_res_ids:
                        # Filter by EDU
                        edu_ids = [id for id in tmp_res_ids if '|EDU' in id]
                        print(f"    EDU filtered: {len(edu_ids)} results")
                        if edu_ids:
                            print(f"    Sample EDU: {edu_ids[:3]}")
                except Exception as e:
                    print(f"  {doc_type}: Error - {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_chromadb_query()
