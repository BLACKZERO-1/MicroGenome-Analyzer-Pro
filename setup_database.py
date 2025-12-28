"""
Database Setup and Test Script
Run this once to initialize the database and add sample data
"""

import os
from datetime import datetime, timedelta
import random
from database_manager import DatabaseManager


def initialize_database(db_path: str = "microgenome.db"):
    """Create fresh database with schema"""
    
    # Remove old database if exists
    if os.path.exists(db_path):
        print(f"⚠️  Removing existing database: {db_path}")
        os.remove(db_path)
    
    print("🔧 Creating new database...")
    db = DatabaseManager(db_path)
    print("✅ Database schema created successfully!")
    
    return db


def add_sample_data(db: DatabaseManager, num_projects: int = 15):
    """Populate database with realistic sample data for testing"""
    
    print(f"\n📊 Adding {num_projects} sample projects...")
    
    # Sample genome files
    sample_genomes = [
        ("E_coli_K12.fasta", "annotation", 4641652, 50.8),
        ("Salmonella_enterica.fna", "annotation", 4809037, 52.1),
        ("Pseudomonas_aeruginosa.fa", "amr", 6264404, 66.3),
        ("Staphylococcus_aureus.fasta", "amr", 2821361, 32.8),
        ("Bacillus_subtilis.fna", "phylogenetics", 4215606, 43.5),
        ("Listeria_monocytogenes.fa", "virulence", 2944528, 38.0),
        ("Mycobacterium_tuberculosis.fasta", "annotation", 4411532, 65.6),
        ("Klebsiella_pneumoniae.fna", "amr", 5333942, 57.5),
        ("Vibrio_cholerae.fa", "phylogenetics", 4033464, 47.5),
        ("Yersinia_pestis.fasta", "virulence", 4653728, 47.6),
        ("Campylobacter_jejuni.fna", "comparative", 1641481, 30.6),
        ("Helicobacter_pylori.fa", "annotation", 1667867, 38.9),
        ("Neisseria_meningitidis.fasta", "pathways", 2272351, 51.5),
        ("Streptococcus_pneumoniae.fna", "amr", 2038615, 39.7),
        ("Acinetobacter_baumannii.fa", "amr", 3976747, 39.0)
    ]
    
    project_ids = []
    base_date = datetime.now() - timedelta(days=30)
    
    for i, (filename, module, genome_len, gc) in enumerate(sample_genomes[:num_projects]):
        # Create project
        file_path = f"E:\\MicroGenome_Analyzer\\test_data\\{filename}"
        file_size = genome_len + random.randint(-100000, 100000)
        
        project_id = db.create_project(filename, file_path, file_size)
        project_ids.append(project_id)
        
        # Update project stats
        db.connection.execute("""
            UPDATE projects 
            SET genome_length = ?, gc_content = ?, 
                upload_date = ?, status = 'completed'
            WHERE project_id = ?
        """, (genome_len, gc, base_date + timedelta(days=i), project_id))
        
        # Create analysis record
        analysis_id = db.start_analysis(project_id, module)
        processing_time = random.uniform(120, 600)  # 2-10 minutes
        
        db.connection.execute("""
            UPDATE analyses 
            SET end_time = DATETIME(start_time, '+' || ? || ' seconds'),
                processing_time_seconds = ?,
                status = 'completed'
            WHERE analysis_id = ?
        """, (int(processing_time), processing_time, analysis_id))
        
        # Add module-specific results
        if module == "annotation":
            genes = random.randint(3500, 5000)
            annotated = int(genes * random.uniform(0.7, 0.95))
            domains = int(annotated * random.uniform(0.6, 0.8))
            rna = random.randint(50, 120)
            
            db.save_annotation_results(project_id, {
                'genes': genes,
                'annotated': annotated,
                'domains': domains,
                'rna': rna,
                'trna': random.randint(40, 80),
                'rrna': random.randint(10, 40),
                'gc': gc,
                'genome_length': genome_len,
                'gff_path': f"results/annotation/{filename}.gff",
                'gbk_path': f"results/annotation/{filename}.gbk"
            })
            
        elif module == "amr":
            total_genes = random.randint(0, 15)
            critical = random.randint(0, min(5, total_genes))
            
            resistance_classes = []
            if total_genes > 0:
                classes = ["Beta-lactam", "Aminoglycoside", "Fluoroquinolone", 
                          "Tetracycline", "Macrolide"]
                resistance_classes = random.sample(classes, min(total_genes, 3))
            
            db.save_amr_results(project_id, {
                'total_genes': total_genes,
                'critical': critical,
                'classes': resistance_classes,
                'genes': [f"gene_{j+1}" for j in range(total_genes)],
                'blast_path': f"amr_results/{filename}_blast.txt"
            })
            
        elif module == "virulence":
            vf_count = random.randint(0, 20)
            toxins = random.randint(0, min(5, vf_count))
            adhesion = random.randint(0, min(8, vf_count))
            
            db.connection.execute("""
                INSERT INTO virulence_results 
                (project_id, virulence_factors_found, toxin_genes, 
                 adhesion_genes, pathogenicity_score)
                VALUES (?, ?, ?, ?, ?)
            """, (project_id, vf_count, toxins, adhesion, 
                  random.uniform(0.3, 0.9)))
    
    db.connection.commit()
    
    # Add some notifications
    print("🔔 Adding sample notifications...")
    db.add_notification('success', f"Analysis completed: {sample_genomes[0][0]}", 
                       project_ids[0], 'normal')
    db.add_notification('warning', f"Low quality sequence detected in {sample_genomes[1][0]}", 
                       project_ids[1], 'high')
    db.add_notification('info', "Database updated successfully", None, 'normal')
    db.add_notification('error', "BLAST search failed - check database path", 
                       project_ids[2], 'high')
    db.add_notification('success', "Phylogenetic tree generated", 
                       project_ids[4], 'normal')
    
    # Add some system logs
    print("📝 Adding system logs...")
    db.log_event('INFO', 'system', 'Application started')
    db.log_event('INFO', 'annotation', 'Prodigal gene prediction completed', project_ids[0])
    db.log_event('WARNING', 'amr', 'High-risk resistance gene detected', project_ids[2])
    db.log_event('ERROR', 'phylogenetics', 'Alignment failed - check input format', project_ids[4])
    
    print(f"✅ Added {num_projects} sample projects with results!")


