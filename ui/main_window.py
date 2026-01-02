from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QStackedWidget, QFrame, 
    QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

# Import Views (Existing)
from ui.dashboard_view import DashboardView
from ui.footer_widget import FooterWidget
from ui.annotation_view import AnnotationView
from ui.comparative_view import ComparativeView
from ui.phylo_view import PhyloView
from ui.specialized_view import SpecializedView
from ui.structure_view import StructureView
from ui.synbio_view import SynBioView
from ui.variant_view import VariantView
from ui.report_view import ReportView
from ui.qc_view import QCView
from ui.data_view import DataManagerView
from ui.reference_view import ReferenceManagerView

# --- NEW MODULES ADDED HERE ---
from ui.assembly_view import AssemblyView
from ui.blast_view import BlastView
from ui.rnaseq_view import RNASeqView

class MainWindow(QMainWindow):
    def __init__(self, db_manager):
        super().__init__()
        self.setWindowTitle("MicroGenome Analyzer Pro v3.0")
        self.resize(1400, 950)
        self.db = db_manager

        # --- GLOBAL STYLE FIX ---
        # Forces Dark Text (#333333) on White Backgrounds everywhere
        self.setStyleSheet("""
            /* Base Application Style */
            QMainWindow { background-color: #F4F7FE; }
            QWidget { 
                font-family: 'Segoe UI'; 
                color: #333333; /* FORCE DARK TEXT GLOBALLY */
            }
            
            /* Message Box Fix (Popups) */
            QMessageBox { 
                background-color: white; 
            }
            QMessageBox QLabel { 
                color: #333333; 
                font-weight: 500;
            }
            QMessageBox QPushButton {
                background-color: #F4F7FE;
                color: #333333;
                border: 1px solid #E0E5F2;
                border-radius: 6px;
                padding: 6px 15px;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background-color: #E0E5F2;
            }

            /* Input Fields Fix */
            QLineEdit { 
                background-color: white; 
                color: #333333; 
                border: 1px solid #D0D0D0;
                border-radius: 8px;
            }
            
            /* Dropdown Menus Fix */
            QComboBox { 
                background-color: white; 
                color: #333333;
                border: 1px solid #D0D0D0;
                border-radius: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                color: #333333;
                selection-background-color: #4318FF;
                selection-color: white;
            }
        """)

        # Main Layout Container
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.layout = QVBoxLayout(self.main_widget)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # 1. TOP NAVIGATION BAR
        self.create_navbar()

        # 2. MAIN CONTENT STACK
        self.pages = QStackedWidget()
        self.layout.addWidget(self.pages)
        
        # 3. SYSTEM FOOTER
        self.footer = FooterWidget()
        self.layout.addWidget(self.footer)

        # Initialize Logic
        self.init_pages()

    def create_navbar(self):
        self.navbar = QFrame()
        self.navbar.setFixedHeight(60)
        self.navbar.setStyleSheet("background-color: white; border-bottom: 1px solid #E0E5F2;")
        
        nav_layout = QHBoxLayout(self.navbar)
        nav_layout.setContentsMargins(30, 0, 30, 0)
        
        # Logo Text
        logo = QLabel("🧬 MicroGenome Pro")
        logo.setStyleSheet("font-size: 20px; font-weight: 900; color: #2B3674;")
        nav_layout.addWidget(logo)
        
        nav_layout.addStretch()
        
        # HOME BUTTON
        self.btn_home = QPushButton("🏠  Return to Dashboard")
        self.btn_home.setFixedSize(180, 36)
        self.btn_home.setCursor(Qt.PointingHandCursor)
        self.btn_home.setStyleSheet("""
            QPushButton {
                background-color: #F4F7FE; color: #4318FF; font-weight: bold; 
                border-radius: 8px; border: 1px solid #E0E5F2; font-size: 13px;
            }
            QPushButton:hover { background-color: #4318FF; color: white; border: none; }
        """)
        self.btn_home.clicked.connect(lambda: self.switch_page(0))
        self.btn_home.setVisible(False) 
        nav_layout.addWidget(self.btn_home)

        self.layout.addWidget(self.navbar)

    def init_pages(self):
        """Initializes the Stacked Widget Pages"""
        # 0. Dashboard
        self.dashboard = DashboardView(self.navigate_from_dashboard)
        self.pages.addWidget(self.dashboard)
        
        # 1. Annotation
        self.pages.addWidget(AnnotationView(self.db))
        # 2. Comparative
        self.pages.addWidget(ComparativeView(self.db))
        # 3. Phylogenetics
        self.pages.addWidget(PhyloView(self.db))
        # 4. Specialized
        self.pages.addWidget(SpecializedView(self.db))
        # 5. Structure
        self.pages.addWidget(StructureView())
        # 6. SynBio
        self.pages.addWidget(SynBioView(self.db))
        # 7. Variant
        self.pages.addWidget(VariantView(self.db))
        # 8. Reports
        self.pages.addWidget(ReportView(self.db))
        
        # 9. QC View
        self.pages.addWidget(QCView(self.db))
        
        # 10. Data Manager
        self.pages.addWidget(DataManagerView(self.db))

        # 11. Reference Manager
        self.pages.addWidget(ReferenceManagerView(self.db))

        # --- NEWLY ADDED MODULES ---
        
        # 12. Genome Assembly (Phase 2)
        self.pages.addWidget(AssemblyView(self.db))
        
        # 13. BLAST Alignment (Phase 2)
        self.pages.addWidget(BlastView(self.db))
        
        # 14. RNA-Seq Analysis (Phase 4)
        self.pages.addWidget(RNASeqView(self.db))

    def navigate_from_dashboard(self, index, module_name):
        if index == -1:
            self.show_construction_msg(module_name)
        else:
            self.switch_page(index)
            self.dashboard.add_log_entry(module_name, "Module Accessed", "Started")

    def switch_page(self, index):
        self.pages.setCurrentIndex(index)
        self.btn_home.setVisible(index != 0)

    def show_construction_msg(self, module_name):
        msg = QMessageBox(self)
        msg.setWindowTitle("Module Under Construction")
        msg.setText(f"<h3 style='color:#2B3674;'>🚧 {module_name}</h3><p>This advanced module is part of the v3.0 Roadmap.</p><p>We are currently implementing this feature.</p>")
        msg.setIcon(QMessageBox.Information)
        msg.exec()