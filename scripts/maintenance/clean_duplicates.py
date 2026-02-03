#!/usr/bin/env python3

"""
Clean duplicate function definitions from dashboard.py
"""

import re
import os
import sys
import shutil
import time

def backup_file(file_path):
    """Create a timestamped backup of a file"""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.{timestamp}.bak"
    
    try:
        shutil.copy2(file_path, backup_path)
        print(f"✅ Created backup: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ Failed to create backup: {e}")
        return None

def clean_duplicate_functions(content):
    """Remove duplicate function definitions from the content"""
    # List of functions to check for duplicates
    functions_to_clean = [
        r'def process_agent_response\(agent_response, session_data, chat_data, user_message\):',
        r'def update_session_from_agent_response\(session_data: Dict\[str, Any\], agent_response: Any\) -> Dict\[str, Any\]:',
        r'def extract_agent_content\(agent_response: Any\) -> str:'
    ]
    
    # Keep track of occurrences
    for func_pattern in functions_to_clean:
        # Find all occurrences
        matches = list(re.finditer(func_pattern, content))
        if len(matches) <= 1:
            print(f"No duplicates found for {func_pattern[:30]}...")
            continue
        
        print(f"Found {len(matches)} occurrences of {func_pattern[:30]}...")
        
        # Keep only the first occurrence, remove the rest
        for match in matches[1:]:
            # Find the end of the function (next function or end of file)
            start_pos = match.start()
            
            # Find the next function definition or end of file
            next_func_match = re.search(r'^def\s+\w+\(', content[start_pos+1:], re.MULTILINE)
            if next_func_match:
                end_pos = start_pos + 1 + next_func_match.start()
            else:
                end_pos = len(content)
            
            # Remove the duplicate function
            print(f"Removing duplicate at position {start_pos}")
            content = content[:start_pos] + content[end_pos:]
    
    # Also check for indented duplicates within exception blocks
    # These often have extra indentation
    indented_patterns = [
        r'    def process_agent_response\(agent_response, session_data, chat_data, user_message\):'
    ]
    
    for func_pattern in indented_patterns:
        # Find all occurrences
        matches = list(re.finditer(func_pattern, content))
        if not matches:
            continue
        
        print(f"Found {len(matches)} indented occurrences of {func_pattern[4:34]}...")
        
        # Remove all these indented occurrences (they're inside exception blocks)
        for match in matches:
            # Find the end of the function (next function or end of block)
            start_pos = match.start()
            
            # Find the next function definition or end of block
            next_func_match = re.search(r'^    def\s+\w+\(|^def\s+\w+\(|^class\s+\w+\(', content[start_pos+1:], re.MULTILINE)
            if next_func_match:
                end_pos = start_pos + 1 + next_func_match.start()
            else:
                # Find the next line with less indentation
                next_line_match = re.search(r'\n[^\s]', content[start_pos:])
                if next_line_match:
                    end_pos = start_pos + next_line_match.start() + 1
                else:
                    end_pos = len(content)
            
            # Remove the duplicate function
            print(f"Removing indented duplicate at position {start_pos}")
            content = content[:start_pos] + content[end_pos:]
    
    return content

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python clean_duplicates.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        sys.exit(1)
    
    # Create a backup first
    backup_path = backup_file(file_path)
    if not backup_path:
        print("❌ Failed to create backup. Aborting.")
        sys.exit(1)
    
    # Read the file
    try:
        with open(file_path, 'r') as file:
            content = file.read()
    except Exception as e:
        print(f"❌ Failed to read file: {e}")
        sys.exit(1)
    
    # Clean duplicates
    print(f"Cleaning duplicates in {file_path}...")
    cleaned_content = clean_duplicate_functions(content)
    
    # Write the cleaned content back
    try:
        with open(file_path, 'w') as file:
            file.write(cleaned_content)
        print(f"✅ Successfully cleaned duplicates in {file_path}")
        print(f"✅ Backup saved to {backup_path}")
    except Exception as e:
        print(f"❌ Failed to write cleaned content: {e}")
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    main()
