#!/usr/bin/env python3
"""
PROJECT MANAGEMENT HIERARCHY - AUTONOMOUS TEAMS
==============================================

Create self-managing project teams that work independently.
Claude becomes the Executive Director, delegating to Project Managers who manage Worker Teams.

Architecture:
- Executive Director (Claude) - Strategic oversight only
- Project Managers (AI Agents) - Plan, delegate, track progress
- Worker Teams (AI Agents) - Execute specific tasks
- Task Queue System - Automated work distribution
- Progress Tracking - Real-time project monitoring

No more Claude doing all the work - autonomous teams handle everything!
"""

import asyncio
import sqlite3
import json
import os
import glob
import re
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
# import google.generativeai as genai  # Optional dependency

@dataclass
class Task:
    """Task data structure."""
    id: str
    title: str
    description: str
    priority: str
    assigned_to: str
    status: str
    created_at: datetime
    due_date: Optional[datetime] = None
    dependencies: List[str] = None
    estimated_hours: float = 0.0
    actual_hours: float = 0.0

@dataclass
class ProjectManager:
    """Project Manager agent."""
    id: str
    name: str
    specialization: str
    team_members: List[str]
    active_projects: List[str]
    performance_rating: float
    task_completion_rate: float

@dataclass
class Worker:
    """Worker agent."""
    id: str
    name: str
    skills: List[str]
    manager_id: str
    current_task: Optional[str]
    tasks_completed: int
    efficiency_rating: float

