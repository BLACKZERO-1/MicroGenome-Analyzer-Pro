import datetime
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QGridLayout, QPushButton, QTableWidget, 
    QTableWidgetItem, QHeaderView, QScrollArea, QLineEdit
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QIcon

class DashboardView(QWidget):
    def __init__(self, navigation_callback):
        super().__init__()
        self.nav_callback = navigation_callback
        
        # Scroll Layout
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setStyleSheet("background: #F4F7FE; border: none;")
        
        self.content = QWidget()
        self.content.setStyleSheet("background: #F4F7FE;")
        self.layout = QVBoxLayout(self.content)
        self.layout.setSpacing(30)
        self.layout.setContentsMargins(50, 40, 50, 40)
        self.scroll.setWidget(self.content)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.addWidget(self.scroll)

        # 1. HERO HEADER (Centered)
        self.create_hero_section()

        # 2. SEARCH BAR (Google Style)
        self.create_search_bar()

        # 3. WORKFLOW PHASES (The Grid)
        self.create_workflow_grid()

        # 4. LIVE MONITOR (Activity Log Only - Wide)
        self.create_live_monitor()

    def create_hero_section(self):
        # Container
        hero = QVBoxLayout()
        hero.setSpacing(10)
        hero.setAlignment(Qt.AlignCenter)
        
        # 1. Logo
        logo = QLabel("🧬")
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet("font-size: 60px; background: transparent;")
        hero.addWidget(logo)

        # 2. Title
        title = QLabel("MicroGenome Analyzer Pro")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 32px; font-weight: 900; color: #1B2559; letter-spacing: 1px;")
        hero.addWidget(title)

        # 3. Narrative Tagline
        desc = QLabel(
            "A comprehensive bioinformatics platform for genomic analysis, evolutionary biology, and synthetic engineering.\n"
            "Streamlining the workflow from raw sequence data to actionable molecular insights."
        )
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("font-size: 14px; color: #707EAE; font-weight: 500; font-family: 'Segoe UI';")
        hero.addWidget(desc)
        
        self.layout.addLayout(hero)

    def create_search_bar(self):
        # Container to center it
        container = QHBoxLayout()
        container.addStretch()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍  Search Modules, Jobs, or Tools... (e.g. 'CRISPR', 'BLAST')")
        self.search_input.setFixedSize(600, 50)
        self.search_input.returnPressed.connect(self.handle_search)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: white; border: 2px solid #E0E5F2; border-radius: 25px;
                padding-left: 20px; font-size: 14px; color: #2B3674; font-weight: bold;
            }
            QLineEdit:focus { border: 2px solid #4318FF; }
        """)
        
        container.addWidget(self.search_input)
        container.addStretch()
        
        self.layout.addLayout(container)

    def create_workflow_grid(self):
        grid = QGridLayout()
        grid.setSpacing(25)

        # --- PHASE 1: ESSENTIALS ---
        self.add_phase_card(grid, 0, 0, "PHASE 1: ESSENTIALS", "📥", "#E3F2FD", "#1565C0", [
            ("Data Manager", 10), 
            ("Reference Manager", 11), 
            ("Quality Control (QC)", 9) 
        ])

        # --- PHASE 2: GENOMICS ---
        # UPDATED: Genome Assembly -> 12, BLAST -> 13
        self.add_phase_card(grid, 0, 1, "PHASE 2: GENOMICS", "🧬", "#E8F5E9", "#2E7D32", [
            ("Genome Assembly", 12), ("Gene Annotation", 1), ("BLAST Alignment", 13), ("Variant Calling", 7)
        ])

        # --- PHASE 3: EVOLUTION ---
        self.add_phase_card(grid, 0, 2, "PHASE 3: EVOLUTION", "🌿", "#FFF3E0", "#EF6C00", [
            ("Comparative (Synteny)", 2), ("Phylogenetics", 3), ("Pangenome Analysis", -1)
        ])

        # --- PHASE 4: DIAGNOSTICS ---
        # UPDATED: RNA-Seq -> 14
        self.add_phase_card(grid, 1, 0, "PHASE 4: DIAGNOSTICS", "💊", "#FFEBEE", "#C62828", [
            ("AMR & Virulence", 4), ("AI Pathogen Classifier", -1), ("RNA-Seq Analysis", 14)
        ])

        # --- PHASE 5: PHARMA ---
        self.add_phase_card(grid, 1, 1, "PHASE 5: PHARMA", "🧊", "#F3E5F5", "#6A1B9A", [
            ("3D Proteomics", 5), ("Molecular Docking", -1)
        ])

        # --- PHASE 6: ENGINEERING ---
        self.add_phase_card(grid, 1, 2, "PHASE 6: ENGINEERING", "⚙️", "#E0F7FA", "#006064", [
            ("Cloning Workbench", 6), ("CRISPR Design", 6), ("Codon Optimization", -1)
        ])

        self.layout.addLayout(grid)

    def add_phase_card(self, grid, row, col, title, icon, bg_color, accent_color, modules):
        card = QFrame()
        card.setFixedHeight(220)
        card.setStyleSheet(f"""
            QFrame {{ 
                background-color: white; border-radius: 16px; border: 1px solid #E0E5F2;
                border-top: 4px solid {accent_color};
            }}
            QFrame:hover {{ border: 2px solid {accent_color}; transform: scale(1.02); }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 15, 20, 15)
        
        # Header
        head = QHBoxLayout()
        ico = QLabel(icon)
        ico.setStyleSheet("font-size: 28px; border: none; background: transparent;")
        lbl = QLabel(title)
        lbl.setStyleSheet(f"font-size: 13px; font-weight: 900; color: {accent_color}; border: none; letter-spacing: 0.5px;")
        head.addWidget(ico); head.addWidget(lbl); head.addStretch()
        layout.addLayout(head)
        
        # Buttons
        layout.addSpacing(10)
        for name, index in modules:
            btn = QPushButton(f"•  {name}")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    text-align: left; padding: 6px; border-radius: 6px; border: none;
                    color: #707EAE; font-weight: 500; font-size: 13px; background: transparent;
                }}
                QPushButton:hover {{ background-color: {bg_color}; color: {accent_color}; font-weight: bold; }}
            """)
            btn.clicked.connect(lambda ch, idx=index, nm=name: self.nav_callback(idx, nm))
            layout.addWidget(btn)
        
        layout.addStretch()
        grid.addWidget(card, row, col)

    def create_live_monitor(self):
        # Full width container for the log
        log_card = QFrame()
        log_card.setStyleSheet("background: white; border-radius: 16px; border: 1px solid #E0E5F2;")
        lc_layout = QVBoxLayout(log_card)
        lc_layout.setContentsMargins(20, 20, 20, 20)
        
        lc_header = QHBoxLayout()
        lc_header.addWidget(QLabel("📝 Real-Time Activity Log", styleSheet="font-size: 16px; font-weight: bold; color: #1B2559; border:none;"))
        lc_header.addStretch()
        lc_layout.addLayout(lc_header)
        
        self.log_table = QTableWidget(0, 3)
        self.log_table.setHorizontalHeaderLabels(["Timestamp", "Action", "Status"])
        self.log_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.log_table.horizontalHeader().setStyleSheet("border-bottom: 2px solid #F4F7FE;")
        self.log_table.verticalHeader().setVisible(False)
        self.log_table.setShowGrid(False)
        self.log_table.setFrameShape(QFrame.NoFrame)
        self.log_table.setSelectionMode(QTableWidget.NoSelection) # Disable clicking selection
        
        # Expanded Height & No Hover
        self.log_table.setMinimumHeight(300) 
        self.log_table.setStyleSheet("""
            QTableWidget { 
                border: none; 
                background-color: white; 
                color: #2B3674; 
                font-size: 13px;
            }
            QTableWidget::item { 
                padding: 10px; 
                border-bottom: 1px solid #F4F7FE; 
            }
            /* Explicitly set hover to remain white */
            QTableWidget::item:hover { 
                background-color: white; 
                color: #2B3674; 
            }
        """)
        lc_layout.addWidget(self.log_table)
        
        # Add a dummy start entry
        self.add_log_entry("System", "Dashboard Loaded", "Ready")
        
        self.layout.addWidget(log_card)

    def handle_search(self):
        query = self.search_input.text().lower().strip()
        if not query: return
        
        # Updated Mapping with new modules
        mapping = {
            "blast": (13, "BLAST Alignment"),  # Updated
            "alignment": (13, "BLAST Alignment"),
            "assembly": (12, "Genome Assembly"), # Updated
            "rna": (14, "RNA-Seq Analysis"), # Updated
            "expression": (14, "RNA-Seq Analysis"),
            "transcript": (14, "RNA-Seq Analysis"),
            "annotation": (1, "Gene Annotation"),
            "gene": (1, "Gene Annotation"),
            "synteny": (2, "Comparative (Synteny)"),
            "phylo": (3, "Phylogenetics"),
            "tree": (3, "Phylogenetics"),
            "amr": (4, "AMR & Virulence"),
            "structure": (5, "3D Proteomics"),
            "protein": (5, "3D Proteomics"),
            "crispr": (6, "CRISPR Design"),
            "cloning": (6, "Cloning Workbench"),
            "variant": (7, "Variant Calling"),
            "qc": (9, "Quality Control (QC)"),
            "quality": (9, "Quality Control (QC)"),
            "data": (10, "Data Manager"),
            "import": (10, "Data Manager"),
            "reference": (11, "Reference Manager"),
            "genome": (11, "Reference Manager"),
            "ncbi": (11, "Reference Manager")
        }
        
        found = False
        for key, (idx, name) in mapping.items():
            if key in query:
                self.nav_callback(idx if idx is not None else -1, name)
                self.search_input.clear()
                found = True
                return
        
        if not found:
            self.search_input.setText("❌ Module not found. Try 'CRISPR' or 'BLAST'...")

    def add_log_entry(self, module, action, status):
        row = self.log_table.rowCount()
        self.log_table.insertRow(row)
        time_str = datetime.datetime.now().strftime("%H:%M:%S")
        
        self.log_table.setItem(row, 0, QTableWidgetItem(time_str))
        self.log_table.setItem(row, 1, QTableWidgetItem(f"{module}: {action}"))
        
        stat_item = QTableWidgetItem(status)
        stat_item.setFont(self.font()) # Default font
        
        if status == "Ready" or status == "Completed": 
            stat_item.setForeground(QColor("#05CD99"))
            stat_item.setText("● " + status)
        elif status == "Processing" or status == "Started": 
            stat_item.setForeground(QColor("#FFB547"))
            stat_item.setText("● " + status)
        else: 
            stat_item.setForeground(QColor("#E31A1A"))
            stat_item.setText("● " + status)
        
        self.log_table.setItem(row, 2, stat_item)
        self.log_table.scrollToBottom()