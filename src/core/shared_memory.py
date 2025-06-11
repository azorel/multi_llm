"""
Shared memory system for the autonomous multi-LLM agent system.

This module provides thread-safe, persistent memory storage with SQLite backend,
context window management, and memory optimization features.
"""

import asyncio
import sqlite3
import json
import pickle
import gzip
import threading
import time
import hashlib
from typing import Dict, List, Any, Optional, Union, Set, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, OrderedDict
from dataclasses import asdict
from contextlib import asynccontextmanager

from loguru import logger
from pydantic import ValidationError

from ..models.schemas import MemoryEntry, TaskContext, ExecutionResult, AgentConfig


class MemoryType:
    """Types of memory entries."""
    TASK = "task"
    RESULT = "result"
    PATTERN = "pattern"
    LEARNING = "learning"
    CONTEXT = "context"
    GENERAL = "general"


class WorkingMemoryState:
    """State of working memory."""
    
    def __init__(self):
        self.active_contexts: Dict[str, Any] = {}
        self.recent_results: List[Any] = []
        self.patterns: Dict[str, Any] = {}
        self.cache: Dict[str, Any] = {}


class MemoryManager:
    """Manager for different types of memory operations."""
    
    def __init__(self, shared_memory):
        self.shared_memory = shared_memory
        self.working_state = WorkingMemoryState()
    
    async def store_task_memory(self, task_id: str, data: Dict[str, Any]):
        """Store task-related memory."""
        await self.shared_memory.set(f"task_{task_id}", data, entry_type=MemoryType.TASK)
    
    async def store_result_memory(self, result_id: str, data: Dict[str, Any]):
        """Store result-related memory."""
        await self.shared_memory.set(f"result_{result_id}", data, entry_type=MemoryType.RESULT)
    
    async def get_working_state(self) -> WorkingMemoryState:
        """Get current working memory state."""
        return self.working_state