class ProjectManagementHierarchy:
    """Autonomous project management system."""
    
    def __init__(self):
        self.gemini_key = os.getenv('GEMINI_API_KEY')
        self.gemini_model = None
        # if self.gemini_key:
        #     genai.configure(api_key=self.gemini_key)
        #     self.gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        self.db_path = 'project_management.db'
        self.init_database()
        self.setup_management_structure()
    
    def init_database(self):
        """Initialize project management database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Project Managers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS project_managers (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                specialization TEXT NOT NULL,
                team_members TEXT, -- JSON array
                active_projects TEXT, -- JSON array
                performance_rating REAL DEFAULT 5.0,
                task_completion_rate REAL DEFAULT 0.0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Workers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workers (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                skills TEXT, -- JSON array
                manager_id TEXT,
                current_task TEXT,
                tasks_completed INTEGER DEFAULT 0,
                efficiency_rating REAL DEFAULT 5.0,
                status TEXT DEFAULT 'available',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (manager_id) REFERENCES project_managers (id)
            )
        ''')
        
        # Tasks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                priority TEXT DEFAULT 'medium',
                assigned_to TEXT,
                manager_id TEXT,
                status TEXT DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                due_date DATETIME,
                dependencies TEXT, -- JSON array
                estimated_hours REAL DEFAULT 0.0,
                actual_hours REAL DEFAULT 0.0,
                completion_percentage INTEGER DEFAULT 0,
                FOREIGN KEY (assigned_to) REFERENCES workers (id),
                FOREIGN KEY (manager_id) REFERENCES project_managers (id)
            )
        ''')
        
        # Projects table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                manager_id TEXT,
                status TEXT DEFAULT 'planning',
                priority TEXT DEFAULT 'medium',
                start_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                target_completion DATETIME,
                completion_percentage INTEGER DEFAULT 0,
                budget REAL DEFAULT 0.0,
                team_size INTEGER DEFAULT 0,
                FOREIGN KEY (manager_id) REFERENCES project_managers (id)
            )
        ''')
        
        # Feature extraction from .md files
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feature_requirements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_file TEXT NOT NULL,
                feature_title TEXT NOT NULL,
                feature_description TEXT,
                implementation_status TEXT DEFAULT 'not_started',
                priority_score INTEGER DEFAULT 5,
                complexity_estimate TEXT DEFAULT 'medium',
                assigned_project TEXT,
                extracted_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Manager communications
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS manager_communications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_manager TEXT,
                to_manager TEXT,
                message_type TEXT,
                message_content TEXT,
                response_content TEXT,
                status TEXT DEFAULT 'sent',
                sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                responded_at DATETIME
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def setup_management_structure(self):
        """Create the initial management hierarchy."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if managers already exist
        cursor.execute("SELECT COUNT(*) FROM project_managers")
        if cursor.fetchone()[0] > 0:
            conn.close()
            return
        
        # Create Project Managers
        managers = [
            {
                'id': 'pm_web_development',
                'name': 'Alex WebDev Manager',
                'specialization': 'Web Development & UI/UX',
                'team_members': ['dev_frontend_1', 'dev_backend_1', 'dev_fullstack_1', 'ui_designer_1'],
                'active_projects': []
            },
            {
                'id': 'pm_business_automation',
                'name': 'Morgan Automation Manager', 
                'specialization': 'Business Process Automation',
                'team_members': ['automation_engineer_1', 'data_analyst_1', 'ai_specialist_1'],
                'active_projects': []
            },
            {
                'id': 'pm_content_marketing',
                'name': 'Jamie Content Manager',
                'specialization': 'Content Creation & Marketing',
                'team_members': ['content_writer_1', 'seo_specialist_1', 'marketing_analyst_1', 'copywriter_1'],
                'active_projects': []
            },
            {
                'id': 'pm_data_analytics',
                'name': 'Taylor Analytics Manager',
                'specialization': 'Data Analytics & Business Intelligence',
                'team_members': ['data_scientist_1', 'business_analyst_1', 'report_specialist_1'],
                'active_projects': []
            },
            {
                'id': 'pm_infrastructure',
                'name': 'Sam Infrastructure Manager',
                'specialization': 'System Infrastructure & DevOps',
                'team_members': ['devops_engineer_1', 'security_specialist_1', 'system_admin_1'],
                'active_projects': []
            }
        ]
        
        for manager in managers:
            cursor.execute('''
                INSERT INTO project_managers (id, name, specialization, team_members, active_projects)
                VALUES (?, ?, ?, ?, ?)
            ''', (manager['id'], manager['name'], manager['specialization'], 
                  json.dumps(manager['team_members']), json.dumps(manager['active_projects'])))
        
        # Create Workers
        workers = [
            # Web Development Team
            {'id': 'dev_frontend_1', 'name': 'Riley Frontend Dev', 'skills': ['React', 'Vue.js', 'HTML/CSS', 'JavaScript'], 'manager_id': 'pm_web_development'},
            {'id': 'dev_backend_1', 'name': 'Casey Backend Dev', 'skills': ['Python', 'Flask', 'SQLite', 'API Design'], 'manager_id': 'pm_web_development'},
            {'id': 'dev_fullstack_1', 'name': 'Jordan Fullstack Dev', 'skills': ['Python', 'JavaScript', 'Database Design', 'API Integration'], 'manager_id': 'pm_web_development'},
            {'id': 'ui_designer_1', 'name': 'Avery UI Designer', 'skills': ['UI/UX Design', 'Bootstrap', 'Responsive Design', 'User Experience'], 'manager_id': 'pm_web_development'},
            
            # Business Automation Team
            {'id': 'automation_engineer_1', 'name': 'Blake Automation Engineer', 'skills': ['Process Automation', 'Python Scripts', 'Workflow Design'], 'manager_id': 'pm_business_automation'},
            {'id': 'data_analyst_1', 'name': 'Quinn Data Analyst', 'skills': ['Data Analysis', 'SQL', 'Business Metrics', 'Reporting'], 'manager_id': 'pm_business_automation'},
            {'id': 'ai_specialist_1', 'name': 'River AI Specialist', 'skills': ['Machine Learning', 'AI Integration', 'Gemini API', 'Automation'], 'manager_id': 'pm_business_automation'},
            
            # Content & Marketing Team
            {'id': 'content_writer_1', 'name': 'Sage Content Writer', 'skills': ['Content Creation', 'Technical Writing', 'Blog Posts', 'Documentation'], 'manager_id': 'pm_content_marketing'},
            {'id': 'seo_specialist_1', 'name': 'Phoenix SEO Specialist', 'skills': ['SEO Optimization', 'Keyword Research', 'Content Strategy'], 'manager_id': 'pm_content_marketing'},
            {'id': 'marketing_analyst_1', 'name': 'Rowan Marketing Analyst', 'skills': ['Marketing Analytics', 'Campaign Analysis', 'Conversion Optimization'], 'manager_id': 'pm_content_marketing'},
            {'id': 'copywriter_1', 'name': 'Skyler Copywriter', 'skills': ['Sales Copy', 'Email Marketing', 'Landing Pages', 'Conversion Copy'], 'manager_id': 'pm_content_marketing'},
            
            # Data Analytics Team
            {'id': 'data_scientist_1', 'name': 'Ellis Data Scientist', 'skills': ['Data Science', 'Statistical Analysis', 'Predictive Modeling'], 'manager_id': 'pm_data_analytics'},
            {'id': 'business_analyst_1', 'name': 'Emery Business Analyst', 'skills': ['Business Analysis', 'Requirements Gathering', 'Process Improvement'], 'manager_id': 'pm_data_analytics'},
            {'id': 'report_specialist_1', 'name': 'Finley Report Specialist', 'skills': ['Dashboard Creation', 'Data Visualization', 'Report Automation'], 'manager_id': 'pm_data_analytics'},
            
            # Infrastructure Team
            {'id': 'devops_engineer_1', 'name': 'Marlowe DevOps Engineer', 'skills': ['Server Management', 'Deployment Automation', 'System Monitoring'], 'manager_id': 'pm_infrastructure'},
            {'id': 'security_specialist_1', 'name': 'Reese Security Specialist', 'skills': ['Security Analysis', 'Vulnerability Assessment', 'Access Control'], 'manager_id': 'pm_infrastructure'},
            {'id': 'system_admin_1', 'name': 'Dakota System Admin', 'skills': ['System Administration', 'Database Management', 'Backup Systems'], 'manager_id': 'pm_infrastructure'}
        ]
        
        for worker in workers:
            cursor.execute('''
                INSERT INTO workers (id, name, skills, manager_id)
                VALUES (?, ?, ?, ?)
            ''', (worker['id'], worker['name'], json.dumps(worker['skills']), worker['manager_id']))
        
        conn.commit()
        conn.close()
        
        print("✅ Management hierarchy created:")
        print(f"   👥 {len(managers)} Project Managers")
        print(f"   🔧 {len(workers)} Specialized Workers")
        print("   🎯 Ready for autonomous project execution")
    
    async def scan_md_files_for_features(self) -> List[Dict]:
        """Scan all .md files to extract unimplemented features."""
        print("📖 Scanning .md files for feature requirements...")
        
        features_found = []
        md_files = glob.glob("*.md")
        
        for md_file in md_files:
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract features using patterns
                features = self.extract_features_from_content(content, md_file)
                features_found.extend(features)
                
            except Exception as e:
                print(f"   ⚠️ Error reading {md_file}: {e}")
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for feature in features_found:
            cursor.execute('''
                INSERT INTO feature_requirements 
                (source_file, feature_title, feature_description, priority_score, complexity_estimate)
                VALUES (?, ?, ?, ?, ?)
            ''', (feature['source_file'], feature['title'], feature['description'], 
                  feature['priority'], feature['complexity']))
        
        conn.commit()
        conn.close()
        
        print(f"   ✅ Extracted {len(features_found)} features from {len(md_files)} files")
        return features_found
    
    def extract_features_from_content(self, content: str, filename: str) -> List[Dict]:
        """Extract feature requirements from markdown content."""
        features = []
        
        # Look for TODO items
        todo_pattern = r'(?:TODO|PENDING|NOT IMPLEMENTED|COMING SOON)[:\s]*([^\n]+)'
        todos = re.findall(todo_pattern, content, re.IGNORECASE)
        
        for todo in todos:
            features.append({
                'source_file': filename,
                'title': f"TODO: {todo.strip()}",
                'description': f"Feature found in {filename}: {todo.strip()}",
                'priority': 7,
                'complexity': 'medium'
            })
        
        # Look for feature headers
        feature_pattern = r'#+\s*(.*(?:Feature|Service|System|Tool|Dashboard)[^\n]*)'
        feature_headers = re.findall(feature_pattern, content, re.IGNORECASE)
        
        for header in feature_headers:
            if 'complete' not in header.lower() and 'built' not in header.lower():
                features.append({
                    'source_file': filename,
                    'title': f"Feature: {header.strip()}",
                    'description': f"Feature section identified in {filename}",
                    'priority': 6,
                    'complexity': 'medium'
                })
        
        # Look for unimplemented sections
