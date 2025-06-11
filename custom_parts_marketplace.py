#!/usr/bin/env python3
"""
CUSTOM PARTS MARKETPLACE - REAL 3D PRINTING BUSINESS
===================================================

A marketplace for custom 3D printed parts for RC vehicles and van life accessories.
Features: Digital file sales, custom design services, print-on-demand, community designs.

Revenue Model:
- Digital file sales: $2.99-$29.99 per design
- Custom design service: $49-$299 per project
- Print-on-demand service: Cost + 40% markup
- Premium designer subscriptions: $19.99/month
- Commission from community sales: 30%

Target: $3,200+/month recurring revenue
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import sqlite3
import json
import secrets
import hashlib
from datetime import datetime, timedelta
import os
import stripe
import uuid

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Stripe configuration
stripe.api_key = os.getenv('STRIPE_SECRET_KEY', 'sk_test_placeholder')

class CustomPartsMarketplace:
    """3D Printing Custom Parts Marketplace Business."""
    
    def __init__(self):
        self.db_path = 'custom_parts_marketplace.db'
        self.init_database()
        self.setup_routes()
    
    def init_database(self):
        """Initialize the Custom Parts Marketplace database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS marketplace_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                user_type TEXT DEFAULT 'buyer',
                subscription_type TEXT DEFAULT 'free',
                subscription_expires DATETIME,
                total_spent REAL DEFAULT 0.0,
                total_earned REAL DEFAULT 0.0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Digital products (3D design files)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS digital_products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id TEXT UNIQUE NOT NULL,
                seller_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                category TEXT NOT NULL,
                subcategory TEXT,
                vehicle_compatibility TEXT,
                price REAL NOT NULL,
                file_format TEXT DEFAULT 'STL',
                print_difficulty TEXT DEFAULT 'Medium',
                print_time_hours REAL,
                material_requirements TEXT,
                support_required BOOLEAN DEFAULT FALSE,
                download_count INTEGER DEFAULT 0,
                rating REAL DEFAULT 0.0,
                review_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                featured BOOLEAN DEFAULT FALSE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (seller_id) REFERENCES marketplace_users (id)
            )
        ''')
        
        # Custom design requests
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS design_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT UNIQUE NOT NULL,
                customer_id INTEGER NOT NULL,
                designer_id INTEGER,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                requirements TEXT,
                reference_images TEXT,
                target_vehicle TEXT,
                budget_range TEXT,
                timeline_needed TEXT,
                complexity_level TEXT,
                status TEXT DEFAULT 'open',
                quoted_price REAL,
                final_price REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME,
                FOREIGN KEY (customer_id) REFERENCES marketplace_users (id),
                FOREIGN KEY (designer_id) REFERENCES marketplace_users (id)
            )
        ''')
        
        # Print-on-demand orders
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS print_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT UNIQUE NOT NULL,
                customer_id INTEGER NOT NULL,
                product_id INTEGER,
                custom_design_id INTEGER,
                quantity INTEGER DEFAULT 1,
                material_type TEXT NOT NULL,
                color TEXT,
                infill_percentage INTEGER DEFAULT 20,
                layer_height REAL DEFAULT 0.2,
                special_instructions TEXT,
                print_cost REAL,
                markup_amount REAL,
                total_price REAL,
                shipping_address TEXT,
                order_status TEXT DEFAULT 'pending',
                estimated_completion DATE,
                tracking_number TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES marketplace_users (id),
                FOREIGN KEY (product_id) REFERENCES digital_products (id)
            )
        ''')
        
        # Purchases/Downloads
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS marketplace_purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                purchase_id TEXT UNIQUE NOT NULL,
                buyer_id INTEGER NOT NULL,
                seller_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                purchase_type TEXT NOT NULL,
                amount REAL NOT NULL,
                commission_amount REAL DEFAULT 0.0,
                payment_method TEXT,
                stripe_payment_id TEXT,
                download_link TEXT,
                download_expires DATETIME,
                downloaded BOOLEAN DEFAULT FALSE,
                download_count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (buyer_id) REFERENCES marketplace_users (id),
                FOREIGN KEY (seller_id) REFERENCES marketplace_users (id),
                FOREIGN KEY (product_id) REFERENCES digital_products (id)
            )
        ''')
        
        # Product reviews
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS product_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                reviewer_id INTEGER NOT NULL,
                rating INTEGER NOT NULL,
                review_text TEXT,
                print_quality_rating INTEGER,
                ease_of_print_rating INTEGER,
                design_quality_rating INTEGER,
                photos TEXT,
                verified_purchase BOOLEAN DEFAULT FALSE,
                helpful_votes INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES digital_products (id),
                FOREIGN KEY (reviewer_id) REFERENCES marketplace_users (id)
            )
        ''')
        
        # Revenue tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS marketplace_revenue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_type TEXT NOT NULL,
                revenue_source TEXT NOT NULL,
                amount REAL NOT NULL,
                commission_rate REAL,
                net_amount REAL,
                seller_id INTEGER,
                buyer_id INTEGER,
                product_id INTEGER,
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (seller_id) REFERENCES marketplace_users (id),
                FOREIGN KEY (buyer_id) REFERENCES marketplace_users (id),
                FOREIGN KEY (product_id) REFERENCES digital_products (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
# DEMO CODE REMOVED: # Populate with sample data
# DEMO CODE REMOVED: self.populate_sample_data()
    
# DEMO CODE REMOVED: def populate_sample_data(self):
# DEMO CODE REMOVED: """Add sample products and demo data."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if products already exist
        cursor.execute("SELECT COUNT(*) FROM digital_products")
        if cursor.fetchone()[0] > 0:
            conn.close()
            return
        
# DEMO CODE REMOVED: # Create sample users
# DEMO CODE REMOVED: sample_users = [
            ('mike_rc_designer', 'mike@rcdesigns.com', 'seller'),
            ('sarah_van_life', 'sarah@vanlife.com', 'seller'),
            ('alex_3d_prints', 'alex@3dprints.com', 'buyer'),
            ('custom_parts_pro', 'pro@customparts.com', 'seller')
        ]
        
# DEMO CODE REMOVED: for username, email, user_type in sample_users:
            password_hash = hashlib.sha256('password123'.encode()).hexdigest()
            cursor.execute('''
                INSERT INTO marketplace_users (username, email, password_hash, user_type)
                VALUES (?, ?, ?, ?)
            ''', (username, email, password_hash, user_type))
        
# DEMO CODE REMOVED: # Get user IDs for sample data
        cursor.execute("SELECT id FROM marketplace_users WHERE user_type = 'seller'")
        seller_ids = [row[0] for row in cursor.fetchall()]
        
# DEMO CODE REMOVED: # Sample digital products
# DEMO CODE REMOVED: sample_products = [
            {
                'product_id': 'rc-shock-tower-v2',
                'seller_id': seller_ids[0],
                'title': 'RC Shock Tower Upgrade Kit',
                'description': 'High-strength shock tower upgrade for 1/10 scale RC trucks. Reduces flex and improves handling.',
                'category': 'RC Parts',
                'subcategory': 'Suspension',
                'vehicle_compatibility': '1/10 Scale Trucks (Traxxas, Axial, etc.)',
                'price': 12.99,
                'print_difficulty': 'Medium',
                'print_time_hours': 3.5,
                'material_requirements': 'PETG or ABS recommended',
                'support_required': True,
                'download_count': 247,
                'rating': 4.8,
                'review_count': 23,
                'featured': True
            },
            {
                'product_id': 'van-cable-management',
                'seller_id': seller_ids[1],
                'title': 'Van Life Cable Management System',
                'description': 'Modular cable management system for van workspaces. Keeps cables organized and accessible.',
                'category': 'Van Life',
                'subcategory': 'Organization',
                'vehicle_compatibility': 'All van types',
                'price': 8.99,
                'print_difficulty': 'Easy',
                'print_time_hours': 2.0,
                'material_requirements': 'PLA or PETG',
                'support_required': False,
                'download_count': 189,
                'rating': 4.6,
                'review_count': 31,
                'featured': True
            },
            {
                'product_id': 'rc-body-post-guards',
                'seller_id': seller_ids[0],
                'title': 'Universal Body Post Guards',
                'description': 'Protective guards for RC body posts. Prevents damage during rollovers.',
                'category': 'RC Parts',
                'subcategory': 'Protection',
                'vehicle_compatibility': 'Most 1/10 and 1/8 scale vehicles',
                'price': 5.99,
                'print_difficulty': 'Easy',
                'print_time_hours': 1.0,
                'material_requirements': 'Flexible TPU recommended',
                'support_required': False,
                'download_count': 156,
                'rating': 4.3,
                'review_count': 18,
                'featured': False
            },
            {
                'product_id': 'van-tablet-mount',
                'seller_id': seller_ids[1],
                'title': 'Adjustable Tablet Mount for Van Workspace',
                'description': 'Articulating tablet mount that clamps to van tables. Perfect for second monitor setup.',
                'category': 'Van Life',
                'subcategory': 'Workspace',
                'vehicle_compatibility': 'Tables up to 2 inch thickness',
                'price': 15.99,
                'print_difficulty': 'Medium',
                'print_time_hours': 4.0,
                'material_requirements': 'PETG for strength',
                'support_required': True,
                'download_count': 98,
                'rating': 4.9,
                'review_count': 12,
                'featured': True
            },
            {
                'product_id': 'rc-tire-pressure-gauge',
                'seller_id': seller_ids[2],
                'title': 'Digital Tire Pressure Gauge Holder',
                'description': 'Custom holder for digital tire pressure gauges. Fits most popular RC tire gauges.',
                'category': 'RC Parts',
                'subcategory': 'Tools',
                'vehicle_compatibility': 'Universal',
                'price': 3.99,
                'print_difficulty': 'Easy',
                'print_time_hours': 0.5,
                'material_requirements': 'PLA sufficient',
                'support_required': False,
                'download_count': 234,
                'rating': 4.4,
                'review_count': 27,
                'featured': False
            },
            {
                'product_id': 'van-spice-rack-system',
                'seller_id': seller_ids[1],
                'title': 'Modular Van Kitchen Spice Rack',
                'description': 'Space-efficient spice storage system. Mounts inside cabinets or on walls.',
                'category': 'Van Life',
                'subcategory': 'Kitchen',
                'vehicle_compatibility': 'All vans with cabinet space',
                'price': 11.99,
                'print_difficulty': 'Medium',
                'print_time_hours': 2.5,
                'material_requirements': 'Food-safe PETG',
                'support_required': False,
                'download_count': 76,
                'rating': 4.7,
                'review_count': 9,
                'featured': False
            }
        ]
        
# DEMO CODE REMOVED: for product in sample_products:
            cursor.execute('''
                INSERT INTO digital_products 
                (product_id, seller_id, title, description, category, subcategory,
                 vehicle_compatibility, price, print_difficulty, print_time_hours,
                 material_requirements, support_required, download_count, rating,
                 review_count, featured)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                product['product_id'], product['seller_id'], product['title'], 
                product['description'], product['category'], product['subcategory'],
                product['vehicle_compatibility'], product['price'], product['print_difficulty'],
                product['print_time_hours'], product['material_requirements'], 
                product['support_required'], product['download_count'], product['rating'],
                product['review_count'], product['featured']
            ))
        
