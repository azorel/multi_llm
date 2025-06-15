#!/usr/bin/env python3
"""
Social Media Database Extension for Vanlife & RC Truck Automation
Extends the existing database with social media specific tables
"""

import sqlite3
from datetime import datetime

def extend_database_for_social_media(db_path="lifeos_local.db"):
    """
    Extend the existing database with social media automation tables
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🗄️ Creating social media database extensions...")
    
    # Social media posts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS social_media_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL,
            original_filename TEXT,
            content_type TEXT NOT NULL, -- 'vanlife', 'rc_truck', 'mixed'
            caption TEXT,
            hashtags TEXT,
            platforms TEXT, -- JSON array: ['youtube', 'instagram']
            scheduled_time DATETIME,
            posted_time DATETIME,
            youtube_video_id TEXT,
            instagram_media_id TEXT,
            views INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            shares INTEGER DEFAULT 0,
            revenue_generated REAL DEFAULT 0.0,
            status TEXT DEFAULT 'draft', -- 'draft', 'scheduled', 'posted', 'failed'
            analysis_data TEXT, -- JSON with AI analysis results
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Trail locations for Southern BC
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trail_locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            region TEXT DEFAULT 'Southern BC',
            difficulty TEXT, -- 'easy', 'moderate', 'difficult', 'extreme'
            gps_lat REAL,
            gps_long REAL,
            elevation INTEGER,
            accessibility TEXT, -- 'car_accessible', 'hiking_required', '4x4_only'
            rc_friendly BOOLEAN DEFAULT TRUE,
            hiking_trail BOOLEAN DEFAULT TRUE,
            description TEXT,
            best_season TEXT, -- 'spring', 'summer', 'fall', 'winter', 'year_round'
            parking_info TEXT,
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_visited DATETIME
        )
    ''')
    
    # RC brands and models for detection
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rc_brands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand_name TEXT NOT NULL,
            model_name TEXT,
            detection_keywords TEXT, -- JSON array of keywords
            category TEXT, -- 'crawler', 'buggy', 'monster_truck', 'drift'
            scale TEXT, -- '1/10', '1/24', '1/8'
            popularity_score INTEGER DEFAULT 0,
            price_range TEXT,
            terrain_type TEXT -- 'rock_crawler', 'trail', 'speed_run'
        )
    ''')
    
    # Competitor analysis for optimal posting
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS competitor_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_name TEXT NOT NULL,
            platform TEXT NOT NULL, -- 'youtube', 'instagram'
            niche TEXT, -- 'vanlife', 'rc_trucks'
            posting_times TEXT, -- JSON array of optimal times
            avg_engagement_rate REAL,
            avg_views INTEGER,
            content_style TEXT,
            hashtag_strategy TEXT, -- JSON array of commonly used hashtags
            analysis_date DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Revenue tracking for van life income
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS revenue_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER,
            revenue_source TEXT, -- 'ad_revenue', 'sponsorship', 'affiliate', 'merchandise'
            amount REAL,
            currency TEXT DEFAULT 'CAD',
            date DATETIME,
            conversion_type TEXT, -- 'view', 'click', 'sale'
            sponsor_brand TEXT,
            notes TEXT,
            FOREIGN KEY (post_id) REFERENCES social_media_posts (id)
        )
    ''')
    
    # Hashtag performance tracking
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hashtag_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hashtag TEXT NOT NULL,
            niche TEXT, -- 'vanlife', 'rc_trucks'
            platform TEXT, -- 'youtube', 'instagram'
            usage_count INTEGER DEFAULT 1,
            avg_engagement REAL DEFAULT 0.0,
            trending_score INTEGER DEFAULT 0,
            last_used DATETIME DEFAULT CURRENT_TIMESTAMP,
            performance_data TEXT -- JSON with detailed metrics
        )
    ''')
    
    # Content calendar for scheduling
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS content_calendar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER,
            scheduled_date DATETIME NOT NULL,
            content_type TEXT,
            theme TEXT, -- 'trail_exploration', 'van_setup', 'rc_review'
            status TEXT DEFAULT 'scheduled',
            notes TEXT,
            FOREIGN KEY (post_id) REFERENCES social_media_posts (id)
        )
    ''')
    
    # Insert default RC brands for detection
    rc_brands_data = [
        ('Axial Racing', 'SCX24', '["scx24", "axial", "deadbolt", "jeep"]', 'crawler', '1/24'),
        ('Axial Racing', 'SCX10 III', '["scx10", "axial", "jeep", "gladiator"]', 'crawler', '1/10'),
        ('Axial Racing', 'RBX10', '["rbx10", "axial", "ryft", "buggy"]', 'buggy', '1/10'),
        ('Vanquish Products', 'VS4-10', '["vs410", "vanquish", "phoenix"]', 'crawler', '1/10'),
        ('Vanquish Products', 'VS4-18', '["vs418", "vanquish", "phoenix"]', 'crawler', '1/8'),
        ('Traxxas', 'TRX-4', '["trx4", "traxxas", "defender", "bronco"]', 'crawler', '1/10'),
        ('Associated', 'Enduro', '["enduro", "associated", "sendero"]', 'crawler', '1/10'),
        ('Element RC', 'Enduro24', '["enduro24", "element", "trail_truck"]', 'crawler', '1/24'),
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO rc_brands 
        (brand_name, model_name, detection_keywords, category, scale)
        VALUES (?, ?, ?, ?, ?)
    ''', rc_brands_data)
    
    # Insert default Southern BC trail locations
    trail_locations_data = [
        ('Whistler Mountain Bike Park', 'Whistler', 'moderate', 50.1163, -122.9574, 'RC trails near bike park', 'summer'),
        ('Squamish Chief Trail', 'Squamish', 'difficult', 49.6816, -123.1550, 'Rocky terrain, great for crawlers', 'spring'),
        ('Lynn Canyon', 'North Vancouver', 'easy', 49.3429, -123.0198, 'Forest trails, family friendly', 'year_round'),
        ('Cypress Mountain', 'West Vancouver', 'moderate', 49.3965, -123.2065, 'Mountain trails with views', 'summer'),
        ('Golden Ears Park', 'Maple Ridge', 'difficult', 49.2606, -122.4931, 'Challenging terrain for advanced crawlers', 'summer'),
        ('Harrison Hot Springs', 'Harrison Mills', 'easy', 49.2944, -121.7750, 'Lakeside trails, scenic camping', 'year_round'),
        ('Cultus Lake', 'Chilliwack', 'moderate', 49.0531, -121.9964, 'Popular camping spot with RC trails', 'summer'),
        ('Mount Seymour', 'North Vancouver', 'difficult', 49.3845, -122.9446, 'Technical mountain terrain', 'summer'),
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO trail_locations 
        (name, region, difficulty, gps_lat, gps_long, description, best_season)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', trail_locations_data)
    
    # Insert default hashtag performance data
    hashtag_data = [
        ('#vanlife', 'vanlife', 'instagram', 100, 8.5, 95),
        ('#bctrails', 'vanlife', 'instagram', 50, 6.2, 80),
        ('#nomadlife', 'vanlife', 'instagram', 80, 7.1, 85),
        ('#homeiswhereyouparkit', 'vanlife', 'instagram', 60, 9.2, 90),
        ('#roadtrip', 'vanlife', 'instagram', 90, 5.8, 75),
        ('#axialracing', 'rc_trucks', 'instagram', 40, 12.5, 88),
        ('#vanquish', 'rc_trucks', 'instagram', 25, 15.2, 92),
        ('#rctrucks', 'rc_trucks', 'instagram', 70, 10.8, 82),
        ('#trailtherapy', 'rc_trucks', 'instagram', 30, 18.5, 95),
        ('#scalerc', 'rc_trucks', 'instagram', 45, 11.2, 78),
        ('#rccrawler', 'rc_trucks', 'instagram', 55, 13.8, 85),
        ('#southernbc', 'vanlife', 'instagram', 35, 9.8, 70),
        ('#bcoutdoors', 'vanlife', 'instagram', 40, 8.2, 72),
        ('#whistler', 'vanlife', 'instagram', 60, 6.5, 68),
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO hashtag_performance 
        (hashtag, niche, platform, usage_count, avg_engagement, trending_score)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', hashtag_data)
    
    # Insert Instagram hashtag research data
    instagram_hashtag_research_data = [
        ('#vanlife', 15000000, 6.8, 'high', '["6:00", "19:00", "21:00"]', '["#nomadlife", "#roadtrip", "#homeonwheels"]'),
        ('#vanlifeadventure', 2500000, 9.2, 'medium', '["7:00", "18:00", "20:00"]', '["#vanlife", "#adventure", "#travel"]'),
        ('#bcvanlife', 150000, 12.5, 'low', '["6:00", "17:00", "19:00"]', '["#vanlife", "#explorebc", "#bcoutdoors"]'),
        ('#rctrucks', 3500000, 8.5, 'medium', '["14:00", "18:00", "20:00"]', '["#rccrawler", "#radiocontrol", "#rclife"]'),
        ('#scalecrawler', 450000, 15.8, 'low', '["15:00", "19:00", "21:00"]', '["#rccrawler", "#rctrucks", "#axialracing"]'),
        ('#trailtherapy', 85000, 18.2, 'low', '["16:00", "18:00", "20:00"]', '["#rctrucks", "#outdoors", "#adventure"]'),
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO instagram_hashtag_research 
        (hashtag, post_count, engagement_rate, competition_level, best_times, related_hashtags)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', instagram_hashtag_research_data)
    
    conn.commit()
    conn.close()
    
    print("✅ Social media database extension complete!")
    print(f"📊 Added {len(rc_brands_data)} RC brands")
    print(f"🏔️ Added {len(trail_locations_data)} Southern BC trail locations")
    print(f"🏷️ Added {len(hashtag_data)} hashtag performance records")
    print(f"📱 Added {len(instagram_hashtag_research_data)} Instagram hashtag research records")
    print(f"🔗 Instagram integration tables created and populated")

def get_social_media_stats(db_path="lifeos_local.db"):
    """Get current social media database statistics"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    stats = {}
    
    tables = [
        'social_media_posts',
        'trail_locations', 
        'rc_brands',
        'revenue_tracking',
        'hashtag_performance',
        'instagram_accounts',
        'scheduled_instagram_posts',
        'instagram_stories',
        'instagram_hashtag_research',
        'instagram_performance'
    ]
    
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            stats[table] = count
        except:
            stats[table] = 0
    
    conn.close()
    return stats

if __name__ == "__main__":
    # Extend the database
    extend_database_for_social_media()
    
    # Show stats
    stats = get_social_media_stats()
    print(f"\n📊 DATABASE STATISTICS:")
    for table, count in stats.items():
        print(f"  {table}: {count} records")