class MemoryDatabase:
    """SQLite-based persistent storage for memory entries."""
    
    def __init__(self, db_path: str = "memory.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_entries (
                    entry_id TEXT PRIMARY KEY,
                    key TEXT NOT NULL,
                    value_data BLOB NOT NULL,
                    entry_type TEXT DEFAULT 'general',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 0,
                    ttl_seconds INTEGER,
                    expires_at TIMESTAMP,
                    tags TEXT,
                    size_bytes INTEGER DEFAULT 0,
                    compression INTEGER DEFAULT 0,
                    metadata TEXT
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_key ON memory_entries(key)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_entry_type ON memory_entries(entry_type)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_expires_at ON memory_entries(expires_at)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_accessed_at ON memory_entries(accessed_at)
            """)
            
            conn.commit()
    
    def store_entry(self, entry: MemoryEntry) -> bool:
        """Store a memory entry in the database."""
        try:
            # Serialize the value
            value_data = pickle.dumps(entry.value)
            
            # Compress if enabled
            if entry.compression:
                value_data = gzip.compress(value_data)
            
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO memory_entries 
                        (entry_id, key, value_data, entry_type, created_at, updated_at, 
                         accessed_at, access_count, ttl_seconds, expires_at, tags, 
                         size_bytes, compression, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        entry.entry_id,
                        entry.key,
                        value_data,
                        entry.entry_type,
                        entry.created_at.isoformat(),
                        entry.updated_at.isoformat(),
                        entry.accessed_at.isoformat(),
                        entry.access_count,
                        entry.ttl_seconds,
                        entry.expires_at.isoformat() if entry.expires_at else None,
                        json.dumps(entry.tags),
                        len(value_data),
                        1 if entry.compression else 0,
                        json.dumps(entry.metadata)
                    ))
                    conn.commit()
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to store memory entry {entry.entry_id}: {e}")
            return False
    
    def get_entry(self, key: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry by key."""
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("""
                        SELECT * FROM memory_entries WHERE key = ? 
                        AND (expires_at IS NULL OR expires_at > ?)
                    """, (key, datetime.utcnow().isoformat()))
                    
                    row = cursor.fetchone()
                    if not row:
                        return None
                    
                    # Update access count and time
                    conn.execute("""
                        UPDATE memory_entries 
                        SET access_count = access_count + 1, accessed_at = ?
                        WHERE entry_id = ?
                    """, (datetime.utcnow().isoformat(), row[0]))
                    conn.commit()
            
            return self._row_to_entry(row)
        
        except Exception as e:
            logger.error(f"Failed to get memory entry for key {key}: {e}")
            return None
    
    def delete_entry(self, key: str) -> bool:
        """Delete a memory entry."""
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("DELETE FROM memory_entries WHERE key = ?", (key,))
                    conn.commit()
                    return cursor.rowcount > 0
        
        except Exception as e:
            logger.error(f"Failed to delete memory entry {key}: {e}")
            return False
    
    def list_entries(self, entry_type: str = None, tags: List[str] = None, 
                    limit: int = 100) -> List[MemoryEntry]:
        """List memory entries with optional filtering."""
        try:
            query = """
                SELECT * FROM memory_entries 
                WHERE (expires_at IS NULL OR expires_at > ?)
            """
            params = [datetime.utcnow().isoformat()]
            
            if entry_type:
                query += " AND entry_type = ?"
                params.append(entry_type)
            
            query += " ORDER BY accessed_at DESC LIMIT ?"
            params.append(limit)
            
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute(query, params)
                    rows = cursor.fetchall()
            
            entries = []
            for row in rows:
                entry = self._row_to_entry(row)
                if entry:
                    # Filter by tags if specified
                    if not tags or any(tag in entry.tags for tag in tags):
                        entries.append(entry)
            
            return entries
        
        except Exception as e:
            logger.error(f"Failed to list memory entries: {e}")
            return []
    
    def cleanup_expired(self) -> int:
        """Remove expired memory entries."""
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("""
                        DELETE FROM memory_entries 
                        WHERE expires_at IS NOT NULL AND expires_at <= ?
                    """, (datetime.utcnow().isoformat(),))
                    conn.commit()
                    return cursor.rowcount
        
        except Exception as e:
            logger.error(f"Failed to cleanup expired entries: {e}")
            return 0
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory database statistics."""
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("""
                        SELECT 
                            COUNT(*) as total_entries,
                            SUM(size_bytes) as total_size,
                            AVG(access_count) as avg_access_count,
                            COUNT(CASE WHEN expires_at IS NOT NULL AND expires_at <= ? THEN 1 END) as expired_entries
                        FROM memory_entries
                    """, (datetime.utcnow().isoformat(),))
                    
                    stats = cursor.fetchone()
                    
                    cursor = conn.execute("""
                        SELECT entry_type, COUNT(*) as count 
                        FROM memory_entries 
                        GROUP BY entry_type
                    """)
                    
                    type_counts = dict(cursor.fetchall())
            
            return {
                'total_entries': stats[0] or 0,
                'total_size_bytes': stats[1] or 0,
                'average_access_count': stats[2] or 0,
                'expired_entries': stats[3] or 0,
                'entries_by_type': type_counts
            }
        
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return {}
    
    def _row_to_entry(self, row: tuple) -> Optional[MemoryEntry]:
        """Convert database row to MemoryEntry object."""
        try:
            # Deserialize value data
            value_data = row[2]
            if row[12]:  # compression flag
                value_data = gzip.decompress(value_data)
            
            value = pickle.loads(value_data)
            
            return MemoryEntry(
                entry_id=row[0],
                key=row[1],
                value=value,
                entry_type=row[3],
                created_at=datetime.fromisoformat(row[4]),
                updated_at=datetime.fromisoformat(row[5]),
                accessed_at=datetime.fromisoformat(row[6]),
                access_count=row[7],
                ttl_seconds=row[8],
                expires_at=datetime.fromisoformat(row[9]) if row[9] else None,
                tags=json.loads(row[10]) if row[10] else [],
                size_bytes=row[11],
                compression=bool(row[12]),
                metadata=json.loads(row[13]) if row[13] else {}
            )
        
        except Exception as e:
            logger.error(f"Failed to deserialize memory entry: {e}")
            return None


class ContextWindowManager:
    """Manages context windows for different agents and tasks."""
    
    def __init__(self, default_max_tokens: int = 8000):
        self.default_max_tokens = default_max_tokens
        self.agent_windows: Dict[str, int] = {}
        self.context_histories: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._lock = asyncio.Lock()
    
    async def set_agent_window_size(self, agent_id: str, max_tokens: int):
        """Set context window size for a specific agent."""
        async with self._lock:
            self.agent_windows[agent_id] = max_tokens
    
    async def add_to_context(self, agent_id: str, context_item: Dict[str, Any]):
        """Add an item to the agent's context history."""
        async with self._lock:
            max_tokens = self.agent_windows.get(agent_id, self.default_max_tokens)
            
            # Add timestamp and token estimate
            context_item['timestamp'] = datetime.utcnow().isoformat()
            context_item['estimated_tokens'] = self._estimate_tokens(context_item)
            
            self.context_histories[agent_id].append(context_item)
            
            # Trim context to fit within window
            await self._trim_context(agent_id, max_tokens)
    
    async def get_context_for_agent(self, agent_id: str, max_tokens: int = None) -> List[Dict[str, Any]]:
        """Get context history for an agent within token limits."""
        async with self._lock:
            if agent_id not in self.context_histories:
                return []
            
            max_tokens = max_tokens or self.agent_windows.get(agent_id, self.default_max_tokens)
            
            # Return context items that fit within the token limit
            context = []
            current_tokens = 0
            
            # Start from most recent items
            for item in reversed(self.context_histories[agent_id]):
                item_tokens = item.get('estimated_tokens', 0)
                if current_tokens + item_tokens <= max_tokens:
                    context.insert(0, item)
                    current_tokens += item_tokens
                else:
                    break
            
            return context
    
    async def clear_context(self, agent_id: str):
        """Clear context history for an agent."""
        async with self._lock:
            if agent_id in self.context_histories:
                self.context_histories[agent_id].clear()
    
    async def get_context_stats(self, agent_id: str) -> Dict[str, Any]:
        """Get context statistics for an agent."""
        async with self._lock:
            if agent_id not in self.context_histories:
                return {'total_items': 0, 'estimated_tokens': 0}
            
            history = self.context_histories[agent_id]
            total_tokens = sum(item.get('estimated_tokens', 0) for item in history)
            
            return {
                'total_items': len(history),
                'estimated_tokens': total_tokens,
                'max_tokens': self.agent_windows.get(agent_id, self.default_max_tokens),
                'utilization': total_tokens / self.agent_windows.get(agent_id, self.default_max_tokens)
            }
    
    async def _trim_context(self, agent_id: str, max_tokens: int):
        """Trim context history to fit within token limits."""
        history = self.context_histories[agent_id]
        
        # Calculate total tokens
        total_tokens = sum(item.get('estimated_tokens', 0) for item in history)
        
        # Remove oldest items until we're under the limit
        while total_tokens > max_tokens and history:
            removed_item = history.pop(0)
            total_tokens -= removed_item.get('estimated_tokens', 0)
    
    def _estimate_tokens(self, context_item: Dict[str, Any]) -> int:
        """Estimate token count for a context item."""
        text_content = str(context_item)
        # Simple approximation: ~4 characters per token
        return max(1, len(text_content) // 4)


class MemoryOptimizer:
    """Optimizes memory usage through compression, cleanup, and intelligent caching."""
    
    def __init__(self, max_memory_mb: int = 500):
        self.max_memory_mb = max_memory_mb
        self.compression_threshold = 1024  # Compress entries larger than 1KB
        self.cleanup_interval = 3600  # Cleanup every hour
        self.last_cleanup = time.time()
    
    async def optimize_entry(self, entry: MemoryEntry) -> MemoryEntry:
        """Optimize a memory entry for storage."""
        # Enable compression for large entries
        if entry.size_bytes > self.compression_threshold:
            entry.compression = True
        
        # Set reasonable TTL if not specified
        if entry.ttl_seconds is None:
            entry.ttl_seconds = self._get_default_ttl(entry.entry_type)
            if entry.ttl_seconds:
                entry.expires_at = entry.created_at + timedelta(seconds=entry.ttl_seconds)
        
        return entry
    
    async def should_cache_entry(self, entry: MemoryEntry) -> bool:
        """Determine if an entry should be cached based on access patterns."""
        # Cache frequently accessed items
        if entry.access_count > 5:
            return True
        
        # Cache recent items
        if (datetime.utcnow() - entry.accessed_at).total_seconds() < 300:  # 5 minutes
            return True
        
        # Cache important entry types
        if entry.entry_type in ['task_result', 'agent_learning', 'system_state']:
            return True
        
        return False
    
    async def cleanup_recommendation(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Provide memory cleanup recommendations."""
        recommendations = []
        
        total_size_mb = stats.get('total_size_bytes', 0) / (1024 * 1024)
        
        if total_size_mb > self.max_memory_mb * 0.8:
            recommendations.append("Memory usage high - consider cleanup")
        
        if stats.get('expired_entries', 0) > 100:
            recommendations.append("Many expired entries - run cleanup")
        
        avg_access = stats.get('average_access_count', 0)
        if avg_access < 1:
            recommendations.append("Many unused entries - consider purging")
        
        return {
            'current_size_mb': total_size_mb,
            'max_size_mb': self.max_memory_mb,
            'utilization': total_size_mb / self.max_memory_mb,
            'recommendations': recommendations,
            'should_cleanup': len(recommendations) > 0
        }
    
    def _get_default_ttl(self, entry_type: str) -> Optional[int]:
        """Get default TTL for different entry types."""
        default_ttls = {
            'task_result': 7200,      # 2 hours
            'agent_state': 3600,      # 1 hour
            'cache': 1800,            # 30 minutes
            'temporary': 300,         # 5 minutes
            'learning': None,         # No expiration
            'system_state': 600,      # 10 minutes
        }
        
        return default_ttls.get(entry_type)


class SharedMemory:
    """
    Thread-safe shared memory system with SQLite persistence and optimization.
    
    Provides memory storage, context management, and optimization for the
    autonomous multi-LLM agent system.
    """
    
    def __init__(self, db_path: str = "memory.db", max_memory_mb: int = 500):
        self.db = MemoryDatabase(db_path)
        self.context_manager = ContextWindowManager()
        self.optimizer = MemoryOptimizer(max_memory_mb)
        
        # In-memory cache for frequently accessed items
        self._cache: OrderedDict[str, MemoryEntry] = OrderedDict()
        self._cache_max_size = 1000
        self._cache_lock = asyncio.Lock()
        
        # Background cleanup task
        self._cleanup_task = None
        self._shutdown_event = asyncio.Event()
        
        logger.info("SharedMemory initialized")
    
    async def initialize(self):
        """Initialize the shared memory system."""
        # Start background cleanup task
        self._cleanup_task = asyncio.create_task(self._background_cleanup())
        logger.info("SharedMemory background tasks started")
    
    async def store(self, key: str, value: Dict[str, Any], entry_type: str = "general",
                   ttl_seconds: Optional[int] = None, tags: List[str] = None,
                   metadata: Dict[str, Any] = None) -> bool:
        """Store a value in shared memory."""
        try:
            # Create memory entry
            entry = MemoryEntry(
                key=key,
                value=value,
                entry_type=entry_type,
                ttl_seconds=ttl_seconds,
                tags=tags or [],
                metadata=metadata or {}
            )
            
            # Calculate size
            entry.size_bytes = len(str(value))
            
            # Optimize entry
            entry = await self.optimizer.optimize_entry(entry)
            
            # Store in database
            success = self.db.store_entry(entry)
            
            if success:
                # Update cache
                await self._update_cache(key, entry)
                logger.debug(f"Stored memory entry: {key}")
            
            return success
        
        except Exception as e:
            logger.error(f"Failed to store memory entry {key}: {e}")
            return False
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve a value from shared memory."""
        try:
            # Check cache first
            async with self._cache_lock:
                if key in self._cache:
                    entry = self._cache[key]
                    # Move to end (most recently used)
                    self._cache.move_to_end(key)
                    logger.debug(f"Retrieved from cache: {key}")
                    return entry.value
            
            # Get from database
            entry = self.db.get_entry(key)
            if entry:
                # Update cache
                await self._update_cache(key, entry)
                logger.debug(f"Retrieved from database: {key}")
                return entry.value
            
            return None
        
        except Exception as e:
            logger.error(f"Failed to get memory entry {key}: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete a value from shared memory."""
        try:
            # Remove from cache
            async with self._cache_lock:
                self._cache.pop(key, None)
            
            # Remove from database
            success = self.db.delete_entry(key)
            
            if success:
                logger.debug(f"Deleted memory entry: {key}")
            
            return success
        
        except Exception as e:
            logger.error(f"Failed to delete memory entry {key}: {e}")
            return False
    
    async def list_keys(self, entry_type: str = None, tags: List[str] = None) -> List[str]:
        """List all keys in memory with optional filtering."""
        try:
            entries = self.db.list_entries(entry_type=entry_type, tags=tags)
            return [entry.key for entry in entries]
        
        except Exception as e:
            logger.error(f"Failed to list memory keys: {e}")
            return []
    
    async def search(self, query: str, entry_type: str = None) -> List[str]:
        """Search for keys containing the query string."""
        try:
            all_keys = await self.list_keys(entry_type=entry_type)
            matching_keys = [key for key in all_keys if query.lower() in key.lower()]
            return matching_keys
        
        except Exception as e:
            logger.error(f"Failed to search memory: {e}")
            return []
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics."""
        try:
            db_stats = self.db.get_memory_stats()
            
            async with self._cache_lock:
                cache_stats = {
                    'cache_size': len(self._cache),
                    'cache_max_size': self._cache_max_size,
                    'cache_utilization': len(self._cache) / self._cache_max_size
                }
            
            optimization_stats = await self.optimizer.cleanup_recommendation(db_stats)
            
            return {
                'database': db_stats,
                'cache': cache_stats,
                'optimization': optimization_stats
            }
        
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return {}
    
    async def cleanup_expired(self) -> int:
        """Clean up expired memory entries."""
        try:
            removed_count = self.db.cleanup_expired()
            
            # Also clean cache
            async with self._cache_lock:
                expired_keys = []
                for key, entry in self._cache.items():
                    if entry.expires_at and entry.expires_at <= datetime.utcnow():
                        expired_keys.append(key)
                
                for key in expired_keys:
                    del self._cache[key]
            
            if removed_count > 0:
                logger.info(f"Cleaned up {removed_count} expired memory entries")
            
            return removed_count
        
        except Exception as e:
            logger.error(f"Failed to cleanup expired entries: {e}")
            return 0
    
    # Context window management methods
    
    async def add_to_context(self, agent_id: str, context_item: Dict[str, Any]):
        """Add an item to an agent's context history."""
        return await self.context_manager.add_to_context(agent_id, context_item)
    
    async def get_context(self, agent_id: str, max_tokens: int = None) -> List[Dict[str, Any]]:
        """Get context history for an agent."""
        return await self.context_manager.get_context_for_agent(agent_id, max_tokens)
    
    async def clear_agent_context(self, agent_id: str):
        """Clear context history for an agent."""
        return await self.context_manager.clear_context(agent_id)
    
    async def get_context_stats(self, agent_id: str) -> Dict[str, Any]:
        """Get context statistics for an agent."""
        return await self.context_manager.get_context_stats(agent_id)
    
    # Utility methods
    
    async def _update_cache(self, key: str, entry: MemoryEntry):
        """Update the in-memory cache."""
        async with self._cache_lock:
            # Check if entry should be cached
            if await self.optimizer.should_cache_entry(entry):
                self._cache[key] = entry
                
                # Trim cache if needed
                while len(self._cache) > self._cache_max_size:
                    self._cache.popitem(last=False)  # Remove oldest item
    
    async def _background_cleanup(self):
        """Background task for periodic cleanup."""
        while not self._shutdown_event.is_set():
            try:
                # Wait for cleanup interval or shutdown
                await asyncio.wait_for(
                    self._shutdown_event.wait(), 
                    timeout=self.optimizer.cleanup_interval
                )
                break  # Shutdown requested
            
            except asyncio.TimeoutError:
                # Time for cleanup
                await self.cleanup_expired()
    
    async def shutdown(self):
        """Shutdown the shared memory system."""
        logger.info("Shutting down SharedMemory")
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Wait for cleanup task to finish
        if self._cleanup_task:
            try:
                await asyncio.wait_for(self._cleanup_task, timeout=5)
            except asyncio.TimeoutError:
                self._cleanup_task.cancel()
        
        logger.info("SharedMemory shutdown complete")
    
    @asynccontextmanager
    async def transaction(self):
        """Context manager for atomic operations (simplified implementation)."""
        # This is a simplified transaction - for full ACID properties,
        # you would need more sophisticated transaction handling
        try:
            yield self
        except Exception as e:
            logger.error(f"Transaction failed: {e}")
            raise