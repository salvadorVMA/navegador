#!/usr/bin/env python3
import re
import sys
import ast

def fix_specific_try_block(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # The specific code we're looking for
    try_block_start = '    try:\n        # Get the pending action details'
    if try_block_start in content:
        print("Found the problematic try block")
        
        # Get the position of the get_agent_response function (which follows our try block)
        next_function_pos = content.find('def get_agent_response')
        
        if next_function_pos > 0:
            # Get the content up to that position
            before_next_function = content[:next_function_pos]
            
            # Add our except block before the function
            except_block = """    except Exception as e:
        print(f"❌ Error in handle_auto_next_step: {e}")
        import traceback
        traceback.print_exc()
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, True

"""
            # Put it all together
            new_content = before_next_function + except_block + content[next_function_pos:]
            
            # Write back to the file
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(new_content)
            
            print("Successfully added missing except block")
            return True
        else:
            print("Could not find get_agent_response function")
    else:
        print("Could not find the specific try block")
    
    return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fix_missing_except_block.py <file_path>")
        sys.exit(1)
        
    file_path = sys.argv[1]
    fix_specific_try_block(file_path)
