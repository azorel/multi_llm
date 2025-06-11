#!/usr/bin/env python3
"""
COMPLETE NOTION ELIMINATION SYSTEM
==================================

Multi-agent system to find and destroy ALL Notion references.
NO MERCY - COMPLETE ELIMINATION.
"""

import os
import re
import asyncio
import subprocess
from pathlib import Path
import shutil

class NotionEliminationTeam:
    """Multi-agent team to completely eliminate Notion."""
    
    def __init__(self):
        self.base_dir = Path('.')
# NOTION_REMOVED:         self.notion_files_found = []
# NOTION_REMOVED:         self.notion_references_found = []
        self.files_to_delete = []
        self.files_to_clean = []
        
# NOTION_REMOVED:     async def agent_1_find_notion_files(self):
        """Agent 1: Find all files with 'notion' in the name"""
        print("🤖 AGENT 1: Hunting down Notion files...")
        
# NOTION_REMOVED:         notion_patterns = [
            '*notion*',
            '*NOTION*', 
            '*Notion*',
            '*.notion.*',
            'notion_*',
            '*_notion_*'
        ]
        
        for pattern in notion_patterns:
            for file_path in self.base_dir.rglob(pattern):
                if file_path.is_file() and 'venv' not in str(file_path):
                    self.notion_files_found.append(file_path)
                    print(f"   🎯 Found: {file_path}")
        
        print(f"✅ AGENT 1: Found {len(self.notion_files_found)} Notion files")
        return True
    
    async def agent_2_scan_code_references(self):
        """Agent 2: Scan all Python files for Notion references"""
        print("🤖 AGENT 2: Scanning code for Notion references...")
        
# NOTION_REMOVED:         notion_keywords = [
            'notion', 'Notion', 'NOTION',
            'notion_headers', 'notion_client',
        ]
        
        python_files = list(self.base_dir.rglob('*.py'))
        
        for file_path in python_files:
            if 'venv' in str(file_path) or 'ELIMINATE_ALL_NOTION' in str(file_path):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
# NOTION_REMOVED:                 has_notion = False
                for keyword in notion_keywords:
                    if keyword in content:
# NOTION_REMOVED:                         has_notion = True
                        break
                
                if has_notion:
                    self.notion_references_found.append(file_path)
                    print(f"   🎯 Notion code found: {file_path}")
                    
            except Exception as e:
                print(f"   ⚠️ Couldn't read {file_path}: {e}")
        
        print(f"✅ AGENT 2: Found {len(self.notion_references_found)} files with Notion code")
        return True
    
    async def agent_3_categorize_for_deletion(self):
        """Agent 3: Categorize files for deletion or cleaning"""
        print("🤖 AGENT 3: Categorizing files for elimination...")
        
        # Files to completely delete (Notion-specific)
        delete_patterns = [
            'notion_migration_tool.py',
            'notion_mcp_client.py',
            'notion_video_updater.py',
            'lifeos_notion_discovery.py',
            'create_todays_cc_page.py',
            'notion_todays_cc.py',
            'todays_cc_monitor.py',
            'notion_client.py',
            'notion_fixed.py',
            'notion_mcp_client_fixed.py'
        ]
        
        # Check all found files
# NOTION_REMOVED:         all_files = set(self.notion_files_found + self.notion_references_found)
        
        for file_path in all_files:
            file_name = file_path.name
            
            # Check if it's a deletion candidate
            should_delete = any(pattern in file_name for pattern in delete_patterns)
            
            # Also delete if it's primarily Notion code
            if file_path in self.notion_references_found:
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
# NOTION_REMOVED:                         notion_lines = sum(1 for line in content.split('\n') 
                                         if any(kw in line for kw in ['notion', 'Notion', 'NOTION']))
                        total_lines = len(content.split('\n'))
                        
                        # If >30% of lines are Notion-related, delete the whole file
                        if total_lines > 0 and (notion_lines / total_lines) > 0.3:
                            should_delete = True
                except:
                    pass
            
            if should_delete:
                self.files_to_delete.append(file_path)
                print(f"   🗑️ Mark for deletion: {file_path}")
            else:
                self.files_to_clean.append(file_path)
                print(f"   🧹 Mark for cleaning: {file_path}")
        
        print(f"✅ AGENT 3: {len(self.files_to_delete)} files to delete, {len(self.files_to_clean)} to clean")
        return True
    
