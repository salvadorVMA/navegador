"""
Utility script to check cache statistics and performance metrics.

Usage:
    python check_cache_stats.py
"""

import sys
from performance_optimization import performance_monitor, _llm_cache, get_cache_stats

def print_separator():
    print("=" * 80)

def main():
    print_separator()
    print("NAVEGADOR CACHE STATISTICS")
    print_separator()

    # Get overall stats
    try:
        stats = get_cache_stats()

        print("\n📊 LLM Call Statistics:")
        print(f"   Total LLM calls: {stats.get('llm_calls', 0)}")
        print(f"   Cache hit rate: {stats.get('cache_hit_rate', 0)}%")

        # Get cache details
        cache_stats = stats.get('cache_stats', {})
        print(f"\n💾 Cache Status:")
        print(f"   Total cached entries: {cache_stats.get('total_entries', 0)}")
        print(f"   Total cache hits: {cache_stats.get('total_hits', 0)}")
        print(f"   Max cache size: {cache_stats.get('max_size', 0)}")
        print(f"   TTL (seconds): {cache_stats.get('ttl_seconds', 0)} ({cache_stats.get('ttl_seconds', 0) / 3600:.1f} hours)")

        # Analysis times
        avg_times = stats.get('average_times_by_type', {})
        if avg_times:
            print(f"\n⏱️  Average Analysis Times:")
            for analysis_type, avg_time in avg_times.items():
                print(f"   {analysis_type}: {avg_time}s")

        print(f"\n⏰ Total Analysis Time: {stats.get('total_analysis_time', 0)}s")

        # Calculate cost savings
        llm_calls = stats.get('llm_calls', 0)
        cache_hit_rate = stats.get('cache_hit_rate', 0)
        cache_hits = int(llm_calls * (cache_hit_rate / 100))

        # Rough cost estimates (GPT-4o-mini is ~$0.15/1M tokens input, ~$0.60/1M tokens output)
        # Assuming average of 1000 tokens per request
        avg_tokens_per_call = 1000
        input_cost_per_1m = 0.15
        output_cost_per_1m = 0.60
        avg_cost_per_call = ((avg_tokens_per_call * input_cost_per_1m / 1_000_000) +
                             (avg_tokens_per_call * output_cost_per_1m / 1_000_000))

        estimated_savings = cache_hits * avg_cost_per_call
        potential_cost = llm_calls * avg_cost_per_call
        actual_cost = potential_cost - estimated_savings

        print(f"\n💰 Estimated Cost Savings (assuming {avg_tokens_per_call} tokens/call):")
        print(f"   Potential cost (no cache): ${potential_cost:.2f}")
        print(f"   Actual cost (with cache): ${actual_cost:.2f}")
        print(f"   Savings: ${estimated_savings:.2f} ({cache_hit_rate}%)")

        print_separator()

        if cache_hit_rate > 0:
            print(f"\n✅ Caching is ACTIVE and saving costs!")
            print(f"   You're avoiding {cache_hits} redundant API calls.")
        else:
            print(f"\n⚠️  No cache hits yet - caching is enabled but needs more usage data.")

        print_separator()

    except Exception as e:
        print(f"Error retrieving cache statistics: {e}", file=sys.stderr)
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())

        # ChromaDB cache stats
        try:
            chromadb_stats = get_chromadb_cache_stats()
            print(f"\n🗄️  ChromaDB Cache Status:")
            print(f"   Total cached queries: {chromadb_stats.get('total_entries', 0)}")
            print(f"   Cache hits: {chromadb_stats.get('hits', 0)}")
            print(f"   Cache misses: {chromadb_stats.get('misses', 0)}")
            print(f"   Hit rate: {chromadb_stats.get('hit_rate', 0)}%")
        except:
            print(f"\n🗄️  ChromaDB Cache: Not available")

