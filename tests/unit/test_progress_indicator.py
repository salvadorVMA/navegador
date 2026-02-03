#!/usr/bin/env python3
"""
Test script to verify the progress indicator implementation works.
"""
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_progress_indicator():
    """Test the progress indicator UI components."""
    try:
        # Test that we can import the dashboard
        print("Testing progress indicator implementation...")
        
        # Test bilingual messages
        from dashboard import get_message
        
        # Test English progress messages
        print("\n=== English Progress Messages ===")
        for status in ['ready', 'thinking', 'classifying', 'searching', 'filtering', 'analyzing', 'generating', 'finalizing', 'complete']:
            message = get_message(f'progress_{status}', 'en')
            print(f"  {status}: {message}")
        
        # Test Spanish progress messages
        print("\n=== Spanish Progress Messages ===")
        for status in ['ready', 'thinking', 'classifying', 'searching', 'filtering', 'analyzing', 'generating', 'finalizing', 'complete']:
            message = get_message(f'progress_{status}', 'es')
            print(f"  {status}: {message}")
        
        # Test helper functions
        from dashboard import show_progress, hide_progress
        
        print("\n=== Helper Functions ===")
        
        # Test show_progress
        style, text = show_progress("progress_searching", "en")
        print(f"Show progress (EN): style={style}, text='{text}'")
        
        style, text = show_progress("progress_analyzing", "es")
        print(f"Show progress (ES): style={style}, text='{text}'")
        
        # Test hide_progress
        style, text = hide_progress()
        print(f"Hide progress: style={style}, text='{text}'")
        
        print("\n✅ Progress indicator implementation test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing progress indicator: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_progress_indicator()
    print(f"\n{'✅' if success else '❌'} Test {'passed' if success else 'failed'}.")
    sys.exit(0 if success else 1)
