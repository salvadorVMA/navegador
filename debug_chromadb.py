#!/usr/bin/env python3
"""
Debug script to examine ChromaDB contents and metadata structure
"""

import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utility_functions import environment_setup, embedding_fun_openai

def examine_database():
    """Examine the structure and contents of the ChromaDB"""
    print("=" * 60)
    print("CHROMADB DATABASE EXAMINATION")
    print("=" * 60)
    
    # Setup environment
    client, db_f1 = environment_setup(embedding_fun_openai)
    
    # Get a sample of documents
    print("\n1. Getting sample documents...")
    sample = db_f1.peek(limit=20)
    
    print(f"Sample IDs ({len(sample['ids'])} items):")
    for i, doc_id in enumerate(sample['ids'][:10]):
        print(f"  {i+1}. {doc_id}")
    
    print(f"\nSample metadata ({len(sample['metadatas'])} items):")
    for i, metadata in enumerate(sample['metadatas'][:5]):
        print(f"  {i+1}. {metadata}")
    
    # Test different query approaches
    print("\n2. Testing different query approaches...")
    
    # Test 1: Query by type only
    print("\n2a. Query by type='question' only:")
    try:
        result = db_f1.query(
            query_embeddings=[embedding_fun_openai(["test query"])[0]],
            n_results=5,
            where={"type": {"$eq": "question"}}
        )
        print(f"   Found {len(result['ids'][0])} results")
        for doc_id in result['ids'][0][:3]:
            print(f"   - {doc_id}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 2: Get all documents with specific metadata
    print("\n2b. Get documents by IDs:")
    try:
        specific_ids = [doc_id for doc_id in sample['ids'][:3] if '__question' in doc_id]
        if specific_ids:
            result = db_f1.get(ids=specific_ids)
            print(f"   Successfully retrieved {len(result['ids'])} documents")
        else:
            print("   No question documents found in sample")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 3: Check topic IDs in metadata
    print("\n3. Analyzing topic ID patterns...")
    unique_qids = set()
    unique_types = set()
    
    for metadata in sample['metadatas']:
        if 'qid' in metadata:
            unique_qids.add(metadata['qid'])
        if 'type' in metadata:
            unique_types.add(metadata['type'])
    
    print(f"Unique QIDs found: {sorted(unique_qids)}")
    print(f"Unique types found: {sorted(unique_types)}")
    
    # Test 4: Check available topic IDs
    print("\n4. Checking available topic IDs...")
    try:
        from dataset_knowledge import rev_topic_dict
        print(f"Available topic IDs in rev_topic_dict: {list(rev_topic_dict.keys())}")
        
        # Check if any sample QIDs match the topic pattern
        for qid in unique_qids:
            for topic_id in rev_topic_dict.keys():
                if topic_id in qid:
                    print(f"   Match found: {qid} contains {topic_id}")
    except Exception as e:
        print(f"   Error loading topic dict: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    examine_database()
