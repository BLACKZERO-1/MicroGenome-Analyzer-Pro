"""
Database Schema for MicroGenome Analyzer
Defines all table structures using SQLite
"""

# Table Creation SQL Statements
SCHEMA = {
    
    # =========================================================================
    # PROJECTS TABLE - Core genome file tracking
    # =========================================================================
    'projects': """
        CREATE TABLE IF NOT EXISTS projects (
            project_id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL UNIQUE,
            file_size INTEGER,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            genome_length INTEGER,
            gc_content REAL,
            num_contigs INTEGER,
            status TEXT DEFAULT 'pending',
            last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        )
    """,
    
    # =========================================================================
    # ANALYSES TABLE - Track each module run
    # =========================================================================
    'analyses': """
        CREATE TABLE IF NOT EXISTS analyses (
            analysis_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            module_name TEXT NOT NULL,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            processing_time_seconds REAL,
            status TEXT DEFAULT 'running',
            error_message TEXT,
            FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
        )
    """,
    
    # =========================================================================
    # ANNOTATION_RESULTS TABLE - Gene prediction & annotation data
    # =========================================================================
    'annotation_results': """
        CREATE TABLE IF NOT EXISTS annotation_results (
            result_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL UNIQUE,
            genes_detected INTEGER DEFAULT 0,
            proteins_annotated INTEGER DEFAULT 0,
            functional_domains INTEGER DEFAULT 0,
            special_genes_count INTEGER DEFAULT 0,
            trna_count INTEGER DEFAULT 0,
            rrna_count INTEGER DEFAULT 0,
            gff_file_path TEXT,
            genbank_file_path TEXT,
            circular_plot_path TEXT,
            faa_file_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
        )
    """,
    
    # =========================================================================
    # AMR_RESULTS TABLE - Antimicrobial resistance screening
    # =========================================================================
    'amr_results': """
        CREATE TABLE IF NOT EXISTS amr_results (
            result_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL UNIQUE,
            total_amr_genes INTEGER DEFAULT 0,
            critical_threats INTEGER DEFAULT 0,
            resistance_classes TEXT,
            detected_genes TEXT,
            blast_output_path TEXT,
            report_file_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
        )
    """,
    
    # =========================================================================
    # VIRULENCE_RESULTS TABLE - Pathogenicity factors
    # =========================================================================
    'virulence_results': """
        CREATE TABLE IF NOT EXISTS virulence_results (
            result_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL UNIQUE,
            virulence_factors_found INTEGER DEFAULT 0,
            toxin_genes INTEGER DEFAULT 0,
            adhesion_genes INTEGER DEFAULT 0,
            pathogenicity_score REAL DEFAULT 0.0,
            vfdb_hits_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
        )
    """,
    
    # =========================================================================
    # PHYLOGENETICS_RESULTS TABLE - Tree building data
    # =========================================================================
    'phylogenetics_results': """
        CREATE TABLE IF NOT EXISTS phylogenetics_results (
            result_id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_id INTEGER NOT NULL UNIQUE,
            tree_file_path TEXT,
            alignment_file_path TEXT,
            tree_method TEXT,
            bootstrap_value INTEGER,
            num_sequences INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (analysis_id) REFERENCES analyses(analysis_id) ON DELETE CASCADE
        )
    """,
    
    # =========================================================================
    # COMPARATIVE_RESULTS TABLE - Pan-genome analysis
    # =========================================================================
    'comparative_results': """
        CREATE TABLE IF NOT EXISTS comparative_results (
            result_id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_id INTEGER NOT NULL UNIQUE,
            num_genomes INTEGER,
            core_genes INTEGER,
            accessory_genes INTEGER,
            unique_genes INTEGER,
            pangenome_size INTEGER,
            results_dir TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (analysis_id) REFERENCES analyses(analysis_id) ON DELETE CASCADE
        )
    """,
    
    # =========================================================================
    # PATHWAY_RESULTS TABLE - Metabolic pathway mapping
    # =========================================================================
    'pathway_results': """
        CREATE TABLE IF NOT EXISTS pathway_results (
            result_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL UNIQUE,
            pathways_mapped INTEGER DEFAULT 0,
            complete_pathways INTEGER DEFAULT 0,
            kegg_annotations TEXT,
            pathway_map_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
        )
    """,
    
    # =========================================================================
    # SYSTEM_LOGS TABLE - Application event logging
    # =========================================================================
    'system_logs': """
        CREATE TABLE IF NOT EXISTS system_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            log_level TEXT NOT NULL,
            module TEXT,
            message TEXT NOT NULL,
            project_id INTEGER,
            FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE SET NULL
        )
    """,
    
    # =========================================================================
    # NOTIFICATIONS TABLE - User alerts and messages
    # =========================================================================
    'notifications': """
        CREATE TABLE IF NOT EXISTS notifications (
            notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            type TEXT NOT NULL,
            priority TEXT DEFAULT 'normal',
            message TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            related_project_id INTEGER,
            action_url TEXT,
            FOREIGN KEY (related_project_id) REFERENCES projects(project_id) ON DELETE SET NULL
        )
    """,
    
    # =========================================================================
    # USER_SETTINGS TABLE - Application preferences
    # =========================================================================
    'user_settings': """
        CREATE TABLE IF NOT EXISTS user_settings (
            setting_id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT NOT NULL UNIQUE,
            value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
}

# =========================================================================
# INDEXES for Performance Optimization
# =========================================================================
INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status)",
    "CREATE INDEX IF NOT EXISTS idx_projects_upload_date ON projects(upload_date DESC)",
    "CREATE INDEX IF NOT EXISTS idx_analyses_project ON analyses(project_id)",
    "CREATE INDEX IF NOT EXISTS idx_analyses_module ON analyses(module_name)",
    "CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(is_read)",
    "CREATE INDEX IF NOT EXISTS idx_notifications_timestamp ON notifications(timestamp DESC)",
    "CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON system_logs(timestamp DESC)",
    "CREATE INDEX IF NOT EXISTS idx_logs_level ON system_logs(log_level)"
]

# =========================================================================
# DEFAULT SETTINGS
# =========================================================================
DEFAULT_SETTINGS = {
    'theme': 'light',
    'auto_refresh': 'true',
    'notification_sound': 'true',
    'max_recent_projects': '10',
    'auto_backup': 'false',
    'blast_evalue': '1e-5',
    'prodigal_mode': 'single',
    'default_output_format': 'genbank'
}