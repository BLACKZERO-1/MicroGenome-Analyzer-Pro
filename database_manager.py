"""
Database Manager for MicroGenome Analyzer
Handles all database operations with thread-safe connections
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import json

from models import SCHEMA, INDEXES, DEFAULT_SETTINGS


class DatabaseManager:
    def __init__(self, db_path: str = "microgenome.db"):
        """Initialize database connection"""
        self.db_path = db_path
        self.connection = None
        self._connect()
        self._initialize_schema()
    
    def _connect(self):
        """Establish database connection with thread safety"""
        self.connection = sqlite3.connect(
            self.db_path, 
            check_same_thread=False,
            isolation_level=None  # Autocommit mode
        )
        self.connection.row_factory = sqlite3.Row  # Access columns by name
        
    def _initialize_schema(self):
        """Create all tables if they don't exist"""
        cursor = self.connection.cursor()
        
        # Create tables
        for table_name, create_sql in SCHEMA.items():
            cursor.execute(create_sql)
        
        # Create indexes
        for index_sql in INDEXES:
            cursor.execute(index_sql)
        
        # Insert default settings if empty
        cursor.execute("SELECT COUNT(*) FROM user_settings")
        if cursor.fetchone()[0] == 0:
            for key, value in DEFAULT_SETTINGS.items():
                cursor.execute(
                    "INSERT INTO user_settings (key, value) VALUES (?, ?)",
                    (key, value)
                )
        
        self.connection.commit()
    
    # =========================================================================
    # PROJECT OPERATIONS
    # =========================================================================
    
    def create_project(self, filename: str, file_path: str, file_size: int = 0) -> int:
        """Create new project entry and return project_id"""
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT INTO projects (filename, file_path, file_size, status)
            VALUES (?, ?, ?, 'pending')
        """, (filename, file_path, file_size))
        self.connection.commit()
        
        project_id = cursor.lastrowid
        self.log_event('INFO', 'projects', f'New project created: {filename}', project_id)
        return project_id
    
    def update_project_status(self, project_id: int, status: str):
        """Update project status (pending/running/completed/failed)"""
        cursor = self.connection.cursor()
        cursor.execute("""
            UPDATE projects 
            SET status = ?, last_modified = CURRENT_TIMESTAMP 
            WHERE project_id = ?
        """, (status, project_id))
        self.connection.commit()
    
    def get_project_by_path(self, file_path: str) -> Optional[Dict]:
        """Get project by file path"""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM projects WHERE file_path = ?", (file_path,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_all_projects(self, limit: int = 100) -> List[Dict]:
        """Get all projects, most recent first"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT * FROM projects 
            ORDER BY upload_date DESC 
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_recent_projects(self, limit: int = 5) -> List[Tuple]:
        """Get recent projects for dashboard table"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT 
                p.filename,
                COALESCE(a.module_name, 'N/A') as module,
                p.status,
                p.upload_date
            FROM projects p
            LEFT JOIN analyses a ON p.project_id = a.project_id
            ORDER BY p.upload_date DESC
            LIMIT ?
        """, (limit,))
        return cursor.fetchall()
    
    def search_projects(self, query: str) -> List[Dict]:
        """Search projects by filename"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT * FROM projects 
            WHERE filename LIKE ? 
            ORDER BY upload_date DESC
        """, (f'%{query}%',))
        return [dict(row) for row in cursor.fetchall()]
    
    def delete_project(self, project_id: int):
        """Delete project (CASCADE deletes all related data)"""
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM projects WHERE project_id = ?", (project_id,))
        self.connection.commit()
        self.log_event('WARNING', 'projects', f'Project {project_id} deleted')
    
    # =========================================================================
    # ANALYSIS OPERATIONS
    # =========================================================================
    
    def start_analysis(self, project_id: int, module_name: str) -> int:
        """Log analysis start and return analysis_id"""
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT INTO analyses (project_id, module_name, start_time, status)
            VALUES (?, ?, CURRENT_TIMESTAMP, 'running')
        """, (project_id, module_name))
        self.connection.commit()
        
        analysis_id = cursor.lastrowid
        self.update_project_status(project_id, 'running')
        return analysis_id
    
    def complete_analysis(self, analysis_id: int, success: bool = True, error: str = None):
        """Mark analysis as completed or failed"""
        status = 'completed' if success else 'failed'
        cursor = self.connection.cursor()
        cursor.execute("""
            UPDATE analyses 
            SET end_time = CURRENT_TIMESTAMP,
                processing_time_seconds = 
                    (julianday(CURRENT_TIMESTAMP) - julianday(start_time)) * 86400,
                status = ?,
                error_message = ?
            WHERE analysis_id = ?
        """, (status, error, analysis_id))
        self.connection.commit()
        
        # Update project status
        cursor.execute("SELECT project_id FROM analyses WHERE analysis_id = ?", (analysis_id,))
        project_id = cursor.fetchone()[0]
        self.update_project_status(project_id, status)
    
    def get_analysis_stats(self) -> Dict:
        """Get overall analysis statistics"""
        cursor = self.connection.cursor()
        
        # Total analyses
        cursor.execute("SELECT COUNT(*) FROM analyses WHERE status = 'completed'")
        total = cursor.fetchone()[0]
        
        # Total time
        cursor.execute("SELECT SUM(processing_time_seconds) FROM analyses WHERE status = 'completed'")
        total_seconds = cursor.fetchone()[0] or 0
        total_hours = total_seconds / 3600
        
        # By module
        cursor.execute("""
            SELECT module_name, COUNT(*) as count 
            FROM analyses 
            WHERE status = 'completed'
            GROUP BY module_name
        """)
        by_module = {row[0]: row[1] for row in cursor.fetchall()}
        
        return {
            'total_analyses': total,
            'total_hours': round(total_hours, 1),
            'by_module': by_module
        }
    
    # =========================================================================
    # ANNOTATION RESULTS
    # =========================================================================
    
    def save_annotation_results(self, project_id: int, data: Dict):
        """Save annotation results"""
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO annotation_results 
            (project_id, genes_detected, proteins_annotated, functional_domains,
             special_genes_count, trna_count, rrna_count, gff_file_path, 
             genbank_file_path, circular_plot_path, faa_file_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            project_id,
            data.get('genes', 0),
            data.get('annotated', 0),
            data.get('domains', 0),
            data.get('rna', 0),
            data.get('trna', 0),
            data.get('rrna', 0),
            data.get('gff_path', ''),
            data.get('gbk_path', ''),
            data.get('plot_path', ''),
            data.get('faa_path', '')
        ))
        self.connection.commit()
        
        # Update project genome stats if available
        if 'gc' in data:
            cursor.execute("""
                UPDATE projects 
                SET gc_content = ?, genome_length = ?
                WHERE project_id = ?
            """, (data.get('gc', 0), data.get('genome_length', 0), project_id))
            self.connection.commit()
    
    def get_annotation_results(self, project_id: int) -> Optional[Dict]:
        """Get annotation results for a project"""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM annotation_results WHERE project_id = ?", (project_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    # =========================================================================
    # AMR RESULTS
    # =========================================================================
    
    def save_amr_results(self, project_id: int, data: Dict):
        """Save AMR screening results"""
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO amr_results
            (project_id, total_amr_genes, critical_threats, resistance_classes,
             detected_genes, blast_output_path, report_file_path)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            project_id,
            data.get('total_genes', 0),
            data.get('critical', 0),
            json.dumps(data.get('classes', [])),
            json.dumps(data.get('genes', [])),
            data.get('blast_path', ''),
            data.get('report_path', '')
        ))
        self.connection.commit()
        
        # Create notification if critical threats found
        if data.get('critical', 0) > 0:
            self.add_notification(
                'warning',
                f"Critical AMR threats detected: {data['critical']} genes",
                project_id,
                priority='high'
            )
    
    def get_amr_results(self, project_id: int) -> Optional[Dict]:
        """Get AMR results for a project"""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM amr_results WHERE project_id = ?", (project_id,))
        row = cursor.fetchone()
        if row:
            result = dict(row)
            result['resistance_classes'] = json.loads(result.get('resistance_classes', '[]'))
            result['detected_genes'] = json.loads(result.get('detected_genes', '[]'))
            return result
        return None
    
    # =========================================================================
    # DASHBOARD METRICS
    # =========================================================================
    
    def get_dashboard_stats(self) -> Dict:
        """Get all statistics for dashboard"""
        cursor = self.connection.cursor()
        
        # Total genomes processed
        cursor.execute("SELECT COUNT(*) FROM projects WHERE status = 'completed'")
        total_genomes = cursor.fetchone()[0]
        
        # Total analysis hours
        cursor.execute("""
            SELECT SUM(processing_time_seconds) / 3600.0 
            FROM analyses 
            WHERE status = 'completed'
        """)
        total_hours = cursor.fetchone()[0] or 0
        
        # Critical alerts (unread high priority notifications)
        cursor.execute("""
            SELECT COUNT(*) FROM notifications 
            WHERE is_read = 0 AND priority = 'high'
        """)
        critical_alerts = cursor.fetchone()[0]
        
        # Storage used (sum of all project file sizes)
        cursor.execute("SELECT SUM(file_size) FROM projects")
        storage_bytes = cursor.fetchone()[0] or 0
        storage_gb = storage_bytes / (1024**3)
        
        return {
            'total_genomes': total_genomes,
            'total_hours': round(total_hours, 1),
            'critical_alerts': critical_alerts,
            'storage_gb': round(storage_gb, 2)
        }
    
    def get_module_usage_stats(self) -> Dict[str, int]:
        """Get count of analyses per module"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT module_name, COUNT(*) as count
            FROM analyses
            WHERE status = 'completed'
            GROUP BY module_name
            ORDER BY count DESC
        """)
        return {row[0]: row[1] for row in cursor.fetchall()}
    
    def get_analysis_timeline(self, days: int = 30) -> List[Tuple]:
        """Get analyses per day for timeline chart"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT DATE(start_time) as date, COUNT(*) as count
            FROM analyses
            WHERE start_time >= DATE('now', ? || ' days')
            GROUP BY DATE(start_time)
            ORDER BY date
        """, (f'-{days}',))
        return cursor.fetchall()
    
    # =========================================================================
    # NOTIFICATIONS
    # =========================================================================
    
    def add_notification(self, type: str, message: str, project_id: int = None, 
                        priority: str = 'normal'):
        """Create a new notification"""
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT INTO notifications (type, message, related_project_id, priority)
            VALUES (?, ?, ?, ?)
        """, (type, message, project_id, priority))
        self.connection.commit()
    
    def get_unread_notifications(self, limit: int = 10) -> List[Dict]:
        """Get unread notifications"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT * FROM notifications 
            WHERE is_read = 0 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]
    
    def mark_notification_read(self, notification_id: int):
        """Mark notification as read"""
        cursor = self.connection.cursor()
        cursor.execute("""
            UPDATE notifications 
            SET is_read = 1 
            WHERE notification_id = ?
        """, (notification_id,))
        self.connection.commit()
    
    def get_recent_activity(self, limit: int = 10) -> List[Dict]:
        """Get recent activity feed for dashboard"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT 
                'analysis' as type,
                a.start_time as timestamp,
                p.filename,
                a.module_name,
                a.status
            FROM analyses a
            JOIN projects p ON a.project_id = p.project_id
            ORDER BY a.start_time DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]
    
    # =========================================================================
    # SYSTEM LOGS
    # =========================================================================
    
    def log_event(self, level: str, module: str, message: str, project_id: int = None):
        """Add system log entry"""
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT INTO system_logs (log_level, module, message, project_id)
            VALUES (?, ?, ?, ?)
        """, (level, module, message, project_id))
        self.connection.commit()
    
    def get_recent_logs(self, limit: int = 100) -> List[Dict]:
        """Get recent system logs"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT * FROM system_logs 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]
    
    # =========================================================================
    # USER SETTINGS
    # =========================================================================
    
    def get_setting(self, key: str) -> Optional[str]:
        """Get user setting value"""
        cursor = self.connection.cursor()
        cursor.execute("SELECT value FROM user_settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row else None
    
    def set_setting(self, key: str, value: str):
        """Set user setting value"""
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO user_settings (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (key, value))
        self.connection.commit()
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    def get_storage_breakdown(self) -> List[Tuple]:
        """Get top 10 largest projects by size"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT filename, file_size, upload_date
            FROM projects
            ORDER BY file_size DESC
            LIMIT 10
        """)
        return cursor.fetchall()
    
    def cleanup_old_projects(self, days: int = 90) -> int:
        """Delete projects older than specified days"""
        cursor = self.connection.cursor()
        cursor.execute("""
            DELETE FROM projects 
            WHERE upload_date < DATE('now', ? || ' days')
        """, (f'-{days}',))
        self.connection.commit()
        return cursor.rowcount
    
    def vacuum_database(self):
        """Optimize database and reclaim space"""
        self.connection.execute("VACUUM")
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
    
    def __del__(self):
        """Destructor to ensure connection is closed"""
        self.close()