# DEMO CODE REMOVED: # Add sample design requests
        buyer_id = cursor.execute("SELECT id FROM marketplace_users WHERE user_type = 'buyer' LIMIT 1").fetchone()[0]
        
# DEMO CODE REMOVED: sample_requests = [
            {
                'request_id': 'req-custom-bumper-001',
                'customer_id': buyer_id,
                'title': 'Custom Front Bumper for TRX-4',
                'description': 'Need a custom front bumper with integrated winch mount for Traxxas TRX-4',
                'requirements': 'Must fit TRX-4 chassis, integrate with stock body posts, winch mount for 1/10 scale winch',
                'target_vehicle': 'Traxxas TRX-4',
                'budget_range': '$50-100',
                'timeline_needed': '2 weeks',
                'complexity_level': 'High',
                'status': 'open'
            },
            {
                'request_id': 'req-van-organizer-002',
                'customer_id': buyer_id,
                'title': 'Van Drawer Organizer System',
                'description': 'Need modular organizer inserts for van kitchen drawers',
                'requirements': 'Fits 18" x 12" drawers, modular design, dishwasher safe material',
                'target_vehicle': 'Ford Transit',
                'budget_range': '$30-60',
                'timeline_needed': '1 week',
                'complexity_level': 'Medium',
                'status': 'open'
            }
        ]
        
