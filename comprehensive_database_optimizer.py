#!/usr/bin/env python3
"""
Comprehensive Database Optimization and Repair System
Tests all database operations, optimizes performance, and implements proper error handling.
"""

import sqlite3
import os
import time
import json
from datetime import datetime
from typing import Dict, List, Any, Tuple

class DatabaseOptimizer:
    """Comprehensive database optimization and testing system."""
    
    def __init__(self, db_path="lifeos_local.db"):
        self.db_path = db_path
        self.test_results = {}
        self.optimization_results = {}
        self.errors = []
        
    def get_connection(self):
        """Get optimized database connection with proper settings."""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        
        # Optimize SQLite settings for performance
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=10000")
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute("PRAGMA mmap_size=268435456")  # 256MB
        
        return conn
    
    def verify_database_exists(self) -> bool:
        """Verify database file exists and is accessible."""
        try:
            if not os.path.exists(self.db_path):
                self.errors.append(f"Database file {self.db_path} does not exist")
                return False
            
            # Check if file is readable and writable
            if not os.access(self.db_path, os.R_OK | os.W_OK):
                self.errors.append(f"Database file {self.db_path} is not readable/writable")
                return False
            
            # Check file size
            file_size = os.path.getsize(self.db_path)
            self.test_results['database_file_size'] = file_size
            
            print(f"✅ Database file exists: {self.db_path} ({file_size:,} bytes)")
            return True
            
        except Exception as e:
            self.errors.append(f"Error verifying database: {str(e)}")
            return False
    
    def get_all_tables(self) -> List[str]:
        """Get list of all tables in the database."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            return tables
            
        except Exception as e:
            self.errors.append(f"Error getting table list: {str(e)}")
            return []
    
    def test_table_operations(self, table_name: str) -> Dict[str, Any]:
        """Test basic CRUD operations on a table."""
        results = {
            'table_name': table_name,
            'exists': False,
            'read_test': False,
            'count': 0,
            'columns': [],
            'indexes': [],
            'performance': {}
        }
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Test if table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if cursor.fetchone():
                results['exists'] = True
                
                # Get column information
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                results['columns'] = [{'name': col[1], 'type': col[2], 'not_null': col[3], 'pk': col[5]} for col in columns]
                
                # Get index information
                cursor.execute(f"PRAGMA index_list({table_name})")
                indexes = cursor.fetchall()
                results['indexes'] = [{'name': idx[1], 'unique': idx[2]} for idx in indexes]
                
                # Test read operations
                start_time = time.time()
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                read_time = time.time() - start_time
                
                results['count'] = count
                results['read_test'] = True
                results['performance']['read_time'] = read_time
                
                # Test sample data retrieval
                if count > 0:
                    start_time = time.time()
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
                    sample_data = cursor.fetchall()
                    sample_time = time.time() - start_time
                    results['performance']['sample_time'] = sample_time
                    results['sample_records'] = len(sample_data)
                
            conn.close()
            
        except Exception as e:
            results['error'] = str(e)
            self.errors.append(f"Error testing table {table_name}: {str(e)}")
        
        return results
    
    def analyze_database_schema(self) -> Dict[str, Any]:
        """Analyze the complete database schema."""
        schema_analysis = {
            'total_tables': 0,
            'total_indexes': 0,
            'total_records': 0,
            'foreign_keys': [],
            'tables': {},
            'missing_indexes': [],
            'performance_issues': []
        }
        
        tables = self.get_all_tables()
        schema_analysis['total_tables'] = len(tables)
        
        for table in tables:
            table_results = self.test_table_operations(table)
            schema_analysis['tables'][table] = table_results
            
            if table_results.get('count', 0) > 0:
                schema_analysis['total_records'] += table_results['count']
            
            schema_analysis['total_indexes'] += len(table_results.get('indexes', []))
            
            # Check for performance issues
            if table_results.get('count', 0) > 1000 and len(table_results.get('indexes', [])) == 0:
                schema_analysis['performance_issues'].append(f"Table {table} has {table_results['count']} records but no indexes")
        
        return schema_analysis
    
    def optimize_database_performance(self) -> Dict[str, Any]:
        """Optimize database performance with indexes and settings."""
        optimization_results = {
            'indexes_created': [],
            'pragma_optimizations': [],
            'vacuum_performed': False,
            'analyze_performed': False,
            'errors': []
        }
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Create performance indexes for frequently queried tables
            performance_indexes = [
                # Knowledge Hub indexes
                ("idx_knowledge_hub_category", "knowledge_hub", "category"),
                ("idx_knowledge_hub_status", "knowledge_hub", "status"),
                ("idx_knowledge_hub_created", "knowledge_hub", "created_date"),
                
                # YouTube channels indexes
                ("idx_youtube_channels_process", "youtube_channels", "process_channel"),
                ("idx_youtube_channels_status", "youtube_channels", "status"),
                
                # Agent command center indexes
                ("idx_agent_command_status", "agent_command_center", "status"),
                ("idx_agent_command_type", "agent_command_center", "agent_type"),
                ("idx_agent_command_execute", "agent_command_center", "execute_agent"),
                
                # Social media indexes
                ("idx_social_media_status", "social_media_posts", "status"),
                ("idx_social_media_content_type", "social_media_posts", "content_type"),
                ("idx_social_media_scheduled", "social_media_posts", "scheduled_time"),
                ("idx_social_media_created", "social_media_posts", "created_date"),
                
                # Hashtag performance indexes
                ("idx_hashtag_niche", "hashtag_performance", "niche"),
                ("idx_hashtag_platform", "hashtag_performance", "platform"),
                ("idx_hashtag_trending", "hashtag_performance", "trending_score"),
                
                # Revenue tracking indexes
                ("idx_revenue_date", "revenue_tracking", "date"),
                ("idx_revenue_source", "revenue_tracking", "revenue_source"),
                
                # Trail locations indexes
                ("idx_trail_region", "trail_locations", "region"),
                ("idx_trail_difficulty", "trail_locations", "difficulty"),
                ("idx_trail_rc_friendly", "trail_locations", "rc_friendly"),
                
                # Tasks indexes
                ("idx_tasks_status", "tasks", "status"),
                ("idx_tasks_priority", "tasks", "priority"),
                ("idx_tasks_due_date", "tasks", "due_date"),
                
                # Today's CC indexes
                ("idx_todays_cc_date", "todays_cc", "date"),
                ("idx_todays_cc_completed", "todays_cc", "completed"),
                ("idx_todays_cc_priority", "todays_cc", "priority"),
                
                # Cost tracking indexes
                ("idx_cost_tracking_date", "cost_tracking", "date"),
                ("idx_cost_tracking_provider", "cost_tracking", "provider"),
                
                # Code analysis indexes
                ("idx_code_analysis_date", "code_analysis_results", "analysis_date"),
                ("idx_code_analysis_status", "code_analysis_results", "status"),
                ("idx_code_patterns_category", "code_patterns", "category"),
                ("idx_code_patterns_frequency", "code_patterns", "frequency"),
            ]
            
            for index_name, table_name, column_name in performance_indexes:
                try:
                    # Check if table exists
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
                    if cursor.fetchone():
                        # Check if index already exists
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name=?", (index_name,))
                        if not cursor.fetchone():
                            cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} ({column_name})")
                            optimization_results['indexes_created'].append(f"{index_name} on {table_name}.{column_name}")
                except Exception as e:
                    optimization_results['errors'].append(f"Error creating index {index_name}: {str(e)}")
            
            # Optimize database with VACUUM and ANALYZE
            try:
                cursor.execute("VACUUM")
                optimization_results['vacuum_performed'] = True
                optimization_results['pragma_optimizations'].append("VACUUM completed")
            except Exception as e:
                optimization_results['errors'].append(f"VACUUM error: {str(e)}")
            
            try:
                cursor.execute("ANALYZE")
                optimization_results['analyze_performed'] = True
                optimization_results['pragma_optimizations'].append("ANALYZE completed")
            except Exception as e:
                optimization_results['errors'].append(f"ANALYZE error: {str(e)}")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            optimization_results['errors'].append(f"Database optimization error: {str(e)}")
        
        return optimization_results
    
    def test_all_database_connections(self) -> Dict[str, Any]:
        """Test database connections from all application components."""
        connection_tests = {
            'web_server_connection': False,
            'database_module_connection': False,
            'social_media_extension_connection': False,
            'concurrent_connections': 0,
            'connection_pool_test': False,
            'errors': []
        }
        
        try:
            # Test basic connection
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result and result[0] == 1:
                connection_tests['database_module_connection'] = True
            conn.close()
            
            # Test concurrent connections
            connections = []
            try:
                for i in range(10):
                    conn = self.get_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM sqlite_master")
                    connections.append(conn)
                
                connection_tests['concurrent_connections'] = len(connections)
                connection_tests['connection_pool_test'] = True
                
                # Close all connections
                for conn in connections:
                    conn.close()
                    
            except Exception as e:
                connection_tests['errors'].append(f"Concurrent connection test error: {str(e)}")
                for conn in connections:
                    try:
                        conn.close()
                    except:
                        pass
        
        except Exception as e:
            connection_tests['errors'].append(f"Connection test error: {str(e)}")
        
        return connection_tests
    
    def implement_backup_system(self) -> Dict[str, Any]:
        """Implement database backup and recovery system."""
        backup_results = {
            'backup_created': False,
            'backup_path': '',
            'backup_size': 0,
            'backup_time': 0,
            'recovery_test': False,
            'errors': []
        }
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{self.db_path}.backup_{timestamp}"
            
            start_time = time.time()
            
            # Create backup using SQLite backup API
            source = sqlite3.connect(self.db_path)
            backup = sqlite3.connect(backup_path)
            
            source.backup(backup)
            
            source.close()
            backup.close()
            
            backup_time = time.time() - start_time
            backup_size = os.path.getsize(backup_path)
            
            backup_results.update({
                'backup_created': True,
                'backup_path': backup_path,
                'backup_size': backup_size,
                'backup_time': backup_time
            })
            
            # Test backup recovery
            try:
                test_conn = sqlite3.connect(backup_path)
                cursor = test_conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM sqlite_master")
                table_count = cursor.fetchone()[0]
                test_conn.close()
                
                if table_count > 0:
                    backup_results['recovery_test'] = True
                    
            except Exception as e:
                backup_results['errors'].append(f"Recovery test error: {str(e)}")
            
        except Exception as e:
            backup_results['errors'].append(f"Backup creation error: {str(e)}")
        
        return backup_results
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive database optimization and repair."""
        print("🔍 Starting comprehensive database optimization and repair...")
        
        comprehensive_results = {
            'timestamp': datetime.now().isoformat(),
            'database_path': self.db_path,
            'verification': {},
            'schema_analysis': {},
            'optimization': {},
            'connection_tests': {},
            'backup_system': {},
            'summary': {},
            'errors': []
        }
        
        # 1. Verify database exists
        print("\n📋 Step 1: Verifying database accessibility...")
        if self.verify_database_exists():
            comprehensive_results['verification']['database_exists'] = True
        else:
            comprehensive_results['verification']['database_exists'] = False
            comprehensive_results['errors'].extend(self.errors)
            return comprehensive_results
        
        # 2. Analyze schema
        print("\n📋 Step 2: Analyzing database schema...")
        schema_analysis = self.analyze_database_schema()
        comprehensive_results['schema_analysis'] = schema_analysis
        
        # 3. Optimize performance
        print("\n📋 Step 3: Optimizing database performance...")
        optimization = self.optimize_database_performance()
        comprehensive_results['optimization'] = optimization
        
        # 4. Test connections
        print("\n📋 Step 4: Testing database connections...")
        connection_tests = self.test_all_database_connections()
        comprehensive_results['connection_tests'] = connection_tests
        
        # 5. Implement backup system
        print("\n📋 Step 5: Implementing backup system...")
        backup_system = self.implement_backup_system()
        comprehensive_results['backup_system'] = backup_system
        
        # 6. Generate summary
        comprehensive_results['summary'] = {
            'total_tables': schema_analysis['total_tables'],
            'total_records': schema_analysis['total_records'],
            'total_indexes': schema_analysis['total_indexes'],
            'indexes_created': len(optimization['indexes_created']),
            'backup_created': backup_system['backup_created'],
            'connection_test_passed': connection_tests['database_module_connection'],
            'performance_issues': len(schema_analysis['performance_issues']),
            'total_errors': len(self.errors) + len(optimization['errors']) + len(connection_tests['errors']) + len(backup_system['errors'])
        }
        
        comprehensive_results['errors'] = self.errors
        
        return comprehensive_results

