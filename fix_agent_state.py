#!/usr/bin/env python3
"""
Agent State Fix Implementation

This script updates dashboard.py to use the state_normalizer for consistent agent state
construction between test and real-world usage.

This addresses the mismatch in agent state construction that was identified
as the source of the database query issues.
"""

import os
import sys
import re
import time
import shutil
import json
from datetime import datetime

def print_header(title):
    """Print a nicely formatted header"""
    print(f"\n{'=' * 80}")
    print(f" {title}")
    print(f"{'=' * 80}\n")

def create_backup(filepath):
    """Create a backup of a file with timestamp"""
    if not os.path.exists(filepath):
        print(f"⚠️ File not found: {filepath}")
        return False
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{filepath}.{timestamp}.bak"
    
    try:
        shutil.copy2(filepath, backup_path)
        print(f"✅ Created backup: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ Failed to create backup: {e}")
        return False

def add_state_normalizer_import(content):
    """Add import for state_normalizer if not present"""
    if "from state_normalizer import" not in content:
        # Find where other imports end
        import_section = re.search(r'^import.*?(?=^[a-zA-Z])', content, re.MULTILINE | re.DOTALL)
        if import_section:
            end_of_imports = import_section.end()
            new_content = (
                content[:end_of_imports] + 
                "\nfrom state_normalizer import normalize_state, normalize_config\n" + 
                content[end_of_imports:]
            )
            return new_content, True
    
    return content, False

def update_agent_state_construction(content):
    """Update the agent state construction in handle_auto_next_step"""
    # Pattern to match the agent_state construction in handle_auto_next_step
    pattern = re.compile(
        r'(\s+)agent_state\s*=\s*\{\s*'
        r'"messages":\s*\[\{"role":\s*"user",\s*"content":\s*user_message\}\],.*?'
        r'}\s*(?=\s+#\s*Create\s+proper\s+config|thread_id)',
        re.DOTALL
    )
    
    match = pattern.search(content)
    if match:
        indentation = match.group(1)
        old_state_construction = match.group(0)
        
        # Create new state construction with normalizer
        new_state_construction = f'''{indentation}# Construct agent state with proper normalization
{indentation}agent_state = {{
{indentation}    "messages": [{{"role": "user", "content": user_message}}],
{indentation}    "intent": session_data.get("intent", ""),
{indentation}    "user_query": user_message,
{indentation}    "original_query": user_message,
{indentation}    "dataset": preferred_datasets or session_data.get("datasets", ["ALL"]),
{indentation}    "selected_variables": session_data.get("variables", []),
{indentation}    "analysis_type": session_data.get("analysis_type", "descriptive"),
{indentation}    "user_approved": False,
{indentation}    "analysis_result": {{}},
{indentation}    "language": session_data.get('language', 'en')
{indentation}}}
{indentation}
{indentation}# Normalize the state to ensure consistency
{indentation}agent_state = normalize_state(agent_state)
{indentation}'''
        
        # Replace the old state construction with the new one
        new_content = content.replace(old_state_construction, new_state_construction)
        return new_content, True
    
    return content, False

def update_config_construction(content):
    """Update the agent config construction in handle_auto_next_step"""
    # Pattern to match the agent_config construction
    pattern = re.compile(
        r'(\s+)thread_id\s*=\s*f"chat_{int\(time\.time\(\)\)}"\s*\n'
        r'(\s+)agent_config\s*=\s*create_agent_config\(thread_id\)',
        re.MULTILINE
    )
    
    match = pattern.search(content)
    if match:
        indentation = match.group(1)
        old_config_construction = match.group(0)
        
        # Create new config construction with normalizer
        new_config_construction = f'''{indentation}thread_id = f"chat_{{int(time.time())}}"
{indentation}agent_config = create_agent_config(thread_id)
{indentation}
{indentation}# Normalize the config to ensure consistency
{indentation}agent_config = normalize_config(agent_config)'''
        
        # Replace the old config construction with the new one
        new_content = content.replace(old_config_construction, new_config_construction)
        return new_content, True
    
    return content, False

def update_test_agent_async(content):
    """Update the test_agent_async function to use state normalizer"""
    # Find the test_agent_async function
    test_agent_pattern = re.compile(
        r'def test_agent_async\(\):.*?^\s*return True', 
        re.MULTILINE | re.DOTALL
    )
    
    match = test_agent_pattern.search(content)
    if match:
        test_agent_func = match.group(0)
        
        # Update the test state construction with normalizer
        updated_test_agent = test_agent_func
        
        # Find and update general state construction
        general_state_pattern = re.compile(
            r'(\s+)general_state\s*=\s*\{\s*"messages".*?\}',
            re.DOTALL
        )
        
        general_match = general_state_pattern.search(updated_test_agent)
        if general_match:
            indentation = general_match.group(1)
            old_general_state = general_match.group(0)
            new_general_state = f'''{indentation}general_state = {{
{indentation}    "messages": [{{"role": "user", "content": "Hello"}}]
{indentation}}}
{indentation}# Normalize test state
{indentation}general_state = normalize_state(general_state)'''
            
            updated_test_agent = updated_test_agent.replace(old_general_state, new_general_state)
        
        # Find and update query state construction
        query_state_pattern = re.compile(
            r'(\s+)query_state\s*=\s*\{\s*"messages".*?\}',
            re.DOTALL
        )
        
        query_match = query_state_pattern.search(updated_test_agent)
        if query_match:
            indentation = query_match.group(1)
            old_query_state = query_match.group(0)
            new_query_state = f'''{indentation}query_state = {{
{indentation}    "messages": [{{"role": "user", "content": "What do Mexicans think about health?"}}],
{indentation}    "intent": "query_variable_database"
{indentation}}}
{indentation}# Normalize test query state
{indentation}query_state = normalize_state(query_state)'''
            
            updated_test_agent = updated_test_agent.replace(old_query_state, new_query_state)
        
        # Find and update test_config construction
        config_pattern = re.compile(
            r'(\s+)test_config\s*=\s*\{\s*"configurable".*?\}',
            re.DOTALL
        )
        
        config_match = config_pattern.search(updated_test_agent)
        if config_match:
            indentation = config_match.group(1)
            old_config = config_match.group(0)
            new_config = f'''{indentation}test_config = {{
{indentation}    "configurable": {{
{indentation}        "thread_id": "test_{int(time.time())}",
{indentation}        "checkpoint_id": str(uuid.uuid4()),
{indentation}        "checkpoint_ns": "test_session"
{indentation}    }}
{indentation}}}
{indentation}# Normalize test config
{indentation}test_config = normalize_config(test_config)'''
            
            updated_test_agent = updated_test_agent.replace(old_config, new_config)
        
        # Replace in the full content
        new_content = content.replace(test_agent_func, updated_test_agent)
        return new_content, True
    
    return content, False

