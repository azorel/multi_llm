#!/usr/bin/env python3
"""
Database Health Monitor and Error Handler
Provides real-time database health monitoring and improved error handling.
"""

import sqlite3
import time
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from contextlib import contextmanager

class DatabaseHealthMonitor:
    """Real-time database health monitoring and error handling system."""
    
    def __init__(self, db_path="lifeos_local.db"):
        self.db_path = db_path
        self.health_stats = {
            'last_check': None,
            'connection_count': 0,
            'query_count': 0,
            'error_count': 0,
            'avg_query_time': 0.0,
            'slowest_query': '',
            'slowest_query_time': 0.0,
            'failed_queries': [],
            'database_size': 0,
            'table_stats': {},
            'connection_pool_active': False,
            'backup_status': 'unknown'
        }
        self.connection_pool = []
        self.pool_lock = threading.Lock()
        self.max_pool_size = 10
        
    @contextmanager
    def get_monitored_connection(self):
        """Get database connection with monitoring and error handling."""
        conn = None
        start_time = time.time()
        
        try:
            # Get connection from pool or create new one
            with self.pool_lock:
                if self.connection_pool:
                    conn = self.connection_pool.pop()
                else:
                    conn = self._create_optimized_connection()
                
                self.health_stats['connection_count'] += 1
            
            yield conn
            
        except Exception as e:
            self.health_stats['error_count'] += 1
            self.health_stats['failed_queries'].append({
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'connection_time': time.time() - start_time
            })
            
            # Keep only last 50 failed queries
            if len(self.health_stats['failed_queries']) > 50:
                self.health_stats['failed_queries'] = self.health_stats['failed_queries'][-50:]
            
            raise
            
        finally:
            if conn:
                # Return connection to pool
                with self.pool_lock:
                    if len(self.connection_pool) < self.max_pool_size:
                        self.connection_pool.append(conn)
                    else:
                        conn.close()
                        
            # Update query time stats
            query_time = time.time() - start_time
            self.health_stats['query_count'] += 1
            
            # Update average query time
            total_queries = self.health_stats['query_count']
            current_avg = self.health_stats['avg_query_time']
            self.health_stats['avg_query_time'] = ((current_avg * (total_queries - 1)) + query_time) / total_queries
            
            # Track slowest query
            if query_time > self.health_stats['slowest_query_time']:
                self.health_stats['slowest_query_time'] = query_time
    
    def _create_optimized_connection(self):
        """Create optimized SQLite connection."""
        conn = sqlite3.connect(self.db_path, timeout=30.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        
        # Optimize SQLite settings
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=10000")
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute("PRAGMA mmap_size=268435456")  # 256MB
        
        return conn
    
    def execute_monitored_query(self, query: str, params: tuple = None, fetch_all: bool = True) -> Any:
        """Execute query with monitoring and error handling."""
        start_time = time.time()
        
        try:
            with self.get_monitored_connection() as conn:
                cursor = conn.cursor()
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
                    conn.commit()
                    return cursor.rowcount
                elif fetch_all:
                    return cursor.fetchall()
                else:
                    return cursor.fetchone()
                    
        except Exception as e:
            query_time = time.time() - start_time
            self.health_stats['failed_queries'].append({
                'query': query[:100] + '...' if len(query) > 100 else query,
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'query_time': query_time
            })
            raise
    
    def check_database_health(self) -> Dict[str, Any]:
        """Perform comprehensive database health check."""
        health_report = {
            'timestamp': datetime.now().isoformat(),
            'database_accessible': False,
            'table_integrity': {},
            'performance_metrics': {},
            'disk_usage': {},
            'connection_pool_status': {},
            'recent_errors': [],
            'recommendations': []
        }
        
        try:
            # Basic connectivity test
            with self.get_monitored_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                health_report['database_accessible'] = (result[0] == 1)
            
            # Check table integrity
            tables = self._get_table_list()
            for table in tables:
                try:
                    with self.get_monitored_connection() as conn:
                        cursor = conn.cursor()
                        
                        # Check table exists and get record count
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        
                        # Check for corruption
                        cursor.execute(f"PRAGMA integrity_check({table})")
                        integrity = cursor.fetchone()[0]
                        
                        health_report['table_integrity'][table] = {
                            'record_count': count,
                            'integrity_check': integrity,
                            'healthy': integrity.lower() == 'ok'
                        }
                        
                except Exception as e:
                    health_report['table_integrity'][table] = {
                        'error': str(e),
                        'healthy': False
                    }
            
            # Performance metrics
            health_report['performance_metrics'] = {
                'total_queries': self.health_stats['query_count'],
                'avg_query_time': self.health_stats['avg_query_time'],
                'slowest_query_time': self.health_stats['slowest_query_time'],
                'error_rate': self.health_stats['error_count'] / max(self.health_stats['query_count'], 1),
                'connection_count': self.health_stats['connection_count']
            }
            
            # Disk usage
            import os
            db_size = os.path.getsize(self.db_path)
            health_report['disk_usage'] = {
                'database_size_bytes': db_size,
                'database_size_mb': round(db_size / (1024 * 1024), 2)
            }
            
            # Connection pool status
            with self.pool_lock:
                health_report['connection_pool_status'] = {
                    'active_connections': len(self.connection_pool),
                    'max_pool_size': self.max_pool_size,
                    'pool_utilization': len(self.connection_pool) / self.max_pool_size
                }
            
            # Recent errors
            health_report['recent_errors'] = self.health_stats['failed_queries'][-10:]
            
            # Generate recommendations
            recommendations = []
            
            if health_report['performance_metrics']['avg_query_time'] > 0.1:
                recommendations.append("Consider adding more indexes for slow queries")
            
            if health_report['performance_metrics']['error_rate'] > 0.05:
                recommendations.append("High error rate detected - review query patterns")
            
            if health_report['disk_usage']['database_size_mb'] > 100:
                recommendations.append("Database size is large - consider archiving old data")
            
            if len(health_report['recent_errors']) > 5:
                recommendations.append("Multiple recent errors - check application logic")
            
            health_report['recommendations'] = recommendations
            
        except Exception as e:
            health_report['critical_error'] = str(e)
            health_report['database_accessible'] = False
        
        self.health_stats['last_check'] = datetime.now().isoformat()
        return health_report
    
    def _get_table_list(self) -> List[str]:
        """Get list of all tables in database."""
        try:
            with self.get_monitored_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                return [row[0] for row in cursor.fetchall()]
        except:
            return []
    
    def create_enhanced_error_handlers(self) -> Dict[str, Any]:
        """Create enhanced error handling decorators and functions."""
        
        def database_transaction(func):
            """Decorator for database transactions with proper error handling."""
            def wrapper(*args, **kwargs):
                max_retries = 3
                retry_count = 0
                
                while retry_count < max_retries:
                    try:
                        with self.get_monitored_connection() as conn:
                            # Start transaction
                            conn.execute("BEGIN")
                            
                            try:
                                result = func(conn, *args, **kwargs)
                                conn.commit()
                                return result
                                
                            except Exception as e:
                                conn.rollback()
                                raise
                                
                    except sqlite3.OperationalError as e:
                        if "database is locked" in str(e).lower() and retry_count < max_retries - 1:
                            retry_count += 1
                            time.sleep(0.1 * retry_count)  # Exponential backoff
                            continue
                        else:
                            raise
                    except Exception as e:
                        raise
                
            wrapper.__name__ = func.__name__
            return wrapper
        
        return {
            'database_transaction': database_transaction,
            'monitored_connection': self.get_monitored_connection,
            'monitored_query': self.execute_monitored_query
        }
    
    def generate_health_report(self) -> str:
        """Generate human-readable health report."""
        health_data = self.check_database_health()
        
        report = []
        report.append("="*80)
        report.append("📊 DATABASE HEALTH REPORT")
        report.append("="*80)
        report.append(f"🕐 Generated: {health_data['timestamp']}")
        report.append(f"📁 Database: {self.db_path}")
        
        # Accessibility
        if health_data['database_accessible']:
            report.append("✅ Database Status: Accessible")
        else:
            report.append("❌ Database Status: Not Accessible")
            if 'critical_error' in health_data:
                report.append(f"   Error: {health_data['critical_error']}")
        
        # Performance metrics
        perf = health_data['performance_metrics']
        report.append(f"\n📈 PERFORMANCE METRICS")
        report.append(f"   Total Queries: {perf['total_queries']:,}")
        report.append(f"   Average Query Time: {perf['avg_query_time']:.4f}s")
        report.append(f"   Slowest Query: {perf['slowest_query_time']:.4f}s")
        report.append(f"   Error Rate: {perf['error_rate']:.2%}")
        report.append(f"   Connections Created: {perf['connection_count']:,}")
        
        # Table integrity
        report.append(f"\n🗄️ TABLE INTEGRITY")
        healthy_tables = sum(1 for t in health_data['table_integrity'].values() if t.get('healthy', False))
        total_tables = len(health_data['table_integrity'])
        report.append(f"   Healthy Tables: {healthy_tables}/{total_tables}")
        
        for table, stats in health_data['table_integrity'].items():
            if stats.get('healthy', False):
                report.append(f"   ✅ {table}: {stats['record_count']:,} records")
            else:
                report.append(f"   ❌ {table}: {stats.get('error', 'Unknown error')}")
        
        # Disk usage
        disk = health_data['disk_usage']
        report.append(f"\n💾 DISK USAGE")
        report.append(f"   Database Size: {disk['database_size_mb']} MB")
        
        # Connection pool
        pool = health_data['connection_pool_status']
        report.append(f"\n🔗 CONNECTION POOL")
        report.append(f"   Active Connections: {pool['active_connections']}/{pool['max_pool_size']}")
        report.append(f"   Pool Utilization: {pool['pool_utilization']:.1%}")
        
        # Recent errors
        if health_data['recent_errors']:
            report.append(f"\n❌ RECENT ERRORS ({len(health_data['recent_errors'])})")
            for error in health_data['recent_errors'][-5:]:
                timestamp = error['timestamp'][:19]  # Remove microseconds
                report.append(f"   {timestamp}: {error['error']}")
        
        # Recommendations
        if health_data['recommendations']:
            report.append(f"\n💡 RECOMMENDATIONS")
            for rec in health_data['recommendations']:
                report.append(f"   • {rec}")
        
        report.append("\n" + "="*80)
        
        return "\n".join(report)

def main():
    """Test the database health monitor."""
    monitor = DatabaseHealthMonitor()
    
    # Run health check
    print("🔍 Running database health check...")
    report = monitor.generate_health_report()
    print(report)
    
    # Test enhanced error handlers
    print("\n🧪 Testing enhanced error handlers...")
    handlers = monitor.create_enhanced_error_handlers()
    
    # Test monitored query
    try:
        result = monitor.execute_monitored_query("SELECT COUNT(*) FROM sqlite_master")
        print(f"✅ Monitored query test: Found {result[0][0]} tables")
    except Exception as e:
        print(f"❌ Monitored query test failed: {e}")
    
    # Save health report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"database_health_report_{timestamp}.txt"
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"\n📄 Health report saved to: {report_file}")

if __name__ == "__main__":
    main()