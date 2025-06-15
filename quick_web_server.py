
from flask import Flask, render_template, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def index():
    with open('unified_main_page.html', 'r') as f:
        return f.read()

@app.route('/realtime-teams')
def realtime_teams():
    with open('quick_realtime_page.html', 'r') as f:
        return f.read()

@app.route('/api/realtime-teams')
def get_realtime_teams():
    try:
        conn = sqlite3.connect('project_management.db')
        cursor = conn.cursor()
        cursor.execute("SELECT t.title, w.name, t.status FROM tasks t JOIN workers w ON t.assigned_to = w.id LIMIT 10")
        teams = []
        for row in cursor.fetchall():
            teams.append({'task': row[0], 'worker': row[1], 'status': row[2]})
        conn.close()
        return jsonify({'success': True, 'teams': teams})
    except:
        return jsonify({'success': False, 'teams': []})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
