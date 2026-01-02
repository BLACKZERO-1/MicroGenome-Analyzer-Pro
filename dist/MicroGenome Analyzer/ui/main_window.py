from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, 
                               QVBoxLayout, QPushButton, QStackedWidget, QFrame, QLabel)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

# Import all View Modules
from ui.dashboard_view import DashboardView
from ui.annotation_view import AnnotationView
from ui.comparative_view import ComparativeView
from ui.phylo_view import PhyloView
from ui.specialized_view import SpecializedView
from ui.pathway_view import PathwayView
from ui.report_view import ReportView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MicroGenome Analyzer Pro v1.0")
        self.resize(1280, 850)

        # ==========================================================================
        # GLOBAL STYLESHEET (High Contrast)
        # ==========================================================================
        self.setStyleSheet("""
            QMainWindow { background-color: #F4F7FE; }
            
            /* SIDEBAR STYLING */
            QFrame#sidebar {
                background-color: #FFFFFF;
                border-right: 1px solid #E0E5F2;
            }
            
            /* LOGO AREA */
            QLabel#app_logo {
                font-size: 24px; font-weight: 900; color: #1B254B;
                padding-left: 10px;
            }
            QLabel#app_ver {
                font-size: 11px; font-weight: 600; color: #707EAE; 
                padding-left: 12px; margin-bottom: 20px;
            }

            /* NAVIGATION BUTTONS */
            QPushButton {
                background-color: transparent;
                color: #2B3674; /* Dark Navy for visibility */
                font-size: 14px;
                font-weight: 600;
                text-align: left;
                padding: 15px 20px;
                border-left: 4px solid transparent;
                border-radius: 0px;
            }
            
            /* HOVER STATE */
            QPushButton:hover {
                background-color: #F4F7FE;
                color: #4318FF;
            }

            /* ACTIVE (CHECKED) STATE */
            QPushButton:checked {
                color: #4318FF; 
                background-color: #E9EDF7; 
                border-left: 4px solid #4318FF; 
                font-weight: 800;
            }
            
            /* FOOTER */
            QLabel#footer_text {
                color: #A3AED0;
                font-size: 10px;
                padding: 10px;
            }
        """)

        # 1. Main Layout Assembly
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QHBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # 2. Sidebar Construction
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(260)
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(0, 30, 0, 20)
        self.sidebar_layout.setSpacing(5)

        # Logo / Branding
        logo = QLabel("MicroGenome")
        logo.setObjectName("app_logo")
        ver = QLabel("ANALYZER PRO")
        ver.setObjectName("app_ver")
        
        self.sidebar_layout.addWidget(logo)
        self.sidebar_layout.addWidget(ver)
        self.sidebar_layout.addSpacing(20)

        # Navigation Buttons
        self.btn_dash = QPushButton("  🚀  Dashboard")
        self.btn_anno = QPushButton("  🧬  Annotation")
        self.btn_comp = QPushButton("  📊  Comparative")
        self.btn_phylo = QPushButton("  🌳  Phylogenetics")
        self.btn_spec = QPushButton("  🛡️  AMR Screening")
        self.btn_path = QPushButton("  🕸️  Pathways")
        self.btn_repr = QPushButton("  📝  Reports")

        self.nav_btns = [
            self.btn_dash, self.btn_anno, self.btn_comp, 
            self.btn_phylo, self.btn_spec, self.btn_path, self.btn_repr
        ]

        for btn in self.nav_btns:
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            self.sidebar_layout.addWidget(btn)
        
        self.sidebar_layout.addStretch()
        
        # Footer
        footer = QLabel("© 2025 BioSoft Systems")
        footer.setObjectName("footer_text")
        footer.setAlignment(Qt.AlignCenter)
        self.sidebar_layout.addWidget(footer)

        self.btn_dash.setChecked(True)

        # 3. Content Stack Initialization
        self.stack = QStackedWidget()
        self.stack.addWidget(DashboardView())      # 0
        self.stack.addWidget(AnnotationView())     # 1
        self.stack.addWidget(ComparativeView())    # 2
        self.stack.addWidget(PhyloView())          # 3
        self.stack.addWidget(SpecializedView())    # 4
        self.stack.addWidget(PathwayView())        # 5
        self.stack.addWidget(ReportView())         # 6

        # 4. Assembly and Logic
        self.layout.addWidget(self.sidebar)
        self.layout.addWidget(self.stack)

        # Page Switching Logic
        self.btn_dash.clicked.connect(lambda: self.switch(0, self.btn_dash))
        self.btn_anno.clicked.connect(lambda: self.switch(1, self.btn_anno))
        self.btn_comp.clicked.connect(lambda: self.switch(2, self.btn_comp))
        self.btn_phylo.clicked.connect(lambda: self.switch(3, self.btn_phylo))
        self.btn_spec.clicked.connect(lambda: self.switch(4, self.btn_spec))
        self.btn_path.clicked.connect(lambda: self.switch(5, self.btn_path))
        self.btn_repr.clicked.connect(lambda: self.switch(6, self.btn_repr))

    def switch(self, index, active_btn):
        # Uncheck all, check the active one
        for btn in self.nav_btns:
            btn.setChecked(False)
        active_btn.setChecked(True)
        self.stack.setCurrentIndex(index)