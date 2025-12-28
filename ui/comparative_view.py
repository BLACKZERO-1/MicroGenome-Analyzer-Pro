import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QFileDialog, QProgressBar, QTextEdit, 
                               QFrame, QScrollArea, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

# IMPORT THE NEW ENGINE
from core.comparative.comparative_engine import ComparativeWorker

class ComparativeView(QWidget):
    def __init__(self, db_manager=None):
        super().__init__()
        self.db = db_manager
        self.worker = None
        self.query_file = ""
        self.ref_file = ""
        self.current_project_id = None

        # --- STYLESHEET ---
        self.setStyleSheet("""
            QWidget { background-color: #F4F7FE; font-family: 'Segoe UI', sans-serif; }
            
            /* HEADERS */
            QLabel#main_title { color: #2B3674; font-size: 26px; font-weight: 900; }
            QLabel#sub_title { color: #A3AED0; font-size: 14px; font-weight: 500; }
            
            /* PANELS */
            QFrame#panel_box { background-color: #FFFFFF; border-radius: 16px; border: 1px solid #E0E5F2; }
            QLabel#panel_title { 
                color: #2B3674; font-size: 14px; font-weight: 800; 
                border-bottom: 2px solid #F0F0F0; padding-bottom: 10px; margin-bottom: 10px;
            }

            /* INPUTS */
            QPushButton { border-radius: 8px; font-weight: 700; font-size: 13px; border: none; }
            QPushButton#btn_browse { background-color: #E9EDF7; color: #4318FF; }
            QPushButton#btn_browse:hover { background-color: #DCE4F5; }
            
            /* RUN BUTTON */
            QPushButton#btn_run { background: #4318FF; color: white; font-size: 14px; margin-top: 10px; }
            QPushButton#btn_run:hover { background: #3311CC; }
            QPushButton#btn_run:disabled { background: #A3AED0; }

            /* LOG TERMINAL */
            QTextEdit#terminal { 
                background-color: #101010; 
                color: #00FF00; 
                font-family: 'Consolas', monospace;
                border: 1px solid #333;
                border-radius: 8px;
            }
            
            /* IMAGE VIEWER */
            QLabel#img_viewer { background-color: #F4F7FE; border-radius: 8px; border: 2px dashed #E0E5F2; }
        """)

        # --- LAYOUT ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)

        self.setup_header(main_layout)
        self.setup_controls(main_layout)
        self.setup_results(main_layout)

    def setup_header(self, layout):
        h = QHBoxLayout()
        icon = QLabel("📊"); icon.setStyleSheet("font-size: 40px; background: transparent;")
        
        v = QVBoxLayout(); v.setSpacing(4)
        t1 = QLabel("Comparative Genomics"); t1.setObjectName("main_title")
        t2 = QLabel("Generate Whole Genome Synteny Dotplots (BLASTN)"); t2.setObjectName("sub_title")
        
        v.addWidget(t1); v.addWidget(t2)
        h.addWidget(icon); h.addSpacing(20); h.addLayout(v); h.addStretch()
        layout.addLayout(h)

    def setup_controls(self, layout):
        panel = QFrame(); panel.setObjectName("panel_box")
        l = QVBoxLayout(panel); l.setContentsMargins(20, 20, 20, 20)
        
        # 1. Query File (Input)
        l.addWidget(QLabel("📂 QUERY GENOME (Your Sequence)", objectName="panel_title"))
        r1 = QHBoxLayout()
        self.lbl_query = QLabel("No file selected"); self.lbl_query.setStyleSheet("color: #A3AED0; font-style: italic;")
        b1 = QPushButton("Select Query"); b1.setObjectName("btn_browse"); b1.setFixedSize(120, 35)
        b1.clicked.connect(lambda: self.select_file("query"))
        r1.addWidget(self.lbl_query); r1.addStretch(); r1.addWidget(b1)
        l.addLayout(r1); l.addSpacing(10)

        # 2. Reference File
        l.addWidget(QLabel("📘 REFERENCE GENOME (e.g., E. coli K12)", objectName="panel_title"))
        r2 = QHBoxLayout()
        self.lbl_ref = QLabel("No file selected"); self.lbl_ref.setStyleSheet("color: #A3AED0; font-style: italic;")
        b2 = QPushButton("Select Reference"); b2.setObjectName("btn_browse"); b2.setFixedSize(120, 35)
        b2.clicked.connect(lambda: self.select_file("ref"))
        r2.addWidget(self.lbl_ref); r2.addStretch(); r2.addWidget(b2)
        l.addLayout(r2); l.addSpacing(15)

        # 3. Run Button & Progress
        self.btn_run = QPushButton("RUN SYNTENY CHECK"); self.btn_run.setObjectName("btn_run")
        self.btn_run.setFixedHeight(45); self.btn_run.setEnabled(False)
        self.btn_run.clicked.connect(self.run_comparison)
        l.addWidget(self.btn_run)
        
        l.addSpacing(10)
        self.progress = QProgressBar(); self.progress.setFixedHeight(6); self.progress.setTextVisible(False)
        self.progress.setStyleSheet("border: none; background: #E0E5F2; border-radius: 3px; QProgressBar::chunk { background: #4318FF; border-radius: 3px; }")
        l.addWidget(self.progress)

        layout.addWidget(panel)

    def setup_results(self, layout):
        row = QHBoxLayout(); row.setSpacing(20)

        # Left: Image Viewer (Scalable)
        viewer_panel = QFrame(); viewer_panel.setObjectName("panel_box")
        vl = QVBoxLayout(viewer_panel); vl.setContentsMargins(10, 10, 10, 10)
        vl.addWidget(QLabel("🎨 SYNTENY DOTPLOT", objectName="panel_title"))
        
        # Scroll Area for large plots
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        
        self.img_label = QLabel("Run comparison to view Plot"); self.img_label.setObjectName("img_viewer")
        self.img_label.setAlignment(Qt.AlignCenter)
        self.img_label.setScaledContents(True) # Allow scaling
        
        scroll.setWidget(self.img_label)
        vl.addWidget(scroll)
        
        # Right: Logs
        log_panel = QFrame(); log_panel.setObjectName("panel_box"); log_panel.setFixedWidth(320)
        ll = QVBoxLayout(log_panel); ll.setContentsMargins(10, 10, 10, 10)
        ll.addWidget(QLabel("📝 ANALYSIS LOGS", objectName="panel_title"))
        
        self.terminal = QTextEdit(); self.terminal.setObjectName("terminal"); self.terminal.setReadOnly(True)
        ll.addWidget(self.terminal)

        row.addWidget(viewer_panel, 3) # Give viewer more space (ratio 3:1)
        row.addWidget(log_panel, 1)
        layout.addLayout(row)

    # --- LOGIC ---

    def select_file(self, ftype):
        f, _ = QFileDialog.getOpenFileName(self, "Select Genome Fasta", "", "Fasta Files (*.fasta *.fna *.fa *.txt)")
        if f:
            name = os.path.basename(f)
            if ftype == "query":
                self.query_file = f
                self.lbl_query.setText(f"📄 {name}")
                self.lbl_query.setStyleSheet("color: #2B3674; font-weight: 600;")
                
                # --- DB: CREATE/FIND PROJECT ---
                if self.db:
                    try:
                        existing = self.db.get_project_by_path(f)
                        if existing: 
                            self.current_project_id = existing['project_id']
                            self.log(f"Resuming Project ID: {self.current_project_id}")
                        else:
                            self.current_project_id = self.db.create_project(name, f, os.path.getsize(f))
                            self.log(f"New Project Created ID: {self.current_project_id}")
                    except Exception as e:
                        self.log(f"⚠️ DB Error: {e}")

            else:
                self.ref_file = f
                self.lbl_ref.setText(f"📘 {name}")
                self.lbl_ref.setStyleSheet("color: #2B3674; font-weight: 600;")
            
            # Enable Run if both files selected
            if self.query_file and self.ref_file:
                self.btn_run.setEnabled(True)

    def run_comparison(self):
        self.terminal.clear(); self.progress.setValue(0)
        self.btn_run.setEnabled(False)
        self.img_label.setText("Generating Plot... Please Wait.")
        
        # DB: Start Analysis Log
        analysis_id = None
        if self.db and self.current_project_id:
            try:
                analysis_id = self.db.start_analysis(self.current_project_id, "comparative")
            except: pass

        # Instantiate the Worker with the two files
        self.worker = ComparativeWorker(self.query_file, self.ref_file)
        
        # Connect Signals
        self.worker.log_signal.connect(self.log)
        self.worker.progress_signal.connect(self.progress.setValue)
        self.worker.result_signal.connect(lambda data: self.display_result(data, analysis_id))
        self.worker.finished_signal.connect(self.on_finish)
        
        self.worker.start()

    def display_result(self, data, analysis_id=None):
        """Displays the generated dotplot and final stats."""
        plot_path = data.get("plot_path")
        matches = data.get("matches")
        
        if plot_path and os.path.exists(plot_path):
            pixmap = QPixmap(plot_path)
            # Scale simply for fit, high-res is saved to disk
            self.img_label.setPixmap(pixmap.scaled(self.img_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.log(f"✅ Plot Generated Successfully.")
            self.log(f"📊 Synteny Matches Found: {matches}")
            self.log(f"💾 Image saved at: {plot_path}")
            
            # --- DB: SAVE RESULTS ---
            if self.db and analysis_id:
                try:
                    # Save summary to comparative_results table
                    # Note: We need to adapt the schema or use a generic field if specific columns don't exist
                    # For now, we will mark the analysis as complete
                    self.db.complete_analysis(analysis_id, success=True)
                    self.db.update_project_status(self.current_project_id, "completed")
                    self.log("✅ Results saved to Database.")
                except Exception as e:
                    self.log(f"⚠️ DB Save Error: {e}")

        else:
            self.img_label.setText("Error loading image")
            self.log("❌ Failed to load generated plot.")
            if self.db and analysis_id:
                self.db.complete_analysis(analysis_id, success=False, error="Plot generation failed")

    def on_finish(self):
        self.btn_run.setEnabled(True)

    def log(self, msg):
        self.terminal.append(f"> {msg}")
        self.terminal.verticalScrollBar().setValue(self.terminal.verticalScrollBar().maximum())