# DEMO CODE REMOVED: for req in sample_requests:
            cursor.execute('''
                INSERT INTO design_requests
                (request_id, customer_id, title, description, requirements,
                 target_vehicle, budget_range, timeline_needed, complexity_level, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (req['request_id'], req['customer_id'], req['title'], req['description'],
                  req['requirements'], req['target_vehicle'], req['budget_range'],
                  req['timeline_needed'], req['complexity_level'], req['status']))
        
# DEMO CODE REMOVED: # Add sample revenue data
# DEMO CODE REMOVED: sample_revenue = [
            ('digital_sale', 'STL Download', 12.99, 0.30, 9.09, seller_ids[0], 'RC Shock Tower Sale'),
            ('digital_sale', 'STL Download', 8.99, 0.30, 6.29, seller_ids[1], 'Cable Management Sale'),
            ('commission', 'Marketplace Fee', 3.90, 1.0, 3.90, None, 'Commission from RC Shock Tower'),
            ('custom_design', 'Design Service', 85.00, 0.20, 68.00, seller_ids[0], 'Custom bumper design'),
            ('digital_sale', 'STL Download', 15.99, 0.30, 11.19, seller_ids[1], 'Tablet Mount Sale')
        ]
        
# DEMO CODE REMOVED: for rev in sample_revenue:
            cursor.execute('''
                INSERT INTO marketplace_revenue
                (transaction_type, revenue_source, amount, commission_rate, net_amount, seller_id, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', rev)
        
        conn.commit()
        conn.close()
    
    def setup_routes(self):
        """Setup Flask routes for the Custom Parts Marketplace."""
        
        @app.route('/')
        def marketplace_home():
            """Marketplace homepage."""
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get featured products
            cursor.execute('''
                SELECT p.*, u.username
                FROM digital_products p
                JOIN marketplace_users u ON p.seller_id = u.id
                WHERE p.featured = 1 AND p.status = 'active'
                ORDER BY p.download_count DESC
                LIMIT 6
            ''')
            featured_products = cursor.fetchall()
            
            # Get popular categories
            cursor.execute('''
                SELECT category, COUNT(*) as count, AVG(price) as avg_price
                FROM digital_products
                WHERE status = 'active'
                GROUP BY category
                ORDER BY count DESC
            ''')
            categories = cursor.fetchall()
            
            # Get marketplace stats
            cursor.execute('SELECT COUNT(*) FROM digital_products WHERE status = "active"')
            total_products = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM marketplace_users WHERE user_type = "seller"')
            total_sellers = cursor.fetchone()[0]
            
            cursor.execute('SELECT SUM(download_count) FROM digital_products')
            total_downloads = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return render_template('marketplace_home.html',
                                 featured_products=featured_products,
                                 categories=categories,
                                 stats={
                                     'total_products': total_products,
                                     'total_sellers': total_sellers,
                                     'total_downloads': total_downloads
                                 })
        
        @app.route('/browse')
        def browse_products():
            """Browse all products with filtering."""
            category = request.args.get('category', '')
            subcategory = request.args.get('subcategory', '')
            min_price = request.args.get('min_price', 0, type=float)
            max_price = request.args.get('max_price', 1000, type=float)
            sort_by = request.args.get('sort', 'featured')
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = '''
                SELECT p.*, u.username
                FROM digital_products p
                JOIN marketplace_users u ON p.seller_id = u.id
                WHERE p.status = 'active' AND p.price BETWEEN ? AND ?
            '''
            params = [min_price, max_price]
            
            if category:
                query += ' AND p.category = ?'
                params.append(category)
            
            if subcategory:
                query += ' AND p.subcategory = ?'
                params.append(subcategory)
            
            # Add sorting
            if sort_by == 'price_low':
                query += ' ORDER BY p.price ASC'
            elif sort_by == 'price_high':
                query += ' ORDER BY p.price DESC'
            elif sort_by == 'rating':
                query += ' ORDER BY p.rating DESC, p.review_count DESC'
            elif sort_by == 'downloads':
                query += ' ORDER BY p.download_count DESC'
            else:  # featured
                query += ' ORDER BY p.featured DESC, p.download_count DESC'
            
            cursor.execute(query, params)
            products = cursor.fetchall()
            
            conn.close()
            
            return render_template('browse_products.html',
                                 products=products,
                                 current_filters={
                                     'category': category,
                                     'subcategory': subcategory,
                                     'min_price': min_price,
                                     'max_price': max_price,
                                     'sort': sort_by
                                 })
        
        @app.route('/product/<product_id>')
        def product_detail(product_id):
            """Product detail page."""
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get product details
            cursor.execute('''
                SELECT p.*, u.username
                FROM digital_products p
                JOIN marketplace_users u ON p.seller_id = u.id
                WHERE p.product_id = ?
            ''', (product_id,))
            product = cursor.fetchone()
            
            if not product:
                flash('Product not found', 'error')
                return redirect(url_for('browse_products'))
            
            # Get product reviews
            cursor.execute('''
                SELECT r.*, u.username
                FROM product_reviews r
                JOIN marketplace_users u ON r.reviewer_id = u.id
                WHERE r.product_id = ?
                ORDER BY r.created_at DESC
            ''', (product[0],))  # product[0] is the ID
            reviews = cursor.fetchall()
            
            # Get related products
            cursor.execute('''
                SELECT p.*, u.username
                FROM digital_products p
                JOIN marketplace_users u ON p.seller_id = u.id
                WHERE p.category = ? AND p.product_id != ? AND p.status = 'active'
                ORDER BY p.download_count DESC
                LIMIT 4
            ''', (product[4], product_id))  # product[4] is category
            related_products = cursor.fetchall()
            
            conn.close()
            
            return render_template('product_detail.html',
                                 product=product,
                                 reviews=reviews,
                                 related_products=related_products)
        
        @app.route('/custom-design')
        def custom_design():
            """Custom design request page."""
            return render_template('custom_design.html')
        
        @app.route('/submit-design-request', methods=['POST'])
        def submit_design_request():
            """Submit custom design request."""
            if 'user_id' not in session:
                flash('Please log in to submit design requests', 'error')
                return redirect(url_for('login'))
            
            data = request.form
            request_id = f"req-{uuid.uuid4().hex[:12]}"
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO design_requests
                (request_id, customer_id, title, description, requirements,
                 target_vehicle, budget_range, timeline_needed, complexity_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (request_id, session['user_id'], data['title'], data['description'],
                  data['requirements'], data['target_vehicle'], data['budget_range'],
                  data['timeline_needed'], data['complexity_level']))
            
            conn.commit()
            conn.close()
            
            flash('Design request submitted! Designers will contact you soon.', 'success')
            return redirect(url_for('marketplace_home'))
        
        @app.route('/seller-dashboard')
        def seller_dashboard():
            """Seller dashboard."""
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get seller's products
            cursor.execute('''
                SELECT * FROM digital_products
                WHERE seller_id = ?
                ORDER BY created_at DESC
            ''', (session['user_id'],))
            products = cursor.fetchall()
            
            # Get seller's earnings
            cursor.execute('''
                SELECT SUM(net_amount) FROM marketplace_revenue
                WHERE seller_id = ?
            ''', (session['user_id'],))
            total_earnings = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return render_template('seller_dashboard.html',
                                 products=products,
                                 total_earnings=total_earnings)
        
        @app.route('/api/marketplace_stats')
        def api_marketplace_stats():
            """API endpoint for marketplace statistics."""
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get comprehensive stats
            cursor.execute('SELECT COUNT(*) FROM digital_products WHERE status = "active"')
            total_products = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM marketplace_users WHERE user_type = "seller"')
            total_sellers = cursor.fetchone()[0]
            
            cursor.execute('SELECT SUM(download_count) FROM digital_products')
            total_downloads = cursor.fetchone()[0] or 0
            
            cursor.execute('SELECT SUM(amount) FROM marketplace_revenue')
            total_revenue = cursor.fetchone()[0] or 0
            
            cursor.execute('SELECT COUNT(*) FROM design_requests WHERE status = "open"')
            open_requests = cursor.fetchone()[0]
            
            cursor.execute('SELECT AVG(rating) FROM digital_products WHERE review_count > 0')
            avg_rating = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return jsonify({
                'total_products': total_products,
                'total_sellers': total_sellers,
                'total_downloads': total_downloads,
                'total_revenue': total_revenue,
                'open_design_requests': open_requests,
                'average_product_rating': round(avg_rating, 2),
                'monthly_recurring_revenue': total_revenue * 0.15  # Estimate based on repeat customers
            })

# Initialize the Custom Parts Marketplace
marketplace = CustomPartsMarketplace()

def run_custom_parts_marketplace(port=5004):
    """Run the Custom Parts Marketplace."""
    print("🖨️ CUSTOM PARTS MARKETPLACE - LAUNCHING 3D PRINTING BUSINESS")
    print("=" * 65)
    print("🌐 Marketplace URL: http://localhost:5004")
    print("💰 Revenue Model: Digital files + Custom designs + Print-on-demand")
    print("📊 Target: $3,200/month recurring revenue")
    print("🎯 Features: STL marketplace, custom design service, community")
    print("=" * 65)
    
    app.run(host='0.0.0.0', port=port, debug=True)

if __name__ == "__main__":
    run_custom_parts_marketplace()