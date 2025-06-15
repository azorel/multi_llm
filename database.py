#!/usr/bin/env python3
"""
Database module for the Life OS Local Application
"""

import sqlite3
import time
import threading
from typing import Dict, List, Any, Optional
from datetime import datetime
from contextlib import contextmanager

class NotionLikeDatabase:
    """SQLite database that mimics your Notion structure."""
    
    def __init__(self, db_path="lifeos_local.db"):
        self.db_path = db_path
        self.connection_pool = []
        self.pool_lock = threading.Lock()
        self.max_pool_size = 10
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Get optimized database connection with connection pooling."""
        conn = None
        try:
            with self.pool_lock:
                if self.connection_pool:
                    conn = self.connection_pool.pop()
                else:
                    conn = self._create_optimized_connection()
            
            yield conn
            
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
            raise
            
        finally:
            if conn:
                with self.pool_lock:
                    if len(self.connection_pool) < self.max_pool_size:
                        self.connection_pool.append(conn)
                    else:
                        conn.close()

    def _create_optimized_connection(self):
        """Create optimized SQLite connection."""
        conn = sqlite3.connect(self.db_path, timeout=30.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        
        # Optimize SQLite settings for performance
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=10000")
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute("PRAGMA mmap_size=268435456")  # 256MB
        
        return conn

    def execute_with_retry(self, query: str, params: tuple = None, max_retries: int = 3):
        """Execute query with retry logic for handling database locks."""
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    if params:
                        cursor.execute(query, params)
                    else:
                        cursor.execute(query)
                    
                    if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
                        conn.commit()
                        return cursor.rowcount
                    else:
                        return cursor.fetchall()
                        
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e).lower() and retry_count < max_retries - 1:
                    retry_count += 1
                    time.sleep(0.1 * retry_count)  # Exponential backoff
                    continue
                else:
                    raise
            except Exception as e:
                raise

    def init_database(self):
        """Initialize all database tables matching your Notion structure."""
        with self.get_connection() as conn:
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
        
        # Social Media Posts table for vanlife & RC content automation
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS social_media_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                content_type TEXT NOT NULL CHECK (content_type IN ('vanlife', 'rc_truck', 'mixed')),
                caption TEXT,
                hashtags TEXT,
                platforms TEXT DEFAULT 'YouTube,Instagram',
                views INTEGER DEFAULT 0,
                likes INTEGER DEFAULT 0,
                revenue REAL DEFAULT 0.0,
                brand_detected TEXT,
                location TEXT,
                terrain_type TEXT,
                rc_model TEXT,
                van_location TEXT,
                upload_status TEXT DEFAULT 'pending',
                youtube_video_id TEXT,
                instagram_post_id TEXT,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                uploaded_date DATETIME,
                performance_score REAL DEFAULT 0.0
            )
        ''')
        
        # Trail Locations database for Southern BC
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trail_locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trail_name TEXT NOT NULL,
                gps_latitude REAL,
                gps_longitude REAL,
                difficulty TEXT CHECK (difficulty IN ('Easy', 'Moderate', 'Difficult', 'Expert')),
                rc_friendly BOOLEAN DEFAULT TRUE,
                access_type TEXT CHECK (access_type IN ('Public', 'Private', 'Permit Required')),
                terrain_description TEXT,
                season_access TEXT DEFAULT 'Year Round',
                elevation_gain INTEGER DEFAULT 0,
                trail_length_km REAL DEFAULT 0.0,
                amenities TEXT,
                photography_spots TEXT,
                last_visited DATE,
                condition_notes TEXT,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # RC Brands database for detection and optimization
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rc_brands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand_name TEXT NOT NULL UNIQUE,
                model_names TEXT,
                detection_keywords TEXT,
                engagement_multiplier REAL DEFAULT 1.0,
                average_views INTEGER DEFAULT 0,
                average_revenue REAL DEFAULT 0.0,
                hashtag_strategy TEXT,
                target_audience TEXT,
                content_style TEXT,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Revenue Tracking for social media monetization
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS revenue_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER,
                income_source TEXT CHECK (income_source IN ('YouTube AdSense', 'Sponsorship', 'Affiliate', 'Merchandise', 'Patreon')),
                amount REAL NOT NULL,
                monetization_type TEXT,
                conversion_rate REAL DEFAULT 0.0,
                date_earned DATE DEFAULT CURRENT_DATE,
                platform TEXT,
                notes TEXT,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES social_media_posts (id)
            )
        ''')
        
        # Content Analytics for performance optimization
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS content_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER,
                platform TEXT,
                engagement_rate REAL DEFAULT 0.0,
                click_through_rate REAL DEFAULT 0.0,
                watch_time_seconds INTEGER DEFAULT 0,
                bounce_rate REAL DEFAULT 0.0,
                demographics TEXT,
                peak_viewing_hours TEXT,
                top_performing_hashtags TEXT,
                analysis_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES social_media_posts (id)
            )
        ''')
        
        # Automation Rules for content processing
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS automation_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_name TEXT NOT NULL,
                content_type TEXT,
                trigger_conditions TEXT,
                action_type TEXT,
                parameters TEXT,
                enabled BOOLEAN DEFAULT TRUE,
                success_rate REAL DEFAULT 0.0,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        
        # Populate with sample data if empty
        self.populate_sample_data()
        
        # Populate social media automation sample data
        self.populate_social_media_data()
    
    def populate_sample_data(self):
        """Populate databases with sample data if empty."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
        
            # Check if data already exists
            cursor.execute("SELECT COUNT(*) FROM agent_command_center")
            if cursor.fetchone()[0] > 0:
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
    
    def populate_social_media_data(self):
        """Populate social media automation tables with sample data."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if social media data already exists
            cursor.execute("SELECT COUNT(*) FROM rc_brands")
            if cursor.fetchone()[0] > 0:
                return
                
            # RC Brands sample data
            rc_brands = [
                ("Axial Racing", "SCX24, SCX10 III, Wraith, Yeti", "axial,scx24,scx10,wraith,yeti", 1.3, 15000, 85.50, "#axialracing #scx24 #scalerc", "RC Enthusiasts, Scale Crawlers", "Technical, Adventure"),
                ("Vanquish Products", "VS4-10, Phoenix, Wraith Axles", "vanquish,vs4,phoenix,wraith axles", 1.2, 12000, 75.20, "#vanquishproducts #vs410 #scalerc", "Serious Crawlers, Builders", "Premium, Technical"),
                ("Traxxas", "TRX-4, TRX-6, Slash, Maxx", "traxxas,trx4,trx6,slash,maxx", 1.4, 25000, 120.00, "#traxxas #trx4 #basherc", "Mainstream RC, Bashers", "Action, Speed"),
                ("RC4WD", "Gelande II, Trail Finder, Accessories", "rc4wd,gelande,trail finder,scale accessories", 1.1, 8000, 45.30, "#rc4wd #scalerc #gelande", "Scale Builders, Detail Enthusiasts", "Authentic, Scale Realism")
            ]
            
            cursor.executemany('''
                INSERT INTO rc_brands (brand_name, model_names, detection_keywords, engagement_multiplier, average_views, average_revenue, hashtag_strategy, target_audience, content_style)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', rc_brands)
            
            # Trail Locations sample data for Southern BC
            trail_locations = [
                ("Squamish Riverside Trail", 49.7016, -123.1558, "Easy", True, "Public", "Gravel path along Squamish River with mountain views", "Year Round", 50, 3.2, "Parking,Washrooms,Picnic Tables", "River views, Mountain backdrop", None, "Great for beginners, wide trails"),
                ("Whistler Valley Trail", 50.1163, -122.9574, "Easy", True, "Public", "Paved multi-use trail through Whistler valley", "April-October", 100, 28.0, "Parking,Bike Rentals,Cafes", "Valley views, Village access", None, "Perfect for scale crawling demos"),
                ("Brohm Lake Trail", 49.8167, -123.0833, "Moderate", True, "Public", "Forest trail to scenic alpine lake", "May-September", 300, 2.5, "Parking,Outhouses", "Lake views, Rock outcrops", None, "Technical sections, great for RC filming"),
                ("Cheakamus Lake Trail", 49.9167, -123.0833, "Moderate", True, "Permit Required", "Rocky trail through old growth forest", "June-October", 400, 4.8, "Parking,Wilderness Camping", "Lake views, Old growth forest", None, "Challenging terrain, permit needed for filming"),
                ("Cypress Mountain Lookout", 49.3667, -123.2000, "Difficult", False, "Public", "Steep technical climb to mountain viewpoint", "July-September", 800, 6.0, "Parking", "City views, Mountain peaks", None, "Expert only, rocky technical sections"),
                ("Joffre Lakes Trail", 50.3667, -122.4833, "Difficult", False, "Public", "Alpine trail to three turquoise lakes", "July-September", 1200, 11.0, "Parking,Outhouses", "Glacier views, Alpine lakes", None, "Not RC friendly, too crowded"),
                ("Garibaldi Lake Trail", 49.9333, -123.0167, "Expert", False, "Public", "Backcountry trail to alpine lake", "August-September", 1500, 18.0, "Parking,Wilderness Camping", "Mountain views, Alpine setting", None, "Backpacking only, not suitable for RC"),
                ("Sea to Sky Trail - Britannia", 49.6167, -123.2000, "Easy", True, "Public", "Converted railway trail with ocean views", "Year Round", 0, 8.5, "Parking,Interpretive Signs", "Ocean views, Mining history", None, "Flat, perfect for RC racing demos")
            ]
            
            cursor.executemany('''
                INSERT INTO trail_locations (trail_name, gps_latitude, gps_longitude, difficulty, rc_friendly, access_type, terrain_description, season_access, elevation_gain, trail_length_km, amenities, photography_spots, last_visited, condition_notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', trail_locations)
            
            # Automation Rules sample data
            automation_rules = [
                ("RC Brand Detection", "rc_truck", "Contains RC vehicle in frame", "detect_brand", '{"confidence_threshold": 0.8, "brands": ["Axial", "Vanquish", "Traxxas", "RC4WD"]}', True, 92.5),
                ("Vanlife Location Tagging", "vanlife", "GPS coordinates available", "tag_location", '{"radius_km": 50, "bc_regions": ["Lower Mainland", "Sea to Sky", "Vancouver Island"]}', True, 88.3),
                ("Terrain Classification", "mixed", "Outdoor content detected", "classify_terrain", '{"types": ["rocky", "muddy", "technical", "scenic", "forest"]}', True, 85.7),
                ("Caption Generation", "vanlife", "Content uploaded", "generate_caption", '{"voice": "relaxed_traveler", "max_length": 200, "include_location": true}', True, 91.2),
                ("Hashtag Optimization", "rc_truck", "Brand detected", "optimize_hashtags", '{"max_hashtags": 30, "mix_ratio": {"brand": 0.3, "activity": 0.4, "location": 0.3}}', True, 89.8),
                ("Revenue Tracking", "mixed", "Content posted", "track_metrics", '{"platforms": ["YouTube", "Instagram"], "update_frequency": "daily"}', True, 95.1)
            ]
            
            cursor.executemany('''
                INSERT INTO automation_rules (rule_name, content_type, trigger_conditions, action_type, parameters, enabled, success_rate)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', automation_rules)
            
            conn.commit()
    
    def get_table_data(self, table_name: str, limit: int = 100) -> List[Dict]:
        """Get data from any table."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT ?", (limit,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error getting table data for {table_name}: {e}")
            return []
    
    def update_record(self, table_name: str, record_id: int, updates: Dict) -> bool:
        """Update a record in any table."""
        try:
            # Build update query
            set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
            values = list(updates.values()) + [record_id]
            
            rows_affected = self.execute_with_retry(
                f"UPDATE {table_name} SET {set_clause} WHERE id = ?", 
                tuple(values)
            )
            return rows_affected > 0
        except Exception as e:
            print(f"Error updating record: {e}")
            return False
    
    def add_record(self, table_name: str, data: Dict) -> int:
        """Add a new record to any table."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build insert query
                columns = ", ".join(data.keys())
                placeholders = ", ".join(["?" for _ in data.keys()])
                values = list(data.values())
                
                cursor.execute(f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})", values)
                record_id = cursor.lastrowid
                conn.commit()
                return record_id
        except Exception as e:
            print(f"Error adding record: {e}")
            return 0
    
    def delete_record(self, table_name: str, record_id: int) -> bool:
        """Delete a record from any table."""
        try:
            rows_affected = self.execute_with_retry(
                f"DELETE FROM {table_name} WHERE id = ?", 
                (record_id,)
            )
            return rows_affected > 0
        except Exception as e:
            print(f"Error deleting record: {e}")
            return False
    
    def get_record(self, table_name: str, record_id: int) -> Dict:
        """Get a single record by ID."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute(f"SELECT * FROM {table_name} WHERE id = ?", (record_id,))
                row = cursor.fetchone()
                
                return dict(row) if row else {}
        except Exception as e:
            print(f"Error getting record: {e}")
            return {}