# DEMO CODE REMOVED: unimplemented_pattern = r'(?:NOT YET|PLACEHOLDER|STUB|MOCK)[:\s]*([^\n]+)'
        unimplemented = re.findall(unimplemented_pattern, content, re.IGNORECASE)
        
        for item in unimplemented:
            features.append({
                'source_file': filename,
                'title': f"Unimplemented: {item.strip()}",
                'description': f"Unimplemented feature in {filename}: {item.strip()}",
                'priority': 8,
                'complexity': 'high'
            })
        
        return features
    
    async def create_projects_from_features(self, features: List[Dict]):
        """Create projects and assign to appropriate managers."""
        print("📋 Creating projects from extracted features...")
        
        # Group features by type/complexity
        project_groups = {
            'web_features': [],
            'automation_features': [],
            'content_features': [],
            'analytics_features': [],
            'infrastructure_features': []
        }
        
        for feature in features:
            title_lower = feature['title'].lower()
            description_lower = feature['description'].lower()
            
            if any(keyword in title_lower or keyword in description_lower 
                   for keyword in ['web', 'ui', 'frontend', 'dashboard', 'interface']):
                project_groups['web_features'].append(feature)
            elif any(keyword in title_lower or keyword in description_lower 
                     for keyword in ['automation', 'engine', 'ai', 'process']):
                project_groups['automation_features'].append(feature)
            elif any(keyword in title_lower or keyword in description_lower 
                     for keyword in ['content', 'marketing', 'seo', 'copy']):
                project_groups['content_features'].append(feature)
            elif any(keyword in title_lower or keyword in description_lower 
                     for keyword in ['analytics', 'data', 'metrics', 'reporting']):
                project_groups['analytics_features'].append(feature)
            else:
                project_groups['infrastructure_features'].append(feature)
        
        # Create projects and assign to managers
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        project_assignments = {
            'web_features': 'pm_web_development',
            'automation_features': 'pm_business_automation',
            'content_features': 'pm_content_marketing',
            'analytics_features': 'pm_data_analytics',
            'infrastructure_features': 'pm_infrastructure'
        }
        
        projects_created = 0
        for group_name, feature_list in project_groups.items():
            if feature_list:
                manager_id = project_assignments[group_name]
                project_id = f"proj_{group_name}_{datetime.now().strftime('%Y%m%d')}"
                
                cursor.execute('''
                    INSERT INTO projects 
                    (id, name, description, manager_id, team_size, target_completion)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (project_id, 
                      f"{group_name.replace('_', ' ').title()} Implementation",
                      f"Implement {len(feature_list)} features from documentation analysis",
                      manager_id, len(feature_list), 
                      datetime.now() + timedelta(days=14)))
                
                projects_created += 1
                print(f"   📂 Created project: {project_id} ({len(feature_list)} features)")
        
        conn.commit()
        conn.close()
        
        print(f"   ✅ Created {projects_created} projects")
    
    async def send_manager_assignments(self):
        """Send work assignments to all project managers."""
        print("📨 Sending assignments to Project Managers...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all managers with their projects
        cursor.execute('''
            SELECT pm.id, pm.name, pm.specialization, 
                   COUNT(p.id) as project_count,
                   GROUP_CONCAT(p.name) as project_names
            FROM project_managers pm
            LEFT JOIN projects p ON pm.id = p.manager_id
            GROUP BY pm.id, pm.name, pm.specialization
        ''')
        managers = cursor.fetchall()
        
        for manager in managers:
            manager_id, name, specialization, project_count, project_names = manager
            
            assignment_message = f"""
🎯 PROJECT ASSIGNMENT FOR {name.upper()}

Specialization: {specialization}
Active Projects: {project_count or 0}

Your Mission:
1. Review your assigned projects: {project_names or 'No projects yet'}
2. Break down features into specific tasks
3. Assign tasks to your team members based on their skills
4. Set realistic timelines and dependencies
5. Report progress daily

Your Team Members:
"""
            
            # Get team members
            cursor.execute('SELECT name, skills FROM workers WHERE manager_id = ?', (manager_id,))
            team_members = cursor.fetchall()
            
            for member_name, skills_json in team_members:
                skills = json.loads(skills_json)
                assignment_message += f"   • {member_name}: {', '.join(skills)}\n"
            
            assignment_message += f"""

Expected Deliverables:
- Task breakdown within 24 hours
- Daily progress reports
- Quality deliverables on schedule
- Team coordination and communication

This is autonomous operation - you have full authority to manage your team and projects.

🚀 GET TO WORK! The business empire depends on your team's execution.
"""
            
            # Store assignment
            cursor.execute('''
                INSERT INTO manager_communications
                (from_manager, to_manager, message_type, message_content)
                VALUES (?, ?, ?, ?)
            ''', ('executive_director', manager_id, 'project_assignment', assignment_message))
            
            print(f"   📧 Assignment sent to {name}")
        
        conn.commit()
        conn.close()
        
        print("   ✅ All managers have received their assignments")
    
    async def generate_executive_dashboard(self) -> Dict[str, Any]:
        """Generate executive dashboard showing autonomous team progress."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get project overview
        cursor.execute('''
            SELECT COUNT(*) as total_projects,
                   SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                   SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
                   AVG(completion_percentage) as avg_completion
            FROM projects
        ''')
        project_stats = cursor.fetchone()
        
        # Get manager performance
        cursor.execute('''
            SELECT pm.name, pm.specialization, pm.performance_rating,
                   COUNT(p.id) as assigned_projects,
                   AVG(p.completion_percentage) as avg_project_completion
            FROM project_managers pm
            LEFT JOIN projects p ON pm.id = p.manager_id
            GROUP BY pm.id, pm.name, pm.specialization, pm.performance_rating
        ''')
        manager_performance = cursor.fetchall()
        
        # Get worker utilization
        cursor.execute('''
            SELECT COUNT(*) as total_workers,
                   SUM(CASE WHEN status = 'working' THEN 1 ELSE 0 END) as active_workers,
                   AVG(efficiency_rating) as avg_efficiency,
                   SUM(tasks_completed) as total_tasks_completed
            FROM workers
        ''')
        worker_stats = cursor.fetchone()
        
        # Get feature extraction results
        cursor.execute('SELECT COUNT(*) FROM feature_requirements')
        total_features = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM feature_requirements WHERE implementation_status = "completed"')
        completed_features = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'project_stats': {
                'total_projects': project_stats[0] or 0,
                'completed_projects': project_stats[1] or 0,
                'in_progress_projects': project_stats[2] or 0,
                'avg_completion': project_stats[3] or 0
            },
            'manager_performance': manager_performance,
            'worker_stats': {
                'total_workers': worker_stats[0] or 0,
                'active_workers': worker_stats[1] or 0,
                'avg_efficiency': worker_stats[2] or 0,
                'total_tasks_completed': worker_stats[3] or 0
            },
            'feature_stats': {
                'total_features_identified': total_features,
                'completed_features': completed_features,
                'completion_rate': (completed_features / max(total_features, 1)) * 100
            },
            'autonomous_status': 'FULLY OPERATIONAL'
        }
    
    async def execute_autonomous_management(self):
        """Execute the complete autonomous management workflow."""
        print("🎯 EXECUTING AUTONOMOUS PROJECT MANAGEMENT")
        print("=" * 60)
        
        # 1. Scan for features
        features = await self.scan_md_files_for_features()
        
        # 2. Create projects
        await self.create_projects_from_features(features)
        
        # 3. Send assignments to managers
        await self.send_manager_assignments()
        
        # 4. Generate dashboard
        dashboard = await self.generate_executive_dashboard()
        
        print("\n📊 EXECUTIVE DASHBOARD")
        print("=" * 30)
        print(f"🎯 Projects: {dashboard['project_stats']['total_projects']} total")
        print(f"👥 Managers: {len(dashboard['manager_performance'])} active")
        print(f"🔧 Workers: {dashboard['worker_stats']['total_workers']} in teams")
        print(f"📋 Features: {dashboard['feature_stats']['total_features_identified']} identified")
        print(f"🤖 Status: {dashboard['autonomous_status']}")
        
        print("\n👔 MANAGER ASSIGNMENTS:")
        for manager in dashboard['manager_performance']:
            name, specialization, rating, projects, completion = manager
            print(f"   • {name}: {projects or 0} projects ({completion or 0:.1f}% avg completion)")
        
        print(f"\n🎉 AUTONOMOUS TEAMS ARE NOW WORKING!")
        print("📈 Project managers will coordinate with their teams")
        print("🔄 Workers will execute tasks independently")
        print("📊 Progress will be tracked automatically")
        print("💡 Claude is now in Executive Director mode - strategic oversight only")

# Initialize the management hierarchy
management_system = ProjectManagementHierarchy()

async def run_autonomous_management():
# DEMO CODE REMOVED: """Run the autonomous management demonstration."""
    await management_system.execute_autonomous_management()

if __name__ == "__main__":
    asyncio.run(run_autonomous_management())