def create_agent_config_function(content):
    """Add normalize_config to the create_agent_config function"""
    # Find the create_agent_config function
    pattern = re.compile(
        r'def create_agent_config\(thread_id\):.*?^\s*return config', 
        re.MULTILINE | re.DOTALL
    )
    
    match = pattern.search(content)
    if match:
        old_func = match.group(0)
        
        # Update the function to use normalize_config
        lines = old_func.split('\n')
        last_line_idx = -1
        for i, line in enumerate(lines):
            if "return config" in line:
                last_line_idx = i
                break
        
        if last_line_idx >= 0:
            indent_match = re.match(r'^(\s*)', lines[last_line_idx])
            if indent_match:
                indentation = indent_match.group(1)
                lines.insert(last_line_idx, f"{indentation}# Normalize config to ensure consistency")
                lines.insert(last_line_idx + 1, f"{indentation}config = normalize_config(config)")
                
                new_func = '\n'.join(lines)
                new_content = content.replace(old_func, new_func)
                return new_content, True
            
        # If we couldn't find the indentation, try a simpler approach
        if "return config" in old_func:
            new_func = old_func.replace("return config", "# Normalize config to ensure consistency\n    config = normalize_config(config)\n    return config")
            new_content = content.replace(old_func, new_func)
            return new_content, True
    
    return content, False

def add_uuid_import(content):
    """Add import for uuid if not present"""
    if "import uuid" not in content:
        # Find where other imports end
        import_section = re.search(r'^import.*?(?=^[a-zA-Z])', content, re.MULTILINE | re.DOTALL)
        if import_section:
            # Check if there's already an "import" statement with uuid
            if "import uuid" not in import_section.group(0):
                end_of_imports = import_section.end()
                new_content = (
                    content[:end_of_imports] + 
                    "import uuid\n" + 
                    content[end_of_imports:]
                )
                return new_content, True
    
    return content, False

def main():
    """Main function to update dashboard.py"""
    print_header("Agent State Construction Fix")
    
    dashboard_path = "dashboard.py"
    
    # Check if dashboard.py exists
    if not os.path.exists(dashboard_path):
        print(f"❌ {dashboard_path} not found")
        return
    
    # Create backup
    backup_path = create_backup(dashboard_path)
    if not backup_path:
        print("❌ Failed to create backup, aborting")
        return
    
    try:
        # Read dashboard.py content
        with open(dashboard_path, "r") as f:
            content = f.read()
        
        # Track changes
        changes_made = 0
        
        # Add import for state_normalizer
        content, changed = add_state_normalizer_import(content)
        if changed:
            changes_made += 1
            print("✅ Added import for state_normalizer")
        
        # Add import for uuid if needed
        content, changed = add_uuid_import(content)
        if changed:
            changes_made += 1
            print("✅ Added import for uuid")
        
        # Update agent state construction
        content, changed = update_agent_state_construction(content)
        if changed:
            changes_made += 1
            print("✅ Updated agent state construction with normalizer")
        
        # Update agent config construction
        content, changed = update_config_construction(content)
        if changed:
            changes_made += 1
            print("✅ Updated agent config construction with normalizer")
        
        # Update test_agent_async function
        content, changed = update_test_agent_async(content)
        if changed:
            changes_made += 1
            print("✅ Updated test_agent_async function with normalizer")
        
        # Update create_agent_config function
        content, changed = create_agent_config_function(content)
        if changed:
            changes_made += 1
            print("✅ Updated create_agent_config function with normalizer")
        
        # Save changes if any were made
        if changes_made > 0:
            with open(dashboard_path, "w") as f:
                f.write(content)
            print(f"\n✅ Successfully made {changes_made} changes to {dashboard_path}")
            print(f"   Backup created at: {backup_path}")
            
            print("\n📝 To verify the changes, run:")
            print(f"   python test_state_construction.py")
        else:
            print("\n⚠️ No changes were needed or made to {dashboard_path}")
        
    except Exception as e:
        print(f"❌ Error updating {dashboard_path}: {e}")
        
        # Try to restore from backup
        if backup_path and os.path.exists(backup_path):
            try:
                shutil.copy2(backup_path, dashboard_path)
                print(f"✅ Restored {dashboard_path} from backup")
            except Exception as restore_error:
                print(f"❌ Failed to restore from backup: {restore_error}")

if __name__ == "__main__":
    main()