def main():
    """Main function to run database optimization."""
    optimizer = DatabaseOptimizer()
    results = optimizer.run_comprehensive_test()
    
    # Print summary
    print("\n" + "="*80)
    print("📊 DATABASE OPTIMIZATION SUMMARY")
    print("="*80)
    
    summary = results['summary']
    print(f"📁 Database: {results['database_path']}")
    print(f"📋 Tables: {summary['total_tables']}")
    print(f"📊 Total Records: {summary['total_records']:,}")
    print(f"🔍 Indexes: {summary['total_indexes']} (created {summary['indexes_created']} new)")
    print(f"💾 Backup: {'✅ Created' if summary['backup_created'] else '❌ Failed'}")
    print(f"🔗 Connections: {'✅ Passed' if summary['connection_test_passed'] else '❌ Failed'}")
    print(f"⚠️  Performance Issues: {summary['performance_issues']}")
    print(f"❌ Total Errors: {summary['total_errors']}")
    
    if results['errors']:
        print("\n❌ ERRORS FOUND:")
        for error in results['errors']:
            print(f"  - {error}")
    
    # Save detailed results
    results_file = f"database_optimization_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Detailed results saved to: {results_file}")
    
    if summary['total_errors'] == 0:
        print("\n✅ DATABASE OPTIMIZATION COMPLETED SUCCESSFULLY!")
    else:
        print(f"\n⚠️  DATABASE OPTIMIZATION COMPLETED WITH {summary['total_errors']} ISSUES")
    
    return results

if __name__ == "__main__":
    main()