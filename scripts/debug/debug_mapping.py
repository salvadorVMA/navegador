#!/usr/bin/env python3
"""
Debug script to understand the topic mapping structure
"""

import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dataset_knowledge import rev_topic_dict, enc_nom_dict, rev_enc_nom_dict

def debug_topic_mapping():
    """Debug the topic mapping dictionaries"""
    print("=" * 60)
    print("DEBUGGING TOPIC MAPPING")
    print("=" * 60)
    
    print("enc_nom_dict (full_name -> abbrev):")
    for k, v in list(enc_nom_dict.items())[:5]:
        print(f"  {k} -> {v}")
    print(f"  ... and {len(enc_nom_dict)-5} more")
    print()
    
    print("rev_enc_nom_dict (abbrev -> full_name):")
    for k, v in list(rev_enc_nom_dict.items())[:5]:
        print(f"  {k} -> {v}")
    print(f"  ... and {len(rev_enc_nom_dict)-5} more")
    print()
    
    print("rev_topic_dict (abbrev -> display_name):")
    for k, v in list(rev_topic_dict.items())[:5]:
        print(f"  {k} -> {v}")
    print(f"  ... and {len(rev_topic_dict)-5} more")
    print()
    
    # Look for education and culture related topics
    print("Education and culture related topics:")
    for abbrev, full_name in rev_enc_nom_dict.items():
        if any(word in full_name.lower() for word in ['educacion', 'cultura']):
            print(f"  {abbrev} -> {full_name} -> {rev_topic_dict.get(abbrev, 'N/A')}")

if __name__ == "__main__":
    debug_topic_mapping()
