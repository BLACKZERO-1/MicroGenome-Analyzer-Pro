import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QFileDialog, QProgressBar, QTextEdit, 
                               QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
                               QRadioButton, QButtonGroup)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont

# IMPORT YOUR UPDATED WORKER
from core.specialized.specialized_engine import SpecializedWorker

class SpecializedView(QWidget):
    def __init__(self, db_manager=None):
        super().__init__()
        self.db = db_manager # Store Database Connection
        self.worker = None
        self.current_mode = "card" # Default to AMR
        self.selected_file = ""
        self.current_analysis_id = None

        # --- STYLESHEET ---
        self.setStyleSheet("""
            QWidget { background-color: #F4F7FE; font-family: 'Segoe UI', sans-serif; }
            QLabel#main_title { color: #2B3674; font-size: 26px; font-weight: 900; }
            QLabel#sub_title { color: #A3AED0; font-size: 14px; font-weight: 500; }
            QFrame#panel_box { background-color: #FFFFFF; border-radius: 16px; border: 1px solid #E0E5F2; }
            QLabel#panel_title { 
                color: #2B3674; font-size: 14px; font-weight: 800; 
                border-bottom: 2px solid #F0F0F0; padding-bottom: 10px; margin-bottom: 10px;
            }
            QPushButton { border-radius: 8px; font-weight: 700; font-size: 13px; border: none; }
            QPushButton#btn_browse { background-color: #E9EDF7; color: #4318FF; }
            QPushButton#btn_browse:hover { background-color: #DCE4F5; }
            QPushButton#btn_run_card { background: #E04F5F; color: white; font-size: 14px; }
            QPushButton#btn_run_card:hover { background: #C22F3E; }
            QPushButton#btn_run_vfdb { background: #8E44AD; color: white; font-size: 14px; }
            QPushButton#btn_run_vfdb:hover { background: #732D91; }
            QTableWidget { border: 1px solid #E0E5F2; border-radius: 8px; background: white; gridline-color: #F0F0F0; }
            QHeaderView::section { background-color: #F4F7FE; color: #A3AED0; font-weight: bold; border: none; padding: 8px; }
            QLabel#risk_badge { border-radius: 6px; padding: 4px 10px; font-weight: 900; color: white; }
            QTextEdit#terminal { 
                background-color: #101010; color: #00FF00; 
                font-family: 'Consolas', monospace; border: 1px solid #333; border-radius: 8px;
            }
        """)

        # --- LAYOUT ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30); main_layout.setSpacing(20)

        self.setup_header(main_layout)
        self.setup_controls(main_layout)
        self.setup_dashboard(main_layout)
        self.setup_logs(main_layout)

    def setup_header(self, layout):
        h = QHBoxLayout()
        self.icon_lbl = QLabel("💊"); self.icon_lbl.setStyleSheet("font-size: 40px; background: transparent;")
        
        v = QVBoxLayout(); v.setSpacing(4)
        self.title_lbl = QLabel("AMR Resistance Scanner"); self.title_lbl.setObjectName("main_title")
        self.desc_lbl = QLabel("Identify antibiotic resistance genes using CARD Database"); self.desc_lbl.setObjectName("sub_title")
        
        v.addWidget(self.title_lbl); v.addWidget(self.desc_lbl)
        h.addWidget(self.icon_lbl); h.addSpacing(20); h.addLayout(v); h.addStretch()
        layout.addLayout(h)

    def setup_controls(self, layout):
        panel = QFrame(); panel.setObjectName("panel_box")
        l = QVBoxLayout(panel); l.setContentsMargins(20, 20, 20, 20)
        
        # Row 1: Mode Selection
        l.addWidget(QLabel("🎯 ANALYSIS MODE", objectName="panel_title"))
        mode_row = QHBoxLayout()
        self.rb_amr = QRadioButton("Antibiotic Resistance (AMR)"); self.rb_amr.setChecked(True)
        self.rb_vir = QRadioButton("Virulence Factors (Pathogenicity)")
        
        for rb in [self.rb_amr, self.rb_vir]:
            rb.setStyleSheet("font-size: 14px; font-weight: 600; color: #2B3674; margin-right: 20px;")
            rb.toggled.connect(self.switch_mode)
            mode_row.addWidget(rb)
        mode_row.addStretch()
        l.addLayout(mode_row); l.addSpacing(15)

        # Row 2: File Selection
        l.addWidget(QLabel("📂 INPUT PROTEINS (.faa)", objectName="panel_title"))
        file_row = QHBoxLayout()
        self.path_lbl = QLabel(" No file selected (Run Annotation First)"); self.path_lbl.setStyleSheet("color: #A3AED0; font-style: italic;")
        btn_browse = QPushButton("Select File"); btn_browse.setObjectName("btn_browse"); btn_browse.setFixedSize(120, 40)
        btn_browse.clicked.connect(self.select_file)
        
        file_row.addWidget(self.path_lbl); file_row.addStretch(); file_row.addWidget(btn_browse)
        l.addLayout(file_row); l.addSpacing(15)

        # Run Button
        self.btn_run = QPushButton("START AMR SCAN"); self.btn_run.setObjectName("btn_run_card")
        self.btn_run.setFixedHeight(50); self.btn_run.setEnabled(False)
        self.btn_run.clicked.connect(self.run_process)
        l.addWidget(self.btn_run)
        
        self.progress = QProgressBar(); self.progress.setFixedHeight(4); self.progress.setTextVisible(False)
        self.progress.setStyleSheet("border: none; background: transparent; QProgressBar::chunk { background: #E04F5F; }")
        l.addWidget(self.progress)
        
        layout.addWidget(panel)

    def setup_dashboard(self, layout):
        row = QHBoxLayout(); row.setSpacing(20)

        # Left: Risk Metrics
        stats_panel = QFrame(); stats_panel.setObjectName("panel_box"); stats_panel.setFixedWidth(280)
        sl = QVBoxLayout(stats_panel); sl.setContentsMargins(20, 20, 20, 20)
        sl.addWidget(QLabel("📊 RISK ASSESSMENT", objectName="panel_title"))
        
        self.risk_badge = QLabel("WAITING"); self.risk_badge.setObjectName("risk_badge")
        self.risk_badge.setStyleSheet("background: #E0E5F2; color: #A3AED0;")
        self.risk_badge.setAlignment(Qt.AlignCenter); self.risk_badge.setFixedHeight(30)
        
        self.count_lbl = QLabel("0"); self.count_lbl.setStyleSheet("font-size: 56px; font-weight: 900; color: #2B3674;")
        self.count_desc = QLabel("Potential Threats Detected"); self.count_desc.setStyleSheet("color: #A3AED0; font-weight: 600;")
        
        sl.addWidget(self.risk_badge); sl.addSpacing(20)
        sl.addWidget(self.count_lbl); sl.addWidget(self.count_desc)
        sl.addStretch()
        
        # Right: Table
        table_panel = QFrame(); table_panel.setObjectName("panel_box")
        tl = QVBoxLayout(table_panel); tl.setContentsMargins(20, 20, 20, 20)
        tl.addWidget(QLabel("🧬 DETECTED GENE FAMILIES", objectName="panel_title"))
        
        self.table = QTableWidget(); self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Gene Family / Class", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        tl.addWidget(self.table)

        row.addWidget(stats_panel); row.addWidget(table_panel)
        layout.addLayout(row)

    def setup_logs(self, layout):
        panel = QFrame(); panel.setObjectName("panel_box")
        l = QVBoxLayout(panel); l.setContentsMargins(20, 20, 20, 20)
        l.addWidget(QLabel("📝 SCAN LOGS", objectName="panel_title"))
        self.terminal = QTextEdit(); self.terminal.setObjectName("terminal"); self.terminal.setReadOnly(True)
        self.terminal.setFixedHeight(120)
        l.addWidget(self.terminal)
        layout.addWidget(panel)

    # --- LOGIC ---
    def switch_mode(self):
        if self.rb_amr.isChecked():
            self.current_mode = "card"
            self.icon_lbl.setText("💊")
            self.title_lbl.setText("AMR Resistance Scanner")
            self.desc_lbl.setText("Identify antibiotic resistance genes using CARD Database")
            self.btn_run.setText("START AMR SCAN")
            self.btn_run.setObjectName("btn_run_card")
            self.progress.setStyleSheet("border: none; background: transparent; QProgressBar::chunk { background: #E04F5F; }")
        else:
            self.current_mode = "vfdb"
            self.icon_lbl.setText("☣️")
            self.title_lbl.setText("Virulence Factor Scanner")
            self.desc_lbl.setText("Identify pathogenicity factors using VFDB Database")
            self.btn_run.setText("START VIRULENCE SCAN")
            self.btn_run.setObjectName("btn_run_vfdb")
            self.progress.setStyleSheet("border: none; background: transparent; QProgressBar::chunk { background: #8E44AD; }")
        
        self.btn_run.style().unpolish(self.btn_run)
        self.btn_run.style().polish(self.btn_run)

    def select_file(self):
        default_dir = os.path.join(os.getcwd(), "results", "annotation")
        f, _ = QFileDialog.getOpenFileName(self, "Select Protein File", default_dir, "Protein Fasta (*.faa)")
        if f:
            self.path_lbl.setText(f"📄 {os.path.basename(f)}")
            self.path_lbl.setStyleSheet("color: #2B3674; font-weight: 600;")
            self.selected_file = f
            self.btn_run.setEnabled(True)
            self.log(f"Loaded input: {os.path.basename(f)}")
            
            # DB Project Tracking
            if self.db:
                try:
                    # Try to link to existing project
                    proj = self.db.get_project_by_path(f.replace(".faa", ".fasta")) # Heuristic
                    if proj: self.log(f"Linked to Project ID: {proj['project_id']}")
                except: pass

    def run_process(self):
        self.terminal.clear(); self.progress.setValue(0); self.table.setRowCount(0)
        self.btn_run.setEnabled(False)
        self.count_lbl.setText("0")
        self.risk_badge.setText("SCANNING...")
        self.risk_badge.setStyleSheet("background: #E0E5F2; color: #707EAE;")

        # DB: Start Log
        if self.db:
             # Just use a dummy ID or last used for now since .faa files are derived
             # In a real app, you'd pass the parent project ID explicitly
             try:
                 projects = self.db.get_all_projects(limit=1)
                 if projects:
                     self.current_analysis_id = self.db.start_analysis(projects[0]['project_id'], "specialized_scan")
             except: pass

        self.worker = SpecializedWorker(self.selected_file, self.current_mode)
        self.worker.log_signal.connect(self.log)
        self.worker.progress_signal.connect(self.progress.setValue)
        self.worker.result_signal.connect(self.display_results)
        self.worker.finished_signal.connect(lambda: self.btn_run.setEnabled(True))
        self.worker.start()

    def display_results(self, data):
        hits = data['total_hits']
        classes = data['classes']
        risk = data['risk_level']

        # Update Metrics
        self.count_lbl.setText(str(hits))
        if risk == "HIGH":
            self.risk_badge.setText("⚠️ HIGH RISK")
            self.risk_badge.setStyleSheet("background: #FF5252; color: white;")
        elif risk == "MEDIUM":
            self.risk_badge.setText("⚠️ MEDIUM RISK")
            self.risk_badge.setStyleSheet("background: #FFAB00; color: white;")
        else:
            self.risk_badge.setText("✅ LOW RISK")
            self.risk_badge.setStyleSheet("background: #05CD99; color: white;")

        # Update Table
        self.table.setRowCount(len(classes))
        for i, item in enumerate(classes):
            self.table.setItem(i, 0, QTableWidgetItem(item))
            self.table.setItem(i, 1, QTableWidgetItem("Detected"))
            
        # DB: Save
        if self.db and self.current_analysis_id:
            # We save the raw count into the analysis log for now
            self.db.complete_analysis(self.current_analysis_id, success=True)

    def log(self, msg):
        self.terminal.append(f"> {msg}")
        self.terminal.verticalScrollBar().setValue(self.terminal.verticalScrollBar().maximum())