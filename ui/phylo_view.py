import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QFileDialog, QProgressBar, QTextEdit, 
                               QFrame, QListWidget, QSplitter)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

from core.phylogenetics.phylo_engine import PhyloWorker

class PhyloView(QWidget):
    def __init__(self, db_manager=None):
        super().__init__()
        self.db = db_manager
        self.worker = None
        self.selected_files = []
        self.current_analysis_id = None

        # --- STYLESHEET ---
        self.setStyleSheet("""
            QWidget { background-color: #F8F9FC; font-family: 'Segoe UI', sans-serif; }
            QLabel#sidebar_title { color: #2B3674; font-size: 18px; font-weight: 800; margin-bottom: 5px; }
            QLabel#section_lbl { color: #A3AED0; font-size: 12px; font-weight: 700; text-transform: uppercase; margin-top: 10px;}
            QFrame#card { background-color: #FFFFFF; border-radius: 15px; border: 1px solid #E0E5F2; }
            QListWidget { 
                border: 2px dashed #E0E5F2; border-radius: 10px; padding: 10px; 
                background: #FAFCFE; color: #2B3674; font-weight: 600; font-size: 13px;
                outline: none;
            }
            QPushButton { border-radius: 10px; font-weight: 700; font-size: 13px; padding: 12px; border: none; }
            QPushButton#btn_primary { background-color: #4318FF; color: white; }
            QPushButton#btn_primary:hover { background-color: #3311CC; }
            QPushButton#btn_primary:disabled { background-color: #A3AED0; }
            QPushButton#btn_secondary { background-color: #E9EDF7; color: #4318FF; }
            QPushButton#btn_secondary:hover { background-color: #DCE4F5; }
            QPushButton#btn_danger { background-color: #FFF5F5; color: #FF5252; border: 1px solid #FFDCDC; }
            QTextEdit#terminal { 
                background-color: #111C44; color: #00E676; 
                font-family: 'Consolas', monospace; font-size: 12px;
                border: none; border-radius: 0px 0px 15px 15px;
            }
            QLabel#tree_view { background-color: white; border-radius: 15px; }
        """)

        # --- LAYOUT ---
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(25, 25, 25, 25); main_layout.setSpacing(25)

        # LEFT SIDEBAR
        sidebar = QFrame(); sidebar.setObjectName("card"); sidebar.setFixedWidth(320)
        sl = QVBoxLayout(sidebar); sl.setContentsMargins(20, 25, 20, 25); sl.setSpacing(15)
        
        # Header
        head_layout = QHBoxLayout()
        icon = QLabel("🌳"); icon.setStyleSheet("font-size: 32px; background: transparent;")
        title = QLabel("Phylogenetics"); title.setObjectName("sidebar_title")
        head_layout.addWidget(icon); head_layout.addWidget(title); head_layout.addStretch()
        sl.addLayout(head_layout)
        
        sl.addWidget(QLabel("INPUT GENOMES", objectName="section_lbl"))
        self.file_list = QListWidget()
        sl.addWidget(self.file_list)
        
        btn_row = QHBoxLayout()
        self.btn_add = QPushButton("Add Files"); self.btn_add.setObjectName("btn_secondary")
        self.btn_add.clicked.connect(self.select_files)
        self.btn_clear = QPushButton("Clear"); self.btn_clear.setObjectName("btn_danger")
        self.btn_clear.clicked.connect(self.clear_files)
        btn_row.addWidget(self.btn_add, 2); btn_row.addWidget(self.btn_clear, 1)
        sl.addLayout(btn_row)

        sl.addStretch()
        sl.addWidget(QLabel("ACTION", objectName="section_lbl"))
        self.btn_run = QPushButton("BUILD TREE"); self.btn_run.setObjectName("btn_primary")
        self.btn_run.setEnabled(False)
        self.btn_run.clicked.connect(self.run_phylo)
        sl.addWidget(self.btn_run)
        
        self.progress = QProgressBar(); self.progress.setFixedHeight(8); self.progress.setTextVisible(False)
        self.progress.setStyleSheet("background: #E0E5F2; border-radius: 4px; QProgressBar::chunk { background: #4318FF; border-radius: 4px; }")
        sl.addWidget(self.progress)
        
        main_layout.addWidget(sidebar)

        # RIGHT PANEL
        right_splitter = QSplitter(Qt.Vertical)
        right_splitter.setStyleSheet("QSplitter::handle { background-color: #E0E5F2; }")
        
        # Tree Container
        tree_container = QFrame(); tree_container.setObjectName("card")
        tl = QVBoxLayout(tree_container); tl.setContentsMargins(0,0,0,0)
        
        th = QFrame(); th.setStyleSheet("background: #FFFFFF; border-bottom: 1px solid #F0F0F0; border-radius: 15px 15px 0 0;")
        thl = QHBoxLayout(th); thl.setContentsMargins(20, 15, 20, 15)
        thl.addWidget(QLabel("🧬 Evolutionary Tree Visualization", objectName="sidebar_title"))
        tl.addWidget(th)
        
        self.tree_lbl = QLabel("Load files and click 'Build Tree'"); self.tree_lbl.setObjectName("tree_view")
        self.tree_lbl.setAlignment(Qt.AlignCenter)
        self.tree_lbl.setStyleSheet("color: #A3AED0; font-size: 16px; font-weight: 600; padding: 20px;")
        tl.addWidget(self.tree_lbl, 1)
        right_splitter.addWidget(tree_container)

        # Log Container
        term_container = QFrame(); term_container.setObjectName("card")
        terml = QVBoxLayout(term_container); terml.setContentsMargins(0,0,0,0)
        
        th2 = QFrame(); th2.setStyleSheet("background: #FFFFFF; border-bottom: 1px solid #F0F0F0; border-radius: 15px 15px 0 0;")
        thl2 = QHBoxLayout(th2); thl2.setContentsMargins(20, 10, 20, 10)
        thl2.addWidget(QLabel("📝 Analysis Logs", styleSheet="font-weight: 800; color: #2B3674;"))
        terml.addWidget(th2)
        
        self.terminal = QTextEdit(); self.terminal.setObjectName("terminal"); self.terminal.setReadOnly(True)
        terml.addWidget(self.terminal)
        right_splitter.addWidget(term_container)
        
        right_splitter.setSizes([800, 250])
        main_layout.addWidget(right_splitter, 1)

    # --- LOGIC ---
    def select_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Genomes", "", "Fasta Files (*.fasta *.fna *.fa)")
        if files:
            for f in files:
                if f not in self.selected_files:
                    self.selected_files.append(f)
                    self.file_list.addItem(f"📄 {os.path.basename(f)}")
            self.check_ready()
            self.log(f"Added {len(files)} files.")

    def clear_files(self):
        self.selected_files = []
        self.file_list.clear()
        self.check_ready()
        self.log("Queue cleared.")

    def check_ready(self):
        self.btn_run.setEnabled(len(self.selected_files) >= 2)
        self.btn_run.setText(f"BUILD TREE ({len(self.selected_files)})" if len(self.selected_files) >= 2 else "Select 2+ Files")

    def run_phylo(self):
        self.terminal.clear()
        self.progress.setValue(5)
        self.btn_run.setEnabled(False)
        self.tree_lbl.setText("⏳ Analyzing... Please Wait")
        
        # --- DB: START ANALYSIS ---
        if self.db and len(self.selected_files) > 0:
            try:
                # Associate with the first file's project ID for tracking
                proj = self.db.get_project_by_path(self.selected_files[0])
                if proj:
                    self.current_analysis_id = self.db.start_analysis(proj['project_id'], "phylogenetics")
            except Exception as e:
                self.log(f"⚠️ DB Error: {e}")

        self.worker = PhyloWorker(self.selected_files)
        self.worker.log_signal.connect(self.log)
        self.worker.progress_signal.connect(self.progress.setValue)
        self.worker.result_signal.connect(self.display_tree)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.start()

    def display_tree(self, img_path):
        if os.path.exists(img_path):
            pixmap = QPixmap(img_path)
            w, h = self.tree_lbl.width(), self.tree_lbl.height()
            self.tree_lbl.setPixmap(pixmap.scaled(w-20, h-20, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.log(f"✅ Tree Visualized: {os.path.basename(img_path)}")
            
            
            # --- DB: COMPLETE ANALYSIS ---
            if self.db and self.current_analysis_id:
                self.db.complete_analysis(self.current_analysis_id, success=True)
                self.db.update_project_status(self.current_analysis_id, "completed")

    def on_finished(self, success, message):
        self.btn_run.setEnabled(True)
        self.check_ready()
        
        if success:
            self.log("🎉 Analysis Finished Successfully.")
            self.progress.setValue(100)
        else:
            self.log(f"❌ ERROR: {message}")
            self.tree_lbl.setText(f"Analysis Failed:\n{message}")
            self.progress.setValue(0)
            
            if self.db and self.current_analysis_id:
                self.db.complete_analysis(self.current_analysis_id, success=False, error=message)

    def log(self, msg):
        self.terminal.append(f"> {msg}")
        self.terminal.verticalScrollBar().setValue(self.terminal.verticalScrollBar().maximum())