def test_queries(db: DatabaseManager):
    """Test database queries"""
    
    print("\n🧪 Testing Database Queries...")
    print("=" * 60)
    
    # Dashboard stats
    stats = db.get_dashboard_stats()
    print(f"\n📊 Dashboard Stats:")
    print(f"   Total Genomes: {stats['total_genomes']}")
    print(f"   Total Hours: {stats['total_hours']}h")
    print(f"   Critical Alerts: {stats['critical_alerts']}")
    print(f"   Storage Used: {stats['storage_gb']} GB")
    
    # Module usage
    module_stats = db.get_module_usage_stats()
    print(f"\n🔬 Module Usage:")
    for module, count in module_stats.items():
        print(f"   {module}: {count} analyses")
    
    # Recent projects
    recent = db.get_recent_projects(5)
    print(f"\n📋 Recent Projects:")
    for filename, module, status, date in recent:
        print(f"   {filename} | {module} | {status}")
    
    # Notifications
    notifications = db.get_unread_notifications(5)
    print(f"\n🔔 Unread Notifications: {len(notifications)}")
    for notif in notifications:
        print(f"   [{notif['type'].upper()}] {notif['message']}")
    
    # Recent activity
    activity = db.get_recent_activity(5)
    print(f"\n⏱️  Recent Activity:")
    for act in activity:
        print(f"   {act['filename']} - {act['module_name']} ({act['status']})")
    
    print("\n✅ All queries executed successfully!")


def main():
    """Main setup script"""
    
    print("=" * 60)
    print("  🧬 MicroGenome Analyzer - Database Setup")
    print("=" * 60)
    
    # Initialize database
    db = initialize_database()
    
    # Ask user if they want sample data
    print("\n❓ Do you want to add sample data for testing? (y/n): ", end="")
    choice = input().strip().lower()
    
    if choice == 'y':
        add_sample_data(db, num_projects=15)
        test_queries(db)
    else:
        print("✅ Empty database created. Ready for real data!")
    
    print("\n" + "=" * 60)
    print("  🎉 Database Setup Complete!")
    print("  📁 Location: microgenome.db")
    print("  🚀 You can now run the main application")
    print("=" * 60)
    
    db.close()


if __name__ == "__main__":
    main()