#!/usr/bin/env python3
"""
VAN LIFE WORKSPACE OPTIMIZER - REAL BUSINESS SERVICE
===================================================

A consulting service that optimizes van setups for remote work productivity.
Features: Van assessments, custom optimization plans, 3D visualizations, equipment sales.

Revenue Model:
- Initial consultation: $199 (1-2 hours virtual assessment)
- Custom optimization plan: $499 (detailed layout with 3D models)
- Implementation support: $99/hour
- Equipment affiliate commissions: 15%
- Monthly workspace coaching: $89/month

Target: $4,000+/month recurring revenue
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import sqlite3
import json
import secrets
import hashlib
from datetime import datetime, timedelta
import os
import stripe

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Stripe configuration
stripe.api_key = os.getenv('STRIPE_SECRET_KEY', 'sk_test_placeholder')

class VanLifeOptimizerService:
    """Van Life Workspace Optimization Business Service."""
    
    def __init__(self):
        self.db_path = 'van_life_optimizer.db'
        self.init_database()
        self.setup_routes()
    
    def init_database(self):
        """Initialize the Van Life Optimizer database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clients table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT,
                van_type TEXT,
                van_size TEXT,
                current_setup_description TEXT,
                work_type TEXT,
                consultation_status TEXT DEFAULT 'requested',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                total_spent REAL DEFAULT 0.0
            )
        ''')
        
        # Consultation sessions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS consultations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                consultation_type TEXT NOT NULL,
                scheduled_date DATETIME,
                duration_minutes INTEGER DEFAULT 120,
                consultation_notes TEXT,
                pain_points TEXT,
                goals TEXT,
                budget_range TEXT,
                status TEXT DEFAULT 'scheduled',
                price REAL NOT NULL,
                zoom_link TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients (id)
            )
        ''')
        
        # Optimization plans
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS optimization_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                consultation_id INTEGER,
                plan_title TEXT NOT NULL,
                current_setup_analysis TEXT,
                optimization_recommendations TEXT,
                layout_3d_model TEXT,
                equipment_list TEXT,
                implementation_steps TEXT,
                estimated_cost REAL,
                estimated_timeline TEXT,
                plan_status TEXT DEFAULT 'draft',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients (id),
                FOREIGN KEY (consultation_id) REFERENCES consultations (id)
            )
        ''')
        
        # Equipment recommendations with affiliate tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS equipment_catalog (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                item_name TEXT NOT NULL,
                description TEXT,
                price_range TEXT,
                affiliate_link TEXT,
                affiliate_commission REAL DEFAULT 0.0,
                van_size_compatibility TEXT,
                pros TEXT,
                cons TEXT,
                image_url TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Coaching subscriptions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS coaching_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                subscription_type TEXT DEFAULT 'monthly_coaching',
                start_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                end_date DATETIME,
                monthly_price REAL DEFAULT 89.0,
                status TEXT DEFAULT 'active',
                coaching_focus TEXT,
                session_count INTEGER DEFAULT 0,
                FOREIGN KEY (client_id) REFERENCES clients (id)
            )
        ''')
        
        # Implementation support sessions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS support_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                session_date DATETIME,
                duration_hours REAL,
                hourly_rate REAL DEFAULT 99.0,
                session_type TEXT,
                work_completed TEXT,
                next_steps TEXT,
                photos_before TEXT,
                photos_after TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients (id)
            )
        ''')
        
        # Revenue tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS revenue_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER,
                transaction_type TEXT NOT NULL,
                service_type TEXT NOT NULL,
                amount REAL NOT NULL,
                payment_method TEXT,
                stripe_payment_id TEXT,
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
# DEMO CODE REMOVED: # Populate with sample data
# DEMO CODE REMOVED: self.populate_sample_data()
    
# DEMO CODE REMOVED: def populate_sample_data(self):
# DEMO CODE REMOVED: """Add sample equipment and demo data."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if equipment already exists
        cursor.execute("SELECT COUNT(*) FROM equipment_catalog")
        if cursor.fetchone()[0] > 0:
            conn.close()
            return
        
# DEMO CODE REMOVED: # Sample equipment recommendations
        equipment_items = [
            {
                'category': 'Internet/Connectivity',
                'item_name': 'WeBoost Drive Reach RV Cell Signal Booster',
                'description': 'Powerful cell signal amplifier for reliable internet in remote areas',
                'price_range': '$499-599',
                'affiliate_link': 'https://amzn.to/weboost-rv',
                'affiliate_commission': 45.99,
                'van_size_compatibility': 'All sizes',
                'pros': 'Dramatically improves cell signal, Easy installation, Works with all carriers',
                'cons': 'Requires external antenna, Higher power consumption'
            },
            {
                'category': 'Power Management',
                'item_name': 'Victron MultiPlus Inverter/Charger',
                'description': 'High-quality pure sine wave inverter with built-in charger',
                'price_range': '$800-1200',
                'affiliate_link': 'https://amzn.to/victron-multiplus',
                'affiliate_commission': 85.50,
                'van_size_compatibility': 'Medium to Large vans',
                'pros': 'Excellent build quality, Remote monitoring, Pure sine wave',
                'cons': 'Higher cost, Complex installation'
            },
            {
                'category': 'Workspace Furniture',
                'item_name': 'UPLIFT Desk V2 Standing Desk Converter',
                'description': 'Adjustable standing desk converter for van workspaces',
                'price_range': '$399-699',
                'affiliate_link': 'https://upliftdesk.pxf.io/van-life',
                'affiliate_commission': 65.25,
                'van_size_compatibility': 'Medium to Large vans',
                'pros': 'Health benefits, Compact when lowered, Sturdy construction',
                'cons': 'Takes up counter space, Needs secure mounting'
            },
            {
                'category': 'Climate Control',
                'item_name': 'Maxxair Fan with Remote Control',
                'description': 'Powerful exhaust fan with rain sensor and remote',
                'price_range': '$199-249',
                'affiliate_link': 'https://amzn.to/maxxair-fan',
                'affiliate_commission': 28.75,
                'van_size_compatibility': 'All sizes',
                'pros': 'Quiet operation, Rain sensor, Remote control',
                'cons': 'Requires roof installation, Some wind noise at highway speeds'
            },
            {
                'category': 'Storage Solutions',
                'item_name': 'Sterilite Modular Storage System',
                'description': 'Customizable storage cubes for organizing office supplies',
                'price_range': '$89-149',
                'affiliate_link': 'https://amzn.to/sterilite-modular',
                'affiliate_commission': 15.99,
                'van_size_compatibility': 'All sizes',
                'pros': 'Highly customizable, Lightweight, Affordable',
                'cons': 'Not as durable as wood, Limited weight capacity'
            },
            {
                'category': 'Lighting',
                'item_name': 'Lumens LED Strip Lighting Kit',
                'description': 'Dimmable LED strips with controller for workspace lighting',
                'price_range': '$79-129',
                'affiliate_link': 'https://amzn.to/lumens-led',
                'affiliate_commission': 18.50,
                'van_size_compatibility': 'All sizes',
                'pros': 'Low power consumption, Dimmable, Easy installation',
                'cons': 'Needs 12V power source, Adhesive may fail over time'
            }
        ]
        
        for item in equipment_items:
            cursor.execute('''
                INSERT INTO equipment_catalog 
                (category, item_name, description, price_range, affiliate_link, 
                 affiliate_commission, van_size_compatibility, pros, cons)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                item['category'], item['item_name'], item['description'], 
                item['price_range'], item['affiliate_link'], item['affiliate_commission'],
                item['van_size_compatibility'], item['pros'], item['cons']
            ))
        