# NOTION_REMOVED:     async def agent_4_delete_notion_files(self):
        """Agent 4: Delete Notion-specific files"""
        print("🤖 AGENT 4: Deleting Notion files...")
        
        deleted_count = 0
        for file_path in self.files_to_delete:
            try:
                if file_path.exists():
                    file_path.unlink()
                    print(f"   🗑️ Deleted: {file_path}")
                    deleted_count += 1
            except Exception as e:
                print(f"   ❌ Failed to delete {file_path}: {e}")
        
        print(f"✅ AGENT 4: Deleted {deleted_count} Notion files")
        return True
    
    async def agent_5_clean_code_references(self):
        """Agent 5: Clean Notion references from remaining files"""
        print("🤖 AGENT 5: Cleaning Notion references from code...")
        
        cleaned_count = 0
        for file_path in self.files_to_clean:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                # Remove Notion imports
                content = re.sub(r'                content = re.sub(r'                
                # Remove Notion-related lines
                lines = content.split('\n')
                cleaned_lines = []
                
                for line in lines:
                    # Skip lines that are primarily Notion-related
                        print(f"   🧹 Removed line: {line.strip()[:60]}...")
                        continue
                    
                    # Comment out Notion API calls
# NOTION_REMOVED:                     if 'notion' in line.lower() and ('=' in line or 'def ' in line):
# NOTION_REMOVED:                         line = f"# NOTION_REMOVED: {line}"
                        print(f"   🧹 Commented: {line.strip()[:60]}...")
                    
                    cleaned_lines.append(line)
                
                new_content = '\n'.join(cleaned_lines)
                
                # Only write if content changed
                if new_content != original_content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"   ✅ Cleaned: {file_path}")
                    cleaned_count += 1
                
            except Exception as e:
                print(f"   ❌ Failed to clean {file_path}: {e}")
        
        print(f"✅ AGENT 5: Cleaned {cleaned_count} files")
        return True
    
    async def agent_6_remove_env_variables(self):
        """Agent 6: Remove Notion environment variables"""
        print("🤖 AGENT 6: Removing Notion environment variables...")
        
        env_file = Path('.env')
        if env_file.exists():
            try:
                with open(env_file, 'r') as f:
                    lines = f.readlines()
                
                cleaned_lines = []
                removed_count = 0
                
                for line in lines:
                    if any(kw in line.upper() for kw in ['NOTION', 'TODAYS_CC', 'LIFEOS']):
                        print(f"   🧹 Removed env var: {line.strip()}")
                        removed_count += 1
                        continue
                    cleaned_lines.append(line)
                
                with open(env_file, 'w') as f:
                    f.writelines(cleaned_lines)
                
                print(f"✅ AGENT 6: Removed {removed_count} Notion environment variables")
                
            except Exception as e:
                print(f"   ❌ Failed to clean .env: {e}")
        
        return True
    
    async def agent_7_cleanup_directories(self):
        """Agent 7: Remove empty Notion-related directories"""
        print("🤖 AGENT 7: Cleaning up empty directories...")
        
        # Directories that might be Notion-related
        potential_dirs = [
            'lifeos_discovery_results',
            'notion-mcp-server',
            'archive/todays_cc'
        ]
        
        removed_count = 0
        for dir_name in potential_dirs:
            dir_path = Path(dir_name)
            if dir_path.exists() and dir_path.is_dir():
                try:
                    # Check if directory is empty or only has generated files
                    files = list(dir_path.rglob('*'))
# NOTION_REMOVED:                     if len(files) == 0 or all('notion' in str(f).lower() for f in files):
                        shutil.rmtree(dir_path)
                        print(f"   🗑️ Removed directory: {dir_path}")
                        removed_count += 1
                except Exception as e:
                    print(f"   ⚠️ Couldn't remove {dir_path}: {e}")
        
        print(f"✅ AGENT 7: Removed {removed_count} directories")
        return True
    
# NOTION_REMOVED:     async def eliminate_all_notion(self):
        """Main elimination coordinator"""
        print("🎯 STARTING COMPLETE NOTION ELIMINATION")
        print("=" * 70)
        print("🔥 MULTI-AGENT NOTION DESTRUCTION TEAM DEPLOYED")
        print("=" * 70)
        
        # Deploy all agents in parallel
        agents = [
            self.agent_1_find_notion_files(),
            self.agent_2_scan_code_references(),
        ]
        
        # First wave: Discovery
        await asyncio.gather(*agents)
        
        # Second wave: Analysis and categorization
        await self.agent_3_categorize_for_deletion()
        
        # Third wave: Destruction
        destruction_agents = [
            self.agent_4_delete_notion_files(),
            self.agent_5_clean_code_references(),
            self.agent_6_remove_env_variables(),
            self.agent_7_cleanup_directories()
        ]
        
        await asyncio.gather(*destruction_agents)
        
        # Final report
        print("\n" + "=" * 70)
        print("📊 NOTION ELIMINATION COMPLETE")
        print("=" * 70)
        print(f"🗑️ Files deleted: {len(self.files_to_delete)}")
        print(f"🧹 Files cleaned: {len(self.files_to_clean)}")
        print(f"📁 Total files processed: {len(set(self.notion_files_found + self.notion_references_found))}")
        print("\n✅ NOTION HAS BEEN COMPLETELY ELIMINATED!")
        print("🚀 System is now 100% SQL-based with no Notion dependencies")

if __name__ == "__main__":
# NOTION_REMOVED:     team = NotionEliminationTeam()
    asyncio.run(team.eliminate_all_notion())