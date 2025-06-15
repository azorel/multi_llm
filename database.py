#!/usr/bin/env python3
"""
Database module for the Life OS Local Application
"""

import sqlite3
from typing import Dict, List, Any
from datetime import datetime

class NotionLikeDatabase:
    """SQLite database that mimics your Notion structure."""
    
    def __init__(self, db_path="lifeos_local.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize all database tables matching your Notion structure."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Knowledge Hub Database
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_hub (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                notion_id TEXT UNIQUE,
                title TEXT NOT NULL,
                source TEXT,
                content TEXT,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_edited DATETIME,
                tags TEXT,
                category TEXT,
                status TEXT DEFAULT 'Active',
                github_stars INTEGER,
                github_forks INTEGER,
                github_language TEXT,
                github_owner TEXT
            )
        ''')
        
        # YouTube Channels Database
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS youtube_channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_name TEXT NOT NULL,
                channel_url TEXT,
                process_channel BOOLEAN DEFAULT FALSE,
                last_processed DATETIME,
                videos_imported INTEGER DEFAULT 0,
                status TEXT DEFAULT 'Active'
            )
        ''')
        
        # Agent Command Center
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_command_center (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT NOT NULL,
                agent_type TEXT,
                provider TEXT,
                prompt_template TEXT,
                execute_agent BOOLEAN DEFAULT FALSE,
                status TEXT DEFAULT 'Ready',
                results TEXT,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Prompt Library
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prompt_library (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt_name TEXT NOT NULL,
                category TEXT,
                prompt_text TEXT,
                success_rate REAL,
                model_used TEXT,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Model Testing Dashboard
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS model_testing (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_name TEXT NOT NULL,
                model_name TEXT,
                prompt_used TEXT,
                response_quality INTEGER,
                cost REAL,
                speed_ms INTEGER,
                test_date DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Voice Commands
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS voice_commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                command_phrase TEXT NOT NULL,
                action_type TEXT,
                parameters TEXT,
                enabled BOOLEAN DEFAULT TRUE,
                usage_count INTEGER DEFAULT 0
            )
        ''')
        
        # Workflow Templates
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workflow_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_name TEXT NOT NULL,
                description TEXT,
                steps TEXT,
                triggers TEXT,
                enabled BOOLEAN DEFAULT TRUE
            )
        ''')
        
        # Agent Results
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id INTEGER,
                execution_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                result_data TEXT,
                success BOOLEAN,
                execution_time_ms INTEGER,
                cost REAL
            )
        ''')
        
        # Cost Tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cost_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE DEFAULT CURRENT_DATE,
                provider TEXT,
                model TEXT,
                tokens_used INTEGER,
                cost REAL,
                operation_type TEXT
            )
        ''')
        
        # Today's CC (Command Center)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS todays_cc (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE DEFAULT CURRENT_DATE,
                task_name TEXT NOT NULL,
                task_type TEXT,
                completed BOOLEAN DEFAULT FALSE,
                auto_generated BOOLEAN DEFAULT FALSE,
                priority INTEGER DEFAULT 3,
                created_time DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tasks Database
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'Todo',
                priority TEXT DEFAULT 'Medium',
                due_date DATE,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_date DATETIME,
                assigned_to INTEGER,
                manager_id INTEGER,
                completion_percentage INTEGER DEFAULT 0
            )
        ''')
        
        # Habits Database
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_name TEXT NOT NULL,
                frequency TEXT DEFAULT 'Daily',
                current_streak INTEGER DEFAULT 0,
                longest_streak INTEGER DEFAULT 0,
                last_completed DATE,
                enabled BOOLEAN DEFAULT TRUE
            )
        ''')
        
        # Shopping List / Spending Log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shopping_list (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT NOT NULL,
                category TEXT,
                priority TEXT DEFAULT 'Medium',
                estimated_cost REAL,
                purchased BOOLEAN DEFAULT FALSE,
                auto_added BOOLEAN DEFAULT FALSE,
                date_added DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Books Database
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT,
                status TEXT DEFAULT 'To Read',
                rating INTEGER,
                notes TEXT,
                date_added DATETIME DEFAULT CURRENT_TIMESTAMP,
                date_finished DATETIME
            )
        ''')
        
        # Journals Database
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS journals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                content TEXT,
                mood TEXT DEFAULT 'Neutral',
                date DATE DEFAULT CURRENT_DATE,
                tags TEXT,
                created_time DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Notes Database
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                category TEXT,
                tags TEXT,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_edited DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Maintenance Schedule
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS maintenance_schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT NOT NULL,
                category TEXT,
                last_maintenance DATE,
                next_due DATE,
                frequency_days INTEGER DEFAULT 30,
                notes TEXT,
                completed BOOLEAN DEFAULT FALSE
            )
        ''')
        
        # Workers table for autonomous teams
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                role TEXT,
                status TEXT DEFAULT 'Available'
            )
        ''')
        
        # Project Managers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS project_managers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                department TEXT,
                status TEXT DEFAULT 'Active'
            )
        ''')
        
        # Business opportunities table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS business_opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                opportunity_name TEXT NOT NULL,
                description TEXT,
                potential_value TEXT,
                status TEXT DEFAULT 'Evaluating',
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Business projects table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS business_projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'Planning',
                roi_percentage REAL,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Revenue streams table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS revenue_streams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stream_name TEXT NOT NULL,
                monthly_revenue REAL,
                growth_rate REAL,
                status TEXT DEFAULT 'Active',
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Business agents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS business_agents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT NOT NULL,
                role TEXT,
                expertise TEXT,
                performance_score REAL,
                status TEXT DEFAULT 'Available',
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Code analysis results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS code_analysis_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                repository_name TEXT NOT NULL,
                repository_path TEXT,
                analysis_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                files_analyzed INTEGER DEFAULT 0,
                lines_of_code INTEGER DEFAULT 0,
                functions_count INTEGER DEFAULT 0,
                classes_count INTEGER DEFAULT 0,
                complexity_score REAL DEFAULT 0,
                quality_score REAL DEFAULT 0,
                patterns_detected TEXT,
                architecture_patterns TEXT,
                analysis_data TEXT,
                status TEXT DEFAULT 'completed'
            )
        ''')
        
        # Code patterns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS code_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_id TEXT UNIQUE NOT NULL,
                pattern_name TEXT NOT NULL,
                category TEXT,
                description TEXT,
                examples TEXT,
                frequency INTEGER DEFAULT 1,
                repositories TEXT,
                confidence REAL DEFAULT 0.5,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Learning insights table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                insight_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                insight_type TEXT,
                examples TEXT,
                repositories TEXT,
                confidence REAL DEFAULT 0.5,
                actionable_advice TEXT,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Code snippets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS code_snippets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snippet_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                function_name TEXT,
                args TEXT,
                language TEXT DEFAULT 'python',
                tags TEXT,
                repository_source TEXT,
                file_path TEXT,
                line_start INTEGER,
                line_end INTEGER,
                complexity INTEGER DEFAULT 1,
                is_async BOOLEAN DEFAULT FALSE,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Populate with sample data if empty
        self.populate_sample_data()
    
    def populate_sample_data(self):
        """Populate databases with sample data if empty."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if data already exists
        cursor.execute("SELECT COUNT(*) FROM agent_command_center")
        if cursor.fetchone()[0] > 0:
            conn.close()
            return
        
        # Sample Agent Command Center entries (without OpenAI)
        agents = [
            ("Content Processor", "Processing", "Anthropic", "Process and analyze content for insights", False, "Ready"),
            ("Task Automation", "Automation", "Local", "Automate routine tasks and workflows", False, "Ready"),
            ("Data Analyzer", "Analysis", "Local", "Analyze data and provide insights", False, "Ready"),
            ("Code Assistant", "Development", "Anthropic", "Assist with code development tasks", False, "Ready")
        ]
        
        cursor.executemany('''
            INSERT INTO agent_command_center (agent_name, agent_type, provider, prompt_template, execute_agent, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', agents)
        
        # Sample Prompt Library entries
        prompts = [
            ("System Analysis", "Analysis", "Analyze the current system state and identify optimization opportunities", 85.5, "Claude-3"),
            ("Content Summarization", "Processing", "Summarize this content while preserving key insights", 92.3, "Claude-3"),
            ("Task Generation", "Automation", "Generate intelligent tasks based on current context", 78.2, "Local"),
            ("Performance Review", "Optimization", "Review performance metrics and suggest improvements", 88.7, "Claude-3")
        ]
        
        cursor.executemany('''
            INSERT INTO prompt_library (prompt_name, category, prompt_text, success_rate, model_used)
            VALUES (?, ?, ?, ?, ?)
        ''', prompts)
        
        # Sample Today's CC tasks
        today_tasks = [
            ("Morning Routine", "Routine", False, True, 1),
            ("Check Email", "Communication", False, True, 2),
            ("Review Today's Schedule", "Planning", False, True, 1),
            ("Coffee Count - Track Usage", "Health", False, True, 3),
            ("RC Car Maintenance Check", "Hobby", False, False, 3),
            ("Shopping List Review", "Personal", False, True, 2),
            ("Competition Preparation", "RC Racing", False, False, 2),
            ("Evening Review", "Routine", False, True, 1)
        ]
        
        cursor.executemany('''
            INSERT INTO todays_cc (task_name, task_type, completed, auto_generated, priority)
            VALUES (?, ?, ?, ?, ?)
        ''', today_tasks)
        
        # Sample Knowledge Hub entries
        knowledge_entries = [
            ("Autonomous Agent Architecture", "System", "Complete architecture for autonomous AI agent systems", "AI,Automation,Architecture"),
            ("Disler SFA Patterns", "Development", "Single File Agent patterns from Disler's repositories", "AI,Patterns,SFA"),
            ("Self-Healing Systems", "Technology", "Implementation of self-healing and self-learning systems", "AI,Self-Healing,Automation"),
            ("RC Car Setup Guide", "Hobby", "Complete guide for RC car setup and tuning", "RC,Racing,Setup")
        ]
        
        cursor.executemany('''
            INSERT INTO knowledge_hub (title, category, content, tags)
            VALUES (?, ?, ?, ?)
        ''', knowledge_entries)
        
        # Sample Shopping List
        shopping_items = [
            ("RC Car Tires", "RC Parts", "High", 25.99, False, True),
            ("Coffee Beans", "Food", "Medium", 12.50, False, True),
            ("Programming Books", "Education", "Low", 45.00, False, False),
            ("Car Batteries", "RC Parts", "High", 89.99, False, True)
        ]
        
        cursor.executemany('''
            INSERT INTO shopping_list (item_name, category, priority, estimated_cost, purchased, auto_added)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', shopping_items)
        
        conn.commit()
        conn.close()
    
    def get_table_data(self, table_name: str, limit: int = 100) -> List[Dict]:
        """Get data from any table."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        
        conn.close()
        return [dict(row) for row in rows]
    
    def update_record(self, table_name: str, record_id: int, updates: Dict) -> bool:
        """Update a record in any table."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build update query
            set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
            values = list(updates.values()) + [record_id]
            
            cursor.execute(f"UPDATE {table_name} SET {set_clause} WHERE id = ?", values)
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error updating record: {e}")
            return False
    
    def add_record(self, table_name: str, data: Dict) -> int:
        """Add a new record to any table."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build insert query
            columns = ", ".join(data.keys())
            placeholders = ", ".join(["?" for _ in data.keys()])
            values = list(data.values())
            
            cursor.execute(f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})", values)
            record_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return record_id
        except Exception as e:
            print(f"Error adding record: {e}")
            return 0
    
    def delete_record(self, table_name: str, record_id: int) -> bool:
        """Delete a record from any table."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(f"DELETE FROM {table_name} WHERE id = ?", (record_id,))
            rows_affected = cursor.rowcount
            conn.commit()
            conn.close()
            return rows_affected > 0
        except Exception as e:
            print(f"Error deleting record: {e}")
            return False
    
    def get_record(self, table_name: str, record_id: int) -> Dict:
        """Get a single record by ID."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(f"SELECT * FROM {table_name} WHERE id = ?", (record_id,))
            row = cursor.fetchone()
            
            conn.close()
            return dict(row) if row else {}
        except Exception as e:
            print(f"Error getting record: {e}")
            return {}