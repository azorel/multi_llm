#!/usr/bin/env python3
"""
Database Schema Update for Real YouTube Data
============================================

Adds columns to support real YouTube metadata extracted by yt-dlp:
- Real video metadata (views, likes, comments, language, etc.)
- Extraction method tracking
- Data source verification
"""

import sqlite3
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_database_schema(db_path: str = 'autonomous_learning.db'):
    """Add new columns to support real YouTube data."""
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        logger.info("🔧 Updating database schema for real YouTube data...")
        
        # List of new columns to add
        new_columns = [
            # Metadata tracking
            ('view_count', 'INTEGER DEFAULT 0'),
            ('like_count', 'INTEGER DEFAULT 0'), 
            ('comment_count', 'INTEGER DEFAULT 0'),
            ('age_limit', 'INTEGER DEFAULT 0'),
            ('language', 'TEXT'),
            ('uploader', 'TEXT'),
            ('upload_date', 'TEXT'),
            ('description', 'TEXT'),
            ('thumbnail_url', 'TEXT'),
            
            # Technical metadata
            ('tags', 'TEXT'),  # JSON array
            ('categories', 'TEXT'),  # JSON array
            ('is_live', 'BOOLEAN DEFAULT FALSE'),
            ('was_live', 'BOOLEAN DEFAULT FALSE'),
            
            # Processing metadata
            ('extraction_method', 'TEXT'),
            ('data_source', 'TEXT'),
            ('has_transcript', 'BOOLEAN DEFAULT FALSE'),
            ('transcript_source', 'TEXT'),
            ('processing_errors', 'TEXT'),
            ('retry_count', 'INTEGER DEFAULT 0'),
            ('last_retry_at', 'DATETIME'),
            
            # Quality indicators
            ('metadata_complete', 'BOOLEAN DEFAULT FALSE'),
            ('transcript_quality', 'TEXT'),  # 'manual', 'auto', 'none'
            ('extraction_quality_score', 'INTEGER DEFAULT 0')  # 0-100
        ]
        
        # Check existing columns
        cursor.execute("PRAGMA table_info(knowledge_hub)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        
        # Add missing columns
        columns_added = 0
        for column_name, column_def in new_columns:
            if column_name not in existing_columns:
                try:
                    alter_sql = f"ALTER TABLE knowledge_hub ADD COLUMN {column_name} {column_def}"
                    cursor.execute(alter_sql)
                    logger.info(f"✅ Added column: {column_name}")
                    columns_added += 1
                except sqlite3.Error as e:
                    logger.error(f"❌ Failed to add column {column_name}: {e}")
        
        # Create indexes for better query performance
        indexes = [
            ('idx_video_id', 'video_id'),
            ('idx_channel', 'channel'),
            ('idx_view_count', 'view_count'),
            ('idx_upload_date', 'upload_date'),
            ('idx_data_source', 'data_source'),
            ('idx_processing_status', 'processing_status'),
            ('idx_has_transcript', 'has_transcript')
        ]
        
        indexes_created = 0
        for index_name, column in indexes:
            try:
                cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON knowledge_hub ({column})")
                indexes_created += 1
            except sqlite3.Error as e:
                logger.warning(f"⚠️ Index creation failed for {index_name}: {e}")
        
        # Update existing records to mark them as needing real data extraction
        cursor.execute("""
            UPDATE knowledge_hub 
# DEMO CODE REMOVED: SET data_source = 'legacy_fake',
                metadata_complete = FALSE,
                extraction_quality_score = 0
            WHERE data_source IS NULL AND url LIKE '%youtube.com%'
        """)
        
        legacy_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        logger.info(f"🎉 Database schema update complete!")
        logger.info(f"   📊 Columns added: {columns_added}")
        logger.info(f"   🔍 Indexes created: {indexes_created}")
        logger.info(f"   📼 Legacy records marked: {legacy_count}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Database schema update failed: {e}")
        return False

def verify_schema_update(db_path: str = 'autonomous_learning.db'):
    """Verify the schema update was successful."""
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check for new columns
        cursor.execute("PRAGMA table_info(knowledge_hub)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        
        required_columns = [
            'view_count', 'like_count', 'comment_count', 'extraction_method', 
            'data_source', 'has_transcript', 'metadata_complete'
        ]
        
        missing_columns = [col for col in required_columns if col not in columns]
        
        if missing_columns:
            logger.error(f"❌ Missing columns: {missing_columns}")
            return False
        
        # Check for indexes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='knowledge_hub'")
        indexes = [row[0] for row in cursor.fetchall()]
        
        # Count records needing real data
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN data_source = 'real_extraction' THEN 1 END) as real_data,
# DEMO CODE REMOVED: COUNT(CASE WHEN data_source = 'legacy_fake' THEN 1 END) as needs_extraction
            FROM knowledge_hub 
            WHERE url LIKE '%youtube.com%'
        """)
        
        stats = cursor.fetchone()
        conn.close()
        
        logger.info("✅ Schema verification complete:")
        logger.info(f"   📊 Required columns: All present")
        logger.info(f"   🔍 Indexes: {len(indexes)} created")
        logger.info(f"   📼 Total YouTube videos: {stats[0]}")
        logger.info(f"   ✅ With real data: {stats[1]}")
        logger.info(f"   🔄 Needs extraction: {stats[2]}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Schema verification failed: {e}")
        return False

if __name__ == "__main__":
    # Update the schema
    if update_database_schema():
        # Verify the update
        verify_schema_update()
    else:
        print("❌ Schema update failed!")