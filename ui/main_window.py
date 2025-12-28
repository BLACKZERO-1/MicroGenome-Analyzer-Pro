import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QStackedWidget, QFrame, QListWidget, QMessageBox
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QAction

# --- IMPORT ALL VIEWS ---
from ui.dashboard_view import DashboardView
from ui.annotation_view import AnnotationView
from ui.variant_view import VariantView         
from ui.structure_view import StructureView     
from ui.synbio_view import SynBioView           # <--- NEW MODULE IMPORT
from ui.comparative_view import ComparativeView 
from ui.phylo_view import PhyloView             
from ui.specialized_view import SpecializedView 
from ui.report_view import ReportView

class MainWindow(QMainWindow):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.setWindowTitle("MicroGenome Analyzer Pro (Research Edition)")
        self.resize(1280, 850)
        
        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QHBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # 1. SIDEBAR
        self._build_sidebar()
        
        # 2. CONTENT AREA
        self._build_content_stack()
        
        # 3. CONNECT NAVIGATION
        self._connect_nav()

        # Load Styles
        self._apply_styles()

    def _build_sidebar(self):
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(260)
        self.sidebar.setObjectName("sidebar")
        
        layout = QVBoxLayout(self.sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Header / Logo
        header = QLabel("🧬 MicroGenome")
        header.setAlignment(Qt.AlignCenter)
        header.setObjectName("sidebar_header")
        header.setFixedHeight(80)
        layout.addWidget(header)
        
        # Navigation Buttons
        self.nav_btns = []
        
        # Define Menu Items: (Label, Icon_Placeholder)
        menu_items = [
            ("Dashboard", "📊"),
            ("Annotation (Genes)", "🧬"),
            ("Variant Analysis (SNP)", "🔬"),
            ("3D Structure", "🧊"),
            ("SynBio (Cloning)", "🧪"),      # <--- NEW MENU ITEM
            ("Comparative (Synteny)", "🔄"),
            ("Phylogenetics (Tree)", "🌳"),
            ("AMR & Virulence", "💊"),
            ("Reports & Export", "📑")
        ]
        
        for i, (label, icon) in enumerate(menu_items):
            btn = QPushButton(f"  {icon}  {label}")
            btn.setCheckable(True)
            btn.setObjectName("nav_btn")
            btn.setFixedHeight(50)
            if i == 0: btn.setChecked(True) # Default to Dashboard
            
            self.nav_btns.append(btn)
            layout.addWidget(btn)
            
        layout.addStretch()
        
        # Footer
        version = QLabel("v2.0 Pro")
        version.setAlignment(Qt.AlignCenter)
        version.setStyleSheet("color: #707EAE; padding-bottom: 20px;")
        layout.addWidget(version)
        
        self.main_layout.addWidget(self.sidebar)

    def _build_content_stack(self):
        self.stack = QStackedWidget()
        
        # 1. Dashboard
        self.stack.addWidget(DashboardView(self.db))
        
        # 2. Annotation
        self.stack.addWidget(AnnotationView(self.db))
        
        # 3. Variant Calling
        self.stack.addWidget(VariantView(self.db))

        # 4. 3D Structure
        self.stack.addWidget(StructureView(self.db))
        
        # 5. SynBio (Cloning) - NEW
        self.stack.addWidget(SynBioView(self.db))
        
        # 6. Comparative 
        try: self.stack.addWidget(ComparativeView(self.db))
        except: self.stack.addWidget(QLabel("Comparative Module Loading..."))
            
        # 7. Phylogenetics
        try: self.stack.addWidget(PhyloView(self.db))
        except: self.stack.addWidget(QLabel("Phylo Module Loading..."))
            
        # 8. Specialized
        try: self.stack.addWidget(SpecializedView(self.db))
        except: self.stack.addWidget(QLabel("Specialized Module Loading..."))
        
        # 9. Reports
        self.stack.addWidget(ReportView(self.db))
        
        self.main_layout.addWidget(self.stack)

    def _connect_nav(self):
        # Map buttons to stack index
        for i, btn in enumerate(self.nav_btns):
            # Capture 'i' in the lambda using default argument
            btn.clicked.connect(lambda checked, index=i: self._switch_tab(index))

    def _switch_tab(self, index):
        self.stack.setCurrentIndex(index)
        
        # Update Button Styles
        for i, btn in enumerate(self.nav_btns):
            btn.setChecked(i == index)

    def _apply_styles(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #F4F7FE; }
            
            /* SIDEBAR STYLE */
            QFrame#sidebar {
                background-color: white;
                border-right: 1px solid #E0E5F2;
            }
            QLabel#sidebar_header {
                font-family: 'Segoe UI';
                font-size: 22px;
                font-weight: 900;
                color: #2B3674;
                border-bottom: 1px solid #E0E5F2;
            }
            
            /* NAV BUTTONS */
            QPushButton#nav_btn {
                text-align: left;
                padding-left: 30px;
                border: none;
                border-left: 4px solid transparent;
                background-color: transparent;
                color: #A3AED0;
                font-size: 14px;
                font-weight: 600;
                font-family: 'Segoe UI';
            }
            QPushButton#nav_btn:hover {
                background-color: #F4F7FE;
                color: #2B3674;
            }
            QPushButton#nav_btn:checked {
                background-color: white;
                color: #4318FF;
                border-left: 4px solid #4318FF;
                font-weight: bold;
            }
        """)