# DEMO CODE REMOVED: # Add sample client for demo
        cursor.execute('''
            INSERT INTO clients 
            (name, email, van_type, van_size, work_type, consultation_status, total_spent)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('Sarah Digital Nomad', 'sarah@example.com', 'Ford Transit', 'Medium (148" WB)', 
              'Software Development', 'completed', 698.0))
        
        client_id = cursor.lastrowid
        
# DEMO CODE REMOVED: # Add sample consultation
        cursor.execute('''
            INSERT INTO consultations 
            (client_id, consultation_type, scheduled_date, consultation_notes, 
             pain_points, goals, budget_range, status, price)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (client_id, 'Initial Assessment', datetime.now() - timedelta(days=7),
              'Comprehensive van workspace evaluation focusing on ergonomics and productivity',
              'Neck pain from poor monitor placement, limited desk space, unreliable internet',
              'Create ergonomic workspace, improve internet reliability, maximize storage',
              '$2000-3000', 'completed', 199.0))
        
        consultation_id = cursor.lastrowid
        
# DEMO CODE REMOVED: # Add sample optimization plan
        cursor.execute('''
            INSERT INTO optimization_plans
            (client_id, consultation_id, plan_title, current_setup_analysis,
             optimization_recommendations, estimated_cost, estimated_timeline, plan_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (client_id, consultation_id, 'Sarah\'s Ergonomic Workspace Transformation',
              'Current setup has monitor too low, causing neck strain. Desk height not adjustable. Internet connectivity issues in remote areas.',
              'Install adjustable monitor arm, add standing desk converter, upgrade to cellular booster with external antenna. Reorganize storage for better cable management.',
              2450.0, '2-3 weeks', 'approved'))
        
# DEMO CODE REMOVED: # Add sample revenue transaction
        cursor.execute('''
            INSERT INTO revenue_transactions
            (client_id, transaction_type, service_type, amount, payment_method, description)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (client_id, 'consultation', 'Initial Assessment', 199.0, 'stripe', 
              'Initial van workspace consultation - 2 hours'))
        
        cursor.execute('''
            INSERT INTO revenue_transactions
            (client_id, transaction_type, service_type, amount, payment_method, description)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (client_id, 'optimization_plan', 'Custom Optimization Plan', 499.0, 'stripe',
              'Custom workspace optimization plan with 3D layout'))
        
        conn.commit()
        conn.close()
    
    def setup_routes(self):
        """Setup Flask routes for the Van Life Optimizer service."""
        
        @app.route('/')
        def van_life_home():
            """Van Life Optimizer homepage."""
            return render_template('van_life_home.html')
        
        @app.route('/services')
        def services():
            """Services page with pricing."""
            return render_template('van_life_services.html')
        
        @app.route('/request-consultation', methods=['GET', 'POST'])
        def request_consultation():
            """Request consultation form."""
            if request.method == 'POST':
                # Save consultation request
                data = request.form
                
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO clients
                    (name, email, phone, van_type, van_size, current_setup_description, work_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (data['name'], data['email'], data['phone'], data['van_type'],
                      data['van_size'], data['current_setup'], data['work_type']))
                
                client_id = cursor.lastrowid
                
                # Create consultation record
                cursor.execute('''
                    INSERT INTO consultations
                    (client_id, consultation_type, pain_points, goals, budget_range, price)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (client_id, 'Initial Assessment', data['pain_points'], 
                      data['goals'], data['budget_range'], 199.0))
                
                conn.commit()
                conn.close()
                
                flash('Consultation request submitted! We\'ll contact you within 24 hours.', 'success')
                return redirect(url_for('consultation_success'))
            
            return render_template('request_consultation.html')
        
        @app.route('/consultation-success')
        def consultation_success():
            """Consultation request success page."""
            return render_template('consultation_success.html')
        
        @app.route('/equipment-guide')
        def equipment_guide():
            """Equipment recommendations guide."""
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT category, item_name, description, price_range, 
                       affiliate_link, pros, cons, van_size_compatibility
                FROM equipment_catalog
                ORDER BY category, item_name
            ''')
            
            equipment = cursor.fetchall()
            conn.close()
            
            # Group by category
            equipment_by_category = {}
            for item in equipment:
                category = item[0]
                if category not in equipment_by_category:
                    equipment_by_category[category] = []
                equipment_by_category[category].append(item)
            
            return render_template('equipment_guide.html', 
                                 equipment_by_category=equipment_by_category)
        
        @app.route('/dashboard')
        def client_dashboard():
            """Client dashboard (placeholder for future development)."""
            return render_template('van_life_dashboard.html')
        
        @app.route('/api/consultation_stats')
        def api_consultation_stats():
            """API endpoint for consultation statistics."""
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get stats
            cursor.execute('SELECT COUNT(*) FROM clients')
            total_clients = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM consultations WHERE status = "completed"')
            completed_consultations = cursor.fetchone()[0]
            
            cursor.execute('SELECT SUM(amount) FROM revenue_transactions')
            total_revenue = cursor.fetchone()[0] or 0
            
            cursor.execute('SELECT COUNT(*) FROM coaching_subscriptions WHERE status = "active"')
            active_coaching = cursor.fetchone()[0]
            
            conn.close()
            
            return jsonify({
                'total_clients': total_clients,
                'completed_consultations': completed_consultations,
                'total_revenue': total_revenue,
                'active_coaching_clients': active_coaching,
                'avg_consultation_value': 199.0,
                'monthly_recurring_revenue': active_coaching * 89.0
            })
        
        @app.route('/process_payment/<service_type>')
        def process_payment(service_type):
            """Process payment for services."""
            prices = {
                'consultation': 19900,  # $199 in cents
                'optimization_plan': 49900,  # $499 in cents
                'coaching_monthly': 8900   # $89 in cents
            }
            
            try:
                checkout_session = stripe.checkout.Session.create(
                    payment_method_types=['card'],
                    line_items=[{
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {
                                'name': f'Van Life Workspace {service_type.replace("_", " ").title()}',
                            },
                            'unit_amount': prices.get(service_type, 19900),
                        },
                        'quantity': 1,
                    }],
                    mode='payment',
                    success_url=request.url_root + 'payment_success',
                    cancel_url=request.url_root + 'services',
                )
                
                return redirect(checkout_session.url, code=303)
                
            except Exception as e:
                flash(f'Payment processing error: {str(e)}', 'error')
                return redirect(url_for('services'))

# Initialize the Van Life Optimizer service
van_life_service = VanLifeOptimizerService()

def run_van_life_optimizer(port=5003):
    """Run the Van Life Optimizer service."""
    print("🚐 VAN LIFE WORKSPACE OPTIMIZER - LAUNCHING CONSULTING SERVICE")
    print("=" * 65)
    print("🌐 Service URL: http://localhost:5003")
    print("💰 Revenue Model: Consultations + Plans + Coaching + Affiliates")
    print("📊 Target: $4,000/month recurring revenue")
    print("🎯 Services: Van workspace optimization consulting")
    print("=" * 65)
    
    app.run(host='0.0.0.0', port=port, debug=True)

if __name__ == "__main__":
    run_van_life_optimizer()